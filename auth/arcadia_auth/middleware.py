from __future__ import annotations

from typing import Any, Callable, Optional, Type

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from .security import decode_token


class CookieUserMiddleware(BaseHTTPMiddleware):
    """Populate request.state.user from a JWT stored in a cookie.

    Configure with a session factory and User model so projects can reuse it
    regardless of their ORM setup. The middleware is intentionally light and
    only sets a "user" attribute for truthy checks in templates.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        session_factory: Callable[[], Any],
        UserModel: Type[Any],
        secret_key: str,
        algorithm: str = "HS256",
        cookie_name: str = "access_token",
        require_active_attr: str = "is_active",
    ) -> None:
        super().__init__(app)
        self._sf = session_factory
        self._U = UserModel
        self._secret = secret_key
        self._alg = algorithm
        self._cookie = cookie_name
        self._active_attr = require_active_attr

    async def dispatch(self, request: Request, call_next):
        try:
            request.state.user = None
            token = request.cookies.get(self._cookie)
            if token:
                data = decode_token(token, self._secret, [self._alg])
                sub = data.get("sub") if data else None
                if sub is not None:
                    s = self._sf()
                    try:
                        u = s.get(self._U, sub)
                        if u is not None:
                            ok = True
                            if hasattr(u, self._active_attr):
                                ok = bool(getattr(u, self._active_attr))
                            if ok:
                                request.state.user = u
                    finally:
                        s.close()
        except Exception:
            # never block request flow because of auth context issues
            request.state.user = None
        return await call_next(request)
