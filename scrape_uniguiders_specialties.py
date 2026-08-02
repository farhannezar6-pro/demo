"""
scrape_uniguiders_specialties.py — UniGuiders Specialties Scraper
==================================================================
Script to extract specialties/programs from each university page on UniGuiders.
Reads universities from data/uniguiders/universities.csv
Output: CSV + JSON + SQLite in data/uniguiders_specialties/
Run: python scrape_uniguiders_specialties.py
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

OUTPUT_DIR = pathlib.Path("e:/جلب بيانات/scraper_project/data/uniguiders_specialties")
SPECIALTIES_CSV = OUTPUT_DIR / "specialties.csv"
SPECIALTIES_JSON = OUTPUT_DIR / "specialties.json"
DB_PATH = OUTPUT_DIR / "specialties.db"

INPUT_CSV = pathlib.Path("e:/جلب بيانات/scraper_project/data/uniguiders/universities.csv")

# Delays (seconds)
MIN_DELAY = 3
MAX_DELAY = 7

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
            print(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(5)
    return None


def extract_specialties(soup, university_name, university_link):
    """Extract specialties/programs from university page."""
    specialties = []

    # Look for program/specialty links or sections
    # Common patterns: links to programs, course listings, etc.

    # Try to find program links
    program_links = soup.find_all('a', href=re.compile(r'/program/|/course/|/specialty/'))

    for link in program_links:
        name = clean_text(link.get_text())
        if name and len(name) > 3:  # Filter out very short names
            specialties.append({
                "university_name": university_name,
                "university_link": university_link,
                "specialty_name": name,
                "specialty_link": BASE_URL + link['href'] if link['href'].startswith('/') else link['href'],
                "source": university_link
            })

    # If no program links found, try to find course/specialty sections
    if not specialties:
        # Look for common section headers or lists
        sections = soup.find_all(['h2', 'h3', 'h4', 'div'], class_=re.compile(r'program|course|specialty|major|degree'))
        for section in sections:
            text = clean_text(section.get_text())
            if text and len(text) > 5 and ('Bachelor' in text or 'Master' in text or 'Degree' in text):
                specialties.append({
                    "university_name": university_name,
                    "university_link": university_link,
                    "specialty_name": text,
                    "specialty_link": "",
                    "source": university_link
                })

    return specialties


def scrape_university_specialties(university):
    """Scrape specialties for a single university."""
    url = university['link']
    print(f"Scraping specialties for: {university['name']}")

    html = scrape_page(url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    specialties = extract_specialties(soup, university['name'], university['link'])

    print(f"Found {len(specialties)} specialties for {university['name']}")
    return specialties


def load_universities():
    """Load universities from CSV."""
    universities = []
    with open(INPUT_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            universities.append(row)
    return universities


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
    cursor.execute('''CREATE TABLE IF NOT EXISTS specialties (
                        id INTEGER PRIMARY KEY,
                        university_name TEXT,
                        university_link TEXT,
                        specialty_name TEXT,
                        specialty_link TEXT,
                        source TEXT
                      )''')
    for item in data:
        cursor.execute("""INSERT INTO specialties
                         (university_name, university_link, specialty_name, specialty_link, source)
                         VALUES (?, ?, ?, ?, ?)""",
                       (item['university_name'], item['university_link'],
                        item['specialty_name'], item['specialty_link'], item['source']))
    conn.commit()
    conn.close()


# ============================================================
#  Main
# ============================================================

def main():
    print("Starting UniGuiders specialties scraper...")

    # Load universities
    universities = load_universities()
    print(f"Loaded {len(universities)} universities from CSV")

    all_specialties = []

    # Scrape specialties for each university
    for university in universities:  # Process all universities
        specialties = scrape_university_specialties(university)
        all_specialties.extend(specialties)

    print(f"Total specialties extracted: {len(all_specialties)}")

    # Save data
    save_to_csv(all_specialties, SPECIALTIES_CSV)
    save_to_json(all_specialties, SPECIALTIES_JSON)
    save_to_sqlite(all_specialties, DB_PATH)

    print("Data saved successfully.")


if __name__ == "__main__":
    main()