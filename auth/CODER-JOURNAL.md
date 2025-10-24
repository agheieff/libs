2025-10-24

Change: A) Remove password_hash from all public dicts; add credentials-only repo method; update login to use it.
Files: auth/arcadia_auth/models.py, auth/arcadia_auth/adapters/sqlalchemy_repo.py, auth/arcadia_auth/repo.py, auth/arcadia_auth/sqlite_repo.py, auth/arcadia_auth/router.py
Commit: cbfda21

2025-10-24

Change: B) Centralize token decode + subject extraction in helper and reuse across router and middleware.
Files: auth/arcadia_auth/auth_utils.py, auth/arcadia_auth/router.py, auth/arcadia_auth/middleware.py
Commit: eaa53fe

2025-10-24

Change: C) Normalize email handling inside repos; ensure case-insensitive lookups.
Files: auth/arcadia_auth/adapters/sqlalchemy_repo.py
Commit: cca8ef0

2025-10-24

Change: D) Standardize repository interfaces/shapes (align name field top-level; optional update sub-protocol).
Files: auth/arcadia_auth/repo.py, auth/arcadia_auth/sqlite_repo.py, auth/arcadia_auth/adapters/sqlalchemy_repo.py, auth/arcadia_auth/__init__.py
Commit: f7e4422

2025-10-24

Change: E) Make password hashing configurable; prefer argon2id by default with PBKDF2 fallback.
Files: auth/arcadia_auth/security.py, auth/arcadia_auth/__init__.py
Commit: b484e0f

2025-10-24

Change: F) Add AuthSettings.unique_profile_names (default False).
Files: auth/arcadia_auth/router.py
Commit: 9cdfb94
 
2025-10-24

Change: G) Always create a default profile on account registration; display_name falls back to email prefix when name is not provided.
Files: auth/arcadia_auth/router.py
Commit: 252c298
