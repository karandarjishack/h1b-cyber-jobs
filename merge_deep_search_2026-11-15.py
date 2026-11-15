#!/usr/bin/env python3
"""merge_deep_search_2026-11-15.py — Nov 15, 2026 evening.

Merges the deep resume-driven web search (5 research workers) into the repo:
- 12 new CORE jobs -> jobs_seed.json (dedup vs seed + held + archives)
- 4 stretch jobs -> jobs_stretch_archived_2026-11-15.json (core-only rule)
- Deloitte PAM Senior Consultant -> jobs_out_of_band_2026-11-15.json
  (6+ yr general-experience line; parent to decide)
- ~45 link-pending roles -> held_jobs.json (direct link needs live board lookup)
- 4 closures marked in held_jobs.json
- New blanket no-sponsorship employers -> excluded.md
- New sponsors -> sponsors.csv (+ WRITER/Qatalog correction)
- Unisys why_fit rewritten recruiter-safe (the PAY FLAG note lived in the
  why_fit and would leak into the tracker draft; the low salary is still
  visible on the card and in the fit score of 40)

Run: python3 merge_deep_search_2026-11-15.py && python3 find_jobs.py && python3 build_site.py
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SEED = ROOT / "jobs_seed.json"
HELD = ROOT / "held_jobs.json"
STRETCH_ARCH = ROOT / "jobs_stretch_archived_2026-11-15.json"
OUT_OF_BAND = ROOT / "jobs_out_of_band_2026-11-15.json"
EXCLUDED = ROOT / "excluded.md"
SPONSORS = ROOT / "sponsors.csv"

EV_B = "B_sponsor_history"
EV_C = "C_ask_recruiter"
EV_A = "A_verified_posting"


def job(job_id, title, employer, location, salary, years, url, ev, note, why, kws, posted=None, closes=None):
    return {
        "id": job_id, "title": title, "employer": employer, "location": location,
        "salary": salary, "years_required": years, "url": url,
        "sponsorship_evidence": ev, "sponsorship_note": note, "why_fit": why,
        "keywords_matched": kws, "posted": posted, "closes": closes,
        "apply_link_type": "direct", "also_at": None,
    }


NEW_CORE = [
    job("stellantis-cyber-ir-team-analyst-2022245",
        "Cyber Security Incident Response Team Analyst", "Stellantis",
        "Auburn Hills, MI, USA", "Not listed", 3,
        "http://careers.stellantis.com/job/24041201/cyber-security-incident-response-team-analyst-auburn-hills-mi/?source=Career_website",
        EV_C,
        "C — FCA US LLC filed 238 certified H-1B LCAs Jul 2025–Jun 2026, 326 in FY2025; posting silent, no exclusion language. Bulk of FCA LCAs are engineering titles, not security-specific — ask recruiter.",
        "Microsoft Sentinel SIEM (explicit), EDR/XDR, threat hunting, incident response, MITRE ATT&CK — near-exact match to KD's Sentinel/SOC/detection stack. 3 years asked, Detroit-area (Auburn Hills).",
        ["Microsoft Sentinel", "SIEM", "EDR", "MITRE ATT&CK"], posted="2026-10-21"),
    job("stellantis-appsec-analyst-2022246",
        "Application Security Analyst", "Stellantis",
        "Auburn Hills, MI, USA (on-site)", "Not listed", 3,
        "https://careers.stellantis.com/job/24043496/application-security-analyst-auburn-hills-mi/",
        EV_C,
        "C — FCA US LLC filed 238 certified H-1B LCAs Jul 2025–Jun 2026, 326 in FY2025; posting silent, no exclusion language. Bulk of FCA LCAs are engineering titles, not security-specific — ask recruiter.",
        "SAST/DAST/IAST, WAF (Akamai, Cloudflare, AWS WAF, Azure Front Door), DevSecOps/CI-CD, Python, OWASP Top 10, NIST/ISO 27001 — KD's VAPT/AppSec background. 3+ years asked, Detroit-area (on-site 5 days/week).",
        ["Python", "VAPT"], posted="2026-10-22"),
    job("doordash-enterprise-sec-eng-7983583",
        "Enterprise Security Engineer", "DoorDash",
        "Remote, US", "$130,600–$192,000", 2,
        "https://job-boards.greenhouse.io/doordashusa/jobs/7983583",
        EV_B,
        "B — DoorDash is a large H-1B sponsor (2,872 LCAs FY2020–2026, 673 last 2 FYs); role tagged 'H1B Visa Sponsor'. Confirm with recruiter for this requisition.",
        "EDR/XDR platforms, Zero Trust network access, identity-aware proxies, browser security, DLP, MDM — near-perfect EDR + Zero Trust + identity match. 2–5 years asked. (Different role from the closed 3-yr Detection Engineer.)",
        ["EDR", "XDR", "Zero Trust"], posted="2026-06-09"),
    job("bofa-manual-ethical-hacker-26037817",
        "Manual Ethical Hacker", "Bank of America",
        "Denver, CO / Washington, DC / Chicago, IL, USA", "Not listed", 4,
        "https://careers.bankofamerica.com/en-us/job-detail/26037817/manual-ethical-hacker-multiple-locations",
        EV_B,
        "B — Bank of America filed 443 certified LCAs FY2026 Q1–Q3, 790 FY2025. Confirm per role.",
        "Manual SQLi/XSS without tools, Burp/SQLMap, SAST, code review; CEH/OSCP desired — near-exact match to KD's VAPT track record (CEH, CWAPT, verified bounties). 4 years asked.",
        ["VAPT"], posted="2026-10-15"),
    job("bofa-vuln-identification-analyst-26038579",
        "Vulnerability Identification Analyst", "Bank of America",
        "Multiple Locations, USA", "Not listed", 3,
        "https://careers.bankofamerica.com/en-us/job-detail/26038579/vulnerability-identification-analyst-multiple-locations",
        EV_B,
        "B — Bank of America filed 443 certified LCAs FY2026 Q1–Q3, 790 FY2025. Confirm per role.",
        "CVE-based vulnerability identification and risk analysis, Tanium — matches KD's Qualys VMDR and vulnerability-remediation day job. 3–5+ years asked.",
        ["Qualys VMDR"], posted="2026-10-20"),
    job("bofa-app-remediation-governance-analyst-26040010",
        "Cyber Security Application Remediation Governance Analyst", "Bank of America",
        "Washington, DC / Chicago, IL / Denver, CO, USA", "Not listed", 3,
        "https://careers.bankofamerica.com/en-us/job-detail/26040010/job-posting-title-cyber-security-application-remediation-governance-analyst-multiple-locations",
        EV_B,
        "B — Bank of America filed 443 certified LCAs FY2026 Q1–Q3, 790 FY2025. Confirm per role.",
        "Vulnerability remediation governance plus AI/LLM-identified vulnerabilities — combines KD's VMDR work with his AI-security differentiator. 3+ years asked. (Ladders copy lists $99,200–$145,000; salary not shown on BofA page.)",
        ["Qualys VMDR"], posted="2026-10-29"),
    job("bofa-appsec-ops-specialist-26037894",
        "Application Security Operations Specialist", "Bank of America",
        "Washington, DC / Chicago, IL / Charlotte, NC / Denver, CO, USA", "Not listed", 3,
        "https://careers.bankofamerica.com/en-us/job-detail/26037894/application-security-operations-specialist-multiple-locations",
        EV_B,
        "B — Bank of America filed 443 certified LCAs FY2026 Q1–Q3, 790 FY2025. Confirm per role.",
        "Vulnerability management, MITRE ATT&CK, Python/PowerShell scripting desired, AI-assisted vulnerability identification and frontier AI model testing — matches KD's VMDR + AI-security work. 3+ years asked.",
        ["MITRE ATT&CK", "Python", "PowerShell"], posted="2026-10-14"),
    job("coinbase-sec-eng-corporate-sec-8319444",
        "Security Engineer, Corporate Security", "Coinbase",
        "Remote, USA", "$152,405–$179,300", 3,
        "https://www.coinbase.com/careers/positions/8319444",
        EV_B,
        "B — Coinbase filed 118 certified LCAs FY2026 Q1–Q3, 186 FY2025, including 5 Information Security Engineer LCAs Jul 2025–Jun 2026. Confirm per role.",
        "Corporate infrastructure, endpoints, enterprise apps and network — KD's EDR/endpoint + Zero Trust stack. 3+ years asked, remote.",
        ["EDR", "Zero Trust"], posted="2026-10-30"),
    job("schwab-appsec-eng-2026-122290",
        "Application Security Engineer", "Charles Schwab",
        "Southlake, TX / Omaha, NE / Orlando, FL, USA", "Not listed", 2,
        "https://www.schwabjobs.com/job/southlake/application-security-engineer/33727/95597965760",
        EV_B,
        "B — Charles Schwab filed 346 certified LCAs FY2026 Q1–Q3, 577 FY2025, 412 H-1B petitions approved FY2026 at ~99%; 27% of filings are transfers. Confirm per role.",
        "SAST (Fortify), CodeQL, GitHub Advanced Security, Python automation, threat modeling, OWASP, secure code review — KD's AppSec/VAPT + Python. 2-year minimum; KD's 4 years sits inside the band.",
        ["Python", "VAPT"], posted="2026-11-11", closes="2026-11-15"),
    job("abbvie-splunk-cribl-eng-r00147767",
        "Splunk / Cribl Engineer, Cybersecurity Engineering", "AbbVie",
        "North Chicago, IL, USA (Hybrid)", "$84,500–$162,000", 4,
        "https://careers.abbvie.com/en/job/splunk-cribl-engineer-cybersecurity-engineering-hybrid-in-north-chicago-il-jid-31077",
        EV_B,
        "B — AbbVie filed 273 LCAs in 2025; posting has no exclusion language. Confirm per role.",
        "Splunk Enterprise admin, SPL, SIEM platform optimization, data pipelines/onboarding, ETL, Python/PowerShell — direct match to KD's Splunk SIEM work feeding Defender + CrowdStrike + Intune + Qualys telemetry. Qualifies via the Master's track (Bachelor's track asks 5 yrs; KD has MS + 4+ yrs).",
        ["Splunk", "SIEM", "Python", "PowerShell"], posted="2026-07-31"),
    job("abbvie-assoc-devsecops-eng-r00150206",
        "Associate DevSecOps Engineer, Platform and Tooling", "AbbVie",
        "Mettawa, IL, USA (Remote)", "$84,500–$162,000", 4,
        "https://careers.abbvie.com/en/job/associate-devsecops-engineer-platform-and-tooling-in-mettawa-il-jid-35392",
        EV_B,
        "B — AbbVie filed 273 LCAs in 2025; posting has no exclusion language. Confirm per role.",
        "Building enterprise AppSec program from the ground up; SAST/DAST/IAST/SCA tooling in CI/CD (GitHub Actions, Azure DevOps), Python automation, ASPM, Snyk/container scanning — KD's VAPT + DevSecOps + Python. Qualifies via the Master's track (Bachelor's track asks 5 yrs).",
        ["Python", "VAPT"], posted="2026-11-04"),
    job("kirkland-cyber-eng-ii-18458770",
        "Cybersecurity Engineer II", "Kirkland & Ellis",
        "Chicago, IL, USA", "$133,000–$166,000", 3,
        "https://staffjobsus.kirkland.com/jobs/18458770-cybersecurity-engineer-ii",
        EV_C,
        "C — Kirkland filed 42 certified LCAs Oct 2025–Jun 2026 and 53 H-1B petitions approved FY2025, but 41 of 42 recent LCAs are for Lawyers (1 Data Scientist). No tech-staff LCA evidence; posting silent on sponsorship. Ask recruiter before applying.",
        "CrowdStrike, Microsoft Sentinel, Google SecOps, Netskope, Cisco Umbrella, BeyondTrust, CyberArk, Microsoft Entra, Azure, Zero Trust, PowerShell, Python, KQL; SC-200 preferred (KD holds it). Near-perfect stack match. 3–5+ years cybersecurity engineering asked.",
        ["CrowdStrike Falcon", "Microsoft Sentinel", "Microsoft Entra ID", "Zero Trust", "PowerShell", "Python", "KQL"]),
]

# Stretch (senior title, in-band years) — archived under the core-only rule,
# restorable on KD's word. Stryker is NOT here: its sponsorship is in conflict.
NEW_STRETCH = [
    job("intuit-sr-sec-eng-dfir-23939",
        "Senior Security Engineer, Digital Forensics and Incident Response (DFIR)", "Intuit",
        "Frisco, TX, USA", "Not listed", 3,
        "https://jobs.intuit.com/job/frisco/senior-security-engineer-digital-forensics-and-incident-response-dfir/27595/100730647872",
        EV_B,
        "B — Intuit: 3,680 H-1B petitions approved FY2022–2026 (928 FY2026, 919 FY2025, 99.7% approval); 4,344 certified LCAs.",
        "DFIR + SOC + AI/LLM incident response playbooks; detection engineering with CrowdStrike Falcon and Wiz; AWS/Azure/GCP. 3–5 years asked.",
        ["CrowdStrike Falcon"], posted="2026-09-14"),
    job("intuit-sr-ir-sec-eng-escalations-23936",
        "Senior Incident Response Security Engineer, Escalations", "Intuit",
        "Charlotte, NC, USA", "Not listed", 3,
        "https://jobs.intuit.com/job/charlotte/senior-incident-response-security-engineer-escalations/27595/100643069376",
        EV_B,
        "B — Intuit: 3,680 H-1B petitions approved FY2022–2026 (928 FY2026, 919 FY2025, 99.7% approval); 4,344 certified LCAs.",
        "SOC escalations IR; CrowdStrike Falcon + Wiz; cloud IAM/CI/CD/network security/DLP. 3–5 years asked.",
        ["CrowdStrike Falcon"], posted="2026-09-14"),
    job("deloitte-cloud-sec-sr-consultant-m365-353826",
        "Cloud Security Senior Consultant, M365", "Deloitte",
        "Detroit, MI, USA", "$105,100–$207,800", 4,
        "https://apply.deloitte.com/en_US/careers/JobDetail/Cloud-Security-Senior-Consultant-M365/353826",
        EV_A,
        "A — posting states 'Limited immigration sponsorship may be available.'",
        "Purview, Intune, Sentinel, Security Copilot, Entra ID, Defender for Office/Endpoints/Servers/Vulnerabilities/Cloud Apps, Defender XDR, SCCM, MFA, Conditional Access. Preferred certs include SC-200 (KD holds it). Strongest stack match in the stretch set. 4+ years asked. 50% travel in North America.",
        ["Microsoft Sentinel", "Microsoft Defender", "Microsoft Entra ID", "Microsoft Intune"], posted="2026-05-21", closes="2026-12-31"),
    job("deloitte-cyber-operate-soc-l3-sr-369556",
        "Cyber Operate SOC L3 Analyst / Shift Lead, Senior Consultant", "Deloitte",
        "Detroit, MI, USA", "$105,400–$207,800", 4,
        "https://apply.deloitte.com/en_US/careers/JobDetail/Cyber-Operate-SOC-L3-Analyst-Shift-Lead-Senior-Consultant/369556",
        EV_A,
        "A — posting states 'Limited immigration sponsorship may be available.'",
        "SIEM, IDS/IPS, DLP, Proxy, WAF, EDR, threat intel, pen testing, MITRE, SQLi/XSS, threat hunting; preferred experience explicitly includes Detection Engineering or Vulnerability Management. 4+ years asked. Rotating 24/7 shifts; requires CISSP/GIAC/CEH or equivalent (KD holds CEH).",
        ["SIEM", "EDR", "MITRE ATT&CK"], posted="2026-10-02", closes="2026-12-31"),
]

# Out of band (6+ yr general-experience line) — parent to decide.
OUT_OF_BAND_ADD = [
    job("deloitte-pam-sr-consultant-cyberark-365234",
        "PAM Senior Consultant, CyberArk/BeyondTrust/Delinea", "Deloitte",
        "Detroit, MI, USA", "$105,400–$207,800", 6,
        "https://apply.deloitte.com/en_US/careers/JobDetail?jobId=365234",
        EV_A,
        "A — posting states 'Limited immigration sponsorship may be available.'",
        "Identity/PAM adjacent to KD's Entra/identity strength — CyberArk, SCIM, directory services, credential rotation, privileged account lifecycle. 4+ years PAM, BUT the posting also requires 6+ years of general information-systems experience — out of band under the 2–5 yr rule.",
        ["Microsoft Entra ID"], posted="2026-09-01", closes="2026-12-31"),
]

# ---------------------------------------------------------------------------
# Link-pending queue (Section C of the deep-search report): role + sponsorship
# verified, direct apply link needs one live-browser board lookup.
# Tuple: (id, title, employer, location, salary, years, evidence, note)
# years=None means unverified / not stated.
# ---------------------------------------------------------------------------
HELD_ADD = [
    ("salesforce-endpoint-sec-mts-jr323795",
     "Systems Engineering, Endpoint Security MTS", "Salesforce",
     "Seattle, WA / San Francisco, CA / Dallas, TX, USA", "$128,500–$176,700", 2, EV_B,
     "Near-perfect KD fit (EDR, CrowdStrike/Tenable/Tanium/Qualys, Python, SIEM/SOAR). TOP PRIORITY hunt: find on Salesforce Workday board (salesforce.wd12.myworkdayjobs.com) by JR323795."),
    ("google-ai-threat-defense-eng-i",
     "AI Threat Defense Engineer I, Google Cloud Consulting", "Google",
     "Austin, TX / Atlanta, GA / Boulder, CO / Chicago, IL / New York, NY / San Francisco, CA / Sunnyvale, CA, USA",
     "$127,000–$182,000", 3, EV_B,
     "AI threat defense, FedRAMP/PCI/HIPAA, Python. URGENT: application window open only until at least Nov 18, 2026. Find via live Google Careers search."),
    ("ey-sts-endpoint-sec-eng-1746330",
     "STS Endpoint Security Engineer", "EY",
     "Hoboken, NJ, USA (anywhere US)", "$91,100–$170,400", 4, EV_B,
     "Endpoint/data security Linux/Mac/Windows, Azure/AWS/GCP. EY is the #1 security sponsor (83 filings Q4 FY2025). Find via live EY careers search by Req 1746330."),
    ("mongodb-product-sec-eng-3263210599",
     "Product Security Engineer", "MongoDB",
     "US (Hybrid)", "$101,000–$198,000", 3, EV_B,
     "3 yrs AppSec/product security, Req ID 3263210599. MongoDB: 670 certified LCAs FY2020–2026. Find on job-boards.greenhouse.io/mongodb."),
    ("circle-sec-eng-dr",
     "Security Engineer II, Detection and Response", "Circle",
     "Remote, US", "$122,500–$165,000", 2, EV_A,
     "SIEM + orchestration, detection-as-code, AWS/EKS, Python/Golang, 'Advance deployment of AI to SOC function' — closest match to KD's AI-SOC differentiator. Posting states 'eligible for day-one PERM sponsorship for qualified candidates' (A). Published Aug 12, 2026 — confirm still open. Find on Circle's Greenhouse board."),
    ("circle-sr-sec-eng-dr",
     "Senior Security Engineer, Detection and Response", "Circle",
     "Remote, US", "$147,500–$195,000", 4, EV_A,
     "SIEM/SOAR, Panther/Snowflake, SQL + Python. Same day-one PERM line (A). Senior title — stretch if listed."),
    ("instacart-detection-eng-ii",
     "Detection Engineer II", "Instacart",
     "Remote, US", "$142,000–$180,500", 2, EV_B,
     "Detection engineering/IR/offensive security, endpoint/cloud/container/SaaS telemetry, AWS/Azure/GCP. Published Nov 9, 2026; apply before Dec 9, 2026. Find on boards.greenhouse.io/instacart (surfaced IDs 1804355/2002537 are generic board snapshots, NOT this role — do not use)."),
    ("paloalto-staff-sec-eng-soc-ai-ml",
     "Staff Security Engineer, SOC AI/ML Specialist", "Palo Alto Networks",
     "US", "$123,000–$200,000", 3, EV_A,
     "3+ yrs InfoSec automation/tooling for SecOps; AI/LLM + ML via XSIAM BYOML. Posting explicitly states 'Is role eligible for Immigration Sponsorship?: Yes' (A). Strong KD fit (AI security governance + SOC automation + Python). Find on careers.paloaltonetworks.com."),
    ("salesforce-offensive-sec-eng-redteam",
     "Offensive Security Engineer, Red Team", "Salesforce",
     "San Francisco, CA / Bellevue, WA, USA (Hybrid)", "$117,200–$223,900", 3, EV_B,
     "3+ yrs red teaming/pentesting/adversary simulation, purple team with Detection Engineering, AI-abuse testing on Agentforce. Find on Salesforce Workday board."),
    ("toast-secops-eng",
     "Security Operations Engineer", "Toast",
     "Remote, US", "$104,000–$166,000", 3, EV_C,
     "3+ yrs SecOps/IR/detection engineering, Splunk/QRadar/Sentinel, EDR, Python/Ruby/Go, threat hunting. Salary conflict ($104k–$166k vs $79k–$126k — zone differences); some Toast postings say 'will not sponsor' — check the sponsorship line on the live Greenhouse posting. Find on careers.toasttab.com."),
    ("scaleai-sec-eng-dr",
     "Security Engineer, Detection & Response", "Scale AI",
     "San Francisco, CA / New York, NY / Seattle, WA, USA", "$172,000–$215,000", 3, EV_B,
     "3–5+ yrs, detection + IR + investigations. 72 certified H-1B LCAs FY2026 Q1–Q3. Posted 9/13/2025 — confirm still open. Find on scale.com careers / Greenhouse board."),
    ("rapid7-detection-eng-tide",
     "Detection Engineer (TIDE team)", "Rapid7",
     "US", "Not listed", 3, EV_B,
     "3+ yrs SOC/IR/offensive OR 2+ yrs threat intel/detection engineering; SentinelOne/CrowdStrike/Defender detections, Splunk use-case rules, MITRE ATT&CK. FY2025: 5 LCAs filed, 5 I-129s approved, 0 denied. Rapid7 moved Greenhouse → Lever; Lever API 404s in text fetch. Find on Rapid7's Lever board."),
    ("okta-sec-analyst-dr",
     "Security Analyst, Detection & Response", "Okta",
     "US (Remote)", "$154,000+ OTE", 3, EV_B,
     "3–5 yrs, Auth0 IR, incident commander, threat hunting, Linux/Mac CLI, forensics, AWS/Azure/GCP; min OTE $154,000/yr + equity. FY2025: 120 LCAs, 106 I-129s approved, 0 denied. Find on Okta's Greenhouse board."),
    ("sofi-staff-enterprise-sec-eng",
     "Staff Enterprise Security Engineer", "SoFi",
     "Seattle, WA / San Francisco, CA / Cottonwood Heights, UT / New York, NY / Frisco, TX, USA",
     "Not listed", 3, EV_B,
     "Bachelor's + 3–4 yrs OR Master's + 2–3 yrs, DLP (Zscaler, Proofpoint, Sentra), CrowdStrike, zero-trust, Python/Go/PowerShell. Social Finance: 90 LCAs FY2026, 162 I-129 petitions FY2025 (161 approved). Senior title — stretch if listed. Find on SoFi's Greenhouse board."),
    ("google-sec-eng-cloud-threat-abuse",
     "Security Engineer, Cloud Threat and Abuse Detection", "Google",
     "Sunnyvale, CA, USA", "$147,000–$211,000", 2, EV_B,
     "2 yrs, host/memory forensics and detections. Published Mar 28, 2026 — confirm still open."),
    ("google-sec-eng-ai-protection",
     "Security Engineer III, AI Protection", "Google",
     "Seattle, WA, USA", "$141,000–$202,000", 2, EV_B,
     "'Experience in conducting AI Red Teaming or participating in AI bug bounties' — excellent KD fit. Published Feb 18, 2026 — confirm still open."),
    ("microsoft-sec-eng-morse",
     "Security Engineer 2, MORSE", "Microsoft",
     "Atlanta, GA, USA", "$100,600–$199,000", 2, EV_B,
     "Master's + 1 yr / Bachelor's + 2 yrs, Pen Testing IC3. Distinct from Windows Security II."),
    ("microsoft-sec-eng-teams",
     "Security Engineer II, Teams group", "Microsoft",
     "US", "$100,600–$199,000", 2, EV_B,
     "Master's + 1 yr / Bachelor's + 2 yrs. Published Feb 13, 2026."),
    ("github-sec-eng-platform-fundamentals",
     "Security Engineer III, Platform Fundamentals", "GitHub",
     "Remote, US", "$97,900–$259,900", 3, EV_B,
     "5+ yrs headline (or Bachelor's + 3 yrs / Master's + 1 yr), 3+ yrs securing Azure, Wiz, Python. Years at top edge of band."),
    ("visa-cyber-eng-mobile-ai-austin",
     "Cybersecurity Engineer, Mobile & AI Application", "Visa",
     "Austin, TX, USA (Hybrid)", "$118,700–$183,600", 2, EV_B,
     "Mobile/Mac security, AI dev tooling (Claude Coding). The 'Visa will not sponsor' line belongs to the Intern variant, NOT this full-time role. Find on jobs.smartrecruiters.com/Visa."),
    ("deloitte-sailpoint-consultant-sec-eng-ii-detroit",
     "Cyber Identity, SailPoint Consultant – Security Engineer II", "Deloitte",
     "Detroit, MI, USA", "$82,600–$162,800", 2, EV_A,
     "SailPoint IdentityIQ/Identity Security Cloud. Sponsorship A ('Limited immigration sponsorship may be available'). Recruiting ends Dec 31, 2026. Find on apply.deloitte.com ('SailPoint Consultant' + Detroit)."),
    ("usbank-info-sec-eng-ii-network",
     "Info Security Engineer II (Network Security)", "U.S. Bank",
     "US (Hybrid)", "Not listed", 3, EV_C,
     "3+ yrs, firewalls/IDS/IPS/VPNs/proxies/DNS, threat detection/VM/risk mitigation, published Oct 20, 2026, hybrid 3+ days on-site. LCA counts unverified — check before listing. Find on careers.usbank.com."),
    ("elastic-sr-threat-detection-eng",
     "Senior Threat Detection Engineer", "Elastic",
     "US (Remote)", "$133,100–$210,600", 3, EV_C,
     "3+ yrs, Elastic Security/SIEM, detection-as-code, cloud. Senior title — stretch if listed. LCA counts unverified; posting requires eligibility for DoD Impact Level 4 environments (not a citizenship statement, but check). Find on Elastic's Greenhouse board."),
    ("optum-info-sec-eng-2374249",
     "Information Security Engineer", "Optum / UnitedHealth Group",
     "Remote, US", "$72,800–$130,000", 3, EV_B,
     "3+ yrs, Splunk, Tanium, ServiceNow, Microsoft Defender, Azure Security, Python/PowerShell, AI-powered security automations. UHG is a massive H-1B sponsor. Find on careers.unitedhealthgroup.com by Req 2374249. WARNING: a different UHG posting (UHG-2346007) states 'Due to FISMA US Citizenship is required' — do not confuse the two."),
    ("homedepot-cyber-eng-ii-siem-edr",
     "Cybersecurity Engineer II, SIEM and EDR", "Home Depot",
     "Remote, US", "$90,000–$130,000", 2, EV_B,
     "2+ yrs cyber / 1+ yrs SIEM-EDR with Splunk/CrowdStrike/Cortex XSIAM, published Aug 13, 2026. Find on homedepot.wd5.myworkdayjobs.com."),
    ("homedepot-cyber-eng-ii-network-sec",
     "Cybersecurity Engineer II, Network Security", "Home Depot",
     "Atlanta, GA, USA", "$90,000–$130,000", 2, EV_B,
     "Req 153660, 2+ yrs, Python/Ansible, firewall lifecycle, IR/VM. Find on homedepot.wd5.myworkdayjobs.com."),
    ("homedepot-cyber-sw-eng-ii-ml-ai",
     "Cybersecurity Software Engineer II, ML & AI", "Home Depot",
     "Remote, US", "$90,000–$140,000", 2, EV_B,
     "LangChain/LangGraph, MCP, RAG, MITRE ATT&CK/detection engineering — strong AI-security fit, published Oct 26, 2026. Find on homedepot.wd5.myworkdayjobs.com."),
    ("jpmorgan-sec-eng-ii-houston-210715113",
     "Security Engineer II", "JPMorgan Chase",
     "Houston, TX, USA", "Not listed", 2, EV_B,
     "'2 plus years of relevant experience,' cloud security (AWS), Active Directory/GPO, Python/Java. Posted Mar 27, 2026 — possibly stale; confirm still open. Find on JPMorgan careers by requisition 210715113."),
    ("paypal-cyber-eng-defense-center",
     "Cybersecurity Engineer, Defense Center", "PayPal",
     "US", "Not listed", 2, EV_B,
     "1+ / min 2 yrs, Defense Center monitoring/response, IR. Published Apr 6, 2026 — confirm still open. Find on careers.pypl.com."),
    ("datadog-sec-eng-ii-cloud-sec-7205511",
     "Security Engineer II, Cloud Security", "Datadog",
     "US", "$145,000–$190,000", None, EV_B,
     "Direct link exists (careers.datadoghq.com/detail/7205511/?gh_jid=7205511) but the fetched page (crawled Jan 4, 2026) contains NO years text — years unverifiable + page stale; live check required before listing."),
    ("cloudflare-sec-eng-tech-delivery",
     "Security Engineer, Security Technology Delivery", "Cloudflare",
     "Austin, TX, USA", "Not listed", 3, EV_B,
     "3+ yrs cyber security, EDR. Only the Senior variant's Greenhouse link surfaced (7+ yrs) — do not use for the non-senior role."),
    ("tesla-sr-sec-eng-fleetnet",
     "Sr. Security Engineer, Fleetnet, Vehicle Software", "Tesla",
     "Palo Alto, CA, USA", "$172,000–$312,000", 3, EV_B,
     "Senior title — stretch if listed. 3+ yrs, published Oct 20, 2026. Tesla: 2,489 LCAs FY2025. Find on careers.tesla.com."),
    ("abbott-cyber-sec-specialist",
     "Cybersecurity Specialist", "Abbott",
     "Remote, US", "$78,000–$156,000", 2, EV_C,
     "2 yrs minimum, product security, MITRE ATT&CK, OWASP, CVSS. Title not in KD's target list; no direct jobs.abbott link found."),
    ("stryker-product-cyber-eng-mako",
     "Product Cybersecurity Engineer, Mako Robotics", "Stryker",
     "Fort Lauderdale, FL, USA (Hybrid)", "Not listed", 2, EV_C,
     "2+ yrs, pentesting/vuln scanning. Dice only; find on careers.stryker.com."),
    ("google-sec-eng-uppercase-research",
     "Security Engineer, Uppercase Research", "Google",
     "Austin, TX, USA", "$118,000–$170,000", 1, EV_B,
     "1 yr coding + 1 yr assessments/threat modeling, detection engineering, SIEM, YARA-L, LLM-based detection. 1-yr minimum is below band."),
    ("netflix-sec-eng-dr-l4",
     "Security Engineer (L4), Detection & Response", "Netflix",
     "US", "$100,000–$720,000", None, EV_C,
     "Detection/response, threat hunting, automations. Years not shown; no direct link."),
    ("rubrik-appsec-eng",
     "Application Security Engineer", "Rubrik",
     "Remote, US", "$124,200–$186,200", None, EV_C,
     "Python/Go, CI/CD, OWASP Top 10, threat modeling, AI coding-agent guardrails (prompt injection, malicious MCP server — direct KD match). No years band stated anywhere; title not in target list; Rubrik H-1B history unverified."),
    ("abnormal-embedded-detection-analyst",
     "Embedded Detection Analyst", "Abnormal Security",
     "US", "$149,200–$214,500", 2, EV_C,
     "2–5 yrs SOC/detection engineering/IR/email security, SIEM/EDR, CEH preferred; published Mar 15, 2026. Title is customer-embedded detection tuning, not a target title; no direct link (BuiltIn only)."),
    ("ping-infra-sec-eng",
     "Infrastructure Security Engineer", "ForgeRock / Ping Identity",
     "US", "$90,000–$107,000", None, EV_C,
     "SOAR (Tines), SIEM design/architecture, AWS/GCP. Years not stated; no direct link."),
    ("nvidia-insider-threat-detection-eng",
     "Insider Threat Detection Engineer", "NVIDIA",
     "Remote, US", "$168,000–$270,000", None, EV_B,
     "Mid-level, years unverified, no direct link; check NVIDIA Workday board."),
    ("dropbox-sr-sec-eng-dr",
     "Senior Security Engineer, Detection and Response", "Dropbox",
     "US", "$149,600–$202,400", 5, EV_B,
     "Senior title — stretch if listed. 5+ yrs. No direct US link verified (only the Poland variant's Greenhouse URL)."),
    ("hashicorp-product-sec-eng-programs",
     "Product Security Engineer, Programs Team", "HashiCorp",
     "Remote, US", "$159,700–$205,000", 4, EV_C,
     "'4+ years of security experience' (will consider less), Go, AWS/Azure/GCP, CI/CD shift-left, vuln management. SPONSORSHIP CONFLICT — HashiCorp-side posting shows no bar, but the IBM-hosted twin states 'IBM will not be providing visa sponsorship for this position now or in the future.' Do not list without recruiter confirmation. No direct link found."),
    # Held for a reason other than a missing link:
    ("microsoft-sec-eng-windows-sec-ii-200053674",
     "Security Engineer II, Windows Security", "Microsoft",
     "Redmond, WA, USA (Fully Remote)", "$102,100–$202,200", 2, EV_B,
     "IC3, Job ID 200053674, posted Nov 3, 2026. VERIFY it is distinct from the held IC2 entry before listing (same Nov 3 date — may be the same requisition re-leveled). Preferred qualification is literally KD's profile: 'Public track record of relevant security research, especially around vulnerability discovery.'"),
    ("stryker-staff-cyber-eng-r575538",
     "Staff Cybersecurity Engineer", "Stryker",
     "Redmond, WA, USA (Hybrid)", "$118,000–$196,600", 4, EV_C,
     "Req R575538, published Oct 22, 2026. SPONSORSHIP CONFLICT: Simplify says 'Company Historically Provides H1B Sponsorship,' but a Stryker posting states 'Must be legally authorized to work in the U.S. and not require employment-based sponsorship now or in the future.' Do NOT list until the sponsorship line on THIS posting is confirmed."),
    ("bofa-cyber-resiliency-analyst-26038363",
     "Cyber Resiliency Analyst", "Bank of America",
     "Denver, CO, USA", "Not listed", 1, EV_B,
     "1–3 yrs, Job ID 26038363. Below band — do not list without KD's word."),
]

# Closures confirmed by the deep search (mark in held_jobs.json, keep as records).
CLOSED_IDS = {
    "kiewit-cyber-sec-analyst-2026-11": "CLOSED — verified on Kiewit's own careers page ('Sorry, this position is no longer available'), Nov 15, 2026.",
    "flosports-appsec-eng-2026-11": "CLOSED — absent from FloSports' live Ashby board (19 open roles, zero security), Nov 15, 2026.",
    "flosports-sec-analyst-2026-11": "CLOSED — absent from FloSports' live Ashby board (19 open roles, zero security), Nov 15, 2026.",
    "meta-sec-detection-eng-insider-trust-3yr-2026-11": "CLOSED/SUPERSEDED — likely superseded by the live 5-yr Insider Trust variant ($147,000–$208,000, published Oct 7–8, 2026); the 3-yr mirror is dated Dec 16, 2024.",
}

# ---------------------------------------------------------------------------
# New blanket no-sponsorship employers (Section E). Tuple: (employer, detail, reason)
# Dedup runs against the existing excluded.md headings.
# ---------------------------------------------------------------------------
EXCLUDED_ADD = [
    ("Cox Enterprises", "Detection Engineer II", "Posting: 'No OPT, CPT, STEM/OPT or visa sponsorship now or in future' — verified on the posting's Workday link."),
    ("Equifax", "cyber roles", "'Does not offer immigration sponsorship' / 'not a sponsorship eligible position'."),
    ("Ford", "cyber roles", "'Visa sponsorship is not available'."),
    ("Consumers Energy", "cyber roles", "Blanket no sponsorship."),
    ("Grainger", "cyber roles", "'Not eligible for any form of sponsorship now or in the future… OPT or H1B… should not apply'."),
    ("United Airlines", "cyber roles", "Blanket no sponsorship."),
    ("Walgreens", "cyber roles", "'Will not provide employment-based visa sponsorship'."),
    ("ZS Associates", "cyber roles", "Blanket no sponsorship."),
    ("Lear", "cyber roles", "'Legally authorized… without sponsorship'."),
    ("Dow", "cyber roles", "'No visa sponsorship/support is available'."),
    ("PNC Bank", "cyber roles", "'Will not provide sponsorship… or participate in STEM OPT'."),
    ("Wells Fargo", "cyber roles", "'Not available for visa sponsorship' / 'not eligible for Visa sponsorship'."),
    ("Fiserv", "Cyber Network Engineer", "Requires 'valid and unrestricted U.S. work authorization'; Cyber Network Engineer explicitly excludes F-1/H-1B/TN."),
    ("Fidelity", "cyber roles", "'Will not provide immigration sponsorship'."),
    ("Eaton", "cyber roles", "Blanket — excludes CPT/OPT/STEM OPT/F-1 to H-1B/H-1B cap/O-1/E-3/TN."),
    ("Emerson", "cyber roles", "Blanket no sponsorship."),
    ("Kaiser Permanente", "cyber roles", "No current/future sponsorship."),
    ("Epic Systems", "cyber roles", "'Without visa sponsorship'."),
    ("Black & Veatch", "cyber roles", "'Visa Sponsorship Available: No'."),
    ("3M", "cyber roles", "Blanket no sponsorship."),
    ("GE Aerospace", "cyber roles", "Blanket no sponsorship."),
    ("Siemens Energy", "cyber roles", "Blanket no sponsorship."),
    ("Rockwell Automation", "cyber roles", "Blanket no sponsorship."),
    ("Boston Scientific", "cyber roles", "Blanket no sponsorship."),
    ("Wiz", "cyber roles", "'Does not offer visa sponsorship'."),
    ("Expel", "cyber roles", "'We do not currently sponsor immigration visas'."),
    ("Microsoft Red Team Gaming/AI", "Red Team roles", "Top Secret clearance + SCI + polygraph + US citizenship."),
    ("Okta Staff D&R Federal", "Staff Detection & Response, Federal", "US Person."),
    ("Cisco FedRAMP roles", "FedRAMP roles", "US Person."),
    ("Palo Alto Networks (selected roles)", "SOC Security Engineer and Security Engineer SOAR/XSIAM", "Posting states sponsorship 'No' on these roles (other Palo Alto roles may differ — check per posting)."),
]

# New sponsors for sponsors.csv. Columns: employer, security_h1b_filings_q4_fy2025,
# role_focus, median_wage_usd, perm_status_oct_2026, notes.
# The count column is Q4 FY2025 specifically — left blank where only a wider
# window was verified; the window is spelled out in notes.
SPONSORS_ADD = [
    ("Stellantis (FCA US LLC)", "", "Security Engineer", "", "Active",
     "238 certified H-1B LCAs Jul 2025–Jun 2026, 326 in FY2025; bulk are engineering titles, not security-specific"),
    ("Bank of America", "", "Security Engineer", "152000", "Active",
     "443 certified LCAs FY2026 Q1–Q3, 790 FY2025, median $152K"),
    ("Coinbase", "", "Security Engineer", "", "Active",
     "118 certified LCAs FY2026 Q1–Q3, 186 FY2025; 5 Information Security Engineer LCAs Jul 2025–Jun 2026"),
    ("Charles Schwab", "", "Application Security Engineer", "", "Active",
     "346 certified LCAs FY2026 Q1–Q3, 577 FY2025; 412 H-1B petitions approved FY2026 at ~99%; 27% transfers"),
    ("Kirkland & Ellis", "", "Security Engineer", "", "Active",
     "42 certified LCAs Oct 2025–Jun 2026, but 41 of 42 are Lawyers; no tech-staff LCA evidence — ask recruiter"),
    ("Circle", "", "Security Engineer", "", "Active",
     "Day-one PERM sponsorship stated on D&R postings; H-1B counts not yet verified"),
    ("Home Depot", "", "Cybersecurity Engineer", "138721", "Active",
     "218 certified LCAs Oct 2025–Jun 2026, incl. 22 Cybersecurity Sr. Engineer LCAs (median $138,721)"),
    ("Toast", "", "Security Operations Engineer", "", "Active",
     "29–31 certified LCAs FY2026 Q1–Q3; some Toast postings say 'will not sponsor' — check per posting"),
    ("Scale AI", "", "Security Engineer", "", "Active",
     "72 certified H-1B LCAs FY2026 Q1–Q3"),
    ("Rapid7", "", "Detection Engineer", "", "Active",
     "FY2025: 5 LCAs filed, 5 I-129s approved, 0 denied"),
    ("Okta", "", "Security Analyst", "", "Active",
     "FY2025: 120 LCAs, 106 I-129s approved, 0 denied"),
    ("SoFi (Social Finance)", "", "Enterprise Security Engineer", "", "Active",
     "90 LCAs FY2026, 162 I-129 petitions FY2025 (161 approved)"),
    ("Datadog", "", "Security Engineer", "", "Active",
     "H-1B counts not yet verified"),
    ("U.S. Bank", "", "Information Security Engineer", "", "Active",
     "H-1B counts not yet verified — check before listing"),
    ("Elastic", "", "Threat Detection Engineer", "", "Active",
     "H-1B counts not yet verified"),
    ("Optum / UnitedHealth Group", "", "Information Security Engineer", "", "Active",
     "Massive H-1B sponsor; counts not yet verified"),
    ("Abbott", "", "Cybersecurity Specialist", "", "Active",
     "H-1B counts not yet verified"),
    ("Stryker", "", "Cybersecurity Engineer", "", "Active",
     "Sponsorship conflict — one posting states no sponsorship; verify per posting"),
    ("Netflix", "", "Security Engineer", "", "Active",
     "H-1B counts not yet verified"),
    ("Rubrik", "", "Application Security Engineer", "", "Active",
     "H-1B history unverified"),
    ("Dropbox", "", "Security Engineer", "", "Active",
     "H-1B counts not yet verified"),
    ("HashiCorp", "", "Product Security Engineer", "", "Active",
     "Sponsorship conflict — IBM-hosted twin states no visa sponsorship; verify per posting"),
    ("Cloudflare", "", "Security Engineer", "146000", "Active",
     "120 certified LCAs FY2026 to Jun 30; Security Engineer 4 LCAs, Network Security Engineer 4, AppSec 1"),
    ("Geotab", "", "Cybersecurity Engineer", "109654", "Active",
     "8 certified LCAs FY2026 Q1–Q3, median $109,654; no security-role filings ever"),
    ("Unisys", "", "Cybersecurity Analyst", "", "Active",
     "43 LCAs filed FY2025, 32 USCIS petitions approved (5 transfers); no security-titled roles in sponsored occupations"),
]


def main():
    seed = json.loads(SEED.read_text())
    held = json.loads(HELD.read_text())
    stretch = json.loads(STRETCH_ARCH.read_text()) if STRETCH_ARCH.exists() else []
    oob = json.loads(OUT_OF_BAND.read_text()) if OUT_OF_BAND.exists() else []
    seed_ids = {j["id"] for j in seed}
    held_ids = {j["id"] for j in held}
    arch_ids = {j["id"] for j in stretch} | {j["id"] for j in oob}
    known = seed_ids | held_ids | arch_ids

    # 1. New CORE jobs -> seed (dedup).
    added, skipped = [], []
    for j in NEW_CORE:
        if j["id"] in known:
            skipped.append(j["id"])
            continue
        seed.append(j)
        known.add(j["id"])
        added.append(j["id"])
    # Unisys why_fit -> recruiter-safe (the PAY FLAG note leaked into drafts).
    for j in seed:
        if j["id"] == "unisys-cyber-sec-analyst-santa-clara-2026-10-15":
            j["why_fit"] = ("SIEM monitoring and incident response — Splunk/SIEM event triage and "
                            "investigation, matching KD's Splunk SIEM build and SOC work. 2 years asked. "
                            "Pay is $72,000–$96,000, below KD's level — listed only because the link is verified.")
            print("  Unisys why_fit rewritten (recruiter-safe)")
    SEED.write_text(json.dumps(seed, indent=2) + "\n")
    print(f"Seed: {len(seed)} jobs (+{len(added)} new core, skipped dupes: {skipped or 'none'})")

    # 2. Stretch -> archive.
    for j in NEW_STRETCH:
        if j["id"] in arch_ids:
            continue
        stretch.append({**j, "archived_reason": "stretch role (senior title) — site is CORE only (KD rule Nov 15, 2026)",
                        "archived_date": "2026-11-15",
                        "archived_rule": "KD Nov 15, 2026: site is CORE jobs only"})
        arch_ids.add(j["id"])
    STRETCH_ARCH.write_text(json.dumps(stretch, indent=2) + "\n")
    print(f"Stretch archive: {len(stretch)} jobs")

    # 3. Out of band -> archive.
    for j in OUT_OF_BAND_ADD:
        if j["id"] in arch_ids:
            continue
        oob.append({**j, "archived_reason": "6+ years of general experience asked — out of the 2–5 yr band (KD rule Nov 15, 2026)",
                    "archived_date": "2026-11-15"})
        arch_ids.add(j["id"])
    OUT_OF_BAND.write_text(json.dumps(oob, indent=2) + "\n")
    print(f"Out-of-band archive: {len(oob)} jobs")

    # 4. Link-pending -> held.
    held_added = 0
    for (hid, title, employer, location, salary, years, ev, note) in HELD_ADD:
        if hid in held_ids:
            continue
        held.append({
            "id": hid, "title": title, "employer": employer, "location": location,
            "salary": salary, "years_required": years, "url": "",
            "sponsorship_evidence": ev, "sponsorship_note": note, "why_fit": note,
            "keywords_matched": [], "posted": None, "closes": None,
            "apply_link_type": "pending", "also_at": None,
            "held_reason": "Direct apply link not yet extracted — needs a live board lookup.",
            "last_checked": "2026-11-15",
        })
        held_ids.add(hid)
        held_added += 1
    # 5. Closures.
    closed = []
    for h in held:
        if h["id"] in CLOSED_IDS:
            h["held_reason"] = CLOSED_IDS[h["id"]]
            h["last_checked"] = "2026-11-15"
            closed.append(h["id"])
    HELD.write_text(json.dumps(held, indent=2) + "\n")
    print(f"Held: {len(held)} entries (+{held_added} link-pending; closed marked: {closed or 'none'})")

    # 6. excluded.md — append, dedup by employer heading.
    text = EXCLUDED.read_text()
    existing = {m.group(1).strip().lower() for m in re.finditer(r"^## \d+\. ([^\n—]+)", text, re.M)}
    nums = [int(m.group(1)) for m in re.finditer(r"^## (\d+)\.", text, re.M)]
    n = max(nums) if nums else 0
    added_ex = 0
    with EXCLUDED.open("a") as fh:
        for employer, detail, reason in EXCLUDED_ADD:
            if employer.lower() in existing:
                continue
            n += 1
            fh.write(f"\n## {n}. {employer} — {detail}\n- Why dropped: {reason}\n")
            added_ex += 1
    print(f"excluded.md: +{added_ex} entries (now {n} total)")

    # 7. sponsors.csv — append via csv module; fix the WRITER/Qatalog row.
    with SPONSORS.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
        fields = ["employer", "security_h1b_filings_q4_fy2025", "role_focus",
                  "median_wage_usd", "perm_status_oct_2026", "notes"]
    have = {r["employer"].strip().lower() for r in rows}
    fixed_writer = False
    for r in rows:
        if r["employer"].strip().lower() == "writer (qatalog inc)":
            r["employer"] = "Writer, Inc."
            r["notes"] = "4 H-1B + 1 PERM in the 2025–26 window. NOT formerly Qatalog Inc — Qatalog is a separate company (acquired by ClickUp Nov 2025); its 2024 LCAs are not WRITER's."
            fixed_writer = True
    added_sp = 0
    for row in SPONSORS_ADD:
        if row[0].strip().lower() in have:
            continue
        rows.append(dict(zip(fields, row)))
        have.add(row[0].strip().lower())
        added_sp += 1
    with SPONSORS.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"sponsors.csv: +{added_sp} sponsors (now {len(rows)} rows); WRITER row fixed: {fixed_writer}")


if __name__ == "__main__":
    main()
