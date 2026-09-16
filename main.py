import sqlite3
import requests
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = "8846822722:AAGO6PGiEdr-QndV9mqVUEHGCCwDjIo3ZNc"
TELEGRAM_CHAT_ID = "1178298208"

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
        f"🚨 **تحدي جديد على {platform}!**\n\n"
        f"📌 **التحدي:** {title}\n"
        f"💰 **الجائزة:** {prize}\n"
        f"📅 **التاريخ / الموعد:** {date_info}\n\n"
        f"📝 **المحتوى والتفاصيل:**\n{short_desc}\n\n"
        f"🔗 [اضغط هنا للوصول للتحدي]({link})"
    )
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Error sending message: {e}")

def check_herox():
    print("--- جاري فحص HeroX ---")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    api_url = "https://www.herox.com/api/challenges" 
    try:
        res = requests.get(api_url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("challenges", [])[:5]:
                title = item.get("title", "غير محدد")
                link = "https://www.herox.com" + item.get("url", "")
                prize = item.get("prize_amount", "غير محدد")
                date_info = item.get("start_date") or item.get("submission_deadline") or "غير مدرج"
                description = item.get("description") or item.get("summary") or "لا يوجد وصف مختصر متوفر."

                if link and not is_seen(link):
                    send_telegram("HeroX", title, prize, date_info, description, link)
                    mark_seen(link)
                    print(f"HeroX Sent: {title}")
    except Exception as e:
        print(f"HeroX Error: {e}")

def check_kaggle():
    print("--- جاري فحص Kaggle ---")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    api_url = "https://www.kaggle.com/api/v1/competitions/list?search="
    try:
        res = requests.get(api_url, headers=headers, timeout=15)
        if res.status_code == 200:
            items = res.json()
            for item in items[:5]:
                title = item.get("title", "غير محدد")
                link = item.get("url", "https://www.kaggle.com/competitions")
                prize = item.get("reward", "غير محدد")
                date_info = item.get("enabledDate") or item.get("deadline") or "غير محدد"
                description = item.get("description") or item.get("briefDescription") or "تحدي على منصة Kaggle."

                if link and not is_seen(link):
                    send_telegram("Kaggle", title, prize, date_info, description, link)
                    mark_seen(link)
                    print(f"Kaggle Sent: {title}")
    except Exception as e:
        print(f"Kaggle Error: {e}")

def check_innocentive():
    print("--- جاري فحص InnoCentive ---")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    url = "https://challenge-center.community.innocentive.com/innovation-management/challenges"
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            cards = soup.select("a[href*='/challenge/'], a[href*='/innovation-management/']")
            for card in cards[:5]:
                title = card.text.strip() if card.text else "تحدي جديد في InnoCentive"
                link = card.get("href", "")
                if link.startswith("/"):
                    link = "https://challenge-center.community.innocentive.com" + link
                
                prize = "راجع تفاصيل التحدي عبر الرابط"
                date_info = "تم النشر حديثاً"
                description = "تحدي ابتكاري مفتوح من منصة InnoCentive."

                if link and not is_seen(link):
                    send_telegram("InnoCentive", title, prize, date_info, description, link)
                    mark_seen(link)
                    print(f"InnoCentive Sent: {title}")
    except Exception as e:
        print(f"InnoCentive Error: {e}")

if __name__ == "__main__":
    init_db()
    
    # إرسال إشعار تجريبي للتأكد من الربط مع التليجرام
    send_telegram(
        "اختبار النظام 🤖",
        "تم بدء عملية فحص المنصات بنجاح!",
        "تجريبي",
        "الآن",
        "هذه الرسالة تأكيدية لإثبات وصول الإشعارات من GitHub Actions إلى التليجرام بشكل مجاني وأوتوماتيكي.",
        "https://github.com"
    )
    
    print("شروع عملية فحص جميع المنصات المحددة...")
    check_herox()
    check_kaggle()
    check_innocentive()
    print("انتهى الفحص بنجاح!")
