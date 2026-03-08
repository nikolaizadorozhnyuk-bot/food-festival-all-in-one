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

# Приховуємо зайве та додаємо стилі
st.markdown("""
    <style>
    .product-card { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #eee; margin-bottom: 20px; min-height: 520px; }
    .stButton > button { background-color: #D4AC0D !important; color: white !important; border-radius: 10px !important; width: 100%; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def load_data(url):
    try:
        response = requests.get(url)
        # Використовуємо кодування utf-8
        df = pd.read_csv(io.StringIO(response.text), dtype=str).fillna('')
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Помилка бази: {e}")
        return None

def show_catalog(u):
    st.title("🍽️ Наше Меню")
    df = load_data(CONFIG["CATALOG_URL"])
    if df is None or df.empty: return

    # --- ЖОРСТКИЙ МАПІНГ КОЛОНОК (щоб нічого не злітало) ---
    cols = list(df.columns)
    
    # Шукаємо назви або використовуємо точні з твого Excel
    name_col = 'Назва' if 'Назва' in cols else cols[0]
    art_col = 'upc' if 'upc' in cols else 'Артикул' if 'Артикул' in cols else cols[1]
    price_col = 'Цена' if 'Цена' in cols else 'Ціна' if 'Ціна' in cols else cols[-1]
    desc_col = 'Опис (укр)' if 'Опис (укр)' in cols else 'Опис'
    photo_col = 'Фото'
    stock_col = 'Остаток_Тек'

    # Фільтри
    search = st.text_input("🔍 Пошук товару (Назва або Код)...").lower()
    
    f_df = df.copy()
    if search:
        f_df = f_df[f_df[name_col].str.lower().contains(search) | f_df[art_col].str.lower().contains(search)]

    # Вивід товарів 3 в ряд
    items = f_df.to_dict('records')
    for i in range(0, len(items), 3):
        row_cols = st.columns(3)
        for j, item in enumerate(items[i:i+3]):
            with row_cols[j]:
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                
                # Фото
                raw_img = str(item.get(photo_col, ''))
                img_url = re.findall(r'(https?://[^\s"\';)]+)', raw_img)
                st.image(img_url[0] if img_url else "https://via.placeholder.com/200", use_container_width=True)
                
                # НАЗВА (ТЕПЕР ТОЧНО НАЗВА)
                st.subheader(item[name_col])
                st.caption(f"Код: {item[art_col]}")

                # ОПИС (УКР)
                product_desc = item.get(desc_col, "")
                if product_desc:
                    with st.expander("📖 Про товар"):
                        st.write(product_desc)
                
                # ЦІНА ТА ЗНИЖКА
                try:
                    p = float(str(item[price_col]).replace(',', '.'))
                    final_p = p * (1 - float(str(u.get('Знижка', '0')).replace('%','')) / 100)
                except: final_p = 0.0
                
                st.markdown(f"### {final_p:g} ₴")
                
                # КНОПКА ЗАМОВЛЕННЯ
                item_id = str(item[art_col])
                qty = st.number_input("Кількість", min_value=0.0, step=1.0, key=f"qty_{item_id}")
                
                if st.button("🛒 В кошик", key=f"btn_{item_id}"):
                    if qty > 0:
                        st.session_state.cart[item[name_col]] = {'qty': qty, 'price': final_p, 'upc': item_id}
                        st.toast(f"Додано: {item[name_col]}")
                
                st.markdown('</div>', unsafe_allow_html=True)

def show_cart(u):
    st.title("🛒 Мій Кошик")
    if not st.session_state.cart:
        st.info("Кошик порожній.")
        return

    total = sum(d['qty'] * d['price'] for d in st.session_state.cart.values())
    
    for name, data in list(st.session_state.cart.items()):
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(f"**{name}**")
        c2.write(f"{data['qty']} шт. на {data['qty']*data['price']:g} ₴")
        if c3.button("Видалити", key=f"del_{name}"):
            del st.session_state.cart[name]
            st.rerun()

    st.divider()
    st.subheader(f"Загальна сума: {total:g} ₴")

    if total >= CONFIG["MIN_ORDER"]:
        addr = st.text_input("📍 Адреса доставки", value=u.get('Адреса', ''))
        if st.button("🚀 Оформити замовлення", use_container_width=True):
            items_list = "\n".join([f"- {n}: {d['qty']} шт." for n, d in st.session_state.cart.items()])
            msg = f"📦 <b>НОВЕ ЗАМОВЛЕННЯ</b>\n👤 Клієнт: {u['Назва']}\n💰 Сума: {total:g} ₴\n📍 Адреса: {addr}\n\n🛒 Товари:\n{items_list}"
            requests.post(f"https://api.telegram.org/bot{CONFIG['TG_TOKEN']}/sendMessage", 
                          data={"chat_id": CONFIG["GROUP_ID"], "text": msg, "parse_mode": "HTML"})
            st.session_state.cart = {}
            st.success("Замовлення відправлено оператору!")
            st.balloons()
    else:
        st.error(f"⚠️ До мінімального замовлення (1000 ₴) не вистачає {CONFIG['MIN_ORDER'] - total:g} ₴")

def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("Вхід Food Festival")
        phone = st.text_input("Ваш номер телефону:")
        if st.button("🚪 Увійти"):
            df_c = load_data(CONFIG["CLIENTS_URL"])
            if df_c is not None:
                user = df_c[df_c['Телефон'].str.strip() == phone.strip()]
                if not user.empty:
                    st.session_state.logged_in, st.session_state.user_info = True, user.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Клієнта з таким телефоном не знайдено.")
    else:
        u = st.session_state.user_info
        st.sidebar.subheader(f"👋 {u['Назва']}")
        page = st.sidebar.radio("Перейти до:", ["Каталог", "Кошик"])
        if st.sidebar.button("Вийти"):
            st.session_state.logged_in = False
            st.rerun()
            
        if page == "Каталог": show_catalog(u)
        else: show_cart(u)

if __name__ == "__main__":
    main()
