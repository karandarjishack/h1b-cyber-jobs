#!/usr/bin/env python3
"""Public ATS discovery for seven-day cybersecurity jobs.

No paid keys and no speculative sponsorship or hiring manager assertions.
The ATS still exposing a posting is evidence it is listed, not proof its
individual requisition accepts transfers. Ambiguous items go to review.
"""
from __future__ import annotations
import csv
import hashlib
import html
import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
TODAY = datetime.now(ZoneInfo("America/Detroit")).date()
CUTOFF = TODAY - timedelta(days=6)
HEADERS = {"User-Agent": "KD-Cyber-Jobs/1.0 (+GitHub Actions; public job boards)", "Accept": "application/json"}
CYBER = re.compile(r"(?:cyber|security|detection|threat hunt|threat intelligence|incident response|penetration test|pentest|vulnerabilit|red team|blue team|forensic|devsecops|soc analyst|siem|soar|identity protection|iam engineer|zero trust|malware analyst)", re.I)
SENIOR = re.compile(r"\b(?:senior|sr\.?|staff|principal|lead|manager|director|head|chief|vp|vice president)\b", re.I)
NO_SPONSOR = re.compile(r"(?:will not|does not|cannot|unable to|not able to|no|without)\s+(?:offer\s+|provide\s+|consider\s+)?(?:visa\s+|immigration\s+)?sponsor(?:ship)?|(?:u\.?s\.?|united states)\s+citizen(?:ship)?\s+(?:only|required)|(?:active\s+)?(?:ts\/sci|secret clearance)\s+required|must\s+be\s+(?:a\s+)?(?:u\.?s\.?\s+citizen|permanent resident)", re.I)
YES_SPONSOR = re.compile(r"(?:we (?:offer|provide)|eligible for|available for)\s+(?:visa\s+|immigration\s+)?sponsor(?:ship)?|(?:h-?1b|visa)\s+sponsorship\s+(?:is\s+)?available", re.I)
YEARS = re.compile(r"\b(\d{1,2})\s*(?:\+|(?:-|–|to)\s*\d{1,2})?\s*(?:years|yrs)\s+(?:of\s+)?(?:relevant\s+|professional\s+|hands.on\s+|work\s+|industry\s+)?experience\b", re.I)
FULLTIME = re.compile(r"\bfull[\s-]?time\b|\bpermanent employment\b", re.I)
REMOTE = re.compile(r"\bremote\b|\bhybrid\b", re.I)
US = re.compile(r"\b(?:united states|usa|u\.s\.|michigan|detroit|chicago|new york|boston|seattle|san francisco|bay area|austin|denver|atlanta|arlington|washington,?\s*d\.?c\.?|california|illinois|virginia|texas|massachusetts|new jersey|connecticut|new hampshire)\b", re.I)
NON_US_ONLY = re.compile(r"\b(?:emea only|europe only|uk only|canada only|apac only|india only)\b", re.I)
BLOCKED_LINKS = ("linkedin.com", "indeed.com", "ziprecruiter.com", "glassdoor.com", "dice.com", "monster.com", "jobicy.com")
KEYWORDS = json.loads((ROOT / "kd_profile.json").read_text())["must_have_keywords"]

# Public job-board identifiers. Failures are counted in source health instead
# of silently claiming that an employer had zero openings.
BOARDS = {
    "greenhouse": [
        "sentry", "plaid", "coinbase", "cloudflare", "jrmconstructionmanagementllc",
        "oura", "pinterest", "stripe", "reddit", "figma", "notion", "discord",
        "robinhood", "chime", "samsara", "instacart", "affirm", "elastic",
        "datadog", "snowflake", "scaleai", "gusto", "okta", "brex",
        "doordash", "anthropic", "writer", "lyft", "hubspot"
    ],
    "ashby": [
        "kin", "linear", "ramp", "retool", "webflow", "writer", "anthropic",
        "openai", "notion", "mercor", "cohere"
    ],
    "lever": ["coalfire", "netlify", "palantir", "motive", "postman"],
}
ALIASES = {
    "amazon": "amazon.com services llc", "aws": "amazon web services inc",
    "ey": "ernst & young u.s. llp", "jpmorgan chase": "jpmorgan chase & co.",
    "citibank": "citibank n.a.", "meta": "meta platforms inc",
    "visa": "visa inc", "accenture": "accenture llp",
}
def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=16) as response:
        return json.load(response)

class Stripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.chunks = []
    def handle_data(self, data):
        self.chunks.append(data)
def strip_markup(raw):
    p = Stripper()
    p.feed(html.unescape(str(raw or "")))
    return re.sub(r"\s+", " ", html.unescape(" ".join(p.chunks))).strip()

