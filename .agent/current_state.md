# 📋 Current Project State

## Last Updated: 2026-04-19

## ✅ Completed

### Core Scraping Infrastructure
- Main spider supporting both `list` mode (tables/cards) and `sections` mode (heading-based pages)
- Playwright integration with human-like simulation (scroll, mouse, random delays)
- 3-stage data pipeline: deduplication → cleaning → triple export (CSV, JSON, SQLite)
- Stealth middleware stack to bypass bot-detection systems
- Visible browser mode enabled (`headless: False`) at core level

### Standalone Extractors & Recent Work
- `scrape_ar_universities.py` — successfully built for universities and internal course tables using Playwright persistent context.
- `scrape_uniguiders.py` + `scrape_uniguiders_specialties.py` — extracted 72 raw university records, cleaned to 14 universities, and produced 1,427 program records.
- `scrape_myunifeatures.py` — extracted 14 universities and 12 language institutes from MyUniFeatures.
- `clean_myunifeatures_data.py` — cleaned MyUniFeatures data and normalized it for export.
- `create_myunifeatures_anlash_ready.py` — generated `anlash_ready_data_myunifeatures.json` with placeholder programs for incomplete site data.

### Output Files
- `data/cleaned/anlash_ready_data_uniguiders.json` — جاهز لـ ANLASH بنية كاملة
- `data/cleaned/anlash_ready_data_myunifeatures.json` — جاهز لـ ANLASH بيانات أساسية
- `data/cleaned/uniguiders_clean_data.json`
- `data/cleaned/myunifeatures_clean_data.json`

### Additional Scripts
- `run_specialties.py` — runs the URL-list spider through the full pipeline
- `process_courses.py` — post-processing script that splits compound text fields (prices, durations, intakes) into separate structured columns
- `myunifeatures_statistics_report.py` — reports MyUniFeatures extraction results and file summary

### Data Quality
- All CSV exports use `utf-8-sig` encoding for Excel compatibility with Arabic
- Data cleaned via `CleaningPipeline`: HTML tags removed, Unicode normalized, whitespace collapsed

## 🔮 Suggested Next Steps
- Clean up extracted UniGuiders data وتأكيد برامج MyUniFeatures الحقيقية
- الحصول على قوائم برامج ورسوم كاملة من MyUniFeatures عبر التواصل
- دمج الملفات النهائية في قاعدة بيانات ANLASH أو تطبيق العميل
