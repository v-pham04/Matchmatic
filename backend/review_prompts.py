"""
Week 4 prompt review session — run together on a call.

Usage:
  1. Paste 20 real job descriptions into SAMPLE_JDS below (10 US + 10 Vietnam).
  2. Paste your sample resume into SAMPLE_RESUME.
  3. Run: python review_prompts.py
  4. Grade each output: ATS score ±10, match level, report quality.
  5. Fix prompts in app/prompts/prompts.py and re-run until ≥17/20 feel correct.

Grading columns to fill in during the call:
  # | Title              | Expected | Actual Score | Match OK? | Report OK? | Notes
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.ats_scorer import run_ats_scorer
from app.agents.visa_analyzer import run_visa_analyzer
from app.agents.report_writer import run_report_writer

# Paste your actual resume text here
SAMPLE_RESUME = """
Victoria Nguyen — DevOps Engineer

Experience:
3 years as DevOps Engineer at StartupCo
- Deployed 12 microservices to AWS using Docker and Kubernetes
- Reduced deployment time by 40% using GitHub Actions CI/CD
- Managed PostgreSQL databases with 99.9% uptime
- Built monitoring with Grafana and Prometheus

Skills: Python, AWS, Docker, Kubernetes, PostgreSQL, GitHub Actions, Terraform
"""

# Paste 20 real JDs from Indeed (US) and TopCV (Vietnam).
# Replace the placeholder entries with full job description text.
SAMPLE_JDS: list[dict] = [
    {
        "id": 1,
        "title": "US — Strong match DevOps (placeholder)",
        "market": "us",
        "text": """
Senior DevOps Engineer — AWS / Kubernetes
Requirements: 3+ years Python, AWS, Docker, Kubernetes, CI/CD, PostgreSQL.
We offer visa sponsorship for qualified candidates.
""",
        "expected_level": "HIGH",
        "expected_score_range": (75, 95),
    },
    {
        "id": 2,
        "title": "US — Clearance / no sponsorship (placeholder)",
        "market": "us",
        "text": """
Software Engineer — Defense Contractor
Requires active Secret clearance. US citizenship required.
Must be authorized to work in the United States. No visa sponsorship.
""",
        "expected_level": "LOW",
        "expected_visa": "citizen_only",
    },
    {
        "id": 3,
        "title": "US — Marketing role wrong field (placeholder)",
        "market": "us",
        "text": """
Marketing Manager — B2B SaaS
5+ years digital marketing, SEO, content strategy, HubSpot, Salesforce.
""",
        "expected_level": "LOW",
        "expected_score_range": (0, 40),
    },
    # --- Add 2 more real JDs below (mix of US Indeed + Vietnam TopCV) ---
    {"id": 4,
     "title": "AWS DevOps Engineer", 
     "market": "us", 
     "text": "As the AWS DevOps Engineer, you will play a critical role in building and managing an automated DevOps release pipeline which delivers tooling for next generation application development efforts and on-going production operations. You will embrace and promote Continuous Integration/Continuous Delivery (CI/CD) mindset, ensuring efficient and reliable processes across the development lifecycle. Must be legally authorized to work in the United States without the need for employer sponsorship now or at any time in the future", 
     "expected_level": "?"},
    
    {"id": 5, 
     "title": "DevOps Engineer",
     "market": "us", 
     "text": "Minimum 3 years of work experience. Master proficiency in DevOps is required. Tech and relevant experience in the following: OpenShift, Linux Administration, Shell Scripting, Release. DevOps CI CD Tools Jenkins, Bitbucket, JFrog Artifactory, Ansible Tower, XL. Agile Cross team Collaboration. Role requires 60% onsite client work (3 days per week) in Charlotte, NC. Associate's degree", 
     "expected_level": "?"},
    
    {"id": 6,
     "title": "Full Stack Engineer (Java/Spring Boot)",
     "market": "vn", 
     "text": "Build and maintain backend services using Java and Spring Boot. Develop frontend features using React, Next.js, or modern web technologies. Design APIs, integrations, and business workflows. Build product features related to property discovery, lead management, CRM, and agent productivity. Explore and implement AI-powered capabilities such as recommendations, search, matching, and workflow automation. Participate in code reviews and technical discussions.",
     "expected_level": "?"},
]

def review_one(jd: dict) -> None:
    print("\n" + "=" * 70)
    print(f"#{jd['id']} {jd['title']} [{jd.get('market', '?')}]")
    print("=" * 70)

    if jd["text"].startswith("PASTE"):
        print("  SKIP — paste a real job description before running review")
        return

    ats = run_ats_scorer(jd["text"], SAMPLE_RESUME)
    print(f"  ATS Score: {ats['score']} | Level: {ats['match_level']}")
    print(f"  Matching: {ats['matching_skills']}")
    print(f"  Missing:  {ats['missing_skills']}")

    if jd.get("market") == "us":
        visa = run_visa_analyzer(jd["text"])
        print(f"  Visa: {visa['visa_signal']} | F1-OPT OK: {visa['f1_opt_compatible']}")
        print(f"  Evidence: {visa['evidence']}")
        if jd.get("expected_visa"):
            ok = visa["visa_signal"] == jd["expected_visa"]
            print(f"  Visa expected {jd['expected_visa']}: {'PASS' if ok else 'FAIL'}")

    report = run_report_writer(jd["text"], SAMPLE_RESUME, ats)
    print(f"\n  Report (first 400 chars):\n  {report[:400]}...")

    if jd.get("expected_level") and jd["expected_level"] != "?":
        level_ok = ats["match_level"] == jd["expected_level"]
        print(f"\n  Expected level {jd['expected_level']}: {'PASS' if level_ok else 'REVIEW'}")

    score_range = jd.get("expected_score_range")
    if score_range:
        lo, hi = score_range
        in_range = lo <= ats["score"] <= hi
        print(f"  Expected score {lo}-{hi}: {'PASS' if in_range else 'REVIEW'}")


def main() -> None:
    print("Week 4 Prompt Review — 5 Job Descriptions")
    print("Grade each output during your joint call. Target: 5/5 correct.\n")

    for jd in SAMPLE_JDS:
        review_one(jd)

    print("\n" + "=" * 70)
    print("Review complete. Update app/prompts/prompts.py for any FAIL/REVIEW cases.")
    print("Re-run this script until ≥17/20 pass your human grading.")
    print("=" * 70)


if __name__ == "__main__":
    main()
