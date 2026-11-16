# CyberJobs — Application Command Center

**Live dashboard:** https://karandarjishack.github.io/h1b-cyber-jobs/

**Latest HTML report:** https://karandarjishack.github.io/h1b-cyber-jobs/reports/latest.html

**Daily GitHub Actions:** https://github.com/karandarjishack/h1b-cyber-jobs/actions/workflows/daily.yml

An application-focused cybersecurity job intelligence dashboard for KD. Designed to reduce time spent researching, applying and preparing hiring-manager outreach. **The dashboard never submits an application or sends an email.**

## What works

- **Daily public ATS discovery** on a scheduled 8 AM America/Detroit job, adjusted for daylight saving time; GitHub's actual workflow start can be delayed.
- **Last seven calendar days** including today, sorted by original published date descending, with a fit-score tie-break. Unknown original dates are not silently treated as new.
- **Non-senior cybersecurity roles** generally requiring 2–5 years, with direct employer/ATS application links and salary when published. No aggregator application links.
- **H-1B evidence classification:** A = employer posting explicitly states sponsorship; B = a matching legal entity has security-title LCAs in the **legacy local CSV** (still held for official-source verification); C = unverified. **No grade guarantees vacancy-specific H-1B transfer or PERM.** Unsupported data stays in the research queue, not in a confirmed-sponsor shortlist.
- **Hiring-manager research channel:** The separate 8 AM ChatGPT research task looks for direct manager/recruiter proof, current title, official profiles and actual vacancy-specific posts and can publish to `docs/research/latest.json` when GitHub publishing is available. **The standalone GitHub Action cannot reliably identify hiring managers.** No guessed contacts or emails.
- **Application convenience:** Compact search/filter rows, Apply, Save, Applied, fit and evidence details; free LinkedIn/public hiring-team search links; exact outreach copy/email draft *after* applying; JSON export/**import** with input validation (local-only tracking).
- **Dated, standalone HTML report** in `docs/reports/YYYY-MM-DD.html`, plus machine-readable JSON snapshots. Original 37 job records retained as `docs/history.json`; previous web dashboard preserved in `docs/legacy.html`.
- **Transparency:** Every daily scan publishes a source-health report. Failed employer boards are counted as failures, not zero available jobs.

## Run schedule

`.github/workflows/daily.yml` schedules **one run at 8:00 AM America/Detroit** using GitHub's timezone-aware scheduling. GitHub may delay the actual start. Manual dispatch and main-branch code-release validation are supported. The workflow runs offline tests **before** live discovery, checks dates, evidence and source health, generates dated HTML/JSON, and pushes only validated report files to `main` using conflict-safe retries. It never rewrites `jobs.json`. On severe feed degradation it fails without publishing an empty replacement.

The **v3 engine** scans public Greenhouse, Ashby and Lever job feeds, known employer Workday career boards, and public SmartRecruiters postings. It derives extra employer board identifiers only from documented links already present in this repository (including archived/held roles), rather than guessing company IDs. Greenhouse original posting dates are fetched from per-job details when necessary. Ashby `publishedAt`, Workday dates, and SmartRecruiters `releasedDate` can be republished/approximate and are explicitly marked **research pending**. The ChatGPT 8 AM research task can supplement sources and investigate managers; GitHub Actions itself does not promise manager identification. Job discovery is **not exhaustive**: employer portals such as Amazon and restricted systems may require manual research. A failed board remains visible as a source failure, not as zero jobs.

## Project files

| File | Purpose |
|---|---|
| `docs/index.html` | Clean responsive application command center |
| `daily_discovery.py` | Backward-compatible wrapper for the v3 engine |
| `research_engine.py` | Multi-source collector, strict screening, provenance and source health |
| `relevance_policy.py` | Technical role taxonomy, weighted match score, Michigan-eligibility checks |
| `tests/test_relevance.py` | 26 labeled relevant/irrelevant cybersecurity title fixtures |
| `docs/research/pending.json` | Daily, dated H-1B and hiring-manager research worklist for manual/ChatGPT verification |
| `tests/test_engine.py` | Offline ATS/visa/date/outage unit tests |
| `tests/board-smoke.mjs` | Browser state, historic records, XSS and tracker import tests |
| `render_daily_report.py` | Dated, offline-readable HTML snapshot |
| `docs/daily.json` | Latest ATS output and source health |
| `docs/research/latest.json` | Separately researched vacancy and hiring contacts |
| `docs/reports/` | Historical daily snapshots |
| `jobs.json`, `jobs_seed.json` | Original 37 jobs and historical seed; preserved |
| `docs/history.json` | Published archive of original job records |
| `sponsors.csv` | Existing historical LCA reference, not live USCIS verification |
| `docs/tracker.html` | Original application tracker |
| `docs/legacy.html` | Previous HTML UI |
| `README_legacy.md` | Original project instructions |

## Privacy and limitations

This repository and its GitHub Pages website are **public**. Do not put private email threads, confidential recruiter notes, contact databases or personal documents into published JSON. Saved/Applied status in the dashboard lives in the browser's localStorage (`h1b_tracker_v1`) and can be exported; it is not automatically synchronized between devices. The public dashboard must never request GitHub tokens from users or embed authentication secrets.

The outreach message is copy-only and must be used **after you actually apply**:

> Hey [First Name],
>
> I just applied for the [Job Title] role at [Company].
>
> Wanted to understand what problem the team is looking to solve through this position.
>
> Looking forward to your response!

No automated applications, emails, DMs or unverifiable manager identities.

## Zero-cost guarantee and limits

This project is designed to operate using **free resources only**:
- Static HTML, JavaScript and CSS served by GitHub Pages from the public repository; no commercial hosting or JS library subscriptions.
- Free-to-access public Greenhouse/Ashby/Lever/Workday/SmartRecruiters ATS job feeds, normal web searches, and public federal immigration data; no Adzuna/JSearch premium API keys or paid recruiter data required.
- GitHub Actions uses hosted runner minutes for a public repository, subject to GitHub's current pricing, quotas, fair-use rules and account settings. This project does not enable billing and cannot guarantee unlimited free service.
- Hiring-manager research uses LinkedIn or company profiles only when publicly accessible. Apollo and premium databases are optional sources that must be skipped if a paid plan is needed.
- Apply on original employers' websites without paying for access. Personal application tracking remains local to your own browser, with free JSON export.

**If any service requests payment or a card, skip it, report the coverage gap, and never turn on paid billing.**

## Verification standards and non-goals

- **Recent means seven Detroit-local calendar dates, inclusive of today.** Use the employer's job-board `first_published` or Lever creation time when available. Republished, inferred and missing dates must never masquerade as certain original dates.
- **The engine never claims a particular employer will sponsor a transfer solely because it has historical LCAs.** It also never invents a hiring manager, LinkedIn hiring post, email address, PERM approval, or salary.
- **Historical catalog:** prior records dated in the last seven days remain visible but are labeled *previous research — recheck*. The live scan does not silently rewrite their status.
- **Fail closed:** if too few employer boards respond, the workflow preserves the prior report, marks the run failed and requires an investigation.
- **Testing:** `python3 -m unittest discover -s tests -p 'test_engine.py' -v`; `node tests/board-smoke.mjs`; `python3 render_daily_report.py`. Live network smoke tests run on a dedicated staging branch before release. All tests use free GitHub runner resources.
- **Actual limits:** GitHub cannot provide full-web search, verified hiring managers, and guaranteed H-1B transfer sponsorship from public ATS feeds alone. Those remain separately researched/manual checks. A good score is not an immigration guarantee.

## Application relevance and quality gates

Search relevance is evaluated separately from immigration support:
- **Technical fit (0–100)** uses the actual role family, matching resume-supported technologies, experience requirements and geographical feasibility. It **does not gain points from corporate H-1B history**.
- Sales, recruiting, business-solutions roles, physical security and senior/principal-level titles are excluded from the non-senior individual-contributor shortlist.
- A 75+ technical score is a prioritization signal, **not** a guarantee of job eligibility, recruiter interest, or work authorization. The dashboard includes a **75+ fit** filter.
- Country-wide remote listings stay pending until Michigan residence is verified; a restricted-state list must not be assumed Michigan-eligible.
- Every validated daily run creates `docs/research/pending.json`, a public prioritized checklist of vacancies needing official LCA/USCIS filing, PERM, actual hiring-team, exact LinkedIn post and verified professional-email research. **It is a research queue, not a verified-contact database.**

Quality gates: unit tests for employer feeds, H-1B wording, posting dates, role relevance, remote-state eligibility, XSS-safe HTML and browser application status; network smoke tests on a staging branch; source-health limits; content validation before GitHub publishing. These tests establish operational reliability on the checked cases—not 90% real-world search recall. Target **9/10** is not currently achieved for hiring-manager verification, exact-position sponsorship, or full-web coverage.

## Run a fresh scan from the dashboard (free)

Select **Run job scan** in the [CyberJobs dashboard](https://karandarjishack.github.io/h1b-cyber-jobs/board-v2.html). It opens a **pre-filled GitHub issue** titled `Run CyberJobs scan`. Sign in as the repository owner and click **Submit new issue**. GitHub Actions automatically starts the ATS discovery, validates the results, commits new JSON/HTML reports, and closes the request issue after the workflow finishes. Open [Actions](https://github.com/karandarjishack/h1b-cyber-jobs/actions/workflows/daily.yml) to see success/failure, then refresh the dashboard. The issue request must be submitted: merely opening the GitHub tab does **not** start a scan.

**Why two clicks?** The dashboard is public and static. Triggering a private GitHub workflow directly from one anonymous click would require exposing an access token or deploying an authenticated backend. Instead, GitHub handles sign-in and authorizes the request without any stored token or paid service. Only issues created by repository owner `karandarjishack` with the exact trigger title can run a scan. Public issue bodies are ignored as code or job-search inputs. Others cannot launch this workflow via issues.

The button starts the **public ATS job scan and GitHub report generation**, not the separate ChatGPT hiring-manager research agent, and it **does not submit job applications or send emails**.

## Application tracker — compact flow view

The [Application tracker](https://karandarjishack.github.io/h1b-cyber-jobs/tracker.html) now uses a Tsenta-style, five-stage Kanban layout: **Saved → Applied → Interview → Offer / Rejected**. Drag cards between stages on desktop or open a card and use the status dropdown on mobile. Search, sort, record dates and private notes, add an external job, and export/import JSON backups. Everything remains on this device in the pre-existing `h1b_tracker_v1` localStorage key. No existing tracker database was deleted or published to GitHub.

GitHub Pages is not a logged-in data service: tracker changes **do not synchronize between different browsers/devices** and GitHub repository history does not contain your application notes. Export a backup if switching devices. The previous tracker is preserved at `docs/tracker-legacy.html`.

## Smoke tests

- `node tests/tracker-smoke.mjs` — verified Kanban stages, browser tracking state, cross-browser backup, XSS escaping, HTTPS-only employer URLs and owner-only issue trigger.
- `node tests/board-smoke.mjs` — recent jobs, filters and existing application status.
- `python3 -m unittest discover -s tests -p 'test_*.py' -v` — ATS discovery and resume evidence tests.
- GitHub Actions runs these before deploying daily results. If the scan fails, no new report is published.
