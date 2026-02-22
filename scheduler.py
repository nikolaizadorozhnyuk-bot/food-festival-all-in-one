import requests
import os

# Твої дані (вони вже в нас є)
TELEGRAM_TOKEN = "8183938320:AAHsDhUXcu3ZeKg8Qh3AZc3xbXMa9YqqqZc"
CHAT_ID = "-5236190167"

def send_reminder():
    text = "🔔 <b>Food Festival: Автоматичне нагадування!</b>\n\nШановні клієнти, сьогодні день замовлень. Будь ласка, перевірте залишки та залиште заявку в додатку. Гарного дня! 🍏"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    
    try:
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            print("✅ Нагадування успішно надіслано!")
        else:
            print(f"❌ Помилка: {r.text}")
    except Exception as e:
        print(f"🆘 Виникла помилка: {e}")

if __name__ == "__main__":
    send_reminder()
