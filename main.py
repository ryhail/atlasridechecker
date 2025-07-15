import os
import sys
import requests
from datetime import datetime
import asyncio
from aiohttp import web

# === Конфигурация ===
API_URL = os.getenv("API_URL")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
THRESHOLD_DATE_STR = os.getenv("THRESHOLD_DATE")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
PORT = int(os.getenv("PORT", "8080"))

if not all([API_URL, BOT_TOKEN, CHAT_ID, THRESHOLD_DATE_STR]):
    print("[ERROR] Не заданы переменные окружения.", file=sys.stderr)
    sys.exit(1)

THRESHOLD_DATE = datetime.fromisoformat(THRESHOLD_DATE_STR)
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram_message(text: str):
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(TELEGRAM_API_URL, json=payload)
        r.raise_for_status()
        print("Сообщение отправлено в Telegram.")
    except requests.RequestException as e:
        print(f"[!] Ошибка отправки в Telegram: {e}", file=sys.stderr)

def check_and_notify():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"[!] Ошибка запроса: {e}", file=sys.stderr)
        return
    except ValueError:
        print("[!] Неверный JSON.", file=sys.stderr)
        return

    available_rides = []

    for ride in data.get("rides", []):
        try:
            departure = datetime.fromisoformat(ride["departure"])
            if departure > THRESHOLD_DATE and ride.get("freeSeats", 0) > 0:
                available_rides.append(ride)
        except (KeyError, ValueError) as e:
            print(f"[!] Неправильная запись поездки: {ride} ({e})", file=sys.stderr)

    if available_rides:
        msg_lines = [f"<b>Найдены свободные поездки после {THRESHOLD_DATE_STR}:</b>"]
        for ride in available_rides:
            msg_lines.append(f"🚌 <b>{ride['departure']}</b> — {ride['freeSeats']} мест")
        send_telegram_message("\n".join(msg_lines))
    else:
        print("Свободных поездок не найдено.")

async def background_loop():
    while True:
        print("[INFO] Запуск проверки...")
        check_and_notify()
        await asyncio.sleep(CHECK_INTERVAL)

async def handle_health(request):
    return web.Response(text="OK")

async def init_app():
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    asyncio.create_task(background_loop())
    return app

if __name__ == "__main__":
    web.run_app(init_app(), port=PORT)
