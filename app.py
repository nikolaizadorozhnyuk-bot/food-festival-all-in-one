import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, date

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
    try: 
        df = pd.read_csv(url, dtype=str).fillna('')
        df.columns = df.columns.str.strip()
        return df
    except: return None

# --- КОШИК ---
def show_cart(u):
    st.title("🛒 Ваше замовлення")
    if not st.session_state.cart:
        st.info("Кошик порожній. Оберіть товари в каталозі.")
        return

    total = 0
    items_txt = ""
    
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
            st.write(f"**{name}**")
            st.caption(f"{data['price']:g} ₴/од.")
        with c2:
            st.write(f"{data['qty']:g}")
        with c3:
            if st.button("❌", key=f"del_{i}"):
                del st.session_state.cart[name]
                st.rerun()
        
        # Красиво форматуємо товари для Телеграму в стовпчик
        items_txt += f"• {name} - {data['qty']:g} шт.\n"

    st.divider()
    st.subheader(f"💰 Разом до сплати: {total:g} ₴")
    st.markdown("---")
    
    # === НОВИЙ БЛОК: КАЛЕНДАР ТА ДОСТАВКА ===
    st.subheader("🚚 Дані доставки")
    
    c_date, c_deliv = st.columns(2)
    with c_date:
        # Мінімальна дата — завжди завтра
        tomorrow = date.today() + timedelta(days=1)
        delivery_date = st.date_input("📅 Бажана дата доставки:", min_value=tomorrow, value=tomorrow)
    
    with c_deliv:
        deliv = st.selectbox("🚚 Спосіб отримання:", ["Доставка Food Festival", "Самовивіз"])
    
    addr = st.text_input("📍 Адреса доставки (обов'язково для доставки):")
    st.markdown("---")
    
    if st.button("🚀 ВІДПРАВИТИ ЗАМОВЛЕННЯ", use_container_width=True):
        if not addr and deliv != "Самовивіз":
            st.error("Вкажіть адресу для доставки!")
            return
        
        date_str = delivery_date.strftime("%d.%m.%Y")
        
        # Красиве повідомлення в Telegram
        msg = (
            f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ!</b>\n"
            f"👤 <b>Клієнт:</b> {u['Назва']}\n"
            f"📞 <b>Телефон:</b> {u['Телефон']}\n"
            f"📅 <b>Дата на коли:</b> {date_str}\n"
            f"🚚 <b>Спосіб:</b> {deliv}\n"
            f"📍 <b>Адреса:</b> {addr if addr else 'Самовивіз'}\n"
            f"💰 <b>Сума:</b> {total:g} ₴\n\n"
            f"🛒 <b>ТОВАРИ:</b>\n{items_txt}"
        )
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": GROUP_ID, "text": msg, "parse_mode": "HTML"})
        
        st.balloons()
        st.session_state.cart = {}
        st.success(f"Замовлення на {date_str} успішно надіслано!")

# --- КАТАЛОГ ---
def show_catalog(u):
    st.title("🍎 Каталог Food Festival")
    df = load_data(SHEET_URL)
    if df is None: 
        st.error("Не вдалося завантажити дані таблиці.")
        return

    # Формуємо список категорій, ховаємо сміття, додаємо Акції
    all_cats = sorted([str(c) for c in df['Категорія'].unique() if str(c).strip()])
    if "000 Мусор" in all_cats: 
        all_cats.remove("000 Мусор")
    
    categories = ["🔥 АКЦІЙНІ ТОВАРИ", "Всі"] + all_cats
    
    c1, c2 = st.columns([1, 2])
    with c1: sel_cat = st.selectbox("📁 Категорія:", categories)
    with c2: search = st.text_input("🔍 Пошук товару:")

    # === БАНЕР ДЛЯ СВІЖОГО М'ЯСА ===
    if sel_cat == "Свіже м'ясо":
        st.warning(
            "🥩 **УВАГА: Спеціальні умови замовлення на СВІЖЕ М'ЯСО!**\n\n"
            "🚛 **Можливі дні постачання:** Вівторок, Середа, Четвер, П'ятниця, Субота.\n"
            "⏳ **Передзамовлення:** Суворо за **2 дні** до бажаного дня постачання."
        )
        st.divider()

    f_df = df
    
    # ЛОГІКА АКЦІЙ ТА ФІЛЬТРАЦІЯ
    if sel_cat == "🔥 АКЦІЙНІ ТОВАРИ":
        f_df = f_df[f_df['Опис (укр)'].str.contains('АКЦІЯ|акція', case=False, na=False)]
        if f_df.empty:
            st.warning("Наразі акційних товарів немає. Заходьте пізніше!")
            return
    elif sel_cat != "Всі":
        f_df = f_df[f_df['Категорія'] == sel_cat]

    if sel_cat != "🔥 АКЦІЙНІ ТОВАРИ":
        f_df = f_df[f_df['Категорія'] != "000 Мусор"]

    if search: f_df = f_df[f_df['Назва'].str.contains(search, case=False, na=False)]

    # ВИВІД КАРТОК
    for idx, row in f_df.iterrows():
        with st.container():
            col_img, col_txt = st.columns([1, 2])
            with col_img:
                img = str(row.get('Фото', '')).strip()
                if img.startswith('http'): st.image(img, use_container_width=True)
                else: st.image("https://via.placeholder.com/300?text=Food+Festival", use_container_width=True)
            
            with col_txt:
                # ВОГНИК для акційних товарів
                is_promo = 'акція' in str(row.get('Опис (укр)', '')).lower()
                display_name = f"🔥 {row.get('Назва', 'Без назви')}" if is_promo else row.get('Назва', 'Без назви')
                st.subheader(display_name)
                
                # Чистимо опис від технічної мітки
                if row.get('Опис (укр)'): 
                    clean_desc = str(row['Опис (укр)']).replace('! АКЦІЯ', '').strip()
                    if clean_desc: st.info(clean_desc)
                
                try:
                    price_str = str(row.get('Ціна', '0')).replace(',', '.').strip()
                    price = float(price_str) if price_str else 0.0
                except ValueError:
                    price = 0.0
                
                st.write(f"💰 Ціна: **{price:g} ₴**")
                
                art = str(row.get('upc', 'no_art')).strip()
                qty = st.number_input("Кількість", min_value=0.0, step=1.0, key=f"q_{art}_{idx}")
                
                if qty > 0:
                    st.session_state.cart[row['Назва']] = {'qty': qty, 'price': price, 'art': art, 'category': row.get('Категорія', '')}
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
                st.session_state.user_info = {'Назва': 'Микола (Власник)', 'Телефон': ph}
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
        page = st.sidebar.radio("Меню", ["🍎 Каталог", "🛒 Кошик"])
        if page == "🍎 Каталог": show_catalog(st.session_state.user_info)
        else: show_cart(st.session_state.user_info)
        if st.sidebar.button("Вийти"):
            st.session_state.logged_in = False
            st.rerun()

if __name__ == "__main__":
    main()