def get_boards(kind, token):
    if kind == "greenhouse":
        endpoint = "https://boards-api.greenhouse.io/v1/boards/" + token + "/jobs?content=true"
        data = get_json(endpoint)
        result = []
        for j in data.get("jobs", []):
            posted = j.get("first_published")  # NEVER use updated_at as original-post date
            location = (j.get("location") or {}).get("name", "")
            result.append({"company": j.get("company_name") or token, "title": j.get("title"),
                           "id": str(j.get("id")), "location": location,
                           "posted": posted, "description": j.get("content") or "",
                           "url": j.get("absolute_url"), "department": ", ".join(
                               d.get("name", "") for d in (j.get("departments") or []))})
        return endpoint, result
    if kind == "ashby":
        endpoint = "https://api.ashbyhq.com/posting-api/job-board/" + token + "?includeCompensation=true"
        data = get_json(endpoint)
        result = []
        for j in data.get("jobs", []):
            if not j.get("isListed", True):
                continue
            salary = (j.get("compensation") or {}).get("scrapeableCompensationSalarySummary") or ""
            result.append({"company": token, "title": j.get("title"), "id": j.get("id") or j.get("jobUrl"),
                           "location": j.get("location") or "", "posted": j.get("publishedAt"),
                           "description": j.get("descriptionPlain") or j.get("descriptionHtml") or "",
                           "url": j.get("applyUrl") or j.get("jobUrl"),
                           "salary": salary, "employment": j.get("employmentType"),
                           "department": j.get("department") or "",
                           "reposted_date": True})
        return endpoint, result
    endpoint = "https://api.lever.co/v0/postings/" + token + "?mode=json"
    data = get_json(endpoint)
    result = []
    for j in data:
        cat = j.get("categories") or {}
        desc = " ".join([j.get("descriptionPlain") or j.get("description") or "",
                         j.get("additionalPlain") or j.get("additional") or ""] +
                        [x.get("text", "") for x in j.get("lists", [])])
        stamp = j.get("createdAt")
        posted = datetime.fromtimestamp(stamp / 1000, ZoneInfo("UTC")).date().isoformat() if isinstance(stamp, (int, float)) else None
        result.append({"company": token, "title": j.get("text"), "id": j.get("id"),
                       "location": cat.get("location", ""), "posted": posted,
                       "description": desc, "url": j.get("applyUrl") or j.get("hostedUrl"),
                       "employment": cat.get("commitment"), "department": cat.get("department") or ""})
    return endpoint, result

def sponsor_lookup(company):
    name = company.lower().strip()
    name = ALIASES.get(name, name)
    for row in SPONSORS:
        legal = row.get("employer", "").lower()
        if name == legal or (len(name) >= 5 and name in legal):
            count = row.get("security_h1b_filings_q4_fy2025", "")
            if count.isdigit() and int(count) > 0:
                return {"grade": "B_sponsor_history",
                        "note": "Historical FY2025 certified security-title LCAs: " + count +
                                " (sponsors.csv). Exact role H-1B transfer and PERM not confirmed.",
                        "entity": row.get("employer"), "source": "sponsors.csv"}
    return None

