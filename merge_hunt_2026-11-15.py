#!/usr/bin/env python3
"""merge_hunt_2026-11-15.py — Nov 15, 2026 evening.

Merges the live-browser link hunt (9 roles, 3 FOUND, 6 NOT FOUND):
- 3 FOUND jobs -> jobs_seed.json (Google AI Threat Defense, EY STS Endpoint,
  Salesforce Red Team JR332456), and REMOVED from held_jobs.json.
- 6 NOT FOUND roles -> held_jobs.json entries updated with the Nov 15 outcome
  (Salesforce JR323795 + MongoDB + Circle x2: likely closed/filled, not on the
  live board; Instacart: board unreachable, not a closed verdict; Palo Alto:
  not listed; board moved careers.paloaltonetworks.com -> jobs.paloaltonetworks.com).

Run: python3 merge_hunt_2026-11-15.py && python3 find_jobs.py && python3 build_site.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
SEED = ROOT / "jobs_seed.json"
HELD = ROOT / "held_jobs.json"

EV_B = "B_sponsor_history"


def job(job_id, title, employer, location, salary, years, url, ev, note, why, kws, posted=None, closes=None):
    return {
        "id": job_id, "title": title, "employer": employer, "location": location,
        "salary": salary, "years_required": years, "url": url,
        "sponsorship_evidence": ev, "sponsorship_note": note, "why_fit": why,
        "keywords_matched": kws, "posted": posted, "closes": closes,
        "apply_link_type": "direct", "also_at": None,
    }


FOUND = [
    job("google-ai-threat-defense-eng-i",
        "AI Threat Defense Engineer I, Google Cloud Consulting", "Google",
        "Austin, TX / Atlanta, GA / Chicago, IL / New York, NY / San Francisco, CA / Sunnyvale, CA, USA",
        "$127,000–$182,000", 3,
        "https://www.google.com/about/careers/applications/jobs/results/111590144095462086-ai-threat-defense-engineer-i-google-cloud-consulting-professional-services",
        EV_B,
        "B — Google LLC: 20,982 DOL filings. Confirm per role.",
        "AI threat defense for Google Cloud Consulting, FedRAMP/PCI/HIPAA, Python — KD's AI-security governance differentiator (Claude/OpenAI/Gemini/OpenClaw) plus detection engineering. 3 years asked. Application window reported open until at least Nov 18, 2026 (no closing date shown on the posting — verify).",
        ["Python"]),
    job("ey-sts-endpoint-sec-eng-1746330",
        "STS Endpoint Security Engineer", "EY",
        "Hoboken, NJ, USA (Anywhere in Country)", "$91,100–$170,400", 4,
        "https://careers.ey.com/ey/job/Hoboken-STS-Endpoint-Security-Engineer-NJ-07030/1444844333/",
        EV_B,
        "B — EY is the #1 security sponsor (83 security H-1B filings Q4 FY2025). Confirm per role.",
        "Endpoint/data security engineering, Linux/Mac/Windows, Azure/AWS/GCP — KD's EDR + endpoint + cloud stack. 4+ years InfoSec / 3+ years engineering asked. Posted Nov 4, 2026.",
        ["EDR", "Azure"], posted="2026-11-04"),
    job("salesforce-offensive-sec-eng-redteam-jr332456",
        "Offensive Security Engineer - Red Team", "Salesforce",
        "San Francisco, CA / Bellevue, WA, USA (Hybrid)", "$117,200–$223,900", 3,
        "https://salesforce.wd12.myworkdayjobs.com/en-US/External_Career_Site/details/Offensive-Security-Engineer---Red-Team_JR332456",
        EV_B,
        "B — Salesforce: 8,227 certified LCAs. Confirm per role.",
        "3+ years hands-on red teaming, penetration testing and offensive security; purple team with Detection Engineering; AI-abuse testing on Agentforce — KD's VAPT + detection + AI-security mix. 3+ years asked.",
        ["VAPT", "Detection Engineering"]),
]

# Held entries to REMOVE (now listed) and to UPDATE (not found on the live board).
REMOVE_FROM_HELD = {
    "google-ai-threat-defense-eng-i",
    "ey-sts-endpoint-sec-eng-1746330",
    "salesforce-offensive-sec-eng-redteam",
}

HELD_UPDATES = {
    "salesforce-endpoint-sec-mts-jr323795":
        "NOT FOUND on the live Salesforce Workday board Nov 15, 2026 (JR323795 returns 0 jobs on two attempts; broader 'Endpoint Security' searches also empty) — likely closed/filled. Re-check in a few days before concluding.",
    "mongodb-product-sec-eng-3263210599":
        "NOT FOUND Nov 15, 2026: MongoDB's Greenhouse board redirects to mongodb.com/company/careers; the live board lists only 'Senior Product Security Engineer, Assessments' — the plain Product Security Engineer / Req 3263210599 is not listed. Likely closed/filled or the req changed.",
    "circle-sec-eng-dr":
        "NOT FOUND Nov 15, 2026: Circle's Greenhouse board is inactive ('no longer active'); Circle's live careers site lists no Security Engineer II, Detection and Response (Remote US) — only a Principal D&R role in Ireland. Likely closed/filled.",
    "circle-sr-sec-eng-dr":
        "NOT FOUND Nov 15, 2026: Circle's Greenhouse board is inactive; Circle's live careers site lists no Senior Security Engineer, Detection and Response (Remote US) — only a Principal D&R role in Ireland. Likely closed/filled.",
    "instacart-detection-eng-ii":
        "Board unreachable Nov 15, 2026 (instacart.careers fails ERR_CONNECTION_CLOSED on every attempt) — NOT a closed verdict; the role could not be verified. Re-check.",
    "paloalto-staff-sec-eng-soc-ai-ml":
        "NOT FOUND Nov 15, 2026: not listed on jobs.paloaltonetworks.com after a thorough search (Staff Security Engineer, SOC, AI/ML Specialist). Likely closed/filled. Note: the board moved — careers.paloaltonetworks.com no longer resolves; the board is now jobs.paloaltonetworks.com.",
}


def main():
    seed = json.loads(SEED.read_text())
    held = json.loads(HELD.read_text())
    seed_ids = {j["id"] for j in seed}

    added = []
    for j in FOUND:
        if j["id"] in seed_ids:
            print(f"  skip (already in seed): {j['id']}")
            continue
        seed.append(j)
        seed_ids.add(j["id"])
        added.append(j["id"])
    SEED.write_text(json.dumps(seed, indent=2) + "\n")
    print(f"Seed: {len(seed)} jobs (+{len(added)}: {added})")

    kept, removed, updated = [], [], []
    for h in held:
        if h["id"] in REMOVE_FROM_HELD:
            removed.append(h["id"])
            continue
        if h["id"] in HELD_UPDATES:
            h["held_reason"] = HELD_UPDATES[h["id"]]
            h["last_checked"] = "2026-11-15"
            updated.append(h["id"])
        kept.append(h)
    HELD.write_text(json.dumps(kept, indent=2) + "\n")
    print(f"Held: {len(kept)} entries (removed listed: {removed}; updated not-found: {updated})")


if __name__ == "__main__":
    main()
