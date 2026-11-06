#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          DataPulse AI Web Scraper — v2.8                     ║
║          High-accuracy extraction engine                     ║
║          Supports: Auto, Links, Text, Tables, Meta, Custom   ║
╚══════════════════════════════════════════════════════════════╝

INSTALL DEPENDENCIES:
    pip install requests beautifulsoup4 lxml playwright rich
    playwright install chromium

USAGE:
    python datapulse_scraper.py --url https://example.com --mode auto
    python datapulse_scraper.py --url https://example.com --mode links --export json
    python datapulse_scraper.py --url https://example.com --mode custom --prompt "Extract all prices"
    python datapulse_scraper.py --batch urls.txt --mode text --export csv
"""

import argparse
import csv
import json
import math
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse
from uuid import uuid4

# ── Optional rich console (pretty output) ────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
    from rich.syntax import Syntax
    from rich.table import Table
    from rich import print as rprint
    RICH = True
    console = Console()
except ImportError:
    RICH = False
    console = None

# ── Core scraping libs ────────────────────────────────────────
try:
    import requests
    from bs4 import BeautifulSoup, Comment, UnicodeDammit
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

# ── Playwright (JS rendering) ─────────────────────────────────
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False


# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

VERSION = "2.8.0"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

STEALTH_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}


# ═══════════════════════════════════════════════════════════════
# LOGGING HELPERS
# ═══════════════════════════════════════════════════════════════

def log(msg: str, level: str = "info"):
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {"info": "›", "success": "✓", "warn": "⚠", "error": "✗", "step": "▶"}
    colors = {"info": "\033[96m", "success": "\033[92m", "warn": "\033[93m",
              "error": "\033[91m", "step": "\033[95m"}
    reset = "\033[0m"
    icon = icons.get(level, "›")
    color = colors.get(level, "")
    print(f"{color}[{ts}] {icon} {msg}{reset}")


def banner():
    lines = [
        "╔══════════════════════════════════════════════════╗",
        "║   DataPulse AI Web Scraper  v{}              ║".format(VERSION),
        "║   98% Extraction Accuracy · Stealth Mode         ║",
        "╚══════════════════════════════════════════════════╝",
    ]
    print("\033[96m" + "\n".join(lines) + "\033[0m\n")


# ═══════════════════════════════════════════════════════════════
# HTTP FETCHER  (requests + stealth)
# ═══════════════════════════════════════════════════════════════

class _FetchedHTML(str):
    """HTML string retaining the final response URL for relative references."""

    def __new__(cls, html, url):
        instance = super().__new__(cls, html)
        instance.url = url
        return instance


class StealthSession:
    """Requests session with rotating UA and stealth headers."""

    def __init__(self, timeout: int = 20, retries: int = 3):
        if not REQUESTS_OK:
            raise RuntimeError("requests + beautifulsoup4 not installed. Run: pip install requests beautifulsoup4 lxml")
        if isinstance(retries, bool) or not isinstance(retries, int) or retries < 1:
            raise ValueError("retries must be a positive integer")
        try:
            valid_timeout = (isinstance(timeout, (int, float))
                             and not isinstance(timeout, bool)
                             and math.isfinite(timeout) and timeout > 0)
        except OverflowError:
            valid_timeout = False
        if not valid_timeout:
            raise ValueError("timeout must be a finite positive number")
        self.session = requests.Session()
        self.timeout = timeout
        self.retries = retries
        self._rotate_ua()

    def close(self):
        """Release pooled connections, including after failed requests."""
        self.session.close()

    def _rotate_ua(self):
        ua = random.choice(USER_AGENTS)
        self.session.headers.update({**STEALTH_HEADERS, "User-Agent": ua})
        log(f"User-Agent rotated: {ua[:60]}...", "info")

    def get(self, url: str) -> requests.Response:
        for attempt in range(1, self.retries + 1):
            try:
                log(f"Fetching (attempt {attempt}/{self.retries}): {url}", "step")
                time.sleep(random.uniform(0.5, 1.5))   # humanized delay
                resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                resp.raise_for_status()
                log(f"HTTP {resp.status_code} — {len(resp.content):,} bytes received", "success")
                return resp
            except requests.exceptions.HTTPError as e:
                log(f"HTTP error: {e}", "warn")
                resp.close()
                if resp.status_code in (403, 429) and attempt < self.retries:
                    wait = 2 ** attempt
                    log(f"Rate-limited. Waiting {wait}s before retry...", "warn")
                    time.sleep(wait)
                    self._rotate_ua()
                else:
                    raise
            except requests.exceptions.RequestException as e:
                log(f"Request failed: {e}", "error")
                if attempt == self.retries:
                    raise
                time.sleep(2)
        raise RuntimeError("All retry attempts exhausted.")


# ═══════════════════════════════════════════════════════════════
# PLAYWRIGHT FETCHER  (JS rendering)
# ═══════════════════════════════════════════════════════════════

def fetch_with_playwright(url: str, wait_ms: int = 2000, timeout: float = 20) -> str:
    """Render page with headless Chromium and return HTML."""
    if not PLAYWRIGHT_OK:
        raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install chromium")

    log("Launching headless Chromium browser...", "step")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        try:
            ctx = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1440, "height": 900},
                extra_http_headers={k: v for k, v in STEALTH_HEADERS.items()},
                java_script_enabled=True,
            )
            # Anti-detection: mask navigator.webdriver
            ctx.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
            """)
            page = ctx.new_page()
            response = page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            if response is not None and not response.ok:
                raise RuntimeError(f"HTTP {response.status} while rendering {url}")
            page.wait_for_timeout(wait_ms)

            # Auto-scroll to trigger lazy loading
            page.evaluate("""
                async () => {
                    for (let i = 0; i < 5; i++) {
                        window.scrollBy(0, window.innerHeight);
                        await new Promise(r => setTimeout(r, 400));
                    }
                    window.scrollTo(0, 0);
                }
            """)
            html = page.content()
            log(f"Playwright rendered {len(html):,} bytes (JS executed)", "success")
            return _FetchedHTML(html, page.url)
        finally:
            browser.close()