def date_only(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except ValueError:
            return None

def annual_max(text):
    found = []
    for num, suffix in re.findall(r"\$\s*(\d{2,3}(?:,\d{3})?)(\s?[kK])?\b", text):
        amt = float(num.replace(",", ""))
        if suffix.strip().lower() == "k":
            amt *= 1000
        if amt >= 30000:
            found.append(amt)
    return max(found) if found else None

def screen(item, kind, token):
    title = str(item.get("title") or "").strip()
    if not CYBER.search(title) or SENIOR.search(title):
        return None
    posted = date_only(item.get("posted"))
    if not posted or not (CUTOFF <= posted <= TODAY):
        return None  # unknown/older dates may not be presented as new
    url = str(item.get("url") or "")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc or any(p in parsed.netloc for p in BLOCKED_LINKS):
        return None
    desc = strip_markup(item.get("description"))
    location = str(item.get("location") or "").strip()
    status = []
    if NON_US_ONLY.search(location) or NON_US_ONLY.search(desc[:1200]):
        return None
    if not US.search(location):
        status.append("US work location not established")
    if not (REMOTE.search(location) or re.search(r"\b(Michigan|Detroit|Chicago)\b", location, re.I)):
        # Hybrid US roles may say 'Hybrid' elsewhere in the description.
        if not re.search(r"\bhybrid\b", desc[:1700], re.I):
            status.append("Eligible hybrid/remote location not established")
    if NO_SPONSOR.search(desc):
        return None
    typ = str(item.get("employment") or "")
    if typ and not re.search(r"full.?time|permanent", typ, re.I):
        return None
    if not typ and not FULLTIME.search(desc):
        status.append("Full-time classification not established")
    yrs = [int(n) for n in YEARS.findall(desc)]
    years = max(yrs) if yrs else None
    if years is None:
        status.append("Minimum experience not established")
    elif years >= 6:
        if not (re.search(r"\bequivalent\b", desc, re.I) and re.search(r"\bCTF\b|bug.bounty", desc, re.I)):
            return None
        status.append("Equivalent-experience exception requires manual review")
    pay = str(item.get("salary") or "")
    upper = annual_max(pay) or annual_max(desc)
    if upper and upper > 250000:
        return None
    evidence = None
    if YES_SPONSOR.search(desc) and not NO_SPONSOR.search(desc):
        evidence = {"grade": "A_verified_posting", "note": "Posting explicitly references sponsorship. Confirm H-1B transfer and PERM for this vacancy.", "entity": str(item.get("company") or token), "source": url}
    else:
        evidence = sponsor_lookup(str(item.get("company") or token))
    if evidence is None:
        status.append("Cybersecurity-title H-1B filing evidence or role-specific sponsorship missing")
        evidence = {"grade": "C_ask_recruiter", "note": "No independently confirmed cybersecurity H-1B filing for this employing entity; do not assume sponsorship.", "entity": str(item.get("company") or token), "source": None}
    if item.get("reposted_date"):
        status.append("Ashby publishedAt can reflect republishing, not proven original creation")
    matches = [x for x in KEYWORDS if x.lower() in (title + " " + desc).lower()]
    grade = evidence["grade"]
    bonus = 20 if grade.startswith("A_") else 14 if grade.startswith("B_") else 8
    score = min(100, round((len(matches) / max(1, len(KEYWORDS))) * 64 + 16 + bonus + (6 if REMOTE.search(location) or re.search("michigan|detroit", location, re.I) else 0)))
    seed = str(item.get("company") or token) + "|" + str(item.get("id")) + "|" + title
    uid = "ats-" + hashlib.sha256(seed.encode()).hexdigest()[:16]
    return {"id": uid, "employer": str(item.get("company") or token).title(),
            "title": title, "location": location, "posted": posted.isoformat(),
            "url": url, "salary": pay or None, "years_required": years,
            "keywords_matched": matches, "fit_score": score, "seniority": "core",
            "sponsorship_evidence": grade, "sponsorship_note": evidence["note"],
            "sponsorship_entity": evidence["entity"], "sponsorship_source": evidence["source"],
            "perm_status": "Unverified", "department": item.get("department") or None,
            "requisition_id": str(item.get("id") or ""), "source_board": kind + ":" + token,
            "source_verified": True, "hiring_manager_status": "Not identified",
            "why_fit": "Matched skills: " + (", ".join(matches[:7]) if matches else "Limited keyword overlap; manual fit review needed"),
            "review_reasons": status, "verification_status": "research_pending" if status else "employer_h1b_history"}

def main():
    global SPONSORS
    with (ROOT / "sponsors.csv").open(newline="") as f:
        SPONSORS = list(csv.DictReader(f))
    queues = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = {pool.submit(get_boards, kind, board): (kind, board) for kind, boards in BOARDS.items() for board in boards}
        for task in as_completed(jobs):
            kind, board = jobs[task]
            try:
                endpoint, postings = task.result()
                queues.append({"name": kind + ":" + board, "status": "ok", "total_postings": len(postings), "url": endpoint})
                for item in postings:
                    item["_kind"] = kind
                    item["_board"] = board
                    ALL_POSTINGS.append(item)
            except Exception as exc:
                queues.append({"name": kind + ":" + board, "status": "error", "error": type(exc).__name__ + ": " + str(exc)[:130]})
    if not any(x["status"] == "ok" for x in queues):
        raise RuntimeError("All source boards failed; refusing to overwrite the last valid daily report")
    seen = set()
    qualified, pending = [], []
    for p in ALL_POSTINGS:
        j = screen(p, p["_kind"], p["_board"])
        if not j:
            continue
        key = (j["employer"].lower(), j["title"].lower(), j["location"].lower())
        if key in seen:
            continue
        seen.add(key)
        if j["review_reasons"] or j["sponsorship_evidence"] == "C_ask_recruiter":
            pending.append(j)
        else:
            qualified.append(j)
    # Historical B does NOT mean role-specific sponsorship verified.
    qualified.sort(key=lambda x: (x["posted"], x["fit_score"]), reverse=True)
    pending.sort(key=lambda x: (x["posted"], x["fit_score"]), reverse=True)
    result = {"generated_at": datetime.now(ZoneInfo("America/Detroit")).isoformat(),
              "window": {"from": CUTOFF.isoformat(), "to": TODAY.isoformat()},
              "verified_history": qualified, "research_pending": pending,
              "sources": sorted(queues, key=lambda x: x["name"]),
              "disclaimer": "Provider coverage is partial. Grade B means employer has historical cyber-title LCA evidence, NOT role-specific H-1B transfer approval. Hiring managers and PERM remain unverified unless separately evidenced."}
    outdir = ROOT / "docs"
    outdir.mkdir(exist_ok=True)
    (outdir / "daily.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    dated = outdir / "reports"
    dated.mkdir(exist_ok=True)
    (dated / (TODAY.isoformat() + ".json")).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"date": str(TODAY), "boards_ok": sum(1 for x in queues if x["status"] == "ok"),
                      "boards_failed": sum(1 for x in queues if x["status"] != "ok"),
                      "screened_history": len(qualified), "pending": len(pending)}))
ALL_POSTINGS = []
SPONSORS = []
if __name__ == "__main__":
    main()
