"""Shared, process-bounded access to NCBI E-utilities."""
from __future__ import annotations

import os
import threading
import time
from urllib.parse import urlencode

from .transport import fetch


BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
_lock = threading.Lock()
_last_request = 0.0


def ncbi(endpoint: str, params: dict[str, str | int]):
    """Keep every NCBI request below three/second across this process."""
    global _last_request
    bounded = {**params, "tool": "ResearchGuardAI"}
    if os.getenv("NCBI_EMAIL"):
        bounded["email"] = os.environ["NCBI_EMAIL"]
    with _lock:
        time.sleep(max(0, 0.36 - (time.monotonic() - _last_request)))
        _last_request = time.monotonic()
        return fetch(BASE + endpoint + "?" + urlencode(bounded))
