import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en;q=0.9',
}

r = requests.get('https://tawfiqia.com/ar/shop?category=belts', headers=headers, timeout=15)
html = r.text

# Let's find all product cards on the shop page
# Look for /product-detail/ links
matches = re.findall(r'<a[^>]*href=[\'"](https://tawfiqia\.com/ar/product-detail/[^\'"]+)[\'"][^>]*>([\s\S]*?)</a>', html)
print(f"Found {len(matches)} product-detail <a> blocks on category page")

# Let's inspect raw HTML chunks around product cards
cards = re.findall(r'<div[^>]*class=[\'"][^\'"]*product[^\'"]*[\'"][^>]*>([\s\S]*?)</div>\s*</div>', html)
print(f"Found {len(cards)} product card div blocks")

# Let's extract items from the page
items = []
# Match product blocks
blocks = re.findall(r'href=[\'"](https://tawfiqia\.com/ar/product-detail/([^\'/]+)/(\d+))[\'"][\s\S]*?(\d[\d,\.]*)\s*(?:ج\.م|EGP|جنيه)', html)
print(f"Found {len(blocks)} item matches with regex:")
for url, slug, pid, price in blocks[:5]:
    import urllib.parse
    title = urllib.parse.unquote(slug).replace('-', ' ')
    print(f"  ID: {pid} | Price: {price} EGP | Title: {title}")
