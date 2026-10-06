import os, re, requests

BASE = 'http://127.0.0.1:8000'
static_dir = 'server/static'
urls_to_test = set()

for root, _, files in os.walk(static_dir):
    for f in files:
        if f.endswith(('.html', '.js')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
                text = fh.read()
                matches = re.findall(r'[\'\"`](/(?:static|evaluation|server|api|cfx|metrics|audit)[^\'\"`\s\?]+)[\'\"`\?]', text)
                for m in matches:
                    if not any(m.endswith(c) for c in ['}', ')', ';', ',']):
                        urls_to_test.add(m)

print(f"Checking {len(urls_to_test)} distinct referenced static and API paths...")
missing = []
for u in sorted(urls_to_test):
    if '${' in u or '`' in u: continue
    try:
        r = requests.get(BASE + u, timeout=5)
        if r.status_code == 404:
            missing.append((u, r.status_code))
    except Exception as e:
        missing.append((u, str(e)))

if missing:
    print(f"WARNING: {len(missing)} URLs failed:")
    for m in missing:
        print(" ", m)
else:
    print("ALL static and API URLs referenced in frontend code loaded successfully (No 404s)!")
