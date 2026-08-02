# 🧠 Project Memory

## Project Goal
A professional web data scraper built on **Scrapy + Playwright** & Standalone **Playwright**, capable of:
- Extracting structured data from any website by simply editing `config.yaml`
- Bypassing modern bot-protection systems (Cloudflare, SG-Captcha, etc.) using persistent contexts and native Chrome channels.
- Automatically exporting data in three formats: CSV, JSON, and SQLite
- Simulating real human browser behavior (scrolling, mouse movement, random delays)

## Architecture Overview

```
main.py                  ← Main entry point (Scrapy CrawlerProcess)
config.yaml              ← All scraping, extraction, and export settings

scraper/
├── spiders/
│   ├── main_spider.py           ← General-purpose spider (list & sections modes)
│   └── ar_specialties_spider.py ← Spider for scraping a list of URLs from menu_links.json
├── pipelines/data_pipeline.py   ← 3-stage pipeline: dedup → clean → export
├── middlewares/                 ← StealthMiddleware + PlaywrightMiddleware
└── settings.py                  ← Scrapy settings and browser configuration

Standalone Scripts:
- scrape_ar_universities.py                ← Extract universities and courses via Playwright persistent context
- scrape_easyuni.py                        ← 3-level crawler for EasyUni Malaysia
- scrape_uniguiders.py                     ← University extraction from UniGuiders
- scrape_uniguiders_specialties.py         ← Specialty extraction from UniGuiders
- scrape_myunifeatures.py                  ← University/institute extraction from MyUniFeatures
- clean_myunifeatures_data.py              ← Clean MyUniFeatures raw results
- create_myunifeatures_anlash_ready.py     ← Create ANLASH-ready JSON for MyUniFeatures
- run_specialties.py                       ← Run URL-list spider through full pipeline
- process_courses.py                       ← Split compound fields into structured columns
- myunifeatures_statistics_report.py       ← Generate summary report for MyUniFeatures data
```

## Key Technical Notes
- **`headless` mode:** MUST be `False` for sites with strong Cloudflare protection.
- **Anti-Bot Override:** When standard Scrapy+Playwright gets a 403 Forbidden, use `launch_persistent_context(..., channel="chrome", headless=False)` in a standalone script (e.g., `scrape_ar_universities.py`) to bypass Cloudflare completely by leveraging the local Chrome's fingerprint and session storage.
- **MyUniFeatures note:** This site only provides basic university/institute listings, so the converter generates placeholder programs until full pricing/program details are obtained.
- **ANLASH readiness:** `anlash_ready_data_uniguiders.json` is complete; `anlash_ready_data_myunifeatures.json` contains basic placeholder program entries.
- **CSV encoding:** Always exported as `utf-8-sig` for full Excel compatibility with Arabic characters.
- **Python environment:** Always run scripts via `.\venv\Scripts\python.exe`, not the global `python`
