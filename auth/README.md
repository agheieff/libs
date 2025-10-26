# Arcadia Auth

Minimal auth for FastAPI using JWT bearer tokens with Accounts. Ships with a pluggable repository layer (in‑memory and SQLite), password policy, and small helpers for cookie‑based identity.

Key features:
- FastAPI router under `/auth`: register, login, logout, `me`
- Configurable via `AuthSettings` (JWT secret/expiry, password policy)
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
    # Password policy (enforced at /auth/register)
    pwd_min_len: int = 8,
    pwd_max_len: int = 256,
    require_upper: bool = False,
    require_lower: bool = False,
    require_digit: bool = False,
    require_special: bool = False,
)
```

## Endpoints (summary)

Base path: `/auth`

- POST `/auth/register` → 201 AccountOut
  - Body: `{"email":"a@b.com","password":"secret"}`
  - Errors: 409 (email exists), 422 (password policy)

- POST `/auth/login` → 200 TokenOut `{ "access_token": "...", "token_type": "bearer" }`
  - Body: `{"email":"a@b.com","password":"secret"}`
  - Errors: 401 (invalid), 403 (inactive)

- GET `/auth/me` → 200 AccountOut
  - Header: `Authorization: Bearer <token>`
  - Errors: 401 (missing/invalid token or account not found)

Minimal curl examples:

```bash
# Register
curl -s -X POST http://localhost:8000/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"a@b.com","password":"secret"}'

# Login → capture token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"a@b.com","password":"secret"}' | jq -r .access_token)

# Me
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/me
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
settings = AuthSettings(secret_key="dev-secret")

app.include_router(create_auth_router(repo, settings))
mount_cookie_agent_middleware(app, secret_key=settings.secret_key)

# run: uvicorn app:app --reload
```
