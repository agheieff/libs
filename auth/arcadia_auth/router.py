from __future__ import annotations

from typing import Optional, Type, Dict, Any
from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, Header, status, Request, Cookie

from .schemas import AccountCreate, AccountOut, LoginIn, TokenOut, ProfileCreate, ProfileOut
from .security import hash_password, verify_password, create_access_token
from .auth_utils import parse_bearer_token, extract_subject
from .repo import AuthRepository
from .policy import validate_password
from .repo import MutableAuthRepository


@dataclass
class AuthSettings:
    secret_key: str
    algorithm: str = "HS256"
    access_expire_minutes: int = 60 * 24 * 7
    multi_profile: bool = True
    # Profile options
    unique_profile_names: bool = False
    # Password policy (optional)
    pwd_min_len: int = 8
    pwd_max_len: int = 256
    require_upper: bool = False
    require_lower: bool = False
    require_digit: bool = False
    require_special: bool = False  # non-alnum


def _auth_header(
    request: Request,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    access_token: Optional[str] = Cookie(default=None),
) -> Optional[str]:
    # Prefer Bearer token from Authorization; fallback to access_token cookie
    token = parse_bearer_token(authorization)
    if token:
        return token
    if access_token:
        return access_token
    try:
        ck = request.cookies.get("access_token")
        if ck:
            return ck
    except Exception:
        pass
    return None


