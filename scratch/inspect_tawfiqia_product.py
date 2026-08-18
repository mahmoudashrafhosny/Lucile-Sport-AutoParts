import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import re
import urllib.parse

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en;q=0.9',
}

url = 'https://tawfiqia.com/ar/product-detail/optibelt-%D8%B3%D9%8A%D8%B1-%D9%83%D8%A7%D8%AA%D9%8A%D9%86%D8%A9-136-%D8%B9%D9%82%D9%84%D8%A9-%D9%84%D8%A7%D8%AF%D8%A7-2110/11115'
r = requests.get(url, headers=headers, timeout=15)
print("Product page status:", r.status_code)

# Check title
h1 = re.findall(r'<h1[^>]*>([^<]+)</h1>', r.text)
print("H1 Title:", h1)

# Check price
prices = re.findall(r'(\d[\d,\.]*)\s*(?:ج\.م|EGP|جنيه)', r.text)
print("Prices in page:", prices)

# Check description
desc = re.findall(r'class=[\'"][^\'"]*description[^\'"]*[\'"][^>]*>(.*?)</div', r.text, re.DOTALL)
if desc:
    print("Description snippet:", re.sub(r'<[^>]+>', ' ', desc[0])[:200])

# Check images
imgs = re.findall(r'src=[\'"]([^\'"]*(?:product|upload)[^\'"]*)[\'"]', r.text)
print("Images found:", imgs[:3])
