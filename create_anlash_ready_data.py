"""
create_anlash_ready_data.py — إنشاء ملف ANLASH جاهز من بيانات UniGuiders
=======================================================================
تحويل بيانات UniGuiders المستخرجة إلى هيكل ANLASH الجاهز للحقن في قاعدة البيانات
"""

import json
import pathlib
from datetime import datetime


# ============================================================
#  Configuration
# ============================================================

INPUT_FILE = pathlib.Path("e:/جلب بيانات/scraper_project/data/cleaned/uniguiders_clean_data.json")
OUTPUT_FILE = pathlib.Path("e:/جلب بيانات/scraper_project/data/cleaned/anlash_ready_data_uniguiders.json")


# ============================================================
#  ANLASH Data Templates
# ============================================================

def get_currencies():
    """العملات المطلوبة لـ ANLASH"""
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


def get_countries():
    """الدول المطلوبة"""
    return [
        {
            "Id": 1,
            "Code": "MY",
            "Name": "Malaysia",
            "NameAr": "ماليزيا",
            "IsActive": True
        }
    ]


def get_cities():
    """المدن المطلوبة - استخراج من بيانات UniGuiders"""
    cities = [
        {"name": "Kuala Lumpur", "name_ar": "كوالالمبور"},
        {"name": "Cyberjaya", "name_ar": "سايبرجايا"},
        {"name": "Petaling Jaya", "name_ar": "بيتالينغ جايا"},
        {"name": "Shah Alam", "name_ar": "شاه علم"},
        {"name": "Subang Jaya", "name_ar": "سوبانغ جايا"},
        {"name": "Nilai", "name_ar": "نيلاي"},
        {"name": "Johor Bahru", "name_ar": "جوهور بارو"},
        {"name": "Penang", "name_ar": "بينانغ"},
        {"name": "Ipoh", "name_ar": "إيبوه"},
        {"name": "Kuching", "name_ar": "كوتشينغ"},
        {"name": "Kota Kinabalu", "name_ar": "كوتا كينابالو"},
        {"name": "Malacca", "name_ar": "ملقا"},
        {"name": "Kampar", "name_ar": "كامبار"},
        {"name": "Sungai Long", "name_ar": "سونغاي لونغ"}
    ]

    return [
        {
            "Id": i + 1,
            "CountryId": 1,
            "Name": city["name"],
            "NameAr": city["name_ar"],
            "IsActive": True,
            "Slug": city["name"].lower().replace(" ", "-")
        }
        for i, city in enumerate(cities)
    ]


def extract_city_from_name(university_name):
    """استخراج اسم المدينة من اسم الجامعة"""
    city_keywords = {
        "Kuala Lumpur": ["kuala lumpur", "kl"],
        "Cyberjaya": ["cyberjaya"],
        "Petaling Jaya": ["petaling jaya"],
        "Shah Alam": ["shah alam"],
        "Subang Jaya": ["subang jaya", "subang"],
        "Nilai": ["nilai"],
        "Johor Bahru": ["johor bahru", "johor"],
        "Penang": ["penang"],
        "Ipoh": ["ipoh"],
        "Kuching": ["kuching"],
        "Kota Kinabalu": ["kota kinabalu"],
        "Malacca": ["malacca", "melaka"],
        "Kampar": ["kampar"],
        "Sungai Long": ["sungai long"]
    }

    university_lower = university_name.lower()
    for city_name, keywords in city_keywords.items():
        for keyword in keywords:
            if keyword in university_lower:
                return city_name
    return "Kuala Lumpur"  # Default


def get_city_id(city_name):
    """الحصول على ID المدينة"""
    city_map = {
        "Kuala Lumpur": 1,
        "Cyberjaya": 2,
        "Petaling Jaya": 3,
        "Shah Alam": 4,
        "Subang Jaya": 5,
        "Nilai": 6,
        "Johor Bahru": 7,
        "Penang": 8,
        "Ipoh": 9,
        "Kuching": 10,
        "Kota Kinabalu": 11,
        "Malacca": 12,
        "Kampar": 13,
        "Sungai Long": 14
    }
    return city_map.get(city_name, 1)  # Default to Kuala Lumpur


def clean_university_name(name):
    """تنظيف اسم الجامعة لـ ANLASH"""
    # إزالة العناوين والأرقام
    name = name.replace(" No.", "").strip()
    name = name.replace(" No.", "").strip()
    return name


def create_university_record(uni_data, uni_id):
    """إنشاء سجل جامعة لـ ANLASH"""
    city_name = extract_city_from_name(uni_data["name"])
    city_id = get_city_id(city_name)

    return {
        "Name": clean_university_name(uni_data["name"]),
        "NameAr": f"[بانتظار الترجمة] {clean_university_name(uni_data['name'])}",
        "Description": "",
        "DescriptionAr": "",
        "AboutText": "",
        "AboutTextAr": "",
        "CountryId": 1,
        "CityId": city_id,
        "CountryName": "Malaysia",
        "CityName": city_name,
        "Type": 2,  # Private University
        "WebsiteUrl": uni_data["link"],
        "Email": "",
        "Phone": "",
        "Rating": 0,
        "RatingCount": 0,
        "WorldRanking": None,
        "EstablishmentYear": None,
        "AcceptanceRate": None,
        "InternationalStudentPercent": None,
        "TuitionFeeRange": "",
        "TuitionFeeRangeAr": "",
        "EmploymentRate": None,
        "TotalStudents": None,
        "AccreditationBodies": "",
        "CitationSource": json.dumps({
            "source": "UniGuiders.com",
            "date": "2026-04"
        }),
        "LogoUrl": "",
        "Slug": clean_university_name(uni_data["name"]).lower().replace(" ", "-").replace("'", ""),
        "SlugAr": clean_university_name(uni_data["name"]).replace(" ", "-").replace("'", ""),
        "MetaDescription": f"Study at {clean_university_name(uni_data['name'])} in Malaysia.",
        "MetaDescriptionAr": f"ادرس في [بانتظار الترجمة] {clean_university_name(uni_data['name'])}.",
        "OfferLetterFee": None,
        "IntakeMonths": "1,7",  # January and July
        "IsActive": True,
        "IsFeatured": False,
        "DisplayOrder": uni_id,
        "TenantId": None,
        "Programs": []
    }


