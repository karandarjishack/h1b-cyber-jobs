# CyberJobs — Application Command Center

**Live dashboard:** https://karandarjishack.github.io/h1b-cyber-jobs/

**Latest HTML report:** https://karandarjishack.github.io/h1b-cyber-jobs/reports/latest.html

**Daily GitHub Actions:** https://github.com/karandarjishack/h1b-cyber-jobs/actions/workflows/daily.yml

An application-focused cybersecurity job intelligence dashboard for KD. Designed to reduce time spent researching, applying and preparing hiring-manager outreach. **The dashboard never submits an application or sends an email.**

## What works

- **Daily public ATS discovery** on a scheduled 8 AM America/Detroit job, adjusted for daylight saving time; GitHub's actual workflow start can be delayed.
- **Last seven calendar days** including today, sorted by original published date descending, with a fit-score tie-break. Unknown original dates are not silently treated as new.
- **Non-senior cybersecurity roles** generally requiring 2–5 years, with direct employer/ATS application links and salary when published. No aggregator application links.
- **H-1B evidence classification:** A = posting says sponsorship; B = historical certified cybersecurity-title LCAs for matching employer; C = no verified cyber-title sponsorship and must be confirmed with recruiting. **A/B is evidence, not a promise of vacancy-level H-1B transfer or PERM.**
- **Hiring-manager research channel:** The separate 8 AM ChatGPT research task looks for direct manager/recruiter proof, current title, official profiles and actual vacancy-specific posts and can publish to `docs/research/latest.json` when GitHub publishing is available. **The standalone GitHub Action cannot reliably identify hiring managers.** No guessed contacts or emails.
- **Application convenience:** Search and filter, apply links, fit summary, copy the user's post-application outreach template, and mark jobs Saved/Applied.
- **Dated, standalone HTML report** in `docs/reports/YYYY-MM-DD.html`, plus machine-readable JSON snapshots. Original 37 job records retained as `docs/history.json`; previous web dashboard preserved in `docs/legacy.html`.
- **Transparency:** Every daily scan publishes a source-health report. Failed employer boards are counted as failures, not zero available jobs.

## Run schedule

`.github/workflows/daily.yml` has UTC schedules at 12:00 and 13:00 with a Detroit-local 08:00 guard. This avoids daylight-saving shifts; one slot exits without writing. A manual dispatch is supported for testing. On success, the workflow validates dates, generates `docs/daily.json` and date-stamped HTML/JSON, and commits them to `main`. It never rewrites `jobs.json`.

GitHub job discovery is not exhaustive web crawling: it accesses a rotating set of public Greenhouse, Ashby and Lever boards. Some employer boards are restricted, and Workday/Amazon/other systems may require separate research. The ChatGPT daily research task is intended to supplement those sources. A source failure is surfaced explicitly.

## Project files

| File | Purpose |
|---|---|
| `docs/index.html` | Clean responsive application command center |
| `daily_discovery.py` | Public ATS seven-day discovery and evidence filtering |
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
- Free-to-access public Greenhouse/Ashby/Lever ATS job feeds, normal web searches, and public federal immigration data; no Adzuna/JSearch premium API keys or paid recruiter data required.
- GitHub Actions uses hosted runner minutes for a public repository, subject to GitHub's current pricing, quotas, fair-use rules and account settings. This project does not enable billing and cannot guarantee unlimited free service.
- Hiring-manager research uses LinkedIn or company profiles only when publicly accessible. Apollo and premium databases are optional sources that must be skipped if a paid plan is needed.
- Apply on original employers' websites without paying for access. Personal application tracking remains local to your own browser, with free JSON export.

**If any service requests payment or a card, skip it, report the coverage gap, and never turn on paid billing.**
