"""
SchemeAI — Phase 6 Automated API Integration Test Suite
Tests:
- Scheme Application Roadmap retrieval and step progress persistence
- Document Readiness Checklist retrieval and item status persistence
- Strict User Ownership and Cross-User Data Isolation
- Eligibility Gap Analysis against verified scheme rules
- Missing profile data handling (never assumes eligible)
- Validation errors (invalid status, nonexistent scheme, invalid step/doc IDs)
- Unauthenticated rejection (HTTP 401)
"""

import sys
import uuid
import requests

BASE_URL = "http://127.0.0.1:8000"

RUN_ID = str(uuid.uuid4())[:8]
USER_A_TOKEN = f"mock-demo-token-user-alice-{RUN_ID}"
USER_B_TOKEN = f"mock-demo-token-user-bob-{RUN_ID}"

AUTH_A = {"Authorization": f"Bearer {USER_A_TOKEN}"}
AUTH_B = {"Authorization": f"Bearer {USER_B_TOKEN}"}

print("=" * 65)
print("SCHEMEAI PHASE 6 ROADMAP, CHECKLIST & GAP ANALYSIS TEST RUNNER")
print("=" * 65)


# ---------------------------------------------------------------------------
# TEST 1: Unauthenticated Requests Rejection
# ---------------------------------------------------------------------------
print("\n--- 1. Testing Unauthenticated Access Rejection ---")
res = requests.get(f"{BASE_URL}/api/schemes/sisfs/roadmap")
assert res.status_code == 401, f"Expected 401, got {res.status_code}"

res = requests.get(f"{BASE_URL}/api/schemes/sisfs/checklist")
assert res.status_code == 401, f"Expected 401, got {res.status_code}"

res = requests.get(f"{BASE_URL}/api/schemes/sisfs/gap-analysis")
assert res.status_code == 401, f"Expected 401, got {res.status_code}"
print("[PASS] All Phase 6 endpoints strictly reject unauthenticated requests with HTTP 401")


# ---------------------------------------------------------------------------
# TEST 2: Nonexistent Scheme ID Handling
# ---------------------------------------------------------------------------
print("\n--- 2. Testing Nonexistent Scheme Rejection ---")
res = requests.get(f"{BASE_URL}/api/schemes/fake_nonexistent_scheme/roadmap", headers=AUTH_A)
assert res.status_code == 404, f"Expected 404, got {res.status_code}"

res = requests.get(f"{BASE_URL}/api/schemes/fake_nonexistent_scheme/checklist", headers=AUTH_A)
assert res.status_code == 404, f"Expected 404, got {res.status_code}"

res = requests.get(f"{BASE_URL}/api/schemes/fake_nonexistent_scheme/gap-analysis", headers=AUTH_A)
assert res.status_code == 404, f"Expected 404, got {res.status_code}"
print("[PASS] Nonexistent scheme IDs correctly return HTTP 404")


# ---------------------------------------------------------------------------
# TEST 3: Roadmap Retrieval & Progress Persistence for User A
# ---------------------------------------------------------------------------
print("\n--- 3. Testing Roadmap Retrieval & Progress Updates ---")
# Initial fetch
res = requests.get(f"{BASE_URL}/api/schemes/sisfs/roadmap", headers=AUTH_A)
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
data = res.json()["roadmap"]
assert data["scheme_id"] == "sisfs"
assert data["total_steps"] == 4
assert data["completed_steps"] == 0
assert data["progress_percentage"] == 0
assert data["is_link_verified"] is True
assert data["official_link"] == "https://seedfund.startupindia.gov.in"
print(f"[PASS] Initial SISFS roadmap loaded: {data['total_steps']} verified steps, 0% complete")

# Update step_1 to 'In progress'
res = requests.put(
    f"{BASE_URL}/api/schemes/sisfs/roadmap/progress",
    headers=AUTH_A,
    json={"step_id": "step_1", "status": "In progress"}
)
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
r_data = res.json()["roadmap"]
assert r_data["in_progress_steps"] == 1
assert r_data["overall_status"] == "In progress"

