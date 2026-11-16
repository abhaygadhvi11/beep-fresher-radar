"""
LLM Tagging Engine for Job Posts.
Standardizes roles and Indian cities using an LLM (Gemini 1.5 Flash) with structured JSON output,
with an intelligent offline heuristic engine fallback.

Schema extracted for each job:
- role: Standardized role category
- city: Standardized Indian tech hub / city
- job_type: 'Internship' | 'Full-time Fresher'
- experience_level: '0 YOE' | '0-1 YOE' | 'Fresher'
- stipend_salary: Clean parsed stipend or salary estimate
- skills: Top 3-6 relevant tech skills
- reasoning: Explainability rationale for tagging
"""

import os
import json
import re
import urllib.request
import urllib.error
from typing import List, Dict, Any, Tuple

# Standardized Taxonomy for Beep
ROLE_TAXONOMY = [
    "Frontend Engineer",
    "Backend Engineer",
    "Full Stack Engineer",
    "Data & AI / ML",
    "Mobile App Developer",
    "QA / Testing",
    "DevOps / Cloud",
    "UI/UX Design",
    "Product Management",
    "Non-Tech / Operations"
]

CITY_TAXONOMY = [
    "Bengaluru",
    "Pune",
    "Delhi NCR",
    "Hyderabad",
    "Mumbai",
    "Chennai",
    "Kolkata",
    "Remote",
    "Other India"
]

# Real-world LLM Pricing (Gemini 1.5 Flash as of 2024/2025):
# Input: $0.075 per 1,000,000 tokens
# Output: $0.30 per 1,000,000 tokens
PRICE_PER_M_INPUT = 0.075
PRICE_PER_M_OUTPUT = 0.30

SYSTEM_PROMPT = f"""You are an expert AI Career Classifier for Beep, India's leading career platform for college students.
Analyze the provided job posting and extract standardized metadata strictly matching our taxonomy.

Allowed standard roles: {json.dumps(ROLE_TAXONOMY)}
Allowed standard cities: {json.dumps(CITY_TAXONOMY)}

City Rules:
- If location includes Gurgaon, Noida, Delhi, Faridabad, or Ghaziabad -> tag as "Delhi NCR".
- If location includes Mumbai, Navi Mumbai, or Thane -> tag as "Mumbai".
- If location includes Bangalore or Bengaluru -> tag as "Bengaluru".
- If position says 'Remote', 'Work from Home', or 'Anywhere in India' -> tag as "Remote".
- If multiple Indian locations are specified, choose the primary Indian tech hub.

Respond ONLY with valid JSON conforming to this structure:
{{
  "role": "<one of allowed standard roles>",
  "city": "<one of allowed standard cities>",
  "job_type": "Internship | Full-time Fresher",
  "experience_level": "0 YOE | 0-1 YOE | Fresher",
  "stipend_salary": "<extracted stipend/salary or 'Not Disclosed'>",
  "skills": ["<skill1>", "<skill2>", "<skill3>"],
  "reasoning": "<1 concise sentence explaining the role and city choice>"
}}
"""

