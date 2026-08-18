import requests
import re
import xml.etree.ElementTree as ET

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

print("=== AUTOSPARE SITEMAP PROBE ===")
try:
    r = requests.get('https://autospare.com.eg/sitemap.xml', headers=headers, timeout=10)
    print("Sitemap status:", r.status_code)
    # Check for sub-sitemaps (e.g. sitemap-products.xml or similar)
    urls = re.findall(r'<loc>(https://[^<]+)</loc>', r.text)
    print(f"Found {len(urls)} URLs in sitemap. Sample:")
    for u in urls[:10]:
        print("  ", u)
except Exception as e:
    print("Autospare error:", e)

print("\n=== TAWFIQIA PROBE ===")
try:
    r2 = requests.get('https://tawfiqia.com/ar', headers=headers, timeout=10)
    print("Tawfiqia homepage status:", r2.status_code)
    links = re.findall(r'href=[\'"](https://tawfiqia\.com/ar/[^\'"]+)[\'"]', r2.text)
    unique_links = list(set(links))
    print(f"Found {len(unique_links)} links on homepage. Sample:")
    for l in unique_links[:15]:
        print("  ", l)
except Exception as e:
    print("Tawfiqia error:", e)