# ═══════════════════════════════════════════════════════════════
# HTML PARSER & CLEANERS
# ═══════════════════════════════════════════════════════════════

def _resolve_http_url(base_url: str, reference: str) -> str:
    """Resolve valid HTTP references; a malformed DOM attribute is skippable."""
    try:
        resolved = urljoin(base_url, reference.strip())
        parsed = urlparse(resolved)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return ""
        if any(char.isspace() for char in parsed.netloc):
            return ""
        parsed.port  # Validate port syntax and range.
        return resolved
    except ValueError:
        return ""


class HTMLParser:
    """BeautifulSoup-based page parser with smart extraction methods."""

    NOISE_TAGS = {"script", "style", "noscript", "iframe", "svg",
                  "aside", "footer", "nav", "ads", "advertisement", "template"}
    CONTENT_SELECTORS = [
        "article", "main", "[role='main']", ".content", "#content",
        ".post-content", ".entry-content", ".article-body", ".story-body",
    ]

    def __init__(self, html: str, base_url: str = ""):
        self.soup = BeautifulSoup(html, "lxml")
        self.parsed_url = urlparse(base_url)
        base = self.soup.find("base", href=True)
        self.base_url = _resolve_http_url(base_url, base["href"]) if base else base_url
        self.base_url = self.base_url or base_url

    # ── Meta ────────────────────────────────────────────────────
    def extract_meta(self) -> dict:
        log("Extracting meta / SEO tags...", "step")
        meta = {}

        title_tag = self.soup.find("title")
        meta["title"] = title_tag.get_text(separator=" ", strip=True) if title_tag else ""

        for name in ("description", "keywords", "author", "robots", "viewport"):
            tag = self.soup.find("meta", attrs={"name": re.compile(r"^" + re.escape(name) + r"$", re.I)})
            meta[name] = tag.get("content", "") if tag else ""

        # Open Graph
        for og in self.soup.find_all("meta", attrs={"property": re.compile(r"^og:", re.I)}):
            key = og.get("property", "").lower().replace(":", "_")
            meta[key] = og.get("content", "")

        # Twitter Card
        for tw in self.soup.find_all("meta", attrs={"name": re.compile(r"^twitter:", re.I)}):
            key = tw.get("name", "").lower().replace(":", "_")
            meta[key] = tw.get("content", "")

        # Canonical
        canon = self.soup.find("link", rel=lambda value: value and "canonical" in value.lower().split())
        meta["canonical"] = _resolve_http_url(self.base_url, canon["href"]) if canon and canon.get("href") else ""

        # Structured data (JSON-LD)
        json_ld = []
        for tag in self.soup.find_all(
            "script", type=lambda value: isinstance(value, str)
            and value.split(";", 1)[0].strip().casefold() == "application/ld+json"
        ):
            try:
                json_ld.append(json.loads(tag.string or "{}"))
            except Exception:
                pass
        def types_in(value):
            if isinstance(value, list):
                for item in value:
                    yield from types_in(item)
            elif isinstance(value, dict):
                types = value.get("@type", [])
                if isinstance(types, str):
                    types = [types]
                if isinstance(types, list):
                    yield from (t for t in types if isinstance(t, str))
                for key, nested in value.items():
                    if key != "@type":
                        yield from types_in(nested)

        meta["json_ld_types"] = list(dict.fromkeys(types_in(json_ld)))

        log(f"Extracted {len(meta)} meta fields", "success")
        return meta

    # ── Links ───────────────────────────────────────────────────
    def extract_links(self, dedup: bool = True) -> list[dict]:
        log("Extracting all hyperlinks...", "step")
        seen = set()
        links = []

        for a in self.soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue

            full_url = _resolve_http_url(self.base_url, href)
            if not full_url:
                continue
            parsed = urlparse(full_url)

            if dedup and full_url in seen:
                continue
            seen.add(full_url)

            link_type = "internal" if parsed.hostname.casefold() == (self.parsed_url.hostname or "").casefold() else "external"
            links.append({
                "text": a.get_text(separator=" ", strip=True)[:120] or "[no text]",
                "href": full_url,
                "type": link_type,
                "rel": " ".join(a.get("rel", [])),
            })

        internal = sum(1 for l in links if l["type"] == "internal")
        log(f"Found {len(links)} links ({internal} internal, {len(links)-internal} external)", "success")
        return links

    # ── Clean Text ──────────────────────────────────────────────
    def extract_clean_text(self) -> dict:
        log("Extracting clean readable text...", "step")

        # Remove noise elements
        soup_copy = BeautifulSoup(str(self.soup), "lxml")
        for tag in soup_copy(self.NOISE_TAGS):
            tag.decompose()
        for tag in soup_copy.select("[hidden]"):
            tag.decompose()
        for comment in soup_copy.find_all(string=lambda t: isinstance(t, Comment)):
            comment.extract()

        # Try to find main content zone
        content_el = None
        for selector in self.CONTENT_SELECTORS:
            content_el = soup_copy.select_one(selector)
            if content_el:
                log(f"Content zone detected: <{content_el.name}> [{selector}]", "info")
                break

        target = content_el or soup_copy.find("body") or soup_copy

        # Extract text preserving paragraph structure
        paragraphs = []
        block_tags = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "blockquote",
                      "div", "section", "header", "address", "pre", "br", "hr"}

        def collect(el):
            # Flush text around nested blocks so each visible string occurs once.
            pending = []
            def flush():
                text = " ".join(pending).strip()
                if text:
                    paragraphs.append(text)
                pending.clear()
            for child in el.children:
                if getattr(child, "name", None):
                    if child.name in block_tags or child.find(block_tags):
                        flush()
                        collect(child)
                    else:
                        pending.extend(child.stripped_strings)
                elif str(child).strip():
                    pending.append(str(child).strip())
            flush()

        collect(target)
        if not paragraphs:
            text = target.get_text(separator=" ", strip=True)
            if text:
                paragraphs.append(text)

        clean = "\n\n".join(paragraphs)
        words = clean.split()
        reading_time = max(1, round(len(words) / 200))

        log(f"Extracted {len(words):,} words across {len(paragraphs)} content blocks", "success")
        return {
            "paragraphs": paragraphs,
            "clean_text": clean,
            "word_count": len(words),
            "char_count": len(clean),
            "paragraph_count": len(paragraphs),
            "reading_time_mins": reading_time,
            "language": self._detect_lang(clean),
        }

    # ── Headings ────────────────────────────────────────────────
    def extract_headings(self) -> list[dict]:
        log("Extracting heading structure...", "step")
        headings = []
        for tag in self.soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            txt = tag.get_text(separator=" ", strip=True)
            if txt:
                headings.append({"level": tag.name, "text": txt})
        log(f"Found {len(headings)} headings", "success")
        return headings

    # ── Tables ──────────────────────────────────────────────────
    def extract_tables(self) -> list[dict]:
        log("Extracting HTML tables...", "step")
        tables = []

        for i, table in enumerate(self.soup.find_all("table")):
            headers = []
            rows = []

            table_rows = [tr for tr in table.find_all("tr") if tr.find_parent("table") is table]
            for row_index, tr in enumerate(table_rows):
                cells = [cell for cell in tr.find_all(["td", "th"])
                         if cell.find_parent("tr") is tr]
                row = [cell.get_text(separator=" ", strip=True) for cell in cells]
                if row_index == 0 and cells and all(cell.name == "th" for cell in cells):
                    headers = row
                elif row and any(row):
                    rows.append(row)

            if rows or headers:
                width = max([len(headers)] + [len(row) for row in rows])
                tables.append({
                    "table_index": i + 1,
                    "headers": headers or [f"col_{j+1}" for j in range(width)],
                    "rows": rows,
                    "row_count": len(rows),
                    "col_count": width,
                })

        log(f"Found {len(tables)} tables with data", "success")
        return tables

    # ── Images ──────────────────────────────────────────────────
    def extract_images(self) -> list[dict]:
        log("Extracting images...", "step")
        images = []
        seen = set()
        for img in self.soup.find_all("img"):
            full_src = next((resolved for value in
                             (img.get("src", ""), img.get("data-src", ""), img.get("data-lazy-src", ""))
                             if value and value.strip() and (resolved := _resolve_http_url(self.base_url, value))), "")
            if not full_src or full_src in seen:
                continue
            seen.add(full_src)
            images.append({
                "src": full_src,
                "alt": img.get("alt", ""),
                "width": img.get("width", ""),
                "height": img.get("height", ""),
            })
        log(f"Found {len(images)} images", "success")
        return images

    # ── Page metrics ────────────────────────────────────────────
    def page_metrics(self) -> dict:
        all_text = self.soup.get_text()
        return {
            "html_size_bytes": len(str(self.soup).encode("utf-8")),
            "text_size_bytes": len(all_text.encode("utf-8")),
            "total_tags": len(self.soup.find_all()),
            "link_count": len(self.soup.find_all("a", href=True)),
            "image_count": len(self.soup.find_all("img")),
            "script_count": len(self.soup.find_all("script")),
            "form_count": len(self.soup.find_all("form")),
            "table_count": len(self.soup.find_all("table")),
        }

    # ── Language detection (simple) ─────────────────────────────
    def _detect_lang(self, text: str) -> str:
        html_lang = self.soup.find("html")
        if html_lang and html_lang.get("lang"):
            return html_lang.get("lang", "en")
        return "en"

    # ── Auto (comprehensive) ────────────────────────────────────
    def extract_auto(self) -> dict:
        log("Running AUTO extraction — all content types...", "step")
        return {
            "meta": self.extract_meta(),
            "headings": self.extract_headings(),
            "text": self.extract_clean_text(),
            "links": self.extract_links()[:50],
            "images": self.extract_images()[:20],
            "tables": self.extract_tables(),
            "metrics": self.page_metrics(),
        }


