"""Load the ignored root .env for local command-line entry points only."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shlex


ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def load_local_env(path: Path = ROOT_ENV) -> int:
    """Load simple dotenv assignments without evaluating shell syntax.

    Existing process variables remain authoritative. Library imports do not call this
    function, which keeps tests and embedding applications deterministic.
    """
    if not path.is_file():
        return 0
    loaded = 0
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ValueError(f"Invalid local environment assignment on line {line_number}.")
        name, encoded = line.split("=", 1)
        name = name.strip()
        if not KEY.fullmatch(name):
            raise ValueError(f"Invalid local environment name on line {line_number}.")
        try:
            values = shlex.split(encoded.strip(), comments=True, posix=True)
        except ValueError:
            raise ValueError(f"Invalid local environment value on line {line_number}.") from None
        if len(values) > 1:
            raise ValueError(f"Quote local environment values containing spaces on line {line_number}.")
        value = values[0] if values else ""
        if name not in os.environ:
            os.environ[name] = value
            loaded += 1
    return loaded
