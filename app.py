import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime, timedelta

# ==========================================
# 🔑 КОНФІГУРАЦІЯ
# ==========================================
CONFIG = {
    "LOGO_URL": "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png",
    "CATALOG_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv",
    "CLIENTS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv",
    "ORDERS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv",
    "TG_TOKEN": "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU",
    "GROUP_ID": "-1003641918928",
    "MIN_ORDER": 1000,
    "ITEMS_PER_PAGE": 12  # Кількість товарів на сторінці
}

st.set_page_config(page_title="Food Festival ERP", layout="wide")

# Стилі (без змін)
st.markdown("""
    <style>
    .product-card { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.07); border: 1px solid #eee; margin-bottom: 20px; min-height: 500px; }
    .stButton > button { background-color: #D4AC0D !important; color: white !important; border-radius: 10px !important; width: 100%; font-weight: bold; border: none !important; }
    .metric-box { background: #fff; padding: 20px; border-radius: 15px; border-left: 5px solid #D4AC0D; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300) # Збільшено до 5 хвилин
def load_data(url):
    try:
        res = requests.get(url, timeout=10)
        df = pd.read_csv(io.StringIO(res.content.decode('utf-8')), dtype=str).fillna('')
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return None

def extract_url(text):
    if not text or not isinstance(text, str): return ""
    found = re.findall(r'(https?://[^\s"\';)]+)', text)
    return found[0] if found else ""

# ==========================================
# 📈 АНАЛІТИКА
# ==========================================
def show_analytics():
    st.title("📈 Аналітика бізнесу")
    df = load_data(CONFIG["ORDERS_URL"])
    if df is None or df.empty:
        st.info("Замовлень ще немає.")
        return

    df['Сума_число'] = pd.to_numeric(df['Сума'].apply(lambda x: re.sub(r'[^\d.]', '', str(x))), errors='coerce').fillna(0)
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-box'>💰 Загальний оборот<br><h2>{df['Сума_число'].sum():,.0f} ₴</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-box'>📦 Всього замовлень<br><h2>{len(df)}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-box'>📊 Середній чек<br><h2>{df['Сума_число'].mean():,.0f} ₴</h2></div>", unsafe_allow_html=True)

    st.divider()
    df_chart = df.groupby('Дата')['Сума_число'].sum().reset_index()
    st.line_chart(df_chart.set_index('Дата'))

# ==========================================
# 🍽️ КАТАЛОГ (ОПТИМІЗОВАНИЙ)
# ==========================================
def show_catalog(u):
    st.title("🍽️ Наше Меню")
    df = load_data(CONFIG["CATALOG_URL"])
    if df is None: return

    # Визначаємо колонки один раз
    low_cols = {c.lower(): c for c in df.columns}
    name_col = low_cols.get('назва') or df.columns[0]
    art_col = low_cols.get('upc') or low_cols.get('артикул') or df.columns[1]
    price_col = low_cols.get('цена') or low_cols.get('ціна') or df.columns[-1]
    desc_col = low_cols.get('опис (укр)') or low_cols.get('опис') or 'Опис (укр)'

    # Пошук
    search = st.text_input("🔍 Швидкий пошук...")
    f_df = df[df[name_col].str.contains(search, case=False)] if search else df

    # --- ПАГІНАЦІЯ ---
    total_items = len(f_df)
    total_pages = (total_items // CONFIG["ITEMS_PER_PAGE"]) + 1
    
    col_p1, col_p2 = st.columns([1, 4])
    with col_p1:
        page = st.number_input("Сторінка", min_value=1, max_value=total_pages, step=1)
    
    start_idx = (page - 1) * CONFIG["ITEMS_PER_PAGE"]
    end_idx = start_idx + CONFIG["ITEMS_PER_PAGE"]
    
    items = f_df.iloc[start_idx:end_idx].to_dict('records')
    
    # Знижка клієнта
    try: disc = float(str(u.get('Знижка', '0')).replace('%','')) / 100
    except: disc = 0.0

    # Відображення сіткою
    for i in range(0, len(items), 3):
        cols = st.columns(3)
        for j, item in enumerate(items[i:i+3]):
            with cols[j]:
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                
                img_url = extract_url(item.get('Фото', ''))
                st.image(img_url if img_url else "https://via.placeholder.com/250x200?text=No+Photo", use_container_width=True)
                
                st.markdown(f"**{item[name_col]}**")
                
                with st.expander("📖 Детальніше"):
                    st.write(item.get(desc_col, "Опис відсутній"))
                
                try:
                    raw_p = float(str(item[price_col]).replace(',', '.'))
                    final_p = raw_p * (1 - disc)
                except: final_p = 0.0
                
                st.subheader(f"{final_p:g} ₴")
                
                q = st.number_input("К-сть", min_value=0.0, step=1.0, key=f"q_{item[art_col]}")
                if st.button("🛒 В кошик", key=f"b_{item[art_col]}"):
                    if q > 0:
                        st.session_state.cart[item[name_col]] = {'qty': q, 'price': final_p}
                        st.toast(f"✅ {item[name_col]} додано!")
                st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🛒 КОШИК ТА TELEGRAM (БЕЗ ЗМІН)
# ==========================================
def show_cart(u):
    st.title("🛒 Кошик")
    if not st.session_state.cart:
        st.info("Кошик порожній.")
        return

    total = sum(d['qty'] * d['price'] for d in st.session_state.cart.values())
    
    for name, d in list(st.session_state.cart.items()):
        c1, c2, c3 = st.columns([3, 1, 0.5])
        c1.write(f"**{name}**")
        c2.write(f"{d['qty']} шт x {d['price']:g} ₴")
        if c3.button("❌", key=f"del_{name}"):
            del st.session_state.cart[name]; st.rerun()

    st.divider()
    st.subheader(f"Загальна сума: {total:g} ₴")

    if total >= CONFIG["MIN_ORDER"]:
        addr = st.text_input("📍 Адреса доставки", value=u.get('Адреса', ''))
        if st.button("🚀 ПІДТВЕРДИТИ ЗАМОВЛЕННЯ", use_container_width=True):
            items_list = "".join([f"🔸 {n} — {d['qty']} шт.\n" for n, d in st.session_state.cart.items()])
            msg = (
                f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ</b>\n👤 <b>Клієнт:</b> {u.get('Назва', 'Невідомо')}\n"
                f"📞 <b>Тел:</b> {u.get('Телефон', '')}\n📍 <b>Адреса:</b> {addr}\n"
                f"━━━━━━━━━━━━━━━━━━\n🛒 <b>ТОВАРИ:</b>\n{items_list}"
                f"━━━━━━━━━━━━━━━━━━\n💰 <b>РАЗОМ: {total:g} ₴</b>"
            )
            requests.post(f"https://api.telegram.org/bot{CONFIG['TG_TOKEN']}/sendMessage", 
                          data={"chat_id": CONFIG["GROUP_ID"], "text": msg, "parse_mode": "HTML"})
            st.session_state.cart = {}
            st.success("Замовлення відправлено!")
            st.balloons()
    else:
        st.error(f"Додайте ще на {CONFIG['MIN_ORDER']-total:g} ₴ для мінімального замовлення.")

# ==========================================
# 📊 ГОЛОВНИЙ МОДУЛЬ
# ==========================================
def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔑 Вхід Food Festival")
        phone = st.text_input("Ваш номер телефону:")
        if st.button("Увійти"):
            with st.spinner("Перевірка номера..."):
                df_c = load_data(CONFIG["CLIENTS_URL"])
                if df_c is not None:
                    inp = re.sub(r'\D', '', phone)
                    user = None
                    for _, row in df_c.iterrows():
                        if any(inp in re.sub(r'\D', '', str(val)) for val in row.values if len(str(val)) > 5):
                            user = row.to_dict()
                            break
                    if user:
                        st.session_state.logged_in, st.session_state.user_info = True, user
                        st.rerun()
                    else: st.error("Номер не знайдено.")
    else:
        u = st.session_state.user_info
        st.sidebar.image(CONFIG["LOGO_URL"], width=150)
        st.sidebar.success(f"Ви увійшли як: **{u.get('Назва', 'Клієнт')}**")
        
        choice = st.sidebar.radio("Меню", ["🍽️ Каталог", "🛒 Кошик", "📜 Історія", "📈 Аналітика"])
        
        if st.sidebar.button("🚪 Вийти"):
            st.session_state.logged_in = False; st.rerun()

        if choice == "🍽️ Каталог": show_catalog(u)
        elif choice == "🛒 Кошик": show_cart(u)
        elif choice == "📈 Аналітика": show_analytics()
        elif choice == "📜 Історія":
            st.title("📜 Історія замовлень")
            df = load_data(CONFIG["ORDERS_URL"])
            if df is not None:
                # Оптимізована фільтрація історії
                phone_clean = re.sub(r'\D', '', str(u.get('Телефон', '')))
                my = df[df.apply(lambda x: phone_clean in re.sub(r'\D', '', str(x)), axis=1)]
                
                if my.empty: st.info("Історія порожня.")
                else:
                    for _, r in my.iloc[::-1].head(10).iterrows(): # Показуємо останні 10
                        with st.expander(f"📦 {r.get('Дата', '---')} | {r.get('Сума', '0')} ₴"):
                            st.write(r.get('Товари', 'Немає даних'))

if __name__ == "__main__":
    main()
