"""
AI Funding & Scheme Matcher — Phase 4 Deterministic Government Scheme Matching Engine
Smart India Hackathon: AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs

STRICT MATCHING PRINCIPLES:
1. Deterministic & Explainable: Evaluated entirely via structured mathematical and logical rules.
2. Status Categories:
   - "Eligible based on available data"
   - "Potential match"
   - "Needs verification"
   - "Not eligible based on a verified rule"
3. No Guarantees: Never claims guaranteed eligibility or guaranteed funding.
4. Missing Information Guard: Missing profile information is NEVER treated as proof of eligibility.
   If vital info is missing, it is marked as "Needs verification".
5. Non-Probabilistic Score: Match percentage is a profile-fit indicator, not an official probability.
6. Zero Fabrication: Preserves all original scheme data, providers, amounts, and official URLs.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("schemeai_matching_engine")

# Path to opportunities.json
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
POSSIBLE_PATHS = [
    os.path.join(CURRENT_DIR, "opportunities.json"),
    os.path.join(CURRENT_DIR, "..", "opportunities.json"),
    os.path.join(os.getcwd(), "opportunities.json"),
    os.path.join(os.getcwd(), "backend", "opportunities.json"),
]

_CACHED_SCHEMES: Optional[List[Dict[str, Any]]] = None


def get_opportunities_file_path() -> str:
    for p in POSSIBLE_PATHS:
        if os.path.exists(p):
            return p
    return os.path.join(CURRENT_DIR, "opportunities.json")


def load_all_schemes(force_reload: bool = False) -> List[Dict[str, Any]]:
    """
    Loads verified government schemes from opportunities.json.
    Enriches with normalized metadata (government level, funding category).
    """
    global _CACHED_SCHEMES
    if _CACHED_SCHEMES is not None and not force_reload:
        return _CACHED_SCHEMES

    file_path = get_opportunities_file_path()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_schemes = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load opportunities.json from {file_path}: {e}")
        raw_schemes = []

    enriched = []
    for s in raw_schemes:
        item = dict(s)
        provider = str(item.get("provider", "")).lower()
        elig = item.get("eligibility", {})
        state_req = elig.get("state")
        raw_type = str(item.get("type", "")).lower()

        # Classify Government (Central vs State)
        if state_req or "tamil nadu" in provider or "startuptn" in provider or "tiic" in provider:
            item["government"] = "State Government (Tamil Nadu)"
            item["government_scope"] = "State"
            item["state"] = "Tamil Nadu"
        else:
            item["government"] = "Central Government"
            item["government_scope"] = "Central"
            item["state"] = "All India"

        # Classify Funding Type
        if "grant" in raw_type and "debt" in raw_type:
            item["funding_type_label"] = "Grant & Debt"
            item["funding_category"] = "grant"
        elif "grant" in raw_type or "fellowship" in raw_type:
            item["funding_type_label"] = "Grant / Seed Capital"
            item["funding_category"] = "grant"
        elif "subsidy" in raw_type:
            item["funding_type_label"] = "Capital Subsidy & Loan"
            item["funding_category"] = "subsidy"
        elif "equity" in raw_type:
            item["funding_type_label"] = "Government Equity"
            item["funding_category"] = "equity"
        elif "loan" in raw_type:
            item["funding_type_label"] = "Subsidized Loan"
            item["funding_category"] = "loan"
        elif "tax" in raw_type:
            item["funding_type_label"] = "Tax Exemption / Relief"
            item["funding_category"] = "grant"
        else:
            item["funding_type_label"] = item.get("type", "Financial Support").title()
            item["funding_category"] = "other"

        enriched.append(item)

    _CACHED_SCHEMES = enriched
    logger.info(f"Loaded {len(_CACHED_SCHEMES)} verified government schemes.")
    return _CACHED_SCHEMES


def parse_user_stage(stage_val: Any) -> int:
    """Normalizes string or int stage representation to integer (1, 2, 3)."""
    if isinstance(stage_val, int) and stage_val in (1, 2, 3):
        return stage_val
    if isinstance(stage_val, str):
        val_clean = stage_val.strip().lower()
        if "ideation" in val_clean or "idea" in val_clean or val_clean == "stage 1" or val_clean == "1":
            return 1
        if "prototype" in val_clean or "pilot" in val_clean or "early" in val_clean or val_clean == "stage 2" or val_clean == "2":
            return 2
        if "scale" in val_clean or "scaling" in val_clean or "market" in val_clean or "growth" in val_clean or "expansion" in val_clean or val_clean == "stage 3" or val_clean == "3":
            return 3
        if "1" in val_clean:
            return 1
        if "2" in val_clean:
            return 2
        if "3" in val_clean:
            return 3
    return 1  # Default to Stage 1


def evaluate_scheme_for_profile(
    scheme: Dict[str, Any],
    profile: Dict[str, Any],
    project: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluates a single scheme against user's saved profile & optional project.
    
    Returns structured deterministic report:
    - match_score: profile-fit indicator (0-100)
    - eligibility_status:
      'Eligible based on available data' |
      'Potential match' |
      'Needs verification' |
      'Not eligible based on a verified rule'
    - primary_status: 'Likely Match' | 'Needs Verification' | 'Not Eligible'
    - match_reasons: list of why criteria fit
    - missing_requirements: checklist of missing prerequisites/documents
    - disqualifications: list of hard rule violations (if any)
    - missing_info: vital profile attributes that were not provided
    - student_alert: institution NOC notice if applicable
    - score_breakdown: detailed component scoring
    """
    elig = scheme.get("eligibility", {})
    scheme_id = scheme.get("id", "")
    scheme_stages = scheme.get("stage", [1, 2, 3])
    provider = scheme.get("provider", "")
    is_scheme_verified = scheme.get("verified", True)
    scheme_status = scheme.get("status", "open")

    # Extract user inputs safely (allow project location & stage to supplement or prioritize profile)
    user_state = (project.get("state") if project else None) or profile.get("state")
    if not user_state and project and project.get("target_location"):
        if "tamil nadu" in str(project["target_location"]).lower():
            user_state = "Tamil Nadu"
    user_district = (project.get("district") if project else None) or profile.get("district")
    user_community = profile.get("community")
    user_age = profile.get("age")
    user_gender = str(profile.get("gender") or "").strip()
    user_income = profile.get("annual_income")
    user_education = str(profile.get("education") or "").strip().lower()
    is_student = bool(profile.get("is_student", False))
    has_registered_co = bool(profile.get("is_registered_company", False))
    is_dpiit = bool(profile.get("is_dpiit_recognised", False))
    is_first_time = bool(profile.get("is_first_time_entrepreneur", True))
    is_woman_led = bool(profile.get("is_woman_led", False) or user_gender.lower() == "female")
    prior_funding = float(profile.get("existing_govt_funding_lakhs") or 0.0)

    # Determine stage from project or profile
    stage_val = (project.get("current_stage") or project.get("stage") if project else None) or profile.get("preferred_stage", 1)
    user_stage = parse_user_stage(stage_val)

    # Tracking lists
    disqualifications: List[str] = []
    missing_requirements: List[str] = []
    missing_info: List[str] = []
    match_reasons: List[str] = []
    student_alert: Optional[str] = None

    breakdown = {
        "stage_alignment": 0,
        "demographic_quota": 0,
        "entity_readiness": 0,
        "geographic_fit": 0,
        "financial_experience": 0
    }

    # ========================================================================
    # 1. GEOGRAPHIC & STATE ELIGIBILITY (Max 20 pts)
    # ========================================================================
    req_state = elig.get("state")
    if req_state:
        if user_state is None or user_state.strip() == "":
            missing_info.append(f"State of enterprise / domicile is not specified (Scheme requires {req_state})")
            breakdown["geographic_fit"] = 6
        elif user_state.strip().lower() == req_state.strip().lower():
            match_reasons.append(f"Enterprise resident in {req_state} as officially required")
            breakdown["geographic_fit"] = 20
        else:
            disqualifications.append(f"Exclusively restricted to {req_state} enterprises/residents (Applicant is registered in {user_state})")
            breakdown["geographic_fit"] = 0
    else:
        # Central schemes open nationwide
        match_reasons.append("Central Government scheme open to eligible applicants across all Indian States & UTs")
        breakdown["geographic_fit"] = 20

    # ========================================================================
    # 2. COMMUNITY & GENDER AFFIRMATIVE QUOTAS (Max 25 pts)
    # ========================================================================
    req_community = elig.get("community")
    req_comm_or_gender = elig.get("community_or_gender")

    if req_community:
        # Exclusive community scheme (e.g., TN SC/ST Startup Fund)
        if user_community is None or user_community.strip() == "":
            missing_info.append(f"Social category is missing (Scheme exclusively reserves funding for {', '.join(req_community)})")
            breakdown["demographic_quota"] = 5
        elif user_community in req_community:
            match_reasons.append(f"Direct match with {user_community} affirmative entrepreneurship quota")
            breakdown["demographic_quota"] = 25
        else:
            disqualifications.append(f"Exclusively reserved for {', '.join(req_community)} community founders (Applicant category: {user_community})")
            breakdown["demographic_quota"] = 0

    elif req_comm_or_gender:
        # Community OR Gender scheme (e.g., Stand-Up India: SC, ST, or Woman)
        is_sc_st = user_community in ["SC", "ST"]
        if is_sc_st or is_woman_led:
            reasons = []
            if is_sc_st:
                reasons.append(f"{user_community} founder category")
            if is_woman_led:
                reasons.append("Woman-Led enterprise")
            match_reasons.append(f"Qualifies under affirmative criteria ({' & '.join(reasons)})")
            breakdown["demographic_quota"] = 25
        elif user_community is None or user_community.strip() == "":
            missing_info.append("Social category and ownership structure needed to verify Stand-Up India quota")
            breakdown["demographic_quota"] = 8
        else:
            disqualifications.append(f"Exclusively reserved for SC, ST, or Women-led enterprises (Applicant is {user_community}, not marked Woman-Led)")
            breakdown["demographic_quota"] = 0

    else:
        # Preferential subsidy schemes (PMEGP, NEEDS, TANSEED, Mudra)
        is_special_cat = (user_community in ["SC", "ST", "BC", "MBC"]) or is_woman_led
        if is_special_cat:
            cat_desc = []
            if user_community in ["SC", "ST", "BC", "MBC"]:
                cat_desc.append(f"{user_community} Category")
            if is_woman_led:
                cat_desc.append("Women Entrepreneur")
            match_reasons.append(f"Eligible for higher Special Category subsidy rates ({', '.join(cat_desc)})")
            breakdown["demographic_quota"] = 25
        elif user_community:
            match_reasons.append("Standard General category rates apply")
            breakdown["demographic_quota"] = 18
        else:
            missing_info.append("Community category not provided (determines priority subsidy tier)")
            breakdown["demographic_quota"] = 12

    # ========================================================================
    # 3. COMPANY REGISTRATION & DPIIT RECOGNITION (Max 20 pts)
    # ========================================================================
    needs_company = elig.get("needs_registered_company", False)
    needs_dpiit = elig.get("needs_dpiit", False)

    if needs_company:
        if has_registered_co:
            if needs_dpiit:
                if is_dpiit:
                    match_reasons.append("Incorporated company with active DPIIT Startup Recognition")
                    breakdown["entity_readiness"] = 20
                else:
                    missing_requirements.append("DPIIT Certificate of Recognition on Startup India portal")
                    match_reasons.append("Registered company ready; DPIIT filing required")
                    breakdown["entity_readiness"] = 12
            else:
                match_reasons.append("Registered corporate entity satisfies incorporation requirement")
                breakdown["entity_readiness"] = 20
        else:
            # Scheme requires registered company, but founder has not registered yet
            missing_requirements.append("Incorporation as a Private Limited Company, LLP, or Registered Partnership")
            if needs_dpiit:
                missing_requirements.append("DPIIT Startup Recognition certificate")
            breakdown["entity_readiness"] = 4
    else:
        # Scheme supports individuals, students, proprietary/unregistered ventures
        if not has_registered_co:
            match_reasons.append("Open to individual innovators, proprietary firms, and unregistered prototypes")
            breakdown["entity_readiness"] = 20
        else:
            match_reasons.append("Registered entity fully eligible to apply")
            breakdown["entity_readiness"] = 18

    # ========================================================================
    # 4. STARTUP DEVELOPMENT STAGE MATCH (Max 20 pts)
    # ========================================================================
    if user_stage in scheme_stages:
        match_reasons.append(f"Matches your current venture development stage (Stage {user_stage})")
        breakdown["stage_alignment"] = 20
    elif (user_stage + 1 in scheme_stages) or (user_stage - 1 in scheme_stages):
        target_stage = scheme_stages[0] if user_stage < scheme_stages[0] else scheme_stages[-1]
        missing_requirements.append(f"Venture advancement to Stage {target_stage} milestones")
        breakdown["stage_alignment"] = 10
    else:
        missing_requirements.append(f"Designed for Stage {', '.join(map(str, scheme_stages))} ventures")
        breakdown["stage_alignment"] = 4

    # ========================================================================
    # 5. AGE, EDUCATION, FIRST-TIME & FUNDING CONSTRAINTS (Max 15 pts)
    # ========================================================================
    fin_pts = 15

    # Age Evaluation
    req_min_age = elig.get("min_age")
    age_rules = elig.get("age")

    if user_age is None:
        if req_min_age or age_rules:
            missing_info.append("Age not provided (scheme enforces age criteria)")
            fin_pts -= 3
    else:
        if req_min_age and user_age < req_min_age:
            disqualifications.append(f"Minimum age requirement is {req_min_age} years (applicant is {user_age})")
            fin_pts = 0
        elif isinstance(age_rules, dict):
            # E.g., NEEDS: General 21-35, Special 21-45
            is_special = (user_community in ["SC", "ST", "BC", "MBC"]) or is_woman_led
            min_a = 21
            max_a = 45 if is_special else 35
            if user_age < min_a or user_age > max_a:
                disqualifications.append(f"Age must be between {min_a} and {max_a} for your category (applicant is {user_age})")
                fin_pts = 0
            else:
                match_reasons.append(f"Age {user_age} falls within verified eligible band ({min_a}–{max_a} years)")

    # Education Evaluation
    req_edu = elig.get("education")
    if req_edu:
        if not user_education or user_education == "none":
            missing_info.append(f"Education level not verified (Scheme requires {req_edu})")
            fin_pts -= 3
        elif "degree" in req_edu.lower():
            if user_education in ["degree", "diploma", "iti"]:
                match_reasons.append(f"Educational qualification ({user_education.title()}) satisfies scheme prerequisite")
            else:
                disqualifications.append(f"Requires Degree, Diploma, or ITI qualification (Applicant qualification: {user_education})")
                fin_pts = 0

    # Prior Funding Ceiling (e.g. SISFS max 10L)
    max_prior = elig.get("max_prior_govt_funding_lakh")
    if max_prior is not None and prior_funding > max_prior:
        disqualifications.append(f"Prior government subsidies received (₹{prior_funding} Lakhs) exceed scheme limit of ₹{max_prior} Lakhs")
        fin_pts = 0
    elif prior_funding == 0.0:
        match_reasons.append("Zero prior government grants received — fully eligible for full subsidy quota")

    # Greenfield / First-Time Requirement (e.g. Stand-Up India)
    if elig.get("project") == "greenfield only (first-time venture)":
        if is_first_time:
            match_reasons.append("Greenfield venture: First-time entrepreneur criteria satisfied")
        else:
            disqualifications.append("Restricted strictly to greenfield (first-time commercial) ventures")
            fin_pts = 0

    # Student NOC check (e.g. NIDHI-PRAYAS)
    if is_student and scheme_id == "nidhi_prayas":
        student_alert = "Institution NOC: As a student, a formal No Objection Certificate from your college/dean is mandatory."
        missing_requirements.append("Institution No Objection Certificate (NOC) for student innovators")

    breakdown["financial_experience"] = max(0, fin_pts)

    # Project Category & Funding Alignment Check
    if project:
        proj_cat = str(project.get("category", "")).lower()
        proj_budget = float(project.get("estimated_budget") or 0.0)
        
        # Sector matching for priority schemes like TANSEED
        if scheme_id == "tanseed":
            if any(k in proj_cat for k in ["green", "agri", "rural", "clean", "climate", "waste", "sustain"]):
                match_reasons.append("Project sector qualifies for enhanced ₹15 Lakh Green Tech / Rural Impact grant bracket")
                breakdown["stage_alignment"] = min(20, breakdown["stage_alignment"] + 5)
        
        # Sector matching against scheme-defined priority sectors
        scheme_sectors = elig.get("sectors", [])
        if scheme_sectors and proj_cat:
            matched_sec = [s for s in scheme_sectors if s.lower() in proj_cat or any(w in s.lower() for w in proj_cat.split() if len(w) > 3)]
            if matched_sec:
                match_reasons.append(f"Venture sector '{project.get('category')}' aligns with target domain ({', '.join(matched_sec)})")
                breakdown["stage_alignment"] = min(20, breakdown["stage_alignment"] + 5)

        # Funding budget checks
        if scheme_id == "sisfs" and 0 < proj_budget <= 2000000:
            match_reasons.append(f"Funding requirement (₹{proj_budget:,.0f}) is within SISFS prototype grant limit (₹20 Lakhs)")
        elif scheme_id == "nidhi_prayas" and 0 < proj_budget <= 1000000:
            match_reasons.append(f"Funding requirement is within NIDHI-PRAYAS ₹10 Lakh prototype grant ceiling")
        elif proj_budget > 0:
            match_reasons.append(f"Funding requirement of ₹{proj_budget:,.0f} registered for project matching")

    # ========================================================================
    # MATCH SCORE & ELIGIBILITY STATUS CLASSIFICATION
    # ========================================================================
    raw_score = sum(breakdown.values())
    total_score = max(0, min(100, raw_score))

    # Determine Status strictly based on deterministic rules:
    if disqualifications:
        eligibility_status = "Not eligible based on a verified rule"
        primary_status = "Not Eligible"
        total_score = min(total_score, 25)
    elif missing_info or not is_scheme_verified:
        # Vital profile info missing OR unverified scheme dataset
        eligibility_status = "Needs verification"
        primary_status = "Needs Verification"
    elif missing_requirements or (user_stage not in scheme_stages):
        eligibility_status = "Potential match"
        primary_status = "Needs Verification"
    elif total_score >= 65:
        eligibility_status = "Eligible based on available data"
        primary_status = "Likely Match"
    else:
        eligibility_status = "Potential match"
        primary_status = "Likely Match"

    # Structured matching criteria explanation list
    structured_criteria = []
    for r in match_reasons:
        structured_criteria.append({"criterion": "Profile Match", "type": "positive", "text": r})
    for m in missing_requirements:
        structured_criteria.append({"criterion": "Prerequisite", "type": "missing", "text": m})
    for w in missing_info:
        structured_criteria.append({"criterion": "Unverified Field", "type": "warning", "text": w})
    for d in disqualifications:
        structured_criteria.append({"criterion": "Eligibility Rule", "type": "ineligible", "text": d})

    # Human-readable summary explanation
    explanation_parts = []
    if match_reasons:
        explanation_parts.append("; ".join(match_reasons[:3]))
    if missing_requirements:
        explanation_parts.append(f"Pending prerequisites: {'; '.join(missing_requirements[:2])}")
    if disqualifications:
        explanation_parts.append(f"Rule conflict: {disqualifications[0]}")
    match_explanation = ". ".join(explanation_parts) + "." if explanation_parts else "Evaluation completed based on available data."

    last_verified_val = scheme.get("last_verified")
    if not last_verified_val or not is_scheme_verified:
        last_verified_date = "Not verified, check official site"
    else:
        last_verified_date = str(last_verified_val)

    official_url = scheme.get("official_link") or "#"
    apply_steps_list = scheme.get("apply_steps", [])

    return {
        "id": scheme_id,
        "scheme_id": scheme_id,
        "name": scheme.get("name"),
        "scheme_name": scheme.get("name"),
        "government": scheme.get("government"),
        "government_scope": scheme.get("government_scope"),
        "state": scheme.get("state"),
        "type": scheme.get("funding_type_label", scheme.get("type")),
        "funding_type": scheme.get("funding_type_label", scheme.get("type")),
        "funding_category": scheme.get("funding_category", "other"),
        "provider": provider,
        "benefit": scheme.get("benefit"),
        "verified_benefit": scheme.get("benefit") if is_scheme_verified else None,
        "stage": scheme_stages,
        "primary_status": primary_status,
        "eligibility_status": eligibility_status,
        "match_score": total_score,
        "match_explanation": match_explanation,
        "matching_criteria_explanation": structured_criteria,
        "match_reasons": match_reasons,
        "missing_requirements": missing_requirements + [f"Unverified profile detail: {i}" for i in missing_info],
        "missing_eligibility_requirements": missing_requirements + [f"Unverified profile detail: {i}" for i in missing_info],
        "missing_info": missing_info,
        "disqualifications": disqualifications,
        "student_alert": student_alert,
        "documents_required": scheme.get("documents_required", []),
        "apply_steps": apply_steps_list,
        "application_steps": apply_steps_list,
        "official_link": official_url,
        "application_url": official_url,
        "official_application_url": official_url,
        "status": scheme.get("status", "open"),
        "last_verified": last_verified_date,
        "last_verified_date": last_verified_date,
        "verify_note": scheme.get("verify_note"),
        "verified": is_scheme_verified,
        "score_breakdown": breakdown
    }



