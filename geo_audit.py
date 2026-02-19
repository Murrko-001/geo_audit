"""
Convenience entry point for running the GEO audit tool without packaging.
"""

from __future__ import annotations

import sys
from pathlib import Path

def main() -> None:
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root))

    from src.main import main as app_main
    app_main()


if __name__ == "__main__":
    main()
