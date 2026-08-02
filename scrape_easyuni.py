"""
scrape_easyuni.py — EasyUni Malaysia Professional Scraper
=========================================================
Standalone Playwright script for a 3-level crawl:
  Level 1: Listing page → extract university cards
  Level 2: University page → extract overview details
  Level 3: Courses tab → extract course rows → visit each course page

Output: CSV (utf-8-sig) + JSON + SQLite in data/easyuni/
Run:    .\\venv\\Scripts\\python.exe scrape_easyuni.py
"""

import csv
import json
import re
import sqlite3
import time
import random
import pathlib
from datetime import datetime
from playwright.sync_api import sync_playwright


# ============================================================
#  Configuration
# ============================================================

BASE_URL = "https://www.easyuni.com"
LISTING_URL = f"{BASE_URL}/malaysia/all/all/all-levels/"

OUTPUT_DIR = pathlib.Path("e:/جلب بيانات/scraper_project/data/easyuni")
UNIVERSITIES_CSV = OUTPUT_DIR / "universities.csv"
COURSES_CSV = OUTPUT_DIR / "courses.csv"
UNIVERSITIES_JSON = OUTPUT_DIR / "universities.json"
COURSES_JSON = OUTPUT_DIR / "courses.json"
DB_PATH = OUTPUT_DIR / "easyuni.db"

PROFILE_DIR = "e:/جلب بيانات/scraper_project/playwright_profile_easyuni"

# Delays (seconds)
MIN_DELAY = 2
MAX_DELAY = 5

# Max retries per page
MAX_RETRIES = 3


# ============================================================
#  Cleaning Helpers
# ============================================================

