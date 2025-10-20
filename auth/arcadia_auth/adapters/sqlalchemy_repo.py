from __future__ import annotations

from typing import Any, Callable, Optional, Dict, Type

from sqlalchemy.orm import Session

from ..repo import AuthRepository


class SQLAlchemyRepo(AuthRepository):
    """Generic SQLAlchemy adapter.

    Configure with model classes and field names used by the project.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        UserModel: Type[Any],
        ProfileModel: Type[Any],
        user_email_field: str = "email",
        user_password_hash_field: str = "password_hash",
        user_is_active_field: str = "is_active",
        user_is_verified_field: str = "is_verified",
        user_role_field: Optional[str] = None,
        user_subscription_field: Optional[str] = None,
        profile_account_fk_field: str = "user_id",
        profile_display_name_field: Optional[str] = "display_name",
        profile_prefs_field: Optional[str] = "prefs",
        profile_extras_field: Optional[str] = None,
    ) -> None:
        self._sf = session_factory
        self.U = UserModel
        self.P = ProfileModel
        self.uf_email = user_email_field
        self.uf_pwd = user_password_hash_field
        self.uf_active = user_is_active_field
        self.uf_verified = user_is_verified_field
        self.uf_role = user_role_field
        self.uf_sub = user_subscription_field
        self.pf_acc = profile_account_fk_field
        self.pf_name = profile_display_name_field
        self.pf_prefs = profile_prefs_field
        self.pf_extras = profile_extras_field

    # ---- helpers ----
    def _acc_to_dict(self, u: Any) -> Dict[str, Any]:
        return {
            "id": getattr(u, "id"),
            "email": getattr(u, self.uf_email),
            "password_hash": getattr(u, self.uf_pwd),
            "is_active": bool(getattr(u, self.uf_active, True)),
            "is_verified": bool(getattr(u, self.uf_verified, True)),
            "role": (getattr(u, self.uf_role) if self.uf_role else None),
            "subscription_tier": (getattr(u, self.uf_sub) if self.uf_sub else None),
            "extras": None,
        }

    def _prof_to_dict(self, p: Any) -> Dict[str, Any]:
        return {
            "id": getattr(p, "id"),
            "account_id": getattr(p, self.pf_acc),
            "display_name": (getattr(p, self.pf_name) if self.pf_name else None),
            "prefs": (getattr(p, self.pf_prefs) if self.pf_prefs else None),
            "extras": (getattr(p, self.pf_extras) if self.pf_extras else None),
        }

    # ---- repo API ----
    def find_account_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        s = self._sf()
        try:
            u = s.query(self.U).filter(getattr(self.U, self.uf_email) == email).first()
            return (self._acc_to_dict(u) if u else None)
        finally:
            s.close()

    def create_account(self, email: str, password_hash: str, *, name: Optional[str]) -> Dict[str, Any]:
        s = self._sf()
        try:
            u = self.U()
            setattr(u, self.uf_email, email)
            setattr(u, self.uf_pwd, password_hash)
            if hasattr(u, self.uf_active):
                setattr(u, self.uf_active, True)
            if hasattr(u, self.uf_verified):
                setattr(u, self.uf_verified, True)
            # best-effort: if model has a 'name' field, set it
            if name and hasattr(u, "name"):
                setattr(u, "name", name)
            s.add(u)
            s.commit()
            s.refresh(u)
            return self._acc_to_dict(u)
        finally:
            s.close()

    def get_account_by_id(self, account_id: str | int) -> Optional[Dict[str, Any]]:
        s = self._sf()
        try:
            u = s.get(self.U, account_id)
            return (self._acc_to_dict(u) if u else None)
        finally:
            s.close()

    def list_profiles(self, account_id: str | int) -> list[Dict[str, Any]]:
        s = self._sf()
        try:
            rows = s.query(self.P).filter(getattr(self.P, self.pf_acc) == account_id).all()
            return [self._prof_to_dict(p) for p in rows]
        finally:
            s.close()

    def create_profile(self, account_id: str | int, *, display_name: Optional[str], prefs: Optional[Dict[str, Any]], extras: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        s = self._sf()
        try:
            p = self.P()
            setattr(p, self.pf_acc, account_id)
            if self.pf_name and hasattr(p, self.pf_name):
                setattr(p, self.pf_name, display_name)
            if self.pf_prefs and hasattr(p, self.pf_prefs):
                setattr(p, self.pf_prefs, prefs)
            if self.pf_extras and hasattr(p, self.pf_extras):
                setattr(p, self.pf_extras, extras)
            s.add(p)
            s.commit()
            s.refresh(p)
            return self._prof_to_dict(p)
        finally:
            s.close()

    def get_profile(self, account_id: str | int, profile_id: str | int) -> Optional[Dict[str, Any]]:
        s = self._sf()
        try:
            p = s.get(self.P, profile_id)
            if not p or getattr(p, self.pf_acc) != account_id:
                return None
            return self._prof_to_dict(p)
        finally:
            s.close()

    def delete_profile(self, account_id: str | int, profile_id: str | int) -> None:
        s = self._sf()
        try:
            p = s.get(self.P, profile_id)
            if not p or getattr(p, self.pf_acc) != account_id:
                return
            s.delete(p)
            s.commit()
        finally:
            s.close()
