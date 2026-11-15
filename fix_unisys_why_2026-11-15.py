#!/usr/bin/env python3
"""fix_unisys_why_2026-11-15.py — remove the internal pay sentence from the
Unisys why_fit so the tracker draft is fully recruiter-clean (salary stays
visible on the card). The pay sentence leaked into tracker drafts via
whyClean because it contains no 'PAY FLAG' marker."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
SEED = ROOT / "jobs_seed.json"

NEW_WHY = ("SIEM monitoring and incident response \u2014 Splunk/SIEM event "
           "triage and investigation, matching KD's Splunk SIEM build and "
           "SOC work. 2 years asked.")

seed = json.loads(SEED.read_text())
for j in seed:
    if j["employer"] == "Unisys":
        old = j["why_fit"]
        j["why_fit"] = NEW_WHY
        print("OLD:", repr(old))
        print("NEW:", repr(j["why_fit"]))
SEED.write_text(json.dumps(seed, indent=2) + "\n")
print("seed written")
