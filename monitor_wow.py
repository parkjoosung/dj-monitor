import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import pytz

URL = "https://www.headachesound.com/woworder/wow-flutter-machine"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "5022930235")
HK_TZ = pytz.timezone("Asia/Hong_Kong")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN not set")
        return
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    resp = requests.post(api_url, json=payload, timeout=10)
    if resp.status_code == 200:
        print("[OK] Telegram message sent")
    else:
        print(f"[ERROR] Telegram send failed: {resp.status_code} {resp.text}")

def check_availability():
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    meta_avail = soup.find("meta", property="product:availability")
    availability_meta = meta_avail["content"].strip().lower() if meta_avail else "unknown"

    title = soup.title.string if soup.title else ""
    title_soldout = "sold out" in title.lower()

    is_available = (
        availability_meta not in ("oos", "out of stock")
        and not title_soldout
    )

    return {
        "is_available": is_available,
        "availability_meta": availability_meta,
        "title": title.strip(),
        "title_soldout": title_soldout,
    }

def main():
    now_hk = datetime.now(HK_TZ).strftime("%Y-%m-%d %H:%M HKT")
    print(f"[{now_hk}] Checking WOW Machine stock...")

    try:
        result = check_availability()
    except Exception as e:
        err_msg = (
            f"ERROR WOW Monitor\n"
            f"Time: {now_hk}\n"
            f"Error: {e}\n"
            f"URL: {URL}"
        )
        print(f"[ERROR] {e}")
        send_telegram(err_msg)
        return

    print(f"  availability_meta : {result['availability_meta']}")
    print(f"  title_soldout     : {result['title_soldout']}")
    print(f"  is_available      : {result['is_available']}")

    if result["is_available"]:
        msg = (
            "MIDNIGHT WOW MACHINE 재입고!\n\n"
            f"Time: {now_hk}\n"
            f"Status: AVAILABLE\n"
            f"Link: {URL}\n\n"
            "빨리 들어가세요!"
        )
        send_telegram(msg)
        print("[ALERT] Restock detected!")
    else:
        print("Still SOLD OUT. No notification sent.")

if __name__ == "__main__":
    main()
