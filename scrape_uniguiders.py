"""
scrape_uniguiders.py — UniGuiders Universities Scraper
=======================================================
Simple script using requests and BeautifulSoup for scraping university listings from UniGuiders.
Output: CSV (utf-8-sig) + JSON + SQLite in data/uniguiders/
Run: python scrape_uniguiders.py
"""

import csv
import json
import re
import sqlite3
import time
import random
import pathlib
from datetime import datetime
import requests
from bs4 import BeautifulSoup


# ============================================================
#  Configuration
# ============================================================

BASE_URL = "https://uniguiders.com"
LISTING_URL = f"{BASE_URL}/search-university/bachelor"

OUTPUT_DIR = pathlib.Path("e:/جلب بيانات/scraper_project/data/uniguiders")
UNIVERSITIES_CSV = OUTPUT_DIR / "universities.csv"
UNIVERSITIES_JSON = OUTPUT_DIR / "universities.json"
DB_PATH = OUTPUT_DIR / "uniguiders.db"

# Delays (seconds)
MIN_DELAY = 2
MAX_DELAY = 5

# Max retries per page
MAX_RETRIES = 3


# ============================================================
#  Cleaning Helpers
# ============================================================

def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())


# ============================================================
#  Scraping Functions
# ============================================================

def scrape_page(url):
    """Scrape a single page using requests."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            return response.text
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(5)
    return None


def extract_universities(soup):
    """Extract university data from BeautifulSoup object."""
    universities = []
    # Find university links - look for links containing university names
    links = soup.find_all('a', href=re.compile(r'/university/'))
    for link in links:
        full_text = clean_text(link.get_text())
        # Extract university name by finding the first occurrence of "University" or "College"
        # and taking text up to the first number (address) or common address words
        name = full_text
        # Remove year and student count at the end
        name = re.sub(r'\s+\d{4}\s+\d+(?:,\d+)?$', '', name)
        # Try to extract name before address patterns
        address_patterns = [
            r'\s+\d+.*',  # numbers like addresses
            r'\s+Jalan\s+',  # Jalan (street in Malay)
            r'\s+Persiaran\s+',  # Persiaran
            r'\s+Kuala\s+Lumpur',  # Kuala Lumpur
            r'\s+Cyberjaya',  # Cyberjaya
            r'\s+Selangor',  # Selangor
            r'\s+Malaysia\s+',  # Malaysia
        ]
        for pattern in address_patterns:
            match = re.search(pattern, name)
            if match:
                name = name[:match.start()].strip()
                break
        # Clean up any remaining unwanted text
        name = re.sub(r',\s*$', '', name)  # remove trailing comma
        if 'University' in name or 'College' in name:
            universities.append({
                "name": name,
                "link": BASE_URL + link['href'],
                "source": LISTING_URL
            })
    return universities


def scrape_all_pages():
    """Scrape all pages."""
    all_universities = []
    page_num = 1
    while page_num <= 5:  # Limit to 5 pages
        url = f"{LISTING_URL}?page={page_num}" if page_num > 1 else LISTING_URL
        print(f"Scraping page {page_num}: {url}")
        html = scrape_page(url)
        if not html:
            break
        soup = BeautifulSoup(html, 'html.parser')
        universities = extract_universities(soup)
        if not universities:
            break
        all_universities.extend(universities)
        page_num += 1

    return all_universities


# ============================================================
#  Data Saving
# ============================================================

def save_to_csv(data, filepath):
    """Save data to CSV."""
    if not data:
        return
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def save_to_json(data, filepath):
    """Save data to JSON."""
    if not data:
        return
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def save_to_sqlite(data, db_path):
    """Save data to SQLite."""
    if not data:
        return
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS universities (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        link TEXT,
                        source TEXT
                      )''')
    for item in data:
        cursor.execute("INSERT INTO universities (name, link, source) VALUES (?, ?, ?)",
                       (item['name'], item['link'], item['source']))
    conn.commit()
    conn.close()


# ============================================================
#  Main
# ============================================================

def main():
    print("Starting UniGuiders scraper...")
    data = scrape_all_pages()

    print(f"Extracted {len(data)} universities.")

    save_to_csv(data, UNIVERSITIES_CSV)
    save_to_json(data, UNIVERSITIES_JSON)
    save_to_sqlite(data, DB_PATH)

    print("Data saved successfully.")


if __name__ == "__main__":
    main()