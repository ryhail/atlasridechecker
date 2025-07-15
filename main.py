from time import sleep
import os
import requests
from datetime import datetime
import sys

API_URL = os.getenv("API_URL")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
THRESHOLD_DATE_STR = os.getenv("THRESHOLD_DATE")

if not all([API_URL, BOT_TOKEN, CHAT_ID, THRESHOLD_DATE_STR]):
    print("[ERROR] Некоторые переменные окружения не заданы.", file=sys.stderr)
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
    except requests.RequestException as e:
        print(f"[!] Ошибка при отправке сообщения в Telegram: {e}", file=sys.stderr)

while True:
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError:
        print("Ошибка при разборе JSON.", file=sys.stderr)
        sys.exit(1)

    available_rides = []

    for ride in data.get("rides", []):
        try:
            departure = datetime.fromisoformat(ride["departure"])
            if departure > THRESHOLD_DATE and ride["freeSeats"] > 0:
                available_rides.append(ride)
        except (KeyError, ValueError) as e:
            print(f"Неверный формат записи поездки: {ride} ({e})", file=sys.stderr)

    if available_rides:
        msg_lines = [f"<b>Найдены свободные поездки после {THRESHOLD_DATE_STR}:</b>"]
        for ride in available_rides:
            msg_lines.append(f"🚌 <b>{ride['departure']}</b> — {ride['freeSeats']} мест")

        message = "\n".join(msg_lines)
        send_telegram_message(message)
        print("Сообщение отправлено в Telegram.")
    else:
        print("Свободных мест после указанной даты не найдено.")
    sleep(30)
