import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import pytz

URL = "https://www.headachesound.com/woworder/wow-flutter-machine"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "5022930235")
DAILY_REPORT       = os.environ.get("DAILY_REPORT", "false").lower() == "true"
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
    }

def main():
    now_hk = datetime.now(HK_TZ).strftime("%Y-%m-%d %H:%M HKT")
    print(f"[{now_hk}] Checking WOW Machine stock... (daily_report={DAILY_REPORT})")

    try:
        result = check_availability()
    except Exception as e:
        err_msg = (
            f"⚠️ WOW Monitor 오류\n"
            f"시간: {now_hk}\n"
            f"오류: {e}"
        )
        print(f"[ERROR] {e}")
        send_telegram(err_msg)
        return

    print(f"  availability : {result['availability_meta']}")
    print(f"  is_available : {result['is_available']}")

    if result["is_available"]:
        # 재입고 감지 → 즉시 알림
        msg = (
            "🔴 MIDNIGHT WOW MACHINE 재입고!\n\n"
            f"⏰ {now_hk}\n"
            f"📦 Status: AVAILABLE\n"
            f"🔗 {URL}\n\n"
            "⚡ 지금 바로 들어가세요!"
        )
        send_telegram(msg)
        print("[ALERT] Restock detected — Telegram sent!")

    elif DAILY_REPORT:
        # 매일 08:00 HKT 상태 리포트 (솔드아웃 유지 중)
        msg = (
            "📋 WOW Machine 일일 리포트\n\n"
            f"⏰ {now_hk}\n"
            f"📦 Status: SOLD OUT\n"
            f"🔗 {URL}\n\n"
            "모니터링 정상 작동 중 ✅"
        )
        send_telegram(msg)
        print("[DAILY] Status report sent.")

    else:
        print("Still SOLD OUT. No notification.")

if __name__ == "__main__":
    main()
