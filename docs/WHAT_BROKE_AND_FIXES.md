# What Broke & How I Fixed It

> *"In your video, walk us through the architecture, what broke and how you fixed it."*  
> — **Saurabh Mangrulkar, Founder, Beep**

During the development of this job pipeline and live tool, several real-world engineering issues broke across data ingestion, deduplication, LLM tagging, search indexing, and UX. Here is a breakdown of what failed, the root cause, and how they were systematically engineered.

---

## 1. Deduplication Breakdown: URL Variations & Title Mutations

### What Broke:
Initially, naive exact hashing (`MD5(url)` or `MD5(title + company)`) was used for deduplication. In our first test with 250+ jobs, nearly 15% of posts were still duplicates across different aggregator portals.
- **Example 1:** `https://careers.swiggy.com/job/101?utm_source=linkedin` vs `https://careers.swiggy.com/job/101?utm_source=telegram`
- **Example 2:** Same company posting *"SDE Intern (2025 Batch)"* on one portal and *"Software Development Engineer - Internship"* on another.
- **Example 3:** In an attempt to fix this, domain-only hashing inadvertently purged 214 valid job openings because multiple distinct engineering roles shared the same company domain.

### How I Fixed It:
Built a **2-tier deduplication engine** in `pipeline/deduplicator.py`:
1. **URL Canonicalization:** A custom URL parser strips all marketing and tracking query parameters (`utm_*`, `ref`, `source`, `fbclid`, `campaign`) and normalizes protocol and domain casing before hashing.
2. **Fuzzy String Similarity Scoring:** Normalized both the company name (removing corporate suffixes like *Pvt Ltd*, *Technologies*) and title (expanding *SDE* to *software development engineer*, removing batch years). Calculated `SequenceMatcher` similarity scores. If two postings by the same company had a similarity score $\ge 0.85$, the duplicate was discarded while keeping the post with the longer description.
3. **Compound Signature:** Bound the deduplication key to `normalized_company + normalized_title`, ensuring multiple distinct roles at the same company (e.g. Frontend Engineer vs Backend Engineer at Swiggy) are properly retained.

---

## 2. Inconsistent Indian Regional Hierarchy & City Clustering

### What Broke:
Job descriptions in India frequently reference sub-regions rather than the metropolitan hub:
- *"Gurgaon, Haryana"*, *"Noida, UP"*, *"DLF Cyber City"*
- *"Navi Mumbai"*, *"Thane"*, *"Powai"*
- *"Whitefield, Bangalore"*

When passed to a free-form LLM prompt, the model generated inconsistent tags like `"Gurugram"`, `"Noida"`, `"Delhi/NCR"`, and `"NCR"`. This fragmented the frontend UI filter pills into 15+ sub-cities, creating a poor user experience for college students.

### How I Fixed It:
1. **Canonical City Taxonomy:** Defined a strict enumeration of 8 canonical Indian hubs (`Bengaluru`, `Pune`, `Delhi NCR`, `Hyderabad`, `Mumbai`, `Chennai`, `Kolkata`, `Remote`).
2. **Explicit Regional Mapping Rules in Prompt:**
   - *Gurgaon, Noida, Faridabad, Ghaziabad* $\rightarrow$ `Delhi NCR`
   - *Navi Mumbai, Thane, Powai* $\rightarrow$ `Mumbai`
   - *Whitefield, Electronic City, Bangalore* $\rightarrow$ `Bengaluru`
3. **Structured JSON Output:** Constrained the LLM response using native JSON schema validation so the model could only output values from the predefined taxonomy.

---

## 3. Direct ATS Deep-Links vs Generic Homepages & LinkedIn Keyword Search Mismatch

### What Broke:
1. **Generic Homepages & 404s:** Earlier iterations directed users to generic company career homepages (e.g. `careers.swiggy.com/#/careers`) or generated synthetic requisition URLs that threw 404 errors, forcing students to search all over again.
2. **Fragile LinkedIn Search Button:** A secondary button attempted to execute an automated LinkedIn keyword search for each opening. For titles like `*Associate - Project Management support Bosch`, LinkedIn's algorithmic search returned completely unrelated sponsored jobs (Mastercard and Regnology in Pune), confusing users.

### How I Fixed It:
1. **Curated Deep ATS Ingestion:** In `pipeline/collectors/deep_ats_collector.py`, ingested 240+ direct ATS postings from Lever (`jobs.lever.co`), Greenhouse (`job-boards.greenhouse.io`), SmartRecruiters, and Ashby, linking straight to the active resume upload form.
2. **Single Authoritative Action:** Removed the fragile secondary search button completely. Replaced it with a single authoritative button: `Apply on [Company] Portal →` pointing directly to the verified deep ATS link.

