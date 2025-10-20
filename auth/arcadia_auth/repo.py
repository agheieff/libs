from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple


class AuthRepository(ABC):
    """Abstract repository to be implemented per project/DB.

    IDs are opaque (int or str). Implementations should normalize email casing.
    """

    @abstractmethod
    def find_account_by_email(self, email: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def create_account(self, email: str, password_hash: str, *, name: Optional[str]) -> Dict[str, Any]: ...

    @abstractmethod
    def get_account_by_id(self, account_id: str | int) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def list_profiles(self, account_id: str | int) -> list[Dict[str, Any]]: ...

    @abstractmethod
    def create_profile(self, account_id: str | int, *, display_name: Optional[str], prefs: Optional[Dict[str, Any]], extras: Optional[Dict[str, Any]]) -> Dict[str, Any]: ...

    @abstractmethod
    def get_profile(self, account_id: str | int, profile_id: str | int) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def delete_profile(self, account_id: str | int, profile_id: str | int) -> None: ...


class InMemoryRepo(AuthRepository):
    """Simple in-memory store for testing.

    Not persistent; IDs are ints.
    """

    def __init__(self) -> None:
        self._acc_id = 0
        self._prof_id = 0
        self.accounts: Dict[int, Dict[str, Any]] = {}
        self.accounts_by_email: Dict[str, int] = {}
        self.profiles: Dict[int, Dict[str, Any]] = {}
        self.profiles_by_acc: Dict[int, list[int]] = {}

    def _next_acc(self) -> int:
        self._acc_id += 1
        return self._acc_id

    def _next_prof(self) -> int:
        self._prof_id += 1
        return self._prof_id

    def find_account_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        key = email.strip().lower()
        acc_id = self.accounts_by_email.get(key)
        return (self.accounts.get(acc_id) if acc_id else None)

    def create_account(self, email: str, password_hash: str, *, name: Optional[str]) -> Dict[str, Any]:
        if self.find_account_by_email(email):
            raise ValueError("email already registered")
        aid = self._next_acc()
        acc = {
            "id": aid,
            "email": email.strip().lower(),
            "password_hash": password_hash,
            "is_active": True,
            "is_verified": True,
            "role": None,
            "subscription_tier": None,
            "extras": {"name": name} if name else None,
        }
        self.accounts[aid] = acc
        self.accounts_by_email[acc["email"]] = aid
        self.profiles_by_acc[aid] = []
        return acc

    def get_account_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        return self.accounts.get(int(account_id))

    def list_profiles(self, account_id: int) -> list[Dict[str, Any]]:
        ids = self.profiles_by_acc.get(int(account_id), [])
        return [self.profiles[i] for i in ids]

    def create_profile(self, account_id: int, *, display_name: Optional[str], prefs: Optional[Dict[str, Any]], extras: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        pid = self._next_prof()
        prof = {
            "id": pid,
            "account_id": int(account_id),
            "display_name": display_name,
            "prefs": prefs,
            "extras": extras,
        }
        self.profiles[pid] = prof
        self.profiles_by_acc.setdefault(int(account_id), []).append(pid)
        return prof

    def get_profile(self, account_id: int, profile_id: int) -> Optional[Dict[str, Any]]:
        prof = self.profiles.get(int(profile_id))
        return prof if prof and int(prof.get("account_id")) == int(account_id) else None

    def delete_profile(self, account_id: int, profile_id: int) -> None:
        prof = self.get_profile(account_id, profile_id)
        if not prof:
            return
        self.profiles.pop(int(profile_id), None)
        arr = self.profiles_by_acc.get(int(account_id), [])
        self.profiles_by_acc[int(account_id)] = [p for p in arr if int(p) != int(profile_id)]
