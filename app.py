import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime, timedelta, date

# ==========================================
# 🔑 КОНФІГУРАЦІЯ
# ==========================================
CONFIG = {
    "LOGO_URL": "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png",
    "CATALOG_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv",
    "CLIENTS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv",
    "ORDERS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv",
    "SETTINGS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=295620790&single=true&output=csv",
    "NEWS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=374278986&single=true&output=csv",
    "TG_TOKEN": "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU",
    "GROUP_ID": "-1003641918928",
    "MIN_ORDER": 1000,
    "OWNER_PHONE": "0675953220"
}

st.set_page_config(page_title="Food Festival ERP", layout="wide")

# ПРЕМІУМ СТИЛІ
st.markdown("""
    <style>
    .product-card { background: white; padding: 15px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.06); border: 1px solid #f2f2f2; margin-bottom: 25px; min-height: 520px; }
    div.stButton > button { background-color: #D4AC0D !important; color: white !important; border-radius: 12px !important; font-weight: bold !important; height: 45px; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- БРОНЕБІЙНЕ ЗАВАНТАЖЕННЯ ---
@st.cache_data(ttl=60) # Збільшив час кешування для швидкості
def load_data(url):
    try:
        response = requests.get(url)
        content = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(content), dtype=str).fillna('')
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return None

def clean_p(phone):
    return re.sub(r'\D', '', str(phone))

def get_active_fop():
    df = load_data(CONFIG["SETTINGS_URL"])
    if df is not None and not df.empty:
        active = df[df['Статус'].str.contains('Актив', case=False)]
        if not active.empty: return active.iloc[0]['Назва ФОП']
    return "ФОП Food Festival"

# ==========================================
# 🍽️ КАТАЛОГ
# ==========================================
def show_catalog(u):
    st.title("🍽️ Наше Меню")
    df = load_data(CONFIG["CATALOG_URL"])
    if df is None: return

    # Колонки
    cols = {c.lower(): c for c in df.columns}
    name_col = cols.get('назва') or df.columns[0]
    art_col = cols.get('upc') or cols.get('артикул') or df.columns[1]
    price_col = cols.get('ціна') or cols.get('цена') or df.columns[-1]
    desc_col = cols.get('опис (укр)') or cols.get('опис') or 'Опис (укр)'

    search = st.text_input("🔍 Швидкий пошук...")
    f_df = df[df[name_col].str.contains(search, case=False) | df[art_col].str.contains(search, case=False)] if search else df

    items = f_df.to_dict('records')
    for i in range(0, len(items), 3):
        row_cols = st.columns(3)
        for j, item in enumerate(items[i:i+3]):
            with row_cols[j]:
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                
                # Фото
                img_raw = str(item.get('Фото', ''))
                img_url = re.findall(r'(https?://[^\s"\';)]+)', img_raw)
                st.image(img_url[0] if img_url else "https://via.placeholder.com/200", use_container_width=True)
                
                st.subheader(item[name_col])
                
                # ОПИС (УКР) - Тепер точно тут
                product_desc = item.get(desc_col, "")
                if product_desc:
                    with st.expander("📖 Детальніше про товар"):
                        st.write(product_desc)
                
                # Ціна
                try:
                    p = float(item[price_col].replace(',', '.'))
                    final_p = p * (1 - float(str(u.get('Знижка', '0')).replace('%',''))/100)
                except: final_p = 0.0
                
                st.markdown(f"### {final_p:g} ₴")
                
                it_id = str(item.get(art_col, f"{i}_{j}"))
                qty = st.number_input("К-сть", min_value=0.0, step=1.0, key=f"q_{it_id}")
                if st.button("🛒 В кошик", key=f"b_{it_id}", use_container_width=True):
                    if qty > 0:
                        st.session_state.cart[item[name_col]] = {'qty': qty, 'price': final_p, 'art': it_id}
                        st.toast(f"✅ Додано!")
                st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🛒 КОШИК
# ==========================================
def show_cart(u):
    st.title("🛒 Ваш Кошик")
    
    # Авто-адреса
    orders_df = load_data(CONFIG["ORDERS_URL"])
    last_addr = ""
    if orders_df is not None:
        my = orders_df[orders_df['Телефон'] == u['Телефон']]
        if not my.empty: last_addr = my.iloc[-1].get('Адреса', '')

    if not st.session_state.cart:
        st.info("Кошик порожній.")
        return

    total = sum(d['qty'] * d['price'] for d in st.session_state.cart.values())
    st.subheader(f"Разом: {total:g} ₴")

    for name, d in list(st.session_state.cart.items()):
        c1, c2, c3 = st.columns([3, 1, 0.5])
        c1.write(name)
        c2.write(f"{d['qty']} x {d['price']}")
        if c3.button("❌", key=f"del_{name}"):
            del st.session_state.cart[name]; st.rerun()

    st.divider()
    our_fop = get_active_fop()
    st.info(f"🏢 Продавець: **{our_fop}**")
    
    addr = st.text_input("📍 Адреса доставки:", value=last_addr)
    
    if st.button("🚀 ПІДТВЕРДИТИ ЗАМОВЛЕННЯ", use_container_width=True, disabled=(total < CONFIG["MIN_ORDER"])):
        items_txt = "; ".join([f"{n} ({d['qty']} шт)" for n, d in st.session_state.cart.items()])
        msg = f"🛍 НОВЕ ЗАМОВЛЕННЯ\n👤 Клієнт: {u['Назва']}\n💰 Сума: {total:g} ₴\n📍 Адреса: {addr}\n🏢 ФОП: {our_fop}\n🛒 Товари: {items_txt}"
        requests.post(f"https://api.telegram.org/bot{CONFIG['TG_TOKEN']}/sendMessage", data={"chat_id": CONFIG["GROUP_ID"], "text": msg})
        st.session_state.cart = {}
        st.success("Надіслано оператору!")
        st.balloons()

# ==========================================
# 📈 ІНШІ РОЗДІЛИ
# ==========================================
def show_history(u):
    st.title("📜 Історія замовлень")
    df = load_data(CONFIG["ORDERS_URL"])
    if df is not None:
        my = df[df['Телефон'] == u['Телефон']]
        for _, r in my.iloc[::-1].iterrows():
            with st.expander(f"📦 Замовлення від {r.get('Дата')} | {r.get('Сума')} ₴"):
                st.write(f"🛒 Товари: {r.get('Товари')}")

def show_news():
    st.title("📰 Новини Food Festival")
    df = load_data(CONFIG["NEWS_URL"])
    if df is not None:
        for _, r in df.iloc[::-1].iterrows():
            st.subheader(r.get('Заголовок'))
            st.write(r.get('Текст новини'))
            st.divider()

# ==========================================
# 📊 ЛОГІН ТА МЕНЮ
# ==========================================
def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("Вхід Food Festival")
        ph = st.text_input("Введіть ваш номер телефону:")
        if st.button("Увійти"):
            df_c = load_data(CONFIG["CLIENTS_URL"])
            if df_c is not None:
                inp_c = clean_p(ph)
                user = None
                for _, row in df_c.iterrows():
                    # Шукаємо в кожній клітинці рядка наш телефон
                    if any(inp_c in clean_p(str(val)) for val in row.values) and len(inp_c) > 5:
                        user = row.to_dict()
                        break
                if user:
                    st.session_state.logged_in, st.session_state.user_info = True, user
                    st.rerun()
                else: st.error("Номер не знайдено.")
    else:
        u = st.session_state.user_info
        st.sidebar.image(CONFIG["LOGO_URL"], width=150)
        st.sidebar.success(f"👤 {u['Назва']}")
        
        # ОСЬ ПОВНЕ МЕНЮ!
        choice = st.sidebar.radio("Навігація", ["🍽️ Каталог", "🛒 Кошик", "📜 Історія", "📰 Новини"])
        
        if st.sidebar.button("🚪 Вийти"):
            st.session_state.logged_in = False; st.rerun()

        if choice == "🍽️ Каталог": show_catalog(u)
        elif choice == "🛒 Кошик": show_cart(u)
        elif choice == "📜 Історія": show_history(u)
        elif choice == "📰 Новини": show_news()

if __name__ == "__main__":
    main()
