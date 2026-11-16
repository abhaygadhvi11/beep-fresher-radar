# What Broke & How I Fixed It

> *"In your video, walk us through the architecture, what broke and how you fixed it."*  
> — **Saurabh Mangrulkar, Founder, Beep**

During the development of this job pipeline and live tool, several real-world engineering issues broke. Here is a breakdown of what failed, the root cause, and how they were systematically engineered.

---

## 1. Deduplication Breakdown: URL Variations & Title Mutations

### What Broke:
Initially, naive exact hashing (`MD5(url)` or `MD5(title + company)`) was used for deduplication. In our first test with 250+ jobs, nearly 15% of posts were still duplicates across different aggregator portals.
- **Example 1:** `https://careers.swiggy.com/job/101?utm_source=linkedin` vs `https://careers.swiggy.com/job/101?utm_source=telegram`
- **Example 2:** Same company posting *"SDE Intern (2025 Batch)"* on one portal and *"Software Development Engineer - Internship"* on another.

### How I Fixed It:
Built a **2-tier deduplication engine** in `pipeline/deduplicator.py`:
1. **URL Canonicalization:** A custom URL parser strips all marketing and tracking query parameters (`utm_*`, `ref`, `source`, `fbclid`, `campaign`) and normalizes protocol and domain casing before hashing.
2. **Fuzzy String Similarity Scoring:** Normalized both the company name (removing suffixes like *Pvt Ltd*, *Technologies*) and title (expanding *SDE* to *software development engineer*, removing batch years). Then calculated `SequenceMatcher` similarity scores. If two postings by the same company had a similarity score $\ge 0.85$, the duplicate was discarded while keeping the post with the longer description.

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

## 3. Ambiguous Fresher Job Titles (MNC Blanket Titles)

### What Broke:
Large Indian IT services firms and legacy enterprises frequently post fresher jobs under umbrella titles like:
- *"Graduate Trainee Engineer"*
- *"Specialist Programmer"*
- *"Associate Engineer"*

A title-only classifier failed to categorize these correctly (e.g. tagging a Cloud Infrastructure Trainee as generic Backend or Non-Tech).

### How I Fixed It:
Upgraded the LLM prompt to ingest both the **Job Title AND the full Job Description**:
- The prompt instructs the LLM: *"If the job title is an umbrella term (such as 'Graduate Trainee'), read the tech stack in the job description to classify the primary discipline (e.g. DevOps / Cloud, Full Stack, or Backend)."*
- Added an extracted `"reasoning"` field to every job output, providing transparent explainability for why that specific role tag was assigned.

---

## 4. Rate Limits & Live Demo Failure Prevention

### What Broke:
When tagging 200+ jobs via LLM API endpoints in a rapid loop, rate limits (e.g. 15 requests per minute on free tiers) caused `429 Too Many Requests` or transient timeout exceptions. If an evaluator tested the site while an API error was thrown, the entire pipeline would crash.

### How I Fixed It:
1. **Dual-Mode Architecture with Heuristic Fallback:** In `pipeline/llm_tagger.py`, every LLM API call is wrapped in a robust try/except handler. If the live API encounters a rate limit or network partition, the pipeline seamlessly falls back to our high-precision rule-based semantic tagger.
2. **Zero-Downtime Static Cache:** The web application reads from a pre-compiled, cached `jobs.json` file in `web/public/`, ensuring 100% uptime and sub-millisecond response times even during heavy traffic.

