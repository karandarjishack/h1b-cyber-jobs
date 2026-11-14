#!/usr/bin/env python3
"""
h1b-cyber-jobs — GitHub wrapper for KD
Finds cybersecurity jobs, filtered to:
  1. Cyber security only (titles in kd_profile.json)
  2. Resume fit (keyword scoring against KD's real experience)
  3. H-1B sponsorship ONLY — employer must have H-1B filing history
     for security/cyber titles, or the posting must state sponsorship.
     Anything saying "US Citizen only", "will not sponsor",
     "no sponsorship", TS/SCI, or GovCloud is excluded.
  4. Target sectors (Nov 13, 2026): tech, finance, consulting AND
     construction / infrastructure / engineering — cyber roles AT
     construction companies (Bechtel, AECOM, Jacobs, Turner, JRM, etc.)
     count. Non-cyber construction roles (civil engineer, site / project
     manager) are NOT in scope unless KD says so — they do not fit his
     cyber resume.
  5. CORE vs STRETCH (fixed Nov 13, 2026 after KD said relevant jobs
     were too low): KD has 4+ years. A role is CORE only if its title
     is non-senior (no Senior/Lead/Manager/Staff/Principal/Director)
     and it asks ~3-5 years. Senior/Lead/Manager/Staff/Principal
     titles, or roles asking 7+ years, are STRETCH — they score -20
     and can never outrank a core job, no matter how many keywords
     match. Skill keywords alone do NOT make a job relevant.
     Best Picks / Core Picks are core jobs only.

How it works (no paid API key needed for the core run):
  - jobs_seed.json is the human-verified seed: jobs found by searching
    official / aggregator listings and checked against the sponsor list.
  - sponsors.csv is the DOL LCA / USCIS sponsor evidence (Q4 FY2025).
  - The script scores each seed job against kd_profile.json,
    drops anything that hits an exclusion phrase, and regenerates
    jobs.md + jobs.csv + jobs.json sorted by fit score.
  - Search links in README / jobs.md let you pull the *next* batch
    manually or via the optional Adzuna / JSearch hooks below.

Optional live APIs (set env vars, otherwise skipped):
  ADZUNA_APP_ID / ADZUNA_APP_KEY — Adzuna jobs API
  JSEARCH_API_KEY — RapidAPI JSearch

Run:
  python3 find_jobs.py
  python3 find_jobs.py --check   # only print, don't rewrite outputs
"""
import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
PROFILE = json.loads((ROOT / "kd_profile.json").read_text())
SEED = json.loads((ROOT / "jobs_seed.json").read_text())

EXCLUDE = [p.lower() for p in PROFILE["exclude_if_any"]]
MUST_HAVE = PROFILE["must_have_keywords"]
TARGET_TITLES = [t.lower() for t in PROFILE["target_titles"]]


def is_cyber_title(title: str) -> bool:
    t = title.lower()
    return any(
        k in t
        for k in [
            "security engineer",
            "detection engineer",
            "cyber",
            "soc engineer",
            "security operations",
            "cloud security",
            "ai security",
            "information security",
            "endpoint detection",
            "edr",
            "pentest",
            "penetration test",
            "security analyst",
            "risk and compliance",
            "vapt",
        ]
    )


def is_excluded(job: dict) -> str | None:
    # Only scan the posting's own title / fit text, NOT our sponsorship_note
    # (which may mention an excluded role as a warning, e.g. "do not confuse
    # with the GovCloud role"). Sponsorship_note is our annotation, not the posting.
    hay = " ".join(
        [
            job.get("title", ""),
            job.get("why_fit", ""),
        ]
    ).lower()
    for phrase in EXCLUDE:
        if phrase in hay:
            return phrase
    if job.get("excluded"):
        return "flagged excluded in seed"
    return None


SENIOR_WORDS = ["senior", "lead", "manager", "staff", "principal", "director", "head of"]


def seniority_of(title: str) -> str:
    t = title.lower()
    return "stretch" if any(w in t for w in SENIOR_WORDS) else "core"


def fit_score(job: dict) -> int:
    """0-100 relevance score. Keyword matches + title match + sponsor
    evidence + location bonus, MINUS 20 for senior/lead/manager/staff/
    principal titles — KD has 4+ years, so a 7-10 year senior role is
    a stretch no matter how many keywords match."""
    matched = job.get("keywords_matched", [])
    # Each matched resume keyword = 8 points, capped at 64
    score = min(64, len(matched) * 8)
    # Title is a target title
    if any(t in job["title"].lower() for t in TARGET_TITLES):
        score += 16
    elif is_cyber_title(job["title"]):
        score += 10
    # Sponsorship evidence: A=20, B=14, C=8
    ev = job.get("sponsorship_evidence", "C_ask_recruiter")
    score += {"A_verified_posting": 20, "B_sponsor_history": 14, "C_ask_recruiter": 8}.get(ev, 8)
    # Location bonus: Michigan / Remote US
    loc = job.get("location", "")
    if "Detroit" in loc or "Michigan" in loc or "Remote" in loc or "MI" in loc:
        score += 6
    # Seniority penalty: KD = 4+ years. Senior/Lead/Manager/Staff/
    # Principal/Director titles (usually 7-10 years asked) are stretch.
    if seniority_of(job["title"]) == "stretch":
        score -= 20
    return max(0, min(100, score))


