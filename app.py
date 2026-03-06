import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta, date

# --- 1. КОНФІГУРАЦІЯ ---
CONFIG = {
    "OWNER_PHONE": "0675953220",
    "LOGO_URL": "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png",
    "SCRIPT_URL": "https://script.google.com/macros/s/AKfycbyaFzeDCKyGghOoel888Xx_QkEaYTytH2te1BsJlSlUAqKYg1LyxF0_AwogvNPOU1PX/exec",
    "TELEGRAM_TOKEN": "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU",
    "GROUP_ID": "-1003641918928",
    # Прямі посилання на CSV експорт
    "URLS": {
        "CATALOG": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=1701329272&single=true&output=csv",
        "CLIENTS": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv",
        "ORDERS": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=1803359156&single=true&output=csv"
    }
}

st.set_page_config(page_title="Food Festival", page_icon=CONFIG["LOGO_URL"], layout="wide")

# --- 2. ДОПОМІЖНІ ФУНКЦІЇ ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        return pd.read_csv(url, dtype=str).fillna('').apply(lambda x: x.str.strip())
    except Exception as e:
        st.error(f"Помилка завантаження даних: {e}")
        return None

def safe_float(val):
    try: return float(str(val).replace(',', '.').replace(' ', ''))
    except: return 0.0

# --- 3. ЛОГІКА КОШИКА ---
def show_cart(u):
    st.title("🛒 Ваш кошик")
    if not st.session_state.cart:
        st.info("Кошик порожній. Перейдіть до каталогу, щоб вибрати товари.")
        return
    
    total = 0
    items_list = []
    
    for name, d in list(st.session_state.cart.items()):
        subtotal = d['qty'] * d['price']
        total += subtotal
        items_list.append(f"{name} ({d['qty']} x {d['price']} ₴)")
        
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1: st.write(f"**{name}**")
        with c2: st.write(f"{d['price']:g} ₴")
        with c3:
            if st.button("❌", key=f"del_{name}"):
                del st.session_state.cart[name]
                st.rerun()

    st.markdown(f"### 💰 Разом до сплати: **{total:g} ₴**")
    
    # Вибір дати (мінімум +1 день, якщо м'ясо +2)
    has_meat = any(d.get('category') == "Свіже м'ясо" for d in st.session_state.cart.values())
    min_d = date.today() + timedelta(days=2 if has_meat else 1)
    deliv_date = st.date_input("📅 Бажана дата доставки", min_value=min_d, value=min_d)
    
    comment = st.text_area("💬 Коментар до замовлення")

    if st.button("🚀 ВІДПРАВИТИ ЗАМОВЛЕННЯ", use_container_width=True, type="primary"):
        items_txt = "; ".join(items_list)
        
        # Відправка в Google Таблицю (JSON формат для нашого Code.gs)
        payload = {
            "type": "NEW_ORDER",
            "phone": u['Телефон'],
            "client": u['Назва'],
            "total": total,
            "items": items_txt,
            "comment": comment,
            "delivery_date": deliv_date.strftime("%d.%m.%Y"),
            "manager": u.get('Менеджер', 'Admin')
        }
        
        try:
            # Надсилаємо JSON в Google Apps Script
            resp = requests.post(CONFIG["SCRIPT_URL"], json=payload)
            
            # Повідомлення в Telegram
            tg_msg = (f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ!</b>\n"
                      f"👤 Клієнт: {u['Назва']}\n"
                      f"📞 Тел: {u['Телефон']}\n"
                      f"💰 Сума: {total:g} ₴\n"
                      f"📅 Дата: {deliv_date.strftime('%d.%m.%Y')}\n"
                      f"🛒 Товари: {items_txt}")
            
            requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_TOKEN']}/sendMessage", 
                          data={"chat_id": CONFIG["GROUP_ID"], "text": tg_msg, "parse_mode": "HTML"})
            
            st.session_state.cart = {}
            st.success("✅ Замовлення прийнято! Менеджер зв'яжеться з вами.")
            st.balloons()
        except:
            st.error("Помилка зв'язку з сервером. Спробуйте ще раз.")

# --- 4. КАТАЛОГ ---
def show_catalog(u):
    st.title("🍎 Наш асортимент")
    df = load_data(CONFIG["URLS"]["CATALOG"])
    if df is None: return

    search = st.sidebar.text_input("🔍 Швидкий пошук")
    categories = ["Всі"] + sorted(df['Категорія'].unique().tolist())
    sel_cat = st.sidebar.selectbox("📂 Категорія", categories)

    f_df = df
    if sel_cat != "Всі": f_df = f_df[f_df['Категорія'] == sel_cat]
    if search: f_df = f_df[f_df['Назва'].str.contains(search, case=False)]

    for _, r in f_df.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(r['Фото'] if 'http' in r['Фото'] else "https://via.placeholder.com/150")
            with col2:
                st.subheader(r['Назва'])
                price = safe_float(r['Ціна'])
                st.write(f"💵 Ціна: **{price:g} ₴**")
                
                q_key = f"q_{r['upc']}"
                qty = st.number_input("Кількість", min_value=0.0, step=1.0, key=q_key)
                if st.button("Додати в кошик", key=f"btn_{r['upc']}"):
                    if qty > 0:
                        st.session_state.cart[r['Назва']] = {'qty': qty, 'price': price, 'category': r['Категорія']}
                        st.toast(f"✅ {r['Назва']} додано!")
                    else:
                        st.warning("Вкажіть кількість!")

# --- 5. ВХІД ТА ГОЛОВНИЙ ЦИКЛ ---
def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.image(CONFIG["LOGO_URL"], width=250)
        st.subheader("Вхід в систему замовлень")
        ph = st.text_input("Введіть ваш номер телефону (0XXXXXXXXX)")
        
        if st.button("Увійти", use_container_width=True):
            if ph == CONFIG["OWNER_PHONE"]:
                st.session_state.logged_in = True
                st.session_state.user_info = {'Назва': 'Микола (Власник)', 'Телефон': ph, 'Менеджер': 'Admin'}
                st.rerun()
            
            df_c = load_data(CONFIG["URLS"]["CLIENTS"])
            if df_c is not None:
                user = df_c[df_c['Телефон'] == ph]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Користувача не знайдено. Зверніться до менеджера.")
    else:
        # Навігація
        st.sidebar.title(f"👋 {st.session_state.user_info['Назва']}")
        page = st.sidebar.radio("Навігація", ["🍎 Каталог", "🛒 Кошик", "📜 Історія замовлень"])
        
        if page == "🍎 Каталог": show_catalog(st.session_state.user_info)
        elif page == "🛒 Кошик": show_cart(st.session_state.user_info)
        elif page == "📜 Історія замовлень":
            st.title("Історія замовлень")
            st.info("Розділ у розробці (дані завантажуються з таблиці)")
        
        if st.sidebar.button("Вийти"):
            st.session_state.logged_in = False
            st.rerun()

if __name__ == "__main__":
    main()
