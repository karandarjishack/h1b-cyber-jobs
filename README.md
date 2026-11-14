# H-1B Cybersecurity Jobs — GitHub wrapper for Karan Darji

A small, honest job finder. Cyber security only, scored against KD's real
resume, and **H-1B sponsors only**.

No paid API. No invented postings. Every job in `jobs.md` was found in a
real listing, checked against DOL / USCIS sponsor evidence, and scored
against `kd_profile.json`.

## What it filters

| Filter | Rule |
|---|---|
| **Cyber only** | Titles in `kd_profile.json`: Security Engineer, Detection Engineer, EDR Engineer, SOC Engineer, Cloud Security, AI Security, Information Security, etc. |
| **Resume fit** | Keywords from KD's actual work: CrowdStrike Falcon, Microsoft Defender, Splunk, Sentinel, Qualys VMDR, Intune, Entra ID, Azure, Zero Trust, Detection Engineering, SIEM, SOAR, VAPT, MITRE ATT&CK, KQL, Python, PowerShell, AI security governance |
| **H-1B only** | Employer filed certified H-1B LCAs for security/cyber titles in FY2025 (DOL data in `sponsors.csv`), OR the posting itself states sponsorship. |
| **Excluded** | "US Citizen only", "will not sponsor", "no sponsorship", TS/SCI, GovCloud. See `excluded.md` for real examples that were dropped. |

KD profile: 4+ years cybersecurity engineering, Cybersecurity Architect
at Detroit Public Schools (80,000 users/endpoints, May 2025–present),
ProNoesis Consultant 2024–2025, Black Box 2019–2021. MS Cybersecurity,
University of New Haven, 2024. CVE-2026-107010 assigned by MITRE
Oct 22, 2026. Location: Detroit, MI — Michigan / Chicago / Remote US preferred.

## Latest run — Nov 13, 2026

See [`jobs.md`](jobs.md) — 9 jobs kept, re-verified Nov 13, 2026, top fit:

1. **CrowdStrike — Detection Engineer, Falcon Complete (Remote)** — 76/100, $100k–$150k, posted Nov 2, closes Jan 1, 2027
2. **Amazon — Security Engineer, Compliance Pentesting (Remote)** — 76/100, $159,300–$202,400, posted Nov 6
3. **Amazon — Security Engineer II, SIRT (Arlington, VA)** — 70/100, $159,300–$202,400, posted Nov 12
4. **Deloitte — AI Cloud Security Engineer, Senior Consultant (Detroit)** — 70/100, AI Zero Trust, KD's strongest differentiator
5. **General Motors — Senior SaaS & AI Security Engineer (Troy, MI)** — 62/100

Full list with apply links, salaries, posted dates, and sponsorship
evidence level (A / B / C) is in `jobs.md`.

## H-1B + PERM trends — the short version

Full sources in [`trends.md`](trends.md).

- **H-1B FY2026:** 343,981 eligible registrations, down 55% from 758,994 in FY2024. Selection rate 34.9–35.3% (120,141 selected). 406,347 petitions approved in FY2025, 2.1% denied. Computer occupations = ~64% of approvals.
- **FY2027 change — wage-weighted lottery + $100,000 fee:** Proclamation Sep 18, 2026. Higher-wage (Level IV) registrations get 4× the weight of Level I. Registrations at the largest IT outsourcers fell 92%. That **helps** KD — a mid/senior security engineer at $140k+ is weighted better than a Level I role.
- **PERM FY2025:** 117,849 applications received, down 22% from 151,773 in FY2024. 138,093 certified. Analyst review ~300–336 days. 157,669 still pending Sep 30, 2025.
- **PERM suspension Oct 8, 2026:** Microsoft, Adobe, Cognizant, Infosys, Tata, Wipro, HCL, Capgemini suspended from PERM, no end date. H-1B is separate — they can still file H-1B — but the green-card path is blocked there for now.
- **Security H-1B, Jul–Sep 2025 (DOL LCA):** 580 employers filed 1,093 certified H-1B applications for security/cyber titles, median $141,378. Security Engineer: 444 filings, median $148,150. Analyst: 201 filings, median $120,300. Top: EY (83 analyst), Amazon (53 engineer), Microsoft (25), Accenture (14), Cognizant (13), JPMorgan (12), Citibank (12), Meta (11).