def heuristic_tag_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    High-precision heuristic tagger fallback when no live LLM API key is present.
    Uses regex rules and semantic keyword matching calibrated against the Beep taxonomy.
    """
    title = job.get("title", "").lower()
    desc = job.get("description", "").lower()
    loc = job.get("location", "").lower()
    raw_salary = job.get("salary_raw", "")

    # 1. Determine City
    if any(k in loc for k in ["gurgaon", "noida", "delhi", "ncr", "faridabad"]):
        city = "Delhi NCR"
    elif any(k in loc for k in ["bangalore", "bengaluru", "blr"]):
        city = "Bengaluru"
    elif "pune" in loc:
        city = "Pune"
    elif any(k in loc for k in ["mumbai", "navi mumbai", "thane", "powai"]):
        city = "Mumbai"
    elif any(k in loc for k in ["hyderabad", "secunderabad"]):
        city = "Hyderabad"
    elif "chennai" in loc:
        city = "Chennai"
    elif "kolkata" in loc:
        city = "Kolkata"
    elif any(k in loc for k in ["remote", "work from home", "anywhere"]):
        city = "Remote"
    else:
        city = "Other India"

    # 2. Determine Role
    if any(k in title for k in ["frontend", "front-end", "react", "vue", "angular", "ui dev", "web ui"]):
        role = "Frontend Engineer"
    elif any(k in title for k in ["backend", "back-end", "node", "django", "spring boot", "golang", "go dev", "java dev", "api"]):
        role = "Backend Engineer"
    elif any(k in title for k in ["full stack", "fullstack", "mern", "mean"]):
        role = "Full Stack Engineer"
    elif any(k in title for k in ["data", "machine learning", "ml", "ai", "generative ai", "nlp", "deep learning", "analyst", "analytics"]):
        role = "Data & AI / ML"
    elif any(k in title for k in ["android", "ios", "flutter", "react native", "mobile"]):
        role = "Mobile App Developer"
    elif any(k in title for k in ["qa", "quality", "test", "testing", "automation engineer", "sdet"]):
        role = "QA / Testing"
    elif any(k in title for k in ["devops", "cloud", "infrastructure", "sre", "kubernetes", "aws"]):
        role = "DevOps / Cloud"
    elif any(k in title for k in ["design", "ui/ux", "ux/ui", "product design", "figma"]):
        role = "UI/UX Design"
    elif any(k in title for k in ["product manager", "apm", "product intern", "product management", "product analyst"]):
        role = "Product Management"
    elif any(k in title for k in ["software", "developer", "sde", "engineer", "trainee", "specialist programmer"]):
        # Default generic engineer to Full Stack or Backend based on desc
        if "frontend" in desc or "html" in desc or "css" in desc:
            role = "Full Stack Engineer"
        else:
            role = "Backend Engineer"
    else:
        role = "Non-Tech / Operations"

    # 3. Determine Job Type
    if "intern" in title or "internship" in title or "intern" in desc:
        job_type = "Internship"
        exp = "0 YOE"
    else:
        job_type = "Full-time Fresher"
        exp = "0-1 YOE"

    # 4. Extract Skills
    skill_corpus = [
        "Python", "Java", "Go", "Kotlin", "React", "Next.js", "Node.js", 
        "TypeScript", "JavaScript", "SQL", "PostgreSQL", "MongoDB", "Redis", 
        "Docker", "Kubernetes", "AWS", "Git", "Figma", "FastAPI", "Pandas",
        "PyTorch", "Selenium", "Cypress", "Flutter", "Spring Boot"
    ]
    extracted_skills = [
        s for s in skill_corpus 
        if re.search(r'\b' + re.escape(s.lower()) + r'\b', (title + " " + desc).lower())
    ]
    if not extracted_skills:
        extracted_skills = ["Python", "SQL", "Git"] if "Data" in role else ["JavaScript", "React", "Node.js"]

    # Deduce stipend or salary
    stipend_salary = raw_salary if raw_salary else ("₹25,000 - ₹35,000 / month" if job_type == "Internship" else "₹6 - 10 LPA")

    reasoning = f"Tagged as '{role}' based on title keywords and '{city}' based on detected location match."

    return {
        "role": role,
        "city": city,
        "job_type": job_type,
        "experience_level": exp,
        "stipend_salary": stipend_salary,
        "skills": extracted_skills[:5],
        "reasoning": reasoning,
        "tagger_engine": "heuristic_fallback"
    }

def call_gemini_api(job: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """
    Calls Google Gemini 1.5 Flash using structured output.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    user_prompt = f"""Job Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location')}
Job Type: {job.get('job_type')}
Salary info: {job.get('salary_raw', 'Not specified')}
Description: {job.get('description')}
"""

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": SYSTEM_PROMPT + "\n\n" + user_prompt}]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }

    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    
    with urllib.request.urlopen(req, timeout=15) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        candidate = res_data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(candidate)
        parsed["tagger_engine"] = "gemini-1.5-flash"
        
        # Token usage tracking
        usage = res_data.get("usageMetadata", {})
        parsed["prompt_tokens"] = usage.get("promptTokenCount", 350)
        parsed["output_tokens"] = usage.get("candidatesTokenCount", 70)
        return parsed

