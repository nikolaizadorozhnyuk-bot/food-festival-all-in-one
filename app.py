import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ==========================================
# 🔑 НАЛАШТУВАННЯ (FOOD FESTIVAL)
# ==========================================
OWNER_PHONE = "0675953220"
LOGO_URL = "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaFzeDCKyGghOoel888Xx_QkEaYTytH2te1BsJlSlUAqKYg1LyxF0_AwogvNPOU1PX/exec"

# Бази даних (CSV посилання з Google Таблиць)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
NEWS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=374278986&single=true&output=csv"

# Telegram Bot
TELEGRAM_TOKEN = "8183938320:AAHsDhUXcu3ZeKg8Qh3AZc3xbXMa9YqqqZc"
CHAT_ID = "-5236190167"

st.set_page_config(page_title="Food Festival ERP", page_icon=LOGO_URL, layout="wide")

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
@st.cache_data(ttl=30)
def load_data(url):
    try: return pd.read_csv(url, dtype=str).fillna('')
    except: return None

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})
    except: pass

def send_update(payload):
    try: return requests.post(SCRIPT_URL, json=payload, timeout=15).text
    except: return "Error"

# Ініціалізація кошика та авторизації
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- ГОЛОВНА ЛОГІКА ---
def main():
    if not st.session_state.logged_in:
        show_login()
        return

    u = st.session_state.user_info
    role = u.get('Роль', 'Client')
    
    # Брендування зверху
    st.image(LOGO_URL, width=150)
    st.success(f"👤 {u.get('Назва')} | {role}")
    
    # Зручне мобільне меню
    menu = ["🍎 Каталог", "🛒 Кошик", "📰 Новини"]
    if role in ['Owner', 'Admin', 'Manager']:
        menu.append("🔔 Нагадування")
    
    choice = st.selectbox("📍 Навігація:", menu)
    
    if st.button("🚪 Вийти", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    st.divider()

    # Перемикання розділів
    if choice == "🍎 Каталог":
        show_catalog(u)
    elif choice == "🛒 Кошик":
        show_cart(u)
    elif choice == "📰 Новини":
        show_news()
    elif choice == "🔔 Нагадування":
        show_reminders(u)

# --- ФУНКЦІЯ: ВХІД ---
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(LOGO_URL, use_container_width=True)
        st.title("Вхід у систему")
        phone = st.text_input("Введіть номер телефону:")
        if st.button("🚪 Увійти", use_container_width=True):
            if phone == OWNER_PHONE:
                st.session_state.logged_in = True
                st.session_state.user_info = {
                    'Назва': 'ВЛАСНИК', 'Роль': 'Owner', 'Телефон': phone, 
                    'Знижка': '0', 'Колонка прайс': 'Ціна'
                }
                st.rerun()
            
            clients_df = load_data(CLIENTS_URL)
            if clients_df is not None:
                user = clients_df[clients_df['Телефон'].str.strip() == phone.strip()]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("❌ Номер не знайдено. Зв'яжіться з менеджером.")

# --- ФУНКЦІЯ: КАТАЛОГ (з описом) ---
def show_catalog(u):
    df = load_data(SHEET_URL)
    if df is not None:
        st.title("🍎 Асортимент")
        
        # Пошук та категорії
        search = st.text_input("🔍 Пошук товару:")
        cats = ["Усі"] + list(df['Категорія'].unique())
        selected_cat = st.selectbox("📁 Категорія:", cats)

        f_df = df.copy()
        if selected_cat != "Усі": f_df = f_df[f_df['Категорія'] == selected_cat]
        if search: f_df = f_df[f_df['Товар'].str.contains(search, case=False)]
        
        p_col = u.get('Колонка прайс', 'Ціна')
        discount_val = str(u.get('Знижка', '0')).replace('%','')
        discount = float(discount_val) / 100 if discount_val.isdigit() else 0

        for _, row in f_df.iterrows():
            with st.container():
                c1, c2 = st.columns([1, 2])
                with c1: 
                    st.image(row['Фото'] if row['Фото'] else "https://via.placeholder.com/150", use_container_width=True)
                with c2:
                    st.subheader(row['Товар'])
                    
                    # ℹ️ Виведення опису товару, якщо він є
                    if 'Опис' in row and row['Опис']:
                        st.info(f"{row['Опис']}")
                    
                    price_raw = str(row.get(p_col, '0')).replace(',', '.')
                    price = float(price_raw) if price_raw.replace('.','').isdigit() else 0.0
                    final_price = price * (1 - discount)
                    
                    if discount > 0:
                        st.write(f"💰 Ціна: ~~{price:g}~~ **{final_price:g} ₴**")
                    else:
                        st.write(f"💰 Ціна: **{final_price:g} ₴**")
                    
                    qty = st.number_input(f"Замовити (Арт: {row['Артикул']})", min_value=0.0, step=1.0, key=f"q_{row['Артикул']}")
                    if qty > 0:
                        st.session_state.cart[row['Товар']] = {
                            'qty': qty, 'price': final_price, 'art': row['Артикул']
                        }
            st.divider()

# --- ФУНКЦІЯ: КОШИК ---
def show_cart(u):
    st.title("🛒 Ваш кошик")
    if not st.session_state.cart:
        st.info("Кошик порожній.")
    else:
        total = 0
        summary = ""
        for name, data in st.session_state.cart.items():
            cost = data['qty'] * data['price']
            total += cost
            st.write(f"🔹 {name} — {data['qty']} шт. ({cost:g} ₴)")
            summary += f"• {name} ({data['qty']} шт.);\n"
        
        st.subheader(f"Разом до сплати: {total:g} ₴")
        delivery = st.selectbox("Спосіб доставки:", ["Доставка FF", "Нова Пошта", "Самовивіз"])
        addr = st.text_input("Адреса / Номер відділення:")
        comm = st.text_area("Коментар:")
        
        if st.button("🚀 ВІДПРАВИТИ ЗАМОВЛЕННЯ", use_container_width=True):
            order_text = (f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ!</b>\n\n"
                          f"👤 Клієнт: {u['Назва']}\n"
                          f"📞 Тел: {u['Телефон']}\n"
                          f"💰 Сума: {total:g} ₴\n"
                          f"🚚 Доставка: {delivery} ({addr})\n\n"
                          f"🛒 Товари:\n{summary}\n"
                          f"💬 Коментар: {comm}")
            
            # Відправка в Telegram та Google Таблицю
            send_to_telegram(order_text)
            send_update({
                "type": "NEW_ORDER", "phone": u['Телефон'], "client": u['Назва'], 
                "total": total, "items": summary, "comment": comm,
                "delivery_method": delivery, "delivery_address": addr
            })
            
            st.balloons()
            st.success("Дякуємо! Замовлення надіслано.")
            st.session_state.cart = {}

# --- ФУНКЦІЯ: НОВИНИ ---
def show_news():
    st.title("📰 Новини")
    news = load_data(NEWS_URL)
    if news is not None:
        for _, row in news.iloc[::-1].iterrows():
            st.subheader(row.get('Заголовок', 'Подія'))
            st.caption(f"📅 {row.get('Дата', '')}")
            st.write(row.get('Текст новини', ''))
            if row.get('Фото'): st.image(row['Фото'], width=350)
            st.divider()

# --- ФУНКЦІЯ: НАГАДУВАННЯ ---
def show_reminders(u):
    st.title("🔔 Розсилка")
    msg_type = st.radio("Тип сповіщення:", ["Нагадування про замовлення", "Власне повідомлення"])
    
    text_to_send = ""
    if msg_type == "Нагадування про замовлення":
        text_to_send = "👋 <b>Шановні клієнти!</b>\nНагадуємо, що сьогодні ми приймаємо замовлення. Чекаємо на ваші заявки в додатку!"
    else:
        text_to_send = st.text_area("Текст повідомлення:", placeholder="Напишіть тут...")

    if st.button("📤 ВІДПРАВИТИ В ГРУПУ", use_container_width=True):
        if text_to_send:
            send_to_telegram(text_to_send)
            st.success("✅ Надіслано у вашу групу Telegram!")
        else:
            st.warning("Введіть текст!")

if __name__ == "__main__":
    main()
