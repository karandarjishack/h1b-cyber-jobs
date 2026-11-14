#!/usr/bin/env python3
"""Generate docs/index.html for GitHub Pages from jobs.json (verified Nov 13, 2026)."""
import json, html
from pathlib import Path
ROOT = Path(__file__).parent
jobs = json.loads((ROOT / "jobs.json").read_text())

def esc(s): return html.escape(str(s or "—"))

cards = []
for j in jobs:
    kws = "".join(f'<span class="kw">{esc(k)}</span>' for k in j.get("keywords_matched", []))
    ev = j.get("sponsorship_evidence", "")
    ev_label = {"A_verified_posting": "A — Posting states sponsorship",
                "B_sponsor_history": "B — H-1B sponsor history (DOL FY2025)",
                "C_ask_recruiter": "C — Ask recruiter to confirm"}.get(ev, ev)
    cards.append(f"""
    <article class="card" data-employer="{esc(j['employer'])}" data-title="{esc(j['title'].lower())}">
      <div class="top"><span class="score">{j['fit_score']}/100 fit</span><span class="emp">{esc(j['employer'])}</span></div>
      <h2>{esc(j['title'])}</h2>
      <p class="meta">{esc(j['location'])} · {esc(j.get('salary',''))}</p>
      <p class="meta">Posted {esc(j.get('posted',''))} · Closes {esc(j.get('closes') or '—')} · PERM: {esc(j.get('perm_status',''))}</p>
      <div class="bar"><div style="width:{j['fit_score']}%"></div></div>
      <p><strong>Sponsorship:</strong> {esc(ev_label)} — {esc(j.get('sponsorship_note',''))}</p>
      <p><strong>Why it fits:</strong> {esc(j.get('why_fit',''))}</p>
      <div class="kws">{kws}</div>
      <p><a class="apply" href="{esc(j['url'])}" target="_blank" rel="noopener">Apply / view posting →</a></p>
    </article>""")

html_doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>H-1B Cybersecurity Jobs — curated for Karan Darji</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:0;background:#0b0f14;color:#e8eef4}}
header{{background:#111827;padding:28px 20px;border-bottom:3px solid #e11d48}}
header h1{{margin:0;font-size:28px}} header p{{color:#9fb0c3;max-width:900px}}
.wrap{{max-width:980px;margin:0 auto;padding:20px}}
.stats{{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}}
.stat{{background:#1f2937;border:1px solid #374151;border-radius:10px;padding:12px 16px}}
.stat b{{font-size:22px;display:block}}
input,select{{padding:10px;border-radius:8px;border:1px solid #374151;background:#111827;color:#e8eef4;width:100%;box-sizing:border-box}}
.filters{{display:grid;grid-template-columns:2fr 1fr;gap:10px;margin:16px 0}}
.card{{background:#111827;border:1px solid #374151;border-radius:12px;padding:18px;margin:14px 0}}
.card h2{{margin:8px 0;font-size:20px}} .top{{display:flex;justify-content:space-between;gap:10px}}
.score{{background:#e11d48;color:#fff;padding:4px 10px;border-radius:999px;font-weight:700;font-size:13px}}
.emp{{color:#9fb0c3;font-weight:700}} .meta{{color:#9fb0c3;margin:4px 0}}
.bar{{height:8px;background:#374151;border-radius:999px;overflow:hidden;margin:10px 0}}
.bar div{{height:100%;background:#22c55e}}
.kw{{display:inline-block;background:#1e3a5f;border:1px solid #2f5b8f;border-radius:999px;padding:3px 9px;margin:2px;font-size:12px}}
.apply{{display:inline-block;margin-top:10px;background:#e11d48;color:#fff;padding:10px 14px;border-radius:8px;text-decoration:none;font-weight:700}}
.note{{background:#1f2937;border:1px solid #f59e0b;border-radius:10px;padding:14px;margin:18px 0}}
a{{color:#7dd3fc}} footer{{color:#9fb0c3;padding:20px;text-align:center}}
</style></head><body>
<header><div class="wrap"><h1>H-1B Cybersecurity Jobs</h1>
<p>Curated for Karan Darji — cyber security only, scored against his resume (CrowdStrike Falcon, Microsoft Defender, Splunk, Sentinel, Qualys, Intune, Entra ID, Zero Trust, Detection Engineering, SIEM, VAPT, AI security governance), H-1B sponsors only. Last verified Nov 13, 2026.</p></div></header>
<div class="wrap">
<div class="stats">
<div class="stat"><b>9</b>jobs kept</div>
<div class="stat"><b>76/100</b>top fit</div>
<div class="stat"><b>Nov 13, 2026</b>last verified</div>
<div class="stat"><b>$100k–$265k</b>salary range in list</div>
</div>
<div class="note"><strong>PERM warning — Oct 8, 2026:</strong> Microsoft, Adobe, Cognizant, Infosys, Tata, Wipro, HCL, Capgemini are suspended from PERM (green-card) sponsorship, no end date. H-1B is a different filing — they can still file H-1B — but the green-card path is blocked there for now.</div>
<div class="note"><strong>Trends:</strong> H-1B FY2026: 343,981 registrations, down 55% from FY2024, 35% selected. FY2027 is wage-weighted + a $100,000 fee — higher-wage senior roles get more weight. PERM FY2025: 117,849 received, down 22%. Security H-1B Jul–Sep 2025: 1,093 filings, median $141,378; Security Engineer median $148,150.</div>
<div class="filters">
<input id="q" placeholder="Search title, employer, keyword…" oninput="filterJobs()">
<select id="emp" onchange="filterJobs()"><option value="">All employers</option><option>Amazon</option><option>CrowdStrike</option><option>Deloitte</option><option>General Motors</option></select>
</div>
<div id="jobs">{''.join(cards)}</div>
<p id="none" style="display:none">No jobs match that search.</p>
<h2>Excluded on purpose</h2>
<p>Roles saying US Citizen only, will not sponsor, no sponsorship, TS/SCI, or GovCloud were dropped — e.g. CrowdStrike GovCloud Associate Security Engineer, Amazon ADC AI Security Engineer (TS/SCI + US Citizen), Palo Alto Cloud Security Systems Engineer (“Is role eligible for Immigration Sponsorship? No”). Full list in the repo’s excluded.md.</p>
<p>Sponsorship evidence: <strong>A</strong> = posting states sponsorship · <strong>B</strong> = employer filed certified H-1B LCAs for security/cyber titles in FY2025 — confirm for this specific role · <strong>C</strong> = large sponsor employer, posting silent — ask recruiter before applying.</p>
</div>
<footer>Source data: jobs.json / jobs.md in github.com/karandarjishack/h1b-cyber-jobs · Generated Nov 13, 2026</footer>
<script>
function filterJobs(){{
  const q=document.getElementById('q').value.toLowerCase();
  const e=document.getElementById('emp').value;
  let n=0;
  document.querySelectorAll('.card').forEach(c=>{{
    const ok=(!e||c.dataset.employer===e)&&c.textContent.toLowerCase().includes(q);
    c.style.display=ok?'':'none'; if(ok)n++;
  }});
  document.getElementById('none').style.display=n?'none':'';
}}
</script>
</body></html>
"""
(ROOT / "docs" / "index.html").write_text(html_doc)
print(f"Wrote docs/index.html ({len(html_doc)} bytes, {len(jobs)} jobs)")
