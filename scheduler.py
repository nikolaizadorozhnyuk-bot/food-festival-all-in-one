import sys, requests, pandas as pd, io
from datetime import datetime, timedelta

# Налаштування
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
TELEGRAM_TOKEN = "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU"
GROUP_ID = "-1003641918928" 

def send_msg(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

def run_report():
    try:
        df_orders = pd.read_csv(ORDERS_URL)
        df_clients = pd.read_csv(CLIENTS_URL)
        df_orders['Дата_dt'] = pd.to_datetime(df_orders['Дата'], format='%d.%m.%Y %H:%M:%S', errors='coerce')
        df_p = df_orders[df_orders['Дата_dt'] >= (datetime.now() - timedelta(days=7))].copy()
        
        # 📊 Загальний звіт у супергрупу
        total = df_p['Сума'].sum()
        msg = f"📊 <b>ТИЖНЕВИЙ ЗВІТ FOOD FESTIVAL</b>\n💰 Загальний оборот: <b>{total:,.0f} ₴</b>"
        send_msg(GROUP_ID, msg)
        
        # 📈 Персональні звіти менеджерам в особисті (ID з стовпчика F)
        for manager in df_p['Менеджер'].unique():
            if pd.isna(manager): continue
            m_sum = df_p[df_p['Менеджер'] == manager]['Сума'].sum()
            m_id = df_clients[df_clients['Назва'] == manager]['Telegram ID'].values
            if len(m_id) > 0 and str(m_id[0]).isdigit():
                send_msg(str(m_id[0]), f"📈 {manager}, твій результат за тиждень: {m_sum:,.0f} ₴")
    except: pass

if __name__ == "__main__":
    run_report()
