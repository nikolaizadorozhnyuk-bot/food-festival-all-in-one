import sys
import requests
import pandas as pd
import io
from datetime import datetime, timedelta

# ==========================================
# 🔑 ПОСИЛАННЯ НА ТАБЛИЦІ
# ==========================================
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"

# ==========================================
# 📢 НАЛАШТУВАННЯ TELEGRAM
# ==========================================
TELEGRAM_TOKEN = "8183938320:AAHsDhUXcu3ZeKg8Qh3AZc3xbXMa9YqqqZc" # Токен бота

GROUP_ID = "-1005236190167" # Група для замовлень
DIRECTOR_ID = "636970008"   # Директор Едуард
DEV_ID = "6856949294"       # Микола (Розробник)

def send_msg(chat_ids, text):
    """Відправляє повідомлення одному або кільком користувачам/групам"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if isinstance(chat_ids, str): 
        chat_ids = [chat_ids]
        
    for chat_id in chat_ids:
        try:
            requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
        except Exception:
            pass

def run_report(report_type):
    try:
        ord_res = requests.get(ORDERS_URL).content
        cli_res = requests.get(CLIENTS_URL).content
        df_orders = pd.read_csv(io.StringIO(ord_res.decode('utf-8')))
        df_clients = pd.read_csv(io.StringIO(cli_res.decode('utf-8')))
    except Exception as e: 
        send_msg(DEV_ID, f"⚠️ Помилка завантаження бази для звіту: {e}")
        return

    # Об'єднуємо дані
    df = pd.merge(df_orders, df_clients[['Телефон', 'Менеджер']], on='Телефон', how='left')
    
    if 'Менеджер_x' in df.columns and 'Менеджер_y' in df.columns:
        df['Менеджер'] = df['Менеджер_x'].combine_first(df['Менеджер_y'])

    df['Дата_dt'] = pd.to_datetime(df['Дата'], format='%d.%m.%Y %H:%M:%S', errors='coerce')
    df['Сума'] = pd.to_numeric(df['Сума'], errors='coerce').fillna(0)

    now = datetime.now()
    if report_type == "weekly":
        start_date = now - timedelta(days=7)
        title = "📊 ТИЖНЕВИЙ ЗВІТ COMPANIY"
    else:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        title = "📅 ЩОДЕННИЙ ЗВІТ COMPANY"
    
    df_p = df[df['Дата_dt'] >= start_date].copy()
    if df_p.empty:
        return

    # 1. ЗАГАЛЬНА ІНФОРМАЦІЯ (В загальну групу + Керівництву)
    if report_type == "weekly":
        total = df_p['Сума'].sum()
        msg = f"{title}\n"
        msg += f"💰 Загальний оборот: <b>{total:,.0f} ₴</b>\n\n"
        msg += "👥 <b>Оборот по менеджерах:</b>\n"
        m_stats = df_p.groupby('Менеджер')['Сума'].sum()
        for m, s in m_stats.items():
            if pd.notna(m) and str(m).strip() != "":
                msg += f"👤 {m}: {s:,.0f} ₴\n"
                
        # Відправляємо в загальну групу, директору і тобі
        send_msg([GROUP_ID, DIRECTOR_ID, DEV_ID], msg)

    # 2. ПЕРСОНАЛЬНІ ЗВІТИ ДЛЯ МЕНЕДЖЕРІВ (Тільки в особисті повідомлення!)
    for manager in df_p['Менеджер'].unique():
        if pd.isna(manager) or str(manager).strip() == "": continue
        
        m_df = df_p[df_p['Менеджер'] == manager]
        m_sum = m_df['Сума'].sum()
        
        m_msg = f"{title}\n👨‍💼 <b>{manager}</b>, твій персональний звіт:\n"
        m_msg += f"💰 Твої продажі: <b>{m_sum:,.0f} ₴</b>\n"
        m_msg += f"📦 К-сть замовлень: {len(m_df)}\n"
        
        if not m_df.empty:
            top_c = m_df.groupby('Клієнт')['Сума'].sum().idxmax()
            m_msg += f"⭐ Твій топ-клієнт: {top_c}\n"
            
        # Шукаємо Telegram ID менеджера в таблиці Клієнти (стовпчик "Назва" має збігатися з іменем)
        manager_row = df_clients[df_clients['Назва'].astype(str).str.strip() == str(manager).strip()]
        
        if not manager_row.empty:
            manager_tg_id = str(manager_row.iloc[0].get('Telegram ID', '')).strip()
            # Перевіряємо, чи вписаний ID і чи це цифри
            if manager_tg_id and manager_tg_id.lower() != 'nan' and manager_tg_id.replace('-', '').isdigit():
                send_msg(manager_tg_id, m_msg)
            else:
                # Якщо ID немає, система тихенько напише тобі в особисті, щоб ти виправив таблицю
                send_msg(DEV_ID, f"⚠️ Не можу відправити звіт. У менеджера '{manager}' не вказано Telegram ID у таблиці.")
        else:
            send_msg(DEV_ID, f"⚠️ Не знайшов менеджера '{manager}' у стовпчику 'Назва'. Звіт не відправлено.")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    run_report(mode)
