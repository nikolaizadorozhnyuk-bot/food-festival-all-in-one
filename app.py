import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime
from PIL import Image
import xlsxwriter

# ==========================================
# 🔑 НАЛАШТУВАННЯ (FOOD FESTIVAL)
# ==========================================
OWNER_PHONE = "0675953220"
COMPANY_NAME = "Food Festival"
LOGO_URL = "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaFzeDCKyGghOoel888Xx_QkEaYTytH2te1BsJlSlUAqKYg1LyxF0_AwogvNPOU1PX/exec"

# Бази даних CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv"
NEWS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=374278986&single=true&output=csv"

# ==========================================
# 📢 TELEGRAM
# ==========================================
TELEGRAM_TOKEN = "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU"
GROUP_ID = "-1003641918928" 
DEV_ID = "6856949294"       

st.set_page_config(page_title="Food Festival ERP", page_icon=LOGO_URL, layout="wide")

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
@st.cache_data(ttl=30)
def load_data(url):
    try: return pd.read_csv(url, dtype=str).fillna('')
    except: return None

def send_update(payload):
    """Запис замовлення в Google Таблицю"""
    try: requests.post(SCRIPT_URL, json=payload, timeout=15)
    except: pass

def send_order_with_photos(text, photos):
    """Надсилає текст замовлення та фото товарів групою"""
    url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    url_media = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMediaGroup"
    
    requests.post(url_msg, data={"chat_id": GROUP_ID, "text": text, "parse_mode": "HTML"})
    
    if photos:
        media = []
        for img in list(dict.fromkeys(photos))[:10]: 
            media.append({"type": "photo", "media": img})
        try:
            requests.post(url_media, json={"chat_id": GROUP_ID, "media": media}, timeout=10)
        except: pass

def send_to_telegram(text, target="group"):
    chat_id = GROUP_ID if target == "group" else target
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        res = requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
        if res.status_code != 200: st.error(f"⚠️ Telegram Error: {res.text}")
    except Exception as e: st.error(f"⚠️ System Error: {e}")

