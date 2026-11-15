#!/usr/bin/env python3
"""Generate docs/index.html + docs/tracker.html for GitHub Pages from jobs.json.
Tracker state lives in the visitor's browser (localStorage, key h1b_tracker_v1)
— it is private to that browser, not sent to GitHub. Shared between both pages.

Design: dark professional theme (KD's cyber brand), red accent, no emojis in
headings. Every Apply button goes to the employer's own careers site or ATS —
no aggregators. Dates render as "Nov 13, 2026", never raw ISO.
"""
import json, html
from datetime import date
from pathlib import Path
ROOT = Path(__file__).parent
jobs = json.loads((ROOT / "jobs.json").read_text())
# Held count for the header: live holds only — the DoorDash entry is a
# CLOSED record, not a role waiting on a direct link.
try:
    _held = json.loads((ROOT / "held_jobs.json").read_text())
    held_n = len([h for h in _held if not str(h.get("held_reason", "")).startswith("CLOSED")])
except Exception:
    held_n = 0
verified_str = date.today().strftime("%b %-d, %Y")

def esc(s): return html.escape(str(s or "—"))

def fmt_date(iso):
    if not iso:
        return None
    try:
        y, m, d = (int(x) for x in str(iso).split("-"))
        return date(y, m, d).strftime("%b %-d, %Y")
    except Exception:
        return str(iso)

def salary_display(s):
    if not s or s.lower().startswith("not listed"):
        return "Salary not listed"
    return s

CSS = """
:root{--bg:#0b0f14;--panel:#111827;--panel2:#1f2937;--line:#2b3648;--text:#e8eef4;--muted:#9fb0c3;--red:#e11d48;--green:#22c55e;--amber:#f59e0b;--blue:#38bdf8}
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;margin:0;background:var(--bg);color:var(--text);font-size:15px;line-height:1.55}
header{background:var(--panel);padding:32px 20px 26px;border-bottom:3px solid var(--red)}
.eyebrow{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
header h1{margin:0;font-size:30px;line-height:1.2;letter-spacing:-.01em}
header p.sub{color:var(--muted);max-width:860px;margin:10px 0 0}
nav{margin-top:18px}
nav a{color:#fff;background:var(--red);padding:10px 16px;border-radius:8px;text-decoration:none;font-weight:700;display:inline-block;margin:6px 8px 0 0}
nav a.ghost{background:var(--panel2);border:1px solid var(--line)}
.wrap{max-width:960px;margin:0 auto;padding:20px}
.updated{color:var(--muted);font-size:13px;margin:14px 0 0}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0 6px}
.stat{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:12px 18px;min-width:110px}
.stat b{font-size:22px;display:block;line-height:1.1}
.stat span{color:var(--muted);font-size:12px}
.note{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--red);border-radius:10px;padding:16px 18px;margin:18px 0}
.note.warn{border-left-color:var(--amber)}
.note h2{margin:0 0 8px;font-size:16px}
.note ol{margin:6px 0 0;padding-left:20px}
.note p{margin:8px 0 0;color:var(--muted)}
.note p strong{color:var(--text)}
.snapshot{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0 4px}
.snap{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.snap b{font-size:17px;display:block}
.snap span{color:var(--muted);font-size:12px}
input,select,textarea{padding:10px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);box-sizing:border-box;font:inherit}
.filters{display:grid;grid-template-columns:2fr 1fr;gap:10px;margin:20px 0 4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px;margin:16px 0}
.card .topline{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap}
.employer{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:700}
.pills{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.pill{display:inline-block;padding:4px 10px;border-radius:999px;font-weight:700;font-size:12px;white-space:nowrap}
.pill.fit{background:var(--red);color:#fff}
.pill.core{background:#14532d;color:#bbf7d0}
.pill.stretch{background:#451a03;color:#fde68a}
.pill.status{background:var(--panel2);border:1px solid var(--line);color:var(--muted);font-weight:600}
.card h2{margin:10px 0 4px;font-size:21px;line-height:1.3}
.meta{color:var(--muted);margin:2px 0}
.meta .sep{margin:0 6px;color:#4b5a6e}
.bar{height:8px;background:var(--panel2);border-radius:999px;overflow:hidden;margin:14px 0 6px}
.bar div{height:100%;background:var(--green)}
.bar.stretchbar div{background:var(--amber)}
.barlabel{font-size:12px;color:var(--muted);display:flex;justify-content:space-between}
.kv{display:grid;grid-template-columns:110px 1fr;gap:4px 12px;margin:12px 0 0}
.kv dt{font-weight:700;font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;padding-top:2px}
.kv dd{margin:0}
.kw{display:inline-block;background:#1e3a5f;border:1px solid #2f5b8f;border-radius:999px;padding:3px 9px;margin:2px 2px 2px 0;font-size:12px}
.sector{display:inline-block;background:var(--panel2);border:1px solid var(--line);border-radius:999px;padding:3px 9px;font-size:12px;color:var(--muted)}
.actions{margin-top:16px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.apply{display:inline-block;background:var(--red);color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none;font-weight:700}
.apply:hover{background:#be123c}
.trackbtn{display:inline-block;background:var(--green);color:#052e12;padding:10px 16px;border-radius:8px;font-weight:700;border:0;cursor:pointer;font:inherit}
.trackbtn.applied{background:var(--panel2);color:var(--text);border:1px solid var(--line)}
.official{font-size:12px;color:var(--muted)}
a{color:#7dd3fc}
footer{color:var(--muted);padding:24px 20px 32px;text-align:center;font-size:13px}
footer p{margin:4px 0}
h2.section{font-size:18px;margin:28px 0 6px}
.tablewrap{overflow-x:auto;margin:16px 0}
table{width:100%;border-collapse:collapse;min-width:760px}
th,td{border:1px solid var(--line);padding:9px 10px;text-align:left;vertical-align:top}
th{background:var(--panel2);font-size:13px;text-transform:uppercase;letter-spacing:.04em}
tr.status-Applied td:first-child{border-left:4px solid var(--green)}
tr.status-Interview td:first-child{border-left:4px solid var(--blue)}
tr.status-Offer td:first-child{border-left:4px solid var(--amber)}
tr.status-Rejected td:first-child{border-left:4px solid var(--red)}
@media (max-width:640px){.kv{grid-template-columns:1fr}.kv dt{padding-top:8px}header h1{font-size:24px}.filters{grid-template-columns:1fr}}
"""

