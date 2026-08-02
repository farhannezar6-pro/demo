from playwright.sync_api import sync_playwright
import time
import os

def research_scraper():
    url = "https://your-uni.com/%D8%AC%D8%A7%D9%85%D8%B9%D8%A7%D8%AA-%D9%85%D8%A7%D9%84%D9%8A%D8%B2%D9%8A%D8%A7/"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        print("Visiting list page:", url)
        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000) # Wait for CF
            
            # Extract links to individual university pages
            links = page.locator("a").evaluate_all(
                "(elements) => elements.map(el => ({href: el.href, text: el.innerText}))"
            )
            uni_links = [l for l in links if 'your-uni.com/' in l['href'] and len(l['text'].strip()) > 3]
            
            # Let's save the list page HTML
            with open("temp_list.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            
            print(f"Found {len(uni_links)} total links. Saving unique ones to file...")
            unique_hrefs = list(set([l['href'] for l in uni_links]))
            
            # Try to guess a university link based on typical slugs
            target_uni = None
            for href in unique_hrefs:
                if 'university' in href.lower() or 'جامع' in href or 'معهد' in href:
                    # check if not equal to the main list
                    if href.strip('/') != url.strip('/'):
                        target_uni = href
                        break
            
            if not target_uni:
                # just pick the first valid link inside entry-content or similar
                content_links = page.locator(".entry-content a, .elementor-widget-wrap a").evaluate_all("(elements) => elements.map(el=>el.href)")
                if content_links:
                     target_uni = content_links[0]
                else:
                     target_uni = unique_hrefs[10] if len(unique_hrefs) > 10 else unique_hrefs[0]

            print("Visiting university page:", target_uni)
            page.goto(target_uni, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            with open("temp_uni.html", "w", encoding="utf-8") as f:
                f.write(page.content())
                
        except Exception as e:
            print("Error during scraping:", e)
        finally:
            browser.close()

if __name__ == "__main__":
    research_scraper()
