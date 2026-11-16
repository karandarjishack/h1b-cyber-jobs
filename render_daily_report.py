#!/usr/bin/env python3
"""Generate a seven-day offline HTML report from the ATS scan plus labeled prior research."""
import html
import json
from datetime import date
from pathlib import Path
ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "docs/daily.json").read_text())
day = data["window"]["to"]
date.fromisoformat(day)
# Include recently catalogued roles as clearly un-reverified entries.
# The ATS-only scan remains separate: do NOT claim old listings were checked today.
history = json.loads((ROOT / "docs/history.json").read_text()) if (ROOT / "docs/history.json").exists() else []
older_recent = [
    {**x, "prior_record": True,
     "review_reasons": list(x.get("review_reasons") or []) +
     ["Previously catalogued; application URL and exact-role sponsorship not rechecked by today's ATS scan"]}
    for x in history
    if x.get("posted") and data["window"]["from"] <= x["posted"] <= day
]
ats_recent = list(data.get("verified_history", [])) + list(data.get("research_pending", []))
researched_file = ROOT / "docs/research/latest.json"
researched = json.loads(researched_file.read_text()).get("jobs", []) if researched_file.exists() else []
newer_research = [j for j in researched if j.get("posted") and data["window"]["from"] <= j["posted"] <= day]
all_rows = older_recent + ats_recent + newer_research
exclusions_file = ROOT / "docs/research/exclusions.json"
exclusions = json.loads(exclusions_file.read_text()).get("exclusions", []) if exclusions_file.exists() else []
def is_disqualified(job):
    return any(
        e.get("decision") == "exclude" and
        str(job.get("employer") or "").strip().casefold() == str(e.get("employer") or "").strip().casefold() and
        str(job.get("title") or "").strip().casefold() == str(e.get("title") or "").strip().casefold()
        for e in exclusions
    )
removed_by_review = sum(is_disqualified(x) for x in all_rows)
all_rows = [x for x in all_rows if not is_disqualified(x)]
deduped = {}
for j in all_rows:
    company = str(j.get("employer", "")).strip().lower()
    role = str(j.get("title", "")).strip().lower()
    location = str(j.get("location", "")).strip().lower()
    original = str(j.get("url") or "").split("?")[0].rstrip("/").lower()
    key = original or (company + "|" + role + "|" + location)
    if key in deduped:
        previous = deduped[key]
        updated = {**previous, **{k: v for k, v in j.items() if v not in (None, "", [])}}
        # A fresh ATS record replaces the stale catalog verification flag.
        if not j.get("prior_record"):
            updated["prior_record"] = False
            updated["review_reasons"] = j.get("review_reasons", [])
        deduped[key] = updated
    else:
        deduped[key] = j
jobs = sorted(deduped.values(), key=lambda x: (x.get("posted") or "", x.get("fit_score") or 0), reverse=True)
def esc(s):
    return html.escape(str(s if s is not None else "—"), quote=True)
def link(url, title):
    if not str(url or "").startswith("https://"):
        return "<span class='muted'>Not verified</span>"
    return '<a target="_blank" rel="noopener noreferrer" href="' + esc(url) + '">' + esc(title) + '</a>'
