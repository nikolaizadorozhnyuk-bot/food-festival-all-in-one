import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ==========================================
# 🔑 НАЛАШТУВАННЯ
# ==========================================
OWNER_PHONE = "0675953220"
LOGO_URL = "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaFzeDCKyGghOoel888Xx_QkEaYTytH2te1BsJlSlUAqKYg1LyxF0_AwogvNPOU1PX/exec"

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"

TELEGRAM_TOKEN = "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU"
GROUP_ID = "-1003641918928"

st.set_page_config(page_title="Food Festival", page_icon=LOGO_URL, layout="wide")

@st.cache_data(ttl=30)
def load_data(url):
    try: return pd.read_csv(url, dtype=str).fillna('')
    except: return None

# --- ЛОГІКА КОШИКА (БЕЗ ОПИСІВ) ---
def show_cart(u):
    st.title("🛒 Ваше замовлення")
    if not st.session_state.cart:
        st.info("Кошик порожній. Оберіть товари в каталозі.")
        return

    total = 0
    items_txt = ""
    
    # Заголовок таблиці кошика
    col_h1, col_h2, col_h3 = st.columns([3, 1, 1])
    col_h1.caption("Товар")
    col_h2.caption("К-сть")
    col_h3.caption("Видалити")
    st.divider()

    for i, (name, data) in enumerate(list(st.session_state.cart.items())):
        line_sum = data['qty'] * data['price']
        total += line_sum
        
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            st.write(f"**{name}**") # Тільки назва, без опису!
            st.caption(f"{data['price']:g} ₴/од.")
        with c2:
            st.write(f"{data['qty']:g}")
        with c3:
            if st.button("❌", key=f"del_{i}"):
                del st.session_state.cart[name]
                st.rerun()
        items_txt += f"{name} ({data['qty']} шт.); "

    st.divider()
    st.subheader(f"💰 Разом до сплати: {total:g} ₴")
    
    addr = st.text_input("📍 Адреса доставки (місто, вулиця, будинок):")
    deliv = st.selectbox("🚚 Спосіб отримання:", ["Доставка Food Festival", "Самовивіз"])
    
    if st.button("🚀 ВІДПРАВИТИ ЗАМОВЛЕННЯ", use_container_width=True):
        if not addr and deliv != "Самовивіз":
            st.error("Будь ласка, вкажіть адресу доставки!")
            return
            
        manager = str(u.get('Менеджер', 'Микола')).strip()
        delivery_time = "СЬОГОДНІ" if datetime.now().hour < 11 else "ЗАВТРА"
        
        msg = (f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ!</b>\n⏰ Доставка на {delivery_time}\n"
               f"👤 {u['Назва']}\n📞 {u['Телефон']}\n💰 Сума: {total:g} ₴\n"
               f"🚚 {deliv}: {addr}\n🛒 {items_txt}")
        
        # Надсилаємо в Telegram
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": GROUP_ID, "text": msg, "parse_mode": "HTML"})
        
        # Надсилаємо в Google Таблицю
        requests.post(SCRIPT_URL, json={
            "type": "NEW_ORDER", "phone": u['Телефон'], "client": u['Назва'], 
            "total": total, "items": items_txt, "address": addr
        })
        
        st.balloons()
        st.success("✅ Замовлення успішно надіслано! Менеджер зв'яжеться з вами.")
        st.session_state.cart = {}
        # st.rerun() # Можна розкоментувати для очищення екрану після замовлення

# --- КАТАЛОГ (З ПРАВИЛЬНИМИ ФОТО ТА НАЗВАМИ) ---
def show_catalog(u):
    st.title("🍎 Каталог Food Festival")
    df = load_data(SHEET_URL)
    if df is None: return

    # Фільтри
    cats = ["Всі"] + sorted(list(df['Категорія'].unique()))
    c1, c2 = st.columns([1, 2])
    with c1: sel_cat = st.selectbox("📁 Категорія:", cats)
    with c2: search = st.text_input("🔍 Пошук товару:")

    f_df = df
    if sel_cat != "Всі": f_df = f_df[f_df['Категорія'] == sel_cat]
    if search: f_df = f_df[f_df['Назва'].str.contains(search, case=False)]

    for idx, row in f_df.iterrows():
        with st.container():
            col_img, col_txt = st.columns([1, 2])
            with col_img:
                img = str(row.get('Фото', '')).strip()
                # Примусово перевіряємо посилання
                if img.startswith('http'): st.image(img, use_container_width=True)
                else: st.image("https://via.placeholder.com/300?text=Food+Festival", use_container_width=True)
            
            with col_txt:
                st.subheader(row['Назва']) # Нова назва (перекладена ШІ)
                if row.get('Опис (укр)'): st.info(row['Опис (укр)']) # Опис тільки тут
                
                price = float(str(row.get('Ціна', '0')).replace(',', '.'))
                st.write(f"💰 Ціна: **{price:g} ₴**")
                
                # Унікальний ключ для кнопки
                key = f"btn_{row['upc']}_{idx}"
                qty = st.number_input("Кількість", min_value=0.0, step=1.0, key=key)
                if qty > 0:
                    st.session_state.cart[row['Назва']] = {'qty': qty, 'price': price, 'art': row['upc']}
        st.divider()

# --- ВХІД ---
def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.image(LOGO_URL, width=200)
        ph = st.text_input("Введіть номер телефону:")
        if st.button("Увійти"):
            if ph == OWNER_PHONE:
                st.session_state.logged_in = True
                st.session_state.user_info = {'Назва': 'Микола (Власник)', 'Телефон': ph, 'Роль': 'Admin'}
                st.rerun()
            df_c = load_data(CLIENTS_URL)
            if df_c is not None:
                user = df_c[df_c['Телефон'] == ph]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Користувача не знайдено.")
    else:
        u = st.session_state.user_info
        page = st.sidebar.radio("Меню", ["🍎 Каталог", "🛒 Кошик"])
        if page == "🍎 Каталог": show_catalog(u)
        else: show_cart(u)
        if st.sidebar.button("Вийти"):
            st.session_state.logged_in = False
            st.rerun()

if __name__ == "__main__":
    main()