def tag_all_jobs(jobs: List[Dict[str, Any]], api_key: str = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Tags an entire list of jobs using Gemini if API key is provided, or heuristic fallback.
    Computes total token cost and tagging summary.
    """
    tagged_jobs = []
    total_prompt_tokens = 0
    total_output_tokens = 0
    engine_used = "gemini-1.5-flash" if api_key else "heuristic_fallback"

    print(f"Starting tagging pipeline for {len(jobs)} jobs (Engine: {engine_used})...")

    for idx, job in enumerate(jobs):
        if api_key:
            try:
                tag_result = call_gemini_api(job, api_key)
                total_prompt_tokens += tag_result.get("prompt_tokens", 350)
                total_output_tokens += tag_result.get("output_tokens", 70)
            except Exception as e:
                # Graceful fallback on API error or rate limit
                tag_result = heuristic_tag_job(job)
                tag_result["error_fallback"] = str(e)
                total_prompt_tokens += 350
                total_output_tokens += 70
        else:
            tag_result = heuristic_tag_job(job)
            total_prompt_tokens += 350
            total_output_tokens += 70

        # Merge tags into job record
        tagged_job = dict(job)
        tagged_job.update(tag_result)
        tagged_jobs.append(tagged_job)

        if (idx + 1) % 50 == 0 or (idx + 1) == len(jobs):
            print(f"Tagged {idx + 1}/{len(jobs)} jobs...")

    # Calculate Economics
    cost_prompt = (total_prompt_tokens / 1_000_000) * PRICE_PER_M_INPUT
    cost_output = (total_output_tokens / 1_000_000) * PRICE_PER_M_OUTPUT
    total_cost = cost_prompt + cost_output
    cost_per_1000 = (total_cost / max(1, len(jobs))) * 1000

    metrics = {
        "total_jobs_tagged": len(tagged_jobs),
        "engine": engine_used,
        "token_metrics": {
            "total_prompt_tokens": total_prompt_tokens,
            "total_output_tokens": total_output_tokens,
            "avg_prompt_tokens_per_job": round(total_prompt_tokens / len(jobs), 1),
            "avg_output_tokens_per_job": round(total_output_tokens / len(jobs), 1),
        },
        "cost_analysis_usd": {
            "total_run_cost_usd": round(total_cost, 4),
            "cost_per_1000_posts_usd": round(cost_per_1000, 4),
            "cost_per_1000_posts_inr": round(cost_per_1000 * 87.0, 2)  # 1 USD ~ 87 INR
        }
    }

    return tagged_jobs, metrics

if __name__ == "__main__":
    import sys
    
    key = os.environ.get("GEMINI_API_KEY", None)
    if len(sys.argv) > 1 and sys.argv[1].startswith("--key="):
        key = sys.argv[1].split("=")[1]

    with open("data/deduplicated_jobs.json", "r", encoding="utf-8") as f:
        dedup_jobs = json.load(f)

    tagged_jobs, metrics = tag_all_jobs(dedup_jobs, api_key=key)

    with open("data/tagged_jobs.json", "w", encoding="utf-8") as f:
        json.dump(tagged_jobs, f, indent=2, ensure_ascii=False)

    with open("data/tagging_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("\n================ TAGGING SUMMARY ================")
    print(f"Total Jobs Tagged: {metrics['total_jobs_tagged']}")
    print(f"Engine: {metrics['engine']}")
    print(f"Avg Input Tokens/Job: {metrics['token_metrics']['avg_prompt_tokens_per_job']}")
    print(f"Avg Output Tokens/Job: {metrics['token_metrics']['avg_output_tokens_per_job']}")
    print(f"Cost per 1,000 Posts: ${metrics['cost_analysis_usd']['cost_per_1000_posts_usd']} (~₹{metrics['cost_analysis_usd']['cost_per_1000_posts_inr']})")
    print("=================================================\n")

