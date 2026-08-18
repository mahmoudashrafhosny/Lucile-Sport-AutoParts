import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import re

headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get('https://tawfiqia.com/ar/categories', headers=headers, timeout=15)
cats = set(re.findall(r'href=[\'"]https://tawfiqia\.com/ar/shop\?category=([^\'"]+)[\'"]', r.text))
print(f"Found {len(cats)} categories on Tawfiqia:")
for c in sorted(cats):
    print("  ", c)