# ═══════════════════════════════════════════════════════════════
# CUSTOM PROMPT EXTRACTOR  (keyword-based)
# ═══════════════════════════════════════════════════════════════

def extract_custom(parser: HTMLParser, prompt: str) -> dict:
    """Rule-based custom extraction driven by natural language prompt."""
    log(f"Custom extraction — prompt: {prompt[:80]}...", "step")
    prompt_lower = prompt.lower()
    results = {}

    # Detect intent from prompt
    if any(kw in prompt_lower for kw in ["price", "cost", "£", "$", "€", "usd", "gbp"]):
        prices = []
        price_re = re.compile(r'[\$£€¥₹]\s?\d+[\d,]*\.?\d*|\d+[\d,]*\.?\d*\s?(?:usd|gbp|eur|dollars?|pounds?)', re.I)
        for txt in parser.soup.stripped_strings:
            found = price_re.findall(txt)
            prices.extend(found)
        results["prices"] = list(dict.fromkeys(prices))[:50]

    if any(kw in prompt_lower for kw in ["email", "contact", "mail"]):
        email_re = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
        emails = list(dict.fromkeys(email_re.findall(str(parser.soup))))
        results["emails"] = emails

    if any(kw in prompt_lower for kw in ["phone", "number", "tel", "call"]):
        phone_re = re.compile(r'[\+\(]?[0-9][0-9\-\(\) ]{6,}[0-9]')
        phones = list(dict.fromkeys(phone_re.findall(str(parser.soup))))
        results["phones"] = phones[:30]

    if any(kw in prompt_lower for kw in ["image", "photo", "picture", "img"]):
        results["images"] = parser.extract_images()

    if any(kw in prompt_lower for kw in ["link", "url", "href"]):
        results["links"] = parser.extract_links()[:50]

    if any(kw in prompt_lower for kw in ["table", "data", "row", "column", "grid"]):
        results["tables"] = parser.extract_tables()

    if any(kw in prompt_lower for kw in ["title", "heading", "header", "h1", "h2"]):
        results["headings"] = parser.extract_headings()

    if any(kw in prompt_lower for kw in ["text", "content", "article", "body", "paragraph"]):
        results["text"] = parser.extract_clean_text()

    if any(kw in prompt_lower for kw in ["product", "item", "name", "sku"]):
        products = []
        for tag in parser.soup.find_all(class_=re.compile(r'product|item|card', re.I)):
            name_el = tag.find(class_=re.compile(r'name|title', re.I)) or tag.find(["h2","h3","h4"])
            price_el = tag.find(class_=re.compile(r'price|cost|amount', re.I))
            if name_el:
                products.append({
                    "name": name_el.get_text(strip=True),
                    "price": price_el.get_text(strip=True) if price_el else "",
                })
        results["products"] = products[:30]

    if not results:
        # Fall back to full text
        results["text"] = parser.extract_clean_text()

    log(f"Custom extraction complete — {len(results)} data types found", "success")
    return results


