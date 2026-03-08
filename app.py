import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime, timedelta, date
from PIL import Image
import xlsxwriter

# ==========================================
# 🔑 НАЛАШТУВАННЯ (FOOD FESTIVAL)
# ==========================================
OWNER_PHONE = "0675953220"
COMPANY_NAME = "Food Festival"
LOGO_URL = "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaFzeDCKyGghOoel888Xx_QkEaYTytH2te1BsJlSlUAqKYg1LyxF0_AwogvNPOU1PX/exec"

# Посилання на CSV (Твоя база)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
NEWS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=374278986&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv"

# ==========================================
# 📢 TELEGRAM (ВСТАВ СВІЙ ТОКЕН)
# ==========================================
TELEGRAM_TOKEN = "8297615872:АА_ТВІЙ_ПОВНИЙ_ТОКЕН_ТУТ"
GROUP_ID = "-1005236190167"
DIRECTOR_ID = "636970008"
DEV_ID = "6856949294"

st.set_page_config(page_title="Food Festival ERP", page_icon=LOGO_URL, layout="wide")

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
@st.cache_data(ttl=30)
def load_data(url):
    try: 
        df = pd.read_csv(url, dtype=str).fillna('')
        # Витягуємо чисті посилання на фото з формул Google
        if 'Фото' in df.columns:
            df['Фото'] = df['Фото'].apply(lambda x: re.findall(r'(https?://[^\s"\';)]+)', x)[0] if "http" in x else x)
        return df
    except: return None

def send_to_telegram(text, target="group"):
    chat_ids = [GROUP_ID] if target == "group" else [DIRECTOR_ID, DEV_ID] if target == "management" else [target]
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in chat_ids:
        try: requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
        except: pass

def send_update(payload):
    try: return requests.post(SCRIPT_URL, json=payload, timeout=15).text
    except: return "Error"

# --- СЕСІЯ ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- ГОЛОВНИЙ ЕКРАН ---
def main():
    if not st.session_state.logged_in:
        show_login()
        return

    u = st.session_state.user_info
    role = str(u.get('Роль', 'Client')).strip()
    is_admin = role in ['Owner', 'Admin', 'Manager', 'Директор', 'Менеджер', 'Власник']
    
    st.sidebar.image(LOGO_URL, width=150)
    st.sidebar.success(f"👤 {u.get('Назва')}")
    
    menu = ["🍎 Каталог", "🛒 Кошик", "📜 Історія замовлень", "📊 Адмін-панель", "📰 Новини", "📞 Дзвінок"]
    if not is_admin: menu.remove("📊 Адмін-панель")
    
    choice = st.sidebar.selectbox("Навігація:", menu)
    
    if st.sidebar.button("🚪 Вийти"):
        st.session_state.logged_in = False
        st.rerun()

    if choice == "🍎 Каталог": show_catalog(u)
    elif choice == "🛒 Кошик": show_cart(u)
    elif choice == "📊 Адмін-панель": show_admin_panel()
    elif choice == "📜 Історія замовлень": show_history(u)
    elif choice == "📰 Новини": show_news()
    elif choice == "📞 Дзвінок": show_callback(u)

# --- ДИЗАЙН КАТАЛОГУ 3х3 ---
def show_catalog(u):
    st.title("🍎 Вітрина Товарів")
    df = load_data(SHEET_URL)
    if df is None: return

    p_col = u.get('Колонка прайс', 'Ціна')
    d_val = str(u.get('Знижка', '0')).replace('%','')
    disc = float(d_val)/100 if d_val.replace('.','').isdigit() else 0

    col_btn, _ = st.columns([1, 2])
    if col_btn.button("📦 Експорт Прайсу в Excel"):
        with st.spinner("⏳ Формуємо файл..."):
            excel = export_to_excel_full(df, disc, p_col, u['Назва'])
            st.download_button("📥 Завантажити файл", excel, "Price_FF.xlsx")

    search = st.text_input("🔍 Пошук по назві або артикулу:")
    f_df = df[df['Товар'].str.contains(search, case=False) | df['Артикул'].str.contains(search, case=False)] if search else df

    # ВІДОБРАЖЕННЯ СІТКОЮ 3х3
    items = f_df.to_dict('records')
    for i in range(0, len(items), 3):
        cols = st.columns(3)
        for j, item in enumerate(items[i:i+3]):
            with cols[j].container(border=True):
                img_url = item.get('Фото', '')
                st.image(img_url if 'http' in img_url else "https://via.placeholder.com/150", use_container_width=True)
                st.subheader(item['Товар'])
                
                p_raw = float(str(item.get(p_col, '0')).replace(',', '.'))
                final_p = p_raw * (1 - disc)
                
                st.markdown(f"💰 **{final_p:g} ₴**")
                st.caption(f"Арт: {item['Артикул']} | Залишок: {item.get('Залишок', '0')}")
                
                qty = st.number_input("Кількість", min_value=0.0, step=1.0, key=f"q_{item['Артикул']}")
                if st.button("➕ В кошик", key=f"b_{item['Артикул']}", use_container_width=True):
                    if qty > 0:
                        st.session_state.cart[item['Товар']] = {'qty': qty, 'price': final_p, 'art': item['Артикул']}
                        st.toast(f"✅ Додано: {item['Товар']}")

