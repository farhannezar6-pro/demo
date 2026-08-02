"""
statistics_report.py — إحصائيات بيانات UniGuiders
=====================================
إنشاء تقرير إحصائي شامل للبيانات قبل وبعد التنظيف
"""

import json
import sqlite3

def main():
    print('=== إحصائيات بيانات UniGuiders ===')
    print()

    # البيانات الأولية (قبل التنظيف)
    print('📊 البيانات الأولية (قبل التنظيف):')
    try:
        conn = sqlite3.connect('e:/جلب بيانات/scraper_project/data/uniguiders/uniguiders.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM universities')
        uni_count_raw = cursor.fetchone()[0]
        print(f'• عدد الجامعات: {uni_count_raw}')

        conn2 = sqlite3.connect('e:/جلب بيانات/scraper_project/data/uniguiders_specialties/specialties.db')
        cursor2 = conn2.cursor()
        cursor2.execute('SELECT COUNT(*) FROM specialties')
        spec_count_raw = cursor2.fetchone()[0]
        print(f'• عدد التخصصات: {spec_count_raw}')

        # متوسط التخصصات لكل جامعة
        cursor2.execute('SELECT university_name, COUNT(*) as count FROM specialties GROUP BY university_name ORDER BY count DESC LIMIT 5')
        top_unis = cursor2.fetchall()
        print('• أكثر الجامعات تخصصات:')
        for uni, count in top_unis:
            print(f'  - {uni[:40]}...: {count} تخصص')

        conn.close()
        conn2.close()
    except Exception as e:
        print(f'خطأ في قراءة البيانات الأولية: {e}')

    print()

    # البيانات بعد التنظيف
    print('🧹 البيانات بعد التنظيف:')
    try:
        with open('e:/جلب بيانات/scraper_project/data/cleaned/uniguiders_clean_data.json', 'r', encoding='utf-8') as f:
            clean_data = json.load(f)

        uni_count_clean = clean_data['metadata']['total_universities']
        spec_count_clean = clean_data['metadata']['total_specialties']

        print(f'• عدد الجامعات: {uni_count_clean}')
        print(f'• عدد التخصصات: {spec_count_clean}')

        # متوسط التخصصات لكل جامعة
        uni_specialties = [(uni['name'], len(uni['specialties'])) for uni in clean_data['universities']]
        uni_specialties.sort(key=lambda x: x[1], reverse=True)

        print('• أكثر الجامعات تخصصات:')
        for name, count in uni_specialties[:5]:
            print(f'  - {name[:40]}...: {count} تخصص')

        # إحصائيات الأسعار
        prices = []
        for uni in clean_data['universities']:
            for spec in uni['specialties']:
                if spec.get('price_myr'):
                    prices.append(spec['price_myr'])

        if prices:
            print('• إحصائيات الأسعار (MYR):')
            print(f'  - الحد الأدنى: {min(prices):,} رينغيت')
            print(f'  - الحد الأقصى: {max(prices):,} رينغيت')
            print(f'  - المتوسط: {sum(prices)//len(prices):,} رينغيت')

    except Exception as e:
        print(f'خطأ في قراءة البيانات النظيفة: {e}')

    print()

    # المقارنة
    print('⚖️ المقارنة:')
    try:
        uni_diff = uni_count_raw - uni_count_clean
        spec_diff = spec_count_raw - spec_count_clean

        print(f'• الجامعات المحذوفة: {uni_diff} (ربما جامعات بدون تخصصات)')
        print(f'• التخصصات المحذوفة: {spec_diff} (ربما تكرارات أو بيانات فارغة)')
        print(f'• معدل التخصصات لكل جامعة: {spec_count_clean/uni_count_clean:.1f}')

    except:
        print('لا يمكن حساب المقارنة - بيانات غير متوفرة')

    print()

    # البيانات النهائية لـ ANLASH
    print('🎯 البيانات النهائية (ANLASH Ready):')
    try:
        with open('e:/جلب بيانات/scraper_project/data/cleaned/anlash_ready_data_uniguiders.json', 'r', encoding='utf-8') as f:
            anlash_data = json.load(f)

        stats = anlash_data['_metadata']['statistics']
        print('• الجامعات:', stats['total_universities'])
        print('• البرامج:', stats['total_programs'])
        print('• المدن:', stats['total_cities'])
        print('• العملات:', stats['total_currencies'])
        print('• تاريخ الإنشاء:', anlash_data['_metadata']['generated_at'][:10])

    except Exception as e:
        print(f'خطأ في قراءة ملف ANLASH: {e}')

if __name__ == "__main__":
    main()