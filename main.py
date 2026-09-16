import sqlite3
import requests
import json
from bs4 import BeautifulSoup

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
        f"🚨 **تحدي جديد مفتوح على {platform}!**\n\n"
        f"📌 **التحدي:** {title}\n"
        f"💰 **الجائزة:** {prize}\n"
        f"📅 **الموعد النهائي / الحالة:** {date_info}\n\n"
        f"📝 **التفاصيل والوصف:**\n{short_desc}\n\n"
        f"🔗 [اضغط هنا للتقديم والمشاركة]({link})"
    )
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Error sending message: {e}")

def send_status_update(message_text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message_text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Error sending status message: {e}")

# 1. فحص منصة HeroX
def check_herox():
    global new_challenges_count
    print("--- جاري فحص HeroX ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    url = "https://www.herox.com/explore"
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # البحث عن البطاقات المفتوحة للتقديم
            cards = soup.select(".challenge-card, .card-challenge, div[class*='challenge-card']")
            if not cards:
                cards = soup.select("a[href*='/challenge/']")
            
            for card in cards[:10]:
                title = card.text.strip().split("\n")[0] if card.text else "تحدي مفتوح على HeroX"
                link = card.get("href", "")
                if link and not link.startswith("http"):
                    link = "https://www.herox.com" + link
                
                prize = "راجع التفاصيل بالرابط"
                date_info = "مفتوح للحلول"
                description = "تحدي ابتكاري مفتوح على منصة HeroX للتطوير والرأي الهندسي والتقني."

                if link and "/challenge/" in link and not is_seen(link):
                    send_telegram("HeroX", title, prize, date_info, description, link)
                    mark_seen(link)
                    new_challenges_count += 1
                    print(f"HeroX Sent: {title}")
    except Exception as e:
        print(f"HeroX Error: {e}")

# 2. فحص منصة Kaggle
def check_kaggle():
    global new_challenges_count
    print("--- جاري فحص Kaggle ---")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    api_url = "https://www.kaggle.com/api/v1/competitions/list"
    try:
        res = requests.get(api_url, headers=headers, timeout=15)
        if res.status_code == 200:
            items = res.json()
            for item in items[:10]:
                title = item.get("title", "غير محدد")
                link = item.get("url", "https://www.kaggle.com/competitions")
                prize = item.get("reward", "غير محدد")
                date_info = item.get("deadline") or "مفتوح حالياً"
                description = item.get("description") or item.get("briefDescription") or "مسابقة ابتكارية وتحليل بيانات على Kaggle."

                if link and not is_seen(link):
                    send_telegram("Kaggle", title, prize, date_info, description, link)
                    mark_seen(link)
                    new_challenges_count += 1
                    print(f"Kaggle Sent: {title}")
    except Exception as e:
        print(f"Kaggle Error: {e}")

# 3. فحص منصة InnoCentive
def check_innocentive():
    global new_challenges_count
    print("--- جاري فحص InnoCentive ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = "https://www.innocentive.com/challenges/"
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # استخراج التحديات المفتوحة
            elements = soup.select("a[href*='/ar/'], a[href*='/challenge/'], a[href*='innocentive.com/']")
            for elem in elements[:10]:
                title = elem.text.strip()
                link = elem.get("href", "")
                if link and len(title) > 10:
                    if not link.startswith("http"):
                        link = "https://www.innocentive.com" + link

                    prize = "جوائز مالية (راجع الرابط)"
                    date_info = "مفتوح للتقديم"
                    description = "تحدي ابتكاري يبحث عن حلول علمية وتقنية من منصة InnoCentive."

                    if link and not is_seen(link):
                        send_telegram("InnoCentive", title, prize, date_info, description, link)
                        mark_seen(link)
                        new_challenges_count += 1
                        print(f"InnoCentive Sent: {title}")
    except Exception as e:
        print(f"InnoCentive Error: {e}")

if __name__ == "__main__":
    init_db()
    print("شروع عملية فحص جميع المنصات المحددة...")
    
    check_herox()
    check_kaggle()
    check_innocentive()
    
    if new_challenges_count == 0:
        send_status_update("✅ **تقرير الفحص الدوري:** تم فحص كافة المنصات (Kaggle, HeroX, InnoCentive) بنجاح. لا توجد تحديات جديدة مضافة حديثاً في هذه الدورة. البوت يعمل وجاهز!")
        
    print("انتهى الفحص بنجاح!")
