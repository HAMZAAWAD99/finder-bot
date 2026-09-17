import sqlite3
import requests
import json

TELEGRAM_BOT_TOKEN = "8846822722:AAGO6PGiEdr-QndV9mqVUEHGCCwDjIo3ZNc"
TELEGRAM_CHAT_ID = "1178298208"

new_challenges_count = 0

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

# ---------- 1. HeroX API Direct ----------
def check_herox():
    global new_challenges_count
    print("--- جاري فحص HeroX ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest"
    }
    url = "https://www.herox.com/api/challenges?page=1"
    try:
        res = requests.get(url, headers=headers, timeout=20)
        print(f"HeroX Status Code: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            items = []
            if isinstance(data, dict):
                items = data.get("challenges") or data.get("results") or data.get("items") or []
            elif isinstance(data, list):
                items = data
                
            count = 0
            for item in items[:10]:
                if isinstance(item, dict):
                    title = item.get("title") or item.get("name") or "تحدي على HeroX"
                    slug = item.get("url") or item.get("slug") or ""
                    link = "https://www.herox.com" + slug if slug.startswith("/") else slug
                    prize = str(item.get("prize_amount") or item.get("total_prize") or "راجع التفاصيل")
                    date_info = str(item.get("submission_deadline") or "مفتوح")
                    desc = item.get("description") or item.get("summary") or "تحدي ابتكاري مفتوح في HeroX."

                    if link and title:
                        send_telegram("HeroX", title, prize, date_info, desc, link)
                        count += 1
                        new_challenges_count += 1
            print(f"HeroX Results: {count}")
    except Exception as e:
        print(f"HeroX Error: {e}")

# ---------- 2. InnoCentive / Wazoku API ----------
def check_innocentive():
    global new_challenges_count
    print("--- جاري فحص InnoCentive ---")
    
    # محاولة الجلب عبر API البحث المباشر في Wazoku
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    url = "https://challenge-center.community.innocentive.com/api/v1/challenges"
    try:
        res = requests.get(url, headers=headers, timeout=20)
        print(f"InnoCentive REST API Status: {res.status_code}")
        if res.status_code == 200:
            items = res.json()
            if isinstance(items, dict):
                items = items.get("challenges") or items.get("data") or []
            
            count = 0
            for item in items[:10]:
                title = item.get("title") or "تحدي مفتوح في InnoCentive"
                slug = item.get("slug") or item.get("id") or ""
                link = f"https://challenge-center.community.innocentive.com/innovation-management/challenge/{slug}" if slug else "https://challenge-center.community.innocentive.com"
                prize = str(item.get("rewardAmount") or item.get("prize") or "راجع التفاصيل")
                desc = item.get("summary") or item.get("description") or "تحدي ابتكاري مفتوح."

                send_telegram("InnoCentive", title, prize, "مفتوح للتقديم", desc, link)
                count += 1
                new_challenges_count += 1
            print(f"InnoCentive Results: {count}")
        else:
            fallback_innocentive_graphql()
    except Exception as e:
        print(f"InnoCentive Error: {e}")
        fallback_innocentive_graphql()

def fallback_innocentive_graphql():
    global new_challenges_count
    print("--- تجربة GraphQL البديل لـ InnoCentive ---")
    url = "https://challenge-center.community.innocentive.com/api/graphql"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json"
    }
    query = """
    query {
      challenges {
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
        res = requests.post(url, json={"query": query}, headers=headers, timeout=20)
        print(f"InnoCentive GraphQL Status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            edges = data.get("data", {}).get("challenges", {}).get("edges", [])
            count = 0
            for edge in edges:
                node = edge.get("node", {})
                title = node.get("title") or "تحدي InnoCentive"
                slug = node.get("slug") or ""
                prize = str(node.get("rewardAmount") or "20,000$ (راجع التفاصيل)")
                desc = node.get("summary") or "تحدي ابتكاري في InnoCentive."
                
                if slug:
                    link = f"https://challenge-center.community.innocentive.com/innovation-management/challenge/{slug}"
                    send_telegram("InnoCentive", title, prize, "مفتوح للتقديم", desc, link)
                    count += 1
                    new_challenges_count += 1
            print(f"InnoCentive GraphQL Results: {count}")
    except Exception as e:
        print(f"GraphQL Fallback Error: {e}")

# ---------- 3. Kaggle API ----------
def check_kaggle():
    global new_challenges_count
    print("--- جاري فحص Kaggle ---")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get("https://www.kaggle.com/api/v1/competitions/list", headers=headers, timeout=15)
        print(f"Kaggle Status Code: {res.status_code}")
        if res.status_code == 200:
            items = res.json()
            count = 0
            for item in items[:10]:
                title = item.get("title", "مسابقة Kaggle")
                link = item.get("url", "https://www.kaggle.com/competitions")
                prize = str(item.get("reward", "غير محدد"))
                date_info = str(item.get("deadline", "مفتوح"))
                description = item.get("briefDescription") or "مسابقة ابتكارية متاح التنافس فيها على Kaggle."

                send_telegram("Kaggle", title, prize, date_info, description, link)
                count += 1
                new_challenges_count += 1
            print(f"Kaggle Results: {count}")
    except Exception as e:
        print(f"Kaggle Error: {e}")

if __name__ == "__main__":
    print("بدء عملية الاستخراج المحدثة...")
    check_herox()
    check_innocentive()
    check_kaggle()
    
    if new_challenges_count == 0:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": "✅ **تقرير الفحص:** تم تنفيذ الفحص المحدث ولم تتمكن الـ APIs من العثور على تحديات متوفرة."}, timeout=15)
        
    print("انتهت العملية!")
