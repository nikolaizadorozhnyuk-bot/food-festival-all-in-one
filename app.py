import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta, date

# --- НАЛАШТУВАННЯ ---
CONFIG = {
    "OWNER_PHONE": "0675953220",
    "LOGO_URL": "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png",
    "SCRIPT_URL": "https://script.google.com/macros/s/AKfycbydqJM4x7127JAMFU98FAIp3Cwown0QJgPix4iAtFVtXrTQzngWjNF3qkcWEUBi4OIq/exec",
    "CATALOG_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=1701329272&single=true&output=csv",
    "CLIENTS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
}

st.set_page_config(page_title="Food Festival Замовлення", page_icon=CONFIG["LOGO_URL"], layout="wide")

@st.cache_data(ttl=60)
def load_data(url):
    try: return pd.read_csv(url, dtype=str).fillna('').apply(lambda x: x.str.strip())
    except: return None

def safe_float(val):
    try: return float(str(val).replace(',', '.').replace(' ', ''))
    except: return 0.0

def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.image(CONFIG["LOGO_URL"], width=250)
        st.subheader("Вхід в систему")
        ph = st.text_input("Введіть ваш номер телефону")
        if st.button("Увійти", type="primary"):
            if ph == CONFIG["OWNER_PHONE"]:
                st.session_state.logged_in, st.session_state.user = True, {'Назва': 'Власник', 'Телефон': ph, 'Менеджер': 'Admin'}
                st.rerun()
            df_c = load_data(CONFIG["CLIENTS_URL"])
            if df_c is not None:
                user = df_c[df_c['Телефон'] == ph]
                if not user.empty:
                    st.session_state.logged_in, st.session_state.user = True, user.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Користувача не знайдено.")
    else:
        st.sidebar.title(f"👋 {st.session_state.user['Назва']}")
        page = st.sidebar.radio("Меню", ["🍎 Каталог", "🛒 Кошик"])
        if page == "🍎 Каталог": show_catalog()
        else: show_cart()
        if st.sidebar.button("Вийти"):
            st.session_state.logged_in = False
            st.rerun()

def show_catalog():
    st.title("🍎 Асортимент")
    df = load_data(CONFIG["CATALOG_URL"])
    if df is None: return
    
    search = st.text_input("🔍 Пошук товару")
    cats = ["Всі"] + sorted(df['Категорія'].unique().tolist())
    sel_cat = st.selectbox("📂 Категорія", cats)

    f_df = df
    if sel_cat != "Всі": f_df = f_df[f_df['Категорія'] == sel_cat]
    if search: f_df = f_df[f_df['Назва'].str.contains(search, case=False)]

    for _, r in f_df.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([1, 3])
            col1.image(r['Фото'] if 'http' in r['Фото'] else "https://via.placeholder.com/150")
            price = safe_float(r['Ціна'])
            col2.subheader(r['Назва'])
            col2.write(f"💵 **{price:g} ₴**")
            
            q_key = f"q_{r['upc']}"
            qty = col2.number_input("Кількість", min_value=0.0, step=1.0, key=q_key)
            if col2.button("Додати в кошик", key=f"btn_{r['upc']}"):
                if qty > 0:
                    st.session_state.cart[r['Назва']] = {'qty': qty, 'price': price}
                    st.toast(f"✅ Додано!")

def show_cart():
    st.title("🛒 Кошик")
    if not st.session_state.cart:
        st.info("Кошик порожній")
        return
    
    total = sum(d['qty'] * d['price'] for d in st.session_state.cart.values())
    for name, d in st.session_state.cart.items():
        st.write(f"• **{name}** — {d['qty']} шт x {d['price']:g} ₴")
    
    st.markdown(f"### 💰 Разом: **{total:g} ₴**")
    
    deliv_date = st.date_input("📅 Дата доставки", min_value=date.today() + timedelta(days=1))
    addr = st.text_input("📍 Точна адреса доставки (Одеса)", value=st.session_state.user.get('Адреса', ''))
    comment = st.text_area("💬 Коментар")

    if st.button("🚀 ВІДПРАВИТИ ЗАМОВЛЕННЯ", use_container_width=True, type="primary"):
        items_txt = "; ".join([f"{n} ({d['qty']} шт)" for n, d in st.session_state.cart.items()])
        payload = {
            "type": "NEW_ORDER",
            "phone": st.session_state.user['Телефон'],
            "client": st.session_state.user['Назва'],
            "total": total,
            "items": items_txt,
            "comment": comment,
            "address": addr,
            "delivery_date": deliv_date.strftime("%d.%m.%Y"),
            "manager": st.session_state.user.get('Менеджер', 'Admin')
        }
        
        try:
            requests.post(CONFIG["SCRIPT_URL"], json=payload)
            st.session_state.cart = {}
            st.success("✅ Замовлення успішно надіслано!")
            st.balloons()
        except:
            st.error("Помилка зв'язку.")

if __name__ == "__main__":
    main()
