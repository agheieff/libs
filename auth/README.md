# Arcadia Auth

Minimal auth for FastAPI using JWT bearer tokens with Accounts and Profiles. Ships with a pluggable repository layer (in‑memory and SQLite), password policy, and small helpers for cookie‑based identity.

Key features:
- FastAPI router under `/auth`: register, login, logout, `me`, and profiles (list/create/delete)
- Configurable via `AuthSettings` (JWT secret/expiry, password policy, multi‑profile, unique profile names)
- Repository abstraction `AuthRepository` with `InMemoryRepo` and `SQLiteRepository`
- Optional cookie middleware to expose a lightweight `request.state.agent`

## Quick start

Install (editable for monorepo):

```bash
uv add -e ../libs/auth
```

Minimal app wiring (in‑memory repo):

```python
from fastapi import FastAPI
from arcadia_auth import InMemoryRepo, create_auth_router, AuthSettings, mount_cookie_agent_middleware

app = FastAPI()

repo = InMemoryRepo()
settings = AuthSettings(
    secret_key="change-me",           # required
    access_expire_minutes=60*24*7,     # default 7 days
    multi_profile=True,                # allow multiple profiles per account
    unique_profile_names=False,        # enforce per‑account unique display_name when True
)

# Expose /auth/* endpoints
app.include_router(create_auth_router(repo, settings))

# Optional: read JWT from an `access_token` cookie to set request.state.agent/user
mount_cookie_agent_middleware(app, secret_key=settings.secret_key, algorithm=settings.algorithm)
```

SQLite adapter instead of in‑memory:

```python
from arcadia_auth import create_sqlite_repo
repo = create_sqlite_repo("sqlite:///auth.db", echo=False)
```

## AuthSettings

```python
from arcadia_auth import AuthSettings

AuthSettings(
    secret_key: str,                 # required, used to sign JWTs
    algorithm: str = "HS256",        # JWT algorithm
    access_expire_minutes: int = 60*24*7,
    # Profile options
    multi_profile: bool = True,      # allow multiple profiles per account
    unique_profile_names: bool = False,  # reject duplicate display_name per account
    # Password policy (enforced at /auth/register)
    pwd_min_len: int = 8,
    pwd_max_len: int = 256,
    require_upper: bool = False,
    require_lower: bool = False,
    require_digit: bool = False,
    require_special: bool = False,
)
```

Notes:
- When registering, a default profile is auto‑created; `display_name` falls back to the email prefix when `name` isn’t provided.
- `unique_profile_names=True` forces per‑account uniqueness and returns 409 on duplicates.

## Endpoints (summary)

Base path: `/auth`

- POST `/auth/register` → 201 AccountOut
  - Body: `{"email":"a@b.com","password":"secret","name":"Alice"}`
  - Errors: 409 (email exists), 422 (password policy)

- POST `/auth/login` → 200 TokenOut `{ "access_token": "...", "token_type": "bearer" }`
  - Body: `{"email":"a@b.com","password":"secret"}`
  - Errors: 401 (invalid), 403 (inactive)

- GET `/auth/me` → 200 AccountOut
  - Header: `Authorization: Bearer <token>`
  - Errors: 401 (missing/invalid token or account not found)

- GET `/auth/profiles/` → 200 list[ProfileOut]
  - Header: `Authorization: Bearer <token>`

- POST `/auth/profiles/` → 201 ProfileOut
  - Header: `Authorization: Bearer <token>`
  - Body: `{"display_name":"Work"}`
  - Errors: 400 (multi‑profile disabled), 409 (duplicate name when `unique_profile_names=True`)

- DELETE `/auth/profiles/{profile_id}` → 200 `{ "ok": true }`
  - Header: `Authorization: Bearer <token>`

Minimal curl examples:

```bash
# Register
curl -s -X POST http://localhost:8000/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"a@b.com","password":"secret","name":"Alice"}'

# Login → capture token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"a@b.com","password":"secret"}' | jq -r .access_token)

# Me
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/me

# Profiles
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/profiles/
curl -s -X POST http://localhost:8000/auth/profiles/ \
  -H 'content-type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"display_name":"Work"}'
```

## Security notes

- Password hashing via passlib `CryptContext` (prefers `argon2`; falls back to `pbkdf2_sha256`).
  - APIs: `hash_password(password)`, `verify_password(plain, hash)`, `set_password_context(ctx)`
- Token utilities using `python-jose`:
  - `create_access_token(subject, secret_key, algorithm="HS256", expires_minutes=...)`
  - `decode_token(token, secret_key, algorithms=["HS256"])`
- Always use a strong `secret_key`; rotate if compromised. Default expiry is 7 days; tune via `access_expire_minutes`.

## Minimal working example

```python
from fastapi import FastAPI
from arcadia_auth import (
    InMemoryRepo,
    create_auth_router,
    AuthSettings,
    mount_cookie_agent_middleware,
)

app = FastAPI()
repo = InMemoryRepo()
settings = AuthSettings(secret_key="dev-secret", multi_profile=True, unique_profile_names=True)

app.include_router(create_auth_router(repo, settings))
mount_cookie_agent_middleware(app, secret_key=settings.secret_key)

# run: uvicorn app:app --reload
```