SHARED_JS = """
const KEY='h1b_tracker_v1';
function load(){try{return JSON.parse(localStorage.getItem(KEY))||{}}catch(e){return{}}}
function save(t){localStorage.setItem(KEY,JSON.stringify(t))}
function setStatus(id,status){const t=load();t[id]=t[id]||{};t[id].status=status;if(status==='Applied'&&!t[id].date)t[id].date=new Date().toISOString().slice(0,10);if(status==='Not applied'){t[id].date='';}save(t);if(document.getElementById('stats'))renderTracker();updateBadges();refreshCount();}
function setField(id,field,val){const t=load();t[id]=t[id]||{};t[id][field]=val;save(t);}
function updateBadges(){const t=load();document.querySelectorAll('[data-jobid]').forEach(el=>{const s=(t[el.dataset.jobid]||{}).status||'Not applied';const b=el.querySelector('.statuspill');if(b)b.textContent=s;const sel=el.querySelector('select.tracksel');if(sel)sel.value=s;const btn=el.querySelector('.trackbtn');if(btn){if(s==='Applied'){btn.textContent='Applied';btn.classList.add('applied');}else{btn.textContent='I have applied';btn.classList.remove('applied');}}});}
function exportCSV(){const t=load();let rows=[['Job','Employer','Location','Salary','Status','Date applied','Notes']];document.querySelectorAll('#trackbody tr').forEach(tr=>{const c=tr.querySelectorAll('td');if(c.length>=7)rows.push([...c].slice(0,7).map(x=>'"'+(x.querySelector('input,select,textarea')?.value||x.textContent).replace(/"/g,'""')+'"'));});const blob=new Blob([rows.map(r=>r.join(',')).join('\\n')],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='h1b-job-tracker.csv';a.click();}
"""

