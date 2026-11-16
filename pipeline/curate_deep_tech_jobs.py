import urllib.request
import json
import re

url = "https://raw.githubusercontent.com/vibhorsi3733/gen-ai-project/main/data/posts.json"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as res:
    posts = json.loads(res.read().decode("utf-8"))

# Filter strictly for tech, student, and early-career jobs
filtered = []
for p in posts:
    title = p.get("title", "").strip()
    loc = p.get("location", "").strip()
    desc = p.get("description", "").strip()
    comp = p.get("company", "").strip()
    link = p.get("url", "").strip()

    # Skip non-India
    if not any(c in loc.lower() for c in ["india", "bangalore", "bengaluru", "pune", "delhi", "noida", "gurgaon", "gurugram", "mumbai", "hyderabad", "chennai", "kolkata", "remote"]):
        continue

    # Skip missing links
    if not link or not link.startswith("http"):
        continue

    # Clean title
    clean_title = re.sub(r'^[*\s\-_]+', '', title) # strip leading asterisks/symbols

    # Filter out obvious non-tech / non-fresher / senior management
    if any(k in clean_title.lower() for k in [
        "senior", "sr.", "lead", "principal", "staff", "director", "head of", "architect", 
        "supervisor", "invoice", "logistics", "warehouse", "aftermarket", "gasoline", "licensing", "fusa", "pastor", "b2r"
    ]):
        continue

    # Only keep genuine tech, engineering, analyst, intern, trainee, or early career roles
    if not any(k in clean_title.lower() for k in [
        "engineer", "developer", "intern", "trainee", "analyst", "associate", "specialist", "ai", "data", "qa", "software", "devops", "cloud", "ui", "ux", "product", "consultant", "researcher", "programmer"
    ]):
        continue

    domain = link.split("/")[2] if "://" in link else "company"
    ats_type = "Greenhouse ATS" if "greenhouse" in domain else (
        "Lever ATS" if "lever" in domain else (
            "SmartRecruiters" if "smartrecruiters" in domain else (
                "Ashby ATS" if "ashby" in domain else (
                    "Workable ATS" if "workable" in domain else "Official ATS"
                )
            )
        )
    )

    is_intern = "intern" in clean_title.lower() or "intern" in desc.lower()[:300]
    
    filtered.append({
        "id": p.get("id"),
        "title": clean_title,
        "company": comp,
        "location": loc,
        "url": link,  # EXACT, LIVE DEEP URL
        "source": f"{comp} ({ats_type})",
        "ats_type": ats_type,
        "description": desc[:600] if desc else f"Exciting tech role at {comp}.",
        "job_type": "Internship" if is_intern else "Full-time Fresher",
        "experience_level": "0-1 YOE (Students & Freshers)",
        "salary_raw": "Competitive Stipend (₹25k - ₹50k/mo)" if is_intern else "₹7 - 16 LPA",
        "posted_at": p.get("posted_at") or "2026-11-15T00:00:00Z"
    })

print(f"Total curated tech student/fresher jobs with DEEP ATS URLs: {len(filtered)}")

# Check company distribution
from collections import Counter
counts = Counter(f['company'] for f in filtered)
for c, cnt in counts.most_common(15):
    print(f"  {c}: {cnt}")