# Update step_1 to 'Completed' and step_2 to 'Completed'
requests.put(
    f"{BASE_URL}/api/schemes/sisfs/roadmap/progress",
    headers=AUTH_A,
    json={"step_id": "step_1", "status": "Completed"}
)
res = requests.put(
    f"{BASE_URL}/api/schemes/sisfs/roadmap/progress",
    headers=AUTH_A,
    json={"step_id": "step_2", "status": "Completed"}
)
assert res.status_code == 200
r_data = res.json()["roadmap"]
assert r_data["completed_steps"] == 2
assert r_data["progress_percentage"] == 50
print("[PASS] User A updated 2 steps; progress percentage verified at 50%")


# ---------------------------------------------------------------------------
# TEST 4: Invalid Status & Invalid Step ID Validation
# ---------------------------------------------------------------------------
print("\n--- 4. Testing Roadmap Input Validation ---")
# Invalid status
res = requests.put(
    f"{BASE_URL}/api/schemes/sisfs/roadmap/progress",
    headers=AUTH_A,
    json={"step_id": "step_1", "status": "Finished"}
)
assert res.status_code == 422, f"Expected 422 for invalid status, got {res.status_code}"

# Invalid step_id
res = requests.put(
    f"{BASE_URL}/api/schemes/sisfs/roadmap/progress",
    headers=AUTH_A,
    json={"step_id": "step_999", "status": "Completed"}
)
assert res.status_code == 422, f"Expected 422 for invalid step_id, got {res.status_code}"
print("[PASS] Invalid statuses and out-of-range step IDs correctly rejected with HTTP 422")


# ---------------------------------------------------------------------------
# TEST 5: Cross-User Data Isolation (User B cannot see User A's progress)
# ---------------------------------------------------------------------------
print("\n--- 5. Testing Cross-User Data Isolation ---")
res_b = requests.get(f"{BASE_URL}/api/schemes/sisfs/roadmap", headers=AUTH_B)
assert res_b.status_code == 200
b_data = res_b.json()["roadmap"]
assert b_data["completed_steps"] == 0, f"User B should see 0 completed, saw {b_data['completed_steps']}"
assert b_data["progress_percentage"] == 0
assert b_data["steps"][0]["status"] == "Not started"

# Confirm User A still sees 50%
res_a = requests.get(f"{BASE_URL}/api/schemes/sisfs/roadmap", headers=AUTH_A)
assert res_a.json()["roadmap"]["progress_percentage"] == 50
print("[PASS] Strict user isolation verified: User B sees independent 0% state while User A has 50%")


# ---------------------------------------------------------------------------
# TEST 6: Document Checklist Retrieval & Persistence
# ---------------------------------------------------------------------------
print("\n--- 6. Testing Document Readiness Checklist ---")
res = requests.get(f"{BASE_URL}/api/schemes/tanseed/checklist", headers=AUTH_A)
assert res.status_code == 200
cl_data = res.json()["checklist"]
assert cl_data["scheme_id"] == "tanseed"
assert cl_data["total_items"] == 4
assert "StartupTN" in cl_data["items"][0]["name"]
assert "privacy_notice" in cl_data
print(f"[PASS] TANSEED checklist loaded with {cl_data['total_items']} verified documents and privacy notice")

# Update doc_1 to 'Ready'
res = requests.put(
    f"{BASE_URL}/api/schemes/tanseed/checklist/progress",
    headers=AUTH_A,
    json={"item_id": "doc_1", "status": "Ready"}
)
assert res.status_code == 200
up_cl = res.json()["checklist"]
assert up_cl["ready_count"] == 1
assert up_cl["readiness_percentage"] == 25

# Update doc_2 to 'Needs attention'
res = requests.put(
    f"{BASE_URL}/api/schemes/tanseed/checklist/progress",
    headers=AUTH_A,
    json={"item_id": "doc_2", "status": "Needs attention"}
)
assert res.status_code == 200
up_cl2 = res.json()["checklist"]
assert up_cl2["needs_attention_count"] == 1

