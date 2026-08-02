import sqlite3
import csv
import pathlib
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright

OUT_DIR = pathlib.Path('e:/جلب بيانات/scraper_project/data/your_uni/universities_ar')
DB_PATH = OUT_DIR / 'universities_ar.db'
UNIS_CSV = OUT_DIR / 'universities.csv'
UNIS_JSON = OUT_DIR / 'universities.json'
COURSES_CSV = OUT_DIR / 'courses.csv'
COURSES_JSON = OUT_DIR / 'courses.json'

def setup_db():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ar_universities (
            arabic_url TEXT PRIMARY KEY,
            name_ar TEXT,
            about_text_ar TEXT,
            english_url TEXT,
            scraped_at TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ar_courses (
            course_name_ar TEXT,
            university_name TEXT,
            arabic_url TEXT,
            requirements_ar TEXT,
            additional_info TEXT,
            scraped_at TEXT,
            PRIMARY KEY (course_name_ar, arabic_url)
        )
    ''')
    conn.commit()
    return conn

def get_completed_urls(conn):
    return set(row[0] for row in conn.execute('SELECT arabic_url FROM ar_universities'))

def export_db_to_csv():
    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Universities
    cur.execute("SELECT name_ar as NameAr, about_text_ar as AboutTextAr, english_url as EnglishUrl, arabic_url as ArabicUrl FROM ar_universities")
    db_unis = [dict(row) for row in cur.fetchall()]
    if db_unis:
        with open(UNIS_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["NameAr", "AboutTextAr", "EnglishUrl", "ArabicUrl"])
            writer.writeheader()
            writer.writerows(db_unis)
        with open(UNIS_JSON, "w", encoding="utf-8") as f:
            json.dump(db_unis, f, ensure_ascii=False, indent=2)
        print(f"Exported {len(db_unis)} universities to CSV and JSON.")

    # Courses
    cur.execute("SELECT university_name as UniversityName, course_name_ar as CourseNameAr, requirements_ar as RequirementsAr, additional_info as AdditionalInfo FROM ar_courses")
    db_courses = [dict(row) for row in cur.fetchall()]
    if db_courses:
        with open(COURSES_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["UniversityName", "CourseNameAr", "RequirementsAr", "AdditionalInfo"])
            writer.writeheader()
            writer.writerows(db_courses)
        with open(COURSES_JSON, "w", encoding="utf-8") as f:
            json.dump(db_courses, f, ensure_ascii=False, indent=2)
        print(f"Exported {len(db_courses)} courses to CSV and JSON")
        
    conn.close()

def scrape_arabic_universities():
    conn = setup_db()
    completed_urls = get_completed_urls(conn)
    cursor = conn.cursor()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="e:/جلب بيانات/scraper_project/playwright_profile",
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
        
        try:
            with open('e:/جلب بيانات/scraper_project/menu_links.json', 'r', encoding='utf-8') as f:
                links_data = json.load(f)
            
            uni_links = []
            for ln in links_data:
                if ':' in ln:
                    title, url = ln.split(':', 1)
                    title, url = title.strip(), url.strip()
                    if 'جامع' in title or 'معهد' in title or 'اكاديمية' in title:
                        uni_links.append(url)
            
            unique_links = list(set(uni_links))
            pending_links = [u for u in unique_links if u not in completed_urls]
            print(f"Found {len(unique_links)} unique university links.")
            print(f"Skipping {len(completed_urls)} completed. {len(pending_links)} remaining.\\n")

            for idx, uni_url in enumerate(pending_links):
                print(f"[{idx+1}/{len(pending_links)}] Scraping University: {uni_url}...")
                page.goto(uni_url, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(4000)
                
                if "403" in page.title() or "Just a moment" in page.title():
                    print("   ⏳ Cloudflare challenge ... Waiting 15s...")
                    page.wait_for_timeout(15000)
                
                # EXTRACT UNIVERSITY DATA
                title_elem = page.locator("h1").first
                name_ar = title_elem.inner_text().strip() if title_elem.count() > 0 else ""
                if not name_ar:
                     name_ar = uni_url.split('/')[-2] if uni_url.endswith('/') else uni_url.split('/')[-1]

                # Description
                paragraphs = page.locator('.entry-content p, .elementor-text-editor p').all_inner_texts()
                about_text_ar = " ".join([p.strip() for p in paragraphs if len(p.strip()) > 20])
                if len(about_text_ar) > 2000:
                    about_text_ar = about_text_ar[:1997] + "..."

                # English URL
                en_link_loc = page.locator('link[hreflang*="en"]')
                english_url = ""
                if en_link_loc.count() > 0:
                    english_url = en_link_loc.first.get_attribute("href")
                
                if not english_url:
                    wpml_loc = page.locator('.wpml-ls-item-en a')
                    if wpml_loc.count() > 0:
                        english_url = wpml_loc.first.get_attribute("href")

                now = datetime.utcnow().isoformat()
                
                # Immediate DB Insert for University
                cursor.execute('''
                    INSERT OR REPLACE INTO ar_universities 
                    VALUES (?, ?, ?, ?, ?)
                ''', (uni_url, name_ar, about_text_ar, english_url, now))
                
                # EXTRACT COURSES
                courses_added = 0
                tables = page.locator("table")
                if tables.count() > 0:
                    rows = page.locator("table tr").all()
                    for r in rows:
                        cells = r.locator("td, th").all_inner_texts()
                        cells = [c.strip() for c in cells]
                        if not cells or "".join(cells) == "":
                            continue
                            
                        course_name = cells[0] if len(cells) > 0 else ""
                        requirements = cells[1] if len(cells) > 1 else ""
                        misc_info = " | ".join(cells[2:]) if len(cells) > 2 else ""
                        
                        if len(course_name) > 3 and "البرنامج" not in course_name and "التخصص" not in course_name:
                            cursor.execute('''
                                INSERT OR REPLACE INTO ar_courses 
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (course_name, name_ar, uni_url, requirements, misc_info, now))
                            courses_added += 1
                else:
                    items = page.locator('.elementor-icon-list-item').all_inner_texts()
                    if items:
                         for item in items:
                             if len(item) > 5:
                                 cursor.execute('''
                                     INSERT OR REPLACE INTO ar_courses 
                                     VALUES (?, ?, ?, ?, ?, ?)
                                 ''', (item.strip(), name_ar, uni_url, "", "", now))
                                 courses_added += 1
                
                conn.commit()
                print(f" -> Saved {name_ar} and {courses_added} courses to database.")

        except Exception as e:
            print("Error:", e)
        finally:
            context.close()
            conn.close()
            
    # Always export full DB at the end
    export_db_to_csv()

if __name__ == "__main__":
    scrape_arabic_universities()
