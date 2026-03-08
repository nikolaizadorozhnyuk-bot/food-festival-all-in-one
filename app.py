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

st.set_page_config(page_title="Food Festival Gold", page_icon=CONFIG["LOGO_URL"], layout="wide")

# Стилі
st.markdown("""
    <style>
    .product-card { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #f0f0f0; margin-bottom: 25px; min-height: 550px; }
    div.stButton > button { background-color: #D4AC0D !important; color: white !important; border-radius: 12px !important; font-weight: bold !important; height: 50px; width: 100%; border: none !important; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def load_data(url):
    try:
        # Читаємо таблицю
        df = pd.read_csv(url, dtype=str).fillna('')
        
        # --- РОЗУМНА ОБРОБКА ФОТО ---
        if 'Фото' in df.columns:
            def fix_url(val):
                val = str(val).strip()
                # Шукаємо будь-яке посилання http всередині клітинки
                urls = re.findall(r'(https?://[^\s"\';)]+)', val)
                if urls:
                    return urls[0]
                return val # Якщо це вже посилання, лишаємо як є
            
            df['Фото'] = df['Фото'].apply(fix_url)
        return df
    except Exception as e:
        st.error(f"Помилка завантаження: {e}")
        return None

def show_catalog(u):
    st.title("🍽️ Меню Food Festival")
    df = load_data(CONFIG["CATALOG_URL"])
    if df is None: return

    # Визначаємо колонки
    cols = {c.lower().strip(): c for c in df.columns}
    name_col = cols.get('назва') or cols.get('товар') or 'Назва'
    art_col = cols.get('артикул') or 'Артикул'
    p_col = cols.get('ціна') or cols.get('цена') or 'Ціна'
    
    # Фільтрація
    search = st.text_input("🔍 Пошук продукту")
    f_df = df[df[name_col].str.contains(search, case=False)] if search else df

    # Сітка 3х3
    items = f_df.to_dict('records')
    for i in range(0, len(items), 3):
        cols_ui = st.columns(3)
        for j, item in enumerate(items[i:i+3]):
            with cols_ui[j].container(border=True):
                # ЛОГІКА ПЕРЕВІРКИ ФОТО
                img = str(item.get('Фото', '')).strip()
                
                # Якщо посилання немає або воно дивне — ставимо логотип або заглушку
                if not img.startswith('http'):
                    img = "https://via.placeholder.com/300x200?text=Food+Festival"
                
                st.image(img, use_container_width=True)
                
                st.subheader(item[name_col])
                
                # Ціна
                try:
                    p = float(item[p_col].replace(',', '.'))
                    disc = float(str(u.get('Знижка', '0')).replace('%','')) / 100
                    final_p = p * (1 - disc)
                except: final_p = 0.0
                
                st.write(f"💰 **{final_p:g} ₴**")
                
                qty = st.number_input("К-сть", min_value=0.0, step=1.0, key=f"q_{item[art_col]}")
                if st.button("➕ В кошик", key=f"b_{item[art_col]}"):
                    if qty > 0:
                        st.session_state.cart[item[name_col]] = {'qty': qty, 'price': final_p}
                        st.toast("Додано!")

# ... (show_cart, show_login та main без змін)

def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        # Спрощена форма входу
        ph = st.text_input("Ваш телефон")
        if st.button("Увійти"):
            df_c = load_data(CONFIG["CLIENTS_URL"])
            if df_c is not None:
                user = df_c[df_c['Телефон'] == ph]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user.iloc[0].to_dict()
                    st.rerun()
    else:
        show_catalog(st.session_state.user_info)

if __name__ == "__main__":
    main()
