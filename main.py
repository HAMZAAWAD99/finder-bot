import requests
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = "8846822722:AAGO6PGiEdr-QndV9mqVUEHGCCwDjIo3ZNc"
TELEGRAM_CHAT_ID = "1178298208"
SCRAPER_API_KEY = "c4abf51b7121d19fde5bfd339c7c5ba32e34560079c12fce860e966794bbcafd"

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

def get_page_content(target_url):
    # تمرير الطلب عبر ScraperAPI لتجاوز الـ WAF و Cloudflare
    api_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true"
    try:
        response = requests.get(api_url, timeout=60)
        if response.status_code == 200:
            return response.text
        else:
            print(f"ScraperAPI Error ({target_url}): Status {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception fetching {target_url}: {e}")
        return None

# ---------- 1. HeroX ----------
def check_herox():
    print("--- جاري فحص HeroX عبر ScraperAPI ---")
    html = get_page_content("https://www.herox.com/crowdsourcing-projects")
    if not html:
        return 0
    
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", href=True)
    count = 0
    seen = set()

    for a in links:
        href = a['href']
        title = a.get_text(strip=True)
        if "/challenge/" in href or "/project/" in href:
            full_url = "https://www.herox.com" + href if href.startswith("/") else href
            if full_url not in seen and len(title) > 5:
                seen.add(full_url)
                send_telegram("HeroX", title, "راجع الرابط لتفاصيل الجائزة", "مفتوح للتقديم", "تحدي ابتكاري متاح على HeroX.", full_url)
                count += 1
                if count >= 5: break
    print(f"HeroX Results: {count}")
    return count

# ---------- 2. InnoCentive ----------
def check_innocentive():
    print("--- جاري فحص InnoCentive عبر ScraperAPI ---")
    html = get_page_content("https://challenge-center.community.innocentive.com/innovation-management/challenges")
    if not html:
        return 0
    
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", href=True)
    count = 0
    seen = set()

    for a in links:
        href = a['href']
        title = a.get_text(strip=True)
        if "/challenge/" in href:
            full_url = "https://challenge-center.community.innocentive.com" + href if href.startswith("/") else href
            if full_url not in seen and len(title) > 5:
                seen.add(full_url)
                send_telegram("InnoCentive", title, "جوائز مالية (راجع الرابط)", "مفتوح للتقديم", "تحدي ابتكاري متاح على منصة InnoCentive.", full_url)
                count += 1
                if count >= 5: break
    print(f"InnoCentive Results: {count}")
    return count

# ---------- 3. Kaggle ----------
def check_kaggle():
    print("--- جاري فحص Kaggle عبر ScraperAPI ---")
    html = get_page_content("https://www.kaggle.com/competitions")
    if not html:
        return 0
    
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", href=True)
    count = 0
    seen = set()

    for a in links:
        href = a['href']
        title = a.get_text(strip=True)
        if "/competitions/" in href and not href.endswith("/competitions"):
            full_url = "https://www.kaggle.com" + href if href.startswith("/") else href
            if full_url not in seen and len(title) > 3:
                seen.add(full_url)
                send_telegram("Kaggle", title, "راجع التفاصيل بالرابط", "مفتوح حالياً", "مسابقة ابتكار وتحليل بيانات على Kaggle.", full_url)
                count += 1
                if count >= 5: break
    print(f"Kaggle Results: {count}")
    return count

if __name__ == "__main__":
    print("بدء عملية الاستخراج الحقيقية وتجاوز الـ WAF...")
    c1 = check_herox()
    c2 = check_innocentive()
    c3 = check_kaggle()
    
    total = c1 + c2 + c3
    if total == 0:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": "⚠️ **تنبيه:** لم يتم العثور على تحديات، يرجى مراجعة الرصيد في ScraperAPI."}, timeout=15)
        
    print(f"انتهت العملية! تم إرسال {total} تحدي بنجاح.")
