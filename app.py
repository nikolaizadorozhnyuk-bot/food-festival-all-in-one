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

# Бази даних (CSV посилання)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
NEWS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=374278986&single=true&output=csv"

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
    try: return requests.post(SCRIPT_URL, json=payload, timeout=10).text
    except: return "Error"

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- ГОЛОВНИЙ ЕКРАН ---
def main():
    if not st.session_state.logged_in:
        show_login()
        return

    u = st.session_state.user_info
    role = u.get('Роль', 'Client')
    
    st.image(LOGO_URL, width=150)
    st.success(f"👤 {u.get('Назва')} | Роль: {role}")
    
    # МЕНЮ НАВІГАЦІЇ
    menu = ["🍎 Каталог", "🛒 Кошик", "📰 Новини"]
    if role in ['Owner', 'Admin', 'Manager']:
        menu.append("🔔 Нагадування")
    
    choice = st.selectbox("📌 Перехід до розділу:", menu)
    
    if st.button("🚪 Вийти", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    st.divider()

    # ВІДОБРАЖЕННЯ РОЗДІЛІВ
    if choice == "🍎 Каталог":
        show_catalog(u)
    elif choice == "🛒 Кошик":
        show_cart(u)
    elif choice == "📰 Новини":
        show_news()
    elif choice == "🔔 Нагадування":
        show_reminders(u)

# --- РОЗДІЛ: ВХІД ---
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(LOGO_URL, use_container_width=True)
        st.title("Вхід у систему")
        phone = st.text_input("Введіть номер телефону:")
        if st.button("🚪 Увійти", use_container_width=True):
            if phone == OWNER_PHONE:
                st.session_state.logged_in = True
                st.session_state.user_info = {'Назва': 'ВЛАСНИК', 'Роль': 'Owner', 'Телефон': phone, 'Знижка': '0', 'Колонка прайс': 'Ціна'}
                st.rerun()
            
            clients_df = load_data(CLIENTS_URL)
            if clients_df is not None:
                user = clients_df[clients_df['Телефон'].str.strip() == phone.strip()]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("❌ Номер не знайдено в базі.")

# --- РОЗДІЛ: КАТАЛОГ ---
def show_catalog(u):
    df = load_data(SHEET_URL)
    if df is not None:
        st.title("🍎 Каталог товарів")
        search = st.text_input("🔍 Швидкий пошук:")
        
        f_df = df[df['Товар'].str.contains(search, case=False)] if search else df
        
        p_col = u.get('Колонка прайс', 'Ціна')
        discount = float(str(u.get('Знижка', '0')).replace('%','')) / 100

        for _, row in f_df.iterrows():
            with st.container():
                c1, c2 = st.columns([1, 2])
                with c1: st.image(row['Фото'] if row['Фото'] else "https://via.placeholder.com/150", use_container_width=True)
                with c2:
                    st.subheader(row['Товар'])
                    price = float(str(row.get(p_col, '0')).replace(',', '.'))
                    final_price = price * (1 - discount)
                    st.write(f"💰 **Ціна: {final_price:g} ₴**")
                    qty = st.number_input(f"Кількість ({row['Артикул']})", min_value=0.0, step=1.0, key=f"q_{row['Артикул']}")
                    if qty > 0:
                        st.session_state.cart[row['Товар']] = {'qty': qty, 'price': final_price, 'art': row['Артикул']}
            st.divider()

# --- РОЗДІЛ: КОШИК ---
def show_cart(u):
    st.title("🛒 Ваше замовлення")
    if not st.session_state.cart:
        st.info("Ваш кошик поки порожній.")
    else:
        total = 0
        summary = ""
        for name, data in st.session_state.cart.items():
            total += data['qty'] * data['price']
            st.write(f"✅ {name} — {data['qty']} шт. ({data['price'] * data['qty']:g} ₴)")
            summary += f"• {name} ({data['qty']} шт.);\n"
        
        st.subheader(f"Загальна сума: {total:g} ₴")
        comm = st.text_area("Додати коментар (наприклад, час доставки):")
        
        if st.button("🚀 ПІДТВЕРДИТИ ЗАМОВЛЕННЯ", use_container_width=True):
            order_msg = (f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ!</b>\n\n"
                         f"👤 Клієнт: {u['Назва']}\n"
                         f"📞 Тел: {u['Телефон']}\n"
                         f"💰 Сума: {total:g} ₴\n\n"
                         f"🛒 Товари:\n{summary}\n"
                         f"💬 Коментар: {comm}")
            
            send_to_telegram(order_msg)
            send_update({"type": "NEW_ORDER", "phone": u['Телефон'], "client": u['Назва'], "total": total, "items": summary, "comment": comm})
            
            st.success("✅ Замовлення прийнято! Ми вже готуємо його.")
            st.session_state.cart = {}

# --- РОЗДІЛ: НОВИНИ ---
def show_news():
    st.title("📰 Новини Food Festival")
    news_df = load_data(NEWS_URL)
    if news_df is not None:
        for _, row in news_df.iloc[::-1].iterrows():
            st.subheader(row.get('Заголовок', 'Подія'))
            st.write(row.get('Текст новини', ''))
            if row.get('Фото'): st.image(row['Фото'], width=400)
            st.divider()

# --- РОЗДІЛ: НАГАДУВАННЯ (Reminders) ---
def show_reminders(u):
    st.title("🔔 Центр сповіщень")
    st.write("Виберіть тип нагадування для відправки в групу:")
    
    msg_type = st.radio("Що відправляємо?", ["Запит на замовлення", "Зміна графіка", "Своє повідомлення"])
    
    custom_text = ""
    if msg_type == "Своє повідомлення":
        custom_text = st.text_area("Введіть текст повідомлення:")
    
    if st.button("📤 ВІДПРАВИТИ НАГАДУВАННЯ", use_container_width=True):
        if msg_type == "Запит на замовлення":
            text = "🔔 <b>Food Festival:</b> Нагадуємо, що сьогодні день замовлень! Будь ласка, перевірте свої залишки в додатку."
        elif msg_type == "Зміна графіка":
            text = "🕒 <b>Увага:</b> Графік роботи Food Festival змінено. Деталі дивіться в розділі 'Новини'."
        else:
            text = f"📢 <b>Важливе повідомлення:</b>\n{custom_text}"
            
        send_to_telegram(text)
        st.success("✅ Повідомлення надіслано в групу Telegram!")

if __name__ == "__main__":
    main()
