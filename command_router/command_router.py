from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Protocol

class Caller(Protocol):
    def send(self, text: str) -> None: ...

@dataclass
class Command:
    name: str
    fn: Callable[[str, "Router", Caller], None]
    help: str = ""

class Router:
    def __init__(self, delim: str = "/"):
        self.delim: str = delim
        self.cmds: Dict[str, Command] = {}
        self._register_builtin()

    def _register_builtin(self) -> None:
        self.register(self._help, "help", "Show this help")
        self.register(self._quit, "quit", "Exit")
        self.register(self._quit, "exit", "")

    def _help(self, args: str, router: Router, caller: Caller) -> None:
        lines = ["Commands:"]
        for c in router.cmds.values():
            lines.append(f"  {router.delim}{c.name:<12} {c.help}")
        caller.send("\n".join(lines))

    def _quit(self, args: str, router: Router, caller: Caller) -> None:
        raise KeyboardInterrupt

    def register(
        self,
        fn: Callable[[str, Router, Caller], None],
        name: Optional[str] = None,
        help: str = "",
    ) -> None:
        name = name or fn.__name__.lstrip("handle_")
        self.cmds[name] = Command(name, fn, help)

    def handle(self, text: str, caller: Caller) -> None:
        text = text.strip()
        if text.startswith(self.delim):
            cmd_raw, _, args = text[1:].partition(" ")
            if cmd := self.cmds.get(cmd_raw):
                cmd.fn(args, self, caller)
            else:
                caller.send(f"Unknown command – {self.delim}help")
        else:
            caller.send(text)

def command(name: Optional[str] = None, help: str = ""):
    def decorator(fn: Callable[[str, Router, Caller], None]) -> Callable[[str, Router, Caller], None]:
        fn._cli_name = name
        fn._cli_help = help
        return fn
    return decorator
