import asyncio
import csv
import sqlite3
import logging
import credentials
from playwright.async_api import async_playwright
from openpyxl import Workbook

# === CONFIG ===
KEYWORD = "Product Manager"
LOCATION = "India"
MAX_PAGES = 10
SCROLL_TIMES = 10
LOG_FILE = "linkedin_scraper.log"

# === LOGGING SETUP ===
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())  # also show in CLI

async def run_scraper():
    # SQLite DB setup
    conn = sqlite3.connect("linkedin_jobs.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            keyword TEXT,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT,
            connection TEXT
        )
    ''')
    conn.commit()

    # Excel setup
    wb = Workbook()
    ws = wb.active
    ws.title = "LinkedIn Jobs"
    ws.append(["Keyword", "Title", "Company", "Location", "URL", "Connection"])

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()

        logger.info("Logging in...")
        await page.goto("https://www.linkedin.com/login")
        await page.fill('input[name="session_key"]', credentials.email)
        await page.fill('input[name="session_password"]', credentials.password)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(5000)

        logger.info("Logged in. Navigating to job search...")
        job_url = f"https://www.linkedin.com/jobs/search/?keywords={KEYWORD.replace(' ', '%20')}&location={LOCATION.replace(' ', '%20')}"
        await page.goto(job_url)
        await page.wait_for_timeout(5000)

        results = []
        current_page = 1

        while current_page <= MAX_PAGES:
            logger.info(f"\nScraping Page {current_page}")
            try:
                await page.wait_for_selector('.job-card-container--clickable', timeout=30000)
            except:
                logger.warning("Job cards not found!")
                break

            # Scroll the entire page to load more jobs
            logger.info("Scrolling to load more job listings...")
            for _ in range(SCROLL_TIMES):
                await page.mouse.wheel(0, 1000)
                await page.wait_for_timeout(2000)

            job_cards = await page.locator('.job-card-container--clickable').all()
            logger.info(f"Found {len(job_cards)} job cards")

            for idx, card in enumerate(job_cards):
                try:
                    title_raw = await card.locator('a.job-card-container__link > span[aria-hidden="true"] strong').all_inner_texts()
                    company_raw = await card.locator('div.artdeco-entity-lockup__subtitle span').all_inner_texts()
                    location_raw = await card.locator('div.artdeco-entity-lockup__caption li span').all_inner_texts()
                    url = await card.locator('a.job-card-container__link').get_attribute('href')

                    job_data = {
                        "Keyword": KEYWORD,
                        "Title": " ".join([t.strip() for t in title_raw if t.strip()]),
                        "Company": " ".join([c.strip() for c in company_raw if c.strip()]),
                        "Location": " ".join([l.strip() for l in location_raw if l.strip()]),
                        "URL": f"https://www.linkedin.com{url.strip()}" if url else "N/A",
                        "Connection": "N/A"
                    }

                    results.append(job_data)

                    cursor.execute('''
                        INSERT INTO jobs (keyword, title, company, location, url, connection)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (job_data["Keyword"], job_data["Title"], job_data["Company"],
                          job_data["Location"], job_data["URL"], job_data["Connection"]))
                    conn.commit()

                    ws.append([job_data[k] for k in ["Keyword", "Title", "Company", "Location", "URL", "Connection"]])

                    logger.info(f"Job {idx + 1} saved: {job_data['Title']} @ {job_data['Company']}")

                except Exception as e:
                    logger.warning(f"Skipping job card {idx + 1} due to error: {e}")
                    continue

            try:
                next_btn = page.locator('button[aria-label="View next page"]')
                if await next_btn.is_visible():
                    logger.info("Clicking next page...")
                    await next_btn.click()
                    await page.wait_for_timeout(5000)
                    current_page += 1
                else:
                    logger.info("No more next pages.")
                    break
            except Exception as e:
                logger.warning("Pagination stopped: %s", e)
                break

        wb.save("linkedin_jobs.xlsx")

        if results:
            with open("linkedin_jobs.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
            logger.info(f"\nDone. {len(results)} jobs saved to CSV, SQLite, and Excel.")
        else:
            logger.warning("No job data scraped.")

        cursor.close()
        conn.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
