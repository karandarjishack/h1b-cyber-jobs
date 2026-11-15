#!/usr/bin/env python3
"""apply_sponsorship_corrections_2026-11-15.py — Nov 15, 2026 evening.

Applies the findings of the H-1B/PERM verification sweep (USCIS Employer
Data Hub + DOL LCA data, FY2025-26, transfers included) to jobs_seed.json:

- 4 jobs were overstated as B (employer sponsors H-1B for cyber titles)
  when no cyber-role filing was actually verified -> downgraded to C
  (Ask recruiter): Spotify, Plaid AI, Geotab, WRITER.
- 2 factual errors corrected: WRITER is NOT formerly Qatalog Inc
  (Qatalog is a separate company; its 2024 LCAs are not WRITER's), and
  the Sentry MyVisaJobs page cited is a different company (a Georgia
  care-home business) — real Sentry is Functional Software, Inc.
- Unisys + JRM notes corrected with the verified filing history.
- Coalfire keeps B (FY2023 InfoSec Analyst LCA verified); Anthropic
  keeps A (posting states sponsorship) with a PERM-program flag added.

Run: python3 apply_sponsorship_corrections_2026-11-15.py && python3 find_jobs.py && python3 build_site.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
SEED = ROOT / "jobs_seed.json"

CORRECTIONS = {
    "spotify-sec-eng-detection-response-2026-09-24": {
        "sponsorship_evidence": "C_ask_recruiter",
        "sponsorship_note": (
            "C — Spotify is a large H-1B sponsor (90 approvals FY2025, 92 FY2026, "
            "8 transfers) but no security-role H-1B filing was specifically verified; "
            "top sponsored roles are software, research and data. Ask recruiter before applying."
        ),
    },
    "plaid-ai-sec-eng-2026-09-19": {
        "sponsorship_evidence": "C_ask_recruiter",
        "sponsorship_note": (
            "C — Plaid sponsors H-1B (31 approvals FY2025, 35 FY2026, transfer-heavy) "
            "but no security-role H-1B filing was verified; FY2026 filings are software, "
            "data and managers. Ask recruiter before applying."
        ),
    },
    "geotab-cyber-ir-specialist-atlanta-2026-11-13": {
        "sponsorship_evidence": "C_ask_recruiter",
        "sponsorship_note": (
            "C — Geotab sponsors H-1B (8 approvals FY2025, 6 FY2026) but no security-role "
            "filing was ever found; FY2026 filings are software, data, BI and sales only. "
            "Ask recruiter before applying."
        ),
    },
    "writer-sec-eng-detection-response-2026-11-03": {
        "sponsorship_evidence": "C_ask_recruiter",
        "sponsorship_note": (
            "C — Writer, Inc. filed 4 H-1B + 1 PERM in the 2025-26 window, but job titles "
            "are unverified. WRITER is NOT formerly Qatalog Inc — Qatalog is a separate "
            "company (acquired by ClickUp Nov 2025); its 2024 LCAs are not WRITER's. "
            "Ask recruiter before applying."
        ),
    },
    "sentry-sec-eng-detection-response-2026-11-13": {
        "sponsorship_evidence": "C_ask_recruiter",
        "sponsorship_note": (
            "C — Real entity is Functional Software, Inc. DBA Sentry (not Sentry Innovation "
            "LLC — that MyVisaJobs page is a Georgia care-home business). Only 1 FY2026 LCA "
            "found: a continuation for Senior Software Engineer, Billing ($219k); no FY2025 "
            "activity and no cyber role in it. Ask recruiter FIRST and confirm before applying."
        ),
    },
    "jrm-cyber-analyst-nyc-2026-11-13": {
        "sponsorship_evidence": "C_ask_recruiter",
        "sponsorship_note": (
            "C — Zero cyber/security H-1B roles ever: all JRM filings are Estimator / "
            "Superintendent, and other JRM postings say candidates must be authorized without "
            "sponsorship. This posting is silent on sponsorship. Ask recruiter FIRST."
        ),
    },
    "unisys-cyber-sec-analyst-santa-clara-2026-10-15": {
        "sponsorship_evidence": "C_ask_recruiter",
        "sponsorship_note": (
            "C — Unisys sponsors H-1B (32 petitions FY2025, 5 transfers; 29 approved FY2026) "
            "but no security-titled role appears in its sponsored occupations. Ask recruiter "
            "before applying."
        ),
    },
    "coalfire-detection-response-eng-splunk-2026-07-21": {
        "sponsorship_evidence": "B_sponsor_history",
        "sponsorship_note": (
            "B — FY2023 certified LCA for Information Security Analyst (new employment); "
            "2 H-1B petitions FY2025, 100% approved. No PERM since 2019. Confirm per role."
        ),
    },
    "anthropic-sec-eng-offensive-sec-5418977008": {
        "sponsorship_evidence": "A_verified_posting",
        "sponsorship_note": (
            "A — posting states: 'Visa sponsorship: We do sponsor visas!' (with the caveat "
            "that not every role/candidate can be sponsored). 189 H-1B approvals FY2026, "
            "43 transfers FY2025. No PERM program on record yet — green-card path unproven. "
            "Direct Greenhouse link verified live Nov 15, 2026. Salary and posted date not "
            "shown on the page."
        ),
    },
}

seed = json.loads(SEED.read_text())
by_id = {j["id"]: j for j in seed}
for job_id, fix in CORRECTIONS.items():
    job = by_id.get(job_id)
    if not job:
        print(f"  MISSING {job_id}")
        continue
    old_ev = job.get("sponsorship_evidence")
    job.update(fix)
    print(f"  {job['employer']} — {job['title'][:45]}: {old_ev} -> {fix['sponsorship_evidence']}")
SEED.write_text(json.dumps(seed, indent=2) + "\n")
print(f"Updated {len(CORRECTIONS)} jobs in jobs_seed.json")
