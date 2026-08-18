import requests
import re
import json
import urllib.parse

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en;q=0.9',
}

print("--- PROBING AUTOSPARE PRODUCT PAGE ---")
sample_url = 'https://autospare.com.eg/products/' + urllib.parse.quote('اكصدام-أمامي-إسبارك-2006')
try:
    r = requests.get(sample_url, headers=headers, timeout=10)
    print("Status:", r.status_code)
    # Check for ld+json
    ld_jsons = re.findall(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', r.text, re.DOTALL)
    print(f"Found {len(ld_jsons)} ld+json blocks")
    for b in ld_jsons:
        try:
            data = json.loads(b.strip())
            print("LD+JSON data keys/type:", type(data), data.get("@type") if isinstance(data, dict) else [d.get("@type") for d in data if isinstance(d, dict)])
            if isinstance(data, dict) and data.get("@type") == "Product":
                print("Product LD+JSON:", json.dumps(data, ensure_ascii=False)[:300])
        except Exception as e:
            print("Error parsing LD+JSON:", e)
    
    # Check for price and title in HTML
    prices = re.findall(r'(\d[\d,\.]*)\s*(?:ج\.م|EGP|جنيه)', r.text)
    print("Regex prices found:", prices[:5])
except Exception as e:
    print("Autospare probe error:", e)

print("\n--- PROBING TAWFIQIA SHOP API / HTML ---")
try:
    # Check if Tawfiqia has an internal API or shop listing
    for url in [
        'https://tawfiqia.com/ar/shop?category=engine-parts',
        'https://tawfiqia.com/ar/shop?page=1',
        'https://tawfiqia.com/api/products',
        'https://tawfiqia.com/ar/api/products',
    ]:
        r = requests.get(url, headers=headers, timeout=10)
        print(url, "-> Status:", r.status_code, "Len:", len(r.text))
        if r.status_code == 200 and 'json' in r.headers.get('content-type', ''):
            print("JSON API FOUND!", r.text[:200])
        elif r.status_code == 200:
            # Check for product titles and prices
            titles = re.findall(r'class=[\'"][^\'"]*product[^\'"]*title[^\'"]*[\'"][^>]*>([^<]+)<', r.text, re.IGNORECASE)
            print(f"HTML product titles count: {len(titles)}")
            if titles:
                print("Sample titles:", titles[:3])
except Exception as e:
    print("Tawfiqia probe error:", e)
