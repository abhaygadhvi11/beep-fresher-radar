"""
Smart Deduplication Engine for Job Posts.
Solves cross-source duplicate listings, tracking URL variations, and title mutations.

Deduplication Tiers:
1. URL Canonicalization (strip tracking params: utm_*, ref, source, etc.)
2. Exact Company + Normalized Title Hash
3. Fuzzy Similarity Scoring (SequenceMatcher on company + normalized role title)
"""

import re
import hashlib
from difflib import SequenceMatcher
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import List, Dict, Any, Tuple

def canonicalize_url(url: str) -> str:
    """Removes tracking query parameters (utm_*, ref, source, etc.) to normalize URLs."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        # Filter out common marketing/tracking parameters
        tracking_prefixes = ("utm_", "ref", "source", "fbclid", "gclid", "campaign", "trk")
        filtered_params = {
            k: v for k, v in query_params.items()
            if not any(k.lower().startswith(prefix) for prefix in tracking_prefixes)
        }
        # Sort keys for deterministic matching
        sorted_query = urlencode(sorted(filtered_params.items()), doseq=True)
        canonical = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower().rstrip("/"),
            parsed.path.rstrip("/"),
            parsed.params,
            sorted_query,
            ""  # drop fragments
        ))
        return canonical
    except Exception:
        return url.strip().lower()

def normalize_company(company: str) -> str:
    """Normalizes company names (e.g. 'Swiggy Technologies Pvt Ltd' -> 'swiggy')."""
    if not company:
        return ""
    comp = company.lower()
    # Strip common corporate suffixes
    comp = re.sub(r"\b(pvt|ltd|limited|technologies|inc|llc|india|solutions|corporation|corp)\b", "", comp)
    comp = re.sub(r"[^\w\s]", " ", comp)
    return " ".join(comp.split())

def normalize_title(title: str) -> str:
    """Normalizes job titles for fuzzy matching and deduplication."""
    if not title:
        return ""
    t = title.lower()
    # Common abbreviations
    t = re.sub(r"\bsde\b", "software development engineer", t)
    t = re.sub(r"\bse\b", "software engineer", t)
    t = re.sub(r"\bqa\b", "quality assurance", t)
    t = re.sub(r"\bml\b", "machine learning", t)
    t = re.sub(r"\bai\b", "artificial intelligence", t)
    # Remove batches/years e.g. 2024, 2025, 2026
    t = re.sub(r"\b202[3-7]\b", "", t)
    # Remove special punctuation
    t = re.sub(r"[^\w\s]", " ", t)
    return " ".join(t.split())

def compute_similarity(str1: str, str2: str) -> float:
    """Computes string similarity score between 0.0 and 1.0 using SequenceMatcher."""
    return SequenceMatcher(None, str1, str2).ratio()

def deduplicate_jobs(jobs: List[Dict[str, Any]], similarity_threshold: float = 0.85) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Deduplicates a list of job postings across all tiers.
    Deduplicates if:
    1. Exact canonical URL AND normalized title match
    2. Exact Company + Normalized Title Hash match
    3. Fuzzy Title Similarity >= similarity_threshold for the same company
    """
    seen_url_title_pairs = set()
    seen_exact_hashes = set()
    unique_jobs: List[Dict[str, Any]] = []
    
    url_duplicates = 0
    exact_duplicates = 0
    fuzzy_duplicates = 0

    for job in jobs:
        url = job.get("url", "")
        title = job.get("title", "")
        company = job.get("company", "")
        description = job.get("description", "")
        
        canon_url = canonicalize_url(url)
        norm_company = normalize_company(company)
        norm_title = normalize_title(title)

        # 1. Exact URL + Title Deduplication
        url_title_signature = f"{canon_url}::{norm_title}"
        if canon_url and url_title_signature in seen_url_title_pairs:
            url_duplicates += 1
            continue

        # 2. Exact Normalized Hash Deduplication (Company + Title)
        exact_signature = f"{norm_company}::{norm_title}"
        exact_hash = hashlib.sha256(exact_signature.encode("utf-8")).hexdigest()

        if exact_hash in seen_exact_hashes:
            exact_duplicates += 1
            continue

        # 3. Fuzzy Matching across existing unique jobs for the same company
        is_fuzzy_duplicate = False
        for idx, existing_job in enumerate(unique_jobs):
            existing_company = normalize_company(existing_job.get("company", ""))
            if norm_company == existing_company:
                existing_title = normalize_title(existing_job.get("title", ""))
                sim_score = compute_similarity(norm_title, existing_title)
                if sim_score >= similarity_threshold:
                    fuzzy_duplicates += 1
                    is_fuzzy_duplicate = True
                    # Retain the one with the richer description
                    if len(description) > len(existing_job.get("description", "")):
                        unique_jobs[idx] = job
                    break

        if is_fuzzy_duplicate:
            continue

        # If it passed all filters, keep it
        if canon_url:
            seen_url_title_pairs.add(url_title_signature)
        seen_exact_hashes.add(exact_hash)
        
        job_copy = dict(job)
        job_copy["canonical_url"] = canon_url
        job_copy["dedup_hash"] = exact_hash[:12]
        unique_jobs.append(job_copy)

    stats = {
        "raw_count": len(jobs),
        "unique_count": len(unique_jobs),
        "total_duplicates_removed": len(jobs) - len(unique_jobs),
        "breakdown": {
            "url_duplicates": url_duplicates,
            "exact_title_company_duplicates": exact_duplicates,
            "fuzzy_duplicates": fuzzy_duplicates
        }
    }

    return unique_jobs, stats

if __name__ == "__main__":
    import json
    import os

    input_path = "data/raw_jobs.json"
    if os.path.exists(input_path):
        with open(input_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        
        # Inject a few intentional duplicates to prove the deduplicator works
        test_data = list(raw_data)
        if len(test_data) > 2:
            # Duplicate 1: URL with extra tracking param
            dup_url = dict(test_data[0])
            dup_url["url"] = dup_url["url"] + "&utm_source=newsletter_blast"
            test_data.append(dup_url)
            
            # Duplicate 2: Fuzzy title variation for same company
            dup_fuzzy = dict(test_data[1])
            dup_fuzzy["title"] = dup_fuzzy["title"] + " (Immediate Joiner / 2025)"
            dup_fuzzy["url"] = "https://different-source.com/job/xyz"
            test_data.append(dup_fuzzy)

        unique_jobs, stats = deduplicate_jobs(test_data)
        
        print(f"--- Deduplication Report ---")
        print(f"Raw Input Jobs: {stats['raw_count']}")
        print(f"Unique Jobs Retained: {stats['unique_count']}")
        print(f"Duplicates Removed: {stats['total_duplicates_removed']}")
        print(f"  - Canonical URL duplicates: {stats['breakdown']['url_duplicates']}")
        print(f"  - Exact (Company + Title) duplicates: {stats['breakdown']['exact_title_company_duplicates']}")
        print(f"  - Fuzzy title match duplicates: {stats['breakdown']['fuzzy_duplicates']}")

        with open("data/deduplicated_jobs.json", "w", encoding="utf-8") as f:
            json.dump(unique_jobs, f, indent=2, ensure_ascii=False)
        print("Saved deduplicated jobs to data/deduplicated_jobs.json")

