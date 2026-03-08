import pandas as pd
import requests
import io
import re
import os
from datetime import datetime, timedelta

# --- КОНФІГУРАЦІЯ ---
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv"
# Токен беремо з секретів GitHub для безпеки
TG_TOKEN = os.getenv("TG_TOKEN", "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU")

def load_data(url):
    try:
        res = requests.get(url, timeout=15)
        df = pd.read_csv(io.StringIO(res.content.decode('utf-8')), dtype=str).fillna('')
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        print(f"Помилка завантаження: {e}")
        return None

def clean_phone(p):
    return re.sub(r'\D', '', str(p))

def send_reminders():
    # 1. Визначаємо завтрашню дату
    # Спробуємо два формати: 09.03.2026 та 2026-03-09
    now = datetime.now() + timedelta(days=1)
    tomorrow_dot = now.strftime('%d.%m.%Y')
    tomorrow_dash = now.strftime('%Y-%m-%d')
    
    print(f"🔎 Перевірка замовлень на: {tomorrow_dot} / {tomorrow_dash}")

    df_clients = load_data(CLIENTS_URL)
    df_orders = load_data(ORDERS_URL)

    if df_clients is None or df_orders is None: return

    # 2. Знаходимо телефони тих, хто ВЖЕ замовив на завтра
    # Використовуємо твої точні назви колонок: 'Дата доставки', 'Телефон', 'Статус замовлення'
    ordered_phones = set()
    for _, row in df_orders.iterrows():
        order_date = row.get('Дата доставки', '').strip()
        order_status = row.get('Статус замовлення', '').lower()
        
        # Якщо дата збігається і замовлення не скасовано
        if (order_date == tomorrow_dot or order_date == tomorrow_dash) and 'скас' not in order_status:
            ordered_phones.add(clean_phone(row.get('Телефон', '')))

    # 3. Розсилка нагадувань
    reminder_count = 0
    # Шукаємо колонки в клієнтах
    c_cols = {c.lower(): c for c in df_clients.columns}
    phone_col = c_cols.get('телефон') or df_clients.columns[0]
    name_col = c_cols.get('назва') or c_cols.get('клієнт') or df_clients.columns[1]
    tg_id_col = c_cols.get('telegram id') or c_cols.get('id')

    for _, client in df_clients.iterrows():
        c_phone = clean_phone(client.get(phone_col, ''))
        tg_id = str(client.get(tg_id_col, '')).strip()
        c_name = client.get(name_col, 'Клієнт')

        # Якщо не замовив і є куди писати (Telegram ID)
        if c_phone not in ordered_phones and tg_id and len(tg_id) > 5:
            try:
                text = f"Вітаємо, {c_name}! 👋\nНагадуємо, що ви ще не зробили замовлення на завтра. Чекаємо на вас у додатку! 🍽️"
                requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                              data={"chat_id": tg_id, "text": text}, timeout=10)
                reminder_count += 1
                print(f"✅ Надіслано: {c_name}")
            except:
                print(f"❌ Помилка для: {c_name}")

    print(f"📊 Разом надіслано нагадувань: {reminder_count}")

if __name__ == "__main__":
    send_reminders()
