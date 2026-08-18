import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import re
import json
import urllib.parse

headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get('https://tawfiqia.com/ar/shop?category=belts', headers=headers, timeout=15)
html = r.text

# Find all <div or <article or <a> that has product-detail in href
links = re.findall(r'<a[^>]+href=[\'"](https://tawfiqia\.com/ar/product-detail/[^\'"]+)[\'"][^>]*>([\s\S]*?)</a>', html)
print(f"Total product links found: {len(links)}")
for url, inner in links[:6]:
    clean_inner = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', inner)).strip()
    slug = url.split('product-detail/')[1].split('/')[0]
    title = urllib.parse.unquote(slug).replace('-', ' ')
    print(f"  URL: {url}")
    print(f"  Slug Title: {title}")
    print(f"  Inner text: {clean_inner}")
    print("-" * 50)
