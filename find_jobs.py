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
  5. YEARS BAND ONLY (Nov 15, 2026 — KD: "Make sure that it only
     includes 3 to 5 years of experience jobs"): the site lists ONLY
     jobs asking 2-5 years of experience. Postings asking 2-5 years
     or 2+ years include 3-5 in their band, and KD's 4+ years sits
     inside them. Jobs asking 6+ years are OUT (archived in
     jobs_out_of_band_2026-11-15.json, not deleted). Jobs whose years
     are not stated on the posting are HELD in held_jobs.json until
     the years are verified as 3-5. find_jobs.py enforces this: a seed
     job outside 2-5 years, or with years_required missing, is
     dropped from jobs.json. CORE vs STRETCH still applies inside the
     band: CORE = non-senior title + pay band topping under $250k;
     STRETCH = Senior/Lead/Manager/Staff/Principal title or a $250k+
     pay band — listed below the core jobs, never ranked above them.
     Skill keywords alone do NOT make a job relevant.
  6. DIRECT APPLY LINKS ONLY (Nov 14, 2026 — KD: "I need jobs from
     the original company website where i dont have to pay"): the
     apply URL must be the employer's own careers site or their ATS
     (amazon.jobs, Workday, Greenhouse, Lever, Ashby, jobsus.deloitte,
     jobs.bechtel, openai.com/careers, etc.). Aggregator links
     (Haystack, Jobicy, Dice, CareerBuilder, MilwaukeeJobs, Jobspresso,
     DreamWorkHQ, The Muse, Monster, Jooble, TheLadders, Remoterush,
     RemoteJobAssistant) are NOT apply links — they sit between KD and
     the employer and some charge to apply. A job with no verified
     direct link is HELD in held_jobs.json, never listed. find_jobs.py
     drops any seed job whose URL host is not a direct employer host.

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

# Direct employer hosts only (KD rule, Nov 14, 2026): the apply URL must
# live on the employer's own careers site or their ATS. Anything else is
# an aggregator and the job is held, not listed.
DIRECT_HOST_SUFFIXES = [
    "amazon.jobs",
    "myworkdayjobs.com",
    "job-boards.greenhouse.io",
    "jobsus.deloitte.com",
    "jobs.bechtel.com",
    "lever.co",
    "ashbyhq.com",
    "openai.com",
    "lifeatspotify.com",
    "careers.spglobal.com",
    "careers.instacart.com",
    "jobs.gm.com",
    "careers.doordash.com",
    "careers.jpmorganchase.com",
    "jobs.citi.com",
    "careers.meta.com",
    "careers.google.com",
    "jobs.cisco.com",
    "jobs.paloaltonetworks.com",
    "careers.ey.com",
    "careers.accenture.com",
    "jobs.visa.com",
    "careers.vanguard.com",
    # Added Nov 15, 2026 (sponsor sweep): employers' own careers sites.
    "stripe.com",
    "jobs.apple.com",
    "plaid.com",
    "sentry.io",
    # Added Nov 15, 2026 (coverage audit): employer careers sites + ATS
    # hosts for verified jobs — Deloitte, Snowflake, Comcast, Angi,
    # SmartRecruiters, Instacart, Cloudflare, Jacobs, WHOOP, Toshiba,
    # Unisys, Motiva, Tesla, IBM, Microsoft, Datadog, ServiceNow,
    # iCIMS, Taleo, Workable, Jobvite, BambooHR.
    "apply.deloitte.com",
    "careers.snowflake.com",
    "jobs.comcast.com",
    "angi.com",
    "smartrecruiters.com",
    "instacart.careers",
    "careers.cloudflare.com",
    "careers.jacobs.com",
    "careers.whoop.com",
    "careers.toshiba.com",
    "careers.unisys.com",
    "careers.motiva.com",
    "careers.tesla.com",
    "tesla.com",
    "careers.ibm.com",
    "careers.microsoft.com",
    "careers.datadoghq.com",
    "careers.servicenow.com",
    "icims.com",
    "taleo.net",
    "workable.com",
    "jobvite.com",
    "bamboohr.com",
    # Added Nov 15, 2026 (deep search): Stellantis, Bank of America, Coinbase,
    # Charles Schwab, AbbVie, Kirkland & Ellis + held-queue boards.
    "stellantis.com",
    "bankofamerica.com",
    "coinbase.com",
    "schwabjobs.com",
    "abbvie.com",
    "kirkland.com",
    "toasttab.com",
    "usbank.com",
    "unitedhealthgroup.com",
    "pypl.com",
    "abbott.com",
    "stryker.com",
    "netflix.com",
    "rubrik.com",
    "dropbox.com",
    "hashicorp.com",
    "scale.com",
    "okta.com",
    "sofi.com",
    "elastic.co",
    "circle.com",
]


def is_direct_link(url: str) -> bool:
    from urllib.parse import urlparse

    host = urlparse(url).netloc.lower()
    return any(host == s or host.endswith("." + s) for s in DIRECT_HOST_SUFFIXES)


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
            "compliance engineer",
            "vapt",
            # Added Nov 15, 2026 (sponsor sweep): genuine security titles
            # that don't contain "security engineer" — platform security,
            # data security, and identity roles are cyber roles.
            "platform security",
            "data security",
            "identity",
            # Added Nov 15, 2026 (coverage audit): genuine cyber titles the
            # gate was rejecting — Vulnerability Management Engineer,
            # Detection & Response Engineer, Incident Response Engineer,
            # SIEM/SOAR/DevSecOps/SOC Analyst/Security Architect/IAM/
            # Zero Trust/Threat Intel/Hunter/Malware/Forensics/Red Team/
            # GRC/Security Consultant, and "Software Engineer, Security".
            "incident response",
            "detection and response",
            "detection & response",
            "vulnerability management",
            "siem",
            "soar",
            "devsecops",
            "soc analyst",
            "security architect",
            "iam",
            "zero trust",
            "threat intel",
            "threat hunt",
            "malware",
            "forensic",
            "red team",
            "grc",
            "security consultant",
            "engineer, security",
            # Added Nov 15, 2026 (deep search): "Manual Ethical Hacker" and
            # "Vulnerability Identification Analyst" are genuine cyber roles
            # the gate was rejecting.
            "ethical hacker",
            "vulnerability identification",
            "vulnerability analyst",
        ]
    )


