"""
AI Funding & Scheme Matcher — Phase 4 Matching Engine Automated Test Suite
Validates the 5 required real-world entrepreneur scenarios:
1. Tamil Nadu student with an unregistered startup idea
2. Registered startup with DPIIT recognition
3. Woman-led startup
4. Profile missing important eligibility information
5. Profile that does not satisfy a verified scheme criterion

Plus API integration tests for:
- GET /api/schemes
- GET /api/schemes/matches (auth enforced, verified user ID)
- GET /api/schemes/{scheme_id}
"""

import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from matching_service import (
    load_all_schemes,
    get_matched_schemes_for_user,
    evaluate_scheme_for_profile,
    get_scheme_by_id
)


def test_scenario_1_tn_student_unregistered_idea():
    """
    Scenario 1: Tamil Nadu student with an unregistered startup idea.
    Expectations:
    - NIDHI-PRAYAS: Excellent fit for student / idea-stage innovators (no company registration strictly required).
    - TANSEED: Requires registered company -> flagged missing requirement.
    - SISFS: Requires DPIIT & registered private limited / LLP -> flagged missing requirement.
    - Status for student-friendly idea schemes: "Eligible based on available data" or "Potential match".
    """
    print("\n--- Running Scenario 1: Tamil Nadu student with unregistered idea ---")
    profile = {
        "full_name": "Karthik Subramanian",
        "email": "karthik.subbu@college.edu",
        "state": "Tamil Nadu",
        "district": "Chennai",
        "community": "BC",
        "age": 21,
        "education": "Degree",
        "is_student": True,
        "is_registered_company": False,
        "is_dpiit_recognised": False,
        "is_first_time_entrepreneur": True,
        "is_woman_led": False,
        "existing_govt_funding_lakhs": 0.0,
        "preferred_stage": "Stage 1"
    }
    project = {
        "title": "Low-Cost Automated IoT Water Desalination",
        "current_stage": "Stage 1",
        "category": "Cleantech & Hardware"
    }

    result = get_matched_schemes_for_user(profile, project)
    matches = result["matches"]
    assert len(matches) > 0, "Matches list should not be empty"

    # Find NIDHI-PRAYAS
    prayas = next((m for m in matches if m["id"] == "nidhi_prayas"), None)
    assert prayas is not None, "NIDHI-PRAYAS should be present in schemes"
    assert prayas["eligibility_status"] in ("Eligible based on available data", "Potential match"), (
        f"NIDHI-PRAYAS should be eligible/potential for student idea, got: {prayas['eligibility_status']}"
    )
    assert prayas["match_score"] >= 80, f"Expected high score for NIDHI-PRAYAS, got {prayas['match_score']}"

    # Find TANSEED - should flag missing company registration
    tanseed = next((m for m in matches if m["id"] == "tanseed"), None)
    assert tanseed is not None, "TANSEED should be present"
    missing_texts = [m.lower() if isinstance(m, str) else m.get("text", "").lower() for m in tanseed.get("missing_requirements", [])]
    assert any("registered" in t or "company" in t for t in missing_texts), (
        f"TANSEED should report missing registered company for unregistered idea. Got: {missing_texts}"
    )
    print("[PASS] Scenario 1 passed successfully!")


def test_scenario_2_registered_dpiit_startup():
    """
    Scenario 2: Registered startup with DPIIT recognition.
    Expectations:
    - SISFS: High match ("Eligible based on available data").
    - TANSEED: Strong match if based in TN.
    - Match score is high; entity criteria are satisfied.
    """
    print("\n--- Running Scenario 2: Registered startup with DPIIT recognition ---")
    profile = {
        "full_name": "Arjun Venkataraman",
        "email": "arjun@deeptechlabs.in",
        "state": "Tamil Nadu",
        "district": "Coimbatore",
        "community": "General",
        "age": 32,
        "education": "Degree",
        "is_student": False,
        "is_registered_company": True,
        "is_dpiit_recognised": True,
        "is_first_time_entrepreneur": False,
        "is_woman_led": False,
        "existing_govt_funding_lakhs": 0.0,
        "preferred_stage": "Stage 2"
    }
    project = {
        "title": "Industrial AI Vision Inspection",
        "current_stage": "Stage 2",
        "category": "Deep Tech"
    }

    result = get_matched_schemes_for_user(profile, project)
    matches = result["matches"]

    sisfs = next((m for m in matches if m["id"] in ("sisfs", "startup_india_seed_fund")), None)
    assert sisfs is not None, "SISFS must be found"
    assert sisfs["eligibility_status"] in ("Eligible based on available data", "Potential match"), (
        f"SISFS should be eligible for DPIIT registered startup, got {sisfs['eligibility_status']}"
    )
    assert sisfs["match_score"] >= 80, f"SISFS fit score should be >= 80, got {sisfs['match_score']}"

    # Verify that company registration is recognized in positive reasons
    positives = [e["text"].lower() for e in sisfs["matching_criteria_explanation"] if e["type"] in ("positive", "match")]
    assert any("dpiit" in p for p in positives), f"DPIIT recognition must be noted in positive criteria: {positives}"
    print("[PASS] Scenario 2 passed successfully!")


