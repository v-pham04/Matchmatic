import os

from app.config import settings


def configure_playwright_browsers() -> None:
    """Point Playwright at repo-local browser binaries before launch."""
    if settings.PLAYWRIGHT_BROWSERS_PATH:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = settings.PLAYWRIGHT_BROWSERS_PATH
