#!/usr/bin/env python3
"""Unit and pipeline tests; no external network or paid services."""
import csv
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import research_engine as e

DAY = date(2026, 11, 16)
BASE = {
    "company": "Example Security Inc",
    "title": "Detection Engineer",
    "id": "TEST-123",
    "location": "Remote, United States",
    "posted": "2026-11-14T09:00:00Z",
    "date_quality": "greenhouse_first_published",
    "description": ("Full-time. Required: 3+ years of experience with "
                    "Microsoft Defender, CrowdStrike Falcon, SIEM and detection engineering."),
    "url": "https://job-boards.greenhouse.io/examplesecurity/jobs/123",
    "employment": "FullTime",
    "salary": "$130,000–$180,000",
    "department": "Security Operations",
}
SPONSOR_ROWS = [{"employer": "Amazon.com Services LLC", "security_h1b_filings_q4_fy2025": "59"}]

def candidate(**updates):
    return {**BASE, **updates}

class EngineTests(unittest.TestCase):
    def test_date_and_strict_window(self):
        self.assertEqual(e.date_only("2026-11-14T09:00:00Z"), date(2026, 11, 14))
        self.assertEqual(e.date_only(None), None)
        self.assertEqual(e.workday_relative("Posted Yesterday", DAY), date(2026, 11, 15))
        self.assertEqual(e.workday_relative("Posted 8 Days Ago", DAY), date(2026, 11, 8))
        self.assertEqual(e.workday_relative("Posted 30+ Days Ago", DAY), None)
        self.assertEqual(e.screen(candidate(posted="2026-11-09"), "greenhouse", "x", [], DAY)[1], "outside_seven_day_window")
        self.assertIsNone(e.screen(candidate(posted="2026-11-10"), "greenhouse", "x", [], DAY)[1])

    def test_core_title_and_exclusions(self):
        self.assertTrue(e.is_cyber("Security Engineer, Detection"))
        self.assertFalse(e.is_cyber("Senior Security Engineer"))
        self.assertFalse(e.is_cyber("Director of Information Security"))
        self.assertFalse(e.is_cyber("Software Developer"))
        self.assertFalse(e.is_cyber("Specialist Sales, Cloud Security"))
        self.assertFalse(e.is_cyber("Security Engineer, RF and Technical Surveillance Countermeasures"))
        self.assertFalse(e.is_cyber("M&A Security Integration Engineer - PMTS"))
        self.assertFalse(e.is_cyber("Platform & Security Sales Specialist"))
        self.assertEqual(e.screen(candidate(title="Senior Detection Engineer"),"greenhouse","x",[],DAY)[1], "not_core_cyber_title")
        self.assertEqual(e.screen(candidate(description=BASE["description"]+" No visa sponsorship."),"greenhouse","x",[],DAY)[1],
                         "explicit_no_sponsorship_or_citizenship_requirement")
        self.assertEqual(e.screen(candidate(description=BASE["description"]+" US citizenship required."),"greenhouse","x",[],DAY)[1],
                         "explicit_no_sponsorship_or_citizenship_requirement")
        self.assertEqual(e.screen(candidate(location="London, United Kingdom"),"greenhouse","x",[],DAY)[1],"not_eligible_US_location")
        self.assertEqual(e.screen(candidate(employment="Contract"),"greenhouse","x",[],DAY)[1],"not_full_time_direct_hire")

    def test_experience_salary_and_reposting(self):
        self.assertEqual(e.required_years("3+ years of experience, 6 years of prior management experience"),3)
        self.assertEqual(e.salary_max("$99,000 - $249,000 per year"),249000)
        self.assertEqual(e.salary_max("$230K to $270K"),270000)
        self.assertEqual(e.screen(candidate(salary="$200,000 - $280,000"),"greenhouse","x",[],DAY)[1],"salary_above_user_cap")
        self.assertEqual(e.screen(candidate(description=BASE["description"].replace("3+","7+")),"greenhouse","x",[],DAY)[1],"six_plus_years_experience")
        job,_=e.screen(candidate(date_quality="ashby_last_published"),"ashby","x",[],DAY)
        self.assertTrue(any("Original job posting date" in v for v in job["review_reasons"]))
        job,_=e.screen(candidate(description="Full-time; no years specified."),"greenhouse","x",[],DAY)
        self.assertTrue(any("experience" in v.lower() for v in job["review_reasons"]))

    def test_visa_evidence_not_overclaimed(self):
        a,_=e.screen(candidate(description=BASE["description"]+" We provide visa sponsorship."),"greenhouse","x",[],DAY)
        self.assertEqual(a["sponsorship_evidence"],"A_verified_posting")
        self.assertEqual(a["sponsorship_source"],BASE["url"])
        b,_=e.screen(candidate(company="Amazon"),"greenhouse","x",SPONSOR_ROWS,DAY)
        self.assertEqual(b["sponsorship_evidence"],"B_sponsor_history")
        self.assertTrue(any("official filing citation" in v for v in b["review_reasons"]))
        c,_=e.screen(candidate(company="JRM Construction Management"),"greenhouse","x",SPONSOR_ROWS,DAY)
        self.assertEqual(c["sponsorship_evidence"],"C_ask_recruiter")
        self.assertTrue(c["review_reasons"])
        self.assertEqual(c["hiring_manager_name"],None)
        self.assertEqual(c["hiring_manager_email"],None)
        self.assertEqual(e.sponsor_lookup("Am",SPONSOR_ROWS),None)

    def test_urls_and_keyword_boundary(self):
        self.assertFalse(e.direct_url("http://boards.greenhouse.io/foo"))
        self.assertFalse(e.direct_url("https://jobs.indeed.com/foo"))
        self.assertTrue(e.direct_url("https://jobs.lever.co/coalfire/example"))
        self.assertEqual(e.keyword_hits("EDR Engineer","editorial review").count("EDR"),1)
        self.assertNotIn("EDR",e.keyword_hits("Analyst","editorial review"))

    def test_greenhouse_retrieves_first_published_from_detail(self):
        listing={"jobs":[{"id":123,"title":"Detection Engineer","location":{"name":"Remote, US"},
                  "absolute_url":BASE["url"],"content":"Full-time 3+ years of experience"}]}
        detail={"id":123,"title":"Detection Engineer","location":{"name":"Remote, US"},
                "first_published":"2026-11-14T10:30:00Z","content":"Full-time 3+ years of experience",
                "absolute_url":BASE["url"]}
        with patch.object(e,"get_json",side_effect=[listing,detail]) as fetch:
            _,jobs,total=e.greenhouse("examplesecurity")
        self.assertEqual(total,1)
        self.assertEqual(len(jobs),1)
        self.assertEqual(jobs[0]["posted"],"2026-11-14T10:30:00Z")
        self.assertEqual(jobs[0]["date_quality"],"greenhouse_first_published")
        self.assertEqual(fetch.call_count,2)

    def test_ashby_published_at_is_not_original_date(self):
        board={"jobs":[{"title":"Detection Engineer","id":"a","location":"Remote, US",
                         "isListed":True,"employmentType":"FullTime","publishedAt":"2026-11-14",
                         "descriptionPlain":BASE["description"],"applyUrl":"https://jobs.ashbyhq.com/example/a/application",
                         "compensation":{"scrapeableCompensationSalarySummary":"$150K–$200K"}}]}
        with patch.object(e,"get_json",return_value=board):
            _,rows,_=e.ashby("example")
        self.assertEqual(rows[0]["date_quality"],"ashby_last_published")
        self.assertEqual(rows[0]["salary"],"$150K–$200K")

    def test_lever_uses_created_at(self):
        board=[{"text":"Detection Engineer","id":"a","createdAt":1794650400000,
                "categories":{"location":"Remote - US","commitment":"Full-time"},
                "descriptionPlain":BASE["description"],
                "applyUrl":"https://jobs.lever.co/test/a/apply"}]
        with patch.object(e,"get_json",return_value=board):
            _,rows,_=e.lever("test")
        self.assertEqual(rows[0]["date_quality"],"lever_created_at")
        self.assertTrue(rows[0]["posted"].startswith("2026-"))

    def test_workday_enrichment_and_unverified_relative_date(self):
        data=[{"jobPostings":[{"title":"Security Engineer","externalPath":"/job/City/Title_R10",
                               "locationsText":"Remote, US","postedOn":"Posted 3 Days Ago"}],"total":1},
              {"jobPostings":[],"total":0},{"jobPostings":[],"total":0},
              {"jobPostingInfo":{"jobReqId":"R10","jobDescription":BASE["description"],
                                 "timeType":"Full-time","startDate":"2026-11-12"}}]
        with patch.object(e,"get_json",side_effect=data):
            _,jobs,_=e.workday("example.wd5.myworkdayjobs.com|example|Careers")
        self.assertEqual(len(jobs),1)
        self.assertEqual(jobs[0]["id"],"R10")
        self.assertEqual(jobs[0]["date_quality"],"workday_start_date_unverified")

    def test_board_catalog_from_actual_repository(self):
        sets=e.board_catalog()
        self.assertIn("greenhouse",sets)
        self.assertIn("workday",sets)
        self.assertTrue(any("crowdstrike.wd5.myworkdayjobs.com" in x for x in sets["workday"]))
        self.assertIn("geotab",sets["greenhouse"])
        self.assertIn("spotify",sets["lever"])

    def test_full_offline_pipeline_and_outage_guard(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with (root/"sponsors.csv").open("w",newline="",encoding="utf8") as handle:
                writer=csv.DictWriter(handle,fieldnames=["employer","security_h1b_filings_q4_fy2025"])
                writer.writeheader();writer.writerows(SPONSOR_ROWS)
            one=candidate(company="Example Security Inc",description=BASE["description"]+" We offer visa sponsorship.")
            second=candidate(company="Other Inc",id="456",title="Security Analyst",url="https://jobs.lever.co/other/456")
            with patch.object(e,"ROOT",root),patch.object(e,"board_catalog",return_value={"greenhouse":[str(i) for i in range(9)]}),patch.object(e,"fetch_board",return_value=("https://example.org", [one,second],2)):
                payload=e.main(now=DAY)
            self.assertEqual(payload["quality"]["successful_sources"],9)
            self.assertEqual(len(payload["verified_history"]),1)
            self.assertEqual(len(payload["research_pending"]),1)
            self.assertEqual(json.loads((root/"docs/daily.json").read_text())["window"]["to"],"2026-11-16")
            self.assertTrue((root/"docs/reports/2026-11-16.json").exists())
            with patch.object(e,"ROOT",root),patch.object(e,"board_catalog",return_value={"greenhouse":["dead"]}),patch.object(e,"fetch_board",side_effect=RuntimeError("429")):
                with self.assertRaisesRegex(RuntimeError,"Source degradation"):
                    e.main(now=DAY)
            self.assertTrue((root/"docs/daily.json").exists(),"Outage must preserve previous report")

if __name__=="__main__":
    unittest.main()
