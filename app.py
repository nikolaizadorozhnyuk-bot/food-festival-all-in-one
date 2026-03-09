import streamlit as st, pandas as pd, requests, io, re

CONFIG = {
    "LOGO_URL": "https://foodfestival.com.ua/image/catalog/logos/logo_foodfestival_upd-2.png",
    "CATALOG_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=0&single=true&output=csv",
    "CLIENTS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=841758260&single=true&output=csv",
    "ORDERS_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vROj05yiP9BW6ddvZ36HcczmZYg-Cxg1IOoJKmwp1lYWoBZ7T3PK9i7JMOj9nyMi4mmQW-nRQxfHexx/pub?gid=157728024&single=true&output=csv",
    "TG_TOKEN": "8275141603:AAGTvEF59ZOaD0rGsXHkitiWOA6TX-wTpRU",
    "GROUP_ID": "-1003641918928", "MIN_ORDER": 1000, "ITEMS_PER_PAGE": 12,
    "GEMINI_KEY": "AIzaSyBvM2lCiI00rFfvgXmXhTrJSdlfsRempWo",
    "ADMIN_PHONES": ["3806856949294"] # Впишіть свій номер для доступу до адмінки!
}

st.set_page_config(page_title="Food Festival ERP", layout="wide")
st.markdown("<style>.product-card { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.07); border: 1px solid #eee; margin-bottom: 20px; min-height: 480px; display: flex; flex-direction: column; justify-content: space-between;} .stButton > button { background-color: #D4AC0D !important; color: white !important; border-radius: 10px !important; width: 100%; font-weight: bold; border: none !important; } .metric-box { background: #fff; padding: 20px; border-radius: 15px; border-left: 5px solid #D4AC0D; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }</style>", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_data(url):
    try:
        df = pd.read_csv(io.StringIO(requests.get(url, timeout=10).content.decode('utf-8')), dtype=str).fillna('')
        df.columns = [c.strip() for c in df.columns]
        if len(df.columns) > 1 and 'Назва' in df.columns: df = df[df['Назва'].astype(str).str.strip() != '']
        return df
    except: return None

def get_ai_recommendations(cart_items):
    if not cart_items: return ""
    try:
        res = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={CONFIG['GEMINI_KEY']}", 
                            json={"contents": [{"parts": [{"text": f"Клієнт додав у кошик: {', '.join(cart_items)}. Порадь 2 супутні товари з продуктового магазину. Почни з '💡 ШІ Рекомендує додати:'"}]}]}, timeout=10)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except: return ""

