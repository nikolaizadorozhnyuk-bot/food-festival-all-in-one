import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime, timedelta
from PIL import Image
import xlsxwriter

# ==========================================
# 🔑 НАЛАШТУВАННЯ (FOOD FESTIVAL)
# ==========================================
OWNER_PHONE = "0675953220"
COMPANY_NAME = "Food Festival"
LOGO_URL = "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaFzeDCKyGghOoel888Xx_QkEaYTytH2te1BsJlSlUAqKYg1LyxF0_AwogvNPOU1PX/exec"

# Посилання на CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"
NEWS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=374278986&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv"

# ==========================================
# 📢 НАЛАШТУВАННЯ TELEGRAM-МАРШРУТИЗАЦІЇ
# ==========================================
TELEGRAM_TOKEN = "8183938320:AAHsDhUXcu3ZeKg8Qh3AZc3xbXMa9YqqqZc"

GROUP_ID = "-1005236190167" # Виправлений ID супергрупи!
DIRECTOR_ID = "636970008"   # Директор
DEV_ID = "8297615872"       # Микола (Розробник)

st.set_page_config(page_title="Food Festival ERP", page_icon=LOGO_URL, layout="wide")

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
@st.cache_data(ttl=30)
def load_data(url):
    try: return pd.read_csv(url, dtype=str).fillna('')
    except: return None

def send_to_telegram(text, target="group"):
    """Розумна маршрутизація повідомлень"""
    if target == "group":
        chat_ids = [GROUP_ID]
    elif target == "management":
        chat_ids = [DIRECTOR_ID, DEV_ID]
    elif target == "all":
        chat_ids = [GROUP_ID, DIRECTOR_ID, DEV_ID]
    else:
        chat_ids = [target]
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    for chat_id in chat_ids:
        try:
            requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
        except Exception:
            pass

def send_update(payload):
    try: return requests.post(SCRIPT_URL, json=payload, timeout=15).text
    except: return "Error"

