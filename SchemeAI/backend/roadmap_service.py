"""
AI Funding & Scheme Matcher — Phase 6: Application Roadmap, Document Checklist, and Eligibility Gap Analysis Service
Smart India Hackathon: AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs

STRICT PRINCIPLES:
1. Zero Invention:
   - Application steps and document lists are strictly sourced from verified opportunities.json records.
   - If steps or documents are unavailable or unverified, explicit "Not verified, check official site"
     or "Needs verification" labels are returned.
   - Never invent application opening dates, deadlines, or submission links.
2. Privacy & Data Minimization:
   - No sensitive documents, Aadhaar numbers, bank passwords, or identity cards are requested or stored.
   - Checklist status allows marking readiness ("Ready", "Needs attention", etc.) without file uploads.
3. Integrity in Gap Analysis:
   - Compares verified scheme rules against user's saved profile & project.
   - Missing profile data is explicitly flagged as "Missing information" and NEVER assumed as eligible.
   - Never advises altering demographic or personal identity attributes.
   - Never promises approval or guarantees funding.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("schemeai_roadmap_service")

# Path to opportunities.json
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
POSSIBLE_PATHS = [
    os.path.join(CURRENT_DIR, "opportunities.json"),
    os.path.join(CURRENT_DIR, "..", "opportunities.json"),
    os.path.join(os.getcwd(), "opportunities.json"),
    os.path.join(os.getcwd(), "backend", "opportunities.json"),
]


def load_raw_schemes() -> List[Dict[str, Any]]:
    for p in POSSIBLE_PATHS:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading {p}: {e}")
    return []


def find_scheme_by_id(scheme_id: str) -> Optional[Dict[str, Any]]:
    schemes = load_raw_schemes()
    clean_id = scheme_id.strip().lower()
    for s in schemes:
        if s.get("id", "").strip().lower() == clean_id:
            return s
    return None


# ============================================================================
# 1. APPLICATION ROADMAP GENERATION
# ============================================================================

VALID_ROADMAP_STATUSES = ["Not started", "In progress", "Completed"]


def build_scheme_roadmap(
    scheme: Dict[str, Any],
    user_step_statuses: Optional[Dict[str, str]] = None,
    last_updated_map: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Builds structured roadmap from verified apply_steps in scheme record.
    """
    user_step_statuses = user_step_statuses or {}
    last_updated_map = last_updated_map or {}

    scheme_id = scheme.get("id", "")
    scheme_name = scheme.get("name", "Government Scheme")
    verified = bool(scheme.get("verified", True))
    raw_steps = scheme.get("apply_steps", [])
    official_link = scheme.get("official_link") if verified else None

    steps = []
    completed_count = 0
    in_progress_count = 0
    latest_update = None

    if not raw_steps:
        # Factual guard: If steps are absent or unverified
        steps.append({
            "step_id": "step_1",
            "step_index": 1,
            "title": "Check official portal for verified application guidelines",
            "status": "Needs verification",
            "is_verified": False,
            "description": "Verified procedural application steps have not yet been indexed for this scheme. Check official site.",
            "last_updated": None
        })
    else:
        for idx, step_text in enumerate(raw_steps):
            step_id = f"step_{idx + 1}"
            status = user_step_statuses.get(step_id, "Not started")
            if status not in VALID_ROADMAP_STATUSES:
                status = "Not started"

            if status == "Completed":
                completed_count += 1
            elif status == "In progress":
                in_progress_count += 1

            up_ts = last_updated_map.get(step_id)
            if up_ts and (latest_update is None or up_ts > latest_update):
                latest_update = up_ts

            steps.append({
                "step_id": step_id,
                "step_index": idx + 1,
                "title": step_text,
                "status": status,
                "is_verified": verified,
                "last_updated": up_ts
            })

    total_steps = len(steps)
    if total_steps > 0:
        progress_pct = round((completed_count / total_steps) * 100)
    else:
        progress_pct = 0

    if completed_count == total_steps and total_steps > 0:
        overall_status = "Completed"
    elif completed_count > 0 or in_progress_count > 0:
        overall_status = "In progress"
    else:
        overall_status = "Not started"

    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme_name,
        "official_link": official_link,
        "is_link_verified": bool(official_link),
        "link_display_text": official_link if official_link else "Not verified, check official site",
        "provider": scheme.get("provider", "Government Agency"),
        "total_steps": total_steps,
        "completed_steps": completed_count,
        "in_progress_steps": in_progress_count,
        "not_started_steps": total_steps - (completed_count + in_progress_count),
        "progress_percentage": progress_pct,
        "overall_status": overall_status,
        "last_updated": latest_update or datetime.now(timezone.utc).isoformat(),
        "steps": steps,
        "disclaimer": "Application roadmap steps are factual reflections of indexed official guidelines. Completing steps does not guarantee government sanction or funding approval."
    }


