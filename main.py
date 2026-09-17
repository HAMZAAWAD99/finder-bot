import requests
import re
import time
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = "8846822722:AAGO6PGiEdr-QndV9mqVUEHGCCwDjIo3ZNc"
TELEGRAM_CHAT_ID = "1178298208"

def send_telegram(platform, title, link):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    msg = (
        f"🚨 **تحدي جديد على {platform}!**\n\n"
        f"📌 **التحدي:** {title}\n\n"
        f"🔗 [اضغط هنا للوصول للتحدي]({link})"
    )
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Telegram Error: {e}")

def run():
    total_sent = 0
    with sync_playwright() as p:
        # تشغيل متصفح حقيقي لتجاوز الحظر وتحميل عناصر JS
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # --- 1. HeroX ---
        print("--- جاري فتح HeroX ---")
        try:
            page.goto("https://www.herox.com/crowdsourcing-projects", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            
            # استخراج كافة الروابط والنصوص التي تحتوي على كلمة challenge أو project
            anchors = page.eval_on_selector_all("a", "elements => elements.map(e => ({href: e.href, text: e.innerText}))")
            seen = set()
            herox_count = 0
            for item in anchors:
                href = item.get('href', '')
                text = item.get('text', '').strip().split('\n')[0]
                if ("/challenge/" in href or "/project/" in href) and href not in seen and len(text) > 5:
                    seen.add(href)
                    send_telegram("HeroX", text, href)
                    herox_count += 1
                    total_sent += 1
                    if herox_count >= 5:
                        break
            print(f"HeroX: تم إرسال {herox_count}")
        except Exception as e:
            print(f"HeroX Error: {e}")

        # --- 2. InnoCentive ---
        print("--- جاري فتح InnoCentive ---")
        try:
            page.goto("https://challenge-center.community.innocentive.com/innovation-management/challenges", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            
            anchors = page.eval_on_selector_all("a", "elements => elements.map(e => ({href: e.href, text: e.innerText}))")
            seen = set()
            inno_count = 0
            for item in anchors:
                href = item.get('href', '')
                text = item.get('text', '').strip().split('\n')[0]
                if "/challenge/" in href and href not in seen and len(text) > 5:
                    seen.add(href)
                    send_telegram("InnoCentive", text, href)
                    inno_count += 1
                    total_sent += 1
                    if inno_count >= 5:
                        break
            print(f"InnoCentive: تم إرسال {inno_count}")
        except Exception as e:
            print(f"InnoCentive Error: {e}")

        browser.close()

    if total_sent == 0:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": "⚠️ لم يتم العثور على تحديات جديدة أثناء هذا التشغيل."}, timeout=15)

if __name__ == "__main__":
    run()