## Website

`docs/index.html` is the proper website version of `jobs.md` — all 9 jobs
as cards with fit-score bars, search, employer filter, salary, posted
dates, and sponsorship evidence. Regenerate it with `python3 build_site.py`.

**Tracker:** `docs/tracker.html` is a second page — "My Application
Tracker". Click "✓ I have applied" on any job card, or change the status
there to Saved / Applied / Interview / Offer / Rejected, add the date
and notes, and export it as CSV. Tracker data saves in the visitor's
browser only (localStorage) — it is not sent to GitHub and will not
show on another device unless you export the CSV.

**GitHub Pages note:** Pages cannot be switched on for a private repo on
KD's plan — GitHub only serves Pages from public repos unless you upgrade.
So the site file lives in the private repo, but the live Pages URL will
stay 404 until the repo (or a separate public site repo) is made public.
The same site is also available as a private page in Muse — ask for that
if you want to view it without making anything public.

```bash
python3 find_jobs.py
# writes jobs.md, jobs.csv, jobs.json
python3 find_jobs.py --check   # print only, don't rewrite
```

Python 3.10+, no dependencies for the core run.

## How to find the *next* batch

The script scores a human-verified seed (`jobs_seed.json`). To add jobs:

1. Search the sponsor employers in `sponsors.csv` on their official careers pages.
2. Or use these pre-filtered searches (open, filter to cyber titles, check sponsorship text on the posting itself):
   - LinkedIn: https://www.linkedin.com/jobs/search/?keywords=Security%20Engineer&location=United%20States&f_TPR=r604800
   - Indeed: https://www.indeed.com/jobs?q=%22security+engineer%22+%22visa+sponsorship%22&l=United+States&sort=date
   - Amazon jobs: https://www.dreamworkhq.com/c/amazon.com/jobs/security-engineer
   - Deloitte Detroit cyber: https://jooble.org/jobs-cyber-security-software-engineer/Troy%2C-MI
3. Add the job to `jobs_seed.json` with `title, employer, location, salary, posted, url, keywords_matched, sponsorship_evidence (A/B/C), sponsorship_note, why_fit`.
4. Run `python3 find_jobs.py` — it scores, filters exclusions, and regenerates `jobs.md`.

Do **not** add a job if the posting says US Citizen only, will not sponsor,
no sponsorship, or requires TS/SCI / GovCloud. Put it in `excluded.md` instead.

## Push this to GitHub

```bash
cd h1b-cyber-jobs
git init
git add .
git commit -m "H-1B cyber jobs wrapper for KD - first run Nov 13 2026"
gh repo create karandarjishack/h1b-cyber-jobs --private --source=. --push
# or create the repo on github.com first, then:
# git remote add origin https://github.com/karandarjishack/h1b-cyber-jobs.git
# git branch -M main && git push -u origin main
```

The GitHub Action in `.github/workflows/daily.yml` runs `find_jobs.py`
every Monday at 8:00 AM ET and commits any updated `jobs.md` — it only
re-scores the seed, it does not invent new jobs. New jobs still need a
human to add them to `jobs_seed.json` (that's the honesty guardrail).

## Files

- `find_jobs.py` — scorer + filter + output generator
- `kd_profile.json` — KD's resume profile used for scoring
- `sponsors.csv` — H-1B sponsor evidence, DOL Q4 FY2025 + PERM status
- `jobs_seed.json` — verified seed jobs
- `jobs.md` / `jobs.csv` / `jobs.json` — latest curated output
- `trends.md` — H-1B + PERM trends with sources
- `excluded.md` — roles dropped by the filter, with reasons
