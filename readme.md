# DataPulse AI Web Scraper v2.8

High-accuracy Python scraping engine with stealth headers, JS rendering, and multi-format export.

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Install Playwright for JS-heavy pages
playwright install chromium

# 3. Run
python datapulse_scraper.py --url https://example.com --mode auto --export json
```

## 🛠 Extraction Modes

| Mode      | What it extracts                                      |
|-----------|-------------------------------------------------------|
| `auto`    | Everything — title, text, links, images, tables, meta |
| `links`   | All hyperlinks (internal + external, deduped)         |
| `text`    | Clean readable text, word count, reading time         |
| `tables`  | All HTML tables as structured rows + headers          |
| `meta`    | Title, description, OG tags, Twitter cards, JSON-LD   |
| `images`  | All image URLs with alt text and dimensions           |
| `custom`  | Natural language — extract prices, emails, products…  |

## 📋 CLI Examples

```bash
# Auto-extract everything
python datapulse_scraper.py --url https://news.ycombinator.com --mode auto --export json

# Get all links as CSV
python datapulse_scraper.py --url https://example.com --mode links --export csv

# Clean article text
python datapulse_scraper.py --url https://blog.example.com/post --mode text --export txt

# Extract tables
python datapulse_scraper.py --url https://example.com/data --mode tables --export all

# Custom extraction
python datapulse_scraper.py --url https://shop.example.com --mode custom \
    --prompt "Extract all product names, prices and star ratings"

# JavaScript-rendered pages (requires playwright)
python datapulse_scraper.py --url https://spa.example.com --mode auto --playwright

# Batch scrape from file
python datapulse_scraper.py --batch urls.txt --mode auto --export json --delay 2
```

## 🐍 Python API

```python
from datapulse_scraper import DataPulseScraper, quick_scrape

# One-liner
result = quick_scrape("https://example.com", mode="links", export="json")
print(result["data"]["links"])

# Full control
scraper = DataPulseScraper(use_playwright=False, timeout=20)
result = scraper.scrape(
    url="https://example.com",
    mode="custom",
    custom_prompt="Extract all emails and phone numbers",
    export="csv"
)
print(result["accuracy_score"])  # e.g. 97.5

# Batch
urls = ["https://site1.com", "https://site2.com"]
results = scraper.batch_scrape(urls, mode="text", export="json", delay=1.5)
```

## 📁 Output Files

All exports saved to `datapulse_output/` (configurable with `--output-dir`):
- `{domain}_{mode}_{timestamp}.json`
- `{domain}_{mode}_{timestamp}.csv`
- `{domain}_{mode}_{timestamp}.txt`
- `{domain}_{mode}_{timestamp}.md`

## ⚙️ Options

```
--url URL           Single URL to scrape
--batch FILE        Text file with one URL per line
--mode MODE         Extraction mode (default: auto)
--prompt TEXT       Custom extraction prompt
--playwright        Use headless Chromium for JS pages
--timeout N         Request timeout seconds (default: 20)
--delay N           Batch delay between requests (default: 1.5)
--export FORMAT     json | csv | txt | md | all
--output-dir DIR    Output folder (default: datapulse_output)
--print-data        Print JSON to stdout
```