"""
Flipkart TWS (True Wireless) Earbuds Scraper
-------------------------------------------------
• Uses ScrapingBee to fetch HTML safely (proxies, anti-bot handled for you)
• Parses product Name, Price, Rating, Reviews, Discount and Product URL
• Auto-pagination: scrape multiple pages in one run (stop when no items)
• Saves output to CSV and Excel for clients
""
# =========================
# Required Libraries
# =========================
import os
import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

# =========================
# 1) Config (edit as needed)
# =========================
TARGET_URL = (
    "https://www.flipkart.com/audio-video/headset/earphones/wireless-earphones/true-wireless/pr?sid="
    "0pm%2Cfcn%2C821%2Ca7x%2C2si&q=airpods&p%5B%5D=facets.rating%255B%255D%3D4%25E2%2598%2585%2B%2526%2Babove"
)
API_URL = "https://app.scrapingbee.com/api/v1/"

# ScrapingBee API key added directly
API_KEY = "QAVXGX3AXDUQE0MIM7FYZ3EIC53YF9ZTY11K7G01G4O6ORXTG076M5URZ9EKO5ORTLWWANQH9IHQSZ" (Somrting looks Missing in this API Dont try😍)

MAX_PAGES = 50
REQUEST_DELAY_SEC = 2

CSV_PATH = "flipkart_products_all.csv"
XLSX_PATH = "flipkart_products_all.xlsx"

# =========================
# 2) Helpers
# =========================
PRICE_NUM = re.compile(r"[\d,]+")

def clean_price(text: str):
    if not text:
        return None
    m = PRICE_NUM.search(text)
    if not m:
        return None
    return int(m.group(0).replace(",", ""))

def extract_first(sel, *queries):
    for q in queries:
        el = sel.select_one(q)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return None

def extract_link(sel):
    a = sel.select_one("a[href]")
    if not a:
        return None
    href = a.get("href", "")
    if href.startswith("/"):
        return "https://www.flipkart.com" + href
    return href or None

def parse_reviews_block(sel):
    blk = sel.select_one("span._2_R_DZ")
    if not blk:
        return None, None
    txt = blk.get_text(" ", strip=True)
    nums = re.findall(r"[\d,]+", txt)
    ratings_count = int(nums[0].replace(",", "")) if nums else None
    reviews_count = int(nums[1].replace(",", "")) if len(nums) > 1 else None
    return ratings_count, reviews_count

def parse_product_cards(html: str):
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select("div._2kHMtA, div._4ddWXP, div._1AtVbE")
    products = []

    for card in cards:
        name = extract_first(card, "div._4rR01T", "a.s1Q9rs", "a._1fQZEK")
        price_text = extract_first(card, "div._30jeq3._1_WHN1", "div._30jeq3")
        price_value = clean_price(price_text)
        rating_text = extract_first(card, "div._3LWZlK")
        try:
            rating_value = float(rating_text) if rating_text else None
        except ValueError:
            rating_value = None
        mrp_text = extract_first(card, "div._3I9_wc._27UcVY", "div._3I9_wc")
        mrp_value = clean_price(mrp_text)
        discount_text = extract_first(card, "div._3Ay6Sb span")
        ratings_count, reviews_count = parse_reviews_block(card)
        product_url = extract_link(card)

        if name or price_value or product_url:
            products.append({
                "Name": name,
                "Price": price_value,
                "Rating": rating_value,
                "MRP": mrp_value,
                "Discount": discount_text,
                "Ratings_Count": ratings_count,
                "Reviews_Count": reviews_count,
                "Product_URL": product_url,
            })

    return products

def build_paged_url(base: str, page: int) -> str:
    if "page=" in base:
        return re.sub(r"(page=)(\d+)", fr"\g<1>{page}", base)
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}page={page}"

# =========================
# 3) Main run: fetch → parse → export
# =========================
all_rows = []
for page in range(1, MAX_PAGES + 1):
    page_url = build_paged_url(TARGET_URL, page)
    print(f"\n⏳ Fetching page {page}: {page_url}")

    params = {"api_key": API_KEY, "url": page_url, "render_js": "false"}
    resp = requests.get(API_URL, params=params, timeout=60)

    if resp.status_code != 200:
        print(f"❌ Failed page {page} | HTTP {resp.status_code}")
        break

    with open(f"flipkart_page_{page}.html", "w", encoding="utf-8") as f:
        f.write(resp.text)

    rows = parse_product_cards(resp.text)
    if not rows:
        print(f"⚠️ No products found on page {page}. Stopping.")
        break

    print(f"✅ Found {len(rows)} products on page {page}")
    all_rows.extend(rows)
    time.sleep(REQUEST_DELAY_SEC)

print(f"\n🎉 Total products collected: {len(all_rows)}")

if all_rows:
    df = pd.DataFrame(all_rows)
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    df.to_excel(XLSX_PATH, index=False, engine="openpyxl")
    print(f"📁 Saved CSV → {CSV_PATH}")
    print(f"📁 Saved Excel → {XLSX_PATH}")
    print("\n🔍 Preview:")
    print(df.head(10))
