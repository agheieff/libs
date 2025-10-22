# cli-loop
Dead-simple delimiter-based CLI loop for Python scripts.

Install (editable):
uv add -e ../libs/cli_loop

```python
from cli_loop import CLI, command

@command("hello", "Say hi")
def handle_hello(args, cli):
    print("Hi", args)

CLI().run()
```
