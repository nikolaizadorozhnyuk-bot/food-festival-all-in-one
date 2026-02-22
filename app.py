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

# Бази даних (Посилання на твої Google Таблиці)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
NEWS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=374278986&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv"

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

# --- ЕКСПОРТ У EXCEL ---
def export_to_excel_full(df, user_discount, p_col, user_name):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Каталог')
    header_style = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#D4AC0D'})
    table_header = workbook.add_format({'bold': True, 'bg_color': '#FFD966', 'border': 1, 'align': 'center'})
    money = workbook.add_format({'num_format': '#,##0.00 ₴', 'border': 1, 'align': 'vcenter'})
    border = workbook.add_format({'border': 1, 'align': 'vcenter', 'text_wrap': True})

    try:
        response = requests.get(LOGO_URL, timeout=5)
        worksheet.insert_image('A1', LOGO_URL, {'image_data': io.BytesIO(response.content), 'x_scale': 0.4, 'y_scale': 0.4})
    except: pass

    worksheet.write('B1', COMPANY_NAME, header_style)
    worksheet.write('B2', f"Клієнт: {user_name} | Прайс від {datetime.now().strftime('%d.%m.%Y')}")

    start_row = 6
    headers = ['Фото', 'Категорія', 'Товар', 'Артикул', 'Залишок', 'Ціна', 'Ваша ціна']
    for col_num, h in enumerate(headers): worksheet.write(start_row, col_num, h, table_header)
    worksheet.set_column('A:A', 15); worksheet.set_column('C:C', 40); worksheet.set_column('D:G', 12)

    for row_num, (_, row) in enumerate(df.iterrows(), start=start_row + 1):
        worksheet.set_row(row_num, 65)
        p_url = row.get('Фото', '')
        if p_url.startswith('http'):
            try:
                img_data = io.BytesIO(requests.get(p_url, timeout=3).content)
                worksheet.insert_image(row_num, 0, p_url, {'image_data': img_data, 'x_scale': 0.16, 'y_scale': 0.16, 'x_offset': 5, 'y_offset': 5})
            except: worksheet.write(row_num, 0, "n/a", border)
        worksheet.write(row_num, 1, row.get('Категорія', ''), border)
        worksheet.write(row_num, 2, row.get('Товар', ''), border)
        worksheet.write(row_num, 3, row.get('Артикул', ''), border)
        worksheet.write(row_num, 4, row.get('Залишок', '0'), border)
        try:
            p = float(str(row.get(p_col, '0')).replace(',', '.'))
            worksheet.write(row_num, 5, p, money); worksheet.write(row_num, 6, p * (1 - user_discount), money)
        except: worksheet.write(row_num, 5, 0, money); worksheet.write(row_num, 6, 0, money)
    workbook.close()
    return output.getvalue()

# --- СЕСІЯ ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

