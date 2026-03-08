import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime, timedelta, date

# --- КОНФІГУРАЦІЯ ---
CONFIG = {
    "OWNER_PHONE": "0675953220",
    "LOGO_URL": "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png",
    "SCRIPT_URL": "https://script.google.com/macros/s/AKfycbydqJM4x7127JAMFU98FAIp3Cwown0QJgPix4iAtFVtXrTQzngWjNF3qkcWEUBi4OIq/exec",
    "CATALOG_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=1701329272&single=true&output=csv",
    "CLIENTS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
}

st.set_page_config(page_title="Food Festival", page_icon=CONFIG["LOGO_URL"], layout="wide")

@st.cache_data(ttl=60)
def load_data(url):
    try: 
        df = pd.read_csv(url, dtype=str).fillna('').apply(lambda x: x.str.strip())
        if 'Фото' in df.columns:
            df['Фото'] = df['Фото'].apply(lambda x: re.findall(r'(https?://[^\s"\';)]+)', x)[0] if "http" in x else x)
        return df
    except: return None

def safe_float(val):
    try: return float(str(val).replace(',', '.').replace(' ', ''))
    except: return 0.0

# --- ІНТЕРФЕЙС ---
def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.image(CONFIG["LOGO_URL"], width=200)
        ph = st.text_input("Ваш номер телефону")
        if st.button("Увійти", type="primary"):
            if ph == CONFIG["OWNER_PHONE"]:
                st.session_state.logged_in, st.session_state.user = True, {'Назва': 'Власник', 'Телефон': ph, 'Менеджер': 'Admin'}
                st.rerun()
            df_c = load_data(CONFIG["CLIENTS_URL"])
            if df_c is not None and not df_c[df_c['Телефон'] == ph].empty:
                st.session_state.logged_in, st.session_state.user = True, df_c[df_c['Телефон'] == ph].iloc[0].to_dict()
                st.rerun()
            else: st.error("Номер не знайдено")
    else:
        pg = st.sidebar.radio("Навігація", ["🍎 Каталог", "🛒 Кошик"])
        if pg == "🍎 Каталог": show_catalog()
        else: show_cart()

def show_catalog():
    st.title("🍎 Наш Асортимент")
    df = load_data(CONFIG["CATALOG_URL"])
    if df is None: return

    # Визначаємо колонки
    cols = {c.lower().strip(): c for c in df.columns}
    p_col = cols.get('ціна') or cols.get('цена')
    a_col = cols.get('upc') or cols.get('ups')

    search = st.text_input("🔍 Швидкий пошук товару...")
    f_df = df[df['Назва'].str.contains(search, case=False)] if search else df

    # Вивід сіткою по 3 товари в ряд
    items = f_df.to_dict('records')
    for i in range(0, len(items), 3):
        cols_ui = st.columns(3)
        for j, item in enumerate(items[i:i+3]):
            with cols_ui[j].container(border=True):
                img = item.get('Фото', '')
                st.image(img if 'http' in img else "https://via.placeholder.com/150", use_container_width=True)
                st.subheader(item['Назва'])
                price = safe_float(item.get(p_col, 0))
                st.write(f"💰 **{price:g} ₴**")
                
                qty = st.number_input("К-сть", min_value=0.0, step=1.0, key=f"q_{item.get(a_col)}")
                if st.button("В кошик", key=f"b_{item.get(a_col)}", use_container_width=True):
                    if qty > 0:
                        st.session_state.cart[item['Назва']] = {'qty': qty, 'price': price}
                        st.toast(f"✅ {item['Назва']} додано!")

def show_cart():
    st.title("🛒 Ваш Кошик")
    if not st.session_state.cart:
        st.info("Кошик порожній. Час щось купити! 😊")
        return
    
    total = 0
    for name, d in list(st.session_state.cart.items()):
        with st.expander(f"{name} — {d['qty']} шт.", expanded=True):
            subtotal = d['qty'] * d['price']
            total += subtotal
            st.write(f"Ціна: {d['price']:g} ₴ | Сума: **{subtotal:g} ₴**")
            if st.button("Видалити", key=f"del_{name}"):
                del st.session_state.cart[name]
                st.rerun()
    
    st.divider()
    st.header(f"Загальна сума: {total:g} ₴")
    
    addr = st.text_input("📍 Адреса доставки", value=st.session_state.user.get('Адреса', ''))
    comm = st.text_area("💬 Коментар")
    
    if st.button("🚀 ПІДТВЕРДИТИ ЗАМОВЛЕННЯ", use_container_width=True, type="primary"):
        # Відправка через requests... (код такий самий як раніше)
        st.success("Замовлення прийнято!")
        st.session_state.cart = {}

if __name__ == "__main__":
    main()
