from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any


@dataclass
class ContextMenuRequest:
    """Context for building a menu for a specific right-click target.

    dataset: data-* attributes gathered from the triggering element.
    selection: current text selection, if any.
    path: current request path (optional, as provided by the client).
    element_id: id of the triggering element, if present.
    user: request-associated user object (if any), forwarded by the server.
    """

    dataset: Dict[str, str] = field(default_factory=dict)
    selection: Optional[str] = None
    path: Optional[str] = None
    element_id: Optional[str] = None
    user: Optional[Any] = None


@dataclass
class MenuItem:
    """Menu item description.

    Use either href for navigation or hx for htmx-actions. Dividers are represented
    by divider=True and ignore other fields.
    """

    id: Optional[str] = None
    label: Optional[str] = None
    href: Optional[str] = None
    method: Optional[str] = None  # e.g., "GET", "POST" (if used with forms)
    target: Optional[str] = None  # "_self" | "_blank"
    hx: Optional[Dict[str, str]] = None  # e.g., {"post": "/api/x", "confirm": "Sure?"}
    divider: bool = False
    disabled: bool = False
    danger: bool = False


class ContextMenuRegistry:
    """Registry of named context-menu providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, Callable[[ContextMenuRequest], List[Dict[str, Any]]]] = {}

    def add(self, name: str, provider: Callable[[ContextMenuRequest], List[Dict[str, Any]]]) -> None:
        self._providers[name] = provider

    def remove(self, name: str) -> None:
        self._providers.pop(name, None)

    def get(self, name: str) -> Optional[Callable[[ContextMenuRequest], List[Dict[str, Any]]]]:
        return self._providers.get(name)
