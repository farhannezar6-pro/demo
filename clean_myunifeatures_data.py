#!/usr/bin/env python3
"""
تنظيف بيانات MyUniFeatures ودمجها
"""

import sqlite3
import json
import os
from datetime import datetime

class MyUniFeaturesDataCleaner:
    def __init__(self):
        self.data_dir = "data/myunifeatures"
        self.cleaned_dir = "data/cleaned"
        os.makedirs(self.cleaned_dir, exist_ok=True)

        self.db_path = os.path.join(self.data_dir, "myunifeatures.db")
        self.cleaned_json_path = os.path.join(self.cleaned_dir, "myunifeatures_clean_data.json")

    def load_raw_data(self):
        """تحميل البيانات الأولية من قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # تحميل الجامعات
        cursor.execute("SELECT name, location, description FROM universities")
        universities = cursor.fetchall()

        # تحميل المعاهد
        cursor.execute("SELECT name, location, description FROM institutes")
        institutes = cursor.fetchall()

        conn.close()

        return universities, institutes

    def clean_university_name(self, name):
        """تنظيف اسم الجامعة"""
        # إزالة الأقواس والمعلومات الإضافية
        if '(' in name and ')' in name:
            # الاحتفاظ بالاسم الكامل مع الاختصار
            pass
        return name.strip()

    def clean_location(self, location):
        """تنظيف الموقع"""
        if not location:
            return ""
        # تنظيف النص وإزالة الأحرف الخاصة
        location = location.replace('', '').strip()
        return location

    def clean_description(self, description):
        """تنظيف الوصف"""
        if not description:
            return ""
        return description.strip()

    def create_clean_dataset(self):
        """إنشاء مجموعة البيانات النظيفة"""
        universities_raw, institutes_raw = self.load_raw_data()

        clean_data = {
            "metadata": {
                "source": "MyUniFeatures",
                "url": "https://myunifeatures.com/",
                "extraction_date": datetime.now().isoformat(),
                "total_universities": len(universities_raw),
                "total_institutes": len(institutes_raw)
            },
            "universities": [],
            "institutes": []
        }

        # تنظيف الجامعات
        for name, location, description in universities_raw:
            clean_uni = {
                "name": self.clean_university_name(name),
                "location": self.clean_location(location),
                "description": self.clean_description(description),
                "type": "university"
            }
            clean_data["universities"].append(clean_uni)

        # تنظيف المعاهد
        for name, location, description in institutes_raw:
            clean_inst = {
                "name": self.clean_university_name(name),
                "location": self.clean_location(location),
                "description": self.clean_description(description),
                "type": "language_institute"
            }
            clean_data["institutes"].append(clean_inst)

        return clean_data

    def save_clean_data(self, clean_data):
        """حفظ البيانات النظيفة"""
        with open(self.cleaned_json_path, 'w', encoding='utf-8') as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)

        print(f"✅ تم حفظ البيانات النظيفة في: {self.cleaned_json_path}")

    def generate_statistics(self, clean_data):
        """توليد إحصائيات"""
        stats = {
            "total_universities": len(clean_data["universities"]),
            "total_institutes": len(clean_data["institutes"]),
            "total_institutions": len(clean_data["universities"]) + len(clean_data["institutes"]),
            "locations": {}
        }

        # إحصاء المواقع
        all_locations = []
        for uni in clean_data["universities"]:
            if uni["location"]:
                all_locations.append(uni["location"])
        for inst in clean_data["institutes"]:
            if inst["location"]:
                all_locations.append(inst["location"])

        # عد المواقع الفريدة
        unique_locations = set(all_locations)
        stats["unique_locations"] = len(unique_locations)
        stats["locations_list"] = sorted(list(unique_locations))

        return stats

    def clean_all(self):
        """تنظيف جميع البيانات"""
        print("🧹 بدء تنظيف بيانات MyUniFeatures...")
        print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # إنشاء البيانات النظيفة
        clean_data = self.create_clean_dataset()

        # حفظ البيانات
        self.save_clean_data(clean_data)

        # توليد الإحصائيات
        stats = self.generate_statistics(clean_data)

        print()
        print("📊 إحصائيات البيانات النظيفة:")
        print(f"• عدد الجامعات: {stats['total_universities']}")
        print(f"• عدد المعاهد: {stats['total_institutes']}")
        print(f"• إجمالي المؤسسات: {stats['total_institutions']}")
        print(f"• عدد المواقع الفريدة: {stats['unique_locations']}")

        if stats['locations_list']:
            print("• المواقع:")
            for loc in stats['locations_list'][:5]:  # أول 5 مواقع
                print(f"  - {loc}")
            if len(stats['locations_list']) > 5:
                print(f"  ... و {len(stats['locations_list']) - 5} مواقع أخرى")

        print()
        print("✅ تم تنظيف البيانات بنجاح!")

        return clean_data, stats

def main():
    cleaner = MyUniFeaturesDataCleaner()
    clean_data, stats = cleaner.clean_all()

if __name__ == "__main__":
    main()