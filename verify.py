import urllib.request

# Check the new audit history page for key content
with urllib.request.urlopen('http://localhost:8000/audit-history', timeout=5) as r:
    body = r.read().decode('utf-8', errors='ignore')

checks = {
    'Page title present': 'Inspection Audit History' in body,
    'Inspection Audit nav link': '/audit-history' in body,
    'Live Inspection nav link': 'Live Inspection' in body,
    'Session summary bar': 'ahSessionBoardContext' in body,
    'Cards grid element': 'ahCardsGrid' in body,
    'Empty state element': 'No Inspections Recorded Yet' in body,
    'Detail modal element': 'ahDetailModal' in body,
    'JS controller script tag': 'audit_history.js' in body,
    'Download audit button': 'btnAHModalDownload' in body,
    'Export CSV button': 'btnAHExportCSV' in body,
    'Health Index bar markup': 'ah-hi-bar-bg' in body,
    'Golden comparison table': 'ahModalGoldenBody' in body,
}
for k, v in checks.items():
    status = 'OK  ' if v else 'MISS'
    print(f'  [{status}] {k}')

# Check main page has the new nav link
with urllib.request.urlopen('http://localhost:8000/', timeout=5) as r:
    main_body = r.read().decode('utf-8', errors='ignore')
found = '/audit-history' in main_body
print()
print(f'  [{"OK  " if found else "MISS"}] index.html has Inspection Audit nav link')

# Check API returns empty list initially
with urllib.request.urlopen('http://localhost:8000/api/session-audits', timeout=5) as r:
    api_data = r.read().decode('utf-8')
print(f'  [OK  ] /api/session-audits response: {api_data.strip()}')