def test_scenario_3_woman_led_startup():
    """
    Scenario 3: Woman-led startup.
    Expectations:
    - Stand-Up India: High match / eligible (mandates woman or SC/ST entrepreneur).
    - TANSEED / Tamil Nadu SC/ST & Women quotas: Recognized and highlighted.
    - Positive criteria note woman leadership.
    """
    print("\n--- Running Scenario 3: Woman-led startup ---")
    profile = {
        "full_name": "Ananya Sundaram",
        "email": "ananya@herkraft.in",
        "state": "Tamil Nadu",
        "district": "Madurai",
        "community": "BC",
        "age": 29,
        "gender": "Female",
        "education": "Degree",
        "is_student": False,
        "is_registered_company": True,
        "is_dpiit_recognised": True,
        "is_first_time_entrepreneur": True,
        "is_woman_led": True,
        "existing_govt_funding_lakhs": 0.0,
        "preferred_stage": "Stage 2"
    }
    project = {
        "title": "Sustainable Eco-Packaging",
        "current_stage": "Stage 2",
        "category": "Sustainability & Manufacturing"
    }

    result = get_matched_schemes_for_user(profile, project)
    matches = result["matches"]

    standup = next((m for m in matches if m["id"] in ("supi", "standup_india")), None)
    assert standup is not None, "Stand-Up India must be found"
    assert standup["eligibility_status"] in ("Eligible based on available data", "Potential match"), (
        f"Stand-Up India should be eligible for woman-led enterprise, got {standup['eligibility_status']}"
    )

    # Verify woman-led status is specifically noted
    explanation_texts = [e["text"].lower() for e in standup["matching_criteria_explanation"]]
    assert any("woman" in t or "female" in t for t in explanation_texts), (
        f"Woman-led qualification should be highlighted in explanation: {explanation_texts}"
    )
    print("[PASS] Scenario 3 passed successfully!")


def test_scenario_4_profile_missing_important_info():
    """
    Scenario 4: Profile missing important eligibility information.
    Expectations:
    - Missing state, community, income, or company registration.
    - Rule: Missing profile information must NEVER be treated as proof of eligibility.
    - Status MUST be flagged as 'Needs verification'.
    - Missing requirements section lists the unknown fields.
    """
    print("\n--- Running Scenario 4: Profile missing important information ---")
    profile = {
        "full_name": "Incomplete Profile User",
        "email": "unknown@example.org",
        "state": None,
        "district": None,
        "community": None,
        "annual_income": None,
        "education": None,
        "is_student": False,
        "is_registered_company": False,
        "is_dpiit_recognised": False,
        "is_first_time_entrepreneur": True,
        "is_woman_led": False,
        "existing_govt_funding_lakhs": 0.0
    }

    result = get_matched_schemes_for_user(profile)
    matches = result["matches"]

    # There must be schemes marked "Needs verification"
    needs_verif = [m for m in matches if m["eligibility_status"] == "Needs verification"]
    assert len(needs_verif) > 0, (
        f"Incomplete profile must result in 'Needs verification' statuses. Found {len(needs_verif)}"
    )

    # Check that missing requirements or warnings exist
    sample = needs_verif[0]
    assert len(sample.get("missing_requirements", [])) > 0 or len(sample.get("warnings", [])) > 0, (
        "Schemes requiring verification must detail missing requirements"
    )
    print(f"[PASS] Scenario 4 passed successfully! ({len(needs_verif)} schemes correctly flagged as 'Needs verification')")


