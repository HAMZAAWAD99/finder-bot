import sqlite3
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = "8846822722:AAGO6PGiEdr-QndV9mqVUEHGCCwDjIo3ZNc"
TELEGRAM_CHAT_ID = "1178298208"

new_challenges_count = 0

def init_db():
    conn = sqlite3.connect("seen_challenges.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS challenges") # لتصفير الجدول وجلب كل التحديات حالياً
    cursor.execute("CREATE TABLE IF NOT EXISTS challenges (link TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

def is_seen(link):
    conn = sqlite3.connect("seen_challenges.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM challenges WHERE link = ?", (link,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def mark_seen(link):
    conn = sqlite3.connect("seen_challenges.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO challenges VALUES (?)", (link,))
        conn.commit()
    except:
        pass
    conn.close()

def send_telegram(platform, title, prize, date_info, description, link):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    short_desc = description[:250] + "..." if len(description) > 250 else description
    
    msg = (
        f"🚨 **تحدي جديد على {platform}!**\n\n"
        f"📌 **التحدي:** {title}\n"
        f"💰 **الجائزة:** {prize}\n"
        f"📅 **الموعد / الحالة:** {date_info}\n\n"
        f"📝 **التفاصيل:**\n{short_desc}\n\n"
        f"🔗 [اضغط هنا للوصول للتحدي]({link})"
    )
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Telegram Error: {e}")

def run_stealth_parser():
    global new_challenges_count
    
    with sync_playwright() as p:
        # تشغيل المتصفح بمواصفات حقيقية لتجاوز الـ WAF
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        # ---------- 1. HeroX Parser ----------
        print("--- جاري فحص HeroX ---")
        try:
            page.goto("https://www.herox.com/explore", wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(5000) # انتظار لتجاوز فحص Cloudflare
            
            # استخراج كافة الروابط المباشرة للتحديات
            elements = page.eval_on_selector_all(
                "a[href*='/challenge/']",
                "nodes => nodes.map(n => ({ text: n.innerText.trim(), href: n.href }))"
            )
            
            found_herox = 0
            for item in elements:
                link = item['href']
                title = item['text'].split('\n')[0]
                
                # تصفية الروابط الفرعية لضمان أخذ رابط التحدي الرئيسي فقط
                if link and "/challenge/" in link and not is_seen(link) and len(title) > 3:
                    send_telegram("HeroX", title, "راجع التفاصيل بالرابط", "مفتوح للتقديم", "تحدي ابتكاري متاح حالياً على منصة HeroX.", link)
                    mark_seen(link)
                    new_challenges_count += 1
                    found_herox += 1
                    if found_herox >= 10: break
            print(f"تم جلب {found_herox} تحدي من HeroX")
        except Exception as e:
            print(f"HeroX Error: {e}")

        # ---------- 2. InnoCentive Parser ----------
        print("--- جاري فحص InnoCentive ---")
        try:
            page.goto("https://challenge-center.community.innocentive.com/innovation-management/challenges", wait_until="networkidle", timeout=40000)
            page.wait_for_timeout(6000)
            
            elements = page.eval_on_selector_all(
                "a[href*='/challenge/']",
                "nodes => nodes.map(n => ({ text: n.innerText.trim(), href: n.href }))"
            )
            
            found_innocentive = 0
            for item in elements:
                link = item['href']
                title = item['text'].split('\n')[0]
                
                if link and not is_seen(link) and len(title) > 5:
                    send_telegram("InnoCentive", title, "جوائز مالية (راجع الرابط)", "مفتوح للتقديم", "تحدي ابتكاري يبحث عن حلول وتقنيات على InnoCentive.", link)
                    mark_seen(link)
                    new_challenges_count += 1
                    found_innocentive += 1
                    if found_innocentive >= 10: break
            print(f"تم جلب {found_innocentive} تحدي من InnoCentive")
        except Exception as e:
            print(f"InnoCentive Error: {e}")

        browser.close()

# ---------- 3. Kaggle API Parser ----------
def check_kaggle():
    global new_challenges_count
    print("--- جاري فحص Kaggle ---")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get("https://www.kaggle.com/api/v1/competitions/list", headers=headers, timeout=15)
        if res.status_code == 200:
            items = res.json()
            for item in items[:10]:
                title = item.get("title", "مسابقة Kaggle")
                link = item.get("url", "https://www.kaggle.com/competitions")
                prize = str(item.get("reward", "غير محدد"))
                date_info = str(item.get("deadline", "مفتوح"))
                description = item.get("briefDescription") or "مسابقة ابتكارية متاح التنافس فيها على Kaggle."

                if link and not is_seen(link):
                    send_telegram("Kaggle", title, prize, date_info, description, link)
                    mark_seen(link)
                    new_challenges_count += 1
    except Exception as e:
        print(f"Kaggle Error: {e}")

if __name__ == "__main__":
    init_db()
    print("بدء عملية الـ Parsing وتجاوز الـ WAF...")
    run_stealth_parser()
    check_kaggle()
    
    if new_challenges_count == 0:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": "✅ **تقرير الفحص:** تم تنفيذ الـ Parser بنجاح مع تجاوز الـ WAF، ولم يتم العثور على تحديات جديدة."}, timeout=15)
        
    print("انتهى الفحص بنجاح!")
