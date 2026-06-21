import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
from app.agents.ats_scorer import run_ats_scorer
from app.agents.visa_analyzer import run_visa_analyzer
from app.agents.report_writer import run_report_writer
 
# Sample job description — paste a real one from Indeed for better results
SAMPLE_JD = """
Senior Software Engineer - Python / Cloud
Company: TechCorp Inc.
 
We are looking for a Senior Software Engineer with 4+ years of Python experience.
You will work on our cloud infrastructure using AWS, Docker, and Kubernetes.
 
Requirements:
- 4+ years Python
- Experience with AWS (EC2, S3, Lambda)
- Docker and Kubernetes
- PostgreSQL or similar database
- Strong communication skills
 
This position requires candidates to be authorized to work in the United States.
We do not offer visa sponsorship at this time.
"""
 
# Sample resume — paste your actual resume text here for real results
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
 
print("="*60)
print("Testing ATS Scorer...")
print("="*60)
ats = run_ats_scorer(SAMPLE_JD, SAMPLE_RESUME)
print(f"Score: {ats['score']} | Level: {ats['match_level']}")
print(f"Matching: {ats['matching_skills']}")
print(f"Missing:  {ats['missing_skills']}")
 
print()
print("="*60)
print("Testing Visa Analyzer...")
print("="*60)
visa = run_visa_analyzer(SAMPLE_JD)
print(f"Signal: {visa['visa_signal']} | Compatible: {visa['f1_opt_compatible']}")
print(f"Evidence: {visa['evidence']}")
 
print()
print("="*60)
print("Testing Report Writer...")
print("="*60)
report = run_report_writer(SAMPLE_JD, SAMPLE_RESUME, ats)
print(report)
print()
print("All agents working correctly!")
