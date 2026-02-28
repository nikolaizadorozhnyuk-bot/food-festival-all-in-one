import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, date

# ==========================================
# 🔑 НАЛАШТУВАННЯ
# ==========================================
OWNER_PHONE = "0675953220"
LOGO_URL = "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbydqJM4x7127JAMFU98FAIp3Cwown0QJgPix4iAtFVtXrTQzngWjNF3qkcWEUBi4OIq/exec"

# URLs твоїх трьох вкладок (переконайся, що вони опубліковані як CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=1803359156&single=true&output=csv"

TELEGRAM_TOKEN = "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU"
GROUP_ID = "-1003641918928"

st.set_page_config(page_title="Food Festival", page_icon=LOGO_URL, layout="wide")

# === МАГІЯ CSS: БІЛЬШІ КНОПКИ ТА ПУЛЬСАЦІЯ ПЛЮСА ===
st.markdown("""
<style>
button[data-testid="stNumberInputStepDown"], 
button[data-testid="stNumberInputStepUp"] {
    transform: scale(1.4);
    margin: 0 10px;
}
@keyframes pulse-plus {
    0% { transform: scale(1.4); }
    50% { transform: scale(1.55); background-color: rgba(255, 75, 75, 0.1); }
    100% { transform: scale(1.4); }
}
button[data-testid="stNumberInputStepUp"] {
    animation: pulse-plus 1.5s infinite;
    color: #ff4b4b !important;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=30)
def load_data(url):
    try: 
        df = pd.read_csv(url, dtype=str).fillna('')
        df.columns = df.columns.str.strip()
        return df
    except: return None

# --- ІСТОРІЯ ЗАМОВЛЕНЬ ---
def show_history(u):
    st.title("📜 Ваші замовлення")
    df_orders = load_data(ORDERS_URL)
    
    if df_orders is None or df_orders.empty:
        st.info("У вас ще немає замовлень.")
        return

    # Фільтруємо замовлення тільки для цього клієнта по телефону
    user_phone = str(u.get('Телефон', '')).strip()
    my_orders = df_orders[df_orders['Телефон'].str.strip() == user_phone]

    if my_orders.empty:
        st.info("Ми не знайшли замовлень, закріплених за вашим номером.")
    else:
        # Показуємо останні замовлення зверху
        for idx, row in my_orders.iloc[::-1].iterrows():
            with st.expander(f"📦 Замовлення від {row['Дата']} — {row['Сума']} ₴"):
                st.write(f"**Статус:** `{row.get('Статус замовлення', 'Обробляється')}`")
                st.write(f"**Товари:** {row['Товари']}")
                st.write(f"**Доставка на:** {row.get('Дата доставки', '-')}")
                st.caption(f"Менеджер: {row.get('Менеджер', '-')}")

# --- КОШИК ---
def show_cart(u):
    st.title("🛒 Кошик")
    if not st.session_state.cart:
        st.info("Кошик порожній.")
        return

    total = 0
    items_txt = ""
    has_meat = any(d.get('category') == "Свіже м'ясо" for d in st.session_state.cart.values())
    
    # Вивід товарів
    for i, (name, data) in enumerate(list(st.session_state.cart.items())):
        total += data['qty'] * data['price']
        items_txt += f"{name} ({data['qty']:g} шт); "
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1: st.write(f"**{name}**")
        with c2:
            new_qty = st.number_input("К-сть", min_value=0.0, value=float(data['qty']), key=f"c_q_{i}", label_visibility="collapsed")
            if new_qty != data['qty']:
                if new_qty == 0: del st.session_state.cart[name]
                else: st.session_state.cart[name]['qty'] = new_qty
                st.rerun()
        with c3:
            if st.button("❌", key=f"c_d_{i}"):
                del st.session_state.cart[name]
                st.rerun()

    st.divider()
    st.subheader(f"💰 Разом: {total:g} ₴")
    
    # Дані доставки
    min_date = date.today() + timedelta(days=2 if has_meat else 1)
    if has_meat: st.warning("🥩 Свіже м'ясо: мінімум 2 дні.")
    
    col1, col2 = st.columns(2)
    with col1: delivery_date = st.date_input("📅 Дата доставки:", min_value=min_date, value=min_date)
    with col2: deliv = st.selectbox("🚚 Спосіб:", ["Доставка Food Festival", "Самовивіз"])
    
    addr = st.text_input("📍 Адреса (для доставки):")
    
    is_valid_day = not (has_meat and delivery_date.weekday() in [0, 6])
    if not is_valid_day: st.error("❌ М'ясо не доставляємо в Нд/Пн.")

    if st.button("🚀 ПІДТВЕРДИТИ ЗАМОВЛЕННЯ", use_container_width=True, disabled=not is_valid_day):
        if not addr and deliv != "Самовивіз":
            st.error("Вкажіть адресу!")
            return

        date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        deliv_str = delivery_date.strftime("%d.%m.%Y")
        manager = u.get('Менеджер', 'Не закріплено')
        client_fop = u.get('Юр_Особа:', '-')
        our_fop = u.get('Наш_ФОП', '-')

        # 1. ЗАПИС У ТАБЛИЦЮ ЧЕРЕЗ APPS SCRIPT
        order_data = {
            "p_date": date_str,
            "p_phone": u['Телефон'],
            "p_items": items_txt,
            "p_sum": total,
            "p_deliv_date": deliv_str,
            "p_status": "Нове",
            "p_manager": manager
        }
        try: requests.post(SCRIPT_URL, data=order_data)
        except: pass

        # 2. ТЕЛЕГРАМ
        msg = (f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ!</b>\n👤 {u['Назва']} ({client_fop})\n📞 {u['Телефон']}\n👨‍💼 Менеджер: {manager}\n🏢 ФОП: {our_fop}\n📅 На коли: {deliv_str}\n💰 Сума: {total:g} ₴\n🛒 {items_txt}")
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": GROUP_ID, "text": msg, "parse_mode": "HTML"})
        
        st.balloons()
        st.session_state.cart = {}
        st.success("Замовлення надіслано!")

# --- КАТАЛОГ ---
def show_catalog(u):
    st.title("🍎 Каталог")
    df = load_data(SHEET_URL)
    if df is None: return

    cats = ["🔥 АКЦІЙНІ ТОВАРИ", "Всі"] + sorted([str(c) for c in df['Категорія'].unique() if str(c).strip() and str(c) != "000 Мусор"])
    c1, c2 = st.columns([1, 2])
    with c1: sel_cat = st.selectbox("📁 Категорія:", cats)
    with c2: search = st.text_input("🔍 Пошук:")

    f_df = df
    if sel_cat == "🔥 АКЦІЙНІ ТОВАРИ":
        f_df = f_df[f_df['Опис (укр)'].str.contains('АКЦІЯ|акція', case=False, na=False)]
    elif sel_cat != "Всі":
        f_df = f_df[f_df['Категорія'] == sel_cat]
    
    if search: f_df = f_df[f_df['Назва'].str.contains(search, case=False, na=False)]

    for idx, row in f_df.iterrows():
        with st.container():
            col_img, col_txt = st.columns([1, 2])
            with col_img:
                img = str(row.get('Фото', '')).strip()
                st.image(img if img.startswith('http') else "https://via.placeholder.com/300?text=Food", use_container_width=True)
            with col_txt:
                is_promo = 'акція' in str(row.get('Опис (укр)', '')).lower()
                st.subheader(f"🔥 {row['Назва']}" if is_promo else row['Назва'])
                raw_desc = str(row.get('Опис (укр)', '')).replace('! АКЦІЯ', '').strip()
                if raw_desc:
                    with st.popover("📖 Читати опис"): st.info(raw_desc)
                price = float(str(row.get('Ціна', '0')).replace(',', '.'))
                st.write(f"💰 Ціна: **{price:g} ₴**")
                art = str(row.get('upc', idx))
                qty = st.number_input("Кількість", min_value=0.0, step=1.0, key=f"q_{art}_{idx}")
                if qty > 0:
                    st.session_state.cart[row['Назва']] = {'qty': qty, 'price': price, 'category': row.get('Категорія', '')}
        st.divider()

# --- ВХІД ТА МЕНЮ ---
def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.image(LOGO_URL, width=200)
        ph = st.text_input("Введіть номер телефону:")
        if st.button("Увійти"):
            if ph == OWNER_PHONE:
                st.session_state.logged_in = True
                st.session_state.user_info = {'Назва': 'Микола (Власник)', 'Телефон': ph, 'Менеджер': 'Сам собі бос'}
                st.rerun()
            df_c = load_data(CLIENTS_URL)
            if df_c is not None:
                user = df_c[df_c['Телефон'].str.strip() == ph.strip()]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Користувача не знайдено.")
    else:
        page = st.sidebar.radio("Меню", ["🍎 Каталог", "🛒 Кошик", "📜 Історія замовлень"])
        if page == "🍎 Каталог": show_catalog(st.session_state.user_info)
        elif page == "🛒 Кошик": show_cart(st.session_state.user_info)
        else: show_history(st.session_state.user_info)
        
        if st.sidebar.button("Вийти"):
            st.session_state.logged_in = False
            st.rerun()

if __name__ == "__main__":
    main()
