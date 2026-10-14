"""
SchemeAI — Phase 4 FastAPI Endpoints Integration Tests
Tests:
- GET /api/schemes (with filtering)
- GET /api/schemes/matches (auth enforced, verified user ID, missing profile 404)
- GET /api/schemes/{scheme_id} (valid ID, invalid ID, personalized evaluation)
"""

import sys
import os
import httpx

BASE_URL = "http://127.0.0.1:8000"
DEMO_TOKEN = "mock-demo-token-demo-entrepreneur-001"

def test_schemes_catalog():
    print("\n--- Testing GET /api/schemes ---")
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    
    # 1. Catalog list
    res = client.get("/api/schemes")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["success"] is True
    assert data["count"] >= 9
    print(f"[PASS] /api/schemes returned {data['count']} schemes")

    # 2. Filter by funding type
    res_ft = client.get("/api/schemes?funding_type=grant")
    assert res_ft.status_code == 200
    grants = res_ft.json()["schemes"]
    assert len(grants) > 0
    print(f"[PASS] Filter by funding_type=grant returned {len(grants)} schemes")

    # 3. Filter by government scope
    res_gov = client.get("/api/schemes?government=Tamil Nadu")
    assert res_gov.status_code == 200
    tn_schemes = res_gov.json()["schemes"]
    assert len(tn_schemes) > 0
    print(f"[PASS] Filter by government=Tamil Nadu returned {len(tn_schemes)} schemes")

    # 4. Search query
    res_q = client.get("/api/schemes?search=nidhi")
    assert res_q.status_code == 200
    q_schemes = res_q.json()["schemes"]
    assert any("nidhi" in s["name"].lower() for s in q_schemes)
    print(f"[PASS] Search query search=nidhi returned {len(q_schemes)} schemes")


def test_schemes_matches_security_and_flow():
    print("\n--- Testing GET /api/schemes/matches Security & Logic ---")
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    # 1. Unauthenticated request must return 401
    res_unauth = client.get("/api/schemes/matches")
    assert res_unauth.status_code == 401, f"Expected 401, got {res_unauth.status_code}"
    print("[PASS] Unauthenticated call correctly rejected with HTTP 401")

    # 2. Invalid/Nonexistent user profile must return 404
    res_noprofile = client.get(
        "/api/schemes/matches",
        headers={"Authorization": "Bearer mock-demo-token-nonexistent-user-999"}
    )
    assert res_noprofile.status_code == 404, f"Expected 404, got {res_noprofile.status_code}"
    print("[PASS] Nonexistent profile correctly rejected with HTTP 404")

    # 3. Authenticated request for existing profile returns matches
    res_auth = client.get(
        "/api/schemes/matches",
        headers={"Authorization": f"Bearer {DEMO_TOKEN}"}
    )
    assert res_auth.status_code == 200, f"Expected 200, got {res_auth.status_code}: {res_auth.text}"
    matches_data = res_auth.json()
    assert matches_data["success"] is True
    assert "match_summary" in matches_data
    assert "profile_summary" in matches_data
    assert "disclaimer" in matches_data
    assert len(matches_data["matches"]) >= 9
    print(f"[PASS] /api/schemes/matches returned {len(matches_data['matches'])} evaluated schemes")

    # 4. Filter matches by status
    res_filter = client.get(
        "/api/schemes/matches?eligibility_status=Eligible",
        headers={"Authorization": f"Bearer {DEMO_TOKEN}"}
    )
    assert res_filter.status_code == 200
    assert len(res_filter.json()["matches"]) > 0
    print("[PASS] Filtered matches by eligibility_status works")


def test_scheme_detail_endpoint():
    print("\n--- Testing GET /api/schemes/{scheme_id} ---")
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    # 1. Valid scheme ID without auth
    res = client.get("/api/schemes/nidhi_prayas")
    assert res.status_code == 200
    data = res.json()
    assert data["scheme"]["name"] == "NIDHI-PRAYAS"
    print("[PASS] /api/schemes/nidhi_prayas returns verified details")

    # 2. Valid scheme ID with auth provides personalized evaluation
    res_auth = client.get(
        "/api/schemes/nidhi_prayas",
        headers={"Authorization": f"Bearer {DEMO_TOKEN}"}
    )
    assert res_auth.status_code == 200
    data_auth = res_auth.json()
    assert data_auth["personalized_evaluation"] is not None
    assert "match_score" in data_auth["personalized_evaluation"]
    print(f"[PASS] Personalized score computed: {data_auth['personalized_evaluation']['match_score']}%")

    # 3. Invalid scheme ID returns 404
    res_404 = client.get("/api/schemes/nonexistent_scheme_xyz")
    assert res_404.status_code == 404
    print("[PASS] Nonexistent scheme ID returns HTTP 404")


if __name__ == "__main__":
    print("=================================================================")
    print("SCHEMEAI PHASE 4 FASTAPI ENDPOINTS INTEGRATION TEST RUNNER")
    print("=================================================================")
    test_schemes_catalog()
    test_schemes_matches_security_and_flow()
    test_scheme_detail_endpoint()
    print("\n=================================================================")
    print("ALL PHASE 4 BACKEND FASTAPI ENDPOINT TESTS PASSED!")
    print("=================================================================")
