import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime, timedelta
from PIL import Image
import xlsxwriter

# ==========================================
# 🔑 НАЛАШТУВАННЯ (FOOD FESTIVAL)
# ==========================================
OWNER_PHONE = "0675953220"
COMPANY_NAME = "Food Festival"
LOGO_URL = "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png"
# Посилання на твій Google Apps Script
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaFzeDCKyGghOoel888Xx_QkEaYTytH2te1BsJlSlUAqKYg1LyxF0_AwogvNPOU1PX/exec"

# Посилання на CSV (база даних)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
NEWS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=374278986&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv"

# ==========================================
# 📢 НАЛАШТУВАННЯ TELEGRAM
# ==========================================
# ⚠️ ВСТАВ ПОВНИЙ ТОКЕН ТУТ:
TELEGRAM_TOKEN = "8275141603:ВСТАВ_СЮДИ_ТОКЕН_З_BOTFATHER"

GROUP_ID = "-1005236190167" 
DIRECTOR_ID = "636970008"
DEV_ID = "6856949294"

st.set_page_config(page_title="Food Festival ERP", page_icon=LOGO_URL, layout="wide")

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
@st.cache_data(ttl=30)
def load_data(url):
    try: return pd.read_csv(url, dtype=str).fillna('')
    except: return None

def send_update(payload):
    """Відправка даних у Google Таблицю"""
    try:
        res = requests.post(SCRIPT_URL, json=payload, timeout=15)
        return res.text
    except Exception as e:
        return f"Error: {e}"

def send_to_telegram(text, target="group"):
    """Відправка сповіщень у Telegram"""
    if target == "group": chat_ids = [GROUP_ID]
    elif target == "management": chat_ids = [DIRECTOR_ID, DEV_ID]
    else: chat_ids = [target]
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in chat_ids:
        try:
            res = requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
            if res.status_code != 200:
                st.error(f"⚠️ Помилка Telegram (ID {chat_id}): {res.text}")
        except Exception as e:
            st.error(f"⚠️ Системна помилка Telegram: {e}")

