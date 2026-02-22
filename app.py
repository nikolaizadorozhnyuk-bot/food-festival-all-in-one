import streamlit as st
import pandas as pd
import requests

# ==========================================
# 🔑 НАЛАШТУВАННЯ
# ==========================================
OWNER_PHONE = "0675953220"
LOGO_URL = "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaFzeDCKyGghOoel888Xx_QkEaYTytH2te1BsJlSlUAqKYg1LyxF0_AwogvNPOU1PX/exec"

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"

TELEGRAM_TOKEN = "8183938320:AAHsDhUXcu3ZeKg8Qh3AZc3xbXMa9YqqqZc"
CHAT_ID = "-5236190167"

st.set_page_config(page_title="Food Festival ERP", page_icon=LOGO_URL, layout="wide")

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
@st.cache_data(ttl=30)
def load_data(url):
    try: return pd.read_csv(url, dtype=str).fillna('')
    except: return None

def send_update(payload):
    try: return requests.post(SCRIPT_URL, json=payload, timeout=10).text
    except: return "Error"

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- ГОЛОВНИЙ ІНТЕРФЕЙС ---
def main():
    if not st.session_state.logged_in:
        show_login()
        return

    u = st.session_state.user_info
    role = u.get('Роль', 'Client')
    
    st.image(LOGO_URL, width=150)
    st.success(f"🔓 {role.upper()}: {u.get('Назва', 'Користувач')}")
    
    # Мобільне меню
    menu = ["🍎 Каталог", "🛒 Кошик", "📰 Новини"]
    if role in ['Owner', 'Admin', 'Manager']:
        menu.append("📊 Звіт")
        menu.append("🔔 Нагадування")

    choice = st.selectbox("📌 Навігація:", menu)
    
    if st.button("🚪 Вийти", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    st.divider()

    if choice == "🍎 Каталог":
        show_catalog(u)
    elif choice == "🛒 Кошик":
        show_cart(u)
    elif choice == "🔔 Нагадування":
        st.title("🔔 Розсилка нагадувань")
        st.info("Тут ми розмістимо твій код нагадування у наступному кроці.")

# --- РОЗДІЛ: ВХІД ---
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(LOGO_URL, use_container_width=True)
        st.title("Вхід у систему")
        phone = st.text_input("Номер телефону:")
        if st.button("🚪 Увійти", use_container_width=True):
            if phone == OWNER_PHONE:
                st.session_state.logged_in = True
                st.session_state.user_info = {'Назва': 'ВЛАСНИК', 'Роль': 'Owner', 'Телефон': phone, 'Колонка прайс': 'Ціна'}
                st.rerun()
            
            clients_df = load_data(CLIENTS_URL)
            if clients_df is not None:
                user = clients_df[clients_df['Телефон'].str.strip() == phone.strip()]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Доступ обмежено. Перевірте номер.")

# --- РОЗДІЛ: КАТАЛОГ ---
def show_catalog(u):
    df = load_data(SHEET_URL)
    if df is not None and not df.empty:
        st.title("🍎 Асортимент")
        
        # Пошук та фільтр
        search = st.text_input("🔍 Пошук за назвою:")
        categories = ["Усі"] + list(df['Категорія'].unique())
        selected_cat = st.selectbox("📁 Категорія:", categories)

        f_df = df.copy()
        if selected_cat != "Усі": f_df = f_df[f_df['Категорія'] == selected_cat]
        if search: f_df = f_df[f_df['Товар'].str.contains(search, case=False, na=False)]
        
        discount = float(str(u.get('Знижка', '0')).replace('%','')) / 100

        for _, row in f_df.iterrows():
            with st.container():
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.image(row['Фото'] if row['Фото'] else "https://via.placeholder.com/150", use_container_width=True)
                with c2:
                    st.subheader(row['Товар'])
                    p_col = u.get('Колонка прайс', 'Ціна')
                    price = float(str(row.get(p_col, '0')).replace(',', '.'))
                    
                    if discount > 0:
                        final_price = price * (1 - discount)
                        st.write(f"💰 Ціна: ~~{price:g}~~ **{final_price:g} ₴**")
                    else:
                        st.write(f"💰 Ціна: **{price:g} ₴**")
                    
                    qty = st.number_input(f"К-сть ({row['Артикул']})", min_value=0.0, step=1.0, key=f"q_{row['Артикул']}")
                    if qty > 0:
                        st.session_state.cart[row['Товар']] = {'qty': qty, 'price': price * (1 - discount)}
            st.divider()

# --- РОЗДІЛ: КОШИК ---
def show_cart(u):
    st.title("🛒 Кошик")
    if not st.session_state.cart:
        st.info("Кошик порожній")
    else:
        total = 0
        items_text = ""
        for name, data in st.session_state.cart.items():
            subtotal = data['qty'] * data['price']
            total += subtotal
            st.write(f"**{name}** | {data['qty']} шт. | {subtotal:g} ₴")
            items_text += f"{name} ({data['qty']}); "
        
        st.subheader(f"Разом: {total:g} ₴")
        
        delivery = st.selectbox("Доставка:", ["Самовивіз", "Нова Пошта", "Доставка FF"])
        addr = st.text_input("Адреса/Відділення:")
        
        if st.button("🚀 Відправити замовлення", use_container_width=True):
            payload = {
                "type": "NEW_ORDER",
                "phone": u['Телефон'],
                "client": u['Назва'],
                "total": total,
                "items": items_text,
                "delivery_method": delivery,
                "delivery_address": addr
            }
            send_update(payload)
            st.success("Замовлення надіслано!")
            st.session_state.cart = {}

if __name__ == "__main__":
    main()
