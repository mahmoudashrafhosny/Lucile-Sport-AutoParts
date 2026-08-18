import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import re

headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get('https://tawfiqia.com/ar/shop?category=belts', headers=headers, timeout=15)
html = r.text

# Let's print the first 2000 chars of a product card
pos = html.find('product-detail')
if pos != -1:
    print(html[pos-200:pos+1500])