# --- СЕСІЯ ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- ПРОМО РОЗРОБНИКА ---
def show_developer_promo():
    st.title("🚀 Бажаєте такий додаток для свого бізнесу?")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""Я розробляю індивідуальні рішення для автоматизації:
        * **✅ Мобільний каталог та кошик**
        * **✅ База на Google Таблицях**
        * **✅ Розумні Telegram-боти**""")
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/3142/3142121.png", width=150)
    st.divider()
    st.link_button("✈️ Написати Миколі", "https://t.me/FoodFestival_Odesa", use_container_width=True)

# --- ГОЛОВНИЙ ЕКРАН ---
def main():
    if not st.session_state.logged_in:
        show_login()
        return

    u = st.session_state.user_info
    role = str(u.get('Роль', 'Client')).strip()
    is_admin = role in ['Owner', 'Admin', 'Manager', 'Директор', 'Менеджер', 'Власник']
    
    st.sidebar.image(LOGO_URL, width=150)
    st.sidebar.success(f"👤 {u.get('Назва')} | {role}")
    
    menu = ["🍎 Каталог", "🛒 Кошик", "📜 Історія замовлень", "📰 Новини", "📞 Дзвінок", "🚀 Власний додаток?"]
    if is_admin:
        menu.insert(3, "📊 Адмін-панель")
        menu.append("🔔 Нагадування")
    
    choice = st.sidebar.selectbox("📍 Навігація:", menu)
    
    if st.sidebar.button("🚪 Вийти", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    if choice == "🍎 Каталог": show_catalog(u)
    elif choice == "🛒 Кошик": show_cart(u)
    elif choice == "📊 Адмін-панель": show_admin_panel()
    elif choice == "📜 Історія замовлень": show_history(u)
    elif choice == "📰 Новини": show_news()
    elif choice == "📞 Дзвінок": show_callback(u)
    elif choice == "🔔 Нагадування": show_reminders(u)
    elif choice == "🚀 Власний додаток?": show_developer_promo()

def show_login():
    st.image(LOGO_URL, width=200)
    phone = st.text_input("Введіть номер телефону:")
    if st.button("Увійти", use_container_width=True):
        if phone == OWNER_PHONE:
            st.session_state.logged_in = True
            st.session_state.user_info = {'Назва': 'ВЛАСНИК', 'Роль': 'Власник', 'Телефон': phone}
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
    st.title("🍎 Каталог")
    df = load_data(SHEET_URL)
    if df is not None:
        p_col = u.get('Колонка прайс', 'Ціна')
        d_val = str(u.get('Знижка', '0')).replace('%','')
        disc = float(d_val)/100 if d_val.replace('.','').isdigit() else 0
        search = st.text_input("🔍 Пошук товару:")
        f_df = df[df['Товар'].str.contains(search, case=False)] if search else df
        for _, row in f_df.iterrows():
            with st.container():
                c1, c2 = st.columns([1, 2])
                with c1: st.image(row['Фото'] if pd.notna(row['Фото']) and row['Фото'] else "https://via.placeholder.com/150", use_container_width=True)
                with c2:
                    st.subheader(row['Товар'])
                    p_raw = float(str(row.get(p_col, '0')).replace(',', '.'))
                    final_p = p_raw * (1 - disc)
                    st.write(f"💰 **Ціна: {final_p:g} ₴** | Артикул: {row['Артикул']}")
                    qty = st.number_input(f"К-сть ({row['Артикул']})", min_value=0.0, step=1.0, key=f"q_{row['Артикул']}")
                    if qty > 0: st.session_state.cart[row['Товар']] = {'qty': qty, 'price': final_p, 'art': row['Артикул']}
            st.divider()

def show_cart(u):
    st.title("🛒 Кошик")
    if not st.session_state.cart: 
        st.info("Кошик порожній.")
    else:
        total = 0; items_txt = ""
        delivery_status = "ДОСТАВКА НА СЬОГОДНІ" if datetime.now().hour < 11 else "ДОСТАВКА НА ЗАВТРА"
        for n, d in st.session_state.cart.items():
            total += d['qty'] * d['price']
            st.write(f"• {n} — {d['qty']} шт. ({d['qty']*d['price']:g} ₴)")
            items_txt += f"{n} ({d['qty']} шт.); "
            
        st.subheader(f"Сума: {total:g} ₴")
        addr = st.text_input("Адреса доставки:")
        deliv = st.selectbox("Спосіб доставки", ["Доставка Food Festival", "Самовивіз", "Нова Пошта"])
        
        if st.button("🚀 ВІДПРАВИТИ ЗАМОВЛЕННЯ", use_container_width=True):
            manager = str(u.get('Менеджер', '')).strip()
            msg = (f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ!</b>\n⏰ {delivery_status}\n👤 {u['Назва']}\n📞 {u['Телефон']}\n"
                   f"👨‍💼 Менеджер: {manager}\n💰 Сума: {total:g} ₴\n🚚 {deliv}: {addr}\n🛒 {items_txt}")
            
            send_to_telegram(msg, target="group")
            send_update({
                "type": "NEW_ORDER", "phone": u['Телефон'], "client": u['Назва'], 
                "total": total, "items": items_txt, "delivery_address": addr, 
                "delivery_method": deliv, "manager": manager, "comment": delivery_status
            })
            st.balloons(); st.success("✅ Замовлено!"); st.session_state.cart = {}

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
    if st.button("📢 Нагадати всім у Telegram"):
        send_to_telegram("🔔 Food Festival: Не забудьте зробити замовлення!", target="group")
        st.success("Надіслано!")

# --- ПРЕМІУМ ЕКСПОРТ EXCEL (З КОНВЕРТАЦІЄЮ WEBP) ---
def export_to_excel_full(df, user_discount, p_col, user_name):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Каталог')
    # (Тут логіка Excel з твого попереднього коду...)
    workbook.close()
    return output.getvalue()

if __name__ == "__main__":
    main()
