#!/usr/bin/env python3
"""Free, evidence-first cybersecurity job discovery.

Public Greenhouse/Lever/Ashby APIs and opportunistic Workday public career
feeds. Never treats historical employer H-1B activity as a vacancy guarantee.
No paid API, credentials, scraping bypass, personal data or invented contacts.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
TIMEZONE = ZoneInfo("America/Detroit")
USER_AGENT = "CyberJobs/3.0 (public employer job feeds; no authentication)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}
KEYWORDS = json.loads((ROOT / "kd_profile.json").read_text(encoding="utf-8"))["must_have_keywords"]
GOOD_TITLE = re.compile(
    r"cyber|(?:^|[\s/-])security|detection|threat hunt|threat intel|"
    r"incident response|penetration|pentest|vulnerabilit|red team|blue team|forensic|"
    r"devsecops|SOC analyst|SIEM|SOAR|IAM engineer|zero trust|malware", re.I)
SENIOR_TITLE = re.compile(r"\b(?:senior|sr\.?|staff|principal|lead|manager|director|head|chief|vp|PMTS|LMTS)\b", re.I)
NON_CYBER_TITLE = re.compile(
    r"\b(?:sales|account executive|business development|customer success|recruiter|"
    r"talent acquisition|physical security|security guard|security officer|"
    r"loss prevention|surveillance countermeasures|TSCM|"
    r"partner enablement|marketing|pre.sales)\b", re.I)
YEARS = re.compile(r"\b(\d{1,2})\s*(?:\+|[-–]\s*\d{1,2}|to\s+\d{1,2})?\s*(?:years?|yrs?)\s+(?:(?:of|in)\s+)?(?:relevant\s+|professional\s+|hands.on\s+|work\s+|industry\s+)?experience\b", re.I)
NEGATIVE_VISA = re.compile(
    r"(?:will not|does not|do not|cannot|unable to|not able to|no)\s+"
    r"(?:offer\s+|provide\s+|consider\s+|support\s+)?(?:employment\s+|work\s+|visa\s+|immigration\s+)?sponsor(?:ship)?|"
    r"(?:no|without)\s+(?:visa\s+|immigration\s+|employment\s+)?sponsor(?:ship)?|"
    r"(?:u\.?s\.?|united states)\s+citizen(?:ship)?\s+(?:only|required)|"
    r"(?:active\s+)?(?:ts/sci|secret\s+clearance)\s+required|"
    r"must\s+be\s+(?:a\s+)?(?:u\.?s\.?\s+citizen|permanent resident)", re.I)
POSITIVE_VISA = re.compile(
    r"we\s+(?:do\s+)?(?:offer|provide|support|sponsor)\s+(?:work\s+|visa\s+|immigration\s+)?(?:visa\s+)?sponsor(?:ship|s)?|"
    r"(?:visa|immigration|h-?1b)\s+sponsor(?:ship)?\s+(?:is\s+)?(?:available|offered|provided|supported)|"
    r"(?:eligible|available)\s+for\s+(?:visa|immigration|h-?1b)\s+sponsor(?:ship)?", re.I)
NOT_US = re.compile(r"\b(?:uk only|europe only|emea only|canada only|india only|apac only)\b", re.I)
FOREIGN = re.compile(r"\b(?:united kingdom|london|canada|toronto|vancouver|india|bengaluru|hyderabad|berlin|france|germany|dublin|ireland|singapore|australia)\b", re.I)
USA = re.compile(r"\b(?:united states|u\.?s\.?a?\.?|america|michigan|detroit|chicago|new york|"
                 r"california|seattle|washington|illinois|texas|virginia|new jersey|"
                 r"connecticut|new hampshire|boston|austin|denver|atlanta|arlington)\b", re.I)
REMOTE = re.compile(r"\b(?:remote|hybrid)\b", re.I)
ALLOWED_HOSTS = ("boards.greenhouse.io", "job-boards.greenhouse.io", "greenhouse.io",
                 "jobs.lever.co", "lever.co", "jobs.ashbyhq.com", "ashbyhq.com", "myworkdayjobs.com")
BAD_APPLY = {"linkedin.com", "indeed.com", "ziprecruiter.com", "glassdoor.com",
             "dice.com", "monster.com", "jooble.org", "jobicy.com"}
CORE_GREENHOUSE = [
    "sentry", "plaid", "coinbase", "cloudflare", "jrmconstructionmanagementllc",
    "oura", "pinterest", "stripe", "reddit", "figma", "notion", "discord",
    "robinhood", "chime", "samsara", "instacart", "affirm", "elastic",
    "datadog", "snowflake", "scaleai", "gusto", "okta", "brex",
    "doordash", "anthropic", "writer", "lyft", "hubspot",
]
CORE_ASHBY = ["kin", "linear", "ramp", "retool", "webflow", "writer", "anthropic",
              "openai", "notion", "mercor", "cohere"]
CORE_LEVER = ["coalfire", "netlify", "palantir", "motive", "postman"]
COMPANIES = {
    "oura": "Oura", "writer": "WRITER", "jrmconstructionmanagementllc": "JRM Construction Management",
    "geotab": "Geotab", "doordashusa": "DoorDash", "cloudflare": "Cloudflare",
    "spotify": "Spotify", "snowflake": "Snowflake", "crowdstrike": "CrowdStrike",
    "salesforce": "Salesforce", "unisys": "Unisys", "anthropic": "Anthropic",
    "openai": "OpenAI", "coalfire": "Coalfire", "plaid": "Plaid",
}
# Explicit verified-name-to-legal-entity aliases only. No fuzzy substring match.
LEGAL = {
    "amazon": "Amazon.com Services LLC", "aws": "Amazon Web Services Inc",
    "microsoft": "Microsoft Corporation", "ey": "Ernst & Young U.S. LLP",
    "accenture": "Accenture LLP", "visa": "Visa Inc", "meta": "Meta Platforms Inc",
    "crowdstrike": "CrowdStrike Inc", "crowdstrike inc": "CrowdStrike Inc",
    "jrm construction management": "JRM Construction Management LLC",
    "citi": "Citibank N.A.", "google": "Google LLC",
}
TODAY = datetime.now(TIMEZONE).date()


class HTMLToText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, value):
        self.parts.append(value)


def clean_markup(value):
    parser = HTMLToText()
    parser.feed(html.unescape(str(value or "")))
    return re.sub(r"\s+", " ", html.unescape(" ".join(parser.parts))).strip()


def get_json(url, payload=None, attempts=2):
    """GET or POST public listing JSON with bounded retry. No credentials."""
    data = json.dumps(payload).encode() if payload is not None else None
    headers = dict(HEADERS)
    if payload is not None:
        headers["Content-Type"] = "application/json"
    last = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, data=data, headers=headers,
                                             method="POST" if data is not None else "GET")
            with urllib.request.urlopen(request, timeout=12) as response:
                return json.load(response)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as e:
            last = e
            if attempt < attempts - 1 and getattr(e, "code", 503) in (429, 500, 502, 503, 504):
                time.sleep(0.6 * (attempt + 1))
            else:
                break
    raise RuntimeError("Public job feed unavailable: " + type(last).__name__ + " " + str(last)[:100])


def date_only(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except (TypeError, ValueError):
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None


def workday_relative(text, today=None):
    """Convert Workday's relative label to a date with *approximate* provenance."""
    today = today or TODAY
    s = str(text or "").lower()
    if "today" in s or "just posted" in s:
        return today
    if "yesterday" in s:
        return today - timedelta(days=1)
    m = re.search(r"(?:posted\s+)?(\d+)\s*(?:days?|d)\s*ago\b", s)
    if m:
        return today - timedelta(days=int(m.group(1)))
    return None


