# 🔍 LinkedIn Job Scraper (Python + Playwright)

This is a real-browser based scraper to automate LinkedIn job searches.  
It logs in securely, searches by keyword & location, scrolls to load jobs, paginates, and saves results in **CSV**, **Excel**, and **SQLite**.

---

## 🚀 Features

- ✅ Headful browser automation using Playwright
- ✅ Secure login via `credentials.py`
- ✅ Scroll support to load more results
- ✅ Paginate through job listings
- ✅ Saves output to:
  - `linkedin_jobs.csv`
  - `linkedin_jobs.xlsx`
  - `linkedin_jobs.db`
- ✅ CLI + log file: `linkedin_scraper.log`
- ✅ Configurable keyword, location, page and scroll limits

---

## 📦 Requirements

```bash
pip install -r requirements.txt