# --- СЕСІЯ ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- РОЗДІЛ: ПРОМО РОЗРОБНИКА ---
def show_developer_promo():
    st.title("🚀 Бажаєте такий додаток для свого бізнесу?")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Перетворіть ваш бізнес на цифрову систему!
        Я розробляю індивідуальні рішення, які допомагають автоматизувати продажі та звітність:
        
        * **✅ Мобільний каталог та кошик** — ваші клієнти замовляють у 3 кліки.
        * **✅ База на Google Таблицях** — зручне та безкоштовне керування без складних баз даних.
        * **✅ Розумні Telegram-боти** — миттєві сповіщення про замовлення.
        * **✅ Адмін-панелі** — бачте прибуток, топ-товари та активність.
        * **✅ Автоматизація рутини** — система сама надсилає звіти менеджерам.
        """)
    
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/3142/3142121.png", use_container_width=True)

    st.divider()
    st.subheader("📊 Кейс Food Festival")
    st.write("На базі цього додатка реалізовано:")
    st.write("• Автоматичний поділ замовлень по менеджерах.")
    st.write("• Розумний контроль часу доставки (до/після 11:00).")
    st.write("• Щоденна та щотижнева звітність для всієї команди.")

    st.divider()
    st.subheader("📩 Зв'язатися з розробником")
    
    c1, c2 = st.columns(2)
    with c1: st.link_button("✈️ Написати в Telegram", "https://t.me/FoodFestival_Odesa", use_container_width=True)
    with c2: st.link_button("📞 Зателефонувати", "tel:+380675953220", use_container_width=True)
    
    st.info("💡 Розробка індивідуального рішення займає від 3-х днів. Зробіть свій бізнес ефективнішим вже сьогодні!")

# --- ГОЛОВНИЙ ЕКРАН ТА МАРШРУТИЗАЦІЯ ---
def main():
    if not st.session_state.logged_in:
        show_login()
        return

    u = st.session_state.user_info
    role = u.get('Роль', 'Client')
    is_admin = role in ['Owner', 'Admin', 'Manager']
    
    st.sidebar.image(LOGO_URL, width=150)
    st.sidebar.success(f"👤 {u.get('Назва')} | {role}")
    
    menu = ["🍎 Каталог", "🛒 Кошик", "📜 Історія замовлень", "📰 Новини", "📞 Дзвінок", "🚀 Власний додаток?"]
    if is_admin:
        menu.insert(3, "📊 Адмін-панель")
        menu.append("🔔 Нагадування")
    
    choice = st.sidebar.selectbox("📍 Навігація:", menu)
    
    if st.sidebar.button("🚪 Вийти", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    st.sidebar.divider()
    st.sidebar.caption("Розробка систем автоматизації")
    st.sidebar.write("👤 **Микола Задорожнюк**")
    st.sidebar.write("📞 +380 67 595 32 20")

    if choice == "🍎 Каталог": show_catalog(u)
    elif choice == "🛒 Кошик": show_cart(u)
    elif choice == "📊 Адмін-панель": show_admin_panel()
    elif choice == "📜 Історія замовлень": show_history(u)
    elif choice == "📰 Новини": show_news()
    elif choice == "📞 Дзвінок": show_callback(u)
    elif choice == "🔔 Нагадування": show_reminders(u)
    elif choice == "🚀 Власний додаток?": show_developer_promo()

    hide_st_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """
    st.markdown(hide_st_style, unsafe_allow_html=True)

    st.divider() 
    footer_html = """
        <div style='text-align: center; color: #888; font-size: 13px; padding-bottom: 20px;'>
            Розроблено <b>Миколою Задорожнюком</b> | 🚀 Automation & ERP Solutions © 2026<br>
            Бажаєте автоматизувати свій бізнес? <a href='https://t.me/FoodFestival_Odesa' target='_blank' style='color: #4CAF50; text-decoration: none; font-weight: bold;'>Замовити розробку</a>
        </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

# --- РОЗДІЛ: АДМІН-ПАНЕЛЬ (АНАЛІТИКА) ---
def show_admin_panel():
    st.title("📊 Аналітика продажів")
    df = load_data(ORDERS_URL)
    
    if df is not None and not df.empty:
        df['Сума'] = pd.to_numeric(df['Сума'], errors='coerce').fillna(0)
        df['Дата_dt'] = pd.to_datetime(df['Дата'], format='%d.%m.%Y %H:%M:%S', errors='coerce')
        
        c1, c2, c3 = st.columns(3)
        total_sales = df['Сума'].sum()
        this_month = df[df['Дата_dt'] >= datetime.now().replace(day=1)]['Сума'].sum()
        active_clients = df['Телефон'].nunique()
        
        c1.metric("Загальний оборот", f"{total_sales:,.0f} ₴".replace(',', ' '))
        c2.metric("Оборот за місяць", f"{this_month:,.0f} ₴".replace(',', ' '))
        c3.metric("Унікальних клієнтів", active_clients)
        
        st.divider()
        st.subheader("📈 Динаміка замовлень")
        chart_data = df.groupby(df['Дата_dt'].dt.date)['Сума'].sum()
        st.area_chart(chart_data)
        
        st.subheader("🏆 Топ затребуваних товарів")
        all_items = []
        for items_str in df['Товари']:
            parts = [p.split(' (')[0].strip() for p in str(items_str).split(';') if '(' in p]
            all_items.extend(parts)
        
        if all_items:
            top_df = pd.Series(all_items).value_counts().head(10)
            st.bar_chart(top_df)
        
        st.subheader("👥 Найактивніші клієнти")
        client_stats = df.groupby('Клієнт').agg({
            'Сума': 'sum',
            'Дата': 'count'
        }).rename(columns={'Дата': 'К-сть замовлень'}).sort_values(by='Сума', ascending=False)
        st.dataframe(client_stats, use_container_width=True)
    else:
        st.warning("Дані для аналітики поки відсутні.")

# --- РЕШТА ФУНКЦІЙ ---
def show_login():
    st.image(LOGO_URL, width=200)
    phone = st.text_input("Введіть номер телефону:")
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
    st.title("🍎 Каталог")
    df = load_data(SHEET_URL)
    if df is not None:
        p_col = u.get('Колонка прайс', 'Ціна')
        d_val = str(u.get('Знижка', '0')).replace('%','')
        disc = float(d_val)/100 if d_val.replace('.','').isdigit() else 0
        if st.button("📦 Завантажити прайс Excel з фото"):
            with st.spinner("⏳ Створюємо файл... Це може зайняти до 20 секунд (завантажуються фото)."):
                excel = export_to_excel_full(df, disc, p_col, u['Назва'])
                send_to_telegram(f"📥 Прайс завантажено: {u['Назва']}", target=DEV_ID)
                st.download_button("📥 Завантажити файл", excel, "Price_FF.xlsx", use_container_width=True)
        search = st.text_input("🔍 Пошук товара:")
        f_df = df[df['Товар'].str.contains(search, case=False)] if search else df
        for _, row in f_df.iterrows():
            with st.container():
                c1, c2 = st.columns([1, 2])
                with c1: st.image(row['Фото'] if pd.notna(row['Фото']) and row['Фото'] else "https://via.placeholder.com/150", use_container_width=True)
                with c2:
                    st.subheader(row['Товар'])
                    if row.get('Опис'): st.info(row['Опис'])
                    p_raw = float(str(row.get(p_col, '0')).replace(',', '.'))
                    final_p = p_raw * (1 - disc)
                    st.write(f"💰 **Ціна: {final_p:g} ₴** | Залишок: {row.get('Залишок', '0')}")
                    qty = st.number_input(f"К-сть ({row['Артикул']})", min_value=0.0, step=1.0, key=f"q_{row['Артикул']}")
                    if qty > 0: st.session_state.cart[row['Товар']] = {'qty': qty, 'price': final_p, 'art': row['Артикул']}
            st.divider()

def show_cart(u):
    st.title("🛒 Кошик")
    if not st.session_state.cart: 
        st.info("Кошик порожній.")
    else:
        now = datetime.now()
        cutoff_time = now.replace(hour=11, minute=0, second=0, microsecond=0)
        is_late = now > cutoff_time
        
        if is_late:
            st.warning("⚠️ Зверніть увагу: замовлення прийняте після 11:00, тому доставка буде здійснена ЗАВТРА.")
            delivery_status = "ДОСТАВКА НА ЗАВТРА"
        else:
            st.success("✅ Замовлення прийняте до 11:00. Доставка згідно з графіком на сьогодні.")
            delivery_status = "ДОСТАВКА НА СЬОГОДНІ"
        
        total = 0; items_txt = ""
        for n, d in st.session_state.cart.items():
            total += d['qty'] * d['price']
            st.write(f"• {n} — {d['qty']} шт. ({d['qty']*d['price']:g} ₴)")
            items_txt += f"{n} ({d['qty']} шт.); "
            
        st.subheader(f"Сума: {total:g} ₴")
        addr = st.text_input("Адреса доставки:")
        comm = st.text_area("Коментар:")
        deliv = st.selectbox("Спосіб доставки", ["Доставка Food Festival", "Самовивіз", "Нова Пошта"])
        
        if st.button("🚀 ВІДПРАВИТИ ЗАМОВЛЕННЯ", use_container_width=True):
            msg = (f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ!</b>\n"
                   f"⏰ <b>{delivery_status}</b>\n"
                   f"👤 {u['Назва']}\n"
                   f"📞 {u['Телефон']}\n"
                   f"💰 Сума: {total:g} ₴\n"
                   f"🚚 {deliv}: {addr}\n"
                   f"🛒 {items_txt}\n"
                   f"💬 {comm}")
            
            send_to_telegram(msg, target="group")
            
            send_update({
                "type": "NEW_ORDER", 
                "phone": u['Телефон'], 
                "client": u['Назва'], 
                "total": total, 
                "items": items_txt, 
                "comment": f"[{delivery_status}] " + comm, 
                "delivery_address": addr, 
                "delivery_method": deliv
            })
            st.balloons()
            st.success(f"✅ Замовлення надіслано! {delivery_status}")
            st.session_state.cart = {}

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
                    st.write(f"🏠 **Адреса:** {o.get('Адреса доставки', 'Не вказано')}")

def show_news():
    st.title("📰 Новини")
    df = load_data(NEWS_URL)
    if df is not None:
        for _, r in df.iloc[::-1].iterrows():
            st.subheader(r.get('Заголовок')); st.write(r.get('Текст новини')); st.divider()

def show_callback(u):
    st.title("📞 Зворотній зв'язок")
    if st.button("🆘 ПЕРЕТЕЛЕФОНУЙТЕ МЕНІ", use_container_width=True):
        send_to_telegram(f"☎️ <b>ЗАПИТ НА ДЗВІНОК!</b>\n👤 {u['Назва']}\n📞 {u['Телефон']}", target=DEV_ID)
        st.success("✅ Запит надіслано! Менеджер скоро зателефонує.")

def show_reminders(u):
    st.title("🔔 Нагадування")
    if st.button("📢 Відправити всім нагадування в Telegram"):
        send_to_telegram("🔔 <b>Food Festival:</b> Не забудьте зробити замовлення на завтра!", target="group")
        st.success("✅ Надіслано у загальну групу!")

# --- ПРЕМІУМ ЕКСПОРТ EXCEL (З ФОТО ТА КОНВЕРТАЦІЄЮ WEBP) ---
def export_to_excel_full(df, user_discount, p_col, user_name):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Каталог')
    
    # Стилі
    header_style = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#D4AC0D'})
    table_header = workbook.add_format({'bold': True, 'bg_color': '#FFD966', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
    money = workbook.add_format({'num_format': '#,##0.00 ₴', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
    border_center = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
    border_left = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
    
    # Ширина колонок
    worksheet.set_column('A:A', 14)  
    worksheet.set_column('B:B', 15)  
    worksheet.set_column('C:C', 45)  
    worksheet.set_column('D:D', 12)  
    worksheet.set_column('E:E', 10)  
    worksheet.set_column('F:G', 15)  

    # Лого та шапка
    try:
        response = requests.get(LOGO_URL, timeout=5)
        worksheet.insert_image('A1', LOGO_URL, {'image_data': io.BytesIO(response.content), 'x_scale': 0.4, 'y_scale': 0.4})
    except: pass
    
    worksheet.write('B1', COMPANY_NAME, header_style)
    worksheet.write('B2', f"Клієнт: {user_name} | Дата: {datetime.now().strftime('%d.%m.%Y')}")
    
    headers = ['Фото', 'Категорія', 'Товар', 'Артикул', 'Залишок', 'Ціна', 'Ваша ціна']
    for col_num, h in enumerate(headers): 
        worksheet.write(6, col_num, h, table_header)
        
    # Заповнення
    for row_num, (_, row) in enumerate(df.iterrows(), start=7):
        worksheet.set_row(row_num, 60)
        
        # Фото (З розумною конвертацією)
        img_url = str(row.get('Фото', '')).strip()
        if img_url.startswith('http'):
            try:
                # Маскуємося під звичайний браузер
                headers_req = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                img_resp = requests.get(img_url, headers=headers_req, timeout=5)
                
                if img_resp.status_code == 200:
                    img_data = io.BytesIO(img_resp.content)
                    
                    try:
                        # Відкриваємо картинку через Pillow
                        img = Image.open(img_data)
                        # Якщо формат не підходить для Excel (наприклад, WebP) - конвертуємо!
                        if img.format not in ['JPEG', 'PNG', 'BMP']:
                            img = img.convert('RGB')
                            img_data = io.BytesIO()
                            img.save(img_data, format='JPEG')
                        
                        img_data.seek(0)
                        worksheet.insert_image(row_num, 0, img_url, {'image_data': img_data, 'x_scale': 0.15, 'y_scale': 0.15, 'object_position': 1})
                    except Exception:
                        worksheet.write(row_num, 0, 'Формат не підт.', border_center)
                else:
                    worksheet.write(row_num, 0, 'Немає доступу', border_center)
            except:
                worksheet.write(row_num, 0, 'Таймаут', border_center)
        else:
            worksheet.write(row_num, 0, '-', border_center)

        # Текст
        worksheet.write(row_num, 1, str(row.get('Категорія', '')), border_center)
        worksheet.write(row_num, 2, str(row.get('Товар', '')), border_left)
        worksheet.write(row_num, 3, str(row.get('Артикул', '')), border_center)
        worksheet.write(row_num, 4, str(row.get('Залишок', '')), border_center)
        
        # Ціна
        try:
            p = float(str(row.get(p_col, '0')).replace(',', '.'))
            worksheet.write(row_num, 5, p, money)
            worksheet.write(row_num, 6, p * (1 - user_discount), money)
        except: 
            worksheet.write(row_num, 5, 0, money)
            worksheet.write(row_num, 6, 0, money)
            
    workbook.close()
    return output.getvalue()

if __name__ == "__main__":
    main()
