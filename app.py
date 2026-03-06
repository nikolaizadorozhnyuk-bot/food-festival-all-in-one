import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, date

# --- КОНФІГУРАЦІЯ ---
CONFIG = {
    "OWNER_PHONE": "0675953220",
    "LOGO_URL": "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png",
    "SCRIPT_URL": "https://script.google.com/macros/s/AKfycbydqJM4x7127JAMFU98FAIp3Cwown0QJgPix4iAtFVtXrTQzngWjNF3qkcWEUBi4OIq/exec",
    "CATALOG_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=1701329272&single=true&output=csv",
    "CLIENTS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
}

st.set_page_config(page_title="Food Festival", page_icon=CONFIG["LOGO_URL"])

@st.cache_data(ttl=60)
def load_data(url):
    try: return pd.read_csv(url, dtype=str).fillna('').apply(lambda x: x.str.strip())
    except: return None

# --- ЛОГІКА ---
def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.image(CONFIG["LOGO_URL"], width=200)
        ph = st.text_input("Ваш номер телефону")
        if st.button("Увійти"):
            if ph == CONFIG["OWNER_PHONE"]:
                st.session_state.logged_in, st.session_state.user = True, {'Назва': 'Власник', 'Телефон': ph, 'Менеджер': 'Admin'}
                st.rerun()
            df_c = load_data(CONFIG["CLIENTS_URL"])
            user = df_c[df_c['Телефон'] == ph] if df_c is not None else None
            if user is not None and not user.empty:
                st.session_state.logged_in, st.session_state.user = True, user.iloc[0].to_dict()
                st.rerun()
            else: st.error("Доступ заборонено")
    else:
        menu = st.sidebar.radio("Меню", ["Каталог", "Кошик"])
        if menu == "Каталог": show_catalog()
        else: show_cart()

def show_catalog():
    st.title("🍎 Каталог")
    df = load_data(CONFIG["CATALOG_URL"])
    if df is None: return
    
    search = st.text_input("🔍 Пошук")
    f_df = df[df['Назва'].str.contains(search, case=False)] if search else df
    
    for _, r in f_df.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([1, 2])
            c1.image(r['Фото'] if 'http' in r['Фото'] else "https://via.placeholder.com/150")
            c2.subheader(r['Назва'])
            price = float(r['Ціна'].replace(',', '.'))
            c2.write(f"💰 **{price:g} ₴**")
            qty = c2.number_input("К-сть", min_value=0.0, step=1.0, key=f"q_{r['upc']}")
            if c2.button("Додати", key=f"b_{r['upc']}"):
                if qty > 0: st.session_state.cart[r['Назва']] = {'qty': qty, 'price': price, 'upc': r['upc']}
                st.toast("Додано!")

def show_cart():
    st.title("🛒 Кошик")
    if not st.session_state.cart:
        st.info("Пусто")
        return
    
    total = sum(d['qty'] * d['price'] for d in st.session_state.cart.values())
    st.subheader(f"Разом: {total:g} ₴")
    
    addr = st.text_input("📍 Адреса доставки (Одеса)", value=st.session_state.user.get('Адреса', ''))
    comm = st.text_area("💬 Коментар")
    
    if st.button("🚀 ПІДТВЕРДИТИ", use_container_width=True, type="primary"):
        items = "; ".join([f"{n} ({d['qty']} шт)" for n, d in st.session_state.cart.items()])
        payload = {
            "type": "NEW_ORDER", "phone": st.session_state.user['Телефон'],
            "client": st.session_state.user['Назва'], "total": total,
            "items": items, "comment": comm, "address": addr,
            "delivery_date": (date.today() + timedelta(days=1)).strftime("%d.%m.%Y"),
            "manager": st.session_state.user.get('Менеджер', 'Admin')
        }
        requests.post(CONFIG["SCRIPT_URL"], json=payload)
        st.session_state.cart = {}
        st.success("Надіслано!")
        st.balloons()

if __name__ == "__main__": main()
