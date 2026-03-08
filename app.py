import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime, timedelta, date

# ==========================================
# 🔑 КОНФІГУРАЦІЯ
# ==========================================
CONFIG = {
    "LOGO_URL": "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png",
    "CATALOG_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv",
    "CLIENTS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv",
    "ORDERS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv",
    "SETTINGS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=295620790&single=true&output=csv",
    "NEWS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=374278986&single=true&output=csv",
    "SCRIPT_URL": "https://script.google.com/macros/s/AKfycbyaFzeDCKyGghOoel888Xx_QkEaYTytH2te1BsJlSlUAqKYg1LyxF0_AwogvNPOU1PX/exec",
    "TG_TOKEN": "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU",
    "GROUP_ID": "-1003641918928",
    "MIN_ORDER": 1000,
    "OWNER_PHONE": "0675953220"
}

st.set_page_config(page_title="Food Festival ERP", page_icon=CONFIG["LOGO_URL"], layout="wide")

st.markdown("""
    <style>
    .product-card { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #f0f0f0; margin-bottom: 25px; min-height: 550px; }
    .special-offer { border: 3px solid #D4AC0D !important; background: #FFFDF9 !important; }
    div.stButton > button { background-color: #D4AC0D !important; color: white !important; border-radius: 12px !important; font-weight: bold !important; height: 50px; width: 100%; border: none !important; }
    .status-alert { padding: 12px; border-radius: 12px; text-align: center; font-weight: bold; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=30)
def load_data(url):
    try:
        df = pd.read_csv(url, dtype=str).fillna('')
        if 'Фото' in df.columns:
            df['Фото'] = df['Фото'].apply(lambda x: re.findall(r'(https?://[^\s"\';)]+)', str(x))[0] if "http" in str(x) else "")
        return df
    except: return None

def get_active_fop():
    df_set = load_data(CONFIG["SETTINGS_URL"])
    if df_set is not None and not df_set.empty:
        active = df_set[df_set['Статус'].str.contains('Актив', case=False)]
        if not active.empty: return active.iloc[0]['Назва ФОП']
    return "ФОП Food Festival"

def show_catalog(u):
    st.title("🍽️ Меню Food Festival")
    df = load_data(CONFIG["CATALOG_URL"])
    if df is None: return

    cols = {c.lower().strip(): c for c in df.columns}
    name_col = cols.get('назва') or cols.get('товар') or 'Назва'
    art_col = cols.get('артикул') or cols.get('upc') or 'Артикул'
    p_col_sys = cols.get('ціна') or cols.get('цена') or 'Цена'
    stock_col = cols.get('остаток_тек') or cols.get('залишок') or 'Остаток_Тек'

    c1, c2, c3 = st.columns([2, 1, 1])
    search = c1.text_input("🔍 Швидкий пошук...")
    cats = ["Всі"] + sorted(df['Категорія'].unique().tolist()) if 'Категорія' in df.columns else ["Всі"]
    sel_cat = c2.selectbox("📂 Категорія", cats)
    sort_opt = c3.selectbox("⚖️ Сортувати", ["Новинки", "Дешевші", "Дорожчі"])

    f_df = df.copy()
    if sel_cat != "Всі": f_df = f_df[f_df['Категорія'] == sel_cat]
    if search: f_df = f_df[f_df[name_col].str.contains(search, case=False) | f_df[art_col].str.contains(search, case=False)]

    items = f_df.to_dict('records')
    for i in range(0, len(items), 3):
        cols_ui = st.columns(3)
        for j, item in enumerate(items[i:i+3]):
            with cols_ui[j]:
                is_promo = "Акція" in item.get('Категорія', '')
                card_class = "product-card special-offer" if is_promo else "product-card"
                
                st.markdown(f"<div class='{card_class}'>", unsafe_allow_html=True)
                
                # --- ВИПРАВЛЕНИЙ БЛОК ФОТО ---
                img_path = str(item.get('Фото', '')).strip()
                if not img_path.startswith('http'):
                    img_path = "https://via.placeholder.com/150"
                st.image(img_path, use_container_width=True)
                # -----------------------------

                st.subheader(item[name_col])
                with st.expander("📖 Опис продукту"):
                    st.write(item.get('Опис', 'Смачно та якісно.'))
                
                p_user = u.get('Колонка прайс')
                final_p_col = p_user if p_user in item else p_col_sys
                try:
                    p_raw = float(str(item.get(final_p_col, '0')).replace(',', '.'))
                    disc = float(str(u.get('Знижка', '0')).replace('%','')) / 100
                    final_p = p_raw * (1 - disc)
                except: final_p = 0.0
                
                st.markdown(f"### {final_p:g} ₴")
                
                try: stock = float(str(item.get(stock_col, '0')).replace(',', '.'))
                except: stock = 0
                
                if stock > 0:
                    qty = st.number_input("К-сть", min_value=0.0, step=1.0, key=f"q_{item[art_col]}")
                    if st.button("➕ В кошик", key=f"b_{item[art_col]}"):
                        if qty > 0:
                            st.session_state.cart[item[name_col]] = {'qty': qty, 'price': final_p, 'art': item[art_col]}
                            st.toast(f"✅ Додано!")
                else:
                    st.error("⌛ Очікується")
                    st.button("Немає в наявності", key=f"off_{item[art_col]}", disabled=True)
                st.markdown("</div>", unsafe_allow_html=True)

# ... Решта коду (show_cart, show_login, main) залишається як була

def show_cart(u):
    st.title("🛒 Оформлення")
    now = datetime.now()
    cutoff = now.replace(hour=11, minute=0, second=0)
    
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
    
    if total < CONFIG["MIN_ORDER"]:
        st.warning(f"⚠️ Мінімалка 1000 ₴. Додайте ще на {CONFIG['MIN_ORDER'] - total:g} ₴")
    else: st.success(f"✅ Сума замовлення: {total:g} ₴")

    for name, d in list(st.session_state.cart.items()):
        c1, c2, c3 = st.columns([3, 1, 0.5])
        c1.write(f"**{name}**")
        c2.write(f"{d['qty']} шт | {d['qty']*d['price']:g} ₴")
        if c3.button("🗑️", key=f"del_{name}"):
            del st.session_state.cart[name]; st.rerun()

    st.divider()
    active_fop = get_active_fop()
    st.info(f"🏢 Продавець: **{active_fop}**")
    
    c1, c2 = st.columns(2)
    client_fop = c1.text_input("📝 Ваш ФОП:", value=last_fop)
    addr = c2.text_input("📍 Адреса доставки:", value=last_addr)
    
    min_d = date.today()
    if now >= cutoff: min_d += timedelta(days=1)
    d_date = st.date_input("📅 Дата доставки:", min_value=min_d, value=min_d)
    
    if st.button("🚀 ПІДТВЕРДИТИ ЗАМОВЛЕННЯ", use_container_width=True, disabled=(total < CONFIG["MIN_ORDER"])):
        manager = u.get('Менеджер', 'Менеджер')
        items_txt = "; ".join([f"{n} ({d['qty']} шт)" for n, d in st.session_state.cart.items()])
        msg = f"🛍 НОВЕ ЗАМОВЛЕННЯ\n👨‍💼 Менеджер: {manager}\n🏢 Продавець: {active_fop}\n👤 Клієнт: {u['Назва']}\n📍 Адреса: {addr}\n💰 Сума: {total:g} ₴\n🛒 Товари: {items_txt}"
        requests.post(f"https://api.telegram.org/bot{CONFIG['TG_TOKEN']}/sendMessage", data={"chat_id": CONFIG["GROUP_ID"], "text": msg})
        st.session_state.cart = {}
        st.success("Надіслано!")
        st.balloons()

def show_login():
    st.image(CONFIG["LOGO_URL"], width=200)
    ph = st.text_input("Ваш номер телефону:")
    if st.button("Увійти"):
        if ph == CONFIG["OWNER_PHONE"]:
            st.session_state.logged_in, st.session_state.user_info = True, {'Назва': 'ВЛАСНИК', 'Роль': 'Admin', 'Телефон': ph}
            st.rerun()
        df = load_data(CONFIG["CLIENTS_URL"])
        if df is not None:
            user = df[df['Телефон'].str.strip() == ph.strip()]
            if not user.empty:
                st.session_state.logged_in, st.session_state.user_info = True, user.iloc[0].to_dict()
                st.rerun()
            else: st.error("❌ Номер не знайдено.")

def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if not st.session_state.logged_in:
        show_login()
    else:
        u = st.session_state.user_info
        st.sidebar.image(CONFIG["LOGO_URL"], width=150)
        choice = st.sidebar.selectbox("Меню", ["🍽️ Меню", "🛒 Кошик"])
        if st.sidebar.button("Вийти"):
            st.session_state.logged_in = False
            st.rerun()
        if choice == "🍽️ Меню": show_catalog(u)
        elif choice == "🛒 Кошик": show_cart(u)

if __name__ == "__main__":
    main()