def clean_text(text: str) -> str:
    """Strip HTML artifacts, collapse whitespace, normalize."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)           # remove HTML tags
    text = re.sub(r"\s+", " ", text).strip()       # collapse whitespace
    return text


def clean_fee(text: str) -> int | None:
    """Extract numeric fee value: '$ 18,985' → 18985."""
    if not text:
        return None
    nums = re.findall(r"[\d,]+", text.replace(" ", ""))
    if nums:
        try:
            return int(nums[0].replace(",", ""))
        except ValueError:
            return None
    return None


def clean_duration_years(raw: str) -> float | None:
    """Convert duration string to years: '27 months' → 2.25."""
    if not raw:
        return None
    raw_lower = raw.lower().strip()

    # Match patterns like '3 years', '2.5 years', '1 year'
    m = re.search(r"([\d.]+)\s*year", raw_lower)
    if m:
        return float(m.group(1))

    # Match patterns like '27 months', '18 months'
    m = re.search(r"([\d.]+)\s*month", raw_lower)
    if m:
        return round(float(m.group(1)) / 12, 2)

    # Match patterns like '12 weeks'
    m = re.search(r"([\d.]+)\s*week", raw_lower)
    if m:
        return round(float(m.group(1)) / 52, 2)

    return None


def extract_id_from_url(url: str) -> int | None:
    """Extract numeric ID from URL slug: '.../apu-8/' → 8."""
    m = re.search(r"-(\d+)/?$", url.rstrip("/"))
    if m:
        return int(m.group(1))
    return None


def extract_slug_from_url(url: str, base="/malaysia/") -> str:
    """Extract slug from URL path."""
    path = url.split(base)[-1] if base in url else url
    return path.strip("/")


def human_delay(min_s=MIN_DELAY, max_s=MAX_DELAY):
    """Sleep for a random human-like duration."""
    time.sleep(random.uniform(min_s, max_s))


def human_scroll(page):
    """Simulate human scrolling behavior."""
    page.mouse.move(random.randint(300, 900), random.randint(200, 500))
    page.wait_for_timeout(random.randint(300, 700))

    # Scroll in 3 steps
    page.evaluate("window.scrollTo({top: document.body.scrollHeight * 0.3, behavior: 'smooth'})")
    page.wait_for_timeout(random.randint(500, 1000))
    page.evaluate("window.scrollTo({top: document.body.scrollHeight * 0.65, behavior: 'smooth'})")
    page.wait_for_timeout(random.randint(500, 1000))
    page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
    page.wait_for_timeout(random.randint(500, 1000))
    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
    page.wait_for_timeout(random.randint(300, 600))


# ============================================================
#  Main Scraper Class
# ============================================================

class EasyUniScraper:

    def __init__(self):
        self.universities = []
        self.courses = []
        self.context = None
        self.page = None
        self.now = datetime.utcnow().isoformat()

    # ----------------------------------------------------------
    #  Browser setup / teardown
    # ----------------------------------------------------------

    def setup_browser(self, playwright):
        """Launch persistent Chrome context with stealth."""
        self.context = playwright.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            viewport={"width": 1366, "height": 768},
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()

        # Apply stealth
        try:
            from playwright_stealth import stealth_sync
            stealth_sync(self.page)
        except Exception as e:
            print(f"⚠ Stealth init warning: {e}")

    def close_browser(self):
        if self.context:
            self.context.close()

    def safe_goto(self, url: str, wait_sel: str = "body", timeout: int = 60000):
        """Navigate with retries and Cloudflare wait."""
        for attempt in range(MAX_RETRIES):
            try:
                self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")
                self.page.wait_for_timeout(3000)

                # Check for Cloudflare challenge
                title = self.page.title()
                if "just a moment" in title.lower() or "403" in title:
                    print(f"   ⏳ Cloudflare detected, waiting 15s...")
                    self.page.wait_for_timeout(15000)

                # Wait for content
                try:
                    self.page.wait_for_selector(wait_sel, timeout=15000)
                except Exception:
                    pass  # proceed anyway

                return True
            except Exception as e:
                print(f"   ⚠ Attempt {attempt+1}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(10)
        return False

    # ----------------------------------------------------------
    #  Level 1: Listing page → University cards
    # ----------------------------------------------------------

    def scrape_listing(self):
        """Extract all university cards from the listing page."""
        print("=" * 60)
        print("📋 Level 1: Scraping university listing...")
        print("=" * 60)

        if not self.safe_goto(LISTING_URL, wait_sel="a[href*='/malaysia/']"):
            print("❌ Failed to load listing page.")
            return

        human_scroll(self.page)

        # Gather all university links from the main content area
        # The listing page shows university cards with links matching /malaysia/{slug}-{id}/
        # We need to find unique university links (not course links which have an extra path segment)
        all_links = self.page.evaluate("""
            () => {
                const results = [];
                const seen = new Set();
                const anchors = document.querySelectorAll('a[href*="/malaysia/"]');
                for (const a of anchors) {
                    const href = a.href;
                    // Match university URLs: /malaysia/{slug}-{id}/ but NOT course URLs (which have 2 path segments after /malaysia/)
                    const match = href.match(/\\/malaysia\\/([a-z0-9-]+-\\d+)\\/?$/i);
                    if (match && !seen.has(href)) {
                        seen.add(href);
                        // Get card content
                        const card = a.closest('li, div[class*="card"], div[class*="institution"], article, section') || a.parentElement;
                        results.push({
                            url: href,
                            name: a.textContent.trim().split('\\n')[0].trim(),
                        });
                    }
                }
                return results;
            }
        """)

        # Deduplicate by URL and filter noise
        seen_urls = set()
        unique_unis = []
        for link in all_links:
            url = link["url"].rstrip("/") + "/"
            name = clean_text(link["name"])
            if url not in seen_urls and name and len(name) > 3:
                # Filter out non-university links (nav items, footer, etc.)
                # University names are usually longer than category labels
                if not any(x in name.lower() for x in ["show all", "all courses", "pre-u", "diploma in", "bachelor in", "master in", "foundation in"]):
                    seen_urls.add(url)
                    unique_unis.append({"url": url, "name": name})

        print(f"✅ Found {len(unique_unis)} unique university links.")

        # Now we also extract card-level data from the listing page
        # For each university, scrape their full detail page in Level 2
        for idx, uni in enumerate(unique_unis):
            uni_id = extract_id_from_url(uni["url"])
            slug = extract_slug_from_url(uni["url"])

            self.universities.append({
                "university_id": uni_id,
                "university_name": uni["name"],
                "university_slug": slug,
                "university_url": uni["url"],
                "city": "",
                "country": "Malaysia",
                "description": "",
                "logo_url": "",
                "is_featured": False,
                "qs_ranking": "",
                "institution_type": "",
                "year_established": "",
                "campus_setting": "",
                "student_population": "",
                "foreign_students_pct": "",
                "undergrad_programs": 0,
                "postgrad_programs": 0,
                "scraped_at": self.now,
            })

        print(f"📊 Prepared {len(self.universities)} universities for Level 2 scraping.")

    def get_completed_universities(self) -> set:
        """Returns a set of university IDs that are already fully scraped."""
        if not DB_PATH.exists():
            return set()
        completed = set()
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    university_id, 
                    IFNULL(undergrad_programs, 0) + IFNULL(postgrad_programs, 0) as expected,
                    (SELECT COUNT(*) FROM courses WHERE courses.university_id = universities.university_id) as actual
                FROM universities
            """)
            for uid, expected, actual in cur.fetchall():
                if actual > 0:
                    # Pagination bug check - if exactly 100 actual and expected > 100, we rescrape
                    if expected > 100 and actual == 100:
                        continue
                    # Safely consider complete if actual >= expected (minus small margin)
                    if actual >= max(1, expected - 5):
                        completed.add(uid)
            conn.close()
        except Exception as e:
            print(f"⚠ Could not read SQLite for resume: {e}")
        return completed

    # ----------------------------------------------------------
    #  Level 2: University detail page
    # ----------------------------------------------------------

    def scrape_university_detail(self, uni_data: dict, idx: int, total: int):
        """Visit university page, extract overview, then scrape courses tab."""
        url = uni_data["university_url"]
        print(f"\n🏫 [{idx+1}/{total}] {uni_data['university_name']}")
        print(f"   URL: {url}")

        if not self.safe_goto(url, wait_sel="h1"):
            print("   ❌ Failed to load university page.")
            return

        human_delay(1, 3)

        # --- Extract overview data ---
        overview = self.page.evaluate("""
            () => {
                const data = {};

                // University name from h1
                const h1 = document.querySelector('h1');
                data.name = h1 ? h1.textContent.trim() : '';

                // Location
                const locEl = document.querySelector('[class*="location"], [class*="campus"]');
                if (locEl) data.location = locEl.textContent.trim();

                // Featured badge
                const body = document.body.textContent;
                data.is_featured = body.includes('Featured');

                // QS Ranking
                const qsMatch = body.match(/# ?([\\d,-]+)\\s*(?:QS|World)/i) || body.match(/QS.*?(\\d[\\d,-]*)/i);
                data.qs_ranking = qsMatch ? qsMatch[1].trim() : '';

                // Program counts
                const ugMatch = body.match(/(\\d+)\\s*Undergraduate/i);
                const pgMatch = body.match(/(\\d+)\\s*Postgraduate/i);
                data.undergrad = ugMatch ? parseInt(ugMatch[1]) : 0;
                data.postgrad = pgMatch ? parseInt(pgMatch[1]) : 0;

                // Logo
                const logo = document.querySelector('img[src*="/media/institution"], img[src*="logo"], header img, [class*="logo"] img');
                data.logo_url = logo ? logo.src : '';

                // Description - from About section
                const aboutSection = document.querySelector('[class*="about"], [class*="description"], [class*="overview"]');
                if (aboutSection) {
                    data.description = aboutSection.textContent.trim().substring(0, 2000);
                }

                // Info cards (Institution Type, Year Established, etc.)
                const allText = document.body.innerText;
                
                const typeMatch = allText.match(/INSTITUTION TYPE[\\s\\n]+(\\w+)/i);
                data.institution_type = typeMatch ? typeMatch[1] : '';

                const yearMatch = allText.match(/YEAR ESTABLISHED[\\s\\n]+([\\d]+|Data not available)/i);
                data.year_established = yearMatch ? yearMatch[1] : '';

                const campusMatch = allText.match(/CAMPUS SETTING[\\s\\n]+(\\w+)/i);
                data.campus_setting = campusMatch ? campusMatch[1] : '';

                const popMatch = allText.match(/STUDENT POPULATION[\\s\\n]+(.+?)(?=\\n|FOREIGN)/i);
                data.student_population = popMatch ? popMatch[1].trim() : '';

                const foreignMatch = allText.match(/FOREIGN STUDENTS[\\s\\n]+(\\S+)/i);
                data.foreign_students_pct = foreignMatch ? foreignMatch[1] : '';

                return data;
            }
        """)

        # Update university record
        if overview.get("name"):
            uni_data["university_name"] = clean_text(overview["name"])
        if overview.get("location"):
            loc = clean_text(overview["location"])
            parts = [p.strip() for p in loc.split(",")]
            uni_data["city"] = parts[0] if parts else ""
            if len(parts) > 1:
                uni_data["country"] = parts[-1]
        uni_data["is_featured"] = overview.get("is_featured", False)
        uni_data["qs_ranking"] = overview.get("qs_ranking", "")
        uni_data["undergrad_programs"] = overview.get("undergrad", 0)
        uni_data["postgrad_programs"] = overview.get("postgrad", 0)
        uni_data["logo_url"] = overview.get("logo_url", "")
        uni_data["description"] = clean_text(overview.get("description", ""))
        uni_data["institution_type"] = overview.get("institution_type", "")
        uni_data["year_established"] = overview.get("year_established", "")
        uni_data["campus_setting"] = overview.get("campus_setting", "")
        uni_data["student_population"] = overview.get("student_population", "")
        uni_data["foreign_students_pct"] = overview.get("foreign_students_pct", "")

        print(f"   ✅ Overview: QS={uni_data['qs_ranking']}, Type={uni_data['institution_type']}, UG={uni_data['undergrad_programs']}, PG={uni_data['postgrad_programs']}")

        # --- Navigate to Courses tab ---
        self.scrape_courses_for_university(uni_data)

    # ----------------------------------------------------------
    #  Level 3: Courses tab → individual course pages
    # ----------------------------------------------------------

    def scrape_courses_for_university(self, uni_data: dict):
        """Navigate to Courses tab and extract all courses."""
        uni_id = uni_data["university_id"]
        uni_name = uni_data["university_name"]

        # Navigate directly to the courses tab URL (avoids breadcrumb click-interception)
        courses_url = uni_data["university_url"].rstrip("/") + "/courses/"
        try:
            if not self.safe_goto(courses_url, wait_sel="a[href]"):
                # Fallback: try JavaScript click on the tab from current page
                print("   >> Fallback: JS-clicking Courses tab...")
                clicked = self.page.evaluate("""
                    () => {
                        const tabs = document.querySelectorAll('a, button');
                        for (const tab of tabs) {
                            if (tab.textContent.trim() === 'Courses') {
                                tab.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                if clicked:
                    self.page.wait_for_timeout(3000)
                    print("   >> JS click succeeded.")
                else:
                    print("   >> Could not find Courses tab. Skipping.")
                    return
            else:
                print("   >> Navigated to courses URL directly.")
        except Exception as e:
            print(f"   >> Could not navigate to courses: {e}")
            return

        human_delay(1, 2)

        # Handle pagination / lazy loading
        print("   >> Scrolling to load all courses...")
        last_height = self.page.evaluate("document.body.scrollHeight")
        no_change_count = 0
        while no_change_count < 4:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.page.wait_for_timeout(2000)
            
            try:
                # Try clicking "Load More" or "Show More" if it exists
                self.page.evaluate("""
                    () => {
                        const btns = Array.from(document.querySelectorAll('button, a')).filter(el => 
                            (el.textContent.includes('Load More') || el.textContent.includes('Show More')) && el.offsetParent !== null
                        );
                        if (btns.length > 0) btns[0].click();
                    }
                """)
                self.page.wait_for_timeout(1500)
            except Exception:
                pass

            new_height = self.page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                no_change_count += 1
            else:
                no_change_count = 0
                last_height = new_height

        # Extract course links from the courses table/list
        course_links = self.page.evaluate("""
            () => {
                const results = [];
                const seen = new Set();
                // Course links follow the pattern: /malaysia/{uni-slug}/{course-slug}-{id}/
                const anchors = document.querySelectorAll('a[href]');
                for (const a of anchors) {
                    const href = a.href;
                    // Match course URLs: /malaysia/{uni-slug}-{id}/{course-slug}-{course-id}/
                    const match = href.match(/\\/malaysia\\/[a-z0-9-]+-\\d+\\/[a-z0-9-]+-\\d+\\/?$/i);
                    if (match && !seen.has(href)) {
                        seen.add(href);
                        // Get course row data
                        const row = a.closest('tr, li, div[class*="course"], div[class*="row"]') || a.parentElement;
                        const rowText = row ? row.textContent : '';
                        
                        results.push({
                            url: href,
                            name: a.textContent.trim().split('\\n')[0].trim(),
                            row_text: rowText.substring(0, 500),
                        });
                    }
                }
                return results;
            }
        """)

        # Deduplicate
        seen_urls = set()
        unique_courses = []
        for c in course_links:
            url = c["url"].rstrip("/") + "/"
            name = clean_text(c["name"])
            if url not in seen_urls and name and len(name) > 3:
                # Skip navigation/filter links
                if not any(x in name.lower() for x in ["apply now", "request info", "show all", "filter"]):
                    seen_urls.add(url)
                    unique_courses.append(c)

        print(f"   📊 Found {len(unique_courses)} courses. Visiting each for details...")

        # Quick-parse row data for duration/fee from listing
        for cidx, course_info in enumerate(unique_courses):
            course_url = course_info["url"].rstrip("/") + "/"
            course_name = clean_text(course_info["name"])
            course_id = extract_id_from_url(course_url)
            course_slug = extract_slug_from_url(course_url, base=f"{extract_slug_from_url(uni_data['university_url'])}/")

            # Extract quick data from row text
            row_text = course_info.get("row_text", "")
            duration_raw = ""
            study_mode = ""
            fee_display = ""

            # Parse duration from row
            dur_match = re.search(r"(\d[\d.]*\s*(?:year|month|week)s?)", row_text, re.IGNORECASE)
            if dur_match:
                duration_raw = dur_match.group(1)

            # Parse study mode
            if "full-time" in row_text.lower() or "full time" in row_text.lower():
                study_mode = "Full-time"
                if "part-time" in row_text.lower() or "part time" in row_text.lower():
                    study_mode = "Full-time / Part-time"
            elif "part-time" in row_text.lower() or "part time" in row_text.lower():
                study_mode = "Part-time"

            # Parse fees
            fee_matches = re.findall(r"(?:From\s*)?\$\s*[\d,]+", row_text)

            # Build initial course record
            course_record = {
                "course_id": course_id,
                "course_name": course_name,
                "course_slug": course_slug,
                "course_url": course_url,
                "university_id": uni_id,
                "university_name": uni_name,
                "qualification_level": "",
                "subject_category": "",
                "duration_raw": duration_raw,
                "duration_years": clean_duration_years(duration_raw),
                "study_mode": study_mode,
                "fee_local_usd": None,
                "fee_foreign_usd": None,
                "fee_display": " | ".join(fee_matches) if fee_matches else "",
                "intake_dates": "",
                "campus_location": "",
                "english_requirement": "",
                "description": "",
                "scraped_at": self.now,
            }

            # --- Visit individual course page for full details ---
            print(f"      📖 [{cidx+1}/{len(unique_courses)}] {course_name[:60]}...")
            self.scrape_course_detail(course_record)
            self.courses.append(course_record)
            human_delay(1.5, 3.5)

        # Navigate back to keep context stable for next university
        print(f"   ✅ Scraped {len(unique_courses)} courses for {uni_name}.")

    def scrape_course_detail(self, course_record: dict):
        """Visit individual course page and extract full details."""
        url = course_record["course_url"]

        if not self.safe_goto(url, wait_sel="h1"):
            print(f"      ❌ Failed to load course page.")
            return

        human_delay(0.5, 1.5)

        details = self.page.evaluate("""
            () => {
                const data = {};
                const body = document.body.innerText || '';

                // Course name
                const h1 = document.querySelector('h1');
                data.name = h1 ? h1.textContent.trim() : '';

                // Qualification level from breadcrumb
                const breadcrumbs = document.querySelectorAll('nav[aria-label*="breadcrumb"] a, [class*="breadcrumb"] a, [class*="breadcrumb"] li, [class*="Breadcrumb"] a');
                const bcTexts = Array.from(breadcrumbs).map(b => b.textContent.trim());
                data.breadcrumbs = bcTexts;

                // Look for qualification keywords
                const qualKeywords = ["Foundation", "Pre-U", "Diploma", "Bachelor", "Master", "Doctoral", "PhD", "Certificate", "MBA"];
                for (const kw of qualKeywords) {
                    if (data.name.toLowerCase().includes(kw.toLowerCase()) || bcTexts.some(b => b.toLowerCase().includes(kw.toLowerCase()))) {
                        data.qualification = kw;
                        break;
                    }
                }

                // Duration
                const durMatch = body.match(/Duration[:\\s]+([\\d.]+\\s*(?:year|month|week)s?)/i) ||
                                 body.match(/(\\d[\\d.]*\\s*(?:year|month|week)s?)/i);
                data.duration = durMatch ? durMatch[1] || durMatch[0] : '';

                // Study mode
                const modeMatch = body.match(/Study\\s*Mode[:\\s]*(Full[- ]?Time(?:\\s*\\/\\s*Part[- ]?Time)?|Part[- ]?Time|Online|ODL)/i) ||
                                  body.match(/(Full[- ]?[Tt]ime(?:\\s*\\/\\s*Part[- ]?[Tt]ime)?)/i);
                data.study_mode = modeMatch ? modeMatch[1] : '';

                // Fees
                const feeSection = body.match(/(?:Estimated|Tuition|Annual).*?(?:cost|fee|price).*?\\n(.*?)\\n/gi) || [];
                const allFees = body.match(/\\$\\s*[\\d,]+(?:\\s*\\((?:local|foreign|international)\\))?/gi) || [];
                data.fees = allFees;

                // Try local vs foreign
                const localFee = body.match(/\\$\\s*([\\d,]+)\\s*\\(?local\\)?/i);
                const foreignFee = body.match(/\\$\\s*([\\d,]+)\\s*\\(?(?:foreign|international)\\)?/i);
                data.fee_local = localFee ? localFee[1] : '';
                data.fee_foreign = foreignFee ? foreignFee[1] : '';
                
                // If just one fee listed (e.g. "From $ 2,785")
                if (!data.fee_local && !data.fee_foreign && allFees.length > 0) {
                    if (allFees.length >= 2) {
                        data.fee_local = allFees[0];
                        data.fee_foreign = allFees[1];
                    } else {
                        data.fee_local = allFees[0];
                    }
                }

                // Intakes
                const intakeMatch = body.match(/Intake[s]?[:\\s]*((?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[,\\s]*)+)/i);
                data.intakes = intakeMatch ? intakeMatch[1].trim() : '';
                
                // Also check for intake badges/pills
                if (!data.intakes) {
                    const badges = document.querySelectorAll('[class*="intake"] span, [class*="badge"], [class*="pill"], [class*="tag"]');
                    const months = [];
                    const monthNames = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];
                    for (const b of badges) {
                        const t = b.textContent.trim().toLowerCase();
                        if (monthNames.some(m => t.startsWith(m))) {
                            months.push(b.textContent.trim());
                        }
                    }
                    data.intakes = months.join(', ');
                }

                // Campus location
                const campusMatch = body.match(/Campus[:\\s]*(.*?)(?:\\n|$)/i) ||
                                    body.match(/Location[:\\s]*(.*?)(?:\\n|$)/i);
                data.campus = campusMatch ? campusMatch[1].trim() : '';

                // English requirement
                const engMatch = body.match(/(?:English|IELTS|TOEFL|MUET)[\\s\\S]*?(?:requirement|score|band)?[:\\s]*(IELTS\\s*[\\d.]+|TOEFL\\s*[\\d]+|MUET\\s*Band\\s*[\\d]+|[\\d.]+)/i);
                data.english_req = engMatch ? engMatch[0].trim().substring(0, 100) : '';

                // Description
                const descEl = document.querySelector('[class*="course-description"], [class*="about-course"], [class*="overview"], [class*="description"], article, main');
                data.description = descEl ? descEl.textContent.trim().substring(0, 2000) : '';

                // Subject category from URL
                data.url = window.location.href;

                return data;
            }
        """)

        # Update course record with details
        if details.get("name"):
            course_record["course_name"] = clean_text(details["name"])

        if details.get("qualification"):
            qual = details["qualification"]
            # Normalize qualification level
            qual_map = {
                "foundation": "Foundation / Pre-U",
                "pre-u": "Foundation / Pre-U",
                "diploma": "Diploma",
                "bachelor": "Bachelor's Degree",
                "master": "Master's Degree",
                "mba": "Master's Degree",
                "doctoral": "Doctoral Degree (PhD)",
                "phd": "Doctoral Degree (PhD)",
                "certificate": "Certificate",
            }
            for key, val in qual_map.items():
                if key in qual.lower():
                    course_record["qualification_level"] = val
                    break

        if details.get("duration"):
            course_record["duration_raw"] = clean_text(details["duration"])
            course_record["duration_years"] = clean_duration_years(course_record["duration_raw"])

        if details.get("study_mode"):
            course_record["study_mode"] = clean_text(details["study_mode"])

        if details.get("fee_local"):
            course_record["fee_local_usd"] = clean_fee(details["fee_local"])

        if details.get("fee_foreign"):
            course_record["fee_foreign_usd"] = clean_fee(details["fee_foreign"])

        if details.get("fees"):
            course_record["fee_display"] = " | ".join(details["fees"][:4])

        if details.get("intakes"):
            course_record["intake_dates"] = clean_text(details["intakes"])

        if details.get("campus"):
            course_record["campus_location"] = clean_text(details["campus"])

        if details.get("english_req"):
            course_record["english_requirement"] = clean_text(details["english_req"])

        if details.get("description"):
            course_record["description"] = clean_text(details["description"])[:2000]

        # Extract subject category from breadcrumbs
        if details.get("breadcrumbs"):
            bcs = details["breadcrumbs"]
            if len(bcs) >= 3:
                course_record["subject_category"] = bcs[2] if len(bcs) > 2 else ""

    # ----------------------------------------------------------
    #  Export
    # ----------------------------------------------------------

    def save_all(self):
        """Save to SQLite database, then export ALL data from DB to CSV and JSON."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print("\n" + "=" * 60)
        print("💾 Saving data...")
        print("=" * 60)

        # 1. Update SQLite with new data from memory
        self._save_sqlite()

        # 2. Export full DB to CSV and JSON (prevents wiping old data)
        self._export_from_db()

    def _export_from_db(self):
        """Read all rows from SQLite and dump to CSV/JSON."""
        if not DB_PATH.exists():
            return
            
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Universities
        cur.execute("SELECT * FROM universities")
        db_unis = [dict(row) for row in cur.fetchall()]
        if db_unis:
            with open(UNIVERSITIES_CSV, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=db_unis[0].keys())
                writer.writeheader()
                writer.writerows(db_unis)
            with open(UNIVERSITIES_JSON, "w", encoding="utf-8") as f:
                json.dump(db_unis, f, ensure_ascii=False, indent=2)
            print(f"   ✅ Exported {len(db_unis)} Universities to CSV/JSON")

        # Courses
        cur.execute("SELECT * FROM courses")
        db_courses = [dict(row) for row in cur.fetchall()]
        if db_courses:
            with open(COURSES_CSV, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=db_courses[0].keys())
                writer.writeheader()
                writer.writerows(db_courses)
            with open(COURSES_JSON, "w", encoding="utf-8") as f:
                json.dump(db_courses, f, ensure_ascii=False, indent=2)
            print(f"   ✅ Exported {len(db_courses)} Courses to CSV/JSON")
            
        conn.close()

    def _save_sqlite(self):
        """Save to SQLite database with proper schema."""
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()

        # Create universities table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS universities (
                university_id INTEGER PRIMARY KEY,
                university_name TEXT,
                university_slug TEXT UNIQUE,
                university_url TEXT,
                city TEXT,
                country TEXT DEFAULT 'Malaysia',
                description TEXT,
                logo_url TEXT,
                is_featured BOOLEAN,
                qs_ranking TEXT,
                institution_type TEXT,
                year_established TEXT,
                campus_setting TEXT,
                student_population TEXT,
                foreign_students_pct TEXT,
                undergrad_programs INTEGER,
                postgrad_programs INTEGER,
                scraped_at TEXT
            )
        """)

        # Create courses table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                course_id INTEGER PRIMARY KEY,
                course_name TEXT,
                course_slug TEXT UNIQUE,
                course_url TEXT,
                university_id INTEGER,
                university_name TEXT,
                qualification_level TEXT,
                subject_category TEXT,
                duration_raw TEXT,
                duration_years REAL,
                study_mode TEXT,
                fee_local_usd INTEGER,
                fee_foreign_usd INTEGER,
                fee_display TEXT,
                intake_dates TEXT,
                campus_location TEXT,
                english_requirement TEXT,
                description TEXT,
                scraped_at TEXT,
                FOREIGN KEY (university_id) REFERENCES universities(university_id)
            )
        """)

        # Insert universities
        for u in self.universities:
            try:
                cur.execute("""
                    INSERT OR REPLACE INTO universities VALUES (
                        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                    )
                """, (
                    u["university_id"], u["university_name"], u["university_slug"],
                    u["university_url"], u["city"], u["country"], u["description"],
                    u["logo_url"], u["is_featured"], u["qs_ranking"],
                    u["institution_type"], u["year_established"], u["campus_setting"],
                    u["student_population"], u["foreign_students_pct"],
                    u["undergrad_programs"], u["postgrad_programs"], u["scraped_at"],
                ))
            except Exception as e:
                print(f"   ⚠ SQLite university insert error: {e}")

        # Insert courses
        for c in self.courses:
            try:
                cur.execute("""
                    INSERT OR REPLACE INTO courses VALUES (
                        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                    )
                """, (
                    c["course_id"], c["course_name"], c["course_slug"],
                    c["course_url"], c["university_id"], c["university_name"],
                    c["qualification_level"], c["subject_category"],
                    c["duration_raw"], c["duration_years"], c["study_mode"],
                    c["fee_local_usd"], c["fee_foreign_usd"], c["fee_display"],
                    c["intake_dates"], c["campus_location"],
                    c["english_requirement"], c["description"], c["scraped_at"],
                ))
            except Exception as e:
                print(f"   ⚠ SQLite course insert error: {e}")

        conn.commit()
        conn.close()
        print(f"   ✅ SQLite database → {DB_PATH}")

    # ----------------------------------------------------------
    #  Main entry point
    # ----------------------------------------------------------

    def run(self):
        """Execute the full 3-level scraping pipeline."""
        start_time = time.time()

        print("🚀 EasyUni Malaysia Scraper — Starting...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        with sync_playwright() as p:
            self.setup_browser(p)

            try:
                # Level 1: Get university list
                self.scrape_listing()

                if not self.universities:
                    print("❌ No universities found. Aborting.")
                    return

                # Check resume state
                completed_ids = self.get_completed_universities()
                pending_unis = [u for u in self.universities if u["university_id"] not in completed_ids]
                
                print(f"\n📈 Resume Check: {len(completed_ids)} universities already completed.")
                print(f"📈 Pending: {len(pending_unis)} remaining out of {len(self.universities)} total.\n")
                
                if not pending_unis:
                    print("🎉 All universities are already fully scraped. Nothing to do!")
                    return
                    
                self.universities = pending_unis

                # Level 2 + 3: For each university → details + courses
                total = len(self.universities)
                for idx, uni in enumerate(self.universities):
                    self.scrape_university_detail(uni, idx, total)
                    human_delay(2, 4)

                    # Save intermediate results every 5 universities
                    if (idx + 1) % 5 == 0:
                        print(f"\n💾 Intermediate save ({idx+1}/{total})...")
                        self.save_all()

            except KeyboardInterrupt:
                print("\n\n⚠ Interrupted by user. Saving collected data...")
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
            finally:
                self.close_browser()

        # Final save
        self.save_all()

        elapsed = time.time() - start_time
        print(f"\n{'=' * 60}")
        print(f"🏁 DONE!")
        print(f"   📊 Universities: {len(self.universities)}")
        print(f"   📊 Courses: {len(self.courses)}")
        print(f"   ⏱  Time: {elapsed/60:.1f} minutes")
        print(f"   📁 Output: {OUTPUT_DIR}")
        print(f"{'=' * 60}")


# ============================================================
#  Entry point
# ============================================================

if __name__ == "__main__":
    scraper = EasyUniScraper()
    scraper.run()
