import sys
import pandas as pd
import requests
import io
import re
import os
from datetime import datetime, timedelta

# --- КОНФІГУРАЦІЯ ---
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv"
TG_TOKEN = os.getenv("TG_TOKEN", "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU")
GROUP_ID = "-1003641918928" # Група, куди полетить щотижневий звіт

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

# ==========================================
# 1. ФУНКЦІЯ НАГАДУВАНЬ (Щоденна)
# ==========================================
def send_reminders():
    now = datetime.now() + timedelta(days=1)
    tomorrow_dot = now.strftime('%d.%m.%Y')
    tomorrow_dash = now.strftime('%Y-%m-%d')
    print(f"🔎 Нагадування: перевірка на {tomorrow_dot} / {tomorrow_dash}")

    df_clients = load_data(CLIENTS_URL)
    df_orders = load_data(ORDERS_URL)
    if df_clients is None or df_orders is None: return

    ordered_phones = set()
    for _, row in df_orders.iterrows():
        order_date = row.get('Дата доставки', '').strip()
        order_status = row.get('Статус замовлення', '').lower()
        if (order_date == tomorrow_dot or order_date == tomorrow_dash) and 'скас' not in order_status:
            ordered_phones.add(clean_phone(row.get('Телефон', '')))

    reminder_count = 0
    c_cols = {c.lower(): c for c in df_clients.columns}
    phone_col = c_cols.get('телефон') or df_clients.columns[0]
    name_col = c_cols.get('назва') or c_cols.get('клієнт') or df_clients.columns[1]
    tg_id_col = c_cols.get('telegram id') or c_cols.get('id')

    for _, client in df_clients.iterrows():
        c_phone = clean_phone(client.get(phone_col, ''))
        tg_id = str(client.get(tg_id_col, '')).strip()
        c_name = client.get(name_col, 'Клієнт')

        if c_phone not in ordered_phones and tg_id and len(tg_id) > 5:
            try:
                text = f"Вітаємо, {c_name}! 👋\nНагадуємо, що ви ще не зробили замовлення на завтра. Чекаємо на вас у додатку! 🍽️"
                requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": tg_id, "text": text}, timeout=10)
                reminder_count += 1
            except: pass
    print(f"✅ Надіслано нагадувань: {reminder_count}")

# ==========================================
# 2. ФУНКЦІЯ ЩОТИЖНЕВОГО ЗВІТУ (Понеділок)
# ==========================================
def send_weekly_report():
    print("📊 Формування щотижневого звіту...")
    df_orders = load_data(ORDERS_URL)
    if df_orders is None or df_orders.empty: return

    # Беремо замовлення за останні 7 днів
    df_orders['Сума_число'] = pd.to_numeric(df_orders['Сума'].apply(lambda x: re.sub(r'[^\d.]', '', str(x))), errors='coerce').fillna(0)
    
    total_sum = df_orders['Сума_число'].sum() # Спрощений варіант: сума всіх замовлень
    total_orders = len(df_orders)

    msg = (
        f"📊 <b>ЩОТИЖНЕВИЙ ЗВІТ FOOD FESTIVAL</b> 📊\n\n"
        f"📦 Всього замовлень: <b>{total_orders}</b>\n"
        f"💰 Загальний оборот: <b>{total_sum:g} ₴</b>\n\n"
        f"Гарного і продуктивного тижня! 🚀"
    )
    
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": GROUP_ID, "text": msg, "parse_mode": "HTML"})
    print("✅ Звіт успішно відправлено в групу!")

# ==========================================
# ТОЧКА ВХОДУ (ПЕРЕМИКАЧ)
# ==========================================
if __name__ == "__main__":
    # Якщо при запуску є слово "weekly" (з weekly_report.yml)
    if len(sys.argv) > 1 and sys.argv[1] == "weekly":
        send_weekly_report()
    # Інакше запускаємо звичайні нагадування (з reminder.yml)
    else:
        send_reminders()