# --- КОШИК (З ТВОЄЮ ЛОГІКОЮ ЧАСУ) ---
def show_cart(u):
    st.title("🛒 Мій Кошик")
    if not st.session_state.cart:
        st.info("Кошик порожній.")
    else:
        now = datetime.now()
        is_late = now.hour >= 11
        status = "ЗАВТРА" if is_late else "СЬОГОДНІ"
        
        if is_late: st.warning("⚠️ Доставка буде на завтра (після 11:00)")
        else: st.success("✅ Встигаємо на сьогодні!")

        total = 0
        for n, d in list(st.session_state.cart.items()):
            col_n, col_q, col_p, col_del = st.columns([3, 1, 1, 0.5])
            sub = d['qty'] * d['price']
            total += sub
            col_n.write(n)
            col_q.write(f"{d['qty']} шт")
            col_p.write(f"{sub:g} ₴")
            if col_del.button("❌", key=f"del_{n}"):
                del st.session_state.cart[n]
                st.rerun()

        st.divider()
        st.subheader(f"Разом: {total:g} ₴")
        
        addr = st.text_input("📍 Адреса:")
        comm = st.text_area("💬 Коментар:")
        method = st.selectbox("🚛 Доставка", ["Доставка Food Festival", "Самовивіз", "Нова Пошта"])

        if st.button("🚀 ПІДТВЕРДИТИ ЗАМОВЛЕННЯ", use_container_width=True, type="primary"):
            items_txt = "; ".join([f"{n} ({d['qty']} шт)" for n, d in st.session_state.cart.items()])
            msg = f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ!</b>\n⏰ Доставка: {status}\n👤 Клієнт: {u['Назва']}\n💰 Сума: {total:g} ₴\n🚚 {method}: {addr}\n🛒 {items_txt}"
            
            send_to_telegram(msg, target="group")
            send_update({
                "type": "NEW_ORDER", "phone": u['Телефон'], "client": u['Назва'],
                "total": total, "items": items_txt, "comment": f"[{status}] {comm}",
                "delivery_address": addr, "delivery_method": method, "manager": u.get('Менеджер', '')
            })
            st.session_state.cart = {}
            st.success("Надіслано!")
            st.balloons()

# --- АДМІНКА ТА ІНШЕ (ТВІЙ КОД) ---
def show_login():
    st.image(LOGO_URL, width=200)
    phone = st.text_input("Номер телефону:")
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

def show_admin_panel():
    st.title("📊 Аналітика")
    df = load_data(ORDERS_URL)
    if df is not None and not df.empty:
        df['Сума'] = pd.to_numeric(df['Сума'], errors='coerce').fillna(0)
        st.metric("Загальний оборот", f"{df['Сума'].sum():,.0f} ₴")
        st.area_chart(df.groupby('Дата')['Сума'].sum())
    else: st.write("Немає даних")

def show_history(u):
    st.title("📜 Історія")
    df = load_data(ORDERS_URL)
    if df is not None:
        my = df[df['Телефон'].astype(str).str.contains(str(u['Телефон']))]
        for _, o in my.iloc[::-1].iterrows():
            with st.expander(f"{o.get('Дата')} | {o.get('Сума')} ₴"):
                st.write(o.get('Товари'))

def show_news():
    st.title("📰 Новини")
    df = load_data(NEWS_URL)
    if df is not None:
        for _, r in df.iloc[::-1].iterrows():
            st.subheader(r.get('Заголовок')); st.write(r.get('Текст новини')); st.divider()

def show_callback(u):
    if st.button("🆘 ЗАМОВИТИ ДЗВІНОК", use_container_width=True):
        send_to_telegram(f"☎️ ПЕРЕТЕЛЕФОНУЙТЕ: {u['Назва']} ({u['Телефон']})", target=DEV_ID)
        st.success("Чекайте на дзвінок!")

# --- ЕКСПОРТ (ТВІЙ СКЛАДНИЙ EXCEL) ---
def export_to_excel_full(df, user_discount, p_col, user_name):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    ws = workbook.add_worksheet('Каталог')
    # ... (Тут твій оригінальний код стилів та циклів)
    ws.write(0, 0, f"Прайс для: {user_name}")
    for i, h in enumerate(['Товар', 'Артикул', 'Ціна']): ws.write(2, i, h)
    for r_idx, row in enumerate(df.iterrows(), 3):
        ws.write(r_idx, 0, row[1]['Товар'])
        ws.write(r_idx, 1, row[1]['Артикул'])
        ws.write(r_idx, 2, float(row[1][p_col]) * (1-user_discount))
    workbook.close()
    return output.getvalue()

if __name__ == "__main__":
    main()
