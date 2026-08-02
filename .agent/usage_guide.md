# 📖 Usage Guide

## Running the Main Scraper
Configure your target in `config.yaml`, then run:
```powershell
.\venv\Scripts\python.exe main.py
```

## Scraping a Custom List of URLs
Add your URLs to `menu_links.json` (one per line, format: `Name: https://url`), then run:
```powershell
.\venv\Scripts\python.exe run_specialties.py
```

## MyUniFeatures Extraction Workflow
To extract MyUniFeatures listings:
```powershell
.\venv\Scripts\python.exe scrape_myunifeatures.py
.\venv\Scripts\python.exe clean_myunifeatures_data.py
.\venv\Scripts\python.exe create_myunifeatures_anlash_ready.py
.\venv\Scripts\python.exe myunifeatures_statistics_report.py
```

## Cleaning & Structuring Raw Data
After scraping, split compound text fields into clean columns:
```powershell
.\venv\Scripts\python.exe process_courses.py
```

## Output Location
All extracted files are saved to `data/<project>/<folder>/` as defined in `config.yaml`:
- `output.csv`  → Excel-compatible (UTF-8 BOM)
- `output.json` → API-ready
- `output.db`   → SQLite database

## Live Browser Monitoring
The browser window is visible by default during scraping.
To run silently (headless), set `"headless": True` in `scraper/settings.py`.

## Notes
- `anlash_ready_data_uniguiders.json` جاهز للاستخدام مع بيانات كاملة.
- `anlash_ready_data_myunifeatures.json` يحتوي بيانات أساسية وبرامج placeholder حتى تُجمع التفاصيل الكاملة.