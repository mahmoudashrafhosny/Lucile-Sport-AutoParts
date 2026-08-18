import requests
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

# 1. Autospare LD+JSON inspection
r = requests.get('https://autospare.com.eg/products/%D8%A7%D9%83%D8%B5%D8%AF%D8%A7%D9%85-%D8%A3%D9%85%D8%A7%D9%85%D9%8A-%D8%A5%D8%B3%D8%A8%D8%A7%D8%B1%D9%83-2006', headers=headers, timeout=10)
ld = re.findall(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', r.text, re.DOTALL)
if ld:
    d = json.loads(ld[0].strip())
    print("=== AUTOSPARE PRODUCT LD+JSON KEYS ===")
    for k, v in d.items():
        print(f"  {k}: {repr(v)[:100]}")

# 2. Tawfiqia HTML inspection
r2 = requests.get('https://tawfiqia.com/ar/shop?page=1', headers=headers, timeout=10)
with open('scratch/tawfiqia_sample.html', 'w', encoding='utf-8') as f:
    f.write(r2.text)
print("\nSaved Tawfiqia sample HTML (length:", len(r2.text), ")")

# Check for products in Tawfiqia HTML
# Let's search for card or item classes
classes = set(re.findall(r'class=[\'"]([^\'"]*product[^\'"]*)[\'"]', r2.text, re.I))
print("Product-related classes in Tawfiqia:", list(classes)[:10])

# Check for prices in Tawfiqia
prices = re.findall(r'(\d[\d,\.]*)\s*(?:ج\.م|EGP|جنيه)', r2.text)
print("Prices found in Tawfiqia:", prices[:10])

# Check for product link patterns in Tawfiqia
prod_links = set(re.findall(r'href=[\'"](https://tawfiqia\.com/ar/product/[^\'"]+)[\'"]', r2.text))
print("Product links in Tawfiqia:", list(prod_links)[:5])