cards = []
for j in jobs:
    grade = str(j.get("sponsorship_evidence") or "C")
    grade = "A" if grade.startswith("A") else "B" if grade.startswith("B") else "C"
    pending = bool(j.get("review_reasons")) or grade == "C" or j.get("prior_record")
    subject = "Previous research: recheck" if j.get("prior_record") else ("Research needed" if pending else "Employer H-1B history")
    manager = j.get("hiring_manager_name")
    contact = (esc(manager) + " (" + esc(j.get("hiring_manager_confidence") or "Unverified") + ")") if manager else "Not identified"
    note = "; ".join(j.get("review_reasons", []))
    cards.append("""
    <article class="card">
      <div class="row"><div><div class="firm">""" + esc(j.get("employer")) + """</div>
      <h2>""" + esc(j.get("title")) + """</h2><p>""" + esc(j.get("location")) + """</p></div>
      <span class="badge">""" + esc(subject) + """</span></div>
      <dl><div><dt>Originally posted</dt><dd>""" + esc(j.get("posted")) + """</dd></div>
      <div><dt>Salary</dt><dd>""" + esc(j.get("salary") or "Not published") + """</dd></div>
      <div><dt>Resume fit</dt><dd>""" + esc(str(j.get("fit_score")) + "/100") + """</dd></div>
      <div><dt>Experience</dt><dd>""" + esc(str(j.get("years_required")) + "+ years" if j.get("years_required") is not None else "Not confirmed") + """</dd></div></dl>
      <p><strong>Technical fit:</strong> """ + esc(j.get("why_fit")) + """</p>
      <p><strong>H-1B:</strong> Grade """ + esc(grade) + """ — """ + esc(j.get("sponsorship_note") or "Role-specific H-1B transfer not verified") + """</p>
      <p><strong>PERM:</strong> """ + esc(j.get("perm_status") or "Not verified") + """; no specific vacancy approval confirmed.</p>
      <p><strong>Hiring manager:</strong> """ + contact + """ — no manager connection assumed.</p>
      <p><strong>Job requisition:</strong> """ + esc(j.get("requisition_id") or "Not established") + """</p>
      """ + ("<p><strong>Checks pending:</strong> " + esc(note) + "</p>" if note else "") + """
      <p>""" + link(j.get("url"), "Open previously catalogued apply link (recheck)" if j.get("prior_record") else "Open current ATS application link") + """</p>
    </article>""")
body = "\n".join(cards) if cards else '<div class="empty">No qualifying new openings were independently confirmed in this scan. This is not evidence that the wider web has no jobs.</div>'
html_text = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cybersecurity job intelligence — """ + esc(day) + """</title>
<style>body{font:14px/1.65 -apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif;background:#f5f7fb;color:#1a2a44;margin:0;padding:36px 14px}.wrap{max-width:900px;margin:auto}h1{font-size:29px;line-height:1.2}h2{font-size:18px;margin:7px 0 2px}.muted,dt,.firm{color:#6d7d95}.firm{font-weight:750;text-transform:uppercase;letter-spacing:.6px;font-size:11px}.card,.empty{background:white;border:1px solid #e0e8f2;border-radius:17px;padding:23px;margin:14px 0}.row{display:flex;justify-content:space-between;gap:10px;align-items:start;flex-wrap:wrap}.badge{font-size:11px;color:#825d0b;background:#fff2df;border-radius:20px;padding:5px 10px}dl{display:grid;grid-template-columns:repeat(2,1fr);gap:9px;background:#f6f8fb;border-radius:10px;padding:14px}dd{font-weight:700;margin:2px 0}dt{font-size:11px}p{margin:10px 0}a{color:#2e57c9;font-weight:700}.note{background:#e8f0ff;border-radius:12px;padding:14px}.footer{color:#68778e;font-size:12px;padding:20px 0}@media(max-width:500px){dl{grid-template-columns:1fr}}</style>
</head><body><div class="wrap"><p><a href="../index.html">Back to interactive dashboard</a></p>
<h1>Cybersecurity intelligence — """ + esc(day) + """</h1>
<p class="note">Window: """ + esc(data["window"]["from"]) + """ to """ + esc(data["window"]["to"]) + """. Newest postings first. A means vacancy mentions sponsorship; B indicates historical cybersecurity-title LCAs; C needs recruiter confirmation. No company history alone confirms transfer or PERM. Job-board coverage is incomplete.</p>
<p>""" + str(len(jobs)) + """ non-excluded recent job record(s) (""" + str(removed_by_review) + """ source-reviewed ineligible removed): """ + str(len(older_recent)) + """ from earlier research (NOT reverified), """ + str(len(ats_recent)) + """ from the current ATS scan. Source boards responding: """ + str(sum(1 for x in data.get("sources", []) if x.get("status") == "ok")) + """.</p>
""" + body + """<p class="footer">This report combines available ATS results with earlier researched records dated within the seven-day window. Prior records are NOT a guarantee that a vacancy remains open; Never send an outreach message saying you applied before actually doing so. Verify links and sponsorship with the recruiting team.</p></div></body></html>"""
folder = ROOT / "docs/reports"
folder.mkdir(parents=True, exist_ok=True)
(folder / (day + ".html")).write_text(html_text)
(folder / "latest.html").write_text(html_text)
print("Generated HTML snapshot for", day, "with", len(jobs), "postings")
