import sqlite3
import requests
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = "8846822722:AAGO6PGiEdr-QndV9mqVUEHGCCwDjIo3ZNc"
TELEGRAM_CHAT_ID = "1178298208"

# متغير لتتبع عدد التحديات الجديدة التي تم العثور عليها
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
        f"🚨 **تحدي مفتوح جديد على {platform}!**\n\n"
        f"📌 **التحدي:** {title}\n"
        f"💰 **الجائزة:** {prize}\n"
        f"📅 **الموعد النهائي:** {date_info}\n\n"
        f"📝 **الوصف:**\n{short_desc}\n\n"
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

def check_herox():
    global new_challenges_count
    print("--- جاري فحص HeroX ---")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    api_url = "https://www.herox.com/api/challenges?status=open" 
    try:
        res = requests.get(api_url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            challenges = data.get("challenges", []) or data.get("results", [])
            for item in challenges[:10]:
                title = item.get("title", "غير محدد")
                link = "https://www.herox.com" + item.get("url", "")
                prize = item.get("prize_amount", "غير محدد")
                date_info = item.get("submission_deadline") or item.get("start_date") or "مفتوح للتقديم"
                description = item.get("description") or item.get("summary") or "تحدي ابتكاري مفتوح على HeroX."

                if link and not is_seen(link):
                    send_telegram("HeroX", title, prize, date_info, description, link)
                    mark_seen(link)
                    new_challenges_count += 1
                    print(f"HeroX Sent: {title}")
    except Exception as e:
        print(f"HeroX Error: {e}")

def check_kaggle():
    global new_challenges_count
    print("--- جاري فحص Kaggle ---")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    api_url = "https://www.kaggle.com/api/v1/competitions/list?group=general&sortBy=latestDeadline"
    try:
        res = requests.get(api_url, headers=headers, timeout=15)
        if res.status_code == 200:
            items = res.json()
            for item in items[:10]:
                if item.get("userHasEntered") is False or item.get("enabled", True):
                    title = item.get("title", "غير محدد")
                    link = item.get("url", "https://www.kaggle.com/competitions")
                    prize = item.get("reward", "غير محدد")
                    date_info = item.get("deadline") or "مفتوح حالياً"
                    description = item.get("description") or item.get("briefDescription") or "مسابقة مفتوحة على Kaggle."

                    if link and not is_seen(link):
                        send_telegram("Kaggle", title, prize, date_info, description, link)
                        mark_seen(link)
                        new_challenges_count += 1
                        print(f"Kaggle Sent: {title}")
    except Exception as e:
        print(f"Kaggle Error: {e}")

def check_innocentive():
    global new_challenges_count
    print("--- جاري فحص InnoCentive ---")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    url = "https://challenge-center.community.innocentive.com/innovation-management/challenges"
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            cards = soup.select("a[href*='/challenge/'], a[href*='/innovation-management/']")
            for card in cards[:10]:
                title = card.text.strip() if card.text else "تحدي مفتوح في InnoCentive"
                link = card.get("href", "")
                if link.startswith("/"):
                    link = "https://challenge-center.community.innocentive.com" + link
                
                prize = "راجع تفاصيل التحدي عبر الرابط"
                date_info = "مفتوح للتقديم"
                description = "تحدي ابتكاري مفتوح من منصة InnoCentive."

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
    
    # إذا لم يتم إرسال أي تحدٍ جديد، سيتم إرسال رسالة اطمئنان
    if new_challenges_count == 0:
        send_status_update("✅ **الفحص الدوري مكتمل:** تم فحص المنصات بنجاح، ولا توجد تحديات جديدة حتّى الآن. البوت يعمل بكفاءة وسيتحقق مجدداً في الدورة القادمة!")
        
    print("انتهى الفحص بنجاح!")
