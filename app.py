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

# Приховуємо зайві елементи Streamlit для краси
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def load_data(url):
    try:
        # Завантажуємо CSV
        response = requests.get(url)
        df = pd.read_csv(io.StringIO(response.text), dtype=str).fillna('')
        
        # Видаляємо зайві пробіли з назв колонок
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Помилка завантаження бази: {e}")
        return None

def show_catalog(u):
    st.title("🍽️ Каталог товарів")
    df = load_data(CONFIG["CATALOG_URL"])
    if df is None or df.empty: return

    # --- ПІДБІР КОЛОНОК ---
    c_map = {c.lower(): c for c in df.columns}
    name_col = c_map.get('назва') or c_map.get('товар') or df.columns[0]
    # Додав upc та sku сюди:
    art_col = c_map.get('upc') or c_map.get('артикул') or c_map.get('sku') or c_map.get('код') or df.columns[1]
    price_col = c_map.get('ціна') or c_map.get('цена') or df.columns[-1]
    photo_col = c_map.get('фото') or c_map.get('зображення')

    search = st.text_input("🔍 Пошук по назві або UPC...")
    f_df = df[df[name_col].str.contains(search, case=False) | df[art_col].str.contains(search, case=False)] if search else df

    # Вивід товарів 3 в ряд
    items = f_df.to_dict('records')
    for i in range(0, len(items), 3):
        row_cols = st.columns(3)
        for j, item in enumerate(items[i:i+3]):
            with row_cols[j].container(border=True):
                # --- ЛОГІКА ФОТО ---
                raw_photo = str(item.get(photo_col, ''))
                # Витягуємо чисте посилання, якщо воно всередині формули IMAGE чи лапок
                clean_photo = re.findall(r'(https?://[^\s"\';)]+)', raw_photo)
                img_url = clean_photo[0] if clean_photo else "https://via.placeholder.com/300x200?text=No+Image"
                
                st.image(img_url, use_container_width=True)
                
                st.subheader(item[name_col])
                st.caption(f"UPC: {item[art_col]}")
                
                # Ціна зі знижкою
                try:
                    p = float(str(item[price_col]).replace(',', '.'))
                    disc = float(str(u.get('Знижка', '0')).replace('%','')) / 100
                    final_p = p * (1 - disc)
                except: final_p = 0.0
                
                st.markdown(f"### {final_p:g} ₴")
                
                # Поле замовлення
                item_id = str(item[art_col]) if art_col in item else f"idx_{i}_{j}"
                qty = st.number_input("Кількість", min_value=0.0, step=1.0, key=f"q_{item_id}")
                
                if st.button("🛒 До кошика", key=f"b_{item_id}", use_container_width=True):
                    if qty > 0:
                        st.session_state.cart[item[name_col]] = {'qty': qty, 'price': final_p, 'upc': item_id}
                        st.success(f"Додано: {item[name_col]}")

def show_cart(u):
    st.title("🛒 Ваш кошик")
    if not st.session_state.cart:
        st.info("Кошик порожній.")
        return

    total = sum(d['qty'] * d['price'] for d in st.session_state.cart.values())
    st.subheader(f"Разом: {total:g} ₴")

    for name, data in list(st.session_state.cart.items()):
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(name)
        c2.write(f"{data['qty']} шт.")
        if c3.button("Видалити", key=f"del_{name}"):
            del st.session_state.cart[name]
            st.rerun()

    if total >= CONFIG["MIN_ORDER"]:
        addr = st.text_input("📍 Адреса доставки", value=u.get('Адреса', ''))
        if st.button("✅ Оформити замовлення", use_container_width=True):
            # Тут логіка відправки замовлення
            st.balloons()
            st.success("Замовлення відправлено!")
            st.session_state.cart = {}
    else:
        st.error(f"Мінімальна сума — {CONFIG['MIN_ORDER']} ₴")

def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("Вхід (Food Festival)")
        phone = st.text_input("Введіть ваш номер телефону:")
        if st.button("Увійти"):
            df_c = load_data(CONFIG["CLIENTS_URL"])
            if df_c is not None:
                user = df_c[df_c['Телефон'].str.strip() == phone.strip()]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Номер не знайдено.")
    else:
        u = st.session_state.user_info
        st.sidebar.title(f"Вітаємо, {u['Назва']}!")
        page = st.sidebar.radio("Навігація", ["Каталог", "Кошик"])
        if st.sidebar.button("Вийти"):
            st.session_state.logged_in = False
            st.rerun()
            
        if page == "Каталог": show_catalog(u)
        else: show_cart(u)

if __name__ == "__main__":
    main()