def main():
    if not st.session_state.logged_in:
        show_login()
        return

    u = st.session_state.user_info
    role = u.get('Роль', 'Client')
    
    st.image(LOGO_URL, width=150)
    st.success(f"👤 {u.get('Назва')} | {role}")
    
    menu = ["🍎 Каталог", "🛒 Кошик", "📜 Історія замовлень", "📰 Новини", "📞 Дзвінок"]
    if role in ['Owner', 'Admin', 'Manager']: menu.append("🔔 Нагадування")
    
    choice = st.selectbox("📍 Меню:", menu)
    
    if st.button("🚪 Вийти", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    st.divider()

    if choice == "🍎 Каталог": show_catalog(u)
    elif choice == "🛒 Кошик": show_cart(u)
    elif choice == "📜 Історія замовлень": show_history(u)
    elif choice == "📰 Новини": show_news()
    elif choice == "📞 Дзвінок": show_callback(u)
    elif choice == "🔔 Нагадування": show_reminders(u)

def show_login():
    st.image(LOGO_URL, width=200)
    phone = st.text_input("Введіть ваш номер телефону:")
    if st.button("Увійти", use_container_width=True):
        if phone == OWNER_PHONE:
            st.session_state.logged_in = True
            st.session_state.user_info = {'Назва': 'ВЛАСНИК', 'Роль': 'Owner', 'Телефон': phone, 'Знижка': '0', 'Колонка прайс': 'Ціна'}
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
    df = load_data(SHEET_URL)
    if df is not None:
        p_col = u.get('Колонка прайс', 'Ціна'); d_val = str(u.get('Знижка', '0')).replace('%',''); disc = float(d_val)/100 if d_val.replace('.','').isdigit() else 0
        
        if st.button("📦 Завантажити прайс Excel з фото"):
            with st.spinner("⏳ Створюємо файл..."):
                excel = export_to_excel_full(df, disc, p_col, u['Назва'])
                send_to_telegram(f"📥 <b>Прайс завантажено!</b>\n👤 {u['Назва']}")
                st.download_button("📥 Тисніть для завантаження", excel, "Price_FF.xlsx", use_container_width=True)

        search = st.text_input("🔍 Пошук товара:")
        f_df = df[df['Товар'].str.contains(search, case=False)] if search else df

        for _, row in f_df.iterrows():
            with st.container():
                c1, c2 = st.columns([1, 2])
                with c1: st.image(row['Фото'] if row['Фото'] else "https://via.placeholder.com/150", use_container_width=True)
                with c2:
                    st.subheader(row['Товар'])
                    if row.get('Опис'): st.info(row['Опис'])
                    p_raw = float(str(row.get(p_col, '0')).replace(',', '.')); final_p = p_raw * (1 - disc)
                    st.write(f"💰 **Ціна: {final_p:g} ₴** | Залишок: {row.get('Залишок', '0')}")
                    qty = st.number_input(f"К-сть ({row['Артикул']})", min_value=0.0, step=1.0, key=f"q_{row['Артикул']}")
                    if qty > 0: st.session_state.cart[row['Товар']] = {'qty': qty, 'price': final_p, 'art': row['Артикул']}
            st.divider()

def show_cart(u):
    st.title("🛒 Кошик")
    if not st.session_state.cart: st.info("Кошик порожній.")
    else:
        total = 0; items_txt = ""
        for n, d in st.session_state.cart.items():
            total += d['qty'] * d['price']; st.write(f"• {n} — {d['qty']} шт."); items_txt += f"{n} ({d['qty']} шт.); "
        st.subheader(f"Разом: {total:g} ₴")
        addr = st.text_input("Адреса доставки:"); deliv = st.selectbox("Спосіб доставки", ["Доставка Food Festival", "Самовивіз", "Нова Пошта"])
        if st.button("🚀 ВІДПРАВИТИ ЗАМОВЛЕННЯ", use_container_width=True):
            send_to_telegram(f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ!</b>\n👤 {u['Назва']}\n💰 {total:g} ₴\n🚚 {deliv}\n🏠 {addr}\n🛒 {items_txt}")
            send_update({"type": "NEW_ORDER", "phone": u['Телефон'], "client": u['Назва'], "total": total, "items": items_txt, "delivery_address": addr, "delivery_method": deliv})
            st.success("✅ Надіслано!"); st.session_state.cart = {}

def show_history(u):
    st.title("📜 Історія замовлень")
    df = load_data(ORDERS_URL)
    if df is not None:
        my_orders = df[df['Телефон'].astype(str).str.contains(str(u['Телефон']))]
        if my_orders.empty: st.info("Історія порожня.")
        else:
            for _, o in my_orders.iloc[::-1].iterrows():
                with st.expander(f"📦 {o.get('Дата')} | {o.get('Сума')} ₴ | {o.get('Статус')}"):
                    st.write(f"🛒 **Товари:** {o.get('Товари')}")
                    st.write(f"🏠 **Адреса:** {o.get('Адреса доставки')}")

def show_news():
    st.title("📰 Новини")
    df = load_data(NEWS_URL)
    if df is not None:
        for _, r in df.iloc[::-1].iterrows():
            st.subheader(r.get('Заголовок')); st.write(r.get('Текст новини')); st.divider()

def show_callback(u):
    if st.button("🆘 ПЕРЕТЕЛЕФОНУЙТЕ МЕНІ", use_container_width=True):
        send_to_telegram(f"☎️ <b>ЗАПИТ НА ДЗВІНОК!</b>\n👤 {u['Назва']}\n📞 {u['Телефон']}"); st.success("✅ Запит надіслано!")

def show_reminders(u):
    if st.button("📢 Нагадування в Telegram"):
        send_to_telegram("🔔 <b>Food Festival:</b> Не забудьте зробити замовлення!"); st.success("Надіслано!")

if __name__ == "__main__":
    main()
