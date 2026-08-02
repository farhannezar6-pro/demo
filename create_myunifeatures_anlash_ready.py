#!/usr/bin/env python3
"""
تحويل بيانات MyUniFeatures إلى هيكل ANLASH جاهز
"""

import json
import os
from datetime import datetime

class MyUniFeaturesToAnlashConverter:
    def __init__(self):
        self.cleaned_data_path = "data/cleaned/myunifeatures_clean_data.json"
        self.output_path = "data/cleaned/anlash_ready_data_myunifeatures.json"

    def load_clean_data(self):
        """تحميل البيانات النظيفة"""
        with open(self.cleaned_data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def create_currencies(self):
        """إنشاء جدول العملات"""
        return [
            {
                "Id": 1,
                "Code": "USD",
                "Name": "US Dollar",
                "NameAr": "دولار أمريكي",
                "Symbol": "$",
                "ExchangeRate": 1.0,
                "IsActive": True
            },
            {
                "Id": 2,
                "Code": "MYR",
                "Name": "Malaysian Ringgit",
                "NameAr": "رينغيت ماليزي",
                "Symbol": "RM",
                "ExchangeRate": 4.47,
                "IsActive": True
            }
        ]

    def create_countries(self):
        """إنشاء جدول الدول"""
        return [
            {
                "Id": 1,
                "Name": "Malaysia",
                "NameAr": "ماليزيا",
                "Code": "MY",
                "PhoneCode": "+60",
                "IsActive": True
            }
        ]

    def create_cities(self, universities, institutes):
        """إنشاء جدول المدن"""
        cities = []
        city_id = 1
        city_names = set()

        # جمع جميع المدن من الجامعات والمعاهد
        for uni in universities:
            if uni["location"] and uni["location"] not in city_names:
                city_names.add(uni["location"])
                cities.append({
                    "Id": city_id,
                    "Name": uni["location"],
                    "NameAr": uni["location"],  # نفس الاسم بالعربية
                    "CountryId": 1,  # ماليزيا
                    "IsActive": True
                })
                city_id += 1

        for inst in institutes:
            if inst["location"] and inst["location"] not in city_names:
                city_names.add(inst["location"])
                cities.append({
                    "Id": city_id,
                    "Name": inst["location"],
                    "NameAr": inst["location"],  # نفس الاسم بالعربية
                    "CountryId": 1,  # ماليزيا
                    "IsActive": True
                })
                city_id += 1

        # إذا لم نجد مدن، نضيف كوالالمبور كمدينة افتراضية
        if not cities:
            cities.append({
                "Id": 1,
                "Name": "Kuala Lumpur",
                "NameAr": "كوالالمبور",
                "CountryId": 1,
                "IsActive": True
            })

        return cities

    def create_universities(self, universities, cities):
        """إنشاء جدول الجامعات"""
        anlash_universities = []
        uni_id = 1

        # إنشاء خريطة للمدن
        city_map = {city["Name"]: city["Id"] for city in cities}

        for uni in universities:
            # تحديد CityId
            city_id = city_map.get(uni["location"], 1)  # افتراضياً كوالالمبور

            anlash_uni = {
                "Id": uni_id,
                "Name": uni["name"],
                "NameAr": uni["name"],  # نفس الاسم بالعربية
                "Description": uni["description"],
                "DescriptionAr": uni["description"],
                "CityId": city_id,
                "Address": uni["location"],
                "Website": "https://myunifeatures.com/",
                "Phone": "",
                "Email": "info@myuni-features.com",
                "EstablishedYear": None,
                "Type": "Private",
                "Ranking": None,
                "IsActive": True,
                "TenantId": None
            }
            anlash_universities.append(anlash_uni)
            uni_id += 1

        return anlash_universities

    def create_institutes(self, institutes, cities, universities):
        """تحويل المعاهد إلى جامعات في ANLASH"""
        anlash_institutes = []
        inst_id = len(universities) + 1

        # إنشاء خريطة للمدن
        city_map = {city["Name"]: city["Id"] for city in cities}

        for inst in institutes:
            # تحديد CityId
            city_id = city_map.get(inst["location"], 1)  # افتراضياً كوالالمبور

            anlash_inst = {
                "Id": inst_id,
                "Name": inst["name"],
                "NameAr": inst["name"],  # نفس الاسم بالعربية
                "Description": inst["description"],
                "DescriptionAr": inst["description"],
                "CityId": city_id,
                "Address": inst["location"],
                "Website": "https://myunifeatures.com/",
                "Phone": "",
                "Email": "info@myuni-features.com",
                "EstablishedYear": None,
                "Type": "Language Institute",
                "Ranking": None,
                "IsActive": True,
                "TenantId": None
            }
            anlash_institutes.append(anlash_inst)
            inst_id += 1

        return anlash_institutes

    def create_programs_placeholder(self, universities, institutes):
        """إنشاء برامج placeholder (بما أن MyUniFeatures لا تحتوي على تفاصيل البرامج)"""
        programs = []
        program_id = 1

        # لكل جامعة، إنشاء برنامج placeholder
        for i, uni in enumerate(universities):
            program = {
                "Id": program_id,
                "UniversityId": uni["Id"],
                "Name": f"برامج {uni['Name']}",
                "NameAr": f"Programs at {uni['Name']}",
                "Description": "معلومات البرامج متاحة عبر التواصل مع MyUniFeatures",
                "DescriptionAr": "Program information available through MyUniFeatures contact",
                "Degree": "Bachelor",
                "Duration": "3-4 years",
                "Language": "English",
                "TuitionFee": None,
                "CurrencyId": 2,  # MYR
                "IntakeMonths": "January,April,September",
                "Requirements": "معلومات متاحة عبر التواصل",
                "IsActive": True,
                "TenantId": None
            }
            programs.append(program)
            program_id += 1

        # لكل معهد، إنشاء برنامج placeholder
        for i, inst in enumerate(institutes):
            program = {
                "Id": program_id,
                "UniversityId": inst["Id"],
                "Name": f"دورات {inst['Name']}",
                "NameAr": f"Courses at {inst['Name']}",
                "Description": "دورات اللغة الإنجليزية وبرامج التحضير",
                "DescriptionAr": "English language courses and preparation programs",
                "Degree": "Language Course",
                "Duration": "1-12 months",
                "Language": "English",
                "TuitionFee": None,
                "CurrencyId": 2,  # MYR
                "IntakeMonths": "Monthly",
                "Requirements": "مستوى أساسي في اللغة الإنجليزية",
                "IsActive": True,
                "TenantId": None
            }
            programs.append(program)
            program_id += 1

        return programs

    def create_metadata(self, stats):
        """إنشاء metadata"""
        return {
            "generated_at": datetime.now().isoformat(),
            "generator": "MyUniFeatures to ANLASH Converter v1.0",
            "description": "بيانات MyUniFeatures جاهزة لحقنها في قاعدة بيانات ANLASH",
            "notes": [
                "يجب إدراج الجداول بالترتيب: Currencies → Countries → Cities → Universities → Programs",
                "حقل UniversityId في Programs هو ID الفعلي للجامعة",
                "TenantId = null يعني بيانات Host مشتركة (IMayHaveTenant)",
                "البيانات الأساسية فقط - لا تحتوي على تفاصيل الأسعار والبرامج الكاملة",
                "للحصول على التفاصيل الكاملة، يرجى التواصل مع MyUniFeatures"
            ],
            "insert_order": [
                f"1. Currencies ({len(self.create_currencies())} records)",
                f"2. Countries ({len(self.create_countries())} records)",
                f"3. Cities ({len(stats.get('cities', []))} records)",
                f"4. Universities ({stats.get('total_universities', 0) + stats.get('total_institutes', 0)} records)",
                f"5. UniversityPrograms ({stats.get('total_programs', 0)} records)"
            ],
            "statistics": {
                "total_universities": stats.get("total_universities", 0),
                "total_institutes": stats.get("total_institutes", 0),
                "total_institutions": stats.get("total_institutions", 0),
                "total_programs": stats.get("total_programs", 0),
                "total_countries": 1,
                "total_cities": len(stats.get("cities", [])),
                "total_currencies": 2,
                "source": "MyUniFeatures.com",
                "extraction_date": datetime.now().isoformat(),
                "note": "بيانات أساسية - تحتاج إلى تفاصيل إضافية من المكتب"
            }
        }

    def convert(self):
        """تحويل البيانات إلى هيكل ANLASH"""
        print("🔄 بدء تحويل بيانات MyUniFeatures إلى ANLASH...")
        print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # تحميل البيانات النظيفة
        clean_data = self.load_clean_data()

        # إنشاء الجداول
        currencies = self.create_currencies()
        countries = self.create_countries()
        cities = self.create_cities(clean_data["universities"], clean_data["institutes"])
        universities = self.create_universities(clean_data["universities"], cities)
        institutes = self.create_institutes(clean_data["institutes"], cities, universities)

        # دمج الجامعات والمعاهد
        all_institutions = universities + institutes

        # إنشاء البرامج
        programs = self.create_programs_placeholder(universities, institutes)

        # إنشاء الإحصائيات
        stats = {
            "total_universities": len(universities),
            "total_institutes": len(institutes),
            "total_institutions": len(all_institutions),
            "total_programs": len(programs),
            "cities": cities
        }

        # إنشاء metadata
        metadata = self.create_metadata(stats)

        # تجميع البيانات النهائية
        anlash_data = {
            "_metadata": metadata,
            "currencies": currencies,
            "countries": countries,
            "cities": cities,
            "universities": all_institutions,
            "programs": programs
        }

        # حفظ البيانات
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(anlash_data, f, ensure_ascii=False, indent=2)

        print(f"✅ تم حفظ البيانات الجاهزة لـ ANLASH في: {self.output_path}")
        print()
        print("📊 إحصائيات البيانات المحولة:")
        print(f"• العملات: {len(currencies)}")
        print(f"• الدول: {len(countries)}")
        print(f"• المدن: {len(cities)}")
        print(f"• الجامعات: {len(universities)}")
        print(f"• المعاهد: {len(institutes)}")
        print(f"• إجمالي المؤسسات: {len(all_institutions)}")
        print(f"• البرامج: {len(programs)}")

        print()
        print("⚠️  ملاحظة مهمة:")
        print("هذه البيانات الأساسية فقط. للحصول على:")
        print("- تفاصيل البرامج والتخصصات")
        print("- الأسعار والرسوم")
        print("- متطلبات القبول")
        print("يرجى التواصل مع MyUniFeatures عبر:")
        print("📧 info@myuni-features.com")
        print("📱 WhatsApp: +60 14 799 2210")
        print("🌐 https://myunifeatures.com/")

        return anlash_data

def main():
    converter = MyUniFeaturesToAnlashConverter()
    anlash_data = converter.convert()

if __name__ == "__main__":
    main()