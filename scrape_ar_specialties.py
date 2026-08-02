import sqlite3
import csv
import pathlib
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

OUT_DIR = pathlib.Path('e:/جلب بيانات/scraper_project/data/your_uni/specialties_ar')
DB_PATH = OUT_DIR / 'specialties_ar.db'
CSV_PATH = OUT_DIR / 'specialties.csv'
JSON_PATH = OUT_DIR / 'specialties.json'

def setup_db():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ar_specialties (
            url TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            scraped_at TEXT
        )
    ''')
    conn.commit()
    return conn

def get_completed_urls(conn):
    return set(row[0] for row in conn.execute('SELECT url FROM ar_specialties'))

def export_db_to_csv():
    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT title, url, description FROM ar_specialties")
    db_items = [dict(row) for row in cur.fetchall()]
    if db_items:
        with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "url", "description"])
            writer.writeheader()
            writer.writerows(db_items)
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(db_items, f, ensure_ascii=False, indent=2)
        print(f"Exported {len(db_items)} specialties to CSV and JSON")
    conn.close()

def scrape_arabic_specialties():
    conn = setup_db()
    completed_urls = get_completed_urls(conn)
    cursor = conn.cursor()
    
    with open('e:/جلب بيانات/scraper_project/menu_links.json', 'r', encoding='utf-8') as f:
        all_links = json.load(f)
        
    specialties = []
    for item in all_links:
        if ': ' in item:
            name, url = item.split(': ', 1)
            name = name.strip()
            url = url.strip()
            if 'جامع' not in name and 'معهد' not in name and 'اكاديمي' not in name and 'الرئيسية' not in name:
                specialties.append({'name': name, 'url': url})
                
    pending_specialties = [spec for spec in specialties if spec['url'] not in completed_urls]
    print(f"Found {len(specialties)} specialties. Skipping {len(completed_urls)} completed. {len(pending_specialties)} remaining.")
    
    if not pending_specialties:
        print("All specialties exist in database. Exporting directly...")
        export_db_to_csv()
        return

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="e:/جلب بيانات/scraper_project/playwright_profile_ar",
            channel="chrome",
            headless=False,
            viewport={'width': 1280, 'height': 800},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            from playwright_stealth import stealth_sync
            stealth_sync(page)
        except Exception as e:
            print(f"Stealth init error: {e}")
        
        for idx, spec in enumerate(pending_specialties):
            print(f"[{idx+1}/{len(pending_specialties)}] Scraping {spec['name']}...")
            try:
                page.goto(spec['url'], timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(4000)
                
                page_title = page.title()
                if "403" in page_title or "Forbidden" in page_title or "Just a moment" in page_title:
                    print("  ...Cloudflare Challenge Detected! Waiting 15s...")
                    page.wait_for_timeout(15000)
                    
                title_elem = page.locator("h1").first
                title = title_elem.inner_text() if title_elem.count() > 0 else spec['name']
                    
                if "403" in title or "Forbidden" in title or "403" in page.title():
                    print("  -> Attempting manual refresh bypass...")
                    page.reload()
                    page.wait_for_timeout(15000)
                    if "403" in page.title() or "Forbidden" in page.title():
                        raise Exception("Still Blocked by Cloudflare (403 Forbidden)")
                    
                paragraphs = page.locator('.entry-content p, .elementor-text-editor p').all_inner_texts()
                
                content_parts = []
                for p_text in paragraphs:
                    p_clean = p_text.strip()
                    if p_clean and len(p_clean) > 20:
                        content_parts.append(p_clean)
                        
                description = " ".join(content_parts)
                if len(description) > 1000:
                    description = description[:997] + "..."
                    
                now = datetime.utcnow().isoformat()
                final_title = title.strip() if title else spec['name']
                
                cursor.execute('''
                    INSERT OR REPLACE INTO ar_specialties 
                    VALUES (?, ?, ?, ?)
                ''', (spec['url'], final_title, description, now))
                conn.commit()
                
                print(" -> Success!")
                
            except Exception as e:
                print(f" -> Failed to scrape {spec['url']}: {e}")
                
        context.close()
        conn.close()
        
    export_db_to_csv()

if __name__ == '__main__':
    scrape_arabic_specialties()
