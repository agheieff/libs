# Arcadia Auth

## Terminology
- Account: Authentication identity and credentials; created and managed by the auth service. Accounts authenticate (e.g., email/password, tokens) and may be used by multiple agents.
- Profile: In‑app workspace/dataset tied to an Account (often many‑to‑one). Apps decide fields and policies; auth exposes profile CRUD via repositories.
- Agent: An actor operating the app (human or automated). Prefer “agent” over “user” in app terminology.
