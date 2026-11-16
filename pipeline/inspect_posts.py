import urllib.request
import json

url = "https://raw.githubusercontent.com/vibhorsi3733/gen-ai-project/main/data/posts.json"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as res:
    posts = json.loads(res.read().decode("utf-8"))

print(f"Total posts: {len(posts)}")

by_company = {}
for p in posts:
    c = p.get("company", "")
    if c not in by_company:
        by_company[c] = []
    by_company[c].append(p)

for c, items in by_company.items():
    print(f"\nCompany: {c} ({len(items)} posts)")
    for it in items[:4]:
        loc = it.get('location', '')
        title = it.get('title', '')
        link = it.get('url', '')
        print(f"   - [{loc}] {title} -> {link}")
