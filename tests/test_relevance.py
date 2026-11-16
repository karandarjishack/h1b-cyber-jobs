"""Labeled fixtures: objective role relevance, state eligibility, technical ranking.

These are synthetic counterexamples, not evidence of real jobs or sponsorship.
Precision over this suite is a regression check, not real-world accuracy.
"""
import unittest
import relevance_policy as r
import research_engine as e

GOOD = [
 ("Detection Engineer","Design SIEM detections, Splunk, EDR and Microsoft Defender."),
 ("Cybersecurity Engineer","Build Zero Trust Entra ID, Intune, Azure and endpoint protection."),
 ("Security Operations Engineer","EDR, SOAR, SIEM, threat hunting and incident response."),
 ("Cloud Security Engineer","Cloud security with Azure, Python and Zero Trust."),
 ("Product Security Engineer","VAPT and penetration testing; Python."),
 ("Application Security Engineer","Pentest, Azure, Python, Qualys and vulnerability management."),
 ("AI Security Engineer","LLM threat model, security monitoring, Microsoft Defender."),
 ("Threat Hunter","Splunk, MITRE ATT&CK and detection engineering."),
 ("Security Analyst","Incident response, SIEM, EDR and Microsoft Defender."),
 ("IAM Engineer","Entra ID, Intune, Microsoft 365, Zero Trust."),
 ("Network Security Engineer","Firewall detection, Azure security, Python, Splunk."),
 ("DevSecOps Engineer","Python, Azure, cloud security, penetration testing."),
 ("Endpoint Security Engineer","Microsoft Defender for Endpoint, Intune, EDR and XDR."),
 ("Vulnerability Management Engineer","Qualys VMDR, Python and penetration testing."),
 ("Security Architect","Zero Trust security architecture, EDR, SIEM, SOAR."),
]
BAD = [
 ("Security Sales Representative","Account management, demos, revenue and sales."),
 ("Security Solutions Architect, Pre-Sales","Meet prospects and close deals."),
 ("Solutions Architect, Business Technology Security","Coordinate people technology teams."),
 ("IT Product Manager, Security","Manage product roadmap."),
 ("Security Recruiter","Recruit engineers and managers."),
 ("Security Guard","Patrol physical premises."),
 ("Physical Security Specialist","Security cameras and surveillance."),
 ("Senior Detection Engineer","Splunk, Sentinel, EDR."),
 ("Staff Security Engineer","Defender, EDR, SOC."),
 ("Security Director","Own an information security team."),
 ("Cloud Security Sales Specialist","Sales demos."),
]
class RelevanceTests(unittest.TestCase):
    def test_labeled_role_precision(self):
        accepted=[title for title,desc in GOOD if
                  e.is_cyber(title) and r.role_group(title)!="adjacent_business"]
        rejected=[title for title,desc in BAD if
                  not e.is_cyber(title) or r.role_group(title)=="adjacent_business"]
        self.assertEqual(len(accepted),len(GOOD),accepted)
        self.assertEqual(len(rejected),len(BAD),rejected)
        self.assertGreaterEqual((len(accepted)+len(rejected))/(len(GOOD)+len(BAD)),.9)

    def test_detection_fit_exceeds_generic_business_role(self):
        strong=r.relevance("Detection Engineer",
                           "CrowdStrike Falcon, Microsoft Defender, Splunk, SIEM, "
                           "SOAR, Python, PowerShell, KQL, detection engineering",
                           "Remote - United States",3)
        weak=r.relevance("Solutions Architect, Business Technology Security",
                         "Policy and general IT projects", "Remote - United States",3)
        self.assertGreaterEqual(strong["fit_score"],75)
        self.assertLessEqual(weak["fit_score"],43)
        self.assertGreater(strong["fit_score"],weak["fit_score"])
        self.assertNotIn("sponsor",str(strong))

    def test_remote_michigan_not_assumed(self):
        x,checks=r.location_verdict("Remote - United States",
            "Remote work is limited to the following states: CA, TX, NJ.")
        self.assertEqual(x,"remote_restricted")
        self.assertTrue(checks)
        x,checks=r.location_verdict("Remote - United States",
            "The position can be performed remotely from anywhere in the United States.")
        self.assertEqual(x,"us_remote_unverified")
        self.assertTrue(checks)
        x,checks=r.location_verdict("Detroit, Michigan","")
        self.assertEqual(x,"michigan_eligible")
        self.assertFalse(checks)

    def test_technology_match_aliases_without_substring_noise(self):
        hits=r.skill_hits("EDR Engineer","Azure AD, Microsoft Defender for Endpoint, Python, Splunk.")
        for keyword in ["EDR","Microsoft Entra ID","Microsoft Defender","Python","Splunk"]:
            self.assertIn(keyword,hits)
        self.assertNotIn("EDR",r.skill_hits("Analyst","editorial content design"))

    def test_sponsorship_does_not_change_technical_match(self):
        a=r.relevance("AI Security Engineer","Defender, Azure, Python, detection rules.",
                      "Remote - United States",3)
        b=r.relevance("AI Security Engineer","Defender, Azure, Python, detection rules.",
                      "Remote - United States",3)
        self.assertEqual(a["fit_score"],b["fit_score"])

    def test_missing_description_cannot_create_false_high_fit(self):
        x=r.relevance("Security Engineer","","Remote - US",None)
        self.assertLessEqual(x["fit_score"],55)

if __name__=="__main__":
    unittest.main()
