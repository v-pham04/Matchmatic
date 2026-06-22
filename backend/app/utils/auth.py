"""
JWT token verification for protecting API endpoints.

Supabase projects using asymmetric signing keys (ES256) expose public keys at:
  {SUPABASE_URL}/auth/v1/.well-known/jwks.json

Legacy HS256 tokens (signed with the project JWT secret) are still accepted when
SUPABASE_JWT_SECRET is configured.

Usage in a router:
    from app.utils.auth import get_current_user_id

    @router.get("/feed")
    def get_feed(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        ...
"""
from __future__ import annotations

import time
from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from loguru import logger
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User

security = HTTPBearer()
SUPABASE_JWT_AUDIENCE = "authenticated"
JWKS_CACHE_TTL_SECONDS = 3600


class SupabaseJWKSClient:
    """Fetches and caches Supabase JWKS; refreshes on TTL or unknown key id (rotation)."""

    def __init__(self, jwks_url: str, cache_ttl: int = JWKS_CACHE_TTL_SECONDS) -> None:
        self.jwks_url = jwks_url
        self.cache_ttl = cache_ttl
        self._jwks: dict | None = None
        self._fetched_at = 0.0

    def _fetch_jwks(self) -> dict:
        response = httpx.get(self.jwks_url, timeout=5.0)
        response.raise_for_status()
        return response.json()

    def _ensure_loaded(self, force_refresh: bool = False) -> None:
        stale = self._jwks is None or (time.time() - self._fetched_at) > self.cache_ttl
        if force_refresh or stale:
            self._jwks = self._fetch_jwks()
            self._fetched_at = time.time()

    def get_signing_key(self, kid: str):
        self._ensure_loaded()
        key = self._find_key(kid)
        if key is not None:
            return jwk.construct(key)

        # Key may have rotated — refresh once and retry
        self._ensure_loaded(force_refresh=True)
        key = self._find_key(kid)
        if key is None:
            raise JWTError(f"Signing key not found for kid={kid}")
        return jwk.construct(key)

    def _find_key(self, kid: str) -> dict | None:
        assert self._jwks is not None
        for key in self._jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        return None


@lru_cache(maxsize=1)
def _get_jwks_client() -> SupabaseJWKSClient:
    jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    return SupabaseJWKSClient(jwks_url)


def _decode_options() -> dict:
    return {
        "verify_aud": True,
        "verify_exp": True,
        "verify_iat": True,
    }


def decode_supabase_token(token: str) -> dict:
    """
    Verify a Supabase access token and return its claims.

    Supports ES256 (JWKS) and legacy HS256 (shared secret).
    """
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as e:
        raise JWTError(f"Invalid token header: {e}") from e

    algorithm = header.get("alg")
    decode_kwargs = {
        "algorithms": [algorithm] if algorithm else [],
        "audience": SUPABASE_JWT_AUDIENCE,
        "options": _decode_options(),
    }

    if algorithm == "ES256":
        kid = header.get("kid")
        if not kid:
            raise JWTError("ES256 token missing kid header")
        signing_key = _get_jwks_client().get_signing_key(kid)
        return jwt.decode(token, signing_key, **decode_kwargs)

    if algorithm == "HS256":
        if not settings.SUPABASE_JWT_SECRET:
            raise JWTError("SUPABASE_JWT_SECRET is not configured for HS256 tokens")
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=SUPABASE_JWT_AUDIENCE,
            options=_decode_options(),
        )

    raise JWTError(f"Unsupported JWT algorithm: {algorithm}")


def _resolve_backend_user_id(payload: dict, db: Session) -> str:
    """
    Map a verified Supabase JWT to the Matchmatic users.id.

    Supabase `sub` is the auth user id; job data is keyed by backend users.id.
    We resolve via email, which POST /users/ uses as the stable identifier.
    """
    email = payload.get("email")
    if email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            return str(user.id)

    raise HTTPException(status_code=404, detail="User not found")


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> str:
    """
    Verify the Supabase JWT from the Authorization header and return Matchmatic user id.
    """
    token = credentials.credentials
    try:
        payload = decode_supabase_token(token)
        return _resolve_backend_user_id(payload, db)
    except HTTPException:
        raise
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
