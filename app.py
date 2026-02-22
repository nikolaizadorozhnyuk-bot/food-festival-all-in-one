import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime
from PIL import Image

# ==========================================
# 🔑 НАЛАШТУВАННЯ
# ==========================================
OWNER_PHONE = "0675953220"
LOGO_URL = "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaFzeDCKyGghOoel888Xx_QkEaYTytH2te1BsJlSlUAqKYg1LyxF0_AwogvNPOU1PX/exec"

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

# 🆕 ОНОВЛЕНА ФУНКЦІЯ ЕКСПОРТУ (З ФОТО ТА ЗАЛИШКАМИ)
def export_to_excel_with_images(df, user_discount, p_col):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Каталог')

    # Форматування
    bold = workbook.add_format({'bold': True, 'bg_color': '#FFD966', 'border': 1})
    money = workbook.add_format({'num_format': '#,##0.00 ₴', 'border': 1})
    border = workbook.add_format({'border': 1, 'align': 'vcenter'})

    # Заголовки
    headers = ['Фото', 'Товар', 'Артикул', 'Залишок', 'Ціна', 'Ціна зі знижкою']
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, bold)

    worksheet.set_column('A:A', 15) # Для фото
    worksheet.set_column('B:B', 40) # Для назви
    worksheet.set_column('C:E', 15) 

    for row_num, (_, row) in enumerate(df.iterrows(), start=1):
        worksheet.set_row(row_num, 60) # Висота рядка для фото
        
        # 1. Завантаження та вставка фото
        photo_url = row.get('Фото', '')
        if photo_url and photo_url.startswith('http'):
            try:
                response = requests.get(photo_url, timeout=5)
                image_data = io.BytesIO(response.content)
                worksheet.insert_image(row_num, 0, photo_url, {
                    'image_data': image_data,
                    'x_scale': 0.15, 'y_scale': 0.15, # Масштабування
                    'x_offset': 5, 'y_offset': 5
                })
            except:
                worksheet.write(row_num, 0, "Немає фото", border)
        
        # 2. Назва, Артикул, Залишок
        worksheet.write(row_num, 1, row.get('Товар', ''), border)
        worksheet.write(row_num, 2, row.get('Артикул', ''), border)
        worksheet.write(row_num, 3, row.get('Залишок', '0'), border)

        # 3. Розрахунок цін
        try:
            raw_p = float(str(row.get(p_col, '0')).replace(',', '.'))
            final_p = raw_p * (1 - user_discount)
            worksheet.write(row_num, 4, raw_p, money)
            worksheet.write(row_num, 5, final_p, money)
        except:
            worksheet.write(row_num, 4, 0, money)
            worksheet.write(row_num, 5, 0, money)

    workbook.close()
    return output.getvalue()

# ... (Інші функції: send_to_telegram, send_update, show_login залишаються без змін) ...

def show_catalog(u):
    df = load_data(SHEET_URL)
    if df is not None:
        st.title("🍎 Асортимент")
        
        p_col = u.get('Колонка прайс', 'Ціна')
        discount_val = str(u.get('Знижка', '0')).replace('%','')
        user_discount = float(discount_val) / 100 if discount_val.replace('.','').isdigit() else 0

        # КНОПКА ЗАВАНТАЖЕННЯ (З ФОТО)
        if st.button("📦 Сформувати Excel-каталог з фото"):
            with st.spinner("⏳ Завантажуємо фото та створюємо файл... зачекайте."):
                excel_file = export_to_excel_with_images(df, user_discount, p_col)
                st.download_button(
                    label="📥 Тисніть тут, щоб завантажити файл",
                    data=excel_file,
                    file_name=f"Price_FF_with_Photos_{datetime.now().strftime('%d_%m')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        st.write("---")
        # ... (Далі стандартний вивід каталогу на екран) ...