def show_catalog(u):
    st.title("🍽️ Наше Меню")
    df = load_data(CONFIG["CATALOG_URL"])
    if df is None or df.empty: return st.warning("Каталог порожній.")
    
    cols = {c.lower(): c for c in df.columns}
    name_c, art_c, price_c = cols.get('назва', df.columns[0]), cols.get('upc', df.columns[1]), cols.get('цінапром', df.columns[-1])
    
    search = st.text_input("🔍 Швидкий пошук...")
    f_df = df[df[name_c].str.contains(search, case=False, na=False)] if search else df
    if f_df.empty: return st.info("Нічого не знайдено.")

    page = st.columns([1,4])[0].number_input("Сторінка", 1, max(1, (len(f_df)-1)//CONFIG["ITEMS_PER_PAGE"]+1), 1)
    items = f_df.iloc[(page-1)*CONFIG["ITEMS_PER_PAGE"] : page*CONFIG["ITEMS_PER_PAGE"]].to_dict('records')
    disc = float(str(u.get('Знижка', '0')).replace('%','')) / 100 if u.get('Знижка') else 0.0

    for i in range(0, len(items), 3):
        row_cols = st.columns(3)
        for j, item in enumerate(items[i:i+3]):
            with row_cols[j]:
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                img = re.findall(r'(https?://[^\s"\';)]+)', item.get('Фото', ''))
                st.image(img[0] if img else "https://via.placeholder.com/250?text=No+Photo", use_container_width=True)
                st.markdown(f"**{item.get(name_c, 'Без назви')}**")
                with st.expander("📖 Детальніше"): st.write(item.get('Опис (укр)', "Опис відсутній"))
                final_p = float(str(item.get(price_c, '0')).replace(',', '.')) * (1 - disc)
                st.subheader(f"{final_p:g} ₴")
                q = st.number_input("К-сть", min_value=0.0, step=1.0, key=f"q_{item.get(art_c, i)}_{j}")
                if st.button("🛒 В кошик", key=f"b_{item.get(art_c, i)}_{j}") and q > 0:
                    st.session_state.cart[item[name_c]] = {'qty': q, 'price': final_p}
                    st.toast(f"✅ Додано!")
                st.markdown('</div>', unsafe_allow_html=True)

def show_cart(u):
    st.title("🛒 Кошик")
    if not st.session_state.cart: return st.info("Кошик порожній.")
    total = sum(d['qty'] * d['price'] for d in st.session_state.cart.values())
    
    for name, d in list(st.session_state.cart.items()):
        c1, c2, c3 = st.columns([3, 1, 0.5])
        c1.write(f"**{name}**"); c2.write(f"{d['qty']} шт x {d['price']:g} ₴")
        if c3.button("❌", key=f"del_{name}"): del st.session_state.cart[name]; st.rerun()
    
    st.divider()
    with st.spinner("ШІ аналізує кошик..."):
        recom = get_ai_recommendations(list(st.session_state.cart.keys()))
        if recom: st.info(recom)
        
    st.subheader(f"Загальна сума: {total:g} ₴")
    if total >= CONFIG["MIN_ORDER"]:
        addr = st.text_input("📍 Адреса доставки", value=u.get('Адреса', ''))
        if st.button("🚀 ПІДТВЕРДИТИ ЗАМОВЛЕННЯ", use_container_width=True):
            items_list = "".join([f"🔸 {n} — {d['qty']} шт.\n" for n, d in st.session_state.cart.items()])
            requests.post(f"https://api.telegram.org/bot{CONFIG['TG_TOKEN']}/sendMessage", data={"chat_id": CONFIG["GROUP_ID"], "text": f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ</b>\n👤 <b>Клієнт:</b> {u.get('Назва', 'Невідомо')}\n📞 <b>Тел:</b> {u.get('Телефон', '')}\n📍 <b>Адреса:</b> {addr}\n━━━━━━━━━━━━━━━━━━\n🛒 <b>ТОВАРИ:</b>\n{items_list}━━━━━━━━━━━━━━━━━━\n💰 <b>РАЗОМ: {total:g} ₴</b>", "parse_mode": "HTML"})
            st.session_state.cart = {}; st.success("Замовлення відправлено!"); st.balloons()
    else: st.error(f"Додайте ще на {CONFIG['MIN_ORDER']-total:g} ₴ для мінімального замовлення.")

def show_admin_panel():
    st.title("⚙️ Адмін-панель (ABC-аналіз)")
    df_orders = load_data(CONFIG["ORDERS_URL"])
    if df_orders is None or df_orders.empty: return st.info("Немає даних.")
    sales = {}
    for _, row in df_orders.iterrows():
        for match in re.findall(r'🔸 (.*?) — (\d+(\.\d+)?) шт', str(row.get('Товари', ''))):
            sales[match[0].strip()] = sales.get(match[0].strip(), 0) + float(match[1])
            
    if not sales: return st.write("Помилка парсингу історії.")
    df_sales = pd.DataFrame(list(sales.items()), columns=['Товар', 'Продано шт.']).sort_values(by='Продано шт.', ascending=False).reset_index(drop=True)
    df_sales['Група'] = (df_sales['Продано шт.'] / df_sales['Продано шт.'].sum() * 100).cumsum().apply(lambda x: '🟩 A (Топ)' if x<=80 else ('🟨 B' if x<=95 else '🟥 C (Мертвий вантаж)'))
    st.dataframe(df_sales, use_container_width=True)

def main():
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔑 Вхід Food Festival")
        phone = st.text_input("Ваш номер телефону:")
        if st.button("Увійти"):
            df_c = load_data(CONFIG["CLIENTS_URL"])
            inp = re.sub(r'\D', '', phone)
            user = next((row.to_dict() for _, row in df_c.iterrows() if any(inp in re.sub(r'\D', '', str(v)) for v in row.values if len(str(v))>5)), None) if df_c is not None else None
            if user: st.session_state.logged_in, st.session_state.user_info = True, user; st.rerun()
            else: st.error("Номер не знайдено.")
    else:
        u = st.session_state.user_info
        st.sidebar.image(CONFIG["LOGO_URL"], width=150)
        menu = ["🍽️ Каталог", "🛒 Кошик", "📜 Історія"]
        
        # Перевірка на Адміна
        if any(re.sub(r'\D', '', str(u.get('Телефон', ''))).endswith(p[-9:]) for p in CONFIG["ADMIN_PHONES"]): menu.append("⚙️ Адмін-панель")
            
        choice = st.sidebar.radio("Меню", menu)
        if st.sidebar.button("🚪 Вийти"): st.session_state.logged_in = False; st.rerun()

        if choice == "🍽️ Каталог": show_catalog(u)
        elif choice == "🛒 Кошик": show_cart(u)
        elif choice == "⚙️ Адмін-панель": show_admin_panel()
        elif choice == "📜 Історія":
            st.title("📜 Історія замовлень")
            df = load_data(CONFIG["ORDERS_URL"])
            my = df[df.apply(lambda x: re.sub(r'\D', '', str(u.get('Телефон', ''))) in re.sub(r'\D', '', str(x)), axis=1)] if df is not None else pd.DataFrame()
            if my.empty: st.info("Історія порожня.")
            else:
                for _, r in my.iloc[::-1].head(10).iterrows():
                    with st.expander(f"📦 {r.get('Дата', '---')} | {r.get('Сума', '0')} ₴"): st.write(r.get('Товари', ''))

if __name__ == "__main__": main()
