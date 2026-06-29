"""Fetch US job listings via JSearch (Google for Jobs aggregate on RapidAPI)."""
from datetime import datetime, timezone

import httpx
from loguru import logger

from app.config import settings
from app.scraper.job_ingestion import JobIngestionService, is_junk_description

SOURCE_NAME = "jsearch_us"
COUNTRY = "us"
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
SEARCH_URL = f"https://{RAPIDAPI_HOST}/search-v2"


def _extract_jobs(payload: dict) -> list[dict]:
    """Support v2 ({data: {jobs: []}}) and legacy v1 ({data: []}) shapes."""
    data = payload.get("data")
    if isinstance(data, dict):
        return data.get("jobs") or []
    if isinstance(data, list):
        return data
    return []


def _parse_posted_at(item: dict) -> datetime:
    raw = item.get("job_posted_at_datetime_utc")
    if raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _map_job(item: dict) -> dict | None:
    title = (item.get("job_title") or "").strip()
    company = (item.get("employer_name") or "Unknown Company").strip()
    description = (item.get("job_description") or "").strip()

    if not title:
        return None
    if not description or len(description) < 150:
        logger.debug(f"Skipping short description: {title}")
        return None
    if is_junk_description(description):
        logger.debug(f"Skipping junk description: {title}")
        return None

    url = item.get("job_apply_link") or item.get("job_google_link")
    job_id = item.get("job_id")
    if not url:
        if not job_id:
            return None
        url = f"jsearch://job/{job_id}"

    location_parts = [item.get("job_city"), item.get("job_state")]
    location = ", ".join(part for part in location_parts if part)
    if not location:
        location = item.get("job_country") or "United States"

    return {
        "title": title,
        "company": company,
        "location": location,
        "url": url,
        "description": description,
        "posted_at": _parse_posted_at(item),
        "external_id": job_id,
    }


def fetch_jobs(keywords: list[str]) -> list[dict]:
    """Call JSearch API and return normalized job dicts ready for JobIngestionService."""
    if not settings.JSEARCH_API_KEY:
        raise ValueError("JSEARCH_API_KEY is not set in .env")

    results: list[dict] = []
    seen_urls: set[str] = set()
    headers = {
        "x-rapidapi-key": settings.JSEARCH_API_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }

    with httpx.Client(timeout=30.0) as client:
        for keyword in keywords:
            query = f"{keyword} 1-2 years experience in united states"
            params = {
                "query": query,
                "page": "1",
                "num_pages": str(settings.JSEARCH_NUM_PAGES),
                "date_posted": settings.JSEARCH_DATE_POSTED,
                "country": "us",
            }
            if settings.JSEARCH_JOB_REQUIREMENTS:
                params["job_requirements"] = settings.JSEARCH_JOB_REQUIREMENTS

            logger.info(f"JSearch API query: {query}")
            response = client.get(SEARCH_URL, params=params, headers=headers)

            if response.status_code >= 400:
                logger.error(
                    f"JSearch HTTP {response.status_code} for '{keyword}': {response.text[:300]}"
                )
                continue

            payload = response.json()
            if payload.get("status") != "OK":
                logger.error(f"JSearch API error for '{keyword}': {payload.get('error', payload)}")
                continue

            jobs = _extract_jobs(payload)
            logger.info(f"JSearch returned {len(jobs)} jobs for '{keyword}'")

            for item in jobs:
                mapped = _map_job(item)
                if mapped and mapped["url"] not in seen_urls:
                    seen_urls.add(mapped["url"])
                    results.append(mapped)

    return results


def run_jsearch_ingestion(keywords: list[str]) -> dict:
    """Fetch from JSearch and persist to Postgres."""
    service = JobIngestionService(source=SOURCE_NAME, country=COUNTRY)
    return service.run(keywords, fetch_jobs)
