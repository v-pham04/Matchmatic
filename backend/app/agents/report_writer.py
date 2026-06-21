import json
from app.agents.gemini_client import gemini_client
from app.prompts.prompts import REPORT_WRITER_PROMPT
from loguru import logger
 
 
def run_report_writer(job_description: str, resume_text: str, ats_result: dict) -> str:
    """
    Generate a substantive written analysis of the job match.
    Returns a plain text string — 4 paragraphs.
 
    This is NOT a summary — it is a real analysis covering:
    1. Headline verdict
    2. Strongest selling points
    3. Gap severity
    4. Apply/skip recommendation
    """
    prompt = REPORT_WRITER_PROMPT.format(
        job_description=job_description[:6000],
        resume_text=resume_text[:3000],
        ats_analysis=json.dumps(ats_result, indent=2),
    )
 
    logger.info("Running Report Writer...")
    analysis = gemini_client.call_model(prompt)  # Plain text, not JSON
 
    # Basic sanity check — should be at least a few sentences
    if len(analysis.strip()) < 100:
        logger.warning("Report Writer returned a very short response")
 
    logger.info(f"Report generated — {len(analysis)} characters")
    return analysis.strip()
