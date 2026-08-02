"""
clean_uniguiders_data.py — تنظيف ودمج بيانات UniGuiders
============================================================
سكريبت لتنظيف ودمج بيانات الجامعات والتخصصات من UniGuiders
الإخراج: ملف JSON و CSV نظيف في data/cleaned/
"""

import csv
import json
import re
import sqlite3
import pathlib
from datetime import datetime


# ============================================================
#  Configuration
# ============================================================

OUTPUT_DIR = pathlib.Path("e:/جلب بيانات/scraper_project/data/cleaned")
CLEAN_DATA_JSON = OUTPUT_DIR / "uniguiders_clean_data.json"
CLEAN_DATA_CSV = OUTPUT_DIR / "uniguiders_clean_data.csv"

UNIVERSITIES_DB = pathlib.Path("e:/جلب بيانات/scraper_project/data/uniguiders/uniguiders.db")
SPECIALTIES_DB = pathlib.Path("e:/جلب بيانات/scraper_project/data/uniguiders_specialties/specialties.db")


# ============================================================
#  Cleaning Functions
# ============================================================

def clean_university_name(name):
    """تنظيف اسم الجامعة"""
    if not name:
        return ""

    # إزالة العناوين والأرقام
    name = re.sub(r'\s*\d+.*$', '', name)  # إزالة الأرقام والعناوين
    name = re.sub(r',\s*$', '', name)  # إزالة الفاصلة في النهاية
    name = re.sub(r'\s+', ' ', name)  # توحيد المسافات

    return name.strip()


def clean_specialty_name(name):
    """تنظيف اسم التخصص"""
    if not name:
        return ""

    # استخراج السعر إذا وجد
    price_match = re.search(r'(\d+(?:,\d+)?)\s*MYR', name)
    price = price_match.group(1).replace(',', '') if price_match else None

    # إزالة السعر من الاسم
    clean_name = re.sub(r'\s*\d+(?:,\d+)?\s*MYR\s*$', '', name)

    # تنظيف إضافي
    clean_name = re.sub(r'\s+', ' ', clean_name)
    clean_name = clean_name.strip()

    return clean_name, price


def clean_specialty_data(specialty):
    """تنظيف بيانات التخصص"""
    name, price = clean_specialty_name(specialty['specialty_name'])

    return {
        'university_name': clean_university_name(specialty['university_name']),
        'university_link': specialty['university_link'],
        'specialty_name': name,
        'specialty_link': specialty['specialty_link'],
        'price_myr': int(price) if price else None,
        'source': specialty['source']
    }


# ============================================================
#  Data Loading
# ============================================================

def load_universities():
    """تحميل الجامعات من قاعدة البيانات"""
    universities = []
    if not UNIVERSITIES_DB.exists():
        print("تحذير: قاعدة بيانات الجامعات غير موجودة")
        return universities

    conn = sqlite3.connect(UNIVERSITIES_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT name, link, source FROM universities')
    for row in cursor.fetchall():
        universities.append({
            'name': row[0],
            'link': row[1],
            'source': row[2]
        })
    conn.close()
    return universities


def load_specialties():
    """تحميل التخصصات من قاعدة البيانات"""
    specialties = []
    if not SPECIALTIES_DB.exists():
        print("تحذير: قاعدة بيانات التخصصات غير موجودة")
        return specialties

    conn = sqlite3.connect(SPECIALTIES_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT university_name, university_link, specialty_name, specialty_link, source FROM specialties')
    for row in cursor.fetchall():
        specialties.append({
            'university_name': row[0],
            'university_link': row[1],
            'specialty_name': row[2],
            'specialty_link': row[3],
            'source': row[4]
        })
    conn.close()
    return specialties


# ============================================================
#  Data Processing
# ============================================================

def create_clean_dataset(universities, specialties):
    """إنشاء مجموعة بيانات نظيفة"""
    # تنظيف الجامعات
    clean_universities = []
    for uni in universities:
        clean_uni = {
            'name': clean_university_name(uni['name']),
            'link': uni['link'],
            'source': uni['source'],
            'specialties': []
        }
        clean_universities.append(clean_uni)

    # تنظيف التخصصات وتجميعها بالجامعات
    university_map = {uni['link']: uni for uni in clean_universities}

    for spec in specialties:
        clean_spec = clean_specialty_data(spec)
        uni_link = clean_spec['university_link']

        if uni_link in university_map:
            university_map[uni_link]['specialties'].append({
                'name': clean_spec['specialty_name'],
                'link': clean_spec['specialty_link'],
                'price_myr': clean_spec['price_myr']
            })

    # إزالة الجامعات بدون تخصصات
    final_universities = [uni for uni in clean_universities if uni['specialties']]

    return {
        'metadata': {
            'source': 'UniGuiders.com',
            'extraction_date': datetime.now().isoformat(),
            'total_universities': len(final_universities),
            'total_specialties': sum(len(uni['specialties']) for uni in final_universities)
        },
        'universities': final_universities
    }


# ============================================================
#  Data Saving
# ============================================================

def save_to_json(data, filepath):
    """حفظ البيانات كـ JSON"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_to_csv(data, filepath):
    """حفظ البيانات كـ CSV"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)

        # كتابة الرأس
        writer.writerow(['University Name', 'University Link', 'Specialty Name', 'Specialty Link', 'Price MYR'])

        # كتابة البيانات
        for uni in data['universities']:
            for spec in uni['specialties']:
                writer.writerow([
                    uni['name'],
                    uni['link'],
                    spec['name'],
                    spec['link'],
                    spec['price_myr'] or ''
                ])


# ============================================================
#  Main
# ============================================================

def main():
    print("بدء تنظيف بيانات UniGuiders...")

    # تحميل البيانات
    universities = load_universities()
    specialties = load_specialties()

    print(f"تم تحميل {len(universities)} جامعة")
    print(f"تم تحميل {len(specialties)} تخصص")

    # إنشاء مجموعة البيانات النظيفة
    clean_data = create_clean_dataset(universities, specialties)

    print(f"بعد التنظيف: {clean_data['metadata']['total_universities']} جامعة")
    print(f"بعد التنظيف: {clean_data['metadata']['total_specialties']} تخصص")

    # حفظ البيانات
    save_to_json(clean_data, CLEAN_DATA_JSON)
    save_to_csv(clean_data, CLEAN_DATA_CSV)

    print("تم حفظ البيانات النظيفة بنجاح!")
    print(f"موقع الملفات: {OUTPUT_DIR}")
    print(f"- JSON: {CLEAN_DATA_JSON.name}")
    print(f"- CSV: {CLEAN_DATA_CSV.name}")


if __name__ == "__main__":
    main()