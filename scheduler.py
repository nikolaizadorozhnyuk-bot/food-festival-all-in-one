import sys
import requests
import pandas as pd
import io
from datetime import datetime, timedelta

# ==========================================
# 🔑 ПОСИЛАННЯ НА ТАБЛИЦІ (CSV)
# ==========================================
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"

# ==========================================
# 📢 НАЛАШТУВАННЯ TELEGRAM
# ==========================================
# ВСТАВ ПОВНИЙ ТОКЕН НОВОГО БОТА (8275141603:...)
TELEGRAM_TOKEN = "8275141603:ВСТАВ_СЮДИ_СЕКРЕТНУ_ЧАСТИНУ_ТОКЕНА"

GROUP_ID = "-1005236190167" 
DIRECTOR_ID = "636970008"   
OWNER_ID = "6856949294"      

def send_msg(chat_ids, text):
    """Відправка повідомлень (одному або списку ID)"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if isinstance(chat_ids, (str, int)): 
        chat_ids = [chat_ids]
    for chat_id in chat_ids:
        try:
            requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
        except: pass

def run_report(report_type="weekly"):
    try:
        # Завантаження даних
        ord_res = requests.get(ORDERS_URL).content
        cli_res = requests.get(CLIENTS_URL).content
        df_orders = pd.read_csv(io.StringIO(ord_res.decode('utf-8')))
        df_clients = pd.read_csv(io.StringIO(cli_res.decode('utf-8')))
    except Exception as e:
        send_msg(OWNER_ID, f"⚠️ Помилка завантаження даних: {e}")
        return

    # Обробка дат та сум
    df_orders['Дата_dt'] = pd.to_datetime(df_orders['Дата'], format='%d.%m.%Y %H:%M:%S', errors='coerce')
    df_orders['Сума'] = pd.to_numeric(df_orders['Сума'], errors='coerce').fillna(0)

    # Фільтрація за тиждень (або день)
    now = datetime.now()
    start_date = now - timedelta(days=7) if report_type == "weekly" else now.replace(hour=0, minute=0, second=0)
    df_p = df_orders[df_orders['Дата_dt'] >= start_date].copy()
    
    if df_p.empty:
        return

    # 1. ЗАГАЛЬНИЙ ЗВІТ (У групу та Керівництву)
    total_revenue = df_p['Сума'].sum()
    summary_msg = f"📊 <b>{report_type.upper()} ЗВІТ FOOD FESTIVAL</b>\n"
    summary_msg += f"💰 Загальний оборот: <b>{total_revenue:,.0f} ₴</b>\n"
    summary_msg += f"📦 К-сть замовлень: {len(df_p)}\n\n"
    
    # Групування по менеджерах для загальної статистики
    # Використовуємо стовпчик 'Менеджер' з таблиці замовлень (стовпчик J)
    m_stats = df_p.groupby('Менеджер')['Сума'].sum().sort_values(ascending=False)
    for m, s in m_stats.items():
        if pd.notna(m) and str(m).strip() != "":
            summary_msg += f"👤 {m}: {s:,.0f} ₴\n"

    send_msg([GROUP_ID, DIRECTOR_ID, OWNER_ID], summary_msg)

    # 2. ПЕРСОНАЛЬНІ ЗВІТИ (В особисті повідомлення менеджерам)
    for manager_name in df_p['Менеджер'].unique():
        if pd.isna(manager_name) or str(manager_name).strip() == "": continue
        
        m_df = df_p[df_p['Менеджер'] == manager_name]
        m_sum = m_df['Сума'].sum()
        
        personal_msg = f"📈 <b>Твій особистий звіт: {manager_name}</b>\n"
        personal_msg += f"💰 Продажі: <b>{m_sum:,.0f} ₴</b>\n"
        personal_msg += f"🛒 Замовлень: {len(m_df)}\n"
        
        # Пошук Telegram ID менеджера в таблиці Клієнти
        m_row = df_clients[df_clients['Назва'].astype(str).str.strip() == str(manager_name).strip()]
        if not m_row.empty:
            tg_id = str(m_row.iloc[0].get('Telegram ID', '')).strip()
            if tg_id and tg_id.replace('-', '').isdigit():
                send_msg(tg_id, personal_msg)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "weekly"
    run_report(mode)
