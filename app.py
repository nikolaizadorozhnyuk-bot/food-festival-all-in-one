import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, date

# --- НАЛАШТУВАННЯ ---
OWNER_PHONE = "0675953220"
LOGO_URL = "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaFzeDCKyGghOoel888Xx_QkEaYTytH2te1BsJlSlUAqKYg1LyxF0_AwogvNPOU1PX/exec"

SHEET_URL = "SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=1701329272&single=true&output=csv""
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=1803359156&single=true&output=csv"

TELEGRAM_TOKEN = "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU"
GROUP_ID = "-1003641918928"

st.set_page_config(page_title="Food Festival", page_icon=LOGO_URL, layout="wide")

# CSS для краси
st.markdown("<style>button[data-testid='stNumberInputStepUp'] { animation: pulse 1.5s infinite; color: red !important; } @keyframes pulse { 0% {transform: scale(1);} 50% {transform: scale(1.1);} 100% {transform: scale(1);} }</style>", unsafe_allow_html=True)

@st.cache_data(ttl=30)
def load_data(url):
    try: return pd.read_csv(url, dtype=str).fillna('').apply(lambda x: x.str.strip())
    except: return None

# --- КОШИК ---
def show_cart(u):
    st.title("🛒 Ваш кошик")
    if not st.session_state.cart:
        st.info("Кошик порожній")
        return
    
    total = 0
    items_txt = ""
    has_meat = any(d.get('category') == "Свіже м'ясо" for d in st.session_state.cart.values())
    
    for name, d in list(st.session_state.cart.items()):
        total += d['qty'] * d['price']
        items_txt += f"• {name} ({d['qty']:g} шт); "
        c1, c2 = st.columns([3, 1])
        with c1: st.write(f"**{name}**\n{d['price']:g} ₴/од.")
        with c2:
            new_q = st.number_input("К-сть", min_value=0.0, value=float(d['qty']), key=f"cart_{name}")
            if new_q != d['qty']:
                if new_q == 0: del st.session_state.cart[name]
                else: st.session_state.cart[name]['qty'] = new_q
                st.rerun()

    st.subheader(f"💰 Разом: {total:g} ₴")
    min_d = date.today() + timedelta(days=2 if has_meat else 1)
    deliv_date = st.date_input("📅 Дата доставки", min_value=min_d, value=min_d)
    addr = st.text_input("📍 Адреса", value=u.get('Адреса', ''))
    
    if st.button("🚀 ПІДТВЕРДИТИ", use_container_width=True):
        manager = u.get('Менеджер', '-')
        req_params = {"p_date": datetime.now().strftime("%d.%m.%Y %H:%M"), "p_phone": u['Телефон'], "p_items": items_txt, "p_sum": total, "p_deliv_date": deliv_date.strftime("%d.%m.%Y"), "p_status": "Нове", "p_manager": manager}
        requests.post(SCRIPT_URL, params=req_params)
        tg_msg = f"🛍 <b>ЗАМОВЛЕННЯ!</b>\n👤 {u['Назва']}\n📞 {u['Телефон']}\n👨‍💼 Менеджер: {manager}\n💰 Сума: {total:g} ₴\n🛒 {items_txt}"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": GROUP_ID, "text": tg_msg, "parse_mode": "HTML"})
        st.session_state.cart = {}
        st.success("Замовлення надіслано!")

# --- КАТАЛОГ ---
def show_catalog(u):
    st.title("🍎 Каталог товарів")
    df = load_data(SHEET_URL)
    if df is None: return

    search = st.sidebar.text_input("🔍 Пошук")
    cats = ["🔥 АКЦІЙНІ ТОВАРИ", "Всі"] + sorted(df['Категорія'].unique().tolist())
    sel_cat = st.sidebar.selectbox("📂 Категорія", cats)

    f_df = df
    if sel_cat == "🔥 АКЦІЙНІ ТОВАРИ": f_df = f_df[f_df['Опис (укр)'].str.contains('акція', case=False)]
    elif sel_cat != "Всі": f_df = f_df[f_df['Категорія'] == sel_cat]
    if search: f_df = f_df[f_df['Назва'].str.contains(search, case=False)]

    for _, r in f_df.iterrows():
        col1, col2 = st.columns([1, 2])
        with col1: st.image(r['Фото'] if 'http' in r['Фото'] else "https://via.placeholder.com/150")
        with col2:
            st.subheader(r['Назва'])
            price = float(r['Ціна'].replace(',', '.'))
            st.write(f"💰 **{price:g} ₴**")
            if r['Опис (укр)']:
                with st.popover("📖 Опис"): st.info(r['Опис (укр)'])
            qty = st.number_input("Кількість", min_value=0.0, step=1.0, key=f"q_{r['upc']}")
            if qty > 0: st.session_state.cart[r['Назва']] = {'qty': qty, 'price': price, 'category': r['Категорія']}
        st.divider()

def show_history(u):
    st.title("📜 Історія замовлень")
    df = load_data(ORDERS_URL)
    if df is not None:
        my = df[df['Телефон'] == str(u['Телефон'])].iloc[::-1]
        for _, r in my.iterrows():
            with st.expander(f"📦 {r['Дата']} | {r['Сума']} ₴ | {r['Статус замовлення']}"):
                st.write(f"🛒 **Товари:** {r['Товари']}")
                st.caption(f"📅 Доставка на: {r['Дата доставки']}")

def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        st.image(LOGO_URL, width=200)
        ph = st.text_input("Ваш номер телефону")
        if st.button("Увійти"):
            if ph == OWNER_PHONE:
                st.session_state.logged_in, st.session_state.user_info = True, {'Назва': 'Микола', 'Телефон': ph, 'Менеджер': 'Admin'}
                st.rerun()
            df_c = load_data(CLIENTS_URL)
            user = df_c[df_c['Телефон'] == ph]
            if not user.empty:
                st.session_state.logged_in, st.session_state.user_info = True, user.iloc[0].to_dict()
                st.rerun()
            else: st.error("Користувача не знайдено")
    else:
        m = st.sidebar.radio("Меню", ["Каталог", "Кошик", "Історія"])
        if m == "Каталог": show_catalog(st.session_state.user_info)
        elif m == "Кошик": show_cart(st.session_state.user_info)
        else: show_history(st.session_state.user_info)
        if st.sidebar.button("Вийти"):
            st.session_state.logged_in = False
            st.rerun()

main()
