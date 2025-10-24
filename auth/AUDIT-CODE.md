# Arcadia Auth – Code Audit (Modularity First)

Scope: `/home/agheieff/Arcadia/libs/auth/arcadia_auth` (schemas, router, middleware, security, repo/adapters, models). Focused on modularity, then LoC reduction, readability, architecture, and error‑prone patterns. No code was modified.

## Summary of Top Recommendations (Highest ROI)

1) Remove `password_hash` from public repository outputs; introduce a credentials‑only retrieval path
   - Files: `models.py` (Account.to_dict ~L38–48), `adapters/sqlalchemy_repo.py` (_acc_to_dict ~L46–56), `repo.py` (InMemoryRepo.create_account ~L62–77), `router.py` (login ~L84–93)
   - Rationale: Eliminates accidental leakage risk, clarifies boundaries between “public account” vs “credentials.” Keep `password_hash` only in a dedicated method like `get_account_credentials(email)` or `get_account_secret_by_id(id)`.

2) Centralize auth dependency (decode + subject extraction) for router and middleware
   - Files: `router.py` (repeated `decode_token` + header parsing in `me`, `profiles/*`; ~L100–150), `middleware.py` (token decode repeated in both middlewares)
   - Rationale: Single source of truth reduces duplication, enforces consistent error handling and algorithms, and lowers maintenance.

3) Standardize repository interface and shapes across implementations
   - Files: `repo.py` (interface), `sqlite_repo.py` (extra `update_*` methods + `**extra_fields`), `adapters/sqlalchemy_repo.py` (case‑sensitive email lookup), `repo.py` InMemoryRepo (stores `name` in `extras` unlike SQLite model field)
   - Rationale: Aligning method signatures and returned dict shapes avoids subtle bugs and adapter‑specific conditionals, improving modularity and reusability.

4) Upgrade password hashing defaults and make them configurable
   - Files: `security.py` (Passlib `CryptContext` with `pbkdf2_sha256`), `__init__.py` exports
   - Rationale: Prefer `argon2id` as default, expose the `CryptContext` or settings injection to allow projects to tune algorithms/rounds without forking.

5) Normalize email handling in all repos
   - Files: `adapters/sqlalchemy_repo.py` (uses equality on email), `sqlite_repo.py` (`ilike`), `router.py` (lower‑cases before calling repo)
   - Rationale: Move normalization (strip/lower) into repos to guarantee consistent behavior regardless of caller.

## Ranked Findings

### High Impact

1. Sensitive field exposure via repository return values
   - Where:
     - `arcadia_auth/models.py` Account.to_dict includes `password_hash` (~L38–48)
     - `arcadia_auth/adapters/sqlalchemy_repo.py` `_acc_to_dict` returns `password_hash` (~L46–56)
     - `arcadia_auth/repo.py` InMemoryRepo returns `password_hash` (create_account ~L62–77)
     - `arcadia_auth/router.py` `login` reads `acc["password_hash"]` (~L84–93)
   - Impact: High risk of accidental leakage in logs, debugging, or future API surfaces that pass repository results through. Increases blast radius of a single misuse.
   - Recommendation: Remove `password_hash` from all public dict outputs and models’ `to_dict`. Add a dedicated repo method (e.g., `get_account_credentials(email)` returning `{id, password_hash, is_active, is_verified}`) used only by `login`. Keep public account shape password‑free.
   - Effort: Medium (touch 3–4 files; small, focused changes).

2. Duplicated token decoding logic and header parsing
   - Where: `arcadia_auth/router.py` (`me`, `profiles` handlers ~L100–150) and `arcadia_auth/middleware.py` (both middlewares)
   - Impact: Inconsistent behavior and error handling over time; harder to evolve algorithms or add claims/rotation.
   - Recommendation: Introduce a small utility/dependency, e.g., `auth_context(settings) -> subject_id | HTTPException`, used by endpoints and middleware. Optionally include minimal `Agent` object creation in one place.
   - Effort: Low–Medium (new helper + replace call sites).

3. Repository interface drift and inconsistent shapes
   - Where:
     - `sqlite_repo.py` defines `update_account`/`update_profile` not present in `AuthRepository`
     - `repo.py` InMemoryRepo stores `name` inside `extras`; `models.py` has a first‑class `name` column
     - `adapters/sqlalchemy_repo.py` email lookup is case‑sensitive; others are case‑insensitive
   - Impact: Adapter‑specific quirks bleed into callers; increases conditional logic and surprises during swaps/mocks.
   - Recommendation: (a) Either extend `AuthRepository` with optional update methods or move them to a separate `MutableAuthRepository` protocol; (b) Define and document the canonical account/profile dict shapes (e.g., `name` is top‑level); (c) Enforce email normalization in every repo implementation.
   - Effort: Medium.

