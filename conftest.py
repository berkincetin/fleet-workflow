"""Repo-root pytest config.

Puts the repository root on sys.path so shared test-support modules can be
imported by their package path (e.g. `from tests.security.corpus import ...`).
The application packages themselves (core, fleet_rag, fleet_api, ...) resolve
through their editable installs, not this — this is only for cross-referencing
helper code that lives under tests/.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
