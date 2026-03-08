import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime, timedelta, date

# ==========================================
# 🔑 КОНФІГУРАЦІЯ (FOOD FESTIVAL GOLD)
# ==========================================
CONFIG = {
    "LOGO_URL": "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png",
    "CATALOG_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv",
    "CLIENTS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv",
    "ORDERS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv",
    "SETTINGS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=295620790&single=true&output=csv",
    "SCRIPT_URL": "https://script.google.com/macros/s/AKfycbyaFzeDCKyGghOoel888Xx_QkEaYTytH2te1BsJlSlUAqKYg1LyxF0_AwogvNPOU1PX/exec",
    "TG_TOKEN": "8297615872:AAHTV_TVOI_TOKEN_TUT", # ВСТАВ СВІЙ ТОКЕН ТУТ
    "GROUP_ID": "-1005236190167",
    "MIN_ORDER": 1000
}

st.set_page_config(page_title="Food Festival ERP", page_icon=CONFIG["LOGO_URL"], layout="wide")

# ==========================================
# ✨ ПРЕМІУМ СТИЛІ (Золоті кнопки та закруглення)
# ==========================================
st.markdown("""
    <style>
    .product-card { background: white; padding: 18px; border-radius: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); border: 1px solid #f1f1f1; margin-bottom: 20px; }
    .special-offer { border: 2px solid #D4AC0D !important; background: #FFFDF5 !important; }
    div.stButton > button { background-color: #D4AC0D !important; color: white !important; border-radius: 12px !important; font-weight: bold !important; height: 48px; border: none !important; }
    .timer-alert { padding: 12px; border-radius: 12px; text-align: center; font-weight: bold; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ ЯДРО ДАНИХ
# ==========================================
@st.cache_data(ttl=30)
def load_data(url):
    try:
        df = pd.read_csv(url, dtype=str).fillna('')
        if 'Фото' in df.columns:
            df['Фото'] = df['Фото'].apply(lambda x: re.findall(r'(https?://[^\s"\';)]+)', x)[0] if "http" in x else x)
        return df
    except: return None

def get_active_fop():
    df_set = load_data(CONFIG["SETTINGS_URL"])
    if df_set is not None and not df_set.empty:
        # Шукаємо рядок зі статусом 'Активно'
        active = df_set[df_set['Статус'].str.contains('Актив', case=False)]
        if not active.empty: return active.iloc[0]['Назва ФОП']
    return "ФОП Основний"

# ==========================================
# 🍽️ КАТАЛОГ 3х3
# ==========================================
def show_catalog(u):
    st.title("🍽️ Меню Food Festival")
    df = load_data(CONFIG["CATALOG_URL"])
    if df is None: return

    # Фільтри
    c1, c2, c3 = st.columns([2, 1, 1])
    search = c1.text_input("🔍 Пошук товару або артикулу...")
    categories = ["Всі"] + sorted(df['Категорія'].unique().tolist())
    sel_cat = c2.selectbox("📂 Категорія", categories)
    sort_opt = c3.selectbox("⚖️ Сортувати", ["Новинки", "Ціна: низька", "Ціна: висока"])

    f_df = df.copy()
    if sel_cat != "Всі": f_df = f_df[f_df['Категорія'] == sel_cat]
    if search: f_df = f_df[f_df['Назва'].str.contains(search, case=False) | f_df['Артикул'].str.contains(search, case=False)]

    # Сортування (враховуємо Цена/Ціна)
    p_col = 'Цена' if 'Цена' in df.columns else 'Ціна'
    if "Ціна" in sort_opt:
        f_df['p_num'] = f_df[p_col].apply(lambda x: float(str(x).replace(',','.')) if x else 0)
        f_df = f_df.sort_values('p_num', ascending=("низька" in sort_opt))
    else: f_df = f_df.iloc[::-1]

    items = f_df.to_dict('records')
    for i in range(0, len(items), 3):
        cols_ui = st.columns(3)
        for j, item in enumerate(items[i:i+3]):
            with cols_ui[j]:
                is_promo = "Акція" in item.get('Категорія', '')
                card_style = "product-card special-offer" if is_promo else "product-card"
                
                st.markdown(f"<div class='{card_style}'>", unsafe_allow_html=True)
                st.image(item.get('Фото', "https://via.placeholder.com/150"), use_container_width=True)
                if is_promo: st.caption("🔥 ТОВАР ДНЯ / АКЦІЯ")
                st.subheader(item['Назва'])
                
                with st.expander("📖 Опис товару"):
                    st.write(item.get('Опис', 'Якісний продукт від Food Festival'))
                
                # Розрахунок ціни зі знижкою
                p_raw = float(str(item.get(p_col, '0')).replace(',', '.'))
                disc = float(str(u.get('Знижка', '0')).replace('%','')) / 100
                final_p = p_raw * (1 - disc)
                
                st.markdown(f"### {final_p:g} ₴")
                
                # Перевірка залишків (Остаток_Тек)
                try: stock = float(str(item.get('Остаток_Тек', '0')).replace(',', '.'))
                except: stock = 0

                if stock > 0:
                    qty = st.number_input("К-сть", min_value=0.0, step=1.0, key=f"q_{item['Артикул']}")
                    if st.button("➕ В кошик", key=f"b_{item['Артикул']}", use_container_width=True):
                        if qty > 0:
                            st.session_state.cart[item['Назва']] = {'qty': qty, 'price': final_p, 'art': item['Артикул']}
                            st.toast(f"✅ Додано: {item['Назва']}")
                else:
                    st.error("⌛ Очікується")
                    st.button("Немає в наявності", key=f"off_{item['Артикул']}", disabled=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 🛒 КОШИК (АВТО-АДРЕСА + МЕНЕДЖЕР)
# ==========================================
def show_cart(u):
    st.title("🛒 Ваше Замовлення")
    
    # Завантажуємо історію для автопідтягування
    orders_df = load_data(CONFIG["ORDERS_URL"])
    last_addr, last_fop = "", ""
    if orders_df is not None:
        my = orders_df[orders_df['Телефон'] == u['Телефон']]
        if not my.empty:
            last_addr = my.iloc[-1].get('Адреса', '')
            last_fop = my.iloc[-1].get('ФОП_Клієнта', '')

    if not st.session_state.cart:
        st.info("Кошик порожній.")
        return

    total = sum(d['qty'] * d['price'] for d in st.session_state.cart.values())
    
    # Перевірка мінімалки 1000 грн
    if total < CONFIG["MIN_ORDER"]:
        st.warning(f"⚠️ Додайте ще на **{CONFIG['MIN_ORDER'] - total:g} ₴** для доставки.")
    else: st.success(f"✅ Сума: {total:g} ₴ (Мінімальне замовлення набрано)")

    # Список товарів
    for name, d in list(st.session_state.cart.items()):
        c1, c2, c3 = st.columns([3, 1, 0.5])
        sub = d['qty'] * d['price']
        c1.write(f"**{name}**")
        c2.write(f"{d['qty']} шт | {sub:g} ₴")
        if c3.button("❌", key=f"del_{name}"):
            del st.session_state.cart[name]; st.rerun()

    st.divider()
    
    # ДАНІ ПРОДАВЦЯ ТА ПОКУПЦЯ
    active_our_fop = get_active_fop()
    st.info(f"🏢 Постачальник: **{active_our_fop}**")
    
    client_legal_name = st.text_input("📝 Ваш ФОП / Назва закладу:", value=last_fop)
    addr = st.text_input("📍 Адреса доставки:", value=last_addr)
    
    # Дата (правило 11:00)
    min_d = date.today()
    if datetime.now().hour >= 11: min_d += timedelta(days=1)
    delivery_date = st.date_input("📅 Дата доставки:", min_value=min_d, value=min_d)
    
    comm = st.text_area("💬 Коментар оператору:")

    if st.button("🚀 ПІДТВЕРДИТИ ЗАМОВЛЕННЯ", use_container_width=True, disabled=(total < CONFIG["MIN_ORDER"])):
        manager = u.get('Менеджер', 'Без менеджера')
        items_txt = "; ".join([f"{n} ({d['qty']} шт)" for n, d in st.session_state.cart.items()])
        
        # ТЕКСТ ДЛЯ ТЕЛЕГРАМ
        msg = (
            f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ</b>\n"
            f"👨‍💼 Менеджер: <b>{manager}</b>\n"
            f"🏢 Наш ФОП: <b>{active_our_fop}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Клієнт: {u['Назва']}\n"
            f"📝 ФОП Клієнта: {client_legal_name}\n"
            f"📞 Тел: {u['Телефон']}\n"
            f"📍 Адреса: {addr}\n"
            f"📅 Дата доставки: {delivery_date.strftime('%d.%m.%Y')}\n"
            f"💰 <b>СУМА: {total:g} ₴</b>\n"
            f"🛒 Товари: {items_txt}\n"
            f"💬 {comm}"
        )
        
        # Відправка
        url_tg = f"https://api.telegram.org/bot{CONFIG['TG_TOKEN']}/sendMessage"
        requests.post(url_tg, data={"chat_id": CONFIG["GROUP_ID"], "text": msg, "parse_mode": "HTML"})
        
        # Запис в таблицю
        requests.post(CONFIG["SCRIPT_URL"], json={
            "type": "NEW_ORDER", "phone": u['Телефон'], "client": u['Назва'],
            "total": total, "items": items_txt, "address": addr, "manager": manager,
            "fop_client": client_legal_name, "fop_our": active_our_fop
        })
        
        st.session_state.cart = {}
        st.success("✅ Надіслано! Оператор вже обробляє замовлення.")
        st.balloons()

# ... ( show_login та main() - залишаються стандартними )

if __name__ == "__main__":
    # Тут логіка авторизації та меню
    pass
