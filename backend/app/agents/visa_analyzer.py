from app.agents.gemini_client import gemini_client
from app.prompts.prompts import VISA_ANALYZER_PROMPT
from loguru import logger
 
 
def run_visa_analyzer(job_description: str) -> dict:
    """
    Analyze a US job description for visa sponsorship signals.
    Only call this if the user has visa_check_enabled = True.
 
    Returns a dict with:
      visa_signal     : "open" | "citizen_only" | "unclear"
      evidence        : string (quote from JD)
      f1_opt_compatible: True | False | None
      confidence      : "HIGH" | "MEDIUM" | "LOW"
    """
    if not job_description:
        return {
            "visa_signal": "unclear",
            "evidence": "No job description provided",
            "f1_opt_compatible": None,
            "confidence": "LOW"
        }
 
    prompt = VISA_ANALYZER_PROMPT.format(
        job_description=job_description[:6000],
    )
 
    logger.info("Running Visa Analyzer...")
    result = gemini_client.call_model_json(prompt)
 
    # Validate visa_signal is one of the expected values
    valid_signals = {"open", "citizen_only", "unclear"}
    if result.get("visa_signal") not in valid_signals:
        result["visa_signal"] = "unclear"
 
    logger.info(f"Visa Signal: {result.get('visa_signal')} (confidence: {result.get('confidence')})")
    return result
