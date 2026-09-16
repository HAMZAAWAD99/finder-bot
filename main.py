import sqlite3
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = "8846822722:AAGO6PGiEdr-QndV9mqVUEHGCCwDjIo3ZNc"
TELEGRAM_CHAT_ID = "1178298208"

new_challenges_count = 0

def init_db():
    conn = sqlite3.connect("seen_challenges.db")
    cursor = conn.cursor()
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
        f"🚨 **تحدي مفتوح على {platform}!**\n\n"
        f"📌 **التحدي:** {title}\n"
        f"💰 **الجائزة:** {prize}\n"
        f"📅 **التاريخ / الحالة:** {date_info}\n\n"
        f"📝 **التفاصيل:**\n{short_desc}\n\n"
        f"🔗 [اضغط هنا للوصول للتحدي]({link})"
    )
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Telegram Error: {e}")

def scrape_all_with_playwright():
    global new_challenges_count
    init_db()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        # ---------------- 1. فحص HeroX ----------------
        print("--- جاري تصفح HeroX ---")
        try:
            page.goto("https://www.herox.com/explore", wait_until="networkidle", timeout=30000)
            items = page.query_selector_all("a[href*='/challenge/']")
            print(f"تم العثور على {len(items)} عنصر في HeroX")
            
            for item in items[:15]:
                link = item.get_attribute("href")
                if link and not link.startswith("http"):
                    link = "https://www.herox.com" + link
                
                title = item.inner_text().strip().split("\n")[0]
                if title and link and not is_seen(link):
                    send_telegram("HeroX", title, "راجع الرابط", "مفتوح للتقديم", "تحدي ابتكاري متاح على منصة HeroX.", link)
                    mark_seen(link)
                    new_challenges_count += 1
        except Exception as e:
            print(f"HeroX Error: {e}")

        # ---------------- 2. فحص InnoCentive ----------------
        print("--- جاري تصفح InnoCentive ---")
        try:
            page.goto("https://challenge-center.community.innocentive.com/innovation-management/challenges", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(4000)
            
            cards = page.query_selector_all("a[href*='/challenge/']")
            print(f"تم العثور على {len(cards)} عنصر في InnoCentive")
            
            for card in cards[:15]:
                link = card.get_attribute("href")
                if link and not link.startswith("http"):
                    link = "https://challenge-center.community.innocentive.com" + link
                
                title = card.inner_text().strip().split("\n")[0]
                if title and len(title) > 5 and not is_seen(link):
                    send_telegram("InnoCentive", title, "جوائز مالية (راجع التفاصيل)", "مفتوح حالياً", "تحدي ابتكاري يبحث عن حلول على InnoCentive.", link)
                    mark_seen(link)
                    new_challenges_count += 1
        except Exception as e:
            print(f"InnoCentive Error: {e}")

        browser.close()

# ---------------- 3. فحص Kaggle عبر الـ API الرسمي ----------------
def check_kaggle():
    global new_challenges_count
    print("--- جاري فحص Kaggle ---")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get("https://www.kaggle.com/api/v1/competitions/list", headers=headers, timeout=15)
        if res.status_code == 200:
            items = res.json()
            for item in items[:15]:
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
    print("بدء عملية الفحص الشامل باستخدام المتصفح السحابي...")
    scrape_all_with_playwright()
    check_kaggle()
    
    if new_challenges_count == 0:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": "✅ **تقرير الفحص:** تم تصفح المنصات بنجاح، ولم يتم العثور على تحديات *جديدة* غير مسجلة لدينا مسبقاً."}, timeout=15)
        
    print("انتهى الفحص بنجاح!")