def is_excluded(job: dict) -> str | None:
    # Scan the posting's own title ONLY — never our annotations. why_fit
    # and sponsorship_note may mention an excluded role as a warning (e.g.
    # "do not confuse with the GovCloud role"), and scanning them silently
    # drops valid jobs. A job that is actually excluded is recorded with
    # the explicit `excluded` flag instead.
    hay = job.get("title", "").lower()
    for phrase in EXCLUDE:
        if phrase in hay:
            return phrase
    if job.get("excluded"):
        return "flagged excluded in seed"
    return None


SENIOR_WORDS = ["senior", "lead", "manager", "staff", "principal", "director", "head of"]


def seniority_of(title: str) -> str:
    t = title.lower()
    if any(w in t for w in SENIOR_WORDS):
        return "stretch"
    # "Sr." abbreviation (e.g. "Sr AI Software Security Engineer", Evolent)
    # — word-boundary match so it cannot fire inside another word.
    import re as _re
    if _re.search(r"\bsr\.?\b", t):
        return "stretch"
    return "core"


def pay_band_stretch(job: dict) -> bool:
    import re as _re
    nums = [int(n.replace(",", "")) for n in _re.findall(r"\$?(\d{3},\d{3}|\d{3,})", job.get("salary", ""))]
    return bool(nums) and max(nums) >= 250000


def fit_score(job: dict) -> int:
    """0-100 relevance score. Keyword matches + title match + sponsor
    evidence + location bonus, MINUS 20 for senior/lead/manager/staff/
    principal titles, MINUS 20 when the pay band tops $250k (a $300k+
    role expects senior/staff level no matter what the title says),
    MINUS 10 when the posting asks 5-6 years, MINUS 20 when it asks
    7+ years. KD has 4+ years, so a 7-10 year senior role is a
    stretch no matter how many keywords match."""
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
    # Pay-band penalty: a role topping $250k expects senior/staff level.
    import re as _re
    nums = [int(n.replace(",", "")) for n in _re.findall(r"\$?(\d{3},\d{3}|\d{3,})", job.get("salary", ""))]
    if nums and max(nums) >= 250000:
        score -= 20
    # Years-asked penalty, from the posting's own requirements text.
    # Skipped when the posting accepts equivalent experience (e.g.
    # Bechtel pentesting: 8+ years OR CTF / bug-bounty contributions).
    yrs = job.get("years_required")
    if isinstance(yrs, (int, float)) and not job.get("equivalent_experience"):
        if yrs >= 7:
            score -= 20
        elif yrs >= 5:
            score -= 10
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
        if not is_direct_link(job.get("url", "")):
            dropped.append((job["id"], "aggregator link — no verified direct employer apply link (held)"))
            continue
        # Years band (KD rule Nov 15, 2026): site lists only jobs asking
        # 2-5 years. 6+ years is out; unstated years is held, not listed.
        yrs = job.get("years_required")
        if not isinstance(yrs, (int, float)):
            dropped.append((job["id"], "years not stated — held until verified 3-5 years (KD rule Nov 15, 2026)"))
            continue
        if yrs < 2 or yrs > 5:
            dropped.append((job["id"], f"asks {int(yrs)}+ years — outside KD's 3-5 year band (Nov 15, 2026)"))
            continue
        job = dict(job)
        job["fit_score"] = fit_score(job)
        # Pay band tops $250k = senior/staff expectations, whatever the title says.
        yrs = job.get("years_required")
        years_stretch = isinstance(yrs, (int, float)) and yrs >= 7 and not job.get("equivalent_experience")
        job["seniority"] = "stretch" if seniority_of(job["title"]) == "stretch" or pay_band_stretch(job) or years_stretch else "core"
        # Core-only (KD rule Nov 15, 2026): stretch jobs are never listed.
        if job["seniority"] == "stretch":
            dropped.append((job["id"], "stretch role (senior title and/or $250k+ pay) — site is CORE only (KD rule Nov 15, 2026)"))
            continue
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
    kept.sort(key=lambda j: (j["seniority"] != "core", -j["fit_score"], j.get("posted") or ""))

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
    lines.append("**Years band (KD rule Nov 15, 2026):** the site lists ONLY jobs asking 2-5 years of experience — postings asking 2-5 years or 2+ years include 3-5 in their band, and KD's 4+ years sits inside them. Jobs asking 6+ years are archived in `jobs_out_of_band_2026-11-15.json`; jobs with unstated years are held until verified.\n")
    lines.append("**Core vs Stretch (inside the band):** CORE = non-senior title + pay band topping under $250k. STRETCH = Senior/Lead/Manager/Staff/Principal title or a $250k+ pay band — listed below the core jobs, never ranked above them. Skill keywords alone do not make a job core.\n")
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
