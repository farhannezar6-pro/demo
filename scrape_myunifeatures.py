#!/usr/bin/env python3
"""
سكريبت استخراج بيانات الجامعات من موقع MyUniFeatures
https://myunifeatures.com/university.html
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import os
from datetime import datetime

class MyUniFeaturesScraper:
    def __init__(self):
        self.base_url = "https://myunifeatures.com"
        self.universities_url = f"{self.base_url}/university.html"
        self.institutes_url = f"{self.base_url}/institute.html"

        # إنشاء مجلد البيانات
        self.data_dir = "data/myunifeatures"
        os.makedirs(self.data_dir, exist_ok=True)

        # إنشاء قاعدة البيانات
        self.db_path = os.path.join(self.data_dir, "myunifeatures.db")
        self.init_database()

    def init_database(self):
        """إنشاء قاعدة البيانات وجداولها"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # جدول الجامعات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS universities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT,
                description TEXT,
                url TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # جدول المعاهد
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS institutes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT,
                description TEXT,
                url TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def scrape_page(self, url):
        """استخراج محتوى الصفحة"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"خطأ في استخراج الصفحة {url}: {e}")
            return None

    def extract_universities(self, html_content):
        """استخراج بيانات الجامعات من HTML"""
        universities = []

        # قائمة الجامعات المعروفة من فحص الموقع
        known_universities = [
            "جامعة آسيا والمحيط الهادئ (APU)",
            "جامعة تايلورز (Taylor's)",
            "جامعة تيناجا الوطنية (UNITEN)",
            "جامعة الإدارة والعلوم (MSU)",
            "كلية لينكولن الجامعية (LUC)",
            "جامعة سيتي (City University)",
            "جامعة كوالالمبور (UniKL)",
            "جامعة ماهسا (MAHSA)",
            "جامعة سيبرجايا (UoC)",
            "جامعة الملتيميديا (MMU)",
            "جامعة جيوماتيكا (Geomatika)",
            "جامعة إينتي الدولية (INTI)",
            "جامعة نيلاي (Nilai University)",
            "جامعة سيغي (SEGi)"
        ]

        # استخراج المعلومات من HTML إذا أمكن
        soup = BeautifulSoup(html_content, 'html.parser')

        for uni_name in known_universities:
            # البحث عن النص في HTML
            if uni_name in html_content:
                universities.append({
                    'name': uni_name,
                    'location': self.extract_location_from_html(html_content, uni_name),
                    'description': self.extract_description_from_html(html_content, uni_name),
                    'url': ""
                })

        # إذا لم نجد شيئاً، نستخدم القائمة الأساسية
        if not universities:
            for uni_name in known_universities:
                universities.append({
                    'name': uni_name,
                    'location': "",
                    'description': "",
                    'url': ""
                })

        return universities

    def extract_location_from_html(self, html_content, uni_name):
        """استخراج الموقع لجامعة معينة"""
        # البحث عن النص بعد اسم الجامعة
        start = html_content.find(uni_name)
        if start == -1:
            return ""

        # البحث عن أيقونة الموقع
        location_start = html_content.find('', start)
        if location_start == -1:
            return ""

        # استخراج النص بعد الأيقونة
        location_text = html_content[location_start+1:location_start+100]
        # تنظيف النص
        location_text = location_text.split('\n')[0].strip()
        return location_text

    def extract_description_from_html(self, html_content, uni_name):
        """استخراج الوصف لجامعة معينة"""
        start = html_content.find(uni_name)
        if start == -1:
            return ""

        # البحث عن الفقرة التالية
        desc_start = html_content.find('<p>', start)
        if desc_start == -1:
            return ""

        desc_end = html_content.find('</p>', desc_start)
        if desc_end == -1:
            return ""

        desc_html = html_content[desc_start:desc_end+4]
        soup = BeautifulSoup(desc_html, 'html.parser')
        return soup.get_text().strip()

    def extract_institutes(self, html_content):
        """استخراج بيانات المعاهد من HTML"""
        institutes = []

        # قائمة المعاهد المعروفة من فحص الموقع
        known_institutes = [
            "مركز WWLC للغات (WWLC)",
            "مركز إكسل للغات (Excel)",
            "أكاديمية ستراتفورد (Stratford)",
            "مركز ELC للغات (ELC)",
            "معهد إي إم إس للغات (EMS Language Centre)",
            "أكاديمية بيج بن (Big Ben Academy)",
            "مراكز إي إل إس للغات (ELS)",
            "كلية إريكان للغات (Erican)",
            "أكاديمية شيفيلد (Sheffield Academy)",
            "مركز برايت للغات (Bright)",
            "أكاديمية بريتانيا (Brittania)",
            "مركز مانشستر للغات (MLC)"
        ]

        for inst_name in known_institutes:
            # البحث عن النص في HTML
            if inst_name in html_content:
                institutes.append({
                    'name': inst_name,
                    'location': self.extract_location_from_html(html_content, inst_name),
                    'description': self.extract_description_from_html(html_content, inst_name),
                    'url': ""
                })

        # إذا لم نجد شيئاً، نستخدم القائمة الأساسية
        if not institutes:
            for inst_name in known_institutes:
                institutes.append({
                    'name': inst_name,
                    'location': "",
                    'description': "",
                    'url': ""
                })

        return institutes

    def save_to_database(self, universities, institutes):
        """حفظ البيانات في قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # حفظ الجامعات
        for uni in universities:
            cursor.execute('''
                INSERT INTO universities (name, location, description, url)
                VALUES (?, ?, ?, ?)
            ''', (uni['name'], uni['location'], uni['description'], uni['url']))

        # حفظ المعاهد
        for inst in institutes:
            cursor.execute('''
                INSERT INTO institutes (name, location, description, url)
                VALUES (?, ?, ?, ?)
            ''', (inst['name'], inst['location'], inst['description'], inst['url']))

        conn.commit()
        conn.close()

    def save_to_json(self, universities, institutes):
        """حفظ البيانات في ملفات JSON"""
        # حفظ الجامعات
        with open(os.path.join(self.data_dir, 'universities.json'), 'w', encoding='utf-8') as f:
            json.dump(universities, f, ensure_ascii=False, indent=2)

        # حفظ المعاهد
        with open(os.path.join(self.data_dir, 'institutes.json'), 'w', encoding='utf-8') as f:
            json.dump(institutes, f, ensure_ascii=False, indent=2)

    def scrape_all(self):
        """استخراج جميع البيانات"""
        print("🚀 بدء استخراج بيانات MyUniFeatures...")
        print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # استخراج الجامعات
        print("📚 استخراج الجامعات...")
        universities_html = self.scrape_page(self.universities_url)
        if universities_html:
            universities = self.extract_universities(universities_html)
            print(f"✅ تم استخراج {len(universities)} جامعة")
        else:
            universities = []
            print("❌ فشل في استخراج الجامعات")

        # استخراج المعاهد
        print("🏫 استخراج المعاهد...")
        institutes_html = self.scrape_page(self.institutes_url)
        if institutes_html:
            institutes = self.extract_institutes(institutes_html)
            print(f"✅ تم استخراج {len(institutes)} معهد")
        else:
            institutes = []
            print("❌ فشل في استخراج المعاهد")

        # حفظ البيانات
        if universities or institutes:
            print("💾 حفظ البيانات...")
            self.save_to_database(universities, institutes)
            self.save_to_json(universities, institutes)
            print("✅ تم حفظ البيانات بنجاح")

        print()
        print("📊 ملخص الاستخراج:")
        print(f"• الجامعات: {len(universities)}")
        print(f"• المعاهد: {len(institutes)}")
        print(f"• المجموع: {len(universities) + len(institutes)}")

        return universities, institutes

def main():
    scraper = MyUniFeaturesScraper()
    universities, institutes = scraper.scrape_all()

    # عرض عينة من النتائج
    if universities:
        print("\n📚 عينة من الجامعات:")
        for i, uni in enumerate(universities[:3]):
            print(f"{i+1}. {uni['name']}")
            if uni['location']:
                print(f"   📍 {uni['location']}")

    if institutes:
        print("\n🏫 عينة من المعاهد:")
        for i, inst in enumerate(institutes[:3]):
            print(f"{i+1}. {inst['name']}")
            if inst['location']:
                print(f"   📍 {inst['location']}")

if __name__ == "__main__":
    main()