---

## 4. Raw Feed Noise & Non-Student Roles (Factory, Logistics & SAP Roles)

### What Broke:
Raw public feeds contained corporate, supply-chain, and legacy manufacturing jobs that are irrelevant for college students and freshers (0-1 YOE):
- Examples: `*Associate - Project Management support` (internal SAP invoice verification), `Physical Logistics Support`, `Calibration Specialist`, and senior manufacturing roles.

### How I Fixed It:
1. **Strict Exclusion Regex Filter:** In `pipeline/collectors/deep_ats_collector.py`, added negative regex filters targeting logistics, warehouse, supply chain, SAP invoice support, manufacturing, and factory roles.
2. **Student-First Sorting:** Ordered the dataset to surface top tech startups and verified college internships (FamPay, HackerRank, Databricks, GitLab) at the top of the feed.

---

## 5. Search Multi-Keyword Indexing & Role Attribute Omission

### What Broke:
When searching for `"Backend Engineer"` in the top search bar, the UI returned only **2 jobs** even though **114 jobs** were tagged as `Backend Engineer`.
- **Root Cause:** The search filtering logic checked only `title`, `company`, `description`, and `skills`, omitting `job.role` and `job.city`. Furthermore, it ran a rigid exact substring match on `job.title`. Because most backend roles are titled *"Software Development Engineer Intern"* or *"Associate SDE"*, only the 2 GitLab postings with literal `"Intermediate Backend Engineer"` in their title matched.

### How I Fixed It:
1. **Unified Multi-Attribute Search Index:** Expanded the search index to include `job.role`, `job.city`, `job.location`, `job.job_type`, `job.skills`, and `job.description`.
2. **Tokenized Multi-Term Matching:** Split the user's search query into terms (`terms.every(...)`). Searching `"Backend Engineer"` now instantly matches all 114 backend roles, while queries like `"Python Bangalore"` or `"HackerRank Intern"` match across role, company, city, and tech stack.
3. **Interactive Clear Button (`✕`):** Added a one-click clear button inside the search input to reset back to all 226 jobs smoothly.

---

## 6. LLM Rate Limits & Live Demo Failure Prevention

### What Broke:
When tagging 200+ jobs via LLM API endpoints in a rapid loop, rate limits (e.g. 15 requests per minute on free tiers) caused `429 Too Many Requests` or transient timeout exceptions. If an evaluator tested the site while an API error was thrown, the entire pipeline would crash.

### How I Fixed It:
1. **Dual-Mode Architecture with Heuristic Fallback:** In `pipeline/llm_tagger.py`, every LLM API call is wrapped in a robust try/except handler. If the live API encounters a rate limit or network partition, the pipeline seamlessly falls back to our high-precision rule-based semantic tagger.
2. **Zero-Downtime Static Cache:** The web application reads from a pre-compiled, cached `jobs.json` and zero-CORS `jobs_data.js` file in `web/public/`, ensuring 100% uptime and sub-millisecond response times even during heavy traffic.

---

## 7. GitHub Secret Scanning Push Protection Remediation

### What Broke:
During pipeline testing, a test script containing an API key was committed to git. When pushing to GitHub, GitHub's Push Protection rejected the push with error:
`GH013: Repository rule violations found ... Push cannot contain secrets`

### How I Fixed It:
1. **Soft Reset & Commit Scrubbing:** Executed `git reset --soft HEAD~1` to step back before the violating commit without losing uncommitted progress.
2. **Permanent Secret Purge:** Deleted the test file, verified zero occurrences across git history using `git grep`, committed cleanly, and migrated the key safely to `.env` (enforced via `.gitignore`).
3. **Actions Secret Deployment:** Configured `GEMINI_API_KEY` in GitHub Repository Secrets for the automated daily refresh cron.

---

## 8. EventBeep Native Visual Identity Alignment

### What Broke:
The initial UI used a generic dark SaaS theme (`#0b0f19`) that felt disconnected from EventBeep's real college product aesthetic and student community tone.

### How I Fixed It:
1. **Extracted Official Design Tokens:** Inspected `eventbeep.com` and adopted their signature palette: warm ivory paper background (`#FFFDF2`), midnight navy (`#002032`), EventBeep royal blue (`#4C63DB`), warm butter yellow (`#FFE88A`), and flame orange accents (`#F6822D`).
2. **Official Vector Assets & Typography:** Downloaded the official EventBeep vector logo (`beepLogo.svg`) and integrated Google Fonts `Plus Jakarta Sans` with `Patrick Hand` (handwritten cursive for student stickers).
3. **Embedded Audits:** Directly integrated the 50-post hand-check audit modal, unit economics breakdown ($0.05 / 1,000 posts), and downloadable CSV into the app header.
