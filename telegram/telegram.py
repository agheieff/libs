from __future__ import annotations
import sys
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

@dataclass
class Command:
    name: str
    fn: Callable[[str, "CLI"], None]
    help: str = ""

class CLI:
    """Delimiter-based command loop.  Auto-registers help & quit."""
    def __init__(self, delim: str = "/", prompt: str = "> "):
        self.delim: str = delim
        self.prompt: str = prompt
        self.cmds: Dict[str, Command] = {}
        self._register_builtin()

    # ----- built-ins -----
    def _register_builtin(self) -> None:
        self.register(self._help, "help", "Show this help")
        self.register(self._quit, "quit", "Exit")
        self.register(self._quit, "exit", "")

    def _help(self, args: str, cli: CLI) -> None:
        print("Commands:")
        for c in self.cmds.values():
            print(f"  {cli.delim}{c.name:<12} {c.help}")

    def _quit(self, args: str, cli: CLI) -> None:
        raise KeyboardInterrupt

    # ----- public API -----
    def register(
        self,
        fn: Callable[[str, "CLI"], None],
        name: Optional[str] = None,
        help: str = "",
    ) -> None:
        """Register a function as a command."""
        name = name or fn.__name__.lstrip("handle_")
        self.cmds[name] = Command(name, fn, help)

    def run(self, on_text: Optional[Callable[[str, "CLI"], None]] = None) -> None:
        while True:
            try:
                raw = input(self.prompt).strip()
            except (KeyboardInterrupt, EOFError):
                break
            if not raw:
                continue
            if raw.startswith(self.delim):
                cmd_raw, _, args = raw[1:].partition(" ")
                try:
                    if cmd := self.cmds.get(cmd_raw):
                        cmd.fn(args, self)
                    else:
                        print(f"Unknown command – {self.delim}help")
                except KeyboardInterrupt:
                    break
                continue
            if on_text:
                try:
                    on_text(raw, self)
                except KeyboardInterrupt:
                    break
        print("\nBye.")

# convenience decorator
def command(name: Optional[str] = None, help: str = ""):
    def decorator(fn: Callable[[str, "CLI"], None]) -> Callable[[str, "CLI"], None]:
        fn._cli_name = name
        fn._cli_help = help
        return fn
    return decorator