def create_auth_router(
    repo: AuthRepository,
    settings: AuthSettings,
    *,
    AccountPublic: Type[AccountOut] = AccountOut,
    ProfilePublic: Type[ProfileOut] = ProfileOut,
) -> APIRouter:
    r = APIRouter(prefix="/auth", tags=["auth"])

    def _to_account_out(acc: Dict[str, Any]) -> AccountOut:
        return AccountPublic.model_validate({
            "id": acc.get("id"),
            "email": acc.get("email"),
            "is_active": bool(acc.get("is_active", True)),
            "is_verified": bool(acc.get("is_verified", True)),
            "role": acc.get("role"),
            "subscription_tier": acc.get("subscription_tier"),
            "extras": acc.get("extras"),
        })

    def _to_profile_out(prof: Dict[str, Any]) -> ProfileOut:
        return ProfilePublic.model_validate({
            "id": prof.get("id"),
            "account_id": prof.get("account_id"),
            "display_name": prof.get("display_name"),
            "prefs": prof.get("prefs"),
            "extras": prof.get("extras"),
        })

    @r.post("/register", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
    def register(payload: AccountCreate):
        email = payload.email.strip().lower()
        if repo.find_account_by_email(email):
            raise HTTPException(status_code=409, detail="Email already registered")
        # Validate password policy; None means OK
        msg = validate_password(payload.password, settings)
        if msg:
            raise HTTPException(status_code=422, detail=msg)
        acc = repo.create_account(email, hash_password(payload.password), name=payload.name)
        # Always auto-create a default profile; display_name falls back to email prefix when name not provided
        repo.create_profile(
            acc["id"],
            display_name=(payload.name or email.split("@")[0]),
            prefs=None,
            extras=None,
        )
        return _to_account_out(acc)

    @r.post("/login", response_model=TokenOut)
    def login(payload: LoginIn):
        email = payload.email.strip().lower()
        creds = repo.get_account_credentials(email)
        if not creds or not verify_password(payload.password, creds.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not creds.get("is_active", True):
            raise HTTPException(status_code=403, detail="Inactive account")
        token = create_access_token(creds["id"], settings.secret_key, settings.algorithm, settings.access_expire_minutes)
        return TokenOut(access_token=token)

    @r.get("/logout")
    def logout():
        from fastapi.responses import RedirectResponse
        resp = RedirectResponse(url="/", status_code=302)
        try:
            resp.delete_cookie("access_token", path="/")
        except Exception:
            pass
        return resp

    @r.get("/me", response_model=AccountOut)
    def me(authorization: Optional[str] = Depends(_auth_header)):
        if not authorization:
            raise HTTPException(status_code=401, detail="Not authenticated")
        sub = extract_subject(authorization, settings.secret_key, [settings.algorithm])
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        acc = repo.get_account_by_id(sub)  # type: ignore[arg-type]
        if not acc:
            raise HTTPException(status_code=401, detail="User not found")
        return _to_account_out(acc)

    # Profiles
    pr = APIRouter(prefix="/profiles", tags=["profiles"])

    @pr.get("/", response_model=list[ProfileOut])
    def list_my_profiles(authorization: Optional[str] = Depends(_auth_header)):
        if not authorization:
            raise HTTPException(401, "Not authenticated")
        sub = extract_subject(authorization, settings.secret_key, [settings.algorithm])
        if sub is None:
            raise HTTPException(401, "Invalid token")
        profs = repo.list_profiles(sub)  # type: ignore[arg-type]
        return [_to_profile_out(p) for p in profs]

    @pr.post("/", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
    def create_my_profile(payload: ProfileCreate, authorization: Optional[str] = Depends(_auth_header)):
        if not settings.multi_profile:
            raise HTTPException(400, "Multiple profiles disabled")
        if not authorization:
            raise HTTPException(401, "Not authenticated")
        sub = extract_subject(authorization, settings.secret_key, [settings.algorithm])
        if sub is None:
            raise HTTPException(401, "Invalid token")
        # Normalize new display name: strip and trim to 32 chars
        new_name = (payload.display_name or "").strip()[:32]
        # Enforce unique profile names per account when enabled (compare against trimmed value)
        if settings.unique_profile_names:
            existing = repo.list_profiles(sub)  # type: ignore[arg-type]
            for prof in existing:
                old_name = (prof.get("display_name") or "").strip()
                if old_name == new_name:
                    raise HTTPException(status_code=409, detail="Display name already exists")
        p = repo.create_profile(sub, display_name=new_name if payload.display_name is not None else None, prefs=payload.prefs, extras=payload.extras)  # type: ignore[arg-type]
        return _to_profile_out(p)

    @pr.put("/{profile_id}", response_model=ProfileOut)
    def update_my_profile(profile_id: str, payload: ProfileCreate, authorization: Optional[str] = Depends(_auth_header)):
        if not authorization:
            raise HTTPException(401, "Not authenticated")
        sub = extract_subject(authorization, settings.secret_key, [settings.algorithm])
        if sub is None:
            raise HTTPException(401, "Invalid token")
        # Ensure repo supports updates
        if not isinstance(repo, MutableAuthRepository):
            raise HTTPException(400, "Profile updates not supported")
        # Uniqueness check when enabled (ignore current profile)
        if settings.unique_profile_names and (payload.display_name is not None):
            new_name = (payload.display_name or "").strip()[:32]
            if new_name:
                existing = repo.list_profiles(sub)  # type: ignore[arg-type]
                for prof in existing:
                    if str(prof.get("id")) == str(profile_id):
                        continue
                    old_name = (prof.get("display_name") or "").strip()
                    if old_name == new_name:
                        raise HTTPException(status_code=409, detail="Display name already exists")
        updates: Dict[str, Any] = {}
        if payload.display_name is not None:
            updates["display_name"] = (payload.display_name or "").strip()[:32]
        if payload.prefs is not None:
            updates["prefs"] = payload.prefs
        if payload.extras is not None:
            updates["extras"] = payload.extras
        updated = repo.update_profile(sub, profile_id, **updates)  # type: ignore[arg-type]
        if not updated:
            raise HTTPException(404, "Profile not found")
        return _to_profile_out(updated)

    @pr.delete("/{profile_id}")
    def delete_my_profile(profile_id: str, authorization: Optional[str] = Depends(_auth_header)):
        if not authorization:
            raise HTTPException(401, "Not authenticated")
        sub = extract_subject(authorization, settings.secret_key, [settings.algorithm])
        if sub is None:
            raise HTTPException(401, "Invalid token")
        repo.delete_profile(sub, profile_id)  # type: ignore[arg-type]
        return {"ok": True}

    r.include_router(pr)
    return r
