import json
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger
from app.config import settings

# Create the client using the new SDK
client = genai.Client(api_key=settings.GEMINI_API_KEY)


class GeminiClient:
    """
    Shared Gemini 2.0 Flash client used by all AI agents.
    Handles: API calls, retry on failure, token usage logging, JSON parsing.
    """

    def __init__(self):
        self.model = "gemini-2.0-flash"
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def call_model(self, prompt: str) -> str:
        """
        Send a prompt to Gemini and return the raw text response.
        Retries up to 3 times with exponential backoff if the call fails.
        """
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        # Log token usage so you can monitor free tier consumption
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            input_tokens  = response.usage_metadata.prompt_token_count or 0
            output_tokens = response.usage_metadata.candidates_token_count or 0
            self.total_input_tokens  += input_tokens
            self.total_output_tokens += output_tokens
            logger.debug(f"Gemini tokens — input: {input_tokens}, output: {output_tokens}")
            logger.debug(f"Session total — input: {self.total_input_tokens}, output: {self.total_output_tokens}")

        return response.text

    def call_model_json(self, prompt: str) -> dict:
        """
        Call Gemini and parse the response as JSON.
        Strips markdown code fences if Gemini wraps the JSON in them.
        Raises ValueError if the response cannot be parsed as JSON.
        """
        raw = self.call_model(prompt)

        # Strip markdown fences Gemini sometimes adds: ```json ... ```
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned invalid JSON: {raw[:200]}")
            raise ValueError(f"Gemini response was not valid JSON: {e}") from e


# Single shared instance — import this everywhere
gemini_client = GeminiClient()