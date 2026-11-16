#!/usr/bin/env python3
"""Backwards-compatible entrypoint for the evidence-first v3 engine.

The previous implementation is retained in Git history. Scheduled automation
runs this file, while tests import research_engine directly.
"""
from research_engine import main

if __name__ == "__main__":
    main()