4. Password hashing defaults lack configurability and modern default
   - Where: `arcadia_auth/security.py` uses `pbkdf2_sha256` with default Passlib params
   - Impact: Secure today, but not best‑in‑class; changing later requires fork/touching library internals.
   - Recommendation: Switch default to `argon2id` and allow injecting a `CryptContext` via settings/env. Keep PBKDF2 as fallback for environments lacking argon2 deps.
   - Effort: Medium.

### Medium Impact

5. Email normalization is split between router and repos
   - Where: Router lower‑cases before calling repo; `SQLAlchemyRepo` uses equality; SQLite uses `ilike`.
   - Impact: Callers outside router can bypass normalization; inconsistent behavior across adapters.
   - Recommendation: Normalize (strip + lower) inside all repo methods for email lookup/creation. Optionally add DB‑level functional index for case‑insensitive email where supported.
   - Effort: Low.

6. Over‑broad exception suppression hides actionable errors
   - Where: `security.verify_password` swallows all exceptions; middlewares catch broad `Exception` and silently continue.
   - Impact: Debugging real misconfigurations becomes difficult; silent auth failures.
   - Recommendation: Catch library‑specific exceptions (e.g., from Passlib/JWT) and optionally log at debug level. Keep behavior non‑blocking but visible in logs.
   - Effort: Low.

7. Token claims are minimal; no audience/issuer options
   - Where: `security.create_access_token`
   - Impact: Harder to integrate with multi‑service architectures; rotation/audience checks become ad‑hoc.
   - Recommendation: Support optional `aud`, `iss`, and key rotation hooks via settings (optional, off by default to preserve simplicity).
   - Effort: Low–Medium.

### Low Impact

8. Minor API shape inconsistencies for profile fields (`timezone`, `theme` exist in models but not surfaced in repos/adapters uniformly)
   - Where: `models.py` has fields that aren’t consistently mapped in adapters.
   - Impact: Confusion for consumers expecting parity across backends.
   - Recommendation: Decide canonical profile shape and map consistently (or document clearly as extension fields).
   - Effort: Low.

9. Unused imports/parameters
   - Where: `sqlite_repo.py` imports `hash_password` but doesn’t use it.
   - Impact: Minor clutter.
   - Recommendation: Remove unused import/params.
   - Effort: Trivial.

## Security‑Sensitive Areas Requiring Attention

- Password storage: Passlib `pbkdf2_sha256` is acceptable, but prefer `argon2id` by default; expose `CryptContext` configurability. Ensure unique per‑password salts (Passlib handles this) and adequate iteration parameters.
- Token handling: HS256 with a single secret is fine for a single service; ensure strong, rotated secrets. Consider optional `aud`/`iss` claims and clock skew handling. `decode_token` collapsing all JWT errors to `None` is simple but loses detail; acceptable for 401s, but consider debug logging.
- Data exposure: Removing `password_hash` from all public dicts (repositories and `Account.to_dict`) is the single most impactful risk reduction.
- Cookies: Library doesn’t set cookies; if consumers set them, recommend `HttpOnly`, `Secure`, and `SameSite` attributes.

## Concrete Next Steps (3–5 changes)

1) Sanitize account data at the source and split credential access
   - Update `Account.to_dict` (models.py ~L38–48) and `_acc_to_dict` (adapters/sqlalchemy_repo.py ~L46–56) to omit `password_hash`.
   - Add repo method `get_account_credentials(email)` returning `{id, password_hash, is_active, is_verified}`; adjust `router.py::login` to use it.

2) Introduce `current_subject_id` dependency/helper
   - Add `auth_utils.py` with `auth_subject(settings, header: str|None) -> str|int` and use in `router.py` (`/me`, `/profiles/*`) and both middlewares.

3) Normalize email inside repositories
   - Ensure `find_account_by_email` and `create_account` in all repos call `email.strip().lower()` and perform case‑insensitive lookup (use `func.lower`/`ilike` as appropriate).

4) Configurable password hashing (argon2id default)
   - Expose a settings hook for `CryptContext` or algo selection in `security.py`; keep PBKDF2 as fallback.

5) Align repository interface across adapters
   - Either extend `AuthRepository` with optional update methods or create a `MutableAuthRepository` sub‑protocol; ensure `name` is a top‑level account field consistently (avoid storing in `extras`).

## Actions Taken in This Audit

- Read and analyzed: `README.md`, `schemas.py`, `router.py`, `middleware.py`, `security.py`, `repo.py`, `sqlite_repo.py`, `adapters/sqlalchemy_repo.py`, `models.py`.
- Grepped for password/token usages to assess exposure and coupling points.
- No code changes performed; this report documents prioritized recommendations.

## Blockers / Uncertainties / Follow‑ups

- Consumers may rely on current dict shapes (including `password_hash`). If so, a two‑step migration (deprecate then remove) is advised.
- If Argon2 dependencies are undesirable in some environments, keep PBKDF2 as default and allow opt‑in Argon2 via settings.
- Decide whether to support audience/issuer claims broadly (could be optional to avoid breaking simple use cases).
