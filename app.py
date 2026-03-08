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
    "TG_TOKEN": "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU",
    "GROUP_ID": "-1003641918928",
    "MIN_ORDER": 1000,
    "OWNER_PHONE": "0675953220"
}

st.set_page_config(page_title="Food Festival Gold", layout="wide")

# Стилі
st.markdown("""
    <style>
    .product-card { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #f0f0f0; margin-bottom: 25px; min-height: 580px; }
    div.stButton > button { background-color: #D4AC0D !important; color: white !important; border-radius: 12px !important; font-weight: bold !important; height: 50px; width: 100%; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
def clean_phone(phone):
    """Залишає лише цифри в номері телефону"""
    return re.sub(r'\D', '', str(phone))

@st.cache_data(ttl=10)
def load_data(url):
    try:
        response = requests.get(url)
        df = pd.read_csv(io.StringIO(response.text), dtype=str).fillna('')
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Помилка завантаження: {e}")
        return None

# ==========================================
# 🍽️ КАТАЛОГ
# ==========================================
def show_catalog(u):
    st.title("🍽️ Меню Food Festival")
    df = load_data(CONFIG["CATALOG_URL"])
    if df is None or df.empty: return

    cols_low = {c.lower().strip(): c for c in df.columns}
    name_col = cols_low.get('назва') or df.columns[0]
    art_col = cols_low.get('upc') or cols_low.get('артикул') or df.columns[1]
    price_col = cols_low.get('цена') or cols_low.get('ціна') or df.columns[-1]
    desc_col = cols_low.get('опис (укр)') or cols_low.get('опис') or 'Опис'
    photo_col = 'Фото'

    search = st.text_input("🔍 Пошук продукту...").lower()
    f_df = df.copy()
    if search:
        f_df = f_df[f_df[name_col].str.lower().str.contains(search) | f_df[art_col].str.lower().str.contains(search)]

    items = f_df.to_dict('records')
    for i in range(0, len(items), 3):
        row_cols = st.columns(3)
        for j, item in enumerate(items[i:i+3]):
            with row_cols[j]:
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                raw_img = str(item.get(photo_col, ''))
                img_url = re.findall(r'(https?://[^\s"\';)]+)', raw_img)
                st.image(img_url[0] if img_url else "https://via.placeholder.com/300x200?text=Food+Festival", use_container_width=True)
                
                st.subheader(item[name_col])
                st.caption(f"Код: {item[art_col]}")

                if desc_col in item and item[desc_col]:
                    with st.expander("📖 Про товар"):
                        st.write(item[desc_col])
                
                try:
                    p = float(str(item[price_col]).replace(',', '.'))
                    disc = float(str(u.get('Знижка', '0')).replace('%','')) / 100
                    final_p = p * (1 - disc)
                except: final_p = 0.0
                
                st.markdown(f"### {final_p:g} ₴")
                
                item_id = str(item[art_col])
                qty = st.number_input("Кількість", min_value=0.0, step=1.0, key=f"qty_{item_id}")
                if st.button("🛒 В кошик", key=f"btn_{item_id}"):
                    if qty > 0:
                        st.session_state.cart[item[name_col]] = {'qty': qty, 'price': final_p, 'upc': item_id}
                        st.toast(f"✅ Додано!")
                st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🛒 КОШИК
# ==========================================
def show_cart(u):
    st.title("🛒 Кошик")
    if not st.session_state.cart:
        st.info("Кошик порожній.")
        return

    total = sum(d['qty'] * d['price'] for d in st.session_state.cart.values())
    for name, data in list(st.session_state.cart.items()):
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(f"**{name}**")
        c2.write(f"{data['qty']} шт. на {data['qty']*data['price']:g} ₴")
        if c3.button("🗑️", key=f"del_{name}"):
            del st.session_state.cart[name]; st.rerun()

    st.divider()
    if total >= CONFIG["MIN_ORDER"]:
        addr = st.text_input("📍 Адреса доставки", value=u.get('Адреса', ''))
        if st.button("🚀 Надіслати", use_container_width=True):
            items_txt = "\n".join([f"- {n}: {d['qty']} шт." for n, d in st.session_state.cart.items()])
            msg = f"🛍 <b>ЗАМОВЛЕННЯ</b>\n👤 {u['Назва']}\n💰 {total:g} ₴\n📍 {addr}\n\n🛒 Товари:\n{items_txt}"
            requests.post(f"https://api.telegram.org/bot{CONFIG['TG_TOKEN']}/sendMessage", data={"chat_id": CONFIG["GROUP_ID"], "text": msg, "parse_mode": "HTML"})
            st.session_state.cart = {}
            st.success("Відправлено!")
            st.balloons()
    else:
        st.error(f"⚠️ До мінімалки 1000 ₴ треба ще {CONFIG['MIN_ORDER'] - total:g} ₴")

# ==========================================
# 📊 ЛОГІН ТА ГОЛОВНА
# ==========================================
def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("Вхід Food Festival")
        phone_input = st.text_input("Введіть ваш номер телефону (напр. 067...):")
        
        if st.button("🚪 Увійти"):
            df_c = load_data(CONFIG["CLIENTS_URL"])
            if df_c is not None:
                # Шукаємо колонку телефон
                c_map = {c.lower().strip(): c for c in df_c.columns}
                phone_col = c_map.get('телефон') or c_map.get('тел') or df_c.columns[1]
                
                # Нормалізуємо вхідний номер
                input_clean = clean_phone(phone_input)
                
                # Пошук
                user_match = None
                for idx, row in df_c.iterrows():
                    if clean_phone(row[phone_col]) == input_clean:
                        user_match = row.to_dict()
                        break
                
                if user_match:
                    st.session_state.logged_in, st.session_state.user_info = True, user_match
                    st.rerun()
                else:
                    st.error("❌ Користувача не знайдено.")
                    with st.expander("🛠 Діагностика для Миколи"):
                        st.write("Що бачить додаток у таблиці Клієнти:")
                        st.write(f"Колонки: {list(df_c.columns)}")
                        st.write(f"Перші 3 номери в базі: {df_c[phone_col].head(3).tolist()}")
    else:
        u = st.session_state.user_info
        page = st.sidebar.radio("Меню", ["Каталог", "Кошик"])
        if st.sidebar.button("Вийти"):
            st.session_state.logged_in = False; st.rerun()
        if page == "Каталог": show_catalog(u)
        else: show_cart(u)

if __name__ == "__main__":
    main()
