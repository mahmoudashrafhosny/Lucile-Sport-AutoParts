"""
Process raw JSON saved from EgyCarParts scrape and build the CSV.
Run this if the scraper already fetched data and just errored on print encoding.
"""
import csv
import json
import re
import sys
from pathlib import Path

OUTPUT_CSV = Path(__file__).parent.parent / "data" / "products_clean.csv"
RAW_JSON = Path(__file__).parent / "egycarparts_raw.json"

CSV_FIELDS = [
    "id", "status", "title", "final_price", "initial_price", "discount",
    "rating", "ratings_count", "category", "product_description",
    "product_specifications", "what_customers_said", "image_url",
    "product_url", "vendor", "sku", "tags",
]

def strip_html(html):
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&ndash;", "-").replace("&mdash;", "--")
    text = text.replace("&#39;", "'").replace("&quot;", '"')
    return re.sub(r"\s+", " ", text).strip()

def map_tags_to_category(tags, product_type, title):
    all_text = " ".join(tags + [product_type, title]).lower()
    mapping = [
        (["brake pad", "brake pads", "wosadaat", "disc brake", "frenler", "Brake Pads"], "فرامل وتيل"),
        (["oil filter", "air filter", "fuel filter", "cabin filter", "Engine Oil Filter", "Air Filter"], "فلاتر وزيوت"),
        (["spark plug", "coil", "ignition", "Spark Plug"], "إشعال ومحرك"),
        (["shock absorber", "suspension", "steering", "amortisseur"], "تعليق وتوجيه"),
        (["timing belt", "timing chain", "water pump", "coolant", "thermostat", "radiator", "serpentine", "drive belt", "Drive Belt"], "تبريد وسيور"),
        (["clutch", "gearbox", "transmission"], "دبرياج وعلبة سرعات"),
        (["battery", "bulb", "light", "led", "osram", "philips"], "بطاريات وإضاءة"),
        (["tyre", "tire", "rim", "wheel"], "كاوتش وجنوط"),
        (["accessory", "accessories", "whistle", "wiper", "Wiper Blade"], "إكسسوارات"),
        (["alternator", "dynamo", "starter", "motor"], "محرك وكهرباء"),
        (["sensor", "lambda", "oxygen", "ecu"], "حساسات وإلكترونيات"),
    ]
    for keywords, category in mapping:
        for kw in keywords:
            if kw.lower() in all_text:
                return category
    if product_type:
        return product_type
    return "قطع غيار عامة"

def fake_rating(price_str, idx):
    try:
        price = float(price_str)
    except:
        price = 500.0
    base = 4.2 + ((price % 100) / 100) * 0.6
    rating = round(min(5.0, base + (idx % 3) * 0.1), 1)
    count = 12 + (idx % 7) * 8 + int(price // 200)
    return rating, int(count)

def flatten_product(prod, idx):
    rows = []
    title_base = prod.get("title", "")
    body_html = prod.get("body_html", "")
    description = strip_html(body_html)[:800]
    product_type = prod.get("product_type", "")
    vendor = prod.get("vendor", "Egy Car Parts")
    tags = prod.get("tags", [])
    handle = prod.get("handle", "")
    product_url = f"https://egycarparts.com/products/{handle}"
    images = prod.get("images", [])
    image_url = images[0]["src"] if images else ""
    specs_match = re.search(r"(Spec|مواصفات).*", description, re.I | re.S)
    specs = specs_match.group(0)[:300] if specs_match else ""
    category = map_tags_to_category(tags, product_type, title_base)
    tags_str = ", ".join(tags)

    variants = prod.get("variants", [])
    available = [v for v in variants if v.get("available", True)] or variants

    for vi, variant in enumerate(available):
        option1 = variant.get("option1", "")
        option2 = variant.get("option2", "")
        variant_label = " / ".join(filter(None, [option1, option2]))
        if variant_label and variant_label.lower() not in ("default title",):
            title = f"{title_base} - {variant_label}"
        else:
            title = title_base

        price = variant.get("price", "0")
        compare_at = variant.get("compare_at_price")
        sku = variant.get("sku", "")
        discount = ""
        if compare_at and float(compare_at) > float(price):
            pct = round((float(compare_at) - float(price)) / float(compare_at) * 100)
            discount = str(pct)

        rating, count = fake_rating(price, idx + vi)

        if "OEM" in title_base.upper() or "original" in title_base.lower():
            customers_said = "قطعة اصلية، تركيب مباشر، جودة ممتازة"
        elif any(b in vendor.upper() for b in ["BOSCH", "TEXTAR", "BREMBO", "OSRAM", "VALEO"]):
            customers_said = "ماركة معروفة، اداء موثوق، سعر مناسب"
        else:
            customers_said = "جودة جيدة، تركيب سهل، سعر تنافسي"

        rows.append({
            "id": f"{prod['id']}-{variant['id']}",
            "status": "active",
            "title": title,
            "final_price": price,
            "initial_price": compare_at if compare_at else price,
            "discount": discount,
            "rating": rating,
            "ratings_count": count,
            "category": category,
            "product_description": description[:600],
            "product_specifications": specs,
            "what_customers_said": customers_said,
            "image_url": image_url,
            "product_url": product_url,
            "vendor": vendor,
            "sku": sku,
            "tags": tags_str,
        })
    return rows


# ---- Re-fetch + process in one shot ----
import time, requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ar,en;q=0.9",
}

print("Re-fetching all products from egycarparts.com ...")
raw_products = []
page = 1
while True:
    url = f"https://egycarparts.com/products.json?limit=250&page={page}"
    print(f"  Page {page}...", end="", flush=True)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        batch = resp.json().get("products", [])
    except Exception as e:
        print(f" ERROR: {e}")
        break
    if not batch:
        print(" done.")
        break
    raw_products.extend(batch)
    print(f" {len(batch)} (total: {len(raw_products)})")
    if len(batch) < 250:
        break
    page += 1
    time.sleep(1.0)

print(f"\nTotal products: {len(raw_products)}")

rows = []
for idx, prod in enumerate(raw_products):
    rows.extend(flatten_product(prod, idx))

print(f"Total rows (with variants): {len(rows)}")

OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nSaved {len(rows)} rows to: {OUTPUT_CSV}")

from collections import Counter
cats = Counter(r["category"] for r in rows)
print("\nCategory breakdown:")
for cat, count in cats.most_common():
    print(f"  {cat}: {count}")

prices = [float(r["final_price"]) for r in rows if r["final_price"]]
if prices:
    print(f"\nPrice range: {min(prices):.0f} - {max(prices):.0f} EGP")
