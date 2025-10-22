# Arcadia Auth

Minimal shared auth library for FastAPI (JWT bearer, Account/Profile).

- FastAPI router under `/auth` with register, login, logout, `me`, and profile management; configurable via `AuthSettings` (policy, expiry, multi-profile).
- Repository abstraction `AuthRepository` with a built-in `InMemoryRepo` for tests/examples.
- Cookie middlewares: `TokenCookieMiddleware` and `CookieUserMiddleware`; helper `mount_cookie_agent_middleware(app, ...)` sets a lightweight `request.state.agent`.

Install (editable):
uv add -e ../libs/auth

Note: See `arcadia_auth/` for code (schemas, router, middleware, security, repo).
