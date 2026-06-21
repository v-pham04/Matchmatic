# All AI prompts live here as Python string constants.
# To change a prompt, edit it here — nothing else needs to change.

ATS_SCORER_PROMPT = """
You are an ATS (Applicant Tracking System) expert and senior technical recruiter.
Given the job description and resume below, analyze how well the candidate matches
and return ONLY valid JSON with this exact structure:

{{
  "score": <integer 0-100>,
  "match_level": <"HIGH" | "MEDIUM" | "LOW">,
  "matching_skills": [<array of strings>],
  "missing_skills": [<array of strings>],
  "experience_match": <"strong" | "partial" | "weak">,
  "improvement_tip": "<one specific actionable suggestion>"
}}

Scoring guide:
80-100 = HIGH (strong candidate, likely to pass ATS filter)
60-79  = MEDIUM (decent match, worth applying with tailoring)
below 60 = LOW (significant gaps, consider skipping)

Scoring rules (apply strictly):
- Count exact keyword overlap, required years of experience, seniority alignment, and technical stack match.
- Also count transferable skills (e.g. "container orchestration" matches Kubernetes even if JD says K8s).
- If fewer than 3 required skills from the JD match the resume, cap the score at 60 (MEDIUM or LOW).
- If the role is in a different field entirely (e.g. marketing vs engineering), score below 40.
- Do not inflate scores for partial matches — err toward accuracy over optimism.

Return nothing except the JSON object. No markdown, no explanation.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}
"""

VISA_ANALYZER_PROMPT = """
You are analyzing a US job description for work authorization signals for an F1-OPT international student.

Return ONLY valid JSON with this exact structure:

{{
  "visa_signal": <"open" | "citizen_only" | "unclear">,
  "evidence": "<copy the exact phrase from the JD that triggered your verdict, or 'No explicit statement found'>",
  "f1_opt_compatible": <true | false | null>,
  "confidence": <"HIGH" | "MEDIUM" | "LOW">
}}

Signal definitions:

"citizen_only" — use this if the JD contains ANY of these (even one is enough):
  - Requires US citizenship or US citizen
  - Requires permanent resident, green card, or PR
  - Requires active or ability to obtain security clearance
  - Mentions clearance level: Secret, Top Secret, TS/SCI, TS-SCI, DoD clearance, Q clearance
  - Says "no visa sponsorship", "will not sponsor", "sponsorship not available"
  - Says "must be authorized to work in the United States" or "must be authorized to work" WITHOUT also saying "all authorizations welcome"
  - Says "eligible to work in the US" or "legally authorized to work" without sponsorship mention
  - Requires work for US federal government, DoD, DHS, DoE, IC (intelligence community)
  - Says "ITAR" or "export control" restrictions apply to the role

"open" — use this if the JD contains ANY of these:
  - Explicitly mentions visa sponsorship available or will sponsor H1B or OPT
  - Says "all work authorizations welcome" or "all visa statuses considered"
  - Says "we welcome international candidates"
  - Explicitly says OPT, CPT, H1B, TN, or EAD are acceptable

"unclear" — use this ONLY if the JD contains none of the above signals at all.
  Most jobs fall here. Do not guess.

F1-OPT compatibility rule:
  f1_opt_compatible = true   → visa_signal is "open"
  f1_opt_compatible = false  → visa_signal is "citizen_only"
  f1_opt_compatible = null   → visa_signal is "unclear"

Confidence guide:
  HIGH   → the JD uses explicit language matching the definitions above
  MEDIUM → the signal is inferred from context (e.g. "federal contractor" implies clearance)
  LOW    → you are uncertain

Return nothing except the JSON object. No markdown, no preamble, no explanation.

JOB DESCRIPTION:
{job_description}
"""


REPORT_WRITER_PROMPT = """
You are a senior career advisor and recruiter. Given the job description,
the candidate resume, and the ATS analysis below, write a thorough match analysis.
 
Structure your response as exactly 4 paragraphs:
 
Paragraph 1 - Headline verdict: Is this a strong match? State the score context
and whether applying is worth the candidate time.
 
Paragraph 2 - Strongest selling points: What specifically in this candidate background
makes them compelling for this role? You MUST name at least 2 specific experiences,
projects, or skills quoted directly from the resume — not generic praise.

Paragraph 3 - Gaps and severity: What is the candidate missing? Are these
deal-breakers or easily explained? Name only real gaps visible in the resume vs JD —
do not invent missing skills.

Paragraph 4 - Recommendation: Give a clear yes-or-no on applying with one specific reason.
Do not be wishy-washy. If no, say why in one sentence.
 
Write in plain English. No bullet points. No jargon. Sound like a thoughtful
advisor, not a robot. This will be read by the candidate to help them decide.
 
JOB DESCRIPTION:
{job_description}
 
RESUME:
{resume_text}
 
ATS ANALYSIS:
{ats_analysis}
"""
