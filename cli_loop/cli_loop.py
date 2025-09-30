from __future__ import annotations
import sys
import inspect
from typing import Dict, Callable, Optional, Any

class CLI:
    """Command-line interface with automatic argument parsing."""

    def __init__(self, delim: str = "/", prompt: str = "> ", text_mode: bool = False):
        self.delim = delim
        self.prompt = prompt
        self.text_mode = text_mode  # If True, non-command input goes to on_text handler
        self.cmds: Dict[str, Callable] = {}
        self._register_builtin()

    def _register_builtin(self) -> None:
        """Register built-in help and quit commands."""
        def help() -> str:
            """Show available commands"""
            if not self.cmds:
                return "No commands available."
            lines = ["Available commands:"]
            for name, fn in sorted(self.cmds.items()):
                help_text = getattr(fn, '__doc__', '') or "No description"
                lines.append(f"  {self.delim}{name} - {help_text.strip()}")
            return "\n".join(lines)

        def quit() -> None:
            """Exit the application"""
            raise KeyboardInterrupt

        self.cmds["help"] = help
        self.cmds["quit"] = quit

    def register(self, fn: Callable, name: Optional[str] = None, help: str = "") -> None:
        """Register a command function with automatic argument parsing."""
        cmd_name = name or fn.__name__
        if help:
            fn.__doc__ = help
        self.cmds[cmd_name] = fn

    def _parse_args(self, fn: Callable, args_str: str) -> tuple[list, dict]:
        """Parse arguments for function based on its signature."""
        if not args_str.strip():
            return [], {}

        sig = inspect.signature(fn)
        params = list(sig.parameters.values())

        # Simple parsing: split by spaces, handle optional params
        args = args_str.strip().split()

        if len(params) == 0:
            return [], {}
        elif len(params) == 1:
            # Single parameter - pass the full string
            return [args_str.strip()] if args_str.strip() else [], {}
        else:
            # Multiple parameters - pass individual args
            return args, {}

    def run(self, on_text: Optional[Callable] = None) -> None:
        """Run the command loop."""
        while True:
            try:
                raw = input(self.prompt).strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not raw:
                continue

            # Check if it's a command (starts with delimiter or no text mode)
            is_command = raw.startswith(self.delim) or not self.text_mode

            if is_command:
                # Parse command
                if raw.startswith(self.delim):
                    cmd_input = raw[1:]
                else:
                    cmd_input = raw

                cmd_name, _, args_str = cmd_input.partition(" ")

                if cmd_fn := self.cmds.get(cmd_name):
                    try:
                        args, kwargs = self._parse_args(cmd_fn, args_str)
                        result = cmd_fn(*args, **kwargs)
                        if result:
                            print(result, flush=True)
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        print(f"Error: {e}", flush=True)
                else:
                    print(f"Unknown command – {self.delim}help", flush=True)
            else:
                # Text mode - pass to handler
                if on_text:
                    try:
                        on_text(raw, self)
                    except KeyboardInterrupt:
                        break

        print("\nBye.", flush=True)


def command(name: Optional[str] = None, help: str = ""):
    """Decorator for command functions."""
    def decorator(fn: Callable) -> Callable:
        fn._command_name = name or fn.__name__
        fn._command_help = help
        return fn
    return decorator
