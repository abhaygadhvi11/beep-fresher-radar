import urllib.request
import json
import re

url = "https://raw.githubusercontent.com/vibhorsi3733/gen-ai-project/main/data/posts.json"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as res:
    posts = json.loads(res.read().decode("utf-8"))

print(f"Total raw posts in feed: {len(posts)}")

# Strict filters
fresher_candidates = []
excluded_senior = re.compile(r'\b(senior|sr\.|lead|principal|staff|director|head of|vp|architect|10\+|8\+|7\+)\b', re.I)

for p in posts:
    title = p.get("title", "").strip()
    loc = p.get("location", "").lower()
    desc = p.get("description", "")
    comp = p.get("company", "")
    link = p.get("url", "")

    # Location India
    if not any(c in loc for c in ["india", "bangalore", "bengaluru", "pune", "delhi", "noida", "gurgaon", "gurugram", "mumbai", "hyderabad", "chennai", "kolkata", "remote"]):
        continue

    # Must be valid deep link
    if not link or not link.startswith("http"):
        continue

    # Exclude obvious senior / staff / principal roles
    if excluded_senior.search(title):
        continue

    # Check if fresher / early career / intern or entry tech
    is_student_fresher = False
    
    # Check title keywords
    if any(k in title.lower() for k in ["intern", "internship", "fresher", "trainee", "associate", "graduate", "junior", "analyst", "engineer", "developer", "specialist", "coordinator", "fellow", "campus"]):
        is_student_fresher = True
    elif any(k in desc.lower()[:400] for k in ["intern", "internship", "fresher", "0-1", "0-2", "recent graduate", "college", "bachelor", "b.tech", "degree"]):
        is_student_fresher = True

    if is_student_fresher:
        fresher_candidates.append(p)

print(f"Filtered student/fresher/early-career jobs with DEEP ATS URLs: {len(fresher_candidates)}")

# Print 10 samples
for j in fresher_candidates[:12]:
    print(f"[{j.get('company')}] {j.get('title')}")
    print(f"   Location: {j.get('location')}")
    print(f"   URL: {j.get('url')}\n")

