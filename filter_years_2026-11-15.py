#!/usr/bin/env python3
"""Apply KD's Nov 15, 2026 rule: the site lists ONLY jobs asking 2-5 years
of experience. Postings asking 2-5 years or 2+ years include 3-5 in their
band, and KD's 4+ years sits inside them. Jobs asking 6+ years leave the
site; jobs with unstated years move to held for verification.

- jobs_seed.json: kept jobs only (years_required in 2..5).
- jobs_out_of_band_2026-11-15.json: archived jobs asking 6+ years, with
  the reason recorded per job. Data kept, not deleted.
- held_jobs.json: +11 entries for jobs whose years are not stated on the
  posting (verify 3-5 years before listing).

Special cases:
- JRM Cybersecurity Analyst: years_required was never recorded, but the
  seed's own why_fit documents "3+ years asked" — set years_required=3
  and keep it. KD already applied to this role Nov 15, 2026.
- Bechtel Pentesting: asks 8+ years OR equivalent experience (CTF /
  bug-bounty) — KD's way in. Archived under the years rule, with a note
  that it restores on KD's word.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
seed = json.loads((ROOT / "jobs_seed.json").read_text())
held = json.loads((ROOT / "held_jobs.json").read_text())

kept, archived, to_hold = [], [], []
for job in seed:
    job = dict(job)
    if job["id"] == "jrm-cyber-analyst-nyc-2026-11-13":
        # why_fit documents "3+ years asked"; the field was never set.
        job["years_required"] = 3
    yrs = job.get("years_required")
    if isinstance(yrs, (int, float)) and 2 <= yrs <= 5:
        kept.append(job)
    elif isinstance(yrs, (int, float)) and yrs > 5:
        reason = f"Asks {int(yrs)}+ years — outside KD's 3-5 year band (Nov 15, 2026 rule)."
        if job.get("equivalent_experience"):
            reason += " NOTE: posting accepts equivalent experience (CTF / bug-bounty) as KD's way in — restore on KD's word."
        job["out_of_band_reason"] = reason
        archived.append(job)
    else:
        entry = dict(job)
        entry["held_reason"] = (
            "Years of experience not stated on the posting — verify it asks "
            "3-5 years before listing (KD rule Nov 15, 2026)."
        )
        entry["last_checked"] = "2026-11-15"
        to_hold.append(entry)

(ROOT / "jobs_seed.json").write_text(json.dumps(kept, indent=2))
(ROOT / "jobs_out_of_band_2026-11-15.json").write_text(json.dumps(archived, indent=2))
held.extend(to_hold)
(ROOT / "held_jobs.json").write_text(json.dumps(held, indent=2))

print(f"Kept on site: {len(kept)}")
print(f"Archived (6+ years): {len(archived)}")
for j in archived:
    print(f"  ARCHIVE {j['employer']} — {j['title']} ({j.get('years_required')} yrs)")
print(f"Moved to held (years unstated): {len(to_hold)}")
for j in to_hold:
    print(f"  HELD {j['employer']} — {j['title']}")
print(f"held_jobs.json total: {len(held)} entries")