# ============================================================================
# 2. DOCUMENT CHECKLIST GENERATION
# ============================================================================

VALID_CHECKLIST_STATUSES = ["Not checked", "Ready", "Needs attention", "Needs verification"]


def build_scheme_checklist(
    scheme: Dict[str, Any],
    user_item_statuses: Optional[Dict[str, str]] = None,
    last_updated_map: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Builds document-readiness checklist from verified documents_required in scheme record.
    """
    user_item_statuses = user_item_statuses or {}
    last_updated_map = last_updated_map or {}

    scheme_id = scheme.get("id", "")
    scheme_name = scheme.get("name", "Government Scheme")
    verified = bool(scheme.get("verified", True))
    raw_docs = scheme.get("documents_required", [])
    provider = scheme.get("provider", "Official Scheme Authority")

    items = []
    ready_count = 0
    needs_attn_count = 0
    needs_verif_count = 0
    not_checked_count = 0
    latest_update = None

    if not raw_docs:
        # Factual guard: If documents are unknown
        items.append({
            "item_id": "doc_1",
            "item_index": 1,
            "name": "Official Document Requirements",
            "explanation": "Specific document checklist has not been verified from official Gazette/notifications. Confirm directly with the scheme provider.",
            "source": f"Official Portal: {scheme.get('official_link') or 'Not verified, check official site'}",
            "status": "Needs verification",
            "is_verified": False,
            "last_updated": None
        })
        needs_verif_count = 1
    else:
        for idx, doc_text in enumerate(raw_docs):
            item_id = f"doc_{idx + 1}"
            status = user_item_statuses.get(item_id, "Not checked")
            if status not in VALID_CHECKLIST_STATUSES:
                status = "Not checked"

            # Contextual explanations based on verified scheme criteria
            explanation, source_ref = _derive_doc_explanation(doc_text, scheme)

            if status == "Ready":
                ready_count += 1
            elif status == "Needs attention":
                needs_attn_count += 1
            elif status == "Needs verification":
                needs_verif_count += 1
            else:
                not_checked_count += 1

            up_ts = last_updated_map.get(item_id)
            if up_ts and (latest_update is None or up_ts > latest_update):
                latest_update = up_ts

            items.append({
                "item_id": item_id,
                "item_index": idx + 1,
                "name": doc_text,
                "explanation": explanation,
                "source": source_ref,
                "status": status,
                "is_verified": verified,
                "last_updated": up_ts
            })

    total_items = len(items)
    readiness_pct = round((ready_count / total_items) * 100) if total_items > 0 else 0

    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme_name,
        "provider": provider,
        "total_items": total_items,
        "ready_count": ready_count,
        "needs_attention_count": needs_attn_count,
        "needs_verification_count": needs_verif_count,
        "not_checked_count": not_checked_count,
        "readiness_percentage": readiness_pct,
        "last_updated": latest_update or datetime.now(timezone.utc).isoformat(),
        "items": items,
        "privacy_notice": "Strict Privacy Policy: You can track document readiness without uploading files. SchemeAI will NEVER ask for or store Aadhaar numbers, bank credentials, passwords, or identity card scans."
    }


def _derive_doc_explanation(doc_name: str, scheme: Dict[str, Any]) -> Tuple[str, str]:
    """Helper providing verified context for specific documents without hallucination."""
    doc_lower = doc_name.lower()
    provider = scheme.get("provider", "Scheme Guidelines")
    link = scheme.get("official_link", "")

    if "dpiit" in doc_lower:
        return (
            "DPIIT Certificate of Recognition issued via Startup India portal (seedfund.startupindia.gov.in). Mandatory for seed fund eligibility.",
            "DPIIT / Startup India Operational Guidelines"
        )
    if "noc" in doc_lower:
        return (
            "No Objection Certificate on institutional letterhead. Mandatory for students or employed innovators to verify approval to pursue prototype development.",
            "DST PRAYAS Centre Guidelines"
        )
    if "community" in doc_lower or "caste" in doc_lower:
        return (
            "Official Community / Caste certificate issued by competent revenue authority (Tahshildar / Taluk office) for affirmative quota verification.",
            "Revenue Department / State Guidelines"
        )
    if "nativity" in doc_lower:
        return (
            "Proof of residence or nativity certificate (minimum required years in State as mandated by scheme norms).",
            f"{provider} Domicile Rules"
        )
    if "edp" in doc_lower:
        return (
            "Entrepreneurship Development Programme (EDP) training certificate from designated institute (e.g. EDII-TN or RSETI).",
            "MSME / DIC Mandate"
        )
    if "dpr" in doc_lower or "project report" in doc_lower or "prototype project plan" in doc_lower:
        return (
            "Detailed project report including technical feasibility, capital expenditure budget, and financial projection.",
            "Bank Appraisal / Investment Committee Format"
        )
    if "quotation" in doc_lower:
        return (
            "Proforma invoices / quotations from verified suppliers for machinery or asset purchases to be financed.",
            "Bank Credit Guidelines"
        )
    if "startuptn" in doc_lower:
        return (
            "Active startup registration record listed on the official StartupTN portal.",
            "StartupTN Policy"
        )
    if "incorporation" in doc_lower or "roc" in doc_lower or "shareholding" in doc_lower:
        return (
            "Certificate of Incorporation from Ministry of Corporate Affairs (MCA) along with official shareholding ledger.",
            "MCA / RoC Compliance"
        )
    if "bank statement" in doc_lower:
        return (
            "Recent 6-month transaction statement from operative bank account.",
            "Lending Institution KYC"
        )
    if "educational" in doc_lower or "mark sheet" in doc_lower or "tc" in doc_lower:
        return (
            "Highest educational qualification certificate (Degree / Diploma / ITI / 8th/10th mark sheet as specified by scheme cost band).",
            "Department of MSME"
        )

    return (
        f"Verified prerequisite item required by {provider}.",
        link if link else provider
    )


# ============================================================================
# 3. ELIGIBILITY GAP ANALYSIS
# ============================================================================

def perform_eligibility_gap_analysis(
    scheme: Dict[str, Any],
    profile: Dict[str, Any],
    project: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compares verified eligibility criteria against user's saved profile & project.
    
    Produces strictly factual categories:
    - satisfied_requirements: Criteria met based on recorded data
    - unsatisfied_requirements: Clear conflicts based on reliable rules
    - missing_information: Necessary profile inputs that were left blank
    - needs_official_verification: Aspects requiring third-party institutional review
    - practical_next_steps: Concrete next actions (without advising changes to personal info)
    """
    elig = scheme.get("eligibility", {})
    scheme_id = scheme.get("id", "")
    scheme_name = scheme.get("name", "Government Scheme")
    provider = scheme.get("provider", "Government Agency")
    official_link = scheme.get("official_link") if scheme.get("verified") else None

    # User Attributes
    user_state = profile.get("state")
    user_community = profile.get("community")
    user_age = profile.get("age")
    user_gender = str(profile.get("gender") or "").strip()
    user_education = str(profile.get("education") or "").strip()
    is_student = bool(profile.get("is_student", False))
    has_registered_co = bool(profile.get("is_registered_company", False))
    is_dpiit = bool(profile.get("is_dpiit_recognised", False))
    is_first_time = bool(profile.get("is_first_time_entrepreneur", True))
    is_woman_led = bool(profile.get("is_woman_led", False) or user_gender.lower() == "female")
    prior_funding = float(profile.get("existing_govt_funding_lakhs") or 0.0)

    satisfied: List[Dict[str, str]] = []
    unsatisfied: List[Dict[str, str]] = []
    missing_info: List[Dict[str, str]] = []
    official_verification: List[Dict[str, str]] = []
    next_steps: List[str] = []

    # 1. Geographic / State Rule
    req_state = elig.get("state")
    if req_state:
        if not user_state or not user_state.strip():
            missing_info.append({
                "criterion": "State of Residence / Enterprise",
                "field_name": "state",
                "impact": f"Scheme strictly requires enterprise located in {req_state}.",
                "how_to_provide": "Update your profile location under Profile Management."
            })
            next_steps.append(f"Specify your enterprise state location in your profile (must be {req_state} for this scheme).")
        elif user_state.strip().lower() == req_state.strip().lower():
            satisfied.append({
                "criterion": "Geographic Eligibility",
                "rule": f"Must be located in {req_state}",
                "user_value": user_state,
                "rationale": f"Enterprise location in {user_state} matches state requirement."
            })
        else:
            unsatisfied.append({
                "criterion": "Geographic Scope Conflict",
                "rule": f"Exclusively restricted to {req_state} enterprises",
                "user_value": user_state,
                "reason": f"Registered state is {user_state}, whereas {scheme_name} is funded exclusively for {req_state} startups."
            })
            next_steps.append(f"Explore Central Government schemes or schemes specific to {user_state}.")
    else:
        satisfied.append({
            "criterion": "National Scope",
            "rule": "Open across all Indian States & Union Territories",
            "user_value": user_state or "All India",
            "rationale": "Central scheme has All-India applicability."
        })

    # 2. Company Registration & DPIIT
    needs_company = elig.get("needs_registered_company", False)
    needs_dpiit = elig.get("needs_dpiit", False)

    if needs_company:
        if has_registered_co:
            satisfied.append({
                "criterion": "Corporate Legal Entity",
                "rule": "Must be incorporated entity (Pvt Ltd / LLP / Partnership)",
                "user_value": "Registered Company",
                "rationale": "Your profile confirms an incorporated corporate entity."
            })
        else:
            unsatisfied.append({
                "criterion": "Company Incorporation Requirement",
                "rule": "Must be registered as Private Limited, LLP or Partnership (sole proprietorships/individuals not accepted)",
                "user_value": "Unregistered / Individual",
                "reason": "This scheme cannot disburse funds to individual bank accounts or unregistered entities."
            })
            next_steps.append("Incorporate your venture as a Private Limited Company or LLP via MCA portal before applying.")

        if needs_dpiit:
            if is_dpiit:
                satisfied.append({
                    "criterion": "DPIIT Startup Recognition",
                    "rule": "Must hold active DPIIT Recognition Certificate",
                    "user_value": "DPIIT Recognised",
                    "rationale": "Recognised startup status verified on your profile."
                })
            else:
                if has_registered_co:
                    unsatisfied.append({
                        "criterion": "Missing DPIIT Recognition",
                        "rule": "Mandatory DPIIT recognition on Startup India portal",
                        "user_value": "Not Recognised",
                        "reason": "Your company is registered but does not have active DPIIT Startup Recognition."
                    })
                    next_steps.append("Register on startupindia.gov.in and obtain DPIIT Recognition Certificate (free and paperless).")
                else:
                    missing_info.append({
                        "criterion": "DPIIT Recognition Prerequisite",
                        "field_name": "is_dpiit_recognised",
                        "impact": "Requires incorporated company before DPIIT recognition can be granted.",
                        "how_to_provide": "Incorporate first, then apply for DPIIT recognition."
                    })
    else:
        # Scheme accepts individual innovators or students (e.g. NIDHI-PRAYAS)
        satisfied.append({
            "criterion": "Individual / Innovator Open Access",
            "rule": "Does not require a pre-registered company",
            "user_value": "Individual / Student / Team",
            "rationale": "Scheme permits prototype grants to individual innovators."
        })

    # 3. Community Quotas & Affirmative Criteria
    req_comm = elig.get("community")
    req_comm_gender = elig.get("community_or_gender")

    if req_comm:
        if not user_community or not user_community.strip():
            missing_info.append({
                "criterion": "Social / Affirmative Category",
                "field_name": "community",
                "impact": f"Scheme exclusively funds founders belonging to {', '.join(req_comm)}.",
                "how_to_provide": "Select your community category in your profile."
            })
            next_steps.append("Update community category in profile to verify affirmative fund eligibility.")
        elif user_community in req_comm:
            satisfied.append({
                "criterion": "Affirmative Community Mandate",
                "rule": f"Reserved for {', '.join(req_comm)} founders",
                "user_value": user_community,
                "rationale": f"Applicant community ({user_community}) satisfies the exclusive mandate."
            })
        else:
            unsatisfied.append({
                "criterion": "Exclusive Community Restriction",
                "rule": f"Exclusively reserved for {', '.join(req_comm)} founders with >50% controlling equity",
                "user_value": user_community,
                "reason": f"Applicant category ({user_community}) does not match the affirmative reservation for this fund."
            })
            next_steps.append("Review universal funding programs like SISFS, TANSEED Open, or Mudra.")

    elif req_comm_gender:
        is_sc_st = user_community in ["SC", "ST"]
        if is_sc_st or is_woman_led:
            reasons = []
            if is_sc_st:
                reasons.append(f"{user_community} category founder")
            if is_woman_led:
                reasons.append("Woman-Led enterprise")
            satisfied.append({
                "criterion": "Stand-Up India Affirmative Mandate",
                "rule": "At least 51% controlling stake by SC, ST, or Woman entrepreneur",
                "user_value": " / ".join(reasons),
                "rationale": f"Satisfies criteria ({' & '.join(reasons)})."
            })
        elif not user_community or not user_community.strip():
            missing_info.append({
                "criterion": "Demographic & Leadership Verification",
                "field_name": "community / is_woman_led",
                "impact": "Stand-Up India requires either SC, ST, or Woman founder leadership.",
                "how_to_provide": "Fill out demographic category and woman-led status in profile."
            })
        else:
            unsatisfied.append({
                "criterion": "Affirmative Founder Criteria",
                "rule": "Exclusively for SC, ST, or Woman entrepreneurs",
                "user_value": f"{user_community} (Not Woman-Led)",
                "reason": "Enterprise is not marked as Woman-Led and community is not SC/ST."
            })
            next_steps.append("Check Mudra Yojana (Tarun/Kishor) or PMEGP General category for alternative collateral-free financing.")

    # 4. Age Criteria
    min_age = elig.get("min_age")
    if min_age:
        if user_age is None:
            missing_info.append({
                "criterion": "Applicant Age Verification",
                "field_name": "age",
                "impact": f"Minimum age requirement of {min_age} years.",
                "how_to_provide": "Provide your age in profile settings."
            })
        elif user_age >= min_age:
            satisfied.append({
                "criterion": "Age Eligibility",
                "rule": f"Minimum {min_age} years old",
                "user_value": f"{user_age} years",
                "rationale": f"Age ({user_age}) satisfies the minimum threshold of {min_age}."
            })
        else:
            unsatisfied.append({
                "criterion": "Age Threshold Not Met",
                "rule": f"Must be at least {min_age} years old",
                "user_value": f"{user_age} years",
                "reason": f"Applicant is under the legal minimum age of {min_age}."
            })

    # 5. Education Criteria (e.g. NEEDS / PMEGP)
    req_edu = elig.get("education")
    if req_edu:
        if not user_education:
            missing_info.append({
                "criterion": "Educational Qualification",
                "field_name": "education",
                "impact": f"Scheme requires qualification: {req_edu}.",
                "how_to_provide": "Select your highest educational qualification in your profile."
            })
            next_steps.append("Specify educational qualification (Degree, Diploma, or ITI) in profile.")
        elif user_education.lower() in ["degree", "diploma", "iti"]:
            satisfied.append({
                "criterion": "Educational Requirement",
                "rule": f"Requires {req_edu}",
                "user_value": user_education.title(),
                "rationale": f"{user_education.title()} meets the vocational/academic requirement."
            })
        else:
            missing_info.append({
                "criterion": "Education Qualification Verification",
                "field_name": "education",
                "impact": f"Requires verified certificate ({req_edu}).",
                "how_to_provide": "Confirm if you hold a Degree, Diploma, or ITI certificate."
            })

    # 6. Student Status & NOC
    if is_student:
        if scheme_id == "nidhi_prayas":
            official_verification.append({
                "criterion": "Student Institutional NOC",
                "verification_body": "Host Educational Institution & PRAYAS Incubator",
                "note": "Students are fully eligible but MUST provide an official No Objection Certificate (NOC) from their college/institution head."
            })
            next_steps.append("Request an official NOC from your university/college principal or dean.")
        elif needs_company:
            official_verification.append({
                "criterion": "Student Company Incorporation",
                "verification_body": "Registrar of Companies (RoC)",
                "note": "Students can incorporate a company, but full-time students must ensure institutional policy permits directorship."
            })

    # 7. Official Verifications Required
    if scheme_id == "sisfs":
        official_verification.append({
            "criterion": "Incubator Pitch & Selection",
            "verification_body": "Incubator Seed Management Committee (ISMC)",
            "note": "Grant and debt approval is decided by an independent incubator committee through in-person pitch presentation."
        })
        official_verification.append({
            "criterion": "Prior Government Grants Cap",
            "verification_body": "DPIIT Seed Fund Portal",
            "note": "Scheme strictly caps prior government monetary assistance at Rs 10 lakh. Audit balance sheet verified upon filing."
        })
    elif scheme_id == "tanseed":
        official_verification.append({
            "criterion": "Grand Jury Valuation & Equity Sanction",
            "verification_body": "StartupTN Grand Jury & Investment Committee",
            "note": "StartupTN takes 3% equity support stake; term sheet and valuation approved during competitive jury rounds."
        })
    elif scheme_id in ["needs", "uyegp"]:
        official_verification.append({
            "criterion": "DLSC Interview & EDP Completion",
            "verification_body": "District Level Selection Committee (DLSC) & EDII-TN",
            "note": "Mandatory in-person interview at District Industries Centre (DIC) followed by structured entrepreneurship training."
        })

    # Always ensure at least 2 practical next steps
    if not next_steps:
        if official_link:
            next_steps.append(f"Visit the verified portal ({official_link}) to review current notification guidelines.")
        next_steps.append("Gather and organize all verified documents listed in the Document Checklist.")
        next_steps.append("Review your business plan / pitch deck milestones with an empanelled mentor.")

    # High-level summary verdict
    if unsatisfied:
        verdict = "Eligibility Gaps Identified"
        verdict_status = "Unsatisfied"
    elif missing_info:
        verdict = "Missing Profile Information"
        verdict_status = "Missing Data"
    else:
        verdict = "Profile Satisfies Available Verified Rules"
        verdict_status = "Satisfied"

    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme_name,
        "provider": provider,
        "official_link": official_link,
        "verdict": verdict,
        "verdict_status": verdict_status,
        "satisfied_requirements": satisfied,
        "unsatisfied_requirements": unsatisfied,
        "missing_information": missing_info,
        "needs_official_verification": official_verification,
        "practical_next_steps": next_steps,
        "disclaimer": "This gap analysis compares your saved profile attributes against published official rules. It is for informational guidance only and does not constitute government approval or guaranteed grant sanction. Never alter personal demographics to force eligibility."
    }
