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

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
def clean_phone(p):
    return re.sub(r'\D', '', str(p))

@st.cache_data(ttl=5)
def load_data(url):
    try:
        response = requests.get(url)
        # Виправляємо кодування (Force UTF-8)
        content = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(content), dtype=str).fillna('')
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Помилка завантаження бази: {e}")
        return None

# ==========================================
# 🍽️ КАТАЛОГ ТА КОШИК
# ==========================================
def show_catalog(u):
    st.title("🍽️ Наше Меню")
    df = load_data(CONFIG["CATALOG_URL"])
    if df is None or df.empty: return

    # Шукаємо колонки за ключовими словами
    cols = list(df.columns)
    name_col = next((c for c in cols if 'назва' in c.lower() or 'товар' in c.lower()), cols[0])
    price_col = next((c for c in cols if 'ціна' in c.lower() or 'цена' in c.lower()), cols[-1])
    art_col = next((c for c in cols if 'upc' in c.lower() or 'артикул' in c.lower()), cols[1])

    search = st.text_input("🔍 Пошук продукту...")
    f_df = df[df[name_col].str.contains(search, case=False)] if search else df

    items = f_df.to_dict('records')
    for i in range(0, len(items), 3):
        row_cols = st.columns(3)
        for j, item in enumerate(items[i:i+3]):
            with row_cols[j].container(border=True):
                # Картинка
                img = str(item.get('Фото', ''))
                img_url = re.findall(r'(https?://[^\s"\';)]+)', img)
                st.image(img_url[0] if img_url else "https://via.placeholder.com/300x200?text=Food+Festival", use_container_width=True)
                
                st.subheader(item[name_col])
                
                # Ціна зі знижкою
                try:
                    p = float(item[price_col].replace(',', '.'))
                    disc = float(str(u.get('Знижка', '0')).replace('%','')) / 100
                    final_p = p * (1 - disc)
                except: final_p = 0.0
                
                st.markdown(f"### {final_p:g} ₴")
                
                # Замовлення
                it_id = str(item.get(art_col, f"idx_{i}_{j}"))
                qty = st.number_input("К-сть", min_value=0.0, step=1.0, key=f"q_{it_id}")
                if st.button("🛒 В кошик", key=f"b_{it_id}"):
                    if qty > 0:
                        st.session_state.cart[item[name_col]] = {'qty': qty, 'price': final_p}
                        st.success("Додано!")

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
            msg = f"🛍 НОВЕ ЗАМОВЛЕННЯ\n👤 Клієнт: {u.get('Назва', 'Клієнт')}\n💰 Сума: {total:g} ₴\n📍 Адреса: {addr}"
            requests.post(f"https://api.telegram.org/bot{CONFIG['TG_TOKEN']}/sendMessage", data={"chat_id": CONFIG["GROUP_ID"], "text": msg})
            st.session_state.cart = {}
            st.success("Відправлено!")
    else:
        st.error(f"Мінімальне замовлення 1000 ₴")

# ==========================================
# 📊 ЛОГІН (ВИПРАВЛЕНИЙ)
# ==========================================
def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("Вхід Food Festival")
        phone_input = st.text_input("Введіть ваш номер телефону (напр. 0675953220):")
        
        if st.button("🚪 Увійти"):
            df_c = load_data(CONFIG["CLIENTS_URL"])
            if df_c is not None:
                input_clean = clean_phone(phone_input)
                
                # --- РОЗУМНИЙ ПОШУК: ШУКАЄМО ПО ВСІЙ ТАБЛИЦІ ---
                user_match = None
                for _, row in df_c.iterrows():
                    # Перевіряємо кожну клітинку в рядку. Якщо там є наш телефон — це наш клієнт!
                    row_values = [clean_phone(str(val)) for val in row.values]
                    if input_clean in row_values and len(input_clean) > 5:
                        user_match = row.to_dict()
                        break
                
                if user_match:
                    st.session_state.logged_in, st.session_state.user_info = True, user_match
                    st.rerun()
                else:
                    st.error("❌ Користувача не знайдено. Перевірте номер або зверніться до менеджера.")
    else:
        u = st.session_state.user_info
        page = st.sidebar.radio("Меню", ["Каталог", "Кошик"])
        if st.sidebar.button("Вийти"):
            st.session_state.logged_in = False; st.rerun()
        if page == "Каталог": show_catalog(u)
        else: show_cart(u)

if __name__ == "__main__":
    main()