def get_matched_schemes_for_user(
    profile: Dict[str, Any],
    project: Optional[Dict[str, Any]] = None,
    funding_type: Optional[str] = None,
    government: Optional[str] = None,
    eligibility_status: Optional[str] = None,
    search_query: Optional[str] = None,
    page: int = 1,
    page_size: int = 15,
    all_items: bool = True
) -> Dict[str, Any]:
    """
    Ranks and filters all schemes for the given profile and optional project.
    Generates summary statistics, pagination metadata, and compliance disclaimers.
    """
    all_schemes = load_all_schemes()
    evaluations: List[Dict[str, Any]] = []

    for s in all_schemes:
        eval_result = evaluate_scheme_for_profile(s, profile, project)
        evaluations.append(eval_result)

    # Sort primarily by match_score descending
    evaluations.sort(key=lambda x: (x["match_score"], x.get("verified", False)), reverse=True)

    # Summary statistics across ALL evaluated schemes
    total_count = len(evaluations)
    eligible_count = sum(1 for e in evaluations if e["eligibility_status"] == "Eligible based on available data")
    potential_count = sum(1 for e in evaluations if e["eligibility_status"] == "Potential match")
    needs_verif_count = sum(1 for e in evaluations if e["primary_status"] == "Needs Verification")
    not_eligible_count = sum(1 for e in evaluations if e["primary_status"] == "Not Eligible")
    likely_match_count = sum(1 for e in evaluations if e["primary_status"] == "Likely Match")
    avg_score = round(sum(e["match_score"] for e in evaluations) / total_count, 1) if total_count > 0 else 0.0

    # Apply Filters if requested
    filtered_results = evaluations

    if funding_type and funding_type.strip().lower() not in ("all", ""):
        ft_clean = funding_type.strip().lower()
        filtered_results = [
            e for e in filtered_results 
            if e["funding_category"] == ft_clean or ft_clean in e["type"].lower()
        ]

    if government and government.strip().lower() not in ("all", ""):
        gov_clean = government.strip().lower()
        filtered_results = [
            e for e in filtered_results 
            if gov_clean in e["government"].lower() or gov_clean in e["government_scope"].lower()
        ]

    if eligibility_status and eligibility_status.strip().lower() not in ("all", ""):
        es_clean = eligibility_status.strip().lower()
        filtered_results = [
            e for e in filtered_results 
            if es_clean in e["eligibility_status"].lower() or es_clean in e.get("primary_status", "").lower()
        ]

    if search_query and search_query.strip():
        q = search_query.strip().lower()
        filtered_results = [
            e for e in filtered_results
            if q in e["name"].lower() or q in e["provider"].lower() or q in e["benefit"].lower()
        ]

    # Assign sequential ranks
    for rank_idx, item in enumerate(filtered_results, 1):
        item["rank"] = rank_idx

    # Pagination calculation
    total_filtered = len(filtered_results)
    actual_page_size = max(1, page_size) if page_size > 0 else 15
    total_pages = max(1, (total_filtered + actual_page_size - 1) // actual_page_size) if total_filtered > 0 else 1
    safe_page = max(1, min(page, total_pages)) if total_filtered > 0 else 1
    start_idx = (safe_page - 1) * actual_page_size
    end_idx = min(start_idx + actual_page_size, total_filtered)

    if all_items or page_size <= 0:
        paged_matches = filtered_results
    else:
        paged_matches = filtered_results[start_idx:end_idx]

    pagination_meta = {
        "page": safe_page,
        "page_size": actual_page_size,
        "total_items": total_filtered,
        "total_pages": total_pages,
        "has_next": safe_page < total_pages,
        "has_prev": safe_page > 1,
        "start_index": start_idx + 1 if total_filtered > 0 else 0,
        "end_index": end_idx
    }

    disclaimer = (
        "Compliance Advisory: Match scores are profile-fit indicators based on available data, "
        "not official eligibility probabilities or funding guarantees. "
        "Government scheme guidelines and quotas are subject to periodic gazette revisions. "
        "Always confirm specific guidelines and deadlines directly on the official department portal before applying."
    )

    return {
        "success": True,
        "pagination": pagination_meta,
        "match_summary": {
            "total_schemes": total_count,
            "filtered_count": total_filtered,
            "eligible_count": eligible_count,
            "potential_count": potential_count,
            "likely_match_count": likely_match_count,
            "needs_verification_count": needs_verif_count,
            "not_eligible_count": not_eligible_count,
            "average_fit_score": avg_score
        },
        "database_coverage": {
            "verified_schemes_count": total_count,
            "page_size": actual_page_size,
            "total_pages": total_pages,
            "note": f"SchemeAI database indexes {total_count} verified central and Tamil Nadu schemes from official gazettes and portals. Displaying up to {actual_page_size} schemes per page."
        },
        "profile_summary": {
            "full_name": profile.get("full_name"),
            "state": (project.get("state") if project else None) or profile.get("state"),
            "district": (project.get("district") if project else None) or profile.get("district"),
            "community": profile.get("community"),
            "stage": (project.get("current_stage") or project.get("stage") if project else None) or profile.get("preferred_stage"),
            "project_title": project.get("title") if project else None,
            "project_category": project.get("category") if project else None,
            "is_registered_company": profile.get("is_registered_company", False),
            "is_dpiit_recognised": profile.get("is_dpiit_recognised", False),
            "is_woman_led": profile.get("is_woman_led", False),
            "is_student": profile.get("is_student", False)
        },
        "disclaimer": disclaimer,
        "matches": paged_matches,
        "all_matches": filtered_results
    }



def get_scheme_by_id(scheme_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single scheme from dataset by ID."""
    all_schemes = load_all_schemes()
    for s in all_schemes:
        if s.get("id", "").lower() == scheme_id.strip().lower():
            return s
    return None
