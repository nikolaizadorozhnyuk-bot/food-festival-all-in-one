import sys
import requests
import pandas as pd
import io
from datetime import datetime, timedelta

# ==========================================
# 🔑 ПОСИЛАННЯ НА ТАБЛИЦІ (CSV)
# ==========================================
# Аркуш "Замовлення"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv"
# Аркуш "Клієнти"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
# Аркуш "Прайс" (для отримання фото товарів)
PRICE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv"

# ==========================================
# 📢 НАЛАШТУВАННЯ TELEGRAM
# ==========================================
TELEGRAM_TOKEN = "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU"
GROUP_ID = "-1003641918928" # Твоя супергрупа
DIRECTOR_ID = "636970008"   
OWNER_ID = "6856949294"      

def send_photo_report(chat_id, text, photo_url):
    """Надсилає фото з підписом або просто повідомлення, якщо фото немає"""
    if photo_url and str(photo_url).startswith('http'):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        try:
            requests.post(url, data={"chat_id": chat_id, "photo": photo_url, "caption": text, "parse_mode": "HTML"}, timeout=10)
            return
        except: pass
    
    # Якщо фото не пройшло або його немає — шлемо текст
    url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url_msg, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

def run_report(report_type="weekly"):
    try:
        # Завантаження даних
        ord_res = requests.get(ORDERS_URL).content
        cli_res = requests.get(CLIENTS_URL).content
        pri_res = requests.get(PRICE_URL).content
        
        df_orders = pd.read_csv(io.StringIO(ord_res.decode('utf-8')))
        df_clients = pd.read_csv(io.StringIO(cli_res.decode('utf-8')))
        df_price = pd.read_csv(io.StringIO(pri_res.decode('utf-8')))
    except Exception as e:
        return

    # Обробка даних
    df_orders['Дата_dt'] = pd.to_datetime(df_orders['Дата'], format='%d.%m.%Y %H:%M:%S', errors='coerce')
    df_orders['Сума'] = pd.to_numeric(df_orders['Сума'], errors='coerce').fillna(0)

    now = datetime.now()
    start_date = now - timedelta(days=7) if report_type == "weekly" else now.replace(hour=0, minute=0, second=0)
    df_p = df_orders[df_orders['Дата_dt'] >= start_date].copy()
    
    if df_p.empty: return

    # 1. ЗАГАЛЬНИЙ ЗВІТ (У групу та керівництву)
    total_revenue = df_p['Суma'].sum()
    
    # Шукаємо хіт продажів всієї компанії
    all_items = []
    for row in df_p['Товари'].dropna():
        items = [i.split(' (')[0].strip() for i in str(row).split(';') if '(' in i]
        all_items.extend(items)
    
    global_top_item = pd.Series(all_items).value_counts().idxmax() if all_items else None
    global_photo = ""
    if global_top_item:
        p_row = df_price[df_price['Товар'] == global_top_item]
        if not p_row.empty: global_photo = str(p_row.iloc[0].get('Фото', ''))

    summary_msg = f"📊 <b>{report_type.upper()} ЗВІТ FOOD FESTIVAL</b>\n"
    summary_msg += f"💰 Оборот: <b>{total_revenue:,.0f} ₴</b>\n"
    if global_top_item: summary_msg += f"🔥 Хіт тижня: {global_top_item}\n"
    
    # Відправляємо в групу з фото хіта
    send_photo_report(GROUP_ID, summary_msg, global_photo)
    # Керівництву також шлемо
    for admin in [DIRECTOR_ID, OWNER_ID]:
        send_photo_report(admin, summary_msg, global_photo)

    # 2. ПЕРСОНАЛЬНІ ЗВІТИ МЕНЕДЖЕРАМ (В особисті)
    for manager_name in df_p['Менеджер'].unique():
        if pd.isna(manager_name) or str(manager_name).strip() == "": continue
        
        m_df = df_p[df_p['Менеджер'] == manager_name]
        m_sum = m_df['Сума'].sum()
        
        # Шукаємо топ-товар конкретного менеджера
        m_items = []
        for row in m_df['Товари'].dropna():
            items = [i.split(' (')[0].strip() for i in str(row).split(';') if '(' in i]
            m_items.extend(items)
        
        m_top_item = pd.Series(m_items).value_counts().idxmax() if m_items else None
        m_photo = ""
        if m_top_item:
            p_row = df_price[df_price['Товар'] == m_top_item]
            if not p_row.empty: m_photo = str(p_row.iloc[0].get('Фото', ''))

        personal_msg = f"📈 <b>Твій тижневий звіт: {manager_name}</b>\n"
        personal_msg += f"💰 Твої продажі: <b>{m_sum:,.0f} ₴</b>\n"
        if m_top_item: personal_msg += f"⭐ Твій лідер продажів: {m_top_item}"
        
        # Знаходимо ID менеджера в таблиці
        m_info = df_clients[df_clients['Назва'].astype(str).str.strip() == str(manager_name).strip()]
        if not m_info.empty:
            tg_id = str(m_info.iloc[0].get('Telegram ID', '')).strip() # Використовуємо стовпчик F
            if tg_id and tg_id.replace('-', '').isdigit():
                send_photo_report(tg_id, personal_msg, m_photo)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "weekly"
    run_report(mode)
