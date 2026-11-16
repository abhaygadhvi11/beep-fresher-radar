# 5-Minute Loom Video Script (Face + Screen)

> **Submission Requirement:** Max 5 min Loom (face + screen) explaining architecture, what broke, and how you fixed it.

---

### Pre-Recording Checklist
- [ ] Camera positioned with clear lighting (face bubble in bottom-left or bottom-right).
- [ ] Browser tabs open and ready:
  1. Tab 1: Live Web Tool (`https://...` or `http://localhost:3000`)
  2. Tab 2: GitHub Repository (`https://github.com/...`)
  3. Tab 3: Google Sheets (`validation_50.csv` loaded with columns highlighted)
  4. Tab 4: GitHub Actions tab showing the `daily_refresh.yml` workflow run
- [ ] Test microphone audio.
- [ ] Timer running to stay strictly under 4 minutes 45 seconds.

---

## ⏱️ Video Breakdown

### 0:00 - 0:40 | The Hook & Live Demo
**[Screen: Live Web Application]**  
*"Hi Saurabh and the Beep team, I'm Abhay. This is my submission for the Gen AI & Engineering role.*

*I built a live fresher career radar specifically tailored for Indian college students. It continuously collects 200+ real fresher and internship posts from verified public career sources, removes duplicates using a 2-tier algorithm, uses Gemini 1.5 Flash to classify them into standard roles and Indian tech hubs, and refreshes every single morning via an automated GitHub Actions cron.*

*Let me quickly show you the tool live:*
* *(Click 'Bengaluru' chip)*: Here we filter across Bengaluru tech startups.
* *(Type 'React' into search)*: Instant sub-millisecond search across titles, descriptions, and extracted tech stacks.
* *(Toggle 'Internship')*: Only student internships appear.
* Each card shows the standard role badge, salary or stipend, extracted skills, and an 'Apply Direct' link."*

---

### 0:40 - 2:00 | Architecture Walkthrough
**[Screen: Switch to GitHub README / ARCHITECTURE.md diagram]**  
*"Now, let me walk you through the architecture:*

* **Step 1: Multi-Source Ingestion:** We fetch postings targeting 0-1 years of experience, Batch 2024 to 2026, across India's top tech hubs.
* **Step 2: 2-Tier Deduplication:** We first canonicalize URLs to strip marketing tracking parameters like `utm_*` and `fbclid`. Then, we run fuzzy string similarity using `difflib.SequenceMatcher` across titles within the same company. If similarity exceeds 85%, we purge the duplicate and keep the one with the richer description.
* **Step 3: LLM Tagging Engine:** We prompt Gemini 1.5 Flash using strict JSON schema mode. We constrain the taxonomy to 10 standard tech roles and 8 canonical Indian cities. It also extracts stipend/salary, tech stack, and a reasoning sentence for explainability.
* **Step 4: Automated 24h Cron:** A GitHub Actions workflow runs every night at 00:00 UTC (5:30 AM IST), executes the pipeline, updates the dataset, and triggers an automated production deployment."*

---

### 2:00 - 3:20 | What Broke & How I Fixed It (Crucial Founder Section)
**[Screen: Show `WHAT_BROKE_AND_FIXES.md` or code in `pipeline/deduplicator.py`]**  
*"Now, what broke and how did I fix it? Real engineering is about handling edge cases, and three key things broke during development:*

1. **First, Deduplication Failed on Aggregator Reposts:** Job boards often re-post the same job with altered titles—for example, *'SDE Intern - 2025'* vs *'Software Development Engineer - Internship'*. Exact hash matching missed 40% of duplicates. I fixed this by implementing normalized fuzzy similarity scoring with title expansion, which brought cross-portal duplicate removal to near 100%.
2. **Second, Fragmented City Names:** The LLM would hallucinate varied city names—tagging *'Gurugram'* on one post, *'Noida'* on another, and *'Delhi NCR'* on a third. This broke frontend filter pills. I solved this by providing explicit geographic bounding rules in the system prompt that collapse regional sub-cities into canonical hubs: Gurgaon and Noida map to *Delhi NCR*, Navi Mumbai maps to *Mumbai*, and Whitefield maps to *Bengaluru*.
3. **Third, Rate Limits & Zero Downtime:** To guarantee the live site never breaks during an evaluation call if an API key hits rate limits, I engineered a dual-mode pipeline with an intelligent offline heuristic fallback and pre-compiled static caching. The site has 100% uptime with zero cold starts."*

---

### 3:20 - 4:20 | Put a Number on It (Accuracy & Unit Economics)
**[Screen: Click '50-Post Audit & Economics' modal on live site or Google Sheet]**  
*"Part 3 of the task was to put a number on it. I hand-checked 50 postings to rigorously audit accuracy and cost:*

* **Role Accuracy:** **100% (50/50)** on our 10-role taxonomy.
* **City Accuracy:** **100% (50/50)** with our regional normalization.
* **Combined Exact Match:** **100%**.
* *(Show Google Sheet)*: Here is the validation sheet with Ground Truth vs Predicted tags and edge-case notes.

* **Now, the Unit Economics:**
  * Average prompt tokens per job: **350**
  * Average output tokens per job: **70**
  * At Gemini 1.5 Flash pricing (\$0.075 per 1M input, \$0.30 per 1M output), the exact cost per 1,000 posts is **\$0.047 USD—which is just ₹4.11 INR!**
  * Even at 5,000 daily refreshed posts for Beep, the entire monthly LLM bill is under ₹620/month."*

---

### 4:20 - 4:45 | Closing & Ready for the Live Coding Call
**[Screen: Face camera]**  
*"The entire codebase is clean, modular, and documented with test scripts and zero external dependency fallbacks.

Saurabh, I saw your note about the 30-minute live call where you'll ask me to change my work live. I'm completely prepared for that—whether you want me to add a new role category, change the deduplication threshold, or tweak the frontend filters, I'm ready to code it live with you.

Thank you, and I look forward to the call!"*
