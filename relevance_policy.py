"""Deterministic relevance policy for a cybersecurity architect's real experience.

Score is *technical match*, not odds of interview or immigration approval.
No external APIs or model inference required. Sensitive immigration evidence is
tracked separately from relevance so unverified sponsors cannot inflate fit.
"""
from __future__ import annotations
import re

# Strong IC cyber engineering titles; title specificity is worth more than
# broad textual mentions of "security" buried in a business role.
ROLE_PATTERNS = {
    "detection_response": r"\b(?:detection engineer|threat hunt(?:er|ing)|incident response|incident responder|"
                          r"security operations engineer|soc engineer|edr|xdr|digital forensic|malware analy)",
    "security_engineering": r"\b(?:cybersecurity engineer|cyber security engineer|security engineer|"
                            r"information security engineer|enterprise security engineer|"
                            r"endpoint security|network security engineer|security architect)",
    "cloud_iam": r"\b(?:cloud security|identity security|identity and access|iam engineer|"
                 r"zero trust|azure security|aws security)",
    "offensive_appsec": r"\b(?:application security|appsec|product security|"
                        r"penetration test|pentest|red team|vulnerability management|"
                        r"offensive security|devsecops)",
    "ai_security": r"\b(?:ai security|llm security|machine learning security|"
                   r"security for ai|genai security|agent security)",
    "security_analyst": r"\b(?:cybersecurity analyst|security analyst|information security analyst|"
                        r"soc analyst|security specialist|threat intelligence)",
}
BUSINESS_ROLE = re.compile(
    r"\b(?:solutions? architect|solutions? consultant|sales engineer|"
    r"product manager|program manager|technical account manager|"
    r"customer success|business technology|compliance auditor|"
    r"physical security|governance risk and compliance manager)\b", re.I)
SECURITY_CONTEXT = re.compile(r"\b(?:cyber|security|endpoint|identity|zero trust|iam|vulnerabilit|pentest|mitre|cloud|edr|siem|soar)\b", re.I)
HARD_CORE_SKILLS = {
    "CrowdStrike Falcon": ("crowdstrike", "falcon"),
    "Microsoft Defender": ("microsoft defender", "defender for endpoint", "mde", "defender xdr"),
    "Splunk": ("splunk",),
    "Microsoft Sentinel": ("microsoft sentinel", "azure sentinel"),
    "Qualys VMDR": ("qualys", "vmdr"),
    "Microsoft Intune": ("intune",),
    "Microsoft Entra ID": ("entra", "azure ad", "azure active directory"),
    "Microsoft 365": ("microsoft 365", "m365", "office 365"),
    "Azure": ("azure",),
    "Zero Trust": ("zero trust",),
    "Detection Engineering": ("detection engineering", "detection engineer", "detection rule", "detection logic"),
    "SIEM": ("siem", "security information and event management"),
    "SOAR": ("soar", "security orchestration"),
    "EDR": ("edr", "endpoint detection and response"),
    "XDR": ("xdr", "extended detection and response"),
    "VAPT": ("vapt", "vulnerability assessment", "penetration testing", "pentest"),
    "MITRE ATT&CK": ("mitre", "att&ck"),
    "KQL": ("kql", "kusto"),
    "Python": ("python",),
    "PowerShell": ("powershell",),
    # Domain capabilities verified in the user's security-architecture and
    # incident-response background. These are not vendor certifications.
    "Incident Response": ("incident response", "incident investigation", "incident remediation"),
    "Identity Security": ("saml", "sso", "single sign-on", "authentication", "authorization", "identity protection"),
    "Application Security": ("application security", "appsec", "product security", "secure development", "threat modeling", "threat modelling"),
    "AI Security": ("ai security", "llm security", "ai-powered detection", "ai agents", "agentic security"),
    "Vulnerability Management": ("vulnerability management", "vulnerability analysis", "cve", "vulnerability triage"),
    "Cloud Security": ("cloud security", "cloud infrastructure security"),
    "Digital Forensics": ("digital forensic", "forensic investigation"),
    "Threat Hunting": ("threat hunting", "threat hunt"),
    "Security Architecture": ("security architecture", "architecture review", "security assessments"),
}
ROLE_PREFERENCES = {
    "detection_response": 39, "security_engineering": 36,
    "cloud_iam": 33, "offensive_appsec": 35, "ai_security": 36,
    "security_analyst": 27,
}
MI = re.compile(r"\b(?:michigan|detroit|troy[, ]+mi|mi,?\s*usa)\b", re.I)
CHICAGO = re.compile(r"\b(?:chicago|illinois)\b", re.I)
US_REMOTE = re.compile(r"\b(?:remote)\b", re.I)
RESTRICTED_REMOTE = re.compile(
    r"(?:remote\s+only\s+in|resid(?:e|ing|ency)\s+in|must\s+(?:be|live|reside)\s+in|"
    r"remote\s+(?:from|within)\s+(?:the\s+)?(?:following|these)\s+states?|"
    r"remote\s+work\s+(?:is\s+)?limited\s+to|not\s+(?:available|eligible)\s+in\s+michigan)",
    re.I)
