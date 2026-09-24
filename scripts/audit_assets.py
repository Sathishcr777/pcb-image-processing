import os
import re
import urllib.request

base_url = 'http://localhost:8000'
html_files = [
    'server/static/index.html',
    'server/static/3d_view.html',
    'server/static/photometric_studio.html',
    'server/static/xray_studio.html',
    'server/static/photometric.html',
    'server/static/metrology.html',
    'server/static/analytics.html',
    'server/static/spc.html',
    'server/static/msa.html',
    'server/static/cfx.html',
    'server/static/audit.html',
    'server/static/presentation.html'
]

checked_urls = set()
broken = []

for hf in html_files:
    if not os.path.exists(hf):
        continue
    with open(hf, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # find src and href
    matches = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', content)
    for m in matches:
        if m.startswith('http') or m.startswith('//') or m.startswith('#') or m.startswith('data:') or m.startswith('mailto:'):
            continue
        # strip queries or hashes
        clean_m = m.split('?')[0].split('#')[0]
        if not clean_m:
            continue
        if clean_m.startswith('/'):
            test_url = base_url + clean_m
        else:
            test_url = base_url + '/static/' + clean_m
        
        if test_url in checked_urls:
            continue
        checked_urls.add(test_url)
        
        try:
            req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
            res = urllib.request.urlopen(req, timeout=2)
            if res.status != 200:
                broken.append((hf, m, res.status))
        except Exception as e:
            broken.append((hf, m, str(e)))
        print(f"Checked: {test_url}", flush=True)

print(f"Total local assets checked: {len(checked_urls)}")
print(f"Broken assets: {len(broken)}")
for b in broken:
    print("Broken:", b)
