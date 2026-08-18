import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en;q=0.9',
}

CATEGORIES = [
    'ac-and-cooling-system', 'accessories-car-care', 'bearings', 'belts',
    'bosch-offers', 'brake-discs-offers', 'brakes-fluid', 'car-care',
    'coolant-fluid', 'electronics', 'engine-cleaner', 'engine-parts',
    'exterior', 'filters', 'fluids', 'fresheners-and-car-perfumes',
    'interior', 'maintenance-packages', 'motor-oil-offers',
    'performance-additives', 'power-steering-fluid', 'shock-absorber-offers',
    'spare-parts', 'suspension-and-brakes', 'transmission-fluid',
    'tyres-rims', 'wiper-blade'
]

def scrape_tawfiqia_category(cat: str):
    products = []
    page = 1
    while page <= 10:  # check up to 10 pages per category
        url = f"https://tawfiqia.com/ar/shop?category={cat}&page={page}"
        try:
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code != 200:
                break
            html = r.text
            
            # Find product cards
            # Pattern for product title & link: <h2 class="title"><a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a></h2>
            items = re.findall(
                r'<img[^>]+src="(?P<img>[^"]+)"[^>]*alt="(?P<alt>[^"]*)"[\s\S]*?'
                r'<h2 class="title"><a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a></h2>[\s\S]*?'
                r'<div class="price">[\s\S]*?(?:EGP|ج\.م)?\s*&nbsp;(?P<price>[\d,\.]+)',
                html
            )
            if not items:
                # Try broader pattern if layout differs
                items = re.findall(
                    r'<h2 class="title"><a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a></h2>[\s\S]*?'
                    r'<div class="price">[\s\S]*?(?:EGP|ج\.م)?\s*&nbsp;(?P<price>[\d,\.]+)',
                    html
                )
                if not items:
                    break
                items = [("", "", url, title, price) for url, title, price in items]
            
            new_count = 0
            for item in items:
                img, alt, purl, title, price_str = item
                price_clean = re.sub(r'[^\d\.]', '', price_str)
                try:
                    price_val = float(price_clean)
                except ValueError:
                    continue
                
                if price_val <= 0:
                    continue
                
                products.append({
                    "title": title.strip(),
                    "price": price_val,
                    "image_url": img if img.startswith('http') else f"https://tawfiqia.com{img}" if img else "",
                    "product_url": purl if purl.startswith('http') else f"https://tawfiqia.com{purl}",
                    "category": cat,
                    "source": "Tawfiqia"
                })
                new_count += 1
                
            if new_count == 0:
                break
            page += 1
        except Exception as e:
            print(f"Error on {cat} p{page}: {e}")
            break
            
    return cat, products

print("Testing Tawfiqia scraping across all 27 categories concurrently...")
all_tawfiqia = []
with ThreadPoolExecutor(max_workers=8) as pool:
    futures = [pool.submit(scrape_tawfiqia_category, cat) for cat in CATEGORIES]
    for fut in as_completed(futures):
        cat, prods = fut.result()
        print(f"  Category '{cat}': {len(prods)} products")
        all_tawfiqia.extend(prods)

print(f"\nTotal Tawfiqia products extracted: {len(all_tawfiqia)}")
if all_tawfiqia:
    print("Sample:", all_tawfiqia[0])
