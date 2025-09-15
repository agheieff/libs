from __future__ import annotations
from command_router import Router, Caller, Command, command
import sys

class _CLICaller(Caller):
    def send(self, text: str) -> None:
        print(text, flush=True)

class CLI(Router):
    """Delimiter-based command loop.  Auto-registers help & quit."""
    def __init__(self, delim: str = "/", prompt: str = "> "):
        super().__init__(delim)
        self.prompt: str = prompt

    def run(self, on_text=None) -> None:
        caller = _CLICaller()
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
                        cmd.fn(args, self, caller)
                    else:
                        caller.send(f"Unknown command – {self.delim}help")
                except KeyboardInterrupt:
                    break
                continue
            if on_text:
                try:
                    on_text(raw, self)
                except KeyboardInterrupt:
                    break
        caller.send("\nBye.")