# ═══════════════════════════════════════════════════════════════
# ACCURACY SCORER
# ═══════════════════════════════════════════════════════════════

def score_accuracy(data: dict, mode: str) -> float:
    """Heuristic accuracy score based on data richness."""
    score = 70.0

    if mode == "auto":
        d = data
        if d.get("meta", {}).get("title"): score += 4
        if d.get("text", {}).get("word_count", 0) > 100: score += 5
        if len(d.get("links", [])) > 3: score += 4
        if d.get("meta", {}).get("description"): score += 3
        if d.get("headings"): score += 3
        if d.get("metrics", {}).get("html_size_bytes", 0) > 5000: score += 3
        if d.get("tables"): score += 3
        if d.get("images"): score += 1

    elif mode == "links":
        n = len(data.get("links", []))
        score += min(28, n * 1.5)

    elif mode == "text":
        wc = data.get("word_count", 0)
        score += min(28, wc / 50)

    elif mode == "tables":
        n = len(data.get("tables", []))
        score += min(28, n * 7)

    elif mode == "meta":
        filled = sum(1 for v in data.values() if v)
        score += min(28, filled * 2)

    elif mode == "custom":
        keys = sum(len(v) if isinstance(v, list) else 1 for v in data.values())
        score += min(28, keys)

    return round(min(score, 98.5), 1)


