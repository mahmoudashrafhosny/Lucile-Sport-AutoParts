import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import re

# 1. Parse Tawfiqia sample HTML
with open('scratch/tawfiqia_sample.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("Tawfiqia HTML length:", len(html))

# Let's find product blocks or cards
# Look for links containing /product/ or /ar/product/
prod_links = set(re.findall(r'href=[\'"]([^\'"]*(?:/product/|/item/)[^\'"]*)[\'"]', html))
print(f"Found {len(prod_links)} product links:")
for l in list(prod_links)[:10]:
    print("  ", l)

# Look for ld+json in Tawfiqia
ld_taw = re.findall(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', html, re.DOTALL)
print(f"\nFound {len(ld_taw)} LD+JSON blocks in Tawfiqia")
for idx, b in enumerate(ld_taw):
    try:
        data = json.loads(b.strip())
        print(f"  Block {idx}: type={type(data)}, schema_type={data.get('@type') if isinstance(data, dict) else [d.get('@type') for d in data if isinstance(data, dict)]}")
    except Exception as e:
        print(f"  Block {idx} error:", e)

# Look for category links in Tawfiqia
cat_links = set(re.findall(r'href=[\'"](https://tawfiqia\.com/ar/shop\?[^\'"]+)[\'"]', html))
print(f"\nFound {len(cat_links)} shop category links in Tawfiqia:")
for c in list(cat_links)[:10]:
    print("  ", c)
