import sqlite3
import requests

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
        f"📅 **الموعد / الحالة:** {date_info}\n\n"
        f"📝 **التفاصيل:**\n{short_desc}\n\n"
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

# 1. فحص HeroX
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
                description = item.get("description") or item.get("summary") or "تحدي ابتكاري على HeroX."

                if link and not is_seen(link):
                    send_telegram("HeroX", title, prize, date_info, description, link)
                    mark_seen(link)
                    new_challenges_count += 1
                    print(f"HeroX Sent: {title}")
    except Exception as e:
        print(f"HeroX Error: {e}")

# 2. فحص Kaggle
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
                description = item.get("description") or item.get("briefDescription") or "مسابقة ابتكارية على Kaggle."

                if link and not is_seen(link):
                    send_telegram("Kaggle", title, prize, date_info, description, link)
                    mark_seen(link)
                    new_challenges_count += 1
                    print(f"Kaggle Sent: {title}")
    except Exception as e:
        print(f"Kaggle Error: {e}")

# 3. فحص InnoCentive (Wazoku GraphQL API)
def check_innocentive():
    global new_challenges_count
    print("--- جاري فحص InnoCentive ---")
    url = "https://challenge-center.community.innocentive.com/api/graphql"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json"
    }
    query = """
    query {
      challenges(first: 10, filter: {status: OPEN}) {
        edges {
          node {
            id
            title
            summary
            rewardAmount
            slug
          }
        }
      }
    }
    """
    try:
        res = requests.post(url, json={'query': query}, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            challenges = data.get('data', {}).get('challenges', {}).get('edges', [])
            for item in challenges:
                node = item.get('node', {})
                title = node.get('title', 'تحدي جديد على InnoCentive')
                slug = node.get('slug', '')
                link = f"https://challenge-center.community.innocentive.com/innovation-management/challenge/{slug}" if slug else "https://challenge-center.community.innocentive.com"
                prize = str(node.get('rewardAmount', 'راجع الرابط'))
                description = node.get('summary', 'تحدي مفتوح للحلول والابتكار على منصة InnoCentive.')

                if link and not is_seen(link):
                    send_telegram("InnoCentive", title, prize, "مفتوح للتقديم", description, link)
                    mark_seen(link)
                    new_challenges_count += 1
                    print(f"InnoCentive Sent: {title}")
        else:
            fallback_innocentive()
    except Exception as e:
        print(f"InnoCentive API Error: {e}")
        fallback_innocentive()

def fallback_innocentive():
    global new_challenges_count
    url = "https://www.innocentive.com/api/challenge/v1/challenges"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            items = res.json()
            for item in items[:10]:
                title = item.get("title", "تحدي InnoCentive")
                link = item.get("url", "https://innocentive.com")
                prize = str(item.get("totalAward", "راجع التفاصيل"))
                description = item.get("description", "تحدي مفتوح في InnoCentive.")
                
                if link and not is_seen(link):
                    send_telegram("InnoCentive", title, prize, "مفتوح", description, link)
                    mark_seen(link)
                    new_challenges_count += 1
    except Exception as e:
        print(f"Fallback Error: {e}")

if __name__ == "__main__":
    init_db()
    print("شروع عملية فحص جميع المنصات المحددة...")
    
    check_herox()
    check_kaggle()
    check_innocentive()
    
    if new_challenges_count == 0:
        send_status_update("✅ **تقرير الفحص الدوري:** تم فحص كافة المنصات (HeroX, Kaggle, InnoCentive) بنجاح. لا توجد تحديات جديدة غير مسجلة حالياً.")
        
    print("انتهى الفحص بنجاح!")
