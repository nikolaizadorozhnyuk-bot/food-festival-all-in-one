import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- НАЛАШТУВАННЯ СТОРІНКИ ---
st.set_page_config(page_title="Miko Supply CRM", page_icon="🛒", layout="wide")

# --- CSS СТИЛІ ДЛЯ РІВНИХ КАРТОК ---
st.markdown("""
<style>
    .product-img-box {
        height: 160px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        margin-bottom: 8px;
        background-color: #ffffff;
        border-radius: 6px;
    }
    .product-img-box img {
        max-height: 160px;
        max-width: 100%;
        object-fit: contain;
    }
    .product-title {
        font-size: 15px;
        font-weight: 600;
        height: 40px;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        margin-bottom: 6px;
        line-height: 1.3;
    }
    .product-meta {
        font-size: 12px;
        color: #8c959f;
        height: 22px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-family: monospace;
    }
    .stock-badge {
        background-color: #238636;
        color: #ffffff;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 11px;
        font-family: sans-serif;
    }
    div[data-testid="stButton"] button {
        padding-left: 8px !important;
        padding-right: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- ГОЛОВНІ НАЛАШТУВАННЯ ---
TELEGRAM_BOT_TOKEN = "9287222887:AAGxr1QuoO0NZ6yqP2WDVheUaGpXXFkjfEk"
TELEGRAM_CHAT_ID = "9094138938"
GOOGLE_SCRIPT_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyomqYX_XTsf-drLG8f0VY8YMqdSUP-Oti51rrMQ7X9D7DjTZ1IR2TgwknpDPXaQpqb/exec"

SUPPORT_PHONE = "097 777 70 60"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1OM0qaqgBryi0OVfBpnYWiQk3Jw3fIV_4L3RqKhK9R9k/export?format=csv&gid=1813155293"

# --- ФУНКЦІЯ ВІДПРАВКИ В TELEGRAM ---
def send_telegram_order(phone, segment, cart_items, total):
    text = f"🚨 <b>НОВЕ ЗАМОВЛЕННЯ!</b>\n\n📞 Клієнт: <code>{phone}</code>\n💼 Сегмент: {segment}\n\n🛒 <b>Кошик:</b>\n"
    for item, details in cart_items.items():
        sku_str = f" (Код: <code>{details.get('арт', '')}</code>)" if details.get('арт') else ""
        text += f"▪️ {item}{sku_str}\n   {details['кількість']} шт. x {details['ціна']:.2f} грн = <b>{details['кількість'] * details['ціна']:.2f} грн</b>\n"
    text += f"\n💰 <b>Загальна сума: {total:.2f} грн</b>"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        res_data = resp.json()
        if not res_data.get("ok"):
            return False, res_data.get("description", "Невідома помилка Telegram")
        return True, "OK"
    except Exception as e:
        return False, str(e)

# --- ФУНКЦІЯ ЗАПИСУ В GOOGLE ТАБЛИЦЮ ---
def send_order_to_sheet(phone, segment, cart_items, total):
    if not GOOGLE_SCRIPT_WEBHOOK_URL:
        return False, "Не вказано посилання вебхука"
        
    items_list = []
    for item, details in cart_items.items():
        sku_str = f" [{details.get('арт')}]" if details.get('арт') else ""
        items_list.append(f"{item}{sku_str} — {details['кількість']} шт. по {details['ціна']:.2f} грн")
        
    payload = {
        "phone": phone,
        "segment": segment,
        "items_text": "\n".join(items_list),
        "total": round(total, 2)
    }
    try:
        resp = requests.post(GOOGLE_SCRIPT_WEBHOOK_URL, json=payload, timeout=15)
        if resp.status_code == 200:
            return True, "OK"
        return False, f"Помилка сервера таблиці (Код {resp.status_code})"
    except Exception as e:
        return False, str(e)

def parse_num(val):
    if pd.isna(val): return 0.0
    try: return float(str(val).replace(',', '.').replace(' ', '').strip())
    except: return 0.0

def format_stock(val):
    num = parse_num(val)
    if num <= 0: return "Під замовлення"
    if num == int(num): return f"{int(num)}"
    return f"{num:.2f}".rstrip('0').rstrip('.')

@st.cache_data(ttl=60)
def load_catalog(url):
    return pd.read_csv(url)

# --- СЕСІЇ ---
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

# --- АВТОРИЗАЦІЯ ---
if st.session_state.user is None:
    st.title("🔑 Вхід для клієнтів Miko Supply")
    phone_input = st.text_input("Введіть ваш номер телефону (наприклад, 0501234567):")
    if st.button("Увійти", use_container_width=True):
        if phone_input:
            segment = "HoReCa" if phone_input.startswith("0") else "Роздріб" 
            st.session_state.user = {"phone": phone_input, "segment": segment}
            st.rerun()
    st.stop()

# --- ОСНОВНИЙ ІНТЕРФЕЙС ---
st.title("🛒 Miko Supply - Оптовий маркетплейс")
st.write(f"👤 Ви увійшли як: **{st.session_state.user['phone']}** (Сегмент: {st.session_state.user['segment']})")

col_btn1, col_btn2, _ = st.columns([1, 1.5, 6])
with col_btn1:
    if st.button("Вийти", use_container_width=True):
        st.session_state.user = None
        st.session_state.cart = {}
        st.rerun()
with col_btn2:
    if st.button("🔄 Оновити прайс", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# --- ЗАВАНТАЖЕННЯ ДАНИХ ---
try:
    with st.spinner("Завантаження каталогу товарів..."):
        catalog_df = load_catalog(SHEET_CSV_URL).copy()
    
    if "Доступно" in catalog_df.columns and "Статус/Графік" in catalog_df.columns:
        catalog_df["Доступно_число"] = catalog_df["Доступно"].apply(parse_num)
        out_of_stock = (catalog_df["Статус/Графік"].astype(str).str.strip() == "В наявності") & (catalog_df["Доступно_число"] <= 0)
        catalog_df = catalog_df[~out_of_stock]
        
    # --- САЙДБАР (КОШИК ТА ФІЛЬТРИ) ---
    with st.sidebar:
        st.header("📞 Контакти")
        st.info(f"**Підтримка та замовлення:**\n\n📱 {SUPPORT_PHONE}\n\nТелефонуйте, якщо є питання!")
        st.markdown("---")
        
        st.header("🔍 Пошук та фільтри")
        search_query = st.text_input("Назва або код товару...")
        
        if "Категорія" in catalog_df.columns:
            all_cats = catalog_df["Категорія"].dropna().astype(str).str.split(",").explode().str.strip()
            categories = ["Усі категорії"] + sorted(all_cats[all_cats != ""].unique().tolist())
        else:
            categories = ["Усі категорії"]
            
        category_filter = st.selectbox("Категорія", categories)
        
        if "Статус/Графік" in catalog_df.columns:
            statuses = ["Усі статуси"] + sorted(catalog_df["Статус/Графік"].dropna().astype(str).unique().tolist())
        else:
            statuses = ["Усі статуси"]
        status_filter = st.selectbox("Статус наявності", statuses)
        
        st.markdown("---")
        st.header("🛒 Ваш кошик")
        
        if not st.session_state.cart:
            st.info("Кошик порожній")
        else:
            total_sum = 0
            for item_name, details in list(st.session_state.cart.items()):
                item_total = details['ціна'] * details['кількість']
                total_sum += item_total
                sku_info = f" ({details.get('арт')})" if details.get('арт') else ""
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**{item_name}**{sku_info}\n{details['кількість']} шт х {details['ціна']:.2f} грн")
                with c2:
                    if st.button("❌", key=f"del_{item_name}"):
                        del st.session_state.cart[item_name]
                        st.rerun()
                        
            st.markdown(f"### Загалом: {total_sum:.2f} грн")
            
            if st.button("✅ Оформити замовлення", use_container_width=True, type="primary"):
                tg_ok, tg_msg = send_telegram_order(st.session_state.user['phone'], st.session_state.user['segment'], st.session_state.cart, total_sum)
                sh_ok, sh_msg = send_order_to_sheet(st.session_state.user['phone'], st.session_state.user['segment'], st.session_state.cart, total_sum)
                
                if tg_ok:
                    st.success("✅ Повідомлення в Telegram успішно відправлено!")
                else:
                    st.error(f"❌ Помилка Telegram: {tg_msg}")
                    
                if sh_ok:
                    st.success("✅ Замовлення записано в Google Таблицю!")
                else:
                    st.error(f"❌ Помилка запису в Таблицю: {sh_msg}")
                
                if tg_ok or sh_ok:
                    st.session_state.cart = {}
                    st.balloons()

    # --- ФІЛЬТРАЦІЯ ТА ПОШУК ---
    if search_query.strip():
        q = search_query.strip()
        name_match = catalog_df["Назва товару"].astype(str).str.contains(q, case=False, na=False, regex=False)
        sku_col = "Штрихкод/Модель" if "Штрихкод/Модель" in catalog_df.columns else ("Штрихкод / Модель" if "Штрихкод / Модель" in catalog_df.columns else None)
        if sku_col:
            sku_match = catalog_df[sku_col].astype(str).str.contains(q, case=False, na=False, regex=False)
            catalog_df = catalog_df[name_match | sku_match]
        else:
            catalog_df = catalog_df[name_match]
        st.session_state.current_page = 1 
        
    if category_filter != "Усі категорії":
        catalog_df = catalog_df[catalog_df["Категорія"].astype(str).str.contains(category_filter, regex=False, na=False)]
        st.session_state.current_page = 1
        
    if status_filter != "Усі статуси":
        catalog_df = catalog_df[catalog_df["Статус/Графік"].astype(str) == status_filter]
        st.session_state.current_page = 1

    # --- ВІДОБРАЖЕННЯ ТОВАРІВ ---
    ITEMS_PER_PAGE = 20
    total_items = len(catalog_df)
    
    if total_items == 0:
        st.warning("Товарів за вашим запитом не знайдено.")
    else:
        total_pages = max(1, (total_items - 1) // ITEMS_PER_PAGE + 1)
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = 1
            
        start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
        page_df = catalog_df.iloc[start_idx:start_idx + ITEMS_PER_PAGE]

        cols = st.columns(4)
        for i, (index, row) in enumerate(page_df.iterrows()):
            raw_price = row.get("Базова ціна", 0) if st.session_state.user["segment"] == "HoReCa" else row.get("Роздрібна ціна", 0)
            price = parse_num(raw_price)
            item_name = str(row.get("Назва товару", "Без назви"))
            
            raw_art = row.get('Штрихкод/Модель', row.get('Штрихкод / Модель', ''))
            art = "" if pd.isna(raw_art) or str(raw_art).strip().lower() == "nan" else str(raw_art).strip()
            
            raw_stock = row.get('Доступно', row.get('Залишок в 1С', 0))
            stock_str = format_stock(raw_stock)
            
            with cols[i % 4]:
                with st.container(border=True):
                    img_url = row.get("Фото URL", "")
                    if img_url and str(img_url).startswith("http"):
                        st.markdown(f'<div class="product-img-box"><img src="{img_url}"></div>', unsafe_allow_html=True)