cards = []
for j in jobs:
    kws = "".join(f'<span class="kw">{esc(k)}</span>' for k in j.get("keywords_matched", []))
    ev = j.get("sponsorship_evidence", "")
    ev_map = {"A_verified_posting": ("A", "Posting states sponsorship"),
              "B_sponsor_history": ("B", "H-1B sponsor history"),
              "C_ask_recruiter": ("C", "Ask recruiter to confirm")}
    ev_letter, ev_label = ev_map.get(ev, ("?", ev))
    sector = f'<span class="sector">{esc(j["sector"])}</span>' if j.get("sector") else ""
    sen = j.get("seniority", "core")
    if sen == "core":
        sen_pill = '<span class="pill core">Core — 3–5 yr fit</span>'
        bar_cls = "bar"
    else:
        sen_pill = '<span class="pill stretch">Stretch — senior / 7+ yr</span>'
        bar_cls = "bar stretchbar"
    posted = fmt_date(j.get("posted")) or "—"
    closes = fmt_date(j.get("closes"))
    closes_txt = f'<span class="sep">·</span>Closes {esc(closes)}' if closes else ""
    domain = esc(j["url"].split("//", 1)[-1].split("/", 1)[0].replace("www.", ""))
    cards.append(f"""
    <article class="card" data-jobid="{esc(j['id'])}" data-employer="{esc(j['employer'])}">
      <div class="topline"><span class="employer">{esc(j['employer'])}</span>
      <span class="pills"><span class="pill fit">{j['fit_score']}/100 fit</span>{sen_pill}<span class="pill status statuspill">Not applied</span></span></div>
      <h2>{esc(j['title'])}</h2>
      <p class="meta">{esc(j['location'])}<span class="sep">·</span>{esc(salary_display(j.get('salary')))}<span class="sep">·</span>Posted {esc(posted)}{closes_txt}</p>
      <p class="meta">{sector}</p>
      <div class="{bar_cls}"><div style="width:{j['fit_score']}%"></div></div>
      <div class="barlabel"><span>Resume fit</span><span>{j['fit_score']}/100</span></div>
      <dl class="kv">
        <dt>Sponsorship</dt><dd><strong>{ev_letter} — {esc(ev_label)}.</strong> {esc(j.get('sponsorship_note',''))}</dd>
        <dt>Why it fits</dt><dd>{esc(j.get('why_fit',''))}</dd>
        <dt>Skills</dt><dd>{kws}</dd>
      </dl>
      <div class="actions">
        <a class="apply" href="{esc(j['url'])}" target="_blank" rel="noopener">Apply on the company's site →</a>
        <button class="trackbtn" onclick="setStatus('{esc(j['id'])}','Applied')">I have applied</button>
        <select class="tracksel" aria-label="Application status" onchange="setStatus('{esc(j['id'])}',this.value)"><option>Not applied</option><option>Saved</option><option>Applied</option><option>Interview</option><option>Offer</option><option>Rejected</option></select>
        <span class="official">Official posting — {domain}</span>
      </div>
    </article>""")

best = [j for j in jobs if j.get("seniority") == "core" and j.get("sponsorship_evidence") in ("A_verified_posting", "B_sponsor_history")][:3]
best_html = "".join(f"<li><strong>{j['fit_score']}/100 — {esc(j['title'])}</strong> · {esc(j['employer'])} · {esc(salary_display(j.get('salary')))} · {esc(j['location'])}</li>" for j in best)
core_n = sum(1 for j in jobs if j.get("seniority") == "core")
stretch_n = len(jobs) - core_n
top_fit = max(j['fit_score'] for j in jobs)
employers = sorted({j['employer'] for j in jobs})
emp_opts = "".join(f"<option>{esc(e)}</option>" for e in employers)
jrm = next((j for j in jobs if j['employer'].startswith('JRM')), None)
jrm_note = ""
if jrm:
    jrm_note = f"<p><strong>Best resume match overall:</strong> {esc(jrm['title'])} at JRM Construction Management ({jrm['fit_score']}/100) — but its sponsorship is evidence C, the weakest on this page. Confirm with the recruiter before applying; do not apply to a C job blind.</p>"

