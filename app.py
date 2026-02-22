import streamlit as st
import pandas as pd
import requests

# ==========================================
# 🔑 НАЛАШТУВАННЯ
# ==========================================
OWNER_PHONE = "0675953220"
LOGO_URL = "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaFzeDCKyGghOoel888Xx_QkEaYTytH2te1BsJlSlUAqKYg1LyxF0_AwogvNPOU1PX/exec"

# Дані про товар та клієнтів
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv"
CLIENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv"

st.set_page_config(page_title="Food Festival ERP", page_icon=LOGO_URL, layout="wide")

# --- ФУНКЦІЇ ---
@st.cache_data(ttl=30)
def load_data(url):
    try: return pd.read_csv(url, dtype=str).fillna('')
    except: return None

# --- ВХІД ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

def main():
    if not st.session_state.logged_in:
        st.image(LOGO_URL, width=200)
        st.title("Вхід у систему")
        phone = st.text_input("Введіть ваш номер:")
        if st.button("🚪 Увійти", use_container_width=True):
            if phone == OWNER_PHONE:
                st.session_state.logged_in = True
                st.session_state.user_info = {'Назва': 'ВЛАСНИК', 'Роль': 'Owner', 'Телефон': phone}
                st.rerun()
            else:
                st.error("Доступ перевіряється...")
        return

    # МЕНЮ ДЛЯ МОБІЛЬНОГО
    st.image(LOGO_URL, width=150)
    choice = st.selectbox("📌 МЕНЮ:", ["🍎 Каталог", "🛒 Кошик", "📰 Новини", "⚙️ Налаштування"])

    if st.button("🚪 Вийти"):
        st.session_state.logged_in = False
        st.rerun()

    st.divider()
    st.write(f"Ви обрали розділ: {choice}")

if __name__ == "__main__":
    main()