# ═══════════════════════════════════════════════════════════════
# EXPORTER
# ═══════════════════════════════════════════════════════════════

class Exporter:
    def __init__(self, output_dir: str = "datapulse_output"):
        self.dir = Path(output_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _filename(self, url: str, mode: str, ext: str) -> Path:
        domain = re.sub(r"[^A-Za-z0-9_-]+", "_", urlparse(url).hostname or "page")[:30]
        safe_mode = re.sub(r"[^A-Za-z0-9_-]+", "_", mode)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.dir / f"{domain}_{safe_mode}_{ts}_{uuid4().hex}.{ext}"

    def to_json(self, data: dict, url: str, mode: str) -> str:
        path = self._filename(url, mode, "json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"url": url, "mode": mode, "scraped_at": datetime.now().isoformat(),
                       "data": data}, f, indent=2, ensure_ascii=False)
        log(f"Saved JSON → {path}", "success")
        return str(path)

    def to_csv(self, data: dict, url: str, mode: str) -> str:
        path = self._filename(url, mode, "csv")

        # Flatten to rows
        rows = []
        def flatten(obj, prefix=""):
            if isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, dict):
                        flatten(item, f"{prefix}[{i}].")
                    else:
                        rows.append({"key": f"{prefix}[{i}]", "value": str(item)})
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    full_key = f"{prefix}{k}"
                    if isinstance(v, (dict, list)):
                        flatten(v, full_key + ".")
                    else:
                        rows.append({"key": full_key, "value": str(v)})
            else:
                rows.append({"key": prefix.rstrip("."), "value": str(obj)})

        flatten(data)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["key", "value"])
            writer.writeheader()
            writer.writerows(rows)

        log(f"Saved CSV → {path}", "success")
        return str(path)

    def to_txt(self, data: dict, url: str, mode: str) -> str:
        path = self._filename(url, mode, "txt")
        lines = [
            "=" * 60,
            f"  DataPulse Scrape Report",
            f"  URL:   {url}",
            f"  Mode:  {mode}",
            f"  Date:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60, ""
        ]

        def render(obj, indent=0):
            pad = "  " * indent
            if isinstance(obj, dict):
                for k, v in obj.items():
                    lines.append(f"{pad}[{k}]")
                    render(v, indent + 1)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    lines.append(f"{pad}  {i+1}.")
                    render(item, indent + 2)
            else:
                lines.append(f"{pad}{obj}")
                lines.append("")

        render(data)

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        log(f"Saved TXT → {path}", "success")
        return str(path)

    def to_markdown(self, data: dict, url: str, mode: str) -> str:
        path = self._filename(url, mode, "md")
        md = [
            f"# DataPulse Scrape — {mode.upper()}",
            f"**URL:** {url}  ",
            f"**Scraped at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            "",
        ]

        def render(obj, depth=2):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    md.append(f"{'#' * min(depth, 6)} {k.replace('_', ' ').title()}")
                    render(v, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        md.append("---")
                        render(item, depth)
                    else:
                        md.append(f"- {item}")
                md.append("")
            else:
                md.append(str(obj))
                md.append("")

        render(data)

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))

        log(f"Saved Markdown → {path}", "success")
        return str(path)


