import sqlite3
import requests
import time
from playwright.sync_api import sync_playwright

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

def scrape_with_stealth_browser():
    global new_challenges_count
    
    with sync_playwright() as p:
        # تشغيل متصفح كامل حقيقي لتجاوز الـ 403 Cloudflare
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="en-US"
        )
        
        page = context.new_page()

        # ---------- 1. HeroX Scraper ----------
        print("--- جاري تصفح HeroX ---")
        try:
            page.goto("https://www.herox.com/explore", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000) # انتظار تجاوز حماية Cloudflare
            
            # استخراج روابط البطاقات
            links = page.eval_on_selector_all(
                "a[href*='/challenge/']",
                "nodes => nodes.map(n => ({ href: n.href, text: n.innerText }))"
            )
            
            herox_added = 0
            seen_links = set()
            for item in links:
                href = item["href"]
                text = item["text"].strip()
                title = text.split("\n")[0] if text else "تحدي مفتوح على HeroX"
                
                if href and "/challenge/" in href and href not in seen_links and len(title) > 3:
                    seen_links.add(href)
                    send_telegram("HeroX", title, "راجع التفاصيل في الرابط", "مفتوح للتقديم", "تحدي ابتكاري مفتوح للتقديم الآن على منصة HeroX.", href)
                    herox_added += 1
                    new_challenges_count += 1
                    if herox_added >= 10: break
            print(f"تم جلب {herox_added} تحدي من HeroX بنجاح!")
        except Exception as e:
            print(f"HeroX Browser Error: {e}")

        # ---------- 2. InnoCentive Scraper ----------
        print("--- جاري تصفح InnoCentive ---")
        try:
            page.goto("https://challenge-center.community.innocentive.com/innovation-management/challenges", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(7000) # انتظار تحميل تطبيق الصفحة الواحدة SPA
            
            links = page.eval_on_selector_all(
                "a[href*='/challenge/']",
                "nodes => nodes.map(n => ({ href: n.href, text: n.innerText }))"
            )
            
            innocentive_added = 0
            seen_links_inno = set()
            for item in links:
                href = item["href"]
                text = item["text"].strip()
                title = text.split("\n")[0] if text else "تحدي InnoCentive"
                
                if href and href not in seen_links_inno and len(title) > 5:
                    seen_links_inno.add(href)
                    send_telegram("InnoCentive", title, "جوائز مالية (راجع الرابط)", "مفتوح حالياً", "تحدي مفتوح للحلول والابتكار من منصة InnoCentive.", href)
                    innocentive_added += 1
                    new_challenges_count += 1
                    if innocentive_added >= 10: break
            print(f"تم جلب {innocentive_added} تحدي من InnoCentive بنجاح!")
        except Exception as e:
            print(f"InnoCentive Browser Error: {e}")

        # ---------- 3. Kaggle Scraper ----------
        print("--- جاري تصفح Kaggle ---")
        try:
            page.goto("https://www.kaggle.com/competitions", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            
            links = page.eval_on_selector_all(
                "a[href*='/competitions/']",
                "nodes => nodes.map(n => ({ href: n.href, text: n.innerText }))"
            )
            
            kaggle_added = 0
            seen_kaggle = set()
            for item in links:
                href = item["href"]
                text = item["text"].strip()
                title = text.split("\n")[0] if text else "مسابقة Kaggle"
                
                if href and href not in seen_kaggle and len(title) > 3 and "/competitions/" in href:
                    # استبعاد الروابط الفرعية العامة
                    if href.endswith("/competitions") or "/about" in href:
                        continue
                    seen_kaggle.add(href)
                    send_telegram("Kaggle", title, "محددة في صفحة المسابقة", "مفتوحة التنافس", "مسابقة تحليل بيانات وذكاء اصطناعي متاحة على Kaggle.", href)
                    kaggle_added += 1
                    new_challenges_count += 1
                    if kaggle_added >= 10: break
            print(f"تم جلب {kaggle_added} مسابقة من Kaggle بنجاح!")
        except Exception as e:
            print(f"Kaggle Browser Error: {e}")

        browser.close()

if __name__ == "__main__":
    print("بدء عملية التصفح الحقيقي وتجاوز حماية الـ 403...")
    scrape_with_stealth_browser()
    
    if new_challenges_count == 0:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": "⚠️ **تنبيه:** لم يتم العثور على تحديات متوفرة حالياً بالصفحات المفتوحة."}, timeout=15)
        
    print("انتهت العملية بالكامل!")
