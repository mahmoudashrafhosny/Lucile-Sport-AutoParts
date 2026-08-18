import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import re

headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get('https://tawfiqia.com/ar/shop?category=belts', headers=headers, timeout=15)
html = r.text

pos = html.find('OPTIBELT سير مشرشر مرسيدس بينز W123')
if pos != -1:
    print(html[pos-100:pos+800])