# Check User B checklist is independent
res_b = requests.get(f"{BASE_URL}/api/schemes/tanseed/checklist", headers=AUTH_B)
assert res_b.json()["checklist"]["ready_count"] == 0
print("[PASS] Document checklist status persisted and isolated between users")


# ---------------------------------------------------------------------------
# TEST 7: Eligibility Gap Analysis Logic
# ---------------------------------------------------------------------------
print("\n--- 7. Testing Eligibility Gap Analysis ---")

# Setup Profile for User A: student, unregistered, Tamil Nadu, SC
profile_payload = {
    "full_name": "Alice Innovator",
    "email": "alice@schemeai.demo",
    "age": 22,
    "gender": "Female",
    "community": "SC",
    "state": "Tamil Nadu",
    "education": "Degree",
    "is_student": True,
    "is_registered_company": False,
    "is_dpiit_recognised": False,
    "is_first_time_entrepreneur": True,
    "existing_govt_funding_lakhs": 0.0
}
res = requests.put(f"{BASE_URL}/api/profile/me", headers=AUTH_A, json=profile_payload)
assert res.status_code == 200

# Case A: NIDHI-PRAYAS (Allows student innovators, physical prototypes)
res = requests.get(f"{BASE_URL}/api/schemes/nidhi_prayas/gap-analysis", headers=AUTH_A)
assert res.status_code == 200
gap_prayas = res.json()["gap_analysis"]
assert gap_prayas["scheme_id"] == "nidhi_prayas"
# Check satisfied requirements
satisfied_titles = [s["criterion"] for s in gap_prayas["satisfied_requirements"]]
assert "Individual / Innovator Open Access" in satisfied_titles
assert "Age Eligibility" in satisfied_titles
# Check institutional NOC required
verif_bodies = [v["verification_body"] for v in gap_prayas["needs_official_verification"]]
assert any("PRAYAS" in b or "Institution" in b for b in verif_bodies)
assert "disclaimer" in gap_prayas
print("[PASS] Gap analysis on NIDHI-PRAYAS correctly verified individual innovator access & student NOC requirement")

# Case B: SISFS (Requires registered company and DPIIT)
res = requests.get(f"{BASE_URL}/api/schemes/sisfs/gap-analysis", headers=AUTH_A)
assert res.status_code == 200
gap_sisfs = res.json()["gap_analysis"]
assert gap_sisfs["verdict_status"] == "Unsatisfied"
unsat_criteria = [u["criterion"] for u in gap_sisfs["unsatisfied_requirements"]]
assert "Company Incorporation Requirement" in unsat_criteria
assert any("Incorporate" in step for step in gap_sisfs["practical_next_steps"])
print("[PASS] Gap analysis on SISFS correctly identified unregistered company gap & recommended incorporation")

# Case C: Missing community profile data against TN SC/ST Fund
# Create User C with missing community
USER_C_TOKEN = "mock-demo-token-user-charlie-303"
AUTH_C = {"Authorization": f"Bearer {USER_C_TOKEN}"}
profile_c = dict(profile_payload)
profile_c["community"] = None
profile_c["email"] = "charlie@schemeai.demo"
# Save User C profile without community
res = requests.put(f"{BASE_URL}/api/profile/me", headers=AUTH_C, json={
    "full_name": "Charlie Founder",
    "email": "charlie@schemeai.demo",
    "state": "Tamil Nadu",
    "is_student": False,
    "is_registered_company": True
})
assert res.status_code == 200

res = requests.get(f"{BASE_URL}/api/schemes/tn_scst_fund/gap-analysis", headers=AUTH_C)
assert res.status_code == 200
gap_scst = res.json()["gap_analysis"]
# Must flag as Missing Information, NEVER assume eligible!
missing_fields = [m["field_name"] for m in gap_scst["missing_information"]]
assert "community" in missing_fields
assert gap_scst["verdict_status"] == "Unsatisfied" or gap_scst["verdict_status"] == "Missing Data"
print("[PASS] Missing community profile data correctly flagged under 'missing_information', never assumed eligible")

print("\n" + "=" * 65)
print("ALL PHASE 6 BACKEND API TESTS PASSED SUCCESSFULLY!")
print("=" * 65)