HYBRID = re.compile(r"\b(?:hybrid|on.?site|in.?office)\b",re.I)


def role_group(title):
    if BUSINESS_ROLE.search(title or ""):
        return "adjacent_business"
    for name in ("ai_security","detection_response","offensive_appsec","cloud_iam",
                 "security_engineering","security_analyst"):
        if re.search(ROLE_PATTERNS[name], title or "", re.I):
            return name
    return "adjacent_other" if SECURITY_CONTEXT.search(title or "") else "unrelated"


def skill_hits(title, description):
    # Avoid counting employer tech stacks as proof the candidate knows them.
    blob = (title or "") + " " + (description or "")
    found = []
    for skill, aliases in HARD_CORE_SKILLS.items():
        if any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", blob,re.I)
               for alias in aliases):
            found.append(skill)
    return found


def location_verdict(location, description):
    """Conservative result; no country-only assumption of Michigan eligibility."""
    loc=str(location or "")
    desc=str(description or "")
    if MI.search(loc):
        return "michigan_eligible", []
    if CHICAGO.search(loc):
        return "chicago_relocation", ["Chicago-based position; Michigan residence / relocation expectations to confirm"]
    if US_REMOTE.search(loc):
        # A state whitelist may exclude Michigan. Explicit anywhere-in-US wording
        # can qualify, but any state restriction overrides it.
        if RESTRICTED_REMOTE.search(desc) or RESTRICTED_REMOTE.search(loc):
            return "remote_restricted", ["Remote-state residency restriction requires Michigan eligibility confirmation"]
        if re.search(r"(?:anywhere|any location|all states)\s+(?:within|across|in|throughout)\s+(?:the\s+)?(?:united states|usa|u\.s\.)",desc,re.I):
            return "us_remote_confirmed", []
        if re.search(r"\b(?:united states|u\.?s\.?a?\.?|usa)\b",loc,re.I):
            return "us_remote_unverified", ["Confirm Michigan is permitted for this US-remote position"]
        return "remote_unverified", ["Confirm remote work accepts Michigan and US-based employees"]
    if HYBRID.search(loc):
        return "hybrid_relocation", ["Hybrid attendance / relocation requirements need confirmation"]
    return "location_pending", ["Worksite and Michigan eligibility not confirmed"]


def relevance(title, description, location, experience_years):
    group = role_group(title)
    skills = skill_hits(title, description)
    verdict, location_flags = location_verdict(location, description)
    base = ROLE_PREFERENCES.get(group, 0)
    # 35 points from technical evidence, increasing with independent match breadth.
    skill_points = min(35, round(35*len(skills)/8))
    # More than 5 years is excluded in the parent engine; missing years is uncertain.
    years_points = 15 if experience_years in (2,3,4,5) else 10 if experience_years in (0,1) else 0
    loc_points = {"michigan_eligible":11, "chicago_relocation":8,
                  "us_remote_confirmed":11, "us_remote_unverified":8, "remote_unverified":5,
                  "remote_restricted":2, "hybrid_relocation":3,
                  "location_pending":0}.get(verdict,0)
    score = max(0,min(100,base+skill_points+years_points+loc_points))
    if group.startswith("adjacent") or group=="unrelated":
        score=min(score,43)
    if len(skills)<2 and group!="detection_response":
        score=min(score,64)
    if not description:
        score=min(score,55)
    return {
        "fit_score":score,"role_family":group,"keywords_matched":skills,
        "location_verdict":verdict,"location_checks":location_flags,
        "relevance_status":"strong" if score>=75 and group not in ("adjacent_business","adjacent_other","unrelated")
                           else "potential" if score>=55 else "low",
        "why_fit":("Core cyber role: "+group.replace("_"," ")+". " if not group.startswith("adjacent") else
                   "Adjacent role, not a confirmed core cybersecurity IC vacancy. ")+
                   ("Matched technologies: "+", ".join(skills[:8])+"." if skills else
                    "Insufficient direct keyword evidence from the description."),
    }
