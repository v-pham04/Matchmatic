from app.agents.gemini_client import gemini_client
from app.prompts.prompts import ATS_SCORER_PROMPT
from loguru import logger
 
 
def run_ats_scorer(job_description: str, resume_text: str) -> dict:
    """
    Score how well a resume matches a job description.
 
    Returns a dict with:
      score          : int (0-100)
      match_level    : "HIGH" | "MEDIUM" | "LOW"
      matching_skills: list of strings
      missing_skills : list of strings
      experience_match: "strong" | "partial" | "weak"
      improvement_tip: string
    """
    if not job_description or not resume_text:
        raise ValueError("Both job_description and resume_text are required")
 
    # Fill in the prompt template with real values
    prompt = ATS_SCORER_PROMPT.format(
        job_description=job_description[:8000],  # Cap to avoid token limits
        resume_text=resume_text[:4000],
    )
 
    logger.info("Running ATS Scorer...")
    result = gemini_client.call_model_json(prompt)
 
    # Validate the required fields are present
    required_fields = ["score", "match_level", "matching_skills", "missing_skills"]
    for field in required_fields:
        if field not in result:
            raise ValueError(f"ATS Scorer response missing required field: {field}")
 
    # Ensure score is within valid range
    score = int(result.get("score", 0))
    result["score"] = max(0, min(100, score))
 
    # Ensure match_level is valid
    valid_levels = {"HIGH", "MEDIUM", "LOW"}
    if result.get("match_level") not in valid_levels:
        # Derive it from the score if Gemini returned something unexpected
        s = result["score"]
        result["match_level"] = "HIGH" if s >= 80 else "MEDIUM" if s >= 60 else "LOW"
 
    logger.info(f"ATS Score: {result['score']} ({result['match_level']})")
    return result
