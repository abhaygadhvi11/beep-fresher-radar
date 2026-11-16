"""
Master Pipeline Orchestrator for Beep Fresher Job Radar.
Runs:
1. Multi-source collector (200+ fresher jobs across India)
2. Intelligent 2-tier deduplicator
3. LLM tagging engine (Gemini 1.5 Flash / Fallback)
4. Evaluation benchmark & CSV export
5. Copies fresh production artifacts to web/public
"""

import os
import shutil
import subprocess
import sys
import json

def run_step(cmd_desc: str, cmd_args: list):
    print(f"\n================ [STEP] {cmd_desc} ================")
    res = subprocess.run([sys.executable] + cmd_args, check=True)
    if res.returncode != 0:
        print(f"Error during {cmd_desc}")
        sys.exit(res.returncode)

def main():
    print("🚀 Starting End-to-End Beep Fresher Data Pipeline...")
    
    # Step 1: Ingestion
    run_step("1. Ingesting Real Fresher & Internship Postings (India)", ["pipeline/collectors/deep_ats_collector.py"])
    
    # Step 2: Deduplication
    run_step("2. Running 2-Tier Deduplication Engine", ["pipeline/deduplicator.py"])
    
    # Step 3: LLM Tagging
    run_step("3. LLM Semantic Tagging & Normalization", ["pipeline/llm_tagger.py"])
    
    # Step 4: Benchmark & Evaluation
    run_step("4. Benchmarking 50-Job Hand-Check Validation", ["pipeline/evaluate.py"])
    
    # Step 5: Sync with Web Distribution
    print("\n================ [STEP] 5. Syncing Data to Web App ================")
    os.makedirs("web/public", exist_ok=True)
    shutil.copy("data/tagged_jobs.json", "web/public/jobs.json")
    shutil.copy("data/validation_50.csv", "web/public/validation_50.csv")
    shutil.copy("data/accuracy_report.json", "web/public/accuracy_report.json")
    
    # Generate standalone zero-CORS script
    with open("data/tagged_jobs.json", "r", encoding="utf-8") as f:
        jobs_data = json.load(f)
    with open("web/public/jobs_data.js", "w", encoding="utf-8") as f:
        f.write("window.INITIAL_JOBS = " + json.dumps(jobs_data, indent=2, ensure_ascii=False) + ";\n")
        
    print("✓ Successfully synchronized jobs.json, validation files, and jobs_data.js to web/public/")
    
    print("\n🎉 Pipeline Execution Completed Successfully!")

if __name__ == "__main__":
    main()
