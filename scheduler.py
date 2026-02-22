import sys
import requests
import pandas as pd
import io
from datetime import datetime, timedelta

# ==========================================
# 📢 НАЛАШТУВАННЯ TELEGRAM
# ==========================================
TELEGRAM_TOKEN = "8183938320:AAHsDhUXcu3ZeKg8Qh3AZc3xbXMa9YqqqZc" # Токен бота

GROUP_ID = "-1005236190167" # Група для замовлень
DIRECTOR_ID = "636970008"   # Директор Едуард
DEV_ID = "6856949294"       # Микола (Розробник)
def send_msg(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

def run_report(report_type):
    try:
        ord_res = requests.get(ORDERS_URL).content
        cli_res = requests.get(CLIENTS_URL).content
        df_orders = pd.read_csv(io.StringIO(ord_res.decode('utf-8')))
        df_clients = pd.read_csv(io.StringIO(cli_res.decode('utf-8')))
    except: return

    # Об'єднуємо дані, щоб знати Менеджера кожного замовлення
    df = pd.merge(df_orders, df_clients[['Телефон', 'Менеджер']], on='Телефон', how='left')
    df['Дата_dt'] = pd.to_datetime(df['Дата'], format='%d.%m.%Y %H:%M:%S', errors='coerce')
    df['Сума'] = pd.to_numeric(df['Сума'], errors='coerce').fillna(0)

    now = datetime.now()
    if report_type == "weekly":
        start_date = now - timedelta(days=7)
        title = "📊 ТИЖНЕВИЙ ЗВІТ"
    else:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        title = "📅 ЩОДЕННИЙ ЗВІТ"
    
    df_p = df[df['Дата_dt'] >= start_date].copy()

    # 1. ЗВІТ ДЛЯ ДИРЕКТОРА (тільки у п'ятницю / weekly)
    if report_type == "weekly":
        total = df_p['Сума'].sum()
        msg = f"{title} (ДИРЕКТОР)\n"
        msg += f"💰 Оборот за тиждень: <b>{total:,.0f} ₴</b>\n\n"
        msg += "👥 <b>Результати менеджерів:</b>\n"
        m_stats = df_p.groupby('Менеджер')['Сума'].sum()
        for m, s in m_stats.items():
            msg += f"👤 {m}: {s:,.0f} ₴\n"
        send_msg(DIRECTOR_CHAT_ID, msg)

    # 2. ПЕРСОНАЛЬНІ ЗВІТИ ДЛЯ МЕНЕДЖЕРІВ
    # (Надсилаються окремими блоками в загальну групу)
    for manager in df_p['Менеджер'].unique():
        if pd.isna(manager) or manager == "": continue
        
        m_df = df_p[df_p['Менеджер'] == manager]
        m_sum = m_df['Сума'].sum()
        
        m_msg = f"{title}: <b>{manager}</b>\n"
        m_msg += f"💰 Продажі по твоїх клієнтах: <b>{m_sum:,.0f} ₴</b>\n"
        m_msg += f"📦 К-сть замовлень: {len(m_df)}\n"
        
        if not m_df.empty:
            top_c = m_df.groupby('Клієнт')['Сума'].sum().idxmax()
            m_msg += f"⭐ Твій топ-клієнт: {top_c}\n"
            
        send_msg(DIRECTOR_CHAT_ID, m_msg)

if __name__ == "__main__":
    # Читаємо аргумент: daily або weekly
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    run_report(mode)