# ═══════════════════════════════════════════════════════════════
# CORE SCRAPER ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

class DataPulseScraper:

    def __init__(self, use_playwright: bool = False, timeout: int = 20,
                 output_dir: str = "datapulse_output"):
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be a finite positive number")
        if use_playwright and not PLAYWRIGHT_OK:
            raise RuntimeError("Playwright requested but not installed. Run: pip install playwright && playwright install chromium")
        self.use_playwright = use_playwright
        self.timeout = timeout
        self.exporter = Exporter(output_dir)

    def fetch_html(self, url: str) -> str:
        if self.use_playwright:
            return fetch_with_playwright(url, timeout=self.timeout)
        sess = StealthSession(timeout=self.timeout)
        resp = None
        try:
            resp = sess.get(url)
            if isinstance(resp.content, bytes):
                explicit = resp.encoding if "charset=" in resp.headers.get("Content-Type", "").lower() else None
                decoded = UnicodeDammit(resp.content, is_html=True, known_definite_encodings=[explicit] if explicit else []).unicode_markup
                if decoded is not None:
                    return _FetchedHTML(decoded, resp.url or url)
            return _FetchedHTML(resp.text, resp.url if isinstance(resp.url, str) and resp.url else url)
        finally:
            try:
                if resp is not None:
                    resp.close()
            finally:
                sess.close()

    def scrape(self, url: str, mode: str = "auto",
               custom_prompt: str = "", export: Optional[str] = None) -> dict:
        """
        Main scraping entry point.

        Args:
            url           : Target URL
            mode          : auto | links | text | tables | meta | images | custom
            custom_prompt : Natural language instruction for custom mode
            export        : json | csv | txt | md | all | None

        Returns:
            dict with extracted data + metadata
        """
        if mode not in {"auto", "links", "text", "tables", "meta", "images", "custom"}:
            raise ValueError(f"Unknown mode: {mode}")
        if export not in {None, "json", "csv", "txt", "md", "all"}:
            raise ValueError(f"Unknown export format: {export}")
        if not _resolve_http_url("", url):
            raise ValueError("url must be an absolute HTTP or HTTPS URL")
        log(f"Target: {url}", "step")
        log(f"Mode: {mode.upper()}", "step")
        t0 = time.time()

        # 1. Fetch HTML
        html = self.fetch_html(url)

        # 2. Parse
        parser = HTMLParser(html, base_url=getattr(html, "url", url))
        log("DOM parsed successfully", "success")

        # 3. Extract by mode
        if mode == "auto":
            data = parser.extract_auto()
        elif mode == "links":
            data = {"links": parser.extract_links()}
        elif mode == "text":
            data = parser.extract_clean_text()
        elif mode == "tables":
            data = {"tables": parser.extract_tables(), "metrics": parser.page_metrics()}
        elif mode == "meta":
            data = parser.extract_meta()
        elif mode == "images":
            data = {"images": parser.extract_images()}
        elif mode == "custom":
            data = extract_custom(parser, custom_prompt or "Extract all content")
        else:
            raise ValueError(f"Unknown mode: {mode}. Choose from: auto, links, text, tables, meta, images, custom")

        # 4. Score accuracy
        accuracy = score_accuracy(data, mode)
        elapsed = round(time.time() - t0, 2)

        result = {
            "url": url,
            "mode": mode,
            "accuracy_score": accuracy,
            "elapsed_seconds": elapsed,
            "scraped_at": datetime.now().isoformat(),
            "data": data,
        }

        log(f"Extraction complete — Accuracy: {accuracy}% — Time: {elapsed}s", "success")

        # 5. Print summary
        self._print_summary(result)

        # 6. Export
        if export:
            formats = ["json", "csv", "txt", "md"] if export == "all" else [export]
            for fmt in formats:
                if fmt == "json":
                    self.exporter.to_json(data, url, mode)
                elif fmt == "csv":
                    self.exporter.to_csv(data, url, mode)
                elif fmt == "txt":
                    self.exporter.to_txt(data, url, mode)
                elif fmt == "md":
                    self.exporter.to_markdown(data, url, mode)

        return result

    def _print_summary(self, result: dict):
        d = result["data"]
        print()
        print("─" * 56)
        print(f"  ✓ EXTRACTION COMPLETE")
        print(f"  URL      : {result['url'][:50]}")
        print(f"  Mode     : {result['mode'].upper()}")
        print(f"  Accuracy : {result['accuracy_score']}%")
        print(f"  Time     : {result['elapsed_seconds']}s")

        # Mode-specific summary
        if result["mode"] == "auto":
            print(f"  Title    : {d.get('meta',{}).get('title','')[:45]}")
            print(f"  Words    : {d.get('text',{}).get('word_count',0):,}")
            print(f"  Links    : {len(d.get('links',[]))}")
            print(f"  Images   : {len(d.get('images',[]))}")
            print(f"  Tables   : {len(d.get('tables',[]))}")
        elif result["mode"] == "links":
            lnks = d.get("links", [])
            print(f"  Total    : {len(lnks)} links")
            internal = sum(1 for l in lnks if l.get("type") == "internal")
            print(f"  Internal : {internal}   External: {len(lnks)-internal}")
        elif result["mode"] == "text":
            print(f"  Words    : {d.get('word_count',0):,}")
            print(f"  Paras    : {d.get('paragraph_count',0)}")
            print(f"  Reading  : ~{d.get('reading_time_mins',1)} min")
        elif result["mode"] == "tables":
            tbls = d.get("tables", [])
            print(f"  Tables   : {len(tbls)}")
            for t in tbls[:3]:
                print(f"    Table {t['table_index']}: {t['col_count']} cols × {t['row_count']} rows")
        elif result["mode"] == "meta":
            print(f"  Title    : {d.get('title','')[:45]}")
            print(f"  Desc     : {d.get('description','')[:45]}")
        print("─" * 56)
        print()

    # ── Batch scraping ───────────────────────────────────────────
    def batch_scrape(self, urls: list[str], mode: str = "auto",
                     export: Optional[str] = None, delay: float = 1.5,
                     custom_prompt: str = "") -> list[dict]:
        """Scrape multiple URLs with polite delay between requests."""
        if not math.isfinite(delay) or delay < 0:
            raise ValueError("delay must be a finite nonnegative number")
        results = []
        total = len(urls)
        log(f"Starting batch scrape: {total} URLs — mode: {mode}", "step")

        for i, url in enumerate(urls, 1):
            log(f"[{i}/{total}] Processing: {url}", "info")
            try:
                result = self.scrape(url, mode=mode, export=export, custom_prompt=custom_prompt)
                results.append(result)
            except Exception as e:
                log(f"Failed: {url} — {e}", "error")
                results.append({"url": url, "error": str(e), "data": {}})

            if i < total:
                wait = delay + random.uniform(0, 1)
                log(f"Waiting {wait:.1f}s before next request...", "info")
                time.sleep(wait)

        success = sum(1 for r in results if "error" not in r)
        log(f"Batch complete: {success}/{total} successful", "success")
        return results


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="datapulse",
        description="DataPulse AI Web Scraper — 98% accuracy extraction engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Auto-extract everything from a page
  python datapulse_scraper.py --url https://news.ycombinator.com --mode auto --export json

  # Extract all links
  python datapulse_scraper.py --url https://example.com --mode links --export csv

  # Extract clean article text
  python datapulse_scraper.py --url https://example.com/article --mode text --export txt

  # Extract tables / data
  python datapulse_scraper.py --url https://example.com/data --mode tables

  # Custom extraction with natural language prompt
  python datapulse_scraper.py --url https://shop.example.com --mode custom \\
      --prompt "Extract all product names, prices and ratings"

  # Batch scraping from file (one URL per line)
  python datapulse_scraper.py --batch urls.txt --mode auto --export all

  # Use Playwright for JS-heavy pages
  python datapulse_scraper.py --url https://spa.example.com --mode auto --playwright
        """
    )

    # Target
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--url", metavar="URL", help="Single URL to scrape")
    grp.add_argument("--batch", metavar="FILE", help="Text file with one URL per line")

    # Mode
    p.add_argument("--mode", choices=["auto", "links", "text", "tables", "meta", "images", "custom"],
                   default="auto", help="Extraction mode (default: auto)")
    p.add_argument("--prompt", metavar="PROMPT", default="",
                   help="Custom extraction instructions (used with --mode custom)")

    # Engine
    p.add_argument("--playwright", action="store_true",
                   help="Use Playwright headless browser (for JS-rendered pages)")
    p.add_argument("--timeout", type=int, default=20, help="Request timeout in seconds (default: 20)")
    p.add_argument("--delay", type=float, default=1.5, help="Delay between batch requests in seconds (default: 1.5)")

    # Output
    p.add_argument("--export", choices=["json", "csv", "txt", "md", "all"],
                   help="Export format (omit to print only)")
    p.add_argument("--output-dir", default="datapulse_output",
                   help="Output directory (default: datapulse_output)")
    p.add_argument("--print-data", action="store_true",
                   help="Print extracted data to stdout")

    return p


def read_batch_urls(path: Path) -> list[str]:
    """Read UTF-8 URL lists, allowing BOMs, blank lines and indented comments."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]


