import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en;q=0.9',
}

url = 'https://tawfiqia.com/ar/shop?category=spare-parts'
r = requests.get(url, headers=headers, timeout=15)
print("Status:", r.status_code, "Length:", len(r.text))

# Check for product links
links = set(re.findall(r'href=[\'"]([^\'"]*(?:product|spare-parts|item)[^\'"]*)[\'"]', r.text, re.I))
print(f"Found {len(links)} related links. Sample:")
for l in list(links)[:10]:
    print("  ", l)

# Check for HTML cards with price and title
# Let's find patterns like <h3 or <h4 or <a with title
titles = re.findall(r'<a[^>]*href=[\'"]([^\'"]*/ar/[^\'"]+)[\'"][^>]*>([^<]{10,80})</a>', r.text)
print(f"\nFound {len(titles)} candidate title links. Sample:")
for href, text in titles[:10]:
    t = text.strip()
    if t and not t.startswith('<'):
        print(f"   [{t}] -> {href}")

# Check for ld+json
ld = re.findall(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', r.text, re.DOTALL)
print(f"\nFound {len(ld)} ld+json blocks")
for b in ld:
    try:
        d = json.loads(b.strip())
        print("  LD+JSON:", d.get('@type') if isinstance(d, dict) else [x.get('@type') for x in d if isinstance(x, dict)])
    except Exception as e:
        print("  LD+JSON error:", e)
