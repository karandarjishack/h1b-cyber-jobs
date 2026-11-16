# Research evidence contract

This folder holds human/ChatGPT-reviewed research, separate from automated public ATS discoveries.

`latest.json` schema:
```json
{
  "generated_at": "2026-11-16T08:00:00-05:00",
  "window": {"from": "2026-11-10", "to": "2026-11-16"},
  "jobs": [
    {
      "id": "company-requisition-123",
      "employer": "Company",
      "title": "Security Engineer",
      "requisition_id": "123",
      "department": "Security Operations",
      "location": "Remote, US (Michigan eligible verified)",
      "posted": "2026-11-16",
      "url": "https://company.example/careers/job/123",
      "salary": "$120,000–$160,000",
      "years_required": 3,
      "fit_score": 83,
      "why_fit": "Concrete technical alignment",
      "keywords_matched": ["EDR", "Splunk"],
      "sponsorship_evidence": "B_sponsor_history",
      "sponsorship_note": "FY and legal entity, source URL, and explicit role uncertainty",
      "sponsorship_source": "https://official-source.example",
      "perm_status": "Unknown or evidence with dates",
      "review_reasons": ["Role-specific H-1B transfer not confirmed"],
      "hiring_manager_name": null,
      "hiring_manager_confidence": "Not identified",
      "hiring_manager_linkedin": null,
      "hiring_post_url": null,
      "hiring_manager_email": null
    }
  ]
}
```

Rules: publish only genuinely new 7-calendar-day employer/ATS openings with verified direct URLs; all roles are full-time, non-senior, generally 2–5 years, pay-band maximum under $250k, and relevant to KD's cybersecurity resume. Published date must be sourced from original employer; unknown-date jobs go to private research, not Latest. Sort newest to oldest, then fit. A = explicit posting support, B = recent certified cyber-title LCA, C = unknown/other employer history; C is only a pending research lead. A and B do NOT establish approval for the exact H-1B transfer. Store precise filing coverage dates and evidence.

Confirmed hiring-manager identity requires a direct public link to the specific vacancy or reporting responsibility. Strong match or potential contact must be labeled accurately. Never generate email addresses. Neither the dashboard nor the research agent sends email or applies.

Use the same permanent `id` and canonical employer application URL when updating a job. Preserve source dates and do not silently overwrite evidence. Review and reconcile against `jobs.json`, `docs/history.json`, and `docs/daily.json` before publishing. Public GitHub Pages exposes all of this content; do not publish private communications or personal application notes.

## Evidence-reviewed corrections (2026-11-16)

The daily research layer may override ATS-extraction gaps using *verified public employer job postings*. Use `latest.json` for corrections to a still-eligible job: company, requisition, salary, office attendance, permitted residence, immigration application wording and source links. The reviewed job must preserve the automatic `id` so the dashboard merges the same opportunity instead of making a duplicate.

`exclusions.json` stores exact company + role + requisition decisions, each with a public evidence URL and reason, for opportunities outside configured conditions. The raw historic catalog remains intact; excluded roles disappear from Latest and the current HTML report. Exclusions do **not** mean an employer universally refuses sponsorship.

Neither source may contain fabricated hiring contacts or implied H-1B guarantees. Public forms asking whether a candidate needs sponsorship do not prove an offer of sponsorship for that position. Recheck exclusion entries if employers modify postings or compensation.
