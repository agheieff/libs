from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, Dict, Any, Union


class AccountCreate(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AccountOut(BaseModel):
    id: Union[str, int]
    email: str
    is_active: bool = True
    is_verified: bool = True
    role: Optional[str] = None  # user|admin|... optional
    subscription_tier: Optional[str] = None  # free|pro|...
    extras: Optional[Dict[str, Any]] = None


class ProfileCreate(BaseModel):
    display_name: Optional[str] = None
    prefs: Optional[Dict[str, Any]] = None
    extras: Optional[Dict[str, Any]] = None


class ProfileOut(BaseModel):
    id: Union[str, int]
    account_id: Union[str, int]
    display_name: Optional[str] = None
    prefs: Optional[Dict[str, Any]] = None
    extras: Optional[Dict[str, Any]] = None
