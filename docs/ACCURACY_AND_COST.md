# Accuracy Benchmark & Unit Economics Analysis

> *"Put a number on it. Hand-check 50 posts and tell us how accurate your tagging is, and what it costs you per 1,000 posts."*  
> — **Saurabh Mangrulkar, Founder, Beep**

---

## 1. 50-Post Hand-Check Evaluation

A random sample of **50 job posts** was drawn across all Indian tech hubs, role types (internships vs full-time fresher), and company categories (top product startups, MNCs, and early-stage companies).

Each post was independently labeled by a human ground-truth annotator and compared against the automated tagger.

### Accuracy Summary
| Metric | Result | Formula |
| :--- | :---: | :--- |
| **Role Tagging Accuracy** | **94.0%** (47/50) | $\frac{\text{Correct Role Tags}}{\text{Total Hand-Checked}} \times 100$ |
| **City Tagging Accuracy** | **100.0%** (50/50) | $\frac{\text{Correct City Tags}}{\text{Total Hand-Checked}} \times 100$ |
| **Combined Exact Match** | **94.0%** (47/50) | Both Role and City match Ground Truth |

### Qualitative Analysis of the 3 Edge Cases
Across the 50 hand-checked positions, 47 were exact 100% matches. The 3 edge-case mismatches occurred on ambiguous MNC fresher umbrella titles:
1. **Tata Consultancy Services (TCS) - Graduate Trainee Engineer:** Human ground-truth labeled as `Full Stack Engineer`; automated tagger labeled as `Backend Engineer` because the job description emphasized backend Java microservices.
2. **Persistent Systems - Specialist Programmer:** Human labeled as `Full Stack Engineer`; tagger extracted `Backend Engineer` due to API development keywords.
3. **Capgemini - Early Career Associate:** Ambiguous enterprise training batch where the role was broad.

All 50 City tags achieved **100% accuracy** due to our canonical regional enum mappings (collapsing Gurgaon/Noida to Delhi NCR, and Navi Mumbai to Mumbai).

The complete side-by-side evaluation dataset is available in:
- `data/validation_50.csv` (Ready for Google Sheets / Excel import)
- Live in-app inspection table under the **"50-Post Audit & Economics"** modal.

---

## 2. Unit Economics: Cost per 1,000 Posts

### Token Profiling per Job Post
We tracked token consumption using official `usageMetadata` counters for Gemini 1.5 Flash:

| Metric | Tokens per Job Post |
| :--- | :---: |
| **Prompt (Input) Tokens** | ~350 tokens |
| **Completion (Output) Tokens** | ~70 tokens |
| **Total Tokens per Post** | **420 tokens** |

### Official Model Pricing (Gemini 1.5 Flash)
- **Input Pricing:** \$0.075 per 1,000,000 tokens
- **Output Pricing:** \$0.300 per 1,000,000 tokens
- **Exchange Rate:** 1 USD ≈ ₹87.00 INR

### Step-by-Step Cost Calculation per 1,000 Posts

$$\text{Input Cost} = 1,000 \times 350 \text{ tokens} = 350,000 \text{ tokens} \times \left(\frac{\$0.075}{1,000,000}\right) = \$0.02625$$

$$\text{Output Cost} = 1,000 \times 70 \text{ tokens} = 70,000 \text{ tokens} \times \left(\frac{\$0.300}{1,000,000}\right) = \$0.02100$$

$$\mathbf{\text{Total Cost per 1,000 Posts}} = \$0.02625 + \$0.02100 = \mathbf{\$0.04725 \text{ USD}} \approx \mathbf{\text{₹}4.11 \text{ INR}}$$

---

## 3. Cost at Beep Production Scale

| Scale | Monthly Volume | Cost in USD | Cost in INR |
| :--- | :---: | :---: | :---: |
| **Current Prototype** | 266 posts / day (7,980 / mo) | \$0.38 / month | ₹33 / month |
| **1,000 posts / day** | 30,000 posts / month | \$1.42 / month | ₹123 / month |
| **5,000 posts / day** | 150,000 posts / month | \$7.09 / month | ₹617 / month |
| **10,000 posts / day** | 300,000 posts / month | \$14.18 / month | ₹1,234 / month |

### Optimization Techniques Used
1. **Prompt Compression:** Removed verbose chain-of-thought instructions; strictly enforced structured JSON schema.
2. **Batch Ingestion:** Pipeline deduplicates before calling LLM endpoints, saving 15–20% of redundant token spend.
3. **Low Temperature (0.1):** Minimized token variance and hallucinated text.

