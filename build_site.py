#!/usr/bin/env python3
"""Generate docs/index.html + docs/tracker.html for GitHub Pages from jobs.json.
Tracker state lives in the visitor's browser (localStorage, key h1b_tracker_v1)
— it is private to that browser, not sent to GitHub. Shared between both pages.
"""
import json, html
from pathlib import Path
ROOT = Path(__file__).parent
jobs = json.loads((ROOT / "jobs.json").read_text())

def esc(s): return html.escape(str(s or "—"))

CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:0;background:#0b0f14;color:#e8eef4}
header{background:#111827;padding:28px 20px;border-bottom:3px solid #e11d48}
header h1{margin:0;font-size:28px} header p{color:#9fb0c3;max-width:900px}
nav a{color:#fff;background:#e11d48;padding:10px 14px;border-radius:8px;text-decoration:none;font-weight:700;display:inline-block;margin:6px 6px 0 0}
nav a.ghost{background:#1f2937;border:1px solid #374151}
.wrap{max-width:980px;margin:0 auto;padding:20px}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}
.stat{background:#1f2937;border:1px solid #374151;border-radius:10px;padding:12px 16px}
.stat b{font-size:22px;display:block}
input,select,textarea{padding:10px;border-radius:8px;border:1px solid #374151;background:#111827;color:#e8eef4;box-sizing:border-box}
.filters{display:grid;grid-template-columns:2fr 1fr;gap:10px;margin:16px 0}
.card{background:#111827;border:1px solid #374151;border-radius:12px;padding:18px;margin:14px 0}
.card h2{margin:8px 0;font-size:20px} .top{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
.score{background:#e11d48;color:#fff;padding:4px 10px;border-radius:999px;font-weight:700;font-size:13px}
.emp{color:#9fb0c3;font-weight:700} .meta{color:#9fb0c3;margin:4px 0}
.bar{height:8px;background:#374151;border-radius:999px;overflow:hidden;margin:10px 0}
.bar div{height:100%;background:#22c55e}
.kw{display:inline-block;background:#1e3a5f;border:1px solid #2f5b8f;border-radius:999px;padding:3px 9px;margin:2px;font-size:12px}
.apply{display:inline-block;margin-top:10px;background:#e11d48;color:#fff;padding:10px 14px;border-radius:8px;text-decoration:none;font-weight:700}
.trackbtn{display:inline-block;margin:10px 8px 0 0;background:#22c55e;color:#052e12;padding:10px 14px;border-radius:8px;font-weight:700;border:0;cursor:pointer}
.note{background:#1f2937;border:1px solid #f59e0b;border-radius:10px;padding:14px;margin:18px 0}
a{color:#7dd3fc} footer{color:#9fb0c3;padding:20px;text-align:center}
table{width:100%;border-collapse:collapse} th,td{border:1px solid #374151;padding:8px;text-align:left;vertical-align:top} th{background:#1f2937}
.status-applied{background:#14532d} .status-interview{background:#1e3a5f} .status-offer{background:#854d0e} .status-rejected{background:#7f1d1d}
"""

SHARED_JS = """
const KEY='h1b_tracker_v1';
function load(){try{return JSON.parse(localStorage.getItem(KEY))||{}}catch(e){return{}}}
function save(t){localStorage.setItem(KEY,JSON.stringify(t))}
function setStatus(id,status){const t=load();t[id]=t[id]||{};t[id].status=status;if(status==='Applied'&&!t[id].date)t[id].date=new Date().toISOString().slice(0,10);if(status==='Not applied'){t[id].date='';}save(t);if(document.getElementById('stats'))renderTracker();updateBadges();}
function setField(id,field,val){const t=load();t[id]=t[id]||{};t[id][field]=val;save(t);}
function updateBadges(){const t=load();document.querySelectorAll('[data-jobid]').forEach(el=>{const s=(t[el.dataset.jobid]||{}).status||'Not applied';const b=el.querySelector('.badge');if(b)b.textContent='Status: '+s;const sel=el.querySelector('select.tracksel');if(sel)sel.value=s;});}
function exportCSV(){const t=load();let rows=[['Job','Employer','Location','Salary','Status','Date applied','Notes']];document.querySelectorAll('#trackbody tr').forEach(tr=>{const c=tr.querySelectorAll('td');if(c.length>=7)rows.push([...c].slice(0,7).map(x=>'"'+(x.querySelector('input,select,textarea')?.value||x.textContent).replace(/"/g,'""')+'"'));});const blob=new Blob([rows.map(r=>r.join(',')).join('\\n')],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='h1b-job-tracker.csv';a.click();}
"""

cards = []
for j in jobs:
    kws = "".join(f'<span class="kw">{esc(k)}</span>' for k in j.get("keywords_matched", []))
    ev = j.get("sponsorship_evidence", "")
    ev_label = {"A_verified_posting": "A — Posting states sponsorship",
                "B_sponsor_history": "B — H-1B sponsor history (DOL FY2025)",
                "C_ask_recruiter": "C — Ask recruiter to confirm"}.get(ev, ev)
    cards.append(f"""
    <article class="card" data-jobid="{esc(j['id'])}" data-employer="{esc(j['employer'])}">
      <div class="top"><span class="score">{j['fit_score']}/100 fit</span><span class="emp">{esc(j['employer'])}</span><span class="badge">Status: Not applied</span></div>
      <h2>{esc(j['title'])}</h2>
      <p class="meta">{esc(j['location'])} · {esc(j.get('salary',''))}</p>
      <p class="meta">Posted {esc(j.get('posted',''))} · Closes {esc(j.get('closes') or '—')} · PERM: {esc(j.get('perm_status',''))}</p>
      <div class="bar"><div style="width:{j['fit_score']}%"></div></div>
      <p><strong>Sponsorship:</strong> {esc(ev_label)} — {esc(j.get('sponsorship_note',''))}</p>
      <p><strong>Why it fits:</strong> {esc(j.get('why_fit',''))}</p>
      <div class="kws">{kws}</div>
      <p><a class="apply" href="{esc(j['url'])}" target="_blank" rel="noopener">Apply / view posting →</a>
      <button class="trackbtn" onclick="setStatus('{esc(j['id'])}','Applied');this.textContent='✓ Marked Applied'">✓ I have applied</button>
      <select class="tracksel" onchange="setStatus('{esc(j['id'])}',this.value)"><option>Not applied</option><option>Saved</option><option>Applied</option><option>Interview</option><option>Offer</option><option>Rejected</option></select></p>
    </article>""")

index_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>H-1B Cybersecurity Jobs — curated for Karan Darji</title><style>{CSS}</style></head><body>
<header><div class="wrap"><h1>H-1B Cybersecurity Jobs</h1>
<p>Curated for Karan Darji — cyber security only, scored against his resume, H-1B sponsors only. Last verified Nov 13, 2026.</p>
<nav><a href="tracker.html">📋 My Application Tracker →</a><a class="ghost" href="https://github.com/karandarjishack/h1b-cyber-jobs">GitHub repo</a></nav></div></header>
<div class="wrap">
<div class="stats"><div class="stat"><b>9</b>jobs kept</div><div class="stat"><b>76/100</b>top fit</div><div class="stat"><b>Nov 13, 2026</b>last verified</div><div class="stat"><b id="appliedCount">0</b>applied (this browser)</div></div>
<div class="note"><strong>PERM warning — Oct 8, 2026:</strong> Microsoft, Adobe, Cognizant, Infosys, Tata, Wipro, HCL, Capgemini are suspended from PERM (green-card) sponsorship, no end date. H-1B is a different filing — they can still file H-1B — but the green-card path is blocked there for now.</div>
<div class="note"><strong>Trends:</strong> H-1B FY2026: 343,981 registrations, down 55% from FY2024, 35% selected. FY2027 is wage-weighted + a $100,000 fee — higher-wage senior roles get more weight. PERM FY2025: 117,849 received, down 22%. Security H-1B Jul–Sep 2025: 1,093 filings, median $141,378; Security Engineer median $148,150.</div>
<div class="filters"><input id="q" placeholder="Search title, employer, keyword…" oninput="filterJobs()"><select id="emp" onchange="filterJobs()"><option value="">All employers</option><option>Amazon</option><option>CrowdStrike</option><option>Deloitte</option><option>General Motors</option></select></div>
<div id="jobs">{''.join(cards)}</div>
<p id="none" style="display:none">No jobs match that search.</p>
<h2>Excluded on purpose</h2>
<p>Roles saying US Citizen only, will not sponsor, no sponsorship, TS/SCI, or GovCloud were dropped. Full list in the repo’s excluded.md.</p>
</div>
<footer>Source: jobs.json / jobs.md in github.com/karandarjishack/h1b-cyber-jobs · Tracker saves in your browser only.</footer>
<script>{SHARED_JS}
function filterJobs(){{const q=document.getElementById('q').value.toLowerCase();const e=document.getElementById('emp').value;let n=0;document.querySelectorAll('.card').forEach(c=>{{const ok=(!e||c.dataset.employer===e)&&c.textContent.toLowerCase().includes(q);c.style.display=ok?'':'none';if(ok)n++;}});document.getElementById('none').style.display=n?'none':'';}}
function refreshCount(){{const t=load();document.getElementById('appliedCount').textContent=Object.values(t).filter(v=>v.status==='Applied'||v.status==='Interview'||v.status==='Offer').length;}}
const _origSave=save; save=function(t){{_origSave(t);refreshCount();}}; updateBadges(); refreshCount();
</script></body></html>"""

rows = []
for j in jobs:
    rows.append(f"""<tr data-jobid="{esc(j['id'])}"><td><strong>{esc(j['title'])}</strong><br>{esc(j['employer'])} · {esc(j['location'])}</td><td>{esc(j.get('salary',''))}</td><td>{j['fit_score']}/100</td><td><select onchange="setStatus('{esc(j['id'])}',this.value)"><option>Not applied</option><option>Saved</option><option>Applied</option><option>Interview</option><option>Offer</option><option>Rejected</option></select></td><td><input type="date" onchange="setField('{esc(j['id'])}','date',this.value)"></td><td><input type="text" placeholder="Notes, recruiter, link…" style="width:100%" onchange="setField('{esc(j['id'])}','notes',this.value)"></td><td><a href="{esc(j['url'])}" target="_blank" rel="noopener">Posting →</a></td></tr>""")

tracker_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Application Tracker — H-1B Cybersecurity Jobs</title><style>{CSS}</style></head><body>
<header><div class="wrap"><h1>📋 My Application Tracker</h1>
<p>Tick a job as Applied, Interview, Offer or Rejected. It saves in <strong>your browser only</strong> — nothing is sent to GitHub, and it will not show on another device unless you export the CSV.</p>
<nav><a href="index.html">← Back to all jobs</a><a class="ghost" href="https://github.com/karandarjishack/h1b-cyber-jobs">GitHub repo</a></nav></div></header>
<div class="wrap">
<div class="stats" id="stats"><div class="stat"><b id="cApplied">0</b>Applied</div><div class="stat"><b id="cInterview">0</b>Interview</div><div class="stat"><b id="cOffer">0</b>Offer</div><div class="stat"><b id="cRejected">0</b>Rejected</div><div class="stat"><b id="cSaved">0</b>Saved</div><div class="stat"><b id="cTodo">9</b>Not applied yet</div></div>
<p><button class="trackbtn" onclick="exportCSV()">⬇ Export tracker as CSV</button>
<button class="trackbtn" style="background:#374151;color:#fff" onclick="if(confirm('Clear all tracker entries in this browser?')){{localStorage.removeItem(KEY);location.reload();}}">Clear tracker</button>
<select id="fstatus" onchange="renderTracker()"><option value="">Show: all statuses</option><option>Not applied</option><option>Saved</option><option>Applied</option><option>Interview</option><option>Offer</option><option>Rejected</option></select></p>
<table><thead><tr><th>Job</th><th>Salary</th><th>Fit</th><th>Status</th><th>Date applied</th><th>Notes</th><th>Posting</th></tr></thead><tbody id="trackbody">{''.join(rows)}</tbody></table>
<p>Tip: on the jobs page, click <strong>“✓ I have applied”</strong> on a card — it will show up here as Applied, with today’s date.</p>
</div>
<footer>Tracker data is stored in this browser (localStorage). Export CSV to keep a copy.</footer>
<script>{SHARED_JS}
function renderTracker(){{const t=load();const f=document.getElementById('fstatus').value;let c={{Applied:0,Interview:0,Offer:0,Rejected:0,Saved:0,'Not applied':0}};document.querySelectorAll('#trackbody tr').forEach(tr=>{{const id=tr.dataset.jobid;const v=t[id]||{{}};const s=v.status||'Not applied';c[s]=(c[s]||0)+1;tr.querySelector('select').value=s;tr.querySelector('input[type=date]').value=v.date||'';tr.querySelector('input[type=text]').value=v.notes||'';tr.style.display=(!f||s===f)?'':'none';}});document.getElementById('cApplied').textContent=c.Applied;document.getElementById('cInterview').textContent=c.Interview;document.getElementById('cOffer').textContent=c.Offer;document.getElementById('cRejected').textContent=c.Rejected;document.getElementById('cSaved').textContent=c.Saved;document.getElementById('cTodo').textContent=c['Not applied'];}}
renderTracker();
</script></body></html>"""

(ROOT / "docs" / "index.html").write_text(index_html)
(ROOT / "docs" / "tracker.html").write_text(tracker_html)
print(f"Wrote docs/index.html ({len(index_html)} bytes) + docs/tracker.html ({len(tracker_html)} bytes), {len(jobs)} jobs")
