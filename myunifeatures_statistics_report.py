#!/usr/bin/env python3
"""
إحصائيات سريعة لبيانات MyUniFeatures
"""

import json
import os

def generate_myunifeatures_statistics():
    """توليد إحصائيات سريعة"""

    # تحميل البيانات الأولية
    raw_data_path = "data/myunifeatures/universities.json"
    institutes_path = "data/myunifeatures/institutes.json"

    # تحميل البيانات النظيفة
    clean_data_path = "data/cleaned/myunifeatures_clean_data.json"

    # تحميل بيانات ANLASH
    anlash_data_path = "data/cleaned/anlash_ready_data_myunifeatures.json"

    print("📊 إحصائيات بيانات MyUniFeatures")
    print()

    try:
        # البيانات الأولية
        with open(raw_data_path, 'r', encoding='utf-8') as f:
            universities = json.load(f)

        with open(institutes_path, 'r', encoding='utf-8') as f:
            institutes = json.load(f)

        print("📊 البيانات الأولية (قبل التنظيف):")
        print(f"• عدد الجامعات: {len(universities)}")
        print(f"• عدد المعاهد: {len(institutes)}")
        print(f"• المجموع: {len(universities) + len(institutes)}")

        # أسماء الجامعات الأولى
        if universities:
            print("• أمثلة على الجامعات:")
            for i, uni in enumerate(universities[:3]):
                print(f"  - {uni['name']}")

        if institutes:
            print("• أمثلة على المعاهد:")
            for i, inst in enumerate(institutes[:3]):
                print(f"  - {inst['name']}")

        print()

        # البيانات النظيفة
        with open(clean_data_path, 'r', encoding='utf-8') as f:
            clean_data = json.load(f)

        print("🧹 البيانات بعد التنظيف:")
        print(f"• عدد الجامعات: {len(clean_data['universities'])}")
        print(f"• عدد المعاهد: {len(clean_data['institutes'])}")
        print(f"• المجموع: {len(clean_data['universities']) + len(clean_data['institutes'])}")

        print()

        # بيانات ANLASH
        with open(anlash_data_path, 'r', encoding='utf-8') as f:
            anlash_data = json.load(f)

        print("🎯 البيانات النهائية (ANLASH Ready):")
        stats = anlash_data["_metadata"]["statistics"]
        print(f"• الجامعات: {stats['total_universities']}")
        print(f"• المعاهد: {stats['total_institutes']}")
        print(f"• إجمالي المؤسسات: {stats['total_institutions']}")
        print(f"• البرامج: {stats['total_programs']}")
        print(f"• الدول: {stats['total_countries']}")
        print(f"• المدن: {stats['total_cities']}")
        print(f"• العملات: {stats['total_currencies']}")

        print()
        print("📁 الملفات المتاحة:")
        files = [
            "data/myunifeatures/universities.json",
            "data/myunifeatures/institutes.json",
            "data/cleaned/myunifeatures_clean_data.json",
            "data/cleaned/anlash_ready_data_myunifeatures.json"
        ]

        for file_path in files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"• {file_path} ({size} bytes)")

        print()
        print("✅ الاستخراج مكتمل بنجاح!")
        print("📌 الملف النهائي: anlash_ready_data_myunifeatures.json")

    except FileNotFoundError as e:
        print(f"❌ ملف مفقود: {e}")
    except Exception as e:
        print(f"❌ خطأ: {e}")

if __name__ == "__main__":
    generate_myunifeatures_statistics()