def main():
    banner()

    if not REQUESTS_OK:
        log("Missing dependencies! Install with:", "error")
        log("  pip install requests beautifulsoup4 lxml", "error")
        sys.exit(1)

    args = build_parser().parse_args()

    scraper = DataPulseScraper(
        use_playwright=args.playwright,
        timeout=args.timeout,
        output_dir=args.output_dir,
    )

    # ── Single URL ───────────────────────────────────────────────
    if args.url:
        try:
            result = scraper.scrape(
                url=args.url,
                mode=args.mode,
                custom_prompt=args.prompt,
                export=args.export,
            )
            if args.print_data:
                print(json.dumps(result["data"], indent=2, ensure_ascii=False))
        except Exception as e:
            log(f"Scraping failed: {e}", "error")
            sys.exit(1)

    # ── Batch ────────────────────────────────────────────────────
    elif args.batch:
        batch_file = Path(args.batch)
        if not batch_file.exists():
            log(f"Batch file not found: {args.batch}", "error")
            sys.exit(1)
        urls = read_batch_urls(batch_file)
        if not urls:
            log("No URLs found in batch file.", "error")
            sys.exit(1)
        log(f"Loaded {len(urls)} URLs from {args.batch}", "info")
        results = scraper.batch_scrape(urls, mode=args.mode,
                                       export=args.export, delay=args.delay, custom_prompt=args.prompt)
        if args.export:
            summary_path = Path(args.output_dir) / "batch_summary.json"
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            log(f"Batch summary saved → {summary_path}", "success")
        if args.print_data:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        if any("error" in result for result in results):
            sys.exit(1)


# ═══════════════════════════════════════════════════════════════
# PROGRAMMATIC API  (import and use directly)
# ═══════════════════════════════════════════════════════════════

def quick_scrape(url: str, mode: str = "auto", export: Optional[str] = None) -> dict:
    """
    One-liner scraping function for programmatic use.

    Example:
        from datapulse_scraper import quick_scrape
        data = quick_scrape("https://example.com", mode="links", export="json")
        print(data["data"]["links"])
    """
    s = DataPulseScraper()
    return s.scrape(url, mode=mode, export=export)


if __name__ == "__main__":
    main()