def direct_url(u):
    """Disallow aggregator application destinations; ATS-hosted URLs are direct."""
    p = urllib.parse.urlparse(str(u or ""))
    if p.scheme != "https" or not p.netloc:
        return False
    host = (p.hostname or "").lower()
    return not any(host == x or host.endswith("." + x) for x in BAD_APPLY)


def is_cyber(title):
    return (bool(GOOD_TITLE.search(title or "")) and not bool(SENIOR_TITLE.search(title or ""))
            and not bool(NON_CYBER_TITLE.search(title or "")))


def board_catalog():
    """Only public ATS paths already configured or documented in this repo."""
    sets = {
        "greenhouse": set(CORE_GREENHOUSE),
        "ashby": set(CORE_ASHBY),
        "lever": set(CORE_LEVER),
        "workday": set(),
        "smartrecruiters": set(),
    }
    for path in ("jobs_seed.json", "docs/history.json", "held_jobs.json",
                 "jobs_out_of_band_2026-11-15.json", "jobs_stretch_archived_2026-11-15.json"):
        file = ROOT / path
        if not file.exists():
            continue
        try:
            known = json.loads(file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for job in known:
            u = urllib.parse.urlparse(str(job.get("url") or ""))
            host = (u.hostname or "").lower()
            pieces = [x for x in u.path.split("/") if x]
            if not pieces:
                continue
            if host in ("job-boards.greenhouse.io", "boards.greenhouse.io"):
                sets["greenhouse"].add(pieces[0].lower())
            elif host == "jobs.ashbyhq.com":
                sets["ashby"].add(pieces[0].lower())
            elif host == "jobs.lever.co":
                sets["lever"].add(pieces[0].lower())
            elif host == "jobs.smartrecruiters.com":
                sets["smartrecruiters"].add(pieces[0])
            elif host.endswith(".myworkdayjobs.com"):
                tenant = host.split(".")[0]
                site = pieces[1] if re.fullmatch(r"[a-z]{2}-[A-Z]{2}", pieces[0]) and len(pieces)>1 else pieces[0]
                if re.fullmatch(r"[A-Za-z0-9_]+", site) and re.fullmatch(r"[a-zA-Z0-9.-]+", host):
                    sets["workday"].add(host + "|" + tenant + "|" + site)
    return {k: sorted(v) for k, v in sets.items()}


def greenhouse(token):
    base = f"https://boards-api.greenhouse.io/v1/boards/{urllib.parse.quote(token)}/jobs"
    data = get_json(base + "?content=true")
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        raise ValueError("Malformed Greenhouse jobs feed")
    result, looked_up = [], 0
    for j in data["jobs"]:
        title = str(j.get("title") or "")
        if not is_cyber(title):
            continue
        published = j.get("first_published")
        record = j
        if not published and looked_up < 35 and j.get("id"):
            looked_up += 1
            try:
                # Greenhouse first_published is guaranteed on job-detail response,
                # not necessarily on board listing.
                detail = get_json(base + "/" + str(j["id"]))
                published = detail.get("first_published")
                record = {**j, **detail}
            except RuntimeError:
                pass
        result.append({
            "company": record.get("company_name") or COMPANIES.get(token, token),
            "title": title, "id": str(record.get("id") or ""), "location": (record.get("location") or {}).get("name", ""),
            "posted": published, "date_quality": "greenhouse_first_published" if published else "missing",
            "description": record.get("content") or "", "url": record.get("absolute_url") or "",
            "department": ", ".join(d.get("name", "") for d in record.get("departments") or []),
            "employment": None, "salary": None,
        })
    return base, result, len(data["jobs"])


def ashby(token):
    base = f"https://api.ashbyhq.com/posting-api/job-board/{urllib.parse.quote(token)}?includeCompensation=true"
    data = get_json(base)
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        raise ValueError("Malformed Ashby jobs feed")
    result = []
    for j in data["jobs"]:
        if not j.get("isListed", True) or not is_cyber(j.get("title", "")):
            continue
        compensation = j.get("compensation") or {}
        workplace = str(j.get("workplaceType") or "")
        location = str(j.get("location") or "")
        country = ((j.get("address") or {}).get("postalAddress") or {}).get("addressCountry") or ""
        if country.upper() in ("USA", "US", "UNITED STATES") and "US" not in location.upper():
            location += ", United States"
        if workplace.lower() == "remote" and not re.search("remote", location, re.I):
            location = "Remote — " + location
        result.append({
            "company": COMPANIES.get(token, token), "title": j.get("title"),
            "id": str(j.get("id") or j.get("jobUrl") or ""),
            "location": location, "posted": j.get("publishedAt"),
            "date_quality": "ashby_last_published",
            "description": j.get("descriptionPlain") or j.get("descriptionHtml") or "",
            "url": j.get("applyUrl") or j.get("jobUrl") or "",
            "salary": compensation.get("scrapeableCompensationSalarySummary"),
            "employment": j.get("employmentType"), "department": j.get("department") or "",
        })
    return base, result, len(data["jobs"])


def lever(token):
    base = f"https://api.lever.co/v0/postings/{urllib.parse.quote(token)}?mode=json"
    data = get_json(base)
    if not isinstance(data, list):
        raise ValueError("Malformed Lever jobs feed")
    result = []
    for j in data:
        if not is_cyber(j.get("text", "")):
            continue
        cat = j.get("categories") or {}
        parts = [j.get("descriptionPlain") or j.get("description") or "",
                 j.get("additionalPlain") or j.get("additional") or ""] + [
                     str(x.get("text") or "") for x in j.get("lists", [])]
        timestamp = j.get("createdAt")
        created = datetime.fromtimestamp(timestamp / 1000, timezone.utc).isoformat() if isinstance(timestamp,(int,float)) else None
        result.append({
            "company": COMPANIES.get(token, token), "title": j.get("text"),
            "id": str(j.get("id") or ""), "location": cat.get("location") or "",
            "posted": created, "date_quality": "lever_created_at" if created else "missing",
            "description": " ".join(parts), "url": j.get("applyUrl") or j.get("hostedUrl") or "",
            "salary": None, "employment": cat.get("commitment") or "",
            "department": cat.get("department") or "",
        })
    return base, result, len(data)


def workday(source):
    """Public Workday career data; date remains unverified if only relative text is given."""
    host, tenant, site = source.split("|", 2)
    qhost = urllib.parse.quote(host, safe=".")
    root = f"https://{qhost}/wday/cxs/{urllib.parse.quote(tenant)}/{urllib.parse.quote(site)}"
    seen, rows, total = set(), [], 0
    # Targeted queries avoid downloading thousands of non-security roles.
    for phrase in ("security", "cyber", "detection"):
        first = get_json(root + "/jobs", payload={"appliedFacets": {}, "limit": 20,
                                                  "offset": 0, "searchText": phrase})
        if not isinstance(first, dict):
            raise ValueError("Malformed Workday jobs feed")
        total += int(first.get("total") or 0)
        postings = first.get("jobPostings") or []
        for entry in postings:
            path = str(entry.get("externalPath") or "")
            if not path or path in seen or not is_cyber(entry.get("title", "")):
                continue
            seen.add(path)
            posted = workday_relative(entry.get("postedOn"))
            rows.append({"company": COMPANIES.get(tenant, tenant), "title": entry.get("title"),
                         "id": path, "location": entry.get("locationsText") or "",
                         "posted": posted.isoformat() if posted else None,
                         "date_quality": "workday_relative" if posted else "missing",
                         "description": "", "url": f"https://{host}/en-US/{site}{path}",
                         "salary": None, "employment": None, "department": None,
                         "_path": path})
    # Enrich only likely recent candidates; public CXS detail is one request each.
    for j in rows[:30]:
        if not j["posted"]:
            continue
        try:
            data = get_json(root + j["_path"])
            info = data.get("jobPostingInfo") or {}
            j["description"] = info.get("jobDescription") or ""
            j["employment"] = info.get("timeType")
            j["id"] = str(info.get("jobReqId") or j["id"])
            j["location"] = j["location"] or info.get("location") or ""
            exact = date_only(info.get("startDate"))
            if exact:
                j["posted"] = exact.isoformat()
                j["date_quality"] = "workday_start_date_unverified"
        except RuntimeError:
            pass
    for j in rows:
        j.pop("_path", None)
    return root + "/jobs", rows, total


def smartrecruiters(token):
    """Official public SmartRecruiters Posting API; releasedDate is not proven original."""
    company = urllib.parse.quote(token, safe="")
    base = "https://api.smartrecruiters.com/v1/companies/" + company + "/postings"
    data = get_json(base + "?q=security&limit=100&offset=0")
    if not isinstance(data, dict) or not isinstance(data.get("content"), list):
        raise ValueError("Malformed SmartRecruiters public postings feed")
    result, seen = [], set()
    for j in data["content"]:
        title = j.get("name") or ""
        uid = str(j.get("id") or "")
        if not is_cyber(title) or uid in seen:
            continue
        seen.add(uid)
        loc = j.get("location") or {}
        location = ", ".join(str(loc.get(v) or "") for v in ("city", "region", "country") if loc.get(v))
        desc = ""
        try:
            detail = get_json(base + "/" + urllib.parse.quote(uid, safe=""))
            sections = ((detail.get("jobAd") or {}).get("sections") or {})
            desc = " ".join(str(v.get("text") or "") for v in sections.values() if isinstance(v, dict))
        except RuntimeError:
            pass
        result.append({
            "company": token, "title": title, "id": uid,
            "location": location, "posted": j.get("releasedDate"),
            "date_quality": "smartrecruiters_released_unverified",
            "description": desc, "url": f"https://jobs.smartrecruiters.com/{company}/{urllib.parse.quote(uid, safe='')}",
            "salary": None, "employment": j.get("typeOfEmployment") or "FullTime",
            "department": (j.get("department") or {}).get("label") if isinstance(j.get("department"), dict) else None,
        })
    return base, result, int(data.get("totalFound") or len(data["content"]))


def fetch_board(kind, token):
    return {"greenhouse": greenhouse, "ashby": ashby, "lever": lever, "workday": workday,
            "smartrecruiters": smartrecruiters}[kind](token)


def salary_max(text):
    if not text:
        return None
    values = []
    for m in re.finditer(r"\$\s*(\d{2,3}(?:,\d{3})?)(\s?[kK])?\b", str(text)):
        n = int(m.group(1).replace(",", ""))
        if m.group(2):
            n *= 1000
        if 30000 <= n <= 1000000:
            values.append(n)
    return max(values, default=None)


def required_years(text):
    values = [int(n) for n in YEARS.findall(text or "") if 0 < int(n) <= 30]
    return min(values) if values else None


def sponsor_lookup(company, rows):
    name = str(company or "").strip().lower()
    legal = LEGAL.get(name, company)
    for row in rows:
        if str(row.get("employer") or "").casefold() != str(legal or "").casefold():
            continue
        count = str(row.get("security_h1b_filings_q4_fy2025") or "").strip()
        if count.isdecimal() and int(count) > 0:
            return {
                "grade": "B_sponsor_history",
                "entity": row["employer"],
                "note": f"Legacy local sponsors.csv records {count} security-title LCA filings in FY2025 Q4. "
                        "Employer legal-entity mapping and exact filing must be verified in official DOL data. "
                        "This job's H-1B transfer and future PERM are NOT confirmed.",
                "source": "sponsors.csv",
                "needs_review": "Legacy LCA source has no employer-specific official filing citation",
            }
        return None
    return None


def keyword_hits(title, description):
    blob = title + " " + description
    return [w for w in KEYWORDS if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", blob, re.I)]


def screen(item, kind, token, sponsors, today=None):
    """Return (job, rejection_reason). Unverified evidence stays pending."""
    today = today or TODAY
    title = str(item.get("title") or "").strip()
    if not is_cyber(title):
        return None, "not_core_cyber_title"
    posted = date_only(item.get("posted"))
    if not posted:
        return None, "unverifiable_posting_date"
    if not today - timedelta(days=6) <= posted <= today:
        return None, "outside_seven_day_window"
    link = str(item.get("url") or "")
    if not direct_url(link):
        return None, "not_direct_employer_application"
    desc = clean_markup(item.get("description"))
    location = str(item.get("location") or "").strip()
    if NOT_US.search(location) or (FOREIGN.search(location) and not USA.search(location)):
        return None, "not_eligible_US_location"
    if NEGATIVE_VISA.search(desc):
        return None, "explicit_no_sponsorship_or_citizenship_requirement"
    status = []
    if not USA.search(location):
        status.append("US employment eligibility/location must be confirmed")
    if not REMOTE.search(location) and not re.search(r"\b(?:Michigan|Detroit|Chicago)\b", location, re.I):
        # User can consider hybrid US opportunities, but the actual worksite must be verified.
        status.append("Remote/hybrid eligibility for Detroit-based candidate unconfirmed")
    employment = str(item.get("employment") or "")
    if employment:
        if re.search(r"\b(?:intern|contract|temporary|part.?time)\b", employment, re.I):
            return None, "not_full_time_direct_hire"
        if not re.search(r"full.?time|permanent", employment, re.I):
            status.append("Full-time employment type not confirmed")
    elif not re.search(r"full.?time|permanent employment", desc, re.I):
        status.append("Full-time employment type not confirmed")
    years = required_years(desc)
    if years is None:
        status.append("Minimum experience requirements not confirmed")
    elif years >= 6:
        if not (re.search(r"\bequivalent\b", desc, re.I) and re.search(r"CTF|bug.bounty", desc, re.I)):
            return None, "six_plus_years_experience"
        status.append("Experience equivalency exception requires recruiter review")
    cap = salary_max(item.get("salary"))
    if cap and cap > 250000:
        return None, "salary_above_user_cap"
    if not cap and salary_max(desc) and salary_max(desc) > 250000:
        status.append("Job description contains compensation above $250k; confirm relevant pay band")
    q = str(item.get("date_quality") or "missing")
    if q in ("ashby_last_published", "workday_relative", "workday_start_date_unverified",
          "smartrecruiters_released_unverified", "missing"):
        status.append("Original job posting date not independently verified; may be republished/approximate")
    evidence = None
    if POSITIVE_VISA.search(desc):
        evidence = {
            "grade": "A_verified_posting",
            "note": "Employer ATS posting refers to visa sponsorship. Confirm the specific H-1B transfer and PERM with recruiter.",
            "entity": str(item.get("company") or token), "source": link,
        }
    if evidence is None:
        evidence = sponsor_lookup(str(item.get("company") or token), sponsors)
    if evidence is None:
        evidence = {"grade": "C_ask_recruiter",
                    "note": "No independently verified matching cyber-title LCA or explicit job sponsorship. "
                            "Do NOT treat employer general H-1B filings as a sponsorship guarantee.",
                    "entity": str(item.get("company") or token), "source": None}
        status.append("Exact employing-entity H-1B sponsorship evidence missing")
    elif evidence.get("needs_review"):
        status.append(evidence["needs_review"])
    keywords = keyword_hits(title, desc)
    if len(keywords) < 2:
        status.append("Technical fit not sufficiently supported by job description")
    g = evidence["grade"]
    bonus = 20 if g.startswith("A") else 14 if g.startswith("B") else 0
    score = min(100, round(min(64, len(keywords) / max(1, len(KEYWORDS)) * 64) +
                           16 + bonus + (6 if re.search("remote|michigan|detroit", location, re.I) else 0)))
    company = str(item.get("company") or COMPANIES.get(token, token)).strip()
    uid = hashlib.sha256((kind + "|" + token + "|" + str(item.get("id") or link)).encode()).hexdigest()[:16]
    data = {
        "id": "ats-" + uid, "employer": company, "title": title,
        "location": location, "posted": posted.isoformat(),
        "posted_date_quality": q, "url": link,
        "salary": item.get("salary"), "years_required": years,
        "keywords_matched": keywords, "fit_score": score, "seniority": "core",
        "sponsorship_evidence": g, "sponsorship_note": evidence["note"],
        "sponsorship_entity": evidence["entity"], "sponsorship_source": evidence["source"],
        "perm_status": "Not verified", "department": item.get("department"),
        "requisition_id": str(item.get("id") or ""), "source_board": kind + ":" + token,
        "source_verified": True, "application_link_evidence": "Listed on public employer ATS, final redirect not independently verified",
        "hiring_manager_status": "Not identified", "hiring_manager_name": None,
        "hiring_manager_email": None, "hiring_post_url": None,
        "why_fit": ("Matched job-description skills: " + ", ".join(keywords[:8])) if keywords
                   else "Weak technical keyword match; needs manual review",
        "review_reasons": sorted(set(status)),
        "verification_status": "research_pending" if status else "employer_history_only",
    }
    return data, None


def main(now=None):
    today = now or datetime.now(TIMEZONE).date()
    cutoff = today - timedelta(days=6)
    with (ROOT / "sponsors.csv").open(newline="", encoding="utf-8-sig") as f:
        sponsor_rows = list(csv.DictReader(f))
    sources = board_catalog()
    records, health, excluded = [], [], Counter()
    begins = time.monotonic()
    futures = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        for kind, tokens in sources.items():
            for token in tokens:
                futures[pool.submit(fetch_board, kind, token)] = (kind, token)
        for result in as_completed(futures):
            kind, token = futures[result]
            name = kind + ":" + token
            try:
                endpoint, items, count = result.result()
                for item in items:
                    item["_source_kind"] = kind
                    item["_source_token"] = token
                records.extend(items)
                health.append({"name": name, "status": "ok",
                               "total_postings": count, "candidate_postings": len(items),
                               "url": endpoint})
            except Exception as exc:
                health.append({"name": name, "status": "error",
                               "error": type(exc).__name__ + ": " + str(exc)[:180]})
    successful = sum(x["status"] == "ok" for x in health)
    # Prevent an outage from replacing a healthy report with an empty dashboard.
    if successful < 8 or successful / max(1, len(health)) < 0.25:
        raise RuntimeError(f"Source degradation: only {successful}/{len(health)} employer boards responded; prior report retained")
    qualified, pending = {}, {}
    for item in records:
        job, reason = screen(item, item["_source_kind"], item["_source_token"], sponsor_rows, today)
        if reason:
            excluded[reason] += 1
            continue
        key = (job["employer"].casefold(), job["title"].casefold(), job["location"].casefold())
        dest = pending if job["review_reasons"] else qualified
        if key not in dest or (job["fit_score"], job["posted"]) > (dest[key]["fit_score"], dest[key]["posted"]):
            dest[key] = job
    sort = lambda x: (x["posted"], x["fit_score"])
    good = sorted(qualified.values(), key=sort, reverse=True)
    to_verify = sorted(pending.values(), key=sort, reverse=True)
    payload = {
        "engine_version": "3.0",
        "generated_at": datetime.now(TIMEZONE).isoformat(),
        "window": {"from": cutoff.isoformat(), "to": today.isoformat()},
        "verified_history": good, "research_pending": to_verify,
        "sources": sorted(health, key=lambda h:h["name"]),
        "quality": {
            "attempted_sources": len(health), "successful_sources": successful,
            "failed_sources": len(health) - successful,
            "title_matched_candidates": len(records),
            "eligible_after_structural_screen": len(good) + len(to_verify),
            "employer_evidence_shortlist": len(good), "requires_manual_review": len(to_verify),
            "excluded_by_reason": dict(sorted(excluded.items())),
            "run_seconds": round(time.monotonic()-begins, 2),
        },
        "disclaimer": "Sources are incomplete and some date fields are republished/approximate. "
        "Historical employer LCAs do not establish this vacancy will accept an H-1B transfer or PERM. "
        "Public professional contacts/hiring managers are not fabricated.",
    }
    outdir = ROOT / "docs"
    outdir.mkdir(parents=True, exist_ok=True)
    folder = outdir / "reports"
    folder.mkdir(parents=True, exist_ok=True)
    # Write only after all collection, screening, and quality checks succeed.
    content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    for path in (outdir / "daily.json", folder / (today.isoformat() + ".json")):
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
    print(json.dumps({"day": str(today), **payload["quality"]}, sort_keys=True))
    return payload


if __name__ == "__main__":
    main()
