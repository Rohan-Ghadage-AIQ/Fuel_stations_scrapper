from curl_cffi import requests
from bs4 import BeautifulSoup
import re

url = 'https://www.jiobp.com/locate-fuel-station'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
}
try:
    resp = requests.get(url, headers=headers, impersonate='chrome120', timeout=20)
    print("Status:", resp.status_code)
    
    html = resp.text
    with open('jio_locator.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    soup = BeautifulSoup(html, 'html.parser')
    apis = set()
    
    # Search for api urls in scripts
    for s in soup.find_all('script'):
        if s.string:
            for m in re.finditer(r'[\'\"`]\s*(https?://[^\'\"`]+(?:api|get|store|locator|pump|outlet)[^\'\"`]*)\s*[\'\"`]', s.string, re.I):
                apis.add(m.group(1))
            for m in re.finditer(r'[\'\"`]\s*(/[^\'\"`]+(?:api|get|store|locator|pump|outlet)[^\'\"`]*)\s*[\'\"`]', s.string, re.I):
                apis.add(m.group(1))
                
    # Search html elements for data-url, etc.
    for tag in soup.find_all(True):
        for attr, value in tag.attrs.items():
            if isinstance(value, str) and ('api' in value.lower() or 'locator' in value.lower() or 'pump' in value.lower()):
                if value.startswith('http') or value.startswith('/'):
                    apis.add(value)
                    
    print('\nFound potential API endpoints:')
    for a in apis:
        print(a)
except Exception as e:
    print('Error:', e)