# --- СЕСІЯ ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- ГОЛОВНИЙ ЕКРАН ---
def main():
    if not st.session_state.logged_in:
        show_login()
        return

    u = st.session_state.user_info
    cart_count = len(st.session_state.cart)
    cart_sum = sum(v['qty'] * v['price'] for v in st.session_state.cart.values())
    cart_label = f"🛒 Кошик ({cart_count} поз. | {cart_sum:g} ₴)" if cart_count > 0 else "🛒 Кошик"

    role = str(u.get('Роль', 'Client')).strip()
    is_admin = role in ['Owner', 'Admin', 'Manager', 'Директор', 'Менеджер', 'Власник']
    
    st.sidebar.image(LOGO_URL, width=150)
    st.sidebar.success(f"👤 {u.get('Назва')} | {role}") 
    
    menu = ["🍎 Каталог", cart_label, "📜 Історія замовлень", "📰 Новини", "📞 Дзвінок", "🚀 ERP Системи"]
    if is_admin:
        menu.insert(3, "📊 Адмін-панель")
        menu.append("🔔 Нагадування")
    
    choice = st.sidebar.selectbox("📍 Навігація:", menu)
    if st.sidebar.button("🚪 Вийти", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    clean_choice = "🛒 Кошик" if "🛒 Кошик" in choice else choice
    if choice == "🍎 Каталог": show_catalog(u)
    elif clean_choice == "🛒 Кошик": show_cart(u)
    elif choice == "📊 Адмін-панель": show_admin_panel()
    elif choice == "📜 Історія замовлень": show_history(u)
    elif choice == "📰 Новини": show_news()
    elif choice == "📞 Дзвінок": show_callback(u)
    elif choice == "🔔 Нагадування": show_reminders(u)
    elif choice == "🚀 ERP Системи": show_developer_promo()

# --- ЛОГІКА ВХОДУ ---
def show_login():
    st.image(LOGO_URL, width=200)
    phone = st.text_input("Введіть номер телефону:")
    if st.button("Увійти", use_container_width=True):
        if phone == OWNER_PHONE:
            st.session_state.logged_in = True
            st.session_state.user_info = {
                'Назва': 'Микола Задорожнюк', 
                'Роль': 'Власник', 
                'Телефон': phone,
                'Менеджер': 'Микола Задорожнюк',
                'Знижка': '0',
                'Колонка прайс': 'Ціна'
            }
            st.rerun()
        df = load_data(CLIENTS_URL)
        if df is not None:
            user = df[df['Телефон'].str.strip() == phone.strip()]
            if not user.empty:
                st.session_state.logged_in = True
                st.session_state.user_info = user.iloc[0].to_dict()
                st.rerun()
            else: st.error("❌ Номер не знайдено.")

def show_catalog(u):
    st.title("🍎 Каталог товарів")
    if st.session_state.cart:
        total = sum(v['qty'] * v['price'] for v in st.session_state.cart.values())
        st.success(f"🛒 У кошику: **{total:g} ₴**. Оформіть замовлення в меню!")

    df = load_data(SHEET_URL)
    if df is not None:
        p_col = u.get('Колонка прайс', 'Ціна')
        search = st.text_input("🔍 Швидкий пошук:")
        f_df = df[df['Товар'].str.contains(search, case=False)] if search else df
        
        # ВИПРАВЛЕННЯ: додаємо idx, щоб ключ завжди був унікальним
        for idx, row in f_df.iterrows():
            with st.container():
                c1, c2 = st.columns([1, 2])
                with c1: st.image(row['Фото'] if pd.notna(row['Фото']) and row['Фото'] else "https://via.placeholder.com/150", use_container_width=True)
                with c2:
                    st.subheader(row['Товар'])
                    if row.get('Опис') and str(row['Опис']).strip() != "":
                        st.info(row['Опис'])
                    p_raw = float(str(row.get(p_col, '0')).replace(',', '.'))
                    st.write(f"💰 **Ціна: {p_raw:g} ₴**")
                    
                    # 100% унікальний ключ (Артикул + номер рядка)
                    art = row.get('Артикул', 'no_art')
                    unique_key = f"q_{art}_{idx}"
                    
                    qty = st.number_input(f"Кількість", min_value=0.0, step=1.0, key=unique_key)
                    if qty > 0: st.session_state.cart[row['Товар']] = {'qty': qty, 'price': p_raw, 'art': art}
                    elif row['Товар'] in st.session_state.cart: del st.session_state.cart[row['Товар']]
            st.divider()

def show_cart(u):
    st.title("🛒 Кошик")
    if not st.session_state.cart:
        st.info("Порожньо.")
    else:
        total = 0; items_txt = ""
        delivery_status = "ДОСТАВКА НА СЬОГОДНІ" if datetime.now().hour < 11 else "ДОСТАВКА НА ЗАВТРА"
        
        # Створюємо унікальні ключі і для видалення в кошику
        for i, (name, data) in enumerate(list(st.session_state.cart.items())):
            line_sum = data['qty'] * data['price']
            total += line_sum
            c_txt, c_del = st.columns([4, 1])
            with c_txt: st.write(f"• **{name}** — {data['qty']} шт. ({line_sum:g} ₴)")
            with c_del:
                if st.button("❌", key=f"del_{data['art']}_{i}"):
                    del st.session_state.cart[name]; st.rerun()
            items_txt += f"{name} ({data['qty']} шт.); "

        st.divider()
        st.subheader(f"Сума: {total:g} ₴")
        addr = st.text_input("Адреса доставки:")
        deliv = st.selectbox("Спосіб", ["Доставка Food Festival", "Самовивіз"])
        if st.button("🚀 ВІДПРАВИТИ ЗАМОВЛЕННЯ", use_container_width=True):
            manager = str(u.get('Менеджер', '')).strip()
            msg = (f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ!</b>\n⏰ {delivery_status}\n👤 {u['Назва']}\n📞 {u['Телефон']}\n"
                   f"👨‍💼 Менеджер: {manager}\n💰 Сума: {total:g} ₴\n🚚 {deliv}: {addr}\n🛒 {items_txt}")
            
            photos = []
            df_p = load_data(SHEET_URL)
            for item_name in st.session_state.cart.keys():
                item_data = df_p[df_p['Товар'] == item_name]
                if not item_data.empty:
                    img_url = str(item_data.iloc[0].get('Фото', '')).strip()
                    if img_url.startswith('http'): photos.append(img_url)

            send_order_with_photos(msg, photos)
            send_update({"type": "NEW_ORDER", "phone": u['Телефон'], "client": u['Назва'], "total": total, "items": items_txt, "delivery_address": addr, "delivery_method": deliv, "manager": manager, "comment": delivery_status})
            st.balloons(); st.session_state.cart = {}; st.rerun()

def show_admin_panel():
    st.title("📊 Аналітика")
    df = load_data(ORDERS_URL)
    if df is not None:
        df['Сума'] = pd.to_numeric(df['Сума'], errors='coerce').fillna(0)
        st.metric("Загальний оборот", f"{df['Сума'].sum():,.0f} ₴")
        st.area_chart(df.groupby('Дата')['Сума'].sum())

def show_history(u):
    st.title("📜 Історія")
    df = load_data(ORDERS_URL)
    if df is not None:
        my = df[df['Телефон'].astype(str).str.contains(str(u['Телефон']))]
        st.dataframe(my)

def show_news():
    st.title("📰 Новини")
    df = load_data(NEWS_URL)
    if df is not None:
        for _, r in df.iterrows(): st.subheader(r['Заголовок']); st.write(r['Текст новини']); st.divider()

def show_callback(u):
    if st.button("🆘 ПЕРЕТЕЛЕФОНУЙТЕ МЕНІ"):
        send_to_telegram(f"☎️ ЗАПИТ НА ДЗВІНОК! {u['Назва']} ({u['Телефон']})", target=DEV_ID)
        st.success("Надіслано!")

def show_reminders(u):
    if st.button("📢 Нагадати всім"):
        send_to_telegram("🔔 Food Festival: Не забудьте замовлення!", target="group")
        st.success("Надіслано!")

def show_developer_promo():
    st.title("🚀 ERP Системи")
    st.link_button("✈️ Зв'язатися з розробником", "https://t.me/FoodFestival_Odesa", use_container_width=True)

if __name__ == "__main__":
    main()
