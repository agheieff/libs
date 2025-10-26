# Arcadia Auth

## Terminology
- Account: Authentication identity and credentials; created and managed by the auth service. Accounts authenticate (e.g., email/password, tokens) and may be used by multiple agents.
- Agent: An actor operating the app (human or automated). Prefer "agent" over "user" in app terminology.

## Note
This library now focuses solely on account management (authentication and authorization). Profile management has been removed to allow applications to implement their own profile systems independently.