def main():
    check_only = "--check" in sys.argv
    sponsors = {}
    with open(ROOT / "sponsors.csv", newline="") as f:
        for row in csv.DictReader(f):
            sponsors[row["employer"].lower()] = row

    kept, dropped = [], []
    for job in SEED:
        reason = is_excluded(job)
        if reason:
            dropped.append((job["id"], reason))
            continue
        if not is_cyber_title(job["title"]):
            dropped.append((job["id"], "not a cyber title"))
            continue
        job = dict(job)
        job["fit_score"] = fit_score(job)
        job["seniority"] = seniority_of(job["title"])
        # Sponsor lookup: match "Amazon" against "Amazon.com Services LLC",
        # "Deloitte" against "Deloitte LLP", etc.
        perm = "Unknown"
        jl = job["employer"].lower()
        for key, row in sponsors.items():
            if jl in key or key.startswith(jl):
                perm = row.get("perm_status_oct_2026", "Unknown")
                break
        job["perm_status"] = perm
        kept.append(job)

    # Core jobs always rank above stretch jobs, regardless of score:
    # a keyword-heavy Senior role (e.g. 10 keywords) must never sit
    # above a core job. Within each group, sort by fit score desc.
    kept.sort(key=lambda j: (j["seniority"] != "core", -j["fit_score"], j.get("posted", "")))

    print(f"Run date: {date.today().isoformat()}")
    print(f"Kept: {len(kept)}  Dropped: {len(dropped)}  Core: {sum(1 for j in kept if j['seniority']=='core')}  Stretch: {sum(1 for j in kept if j['seniority']=='stretch')}")
    for j in kept:
        print(f"  {j['fit_score']:3d}  [{j['seniority']}]  {j['employer']} — {j['title']} ({j['location']}) [{j['sponsorship_evidence']}]")
    for job_id, reason in dropped:
        print(f"  DROP {job_id}: {reason}")

    if check_only:
        return 0

    # jobs.json
    (ROOT / "jobs.json").write_text(json.dumps(kept, indent=2))

    # jobs.csv
    with open(ROOT / "jobs.csv", "w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["fit_score", "seniority", "employer", "title", "location", "salary", "posted", "closes", "sponsorship_evidence", "perm_status", "url"],
        )
        w.writeheader()
        for j in kept:
            w.writerow({k: j.get(k, "") for k in w.fieldnames})

    # jobs.md
    lines = []
    lines.append("# H-1B Cybersecurity Jobs — curated for Karan Darji\n")
    lines.append(f"_Last run: {date.today().isoformat()} — cyber only, resume-scored, H-1B sponsors only._\n")
    lines.append("**Filter:** cyber-security titles only. Fit score = resume keyword matches (CrowdStrike, Defender, Splunk, Sentinel, Qualys, Intune, Entra, Zero Trust, Detection, SIEM, VAPT, AI security, KQL, Python) + target-title match + sponsorship evidence + Michigan / Remote bonus, MINUS 20 for Senior/Lead/Manager/Staff/Principal/Director titles. Max 100.\n")
    lines.append("**Core vs Stretch:** CORE = non-senior title, ~3-5 years asked — these are the jobs KD can actually get. STRETCH = Senior/Lead/Manager/Staff/Principal title or 7+ years asked — listed below the core jobs, never ranked above them. Skill keywords alone do not make a job core.\n")
    lines.append("**Sponsorship evidence:** A = posting states sponsorship · B = employer filed certified H-1B LCAs for security/cyber titles in FY2025 (DOL) — confirm for this specific role · C = large sponsor employer, posting silent — ask recruiter before applying.\n")
    lines.append("**PERM warning (Oct 8, 2026):** Microsoft, Adobe, Cognizant, Infosys, Tata, Wipro, HCL, Capgemini are suspended from PERM (green-card) sponsorship, no end date. H-1B is a different filing — they can still file H-1B — but long-term green-card path is blocked there for now. See `trends.md`.\n")
    lines.append("**Excluded on purpose:** roles saying US Citizen only / will not sponsor / no sponsorship / TS/SCI / GovCloud. Examples in `excluded.md`.\n")
    for j in kept:
        lines.append(f"## {j['fit_score']}/100 — {j['title']} [{j['seniority'].upper()}]")
        lines.append(f"- **Employer:** {j['employer']} · **Location:** {j['location']} · **Salary:** {j.get('salary','—')}")
        lines.append(f"- **Posted:** {j.get('posted','—')} · **Closes:** {j.get('closes','—')} · **Sponsorship:** {j['sponsorship_evidence']} — {j.get('sponsorship_note','')}")
        lines.append(f"- **PERM status:** {j.get('perm_status','Unknown')}")
        lines.append(f"- **Why it fits KD:** {j.get('why_fit','')}")
        lines.append(f"- **Resume keywords:** {', '.join(j.get('keywords_matched', []))}")
        lines.append(f"- **Apply / source:** {j['url']}")
        if j.get("also_at"):
            lines.append(f"- **Also listed at:** {j['also_at']}")
        lines.append("")
    (ROOT / "jobs.md").write_text("\n".join(lines))
    print("Wrote jobs.md, jobs.csv, jobs.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