def create_program_record(spec_data, program_id):
    """إنشاء سجل برنامج لـ ANLASH"""
    # تحديد المستوى بناءً على اسم البرنامج
    level = 3  # Bachelor by default
    if "Master" in spec_data["name"].upper() or "MSC" in spec_data["name"].upper():
        level = 4  # Master
    elif "PhD" in spec_data["name"].upper() or "DOCTOR" in spec_data["name"].upper():
        level = 5  # PhD
    elif "Foundation" in spec_data["name"] or "Diploma" in spec_data["name"]:
        level = 1  # Foundation/Diploma

    # تحديد المدة الزمنية
    duration_years = 3  # Default for Bachelor
    if level == 4:  # Master
        duration_years = 1
    elif level == 5:  # PhD
        duration_years = 3
    elif level == 1:  # Foundation
        duration_years = 1

    return {
        "UniversityId": "__PLACEHOLDER__",
        "Name": spec_data["name"],
        "NameAr": f"[بانتظار الترجمة] {spec_data['name']}",
        "Description": f"{clean_university_name(spec_data.get('university_name', ''))} Malaysia",
        "DescriptionAr": "",
        "Level": level,
        "Mode": 1,  # Full-time
        "Field": "",
        "FieldAr": "",
        "DurationYears": duration_years,
        "DurationSemesters": None,
        "DurationMonths": None,
        "TotalCredits": None,
        "TuitionFee": spec_data.get("price_myr", 0) if spec_data.get("price_myr") else None,
        "CurrencyId": 2,  # MYR
        "FeeType": "Total" if spec_data.get("price_myr") else "",
        "ApplicationFee": None,
        "ApplicationDeadline": None,
        "Requirements": "",
        "RequirementsAr": "",
        "IsActive": True,
        "IsFeatured": False,
        "DisplayOrder": program_id,
        "Slug": spec_data["name"].lower().replace(" ", "-").replace("(", "").replace(")", "").replace(",", ""),
        "SlugAr": spec_data["name"].replace(" ", "-").replace("(", "").replace(")", "").replace(",", "")
    }


# ============================================================
#  Main Processing
# ============================================================

def main():
    print("بدء إنشاء ملف ANLASH الجاهز...")

    # قراءة البيانات المستخرجة
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"تم تحميل {data['metadata']['total_universities']} جامعة و {data['metadata']['total_specialties']} تخصص")

    # إنشاء هيكل ANLASH
    anlash_data = {
        "_metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator": "UniGuiders to ANLASH Converter v1.0",
            "description": "بيانات UniGuiders جاهزة لحقنها في قاعدة بيانات ANLASH",
            "notes": [
                "يجب إدراج الجداول بالترتيب: Currencies → Countries → Cities → Universities → Programs",
                "حقل UniversityId في Programs هو '__PLACEHOLDER__' — يجب استبداله بالـ ID الفعلي بعد إدراج الجامعة",
                "حقل _university_index يشير إلى ترتيب الجامعة في مصفوفة universities (1-indexed)",
                "TenantId = null يعني بيانات Host مشتركة (IMayHaveTenant)",
                "جميع الحقول ThreeDimensional اللغة إلزامية — القيم المفقودة معبأة بـ [بانتظار الترجمة]"
            ],
            "insert_order": [
                "1. Currencies (2 records)",
                "2. Countries (1 records)",
                "3. Cities (14 records)",
                "4. Universities (14 records)",
                "5. UniversityPrograms (1427 records)"
            ],
            "statistics": {
                "total_universities": data['metadata']['total_universities'],
                "total_programs": data['metadata']['total_specialties'],
                "total_countries": 1,
                "total_cities": 14,
                "total_currencies": 2,
                "source": "UniGuiders.com",
                "extraction_date": data['metadata']['extraction_date']
            }
        },
        "currencies": get_currencies(),
        "countries": get_countries(),
        "cities": get_cities(),
        "universities": []
    }

    # معالجة الجامعات والبرامج
    program_counter = 1
    for uni_index, uni in enumerate(data['universities'], 1):
        university_record = create_university_record(uni, uni_index)
        university_record["_university_index"] = uni_index

        # إضافة البرامج
        for spec in uni['specialties']:
            program_record = create_program_record(spec, program_counter)
            university_record["Programs"].append(program_record)
            program_counter += 1

        anlash_data["universities"].append(university_record)

    # حفظ الملف
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(anlash_data, f, ensure_ascii=False, indent=2)

    print("تم إنشاء ملف ANLASH الجاهز بنجاح!")
    print(f"الموقع: {OUTPUT_FILE}")
    print(f"الجامعات: {len(anlash_data['universities'])}")
    print(f"إجمالي البرامج: {sum(len(uni['Programs']) for uni in anlash_data['universities'])}")


if __name__ == "__main__":
    main()