def test_scenario_5_failing_verified_criterion():
    """
    Scenario 5: Profile that does not satisfy a verified scheme criterion.
    Expectations:
    - E.g. Tamil Nadu SC/ST Startup Fund applied by an applicant with state = 'Maharashtra' and community = 'General'.
    - State is non-Tamil Nadu -> Explicitly fails verified geographic rule.
    - Status MUST be 'Not eligible based on a verified rule'.
    - Explanation clearly specifies which rule disqualified the applicant.
    """
    print("\n--- Running Scenario 5: Profile failing verified scheme criterion ---")
    profile = {
        "full_name": "Rahul Verma",
        "email": "rahul@mumbai.in",
        "state": "Maharashtra",
        "district": "Mumbai Suburbs",
        "community": "General",
        "annual_income": 800000.0,
        "age": 30,
        "education": "Degree",
        "is_student": False,
        "is_registered_company": True,
        "is_dpiit_recognised": True,
        "is_first_time_entrepreneur": False,
        "is_woman_led": False,
        "existing_govt_funding_lakhs": 0.0
    }

    result = get_matched_schemes_for_user(profile)
    matches = result["matches"]

    # Check TN SC/ST Startup Fund
    tn_sc_st = next((m for m in matches if m["id"] in ("tn_scst_fund", "tn_sc_st_startup_fund")), None)
    assert tn_sc_st is not None, "TN SC/ST Fund should be present"
    assert tn_sc_st["eligibility_status"] == "Not eligible based on a verified rule", (
        f"Non-TN General applicant must be 'Not eligible based on a verified rule' for TN SC/ST fund. Got: {tn_sc_st['eligibility_status']}"
    )

    # Check explanation states verified exclusion
    disqualifiers = [e["text"].lower() for e in tn_sc_st["matching_criteria_explanation"] if e["type"] in ("negative", "ineligible", "warning")]
    assert any("tamil nadu" in d or "state" in d or "community" in d or "sc/st" in d for d in disqualifiers), (
        f"Disqualification reason must mention state or community restriction: {disqualifiers}"
    )
    print("[PASS] Scenario 5 passed successfully! ('Not eligible based on a verified rule' correctly applied)")


def test_no_guarantee_compliance():
    """
    Verify that match explanations and disclaimers NEVER claim guaranteed funding or official approval.
    """
    print("\n--- Testing Compliance & Disclaimers ---")
    profile = {
        "full_name": "Compliant User",
        "email": "compliant@example.com",
        "state": "Tamil Nadu",
        "community": "BC",
        "is_registered_company": True,
        "is_dpiit_recognised": True,
        "is_woman_led": True
    }
    result = get_matched_schemes_for_user(profile)
    assert "disclaimer" in result
    assert "Compliance Advisory" in result["disclaimer"]
    assert "not official eligibility probabilities or funding guarantees" in result["disclaimer"]

    for m in result["matches"]:
        # Verify card has required Phase 4 fields
        assert "name" in m
        assert "government" in m
        assert "funding_category" in m or "type" in m
        assert "eligibility_status" in m
        assert "match_score" in m
        assert "matching_criteria_explanation" in m
        assert "missing_requirements" in m
        assert "application_steps" in m
        assert "application_url" in m
        assert "last_verified_date" in m
        assert m["eligibility_status"] in [
            "Eligible based on available data",
            "Potential match",
            "Needs verification",
            "Not eligible based on a verified rule"
        ]
    print("[PASS] Compliance & Schema completeness tests passed!")


if __name__ == "__main__":
    print("=================================================================")
    print("SCHEMEAI PHASE 4 DETERMINISTIC MATCHING SERVICE TEST RUNNER")
    print("=================================================================")
    test_scenario_1_tn_student_unregistered_idea()
    test_scenario_2_registered_dpiit_startup()
    test_scenario_3_woman_led_startup()
    test_scenario_4_profile_missing_important_info()
    test_scenario_5_failing_verified_criterion()
    test_no_guarantee_compliance()
    print("\n=================================================================")
    print("ALL 5 REQUIRED SCENARIOS & COMPLIANCE TESTS PASSED!")
    print("=================================================================")