index_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Cybersecurity jobs with H-1B sponsorship, curated for Karan Darji and scored against his resume. Every apply link goes to the company's own careers site.">
<title>H-1B Cybersecurity Jobs — curated for Karan Darji</title><style>{CSS}</style></head><body>
<header><div class="wrap"><p class="eyebrow">Curated for Karan Darji · H-1B sponsors only · Cyber security only</p>
<h1>H-1B Cybersecurity Jobs</h1>
<p class="sub">Every role is scored against KD's resume — 4+ years in detection engineering, SIEM, EDR and VAPT — and every Apply button goes to the company's own careers site. No aggregators, nothing that charges to apply.</p>
<nav><a href="tracker.html">My Application Tracker →</a><a class="ghost" href="https://github.com/karandarjishack/h1b-cyber-jobs">GitHub repo</a></nav></div></header>
<div class="wrap">
<div class="stats"><div class="stat"><b>{len(jobs)}</b><span>jobs listed</span></div><div class="stat"><b>{core_n}</b><span>core · 3–5 yr fit</span></div><div class="stat"><b>{stretch_n}</b><span>stretch · senior+</span></div><div class="stat"><b>{top_fit}/100</b><span>top fit</span></div><div class="stat"><b id="appliedCount">0</b><span>applied · this browser</span></div></div>
<p class="updated">Last verified {verified_str} · Refreshes daily at 6:00 AM ET · {held_n} more roles held until their company apply link is verified</p>
<div class="note"><h2>Core picks — highest-fit core jobs with verified sponsorship</h2><ol>{best_html}</ol>{jrm_note}<p>Stretch jobs (senior title, 7+ years asked, or a $250k+ pay band) are listed below the core jobs. A senior title costs 20 points, so a stretch role never outranks a core job.</p></div>
<div class="note warn"><h2>Market snapshot</h2>
<div class="snapshot"><div class="snap"><b>343,981</b><span>H-1B registrations, FY2026 — down 55% from FY2024</span></div><div class="snap"><b>35%</b><span>selected in the FY2026 lottery</span></div><div class="snap"><b>$141,378</b><span>median security H-1B salary, Jul–Sep 2025 (1,093 filings)</span></div><div class="snap"><b>$100,000</b><span>new H-1B fee from FY2027, with a wage-weighted lottery</span></div></div>
<p><strong>PERM warning — Oct 8, 2026:</strong> Microsoft, Adobe, Cognizant, Infosys, Tata, Wipro, HCL and Capgemini are suspended from PERM (green-card) sponsorship, with no end date. H-1B is a separate filing — they can still file H-1B — but the green-card path is blocked there for now. PERM applications overall fell 22% in FY2025 (117,849 received).</p></div>
<div class="filters"><input id="q" placeholder="Search title, employer, keyword…" oninput="filterJobs()" aria-label="Search jobs"><select id="emp" onchange="filterJobs()" aria-label="Filter by employer"><option value="">All employers</option>{emp_opts}</select></div>
<div id="jobs">{''.join(cards)}</div>
<p id="none" style="display:none">No jobs match that search.</p>
<h2 class="section">Excluded on purpose</h2>
<p class="meta">Roles saying “US Citizen only”, “will not sponsor”, “no sponsorship”, TS/SCI clearance, or GovCloud were dropped. The full list is in the repo's <a href="https://github.com/karandarjishack/h1b-cyber-jobs/blob/main/excluded.md">excluded.md</a>.</p>
</div>
<footer><p>Sources: company careers pages, DOL LCA data (FY2025), USCIS Employer Data Hub. Data in <a href="https://github.com/karandarjishack/h1b-cyber-jobs">github.com/karandarjishack/h1b-cyber-jobs</a>.</p><p>Not affiliated with any employer listed. Application status is saved in your browser only.</p></footer>
<script>{SHARED_JS}
function filterJobs(){{const q=document.getElementById('q').value.toLowerCase();const e=document.getElementById('emp').value;let n=0;document.querySelectorAll('.card').forEach(c=>{{const ok=(!e||c.dataset.employer===e)&&c.textContent.toLowerCase().includes(q);c.style.display=ok?'':'none';if(ok)n++;}});document.getElementById('none').style.display=n?'none':'';}}
function refreshCount(){{const t=load();document.getElementById('appliedCount').textContent=Object.values(t).filter(v=>v.status==='Applied'||v.status==='Interview'||v.status==='Offer').length;}}
updateBadges(); refreshCount();
</script></body></html>"""

rows = []
for j in jobs:
    rows.append(f"""<tr data-jobid="{esc(j['id'])}"><td><strong>{esc(j['title'])}</strong><br><span class="meta">{esc(j['employer'])} · {esc(j['location'])}</span></td><td>{esc(salary_display(j.get('salary')))}</td><td>{j['fit_score']}/100</td><td><select class="tracksel" onchange="setStatus('{esc(j['id'])}',this.value)"><option>Not applied</option><option>Saved</option><option>Applied</option><option>Interview</option><option>Offer</option><option>Rejected</option></select></td><td><input type="date" onchange="setField('{esc(j['id'])}','date',this.value)"></td><td><input type="text" placeholder="Notes, recruiter, link…" style="width:100%" onchange="setField('{esc(j['id'])}','notes',this.value)"></td><td><a href="{esc(j['url'])}" target="_blank" rel="noopener">Posting →</a></td></tr>""")

tracker_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Track H-1B cybersecurity job applications — status, date and notes, saved in your browser only.">
<title>Application Tracker — H-1B Cybersecurity Jobs</title><style>{CSS}</style></head><body>
<header><div class="wrap"><p class="eyebrow">H-1B Cybersecurity Jobs · Karan Darji</p><h1>My Application Tracker</h1>
<p class="sub">Mark a job Applied, Interview, Offer or Rejected. It saves in <strong>your browser only</strong> — nothing is sent to GitHub, and it will not show on another device unless you export the CSV.</p>
<nav><a href="index.html">← Back to all jobs</a><a class="ghost" href="https://github.com/karandarjishack/h1b-cyber-jobs">GitHub repo</a></nav></div></header>
<div class="wrap">
<div class="stats" id="stats"><div class="stat"><b id="cApplied">0</b><span>Applied</span></div><div class="stat"><b id="cInterview">0</b><span>Interview</span></div><div class="stat"><b id="cOffer">0</b><span>Offer</span></div><div class="stat"><b id="cRejected">0</b><span>Rejected</span></div><div class="stat"><b id="cSaved">0</b><span>Saved</span></div><div class="stat"><b id="cTodo">{len(jobs)}</b><span>Not applied yet</span></div></div>
<p><button class="trackbtn" onclick="exportCSV()">Export tracker as CSV</button>
<button class="trackbtn" style="background:#374151;color:#fff" onclick="if(confirm('Clear all tracker entries in this browser?')){{localStorage.removeItem(KEY);location.reload();}}">Clear tracker</button>
<select id="fstatus" onchange="renderTracker()" aria-label="Filter by status"><option value="">Show: all statuses</option><option>Not applied</option><option>Saved</option><option>Applied</option><option>Interview</option><option>Offer</option><option>Rejected</option></select></p>
<div class="tablewrap"><table><thead><tr><th>Job</th><th>Salary</th><th>Fit</th><th>Status</th><th>Date applied</th><th>Notes</th><th>Posting</th></tr></thead><tbody id="trackbody">{''.join(rows)}</tbody></table></div>
<p class="meta">Tip: on the jobs page, click “I have applied” on a card — it will show up here as Applied, with today's date.</p>
</div>
<footer><p>Tracker data is stored in this browser (localStorage). Export the CSV to keep a copy.</p></footer>
<script>{SHARED_JS}
function renderTracker(){{const t=load();const f=document.getElementById('fstatus').value;let c={{Applied:0,Interview:0,Offer:0,Rejected:0,Saved:0,'Not applied':0}};document.querySelectorAll('#trackbody tr').forEach(tr=>{{const id=tr.dataset.jobid;const v=t[id]||{{}};const s=v.status||'Not applied';c[s]=(c[s]||0)+1;tr.querySelector('select').value=s;tr.querySelector('input[type=date]').value=v.date||'';tr.querySelector('input[type=text]').value=v.notes||'';tr.style.display=(!f||s===f)?'':'none';tr.className='status-'+s;}});document.getElementById('cApplied').textContent=c.Applied;document.getElementById('cInterview').textContent=c.Interview;document.getElementById('cOffer').textContent=c.Offer;document.getElementById('cRejected').textContent=c.Rejected;document.getElementById('cSaved').textContent=c.Saved;document.getElementById('cTodo').textContent=c['Not applied'];}}
renderTracker();
</script></body></html>"""

(ROOT / "docs" / "index.html").write_text(index_html)
(ROOT / "docs" / "tracker.html").write_text(tracker_html)
print(f"Wrote docs/index.html ({len(index_html)} bytes) + docs/tracker.html ({len(tracker_html)} bytes), {len(jobs)} jobs")
