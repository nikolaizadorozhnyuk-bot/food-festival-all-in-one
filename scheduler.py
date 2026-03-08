import pandas as pd
import requests
import io
import re
from datetime import datetime, timedelta

# --- 1. НАЛАШТУВАННЯ (Беремо з твого CONFIG) ---
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv"
TG_TOKEN = "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU"

def load_data(url):
    try:
        res = requests.get(url)
        df = pd.read_csv(io.StringIO(res.content.decode('utf-8')), dtype=str).fillna('')
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return None

def send_reminders():
    # 1. Визначаємо дату "завтра" у форматі вашої таблиці (наприклад, YYYY-MM-DD)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"🔎 Шукаю забудькуватих клієнтів на {tomorrow}...")

    # 2. Завантажуємо дані
    df_clients = load_data(CLIENTS_URL)
    df_orders = load_data(ORDERS_URL)

    if df_clients is None or df_orders is None:
        print("❌ Помилка завантаження даних.")
        return

    # 3. Знаходимо унікальні ідентифікатори (телефони) тих, хто ВЖЕ замовив на завтра
    # (Припускаємо, що в ORDERS_URL є колонки 'Дата доставки' та 'Телефон')
    c_map_orders = {c.lower(): c for c in df_orders.columns}
    date_col = c_map_orders.get('дата доставки') or c_map_orders.get('дата') or 'Дата'
    phone_col_ord = c_map_orders.get('телефон') or 'Телефон'

    # Очищуємо телефони від символів для точного порівняння
    df_orders['clean_phone'] = df_orders[phone_col_ord].apply(lambda x: re.sub(r'\D', '', str(x)))
    
    # Клієнти, які вже мають замовлення на завтра
    ordered_phones = df_orders[df_orders[date_col] == tomorrow]['clean_phone'].unique()

    # 4. Проходимо по списку ВСІХ клієнтів
    c_map_clients = {c.lower(): c for c in df_clients.columns}
    phone_col_cli = c_map_clients.get('телефон') or 'Телефон'
    name_col = c_map_clients.get('назва') or 'Назва'
    tg_id_col = c_map_clients.get('telegram id') or 'Telegram ID'

    reminder_count = 0
    for _, client in df_clients.iterrows():
        client_phone = re.sub(r'\D', '', str(client[phone_col_cli]))
        tg_id = str(client.get(tg_id_col, '')).strip()

        # Якщо клієнта немає в списку тих, хто замовив, і у нас є його Telegram ID
        if client_phone not in ordered_phones and tg_id:
            try:
                msg = f"Привіт, {client[name_col]}! 👋\nНе забудьте зробити замовлення на завтра! 🍽️"
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                requests.post(url, data={"chat_id": tg_id, "text": msg})
                reminder_count += 1
            except Exception as e:
                print(f"Помилка відправки для {client[name_col]}: {e}")

    print(f"✅ Розсилка завершена. Надіслано {reminder_count} нагадувань.")

# Запуск функції
if __name__ == "__main__":
    send_reminders()
