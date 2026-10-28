# 🌐 Web Scraper Application

A modern, user-friendly **web scraping application** that allows users to extract and analyze data from web pages through a clean web interface.

🔗 **Live Demo:** https://webscrapper-ten-hazel.vercel.app/

---

## 🚀 Features

- 🔍 Scrape data from public web pages  
- 🧾 Extract structured content (text, links, headings, etc.)
- ⚡ Fast and lightweight scraping
- 🌐 Web-based interface (no local setup required for users)
- 📱 Responsive UI (works on desktop & mobile)

---

## 🛠️ Tech Stack

**Frontend**
- HTML, CSS, JavaScript
- Deployed on **Vercel**

**Backend / Logic**
- Python-based scraping logic
- Libraries such as:
  - `requests`
  - `BeautifulSoup`
  - (or equivalent, depending on your implementation)

---

## 📌 How It Works

1. User enters a valid website URL
2. The scraper fetches the webpage content
3. HTML is parsed and relevant data is extracted
4. Processed data is displayed on the web interface

---

## 🧠 Use Cases

- Data collection for research
- Competitive analysis
- Learning web scraping concepts
- Content monitoring
- Academic & demo projects

---

## ⚠️ Disclaimer

This project is intended **for educational purposes only**.  
Always ensure you follow:
- Website **robots.txt**
- Terms of Service
- Legal and ethical scraping practices

---

## 📷 Live Preview

👉 Try it here:  
**https://webscrapper-ten-hazel.vercel.app/**

---

## 📂 Project Status

✅ Functional  
🚧 Actively improving (features & optimizations planned)

---

## Python CLI and regression checks

The standalone scraper is `script.py`. Install its dependencies and run it directly:

```bash
python -m pip install -r requirements.txt
python script.py --url https://example.com --mode text --export json
```

Use `--playwright` for pages that need JavaScript rendering after running
`python -m playwright install chromium`. Requesting this engine without installing
Playwright reports an error. `--timeout` sets its navigation timeout as well as
the HTTP request timeout, in seconds.

Batch input uses UTF-8, with one URL per line; blank lines and comments beginning
with `#` (including indented comments) are ignored:

```bash
python script.py --batch urls.txt --mode auto --export all --output-dir reports/run
```

Run the regression suite without a browser, API keys, or live network requests:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

GitHub Actions runs these checks on Python 3.11 and 3.12 for pushes to `main`
and pull requests. Coverage includes structured metadata, URL resolution, text,
tables, images, Unicode, export integrity, request cleanup, configuration errors,
and batch input. Browser navigation and HTTP fetches are mocked in these tests.
The displayed accuracy score is a data-richness heuristic, not measured accuracy.

---

## 👨‍💻 Author

**Ayush Tiwari**  
- 🎓 B.Tech | Data Science & AI  
- 🔗 GitHub: https://github.com/Ayushdevo  
- 🌐 Portfolio: (add when ready)

---

## ⭐ Feedback & Contributions

Suggestions and improvements are welcome!  
If you find this project useful, don’t forget to ⭐ the repository.
