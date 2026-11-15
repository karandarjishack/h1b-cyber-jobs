#!/usr/bin/env python3
"""Generate docs/index.html + docs/tracker.html for GitHub Pages from jobs.json.

Design (Nov 15, 2026 — KD: the dark/red theme was "the worst website I
can ever see"): Apple.com style — white cards on a light-gray page,
near-black text, blue links and buttons, generous spacing, smooth
fade-up and hover animations. No emojis in headings.

Years rule (KD, Nov 15, 2026): the site lists ONLY jobs asking 2-5 years
of experience. Postings asking 2-5 years or 2+ years include 3-5 in
their band, and KD's 4+ years sits inside them. 6+ year jobs are
archived; unstated-years jobs are held. Enforced in find_jobs.py.

Tracker (KD, Nov 15, 2026): the tracker shows ONLY jobs KD has applied
to — nothing he has not applied to. When he clicks "I have applied" on
a card, the job (with its details snapshotted) goes to the tracker, and
each applied job carries a draft message to send to the recruiter /
hiring manager, with a Copy button and a LinkedIn recruiter search link.
Tracker state lives in the visitor's browser (localStorage, key
h1b_tracker_v1) — private to that browser, not sent to GitHub. JRM is
seeded as Applied (KD applied Nov 15, 2026, outside the site).

Every Apply button goes to the employer's own careers site or ATS —
no aggregators. Dates render as "Nov 13, 2026", never raw ISO.
"""
import json, html
from datetime import date
from pathlib import Path
ROOT = Path(__file__).parent
jobs = json.loads((ROOT / "jobs.json").read_text())
# Held count for the header: live holds only — CLOSED records are not
# roles waiting on a direct link.
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
:root{--bg:#f5f5f7;--card:#ffffff;--text:#1d1d1f;--muted:#6e6e73;--line:#d2d2d7;--blue:#0066cc;--btn:#0071e3;--btn-hover:#0077ed;--softblue:#e8f1fc;--green:#1e8e3e;--amber:#9a6a00;--red:#d70015}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','SF Pro Text','Helvetica Neue','Segoe UI',Arial,sans-serif;margin:0;background:var(--bg);color:var(--text);font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:var(--blue);text-decoration:none}
a:hover{text-decoration:underline}
.topnav{position:sticky;top:0;z-index:50;background:rgba(251,251,253,.85);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom:1px solid var(--line)}
.topnav .wrap{display:flex;align-items:center;gap:22px;padding:11px 20px}
.topnav .brand{font-weight:700;font-size:15px;color:var(--text);text-decoration:none;letter-spacing:-.01em}
.topnav .spacer{flex:1}
.topnav a.navlink{color:var(--text);font-size:13px;text-decoration:none;opacity:.8;transition:opacity .2s ease}
.topnav a.navlink:hover{opacity:1;text-decoration:none}
header{background:#fff;border-bottom:1px solid var(--line);padding:48px 20px 36px}
.eyebrow{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 10px;font-weight:600}
header h1{margin:0;font-size:32px;line-height:1.1;letter-spacing:-.02em;font-weight:700}
header p.sub{color:var(--muted);max-width:720px;margin:14px 0 0;font-size:17px;line-height:1.5}
.wrap{max-width:980px;margin:0 auto;padding:0 20px}
.updated{color:var(--muted);font-size:13px;margin:16px 0 0}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0 6px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:16px 20px;min-width:120px;transition:transform .25s ease,box-shadow .25s ease}
.stat:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.06)}
.stat b{font-size:28px;display:block;line-height:1.1;letter-spacing:-.02em}
.stat span{color:var(--muted);font-size:12px}
.note{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 24px;margin:20px 0}
.note h2{margin:0 0 10px;font-size:17px;letter-spacing:-.01em}
.note ol{margin:6px 0 0;padding-left:20px}
.note p{margin:10px 0 0;color:var(--muted)}
.note p strong{color:var(--text)}
.snapshot{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0 4px}
.snap{background:var(--bg);border-radius:14px;padding:12px 14px}
.snap b{font-size:18px;display:block;letter-spacing:-.01em}
.snap span{color:var(--muted);font-size:12px}
input,select,textarea{padding:10px 12px;border-radius:12px;border:1px solid var(--line);background:#fff;color:var(--text);box-sizing:border-box;font:inherit;transition:border-color .2s ease,box-shadow .2s ease}
input:focus,select:focus,textarea:focus{outline:none;border-color:var(--btn);box-shadow:0 0 0 3px rgba(0,113,227,.15)}
.filters{display:grid;grid-template-columns:2fr 1fr;gap:10px;margin:22px 0 4px}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:24px;margin:18px 0;animation:fadeUp .5s ease both;transition:transform .3s ease,box-shadow .3s ease}
.card:hover{transform:translateY(-2px);box-shadow:0 12px 32px rgba(0,0,0,.08)}
.card .topline{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap}
.employer{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:700}
.pills{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.pill{display:inline-block;padding:5px 12px;border-radius:999px;font-weight:600;font-size:12px;white-space:nowrap}
.pill.fit{background:var(--text);color:#fff}
.pill.core{background:var(--softblue);color:var(--blue)}
.pill.stretch{background:var(--bg);color:var(--muted)}
.pill.status{background:var(--bg);color:var(--muted)}
.card h2{margin:12px 0 4px;font-size:20px;line-height:1.25;letter-spacing:-.015em}
.card h3{margin:16px 0 6px;font-size:15px}
.meta{color:var(--muted);margin:2px 0}
.meta .sep{margin:0 6px;color:#a1a1a6}
.bar{height:8px;background:#e8e8ed;border-radius:999px;overflow:hidden;margin:16px 0 6px}
.bar div{height:100%;background:var(--btn);border-radius:999px;transition:width .6s ease}
.bar.stretchbar div{background:#86868b}
.barlabel{font-size:12px;color:var(--muted);display:flex;justify-content:space-between}
.kv{display:grid;grid-template-columns:110px 1fr;gap:4px 12px;margin:14px 0 0}
.kv dt{font-weight:600;font-size:13px;color:var(--muted);padding-top:2px}
.kv dd{margin:0}
.kw{display:inline-block;background:var(--bg);border:1px solid var(--line);border-radius:999px;padding:3px 10px;margin:2px 2px 2px 0;font-size:12px}
.sector{display:inline-block;background:var(--bg);border:1px solid var(--line);border-radius:999px;padding:3px 10px;font-size:12px;color:var(--muted)}
.actions{margin-top:18px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.apply{display:inline-block;background:var(--btn);color:#fff;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;transition:background .2s ease,transform .2s ease}
.apply:hover{background:var(--btn-hover);text-decoration:none;transform:translateY(-1px)}
.trackbtn{display:inline-block;background:#fff;color:var(--btn);padding:10px 18px;border-radius:999px;font-weight:600;border:1px solid var(--line);cursor:pointer;font:inherit;transition:all .2s ease}
.trackbtn:hover{border-color:var(--btn)}
.trackbtn.applied{background:var(--softblue);border-color:transparent}
.copybtn{display:inline-block;background:var(--btn);color:#fff;padding:9px 18px;border-radius:999px;font-weight:600;border:0;cursor:pointer;font:inherit;transition:background .2s ease}
.copybtn:hover{background:var(--btn-hover)}
.official{font-size:12px;color:var(--muted)}
.row{margin-top:14px}
.row .lbl{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.row .val{font-size:15px;line-height:1.55}
.row .val .yes{color:var(--green);font-weight:700}
.row .val .ask{color:var(--amber);font-weight:700}
.yes{color:var(--green);font-weight:700}
.ask{color:var(--amber);font-weight:700}
.urllink{word-break:break-all;font-size:14px;line-height:1.5}
.removebtn{display:inline-block;background:none;border:0;color:var(--red);font-size:13px;font-weight:600;cursor:pointer;padding:9px 4px;font:inherit}
.removebtn:hover{text-decoration:underline}
.draft{background:var(--bg);border-radius:14px;padding:16px 18px;margin-top:18px}
.draft h3{margin:0 0 4px;font-size:15px}
.draft-subject{font-size:13px;color:var(--muted);margin:4px 0}
.draft-body{white-space:pre-wrap;font-family:inherit;font-size:14px;line-height:1.65;margin:10px 0}
.card.empty{text-align:center;padding:36px 24px}
.card.empty h2{margin-top:0}
footer{color:var(--muted);padding:28px 20px 36px;text-align:center;font-size:13px}
footer p{margin:4px 0}
h2.section{font-size:19px;margin:30px 0 6px;letter-spacing:-.01em}
@media (max-width:640px){.kv{grid-template-columns:1fr}.kv dt{padding-top:8px}header h1{font-size:32px}.filters{grid-template-columns:1fr}.card{padding:20px 18px}}
"""

SHARED_JS = """
const KEY='h1b_tracker_v1';
const APPLIED_STATUSES=['Applied','Interview','Offer','Rejected'];
function load(){try{return JSON.parse(localStorage.getItem(KEY))||{}}catch(e){return{}}}
function save(t){localStorage.setItem(KEY,JSON.stringify(t))}
function seedApplications(){if(typeof SEEDED_APPLICATIONS==='undefined')return;const t=load();let changed=false;SEEDED_APPLICATIONS.forEach(s=>{if(!t[s.id]){t[s.id]={status:s.status,date:s.date,notes:s.notes||'',snap:{title:s.title,employer:s.employer,location:s.location,salary:s.salary,fit:String(s.fit),url:s.url,keywords:s.keywords||[],why:s.why||'',ev:s.ev||'',evnote:s.evnote||''}};changed=true;}});if(changed)save(t);}
function snapshotFromCard(id){const card=document.querySelector('[data-jobid="'+id+'"]');if(!card)return null;const d=card.dataset;return {title:d.title||'',employer:d.employer||'',location:d.location||'',salary:d.salary||'',fit:d.fit||'',url:d.url||'',keywords:(d.keywords||'').split('|').filter(Boolean),why:d.why||'',ev:d.ev||'',evnote:d.evnote||''};}
function setStatus(id,status){const t=load();t[id]=t[id]||{};if((status==='Applied'||status==='Interview'||status==='Offer'||status==='Rejected')&&!t[id].snap){const s=snapshotFromCard(id);if(s)t[id].snap=s;}t[id].status=status;if(status==='Applied'&&!t[id].date)t[id].date=new Date().toISOString().slice(0,10);if(status==='Not applied'){t[id].date='';}save(t);if(document.getElementById('tracklist'))renderTracker();updateBadges();refreshCount();if(typeof filterJobs==='function')filterJobs();}
function markApplied(id){setStatus(id,'Applied');}
function filterJobs(){const qEl=document.getElementById('q');if(!qEl)return;const q=qEl.value.toLowerCase();const e=document.getElementById('emp').value;const t=load();let n=0;let anyLeft=0;document.querySelectorAll('.card[data-jobid]').forEach(c=>{const s=(t[c.dataset.jobid]||{}).status||'Not applied';const applied=APPLIED_STATUSES.indexOf(s)>=0;if(!applied)anyLeft++;const ok=!applied&&(!e||c.dataset.employer===e)&&c.textContent.toLowerCase().includes(q);c.style.display=ok?'':'none';if(ok)n++;});const none=document.getElementById('none');if(n===0){none.style.display='';none.textContent=anyLeft===0?'All jobs are on your tracker.':'No jobs match that search.';}else{none.style.display='none';}}
function setField(id,field,val){const t=load();t[id]=t[id]||{};t[id][field]=val;save(t);}
function updateBadges(){const t=load();document.querySelectorAll('[data-jobid]').forEach(el=>{const s=(t[el.dataset.jobid]||{}).status||'Not applied';const b=el.querySelector('.statuspill');if(b)b.textContent=s;const sel=el.querySelector('select.tracksel');if(sel)sel.value=s;const btn=el.querySelector('.trackbtn');if(btn){if(s==='Applied'){btn.textContent='Applied';btn.classList.add('applied');}else{btn.textContent='I have applied';btn.classList.remove('applied');}}});}
function refreshCount(){const el=document.getElementById('appliedCount');if(!el)return;const t=load();el.textContent=Object.values(t).filter(v=>v.status==='Applied'||v.status==='Interview'||v.status==='Offer').length;}
"""

TRACKER_JS = """
function draftFor(j){const kws=j.keywords||[];const kw=kws.slice(0,4).join(', ');const has=function(){for(var i=0;i<arguments.length;i++){if(kws.indexOf(arguments[i])>=0)return true;}return false;};let focus;if(has('VAPT','Penetration Testing','Burp Suite'))focus=`I'm a cybersecurity engineer with 4+ years in VAPT and detection engineering — I've reported vulnerabilities to Google and US government programs, and I run security testing alongside SOC operations.`;else if(has('Splunk','Microsoft Sentinel','SIEM','SOAR'))focus=`I'm a cybersecurity engineer with 4+ years in detection engineering and SOC operations — I built a centralized Splunk SIEM ingesting Defender, CrowdStrike Falcon, Intune, Qualys and Lightspeed telemetry, cutting incident triage time by 40%.`;else if(has('CrowdStrike Falcon','Microsoft Defender','EDR','XDR'))focus=`I'm a cybersecurity engineer with 4+ years in endpoint detection and response — I run CrowdStrike Falcon and Microsoft Defender across 80,000 endpoints at Detroit Public Schools, with Entra ID Conditional Access and Zero Trust controls.`;else if(has('Zero Trust','Microsoft Entra ID','Microsoft Intune'))focus=`I'm a cybersecurity engineer with 4+ years in Zero Trust architecture and identity security — I lifted Microsoft Secure Score 13% with Conditional Access, attack-surface reduction and device compliance across 80,000 users and endpoints.`;else focus=`I'm a cybersecurity engineer with 4+ years in detection engineering, Zero Trust, and modern SOC operations — currently Cybersecurity Architect at ProNoesis for Detroit Public Schools (80,000 endpoints), working with CrowdStrike Falcon, Microsoft Defender, Splunk, Sentinel, Qualys, and Entra ID.`;const subject='Application — '+j.title+', '+j.employer+' (Karan Darji)';const whyPart=j.why?`


Why I am a fit for this role: ${j.why}`:'';const kwPart=kw?`


My background lines up on: ${kw}.`:'';let body=`Hi [Name],

I recently applied for the ${j.title} role at ${j.employer} (${j.location}) and wanted to reach out directly.

${focus}${whyPart}${kwPart}

I'd welcome a short conversation about how I can help your team. Thank you for your time.

Karan Darji
Detroit, MI · karandarji18@gmail.com`;return {subject:subject,body:body};}
function followupFor(j){const kw=(j.keywords||[]).slice(0,3).join(', ');const subject='Following up — '+j.title+', '+j.employer+' (Karan Darji)';let body=`Hi [Name],

I applied for the ${j.title} role at ${j.employer} two days ago and wanted to follow up directly.

I know it's only been two days — I'm reaching out because I'm persistent about the roles I'm a strong fit for, and this is one of them.${kw ? `

My background lines up on: ${kw}.` : ''}

I'd welcome a short conversation about how I can help your team. Thank you for your time.

Karan Darji
Detroit, MI · karandarji18@gmail.com`;return {subject:subject,body:body};}
function escHtml(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function copyDraft(btn,id){const t=load();const v=t[id];if(!v||!v.snap)return;const d=draftFor(v.snap);const text=d.subject+'\\n\\n'+d.body;const done=function(){btn.textContent='Copied';setTimeout(function(){btn.textContent='Copy message';},2000);};if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(done).catch(function(){fallbackCopy(text);done();});}else{fallbackCopy(text);done();}}
function copyFollowup(btn,id){const t=load();const v=t[id];if(!v||!v.snap)return;const f=followupFor(v.snap);const text=f.subject+'\\n\\n'+f.body;const done=function(){btn.textContent='Copied';setTimeout(function(){btn.textContent='Copy follow-up';},2000);};if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(done).catch(function(){fallbackCopy(text);done();});}else{fallbackCopy(text);done();}}
function fallbackCopy(text){const ta=document.createElement('textarea');ta.value=text;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');}catch(e){}document.body.removeChild(ta);}
function exportCSV(){const t=load();const rows=[['Job','Employer','Location','Salary','Fit','Status','Date applied','Notes','Posting']];Object.keys(t).forEach(function(id){const v=t[id];if(!v||!v.snap)return;if(APPLIED_STATUSES.indexOf(v.status)<0)return;const s=v.snap;rows.push([s.title,s.employer,s.location,s.salary,s.fit,v.status,v.date||'',v.notes||'',s.url]);});const csv=rows.map(function(r){return r.map(function(x){return '"'+String(x==null?'':x).replace(/"/g,'""')+'"';}).join(',');}).join('\\n');const blob=new Blob([csv],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='h1b-job-tracker.csv';a.click();}
function renderTracker(){seedApplications();const t=load();const f=document.getElementById('fstatus').value;const list=document.getElementById('tracklist');const counts={Applied:0,Interview:0,Offer:0,Rejected:0};let html='';Object.keys(t).forEach(function(id){const v=t[id];if(!v||!v.snap)return;const s=v.snap;const st=v.status||'Not applied';if(APPLIED_STATUSES.indexOf(st)<0)return;counts[st]=(counts[st]||0)+1;if(f&&st!==f)return;const d=draftFor(s);const fu=followupFor(s);const li='https://www.linkedin.com/search/results/people/?keywords='+encodeURIComponent(s.employer+' recruiter');html+='<article class="card" data-jobid="'+escHtml(id)+'"><div class="topline"><span class="employer">'+escHtml(s.employer)+'</span><span class="pills"><span class="pill fit">'+escHtml(s.fit)+'/100 fit</span><span class="pill status statuspill">'+escHtml(st)+'</span></span></div><h2>'+escHtml(s.title)+'</h2><p class="meta">'+escHtml(s.location)+' &middot; '+escHtml(s.salary)+'</p><div class="actions"><select class="tracksel" aria-label="Application status" onchange="setStatus(\\''+escHtml(id)+'\\',this.value)">'+['Applied','Interview','Offer','Rejected'].map(function(o){return '<option'+(o===st?' selected':'')+'>'+o+'</option>';}).join('')+'</select><input type="date" value="'+escHtml(v.date||'')+'" onchange="setField(\\''+escHtml(id)+'\\',\\'date\\',this.value)" aria-label="Date applied"><input type="text" placeholder="Notes, recruiter, link..." style="flex:1;min-width:180px" value="'+escHtml(v.notes||'')+'" onchange="setField(\\''+escHtml(id)+'\\',\\'notes\\',this.value)"><a class="apply" href="'+escHtml(s.url)+'" target="_blank" rel="noopener">View posting</a><button class="removebtn" onclick="setStatus(\\''+escHtml(id)+'\\',\\'Not applied\\')">Remove from tracker</button></div><p class="meta">Sponsorship: '+((s.ev==='A_verified_posting'||s.ev==='B_sponsor_history'||s.ev==='Posting states sponsorship'||s.ev==='H-1B sponsor history')?'<span class="yes">Yes</span>':'<span class="ask">Ask recruiter</span>')+'</p><div class="draft"><h3>Draft message — send this to the recruiter / hiring manager</h3><p class="draft-subject">Subject: '+escHtml(d.subject)+'</p><pre class="draft-body">'+escHtml(d.body)+'</pre><div class="actions"><button class="copybtn" onclick="copyDraft(this,\\''+escHtml(id)+'\\')">Copy message</button><a href="'+li+'" target="_blank" rel="noopener">Find the recruiter on LinkedIn</a></div><h3 style="margin-top:18px">Follow-up email — send 2 days after applying</h3><p class="draft-subject">Subject: '+escHtml(fu.subject)+'</p><pre class="draft-body">'+escHtml(fu.body)+'</pre><div class="actions"><button class="copybtn" onclick="copyFollowup(this,\\''+escHtml(id)+'\\')">Copy follow-up</button></div><p class="meta">Replace [Name] with the recruiter\\'s name. The drafts are written from your resume — 4+ years, detection engineering, Zero Trust, CrowdStrike Falcon, Defender, Splunk, Sentinel, Qualys.</p></div></article>';});list.innerHTML=html||'<div class="card empty"><h2>No applications yet</h2><p>When you apply to a job on the main page, click &ldquo;I have applied&rdquo; — it will appear here with a draft message ready to send to the recruiter.</p><p><a class="apply" href="index.html">Browse jobs</a></p></div>';document.getElementById('cApplied').textContent=counts.Applied;document.getElementById('cInterview').textContent=counts.Interview;document.getElementById('cOffer').textContent=counts.Offer;document.getElementById('cRejected').textContent=counts.Rejected;}
renderTracker();
"""

def clean_why(s):
    # Strip the CORE:/STRETCH: annotation prefix — KD wants the exact
    # reason the job fits, not our scoring labels.
    t = str(s or "").strip()
    for p in ("CORE: ", "STRETCH: "):
        if t.startswith(p):
            t = t[len(p):]
            break
    return t

cards = []
for idx, j in enumerate(jobs):
    kws = "".join(f'<span class="kw">{esc(k)}</span>' for k in j.get("keywords_matched", []))
    ev = j.get("sponsorship_evidence", "")
    if ev in ("A_verified_posting", "B_sponsor_history"):
        spon_html = '<span class="yes">Yes</span>'
    else:
        spon_html = '<span class="ask">Ask recruiter</span>'
    sen = j.get("seniority", "core")
    if sen == "core":
        sen_pill = '<span class="pill core">Core — 2–5 yr fit</span>'
    else:
        sen_pill = '<span class="pill stretch">Stretch — senior title / $250k+ pay</span>'
    closes = fmt_date(j.get("closes"))
    closes_txt = f'<span class="sep">·</span>Apply by {esc(closes)}' if closes else ""
    cards.append(f"""
    <article class="card" style="animation-delay:{idx*40}ms" data-jobid="{esc(j['id'])}" data-employer="{esc(j['employer'])}" data-title="{esc(j['title'])}" data-location="{esc(j['location'])}" data-salary="{esc(salary_display(j.get('salary')))}" data-fit="{j['fit_score']}" data-url="{esc(j['url'])}" data-keywords="{esc('|'.join(j.get('keywords_matched', [])))}" data-why="{esc(j.get('why_fit',''))}" data-ev="{esc(ev)}" data-evnote="{esc(j.get('sponsorship_note',''))}">
      <div class="topline"><span class="employer">{esc(j['employer'])}</span>
      <span class="pills"><span class="pill fit">{j['fit_score']}/100 fit</span>{sen_pill}</span></div>
      <h2>{esc(j['title'])}</h2>
      <p class="meta">{esc(j['location'])}<span class="sep">·</span>{esc(salary_display(j.get('salary')))}{closes_txt}</p>
      <div class="row"><div class="lbl">Sponsorship</div><div class="val">{spon_html}</div></div>
      <div class="row"><div class="lbl">Why it fits</div><div class="val">{esc(clean_why(j.get('why_fit','')))}</div></div>
      <div class="row"><div class="lbl">Skills that match</div><div class="val">{kws}</div></div>
      <div class="row"><div class="lbl">Apply link</div><div class="val"><a class="urllink" href="{esc(j['url'])}" target="_blank" rel="noopener">{esc(j['url'])}</a></div></div>
      <div class="actions">
        <a class="apply" href="{esc(j['url'])}" target="_blank" rel="noopener" onclick="markApplied('{esc(j['id'])}')">Apply on the company's site</a>
        <button class="trackbtn" onclick="setStatus('{esc(j['id'])}','Applied')">I have applied</button>
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
    jrm_note = f"<p><strong>You applied to the JRM Cybersecurity Analyst role on Nov 15</strong> — it is on your tracker with a draft message ready to send to the recruiter. Sponsorship is still ask-first (evidence C).</p>"

# Tracker: applied jobs only. Job details come from the localStorage
# snapshot (saved when "I have applied" is clicked) or from JOB_DATA
# (fallback for older entries). JRM is seeded as Applied — KD applied
# Nov 15, 2026 outside the site. The seed is also embedded on the
# index page so the "applied" count is right on first load.
job_data = {}
for j in jobs:
    job_data[j["id"]] = {
        "title": j["title"], "employer": j["employer"], "location": j["location"],
        "salary": salary_display(j.get("salary")), "fit": j["fit_score"],
        "url": j["url"], "keywords": j.get("keywords_matched", []),
        "why": j.get("why_fit", ""), "ev": j.get("sponsorship_evidence", ""),
        "evnote": j.get("sponsorship_note", ""),
    }
seeded = []
if jrm:
    seeded.append({
        "id": jrm["id"], "title": jrm["title"], "employer": jrm["employer"],
        "location": jrm["location"], "salary": salary_display(jrm.get("salary")),
        "fit": jrm["fit_score"], "url": jrm["url"],
        "keywords": jrm.get("keywords_matched", []), "why": jrm.get("why_fit", ""),
        "ev": "C_ask_recruiter", "evnote": jrm.get("sponsorship_note", ""),
        "status": "Applied", "date": "2026-11-15",
        "notes": "Applied Nov 15, 2026 — sponsorship ask-first (evidence C).",
    })
job_data_json = json.dumps(job_data).replace("</", "<\\/")
seeded_json = json.dumps(seeded).replace("</", "<\\/")

index_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Cybersecurity jobs with H-1B sponsorship, curated for Karan Darji and scored against his resume. Every job asks 2-5 years of experience. Every apply link goes to the company's own careers site.">
<title>H-1B Cybersecurity Jobs — curated for Karan Darji</title><style>{CSS}</style></head><body>
<nav class="topnav"><div class="wrap"><a class="brand" href="index.html">H-1B Cybersecurity Jobs</a><span class="spacer"></span><a class="navlink" href="index.html">Jobs</a><a class="navlink" href="tracker.html">My Tracker</a><a class="navlink" href="https://github.com/karandarjishack/h1b-cyber-jobs">GitHub</a></div></nav>
<header><div class="wrap"><h1>H-1B Cybersecurity Jobs</h1></div></header>
<div class="wrap">
<div class="filters"><input id="q" placeholder="Search title, employer, keyword…" oninput="filterJobs()" aria-label="Search jobs"><select id="emp" onchange="filterJobs()" aria-label="Filter by employer"><option value="">All employers</option>{emp_opts}</select></div>
<div id="jobs">{''.join(cards)}</div>
<p id="none" style="display:none">No jobs match that search.</p>
</div>
<script>
const SEEDED_APPLICATIONS={seeded_json};
{SHARED_JS}
seedApplications(); updateBadges(); refreshCount(); filterJobs();
</script></body></html>"""

tracker_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Track H-1B cybersecurity job applications — only the jobs you applied to, each with a draft message for the recruiter. Saved in your browser only.">
<title>Application Tracker — H-1B Cybersecurity Jobs</title><style>{CSS}</style></head><body>
<nav class="topnav"><div class="wrap"><a class="brand" href="index.html">H-1B Cybersecurity Jobs</a><span class="spacer"></span><a class="navlink" href="index.html">Jobs</a><a class="navlink" href="tracker.html">My Tracker</a><a class="navlink" href="https://github.com/karandarjishack/h1b-cyber-jobs">GitHub</a></div></nav>
<header><div class="wrap"><p class="eyebrow">H-1B Cybersecurity Jobs · Karan Darji</p><h1>My Application Tracker</h1>
<p class="sub">Only the jobs you have applied to, each with a draft message for the recruiter.</p></div></header>
<div class="wrap">
<div class="stats" id="stats"><div class="stat"><b id="cApplied">0</b><span>Applied</span></div><div class="stat"><b id="cInterview">0</b><span>Interview</span></div><div class="stat"><b id="cOffer">0</b><span>Offer</span></div><div class="stat"><b id="cRejected">0</b><span>Rejected</span></div></div>
<p><button class="trackbtn" onclick="exportCSV()">Export tracker as CSV</button>
<button class="trackbtn" onclick="if(confirm('Clear all tracker entries in this browser?')){{localStorage.removeItem(KEY);location.reload();}}">Clear tracker</button>
<select id="fstatus" onchange="renderTracker()" aria-label="Filter by status"><option value="">Show: all applied jobs</option><option>Applied</option><option>Interview</option><option>Offer</option><option>Rejected</option></select></p>
<div id="tracklist"></div>
<p class="meta">Tip: on the jobs page, click “I have applied” on a card — it will show up here as Applied, with today's date and a draft message for the recruiter.</p>
</div>
<footer><p>Tracker data is stored in this browser (localStorage). Export the CSV to keep a copy.</p></footer>
<script>
const JOB_DATA={job_data_json};
const SEEDED_APPLICATIONS={seeded_json};
{SHARED_JS}
{TRACKER_JS}
</script></body></html>"""

(ROOT / "docs" / "index.html").write_text(index_html)
(ROOT / "docs" / "tracker.html").write_text(tracker_html)
print(f"Wrote docs/index.html ({len(index_html)} bytes) + docs/tracker.html ({len(tracker_html)} bytes), {len(jobs)} jobs")
