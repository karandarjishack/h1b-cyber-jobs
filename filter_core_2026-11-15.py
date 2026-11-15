#!/usr/bin/env python3
"""filter_core_2026-11-15.py — KD rule Nov 15, 2026 (evening, 2nd round):
the site lists CORE jobs ONLY. Stretch jobs (senior title or a $250k+
pay band, including every 0/100-fit job) are archived, never listed.

The seed has no seniority/fit fields — those are computed by
find_jobs.py — so jobs.json (the computed output) is the authority
for which seed jobs are stretch. Archived jobs go to
jobs_stretch_archived_2026-11-15.json with a per-job reason, so they
can be restored on KD's word. find_jobs.py main() now enforces the
same rule, so a stretch job re-added to the seed is dropped, not listed.

Run: python3 filter_core_2026-11-15.py && python3 find_jobs.py && python3 build_site.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
SEED = ROOT / "jobs_seed.json"
OUT = ROOT / "jobs.json"
ARCHIVE = ROOT / "jobs_stretch_archived_2026-11-15.json"

computed = {j["id"]: j for j in json.loads(OUT.read_text())}
seed = json.loads(SEED.read_text())

kept, archived = [], []
for job in seed:
    c = computed.get(job["id"])
    sen = (c or {}).get("seniority")
    fit = (c or {}).get("fit_score")
    if sen == "core":
        kept.append(job)
        continue
    reason = []
    if fit == 0:
        reason.append("0/100 fit — no resume match at all")
    if sen == "stretch":
        reason.append("stretch role (senior title and/or $250k+ pay band)")
    elif sen is None:
        reason.append("seniority could not be computed — held out of caution")
    archived.append({**job, "fit_score_at_archive": fit,
                     "archived_reason": "; ".join(reason),
                     "archived_date": "2026-11-15",
                     "archived_rule": "KD Nov 15, 2026: site is CORE jobs only"})

SEED.write_text(json.dumps(kept, indent=2) + "\n")
ARCHIVE.write_text(json.dumps(archived, indent=2) + "\n")
print(f"Kept (core): {len(kept)}")
print(f"Archived (stretch): {len(archived)} -> {ARCHIVE.name}")
for j in archived:
    print(f"  {j.get('fit_score_at_archive','?'):>3}  {j['employer']} — {j['title'][:60]}")
