#!/usr/bin/env python3
"""Backward-compatible command line launcher for obsplan.

The installable entry point is ``obsplan``. This file remains so existing
workflows that run ``python obslst.py`` continue to work from a source checkout.
"""

from obsplan.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
