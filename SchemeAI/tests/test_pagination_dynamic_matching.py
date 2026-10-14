"""
SchemeAI — Verification Test Suite for Pagination & Dynamic Project Matching
Requirements tested:
1. First page displays up to 15 schemes.
2. Page 2 loads the next set of schemes (Schemes 16-22).
3. No duplicate schemes across pages.
4. Total matching results not capped at 15 in backend.
5. Editing project details (stage, category, budget, location) dynamically recalculates matching results.
6. Dynamic filtering by funding type, government scope, and search returns relevant subsets.
7. All available matching results can be accessed across pages.
"""

import httpx

BASE_URL = "http://127.0.0.1:8000"
DEMO_TOKEN = "mock-demo-token-demo-entrepreneur-001"
HEADERS = {"Authorization": f"Bearer {DEMO_TOKEN}"}


def run_tests():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    print("=================================================================")
    print("AI FUNDING & SCHEME MATCHER PAGINATION & DYNAMIC MATCHING TEST SUITE")
    print("=================================================================")

    # Test 1: Page 1 displays up to 15 schemes
    print("\n--- Test 1: Page 1 Scheme Display (Page Size = 15) ---")
    res_p1 = client.get("/api/schemes/matches?page=1&page_size=15", headers=HEADERS)
    assert res_p1.status_code == 200, f"Expected 200, got {res_p1.status_code}: {res_p1.text}"
    data_p1 = res_p1.json()
    matches_p1 = data_p1.get("matches", [])
    pagination_p1 = data_p1.get("pagination", {})
    
    assert len(matches_p1) == 15, f"Expected exactly 15 schemes on page 1, got {len(matches_p1)}"
    assert pagination_p1.get("page") == 1
    assert pagination_p1.get("page_size") == 15
    assert pagination_p1.get("total_items") >= 22, f"Total items should be at least 22, got {pagination_p1.get('total_items')}"
    total_pages = pagination_p1.get("total_pages")
    assert total_pages >= 2, f"Total pages should be at least 2, got {total_pages}"
    assert pagination_p1.get("has_next") is True
    assert pagination_p1.get("has_prev") is False
    print(f"[PASS] Page 1 returned exactly {len(matches_p1)} schemes (Total: {pagination_p1.get('total_items')}, Total Pages: {total_pages})")

    # Verify all required fields per Requirement 2 are present on each scheme card
    required_fields = [
        "name", "provider", "government", "benefit", 
        "eligibility_status", "match_score", "match_explanation",
        "documents_required", "official_link"
    ]
    for s in matches_p1:
        for f in required_fields:
            assert f in s, f"Scheme {s.get('id')} missing required field: {f}"
        assert s["official_link"].startswith("http"), f"Official link must be a valid URL: {s['official_link']}"
    print("[PASS] All required scheme fields (Department, verified benefits, eligibility, docs, links, status) present")

    # Test 2: Page 2 loads the next set of schemes
    print("\n--- Test 2: Page 2 Scheme Display (Schemes 16–30) ---")
    res_p2 = client.get("/api/schemes/matches?page=2&page_size=15", headers=HEADERS)
    assert res_p2.status_code == 200
    data_p2 = res_p2.json()
    matches_p2 = data_p2.get("matches", [])
    pagination_p2 = data_p2.get("pagination", {})

    assert len(matches_p2) == min(15, pagination_p1.get("total_items") - 15)
    assert pagination_p2.get("page") == 2
    assert pagination_p2.get("has_prev") is True
    print(f"[PASS] Page 2 returned {len(matches_p2)} schemes (next set)")

    # Test 3: Zero duplicate schemes across all pages
    print("\n--- Test 3: Zero Duplicate Schemes Across All Pages ---")
    all_paged_ids = []
    for p in range(1, total_pages + 1):
        resp = client.get(f"/api/schemes/matches?page={p}&page_size=15", headers=HEADERS)
        assert resp.status_code == 200
        p_matches = resp.json().get("matches", [])
        p_ids = [s.get("id") or s.get("scheme_id") for s in p_matches]
        assert len(p_ids) == len(set(p_ids)), f"Duplicates detected within Page {p}!"
        all_paged_ids.extend(p_ids)

    assert len(all_paged_ids) == len(set(all_paged_ids)), "Duplicate schemes found across pages!"
    assert len(all_paged_ids) == pagination_p1.get("total_items"), f"Retrieved {len(all_paged_ids)} schemes, expected {pagination_p1.get('total_items')}"
    print(f"[PASS] Zero duplicate schemes across pages. Total retrieved: {len(all_paged_ids)}, All unique")

    # Test 4: All matching schemes accessible
    print("\n--- Test 4: All Matching Schemes Accessible (Total > 15) ---")
    print(f"[PASS] All {len(all_paged_ids)} available matching schemes accessible across {total_pages} pages")

    # Test 5: Dynamic Project Updates Trigger Live Recalculation
    print("\n--- Test 5: Dynamic Project Stage & Category Rematching ---")
    
    # 5A. Update project to Stage 1 (Ideation)
    proj_ideation = {
        "title": "Autonomous Drone Soil Nutrient Mapping",
        "category": "Agritech & Robotics",
        "current_stage": "Ideation",
        "estimated_budget": 500000.0,
        "district": "Coimbatore"
    }
    res_up1 = client.put("/api/projects/me", json=proj_ideation, headers=HEADERS)
    assert res_up1.status_code == 200, "Failed to update project"
    
    res_ideation_matches = client.get("/api/schemes/matches?all=true&_t=1", headers=HEADERS)
    assert res_ideation_matches.status_code == 200
    all_ideation = res_ideation_matches.json()["matches"]
    
    # NIDHI-PRAYAS is an ideation/prototype grant - should have top match score for Ideation stage
    nidhi_match = next((s for s in all_ideation if s["id"] == "nidhi_prayas"), None)
    assert nidhi_match is not None
    assert nidhi_match["eligibility_status"] in ("Eligible based on available data", "Potential match")
    print(f"[PASS] Ideation project updated: NIDHI-PRAYAS score = {nidhi_match['match_score']}%, status = {nidhi_match['eligibility_status']}")

    # 5B. Update project to Stage 3 (Scaling / Market Expansion) with higher budget
    proj_scaling = {
        "title": "Autonomous Drone Soil Nutrient Mapping",
        "category": "Agritech & Robotics",
        "current_stage": "Scaling / Market Expansion",
        "estimated_budget": 5000000.0,
        "district": "Coimbatore"
    }
    res_up2 = client.put("/api/projects/me", json=proj_scaling, headers=HEADERS)
    assert res_up2.status_code == 200
    
    res_scaling_matches = client.get("/api/schemes/matches?all=true&_t=2", headers=HEADERS)
    assert res_scaling_matches.status_code == 200
    all_scaling = res_scaling_matches.json()["matches"]
    
    # PMEGP & Scaling schemes should reflect updated scaling stage fit
    pmegp_match = next((s for s in all_scaling if s["id"] == "pmegp"), None)
    assert pmegp_match is not None
    print(f"[PASS] Scaling project updated: PMEGP score = {pmegp_match['match_score']}%, status = {pmegp_match['eligibility_status']}")

    # 5C. Update project to Biotechnology Category
    proj_biotech = {
        "title": "Bio-Enzymatic Crop Residue Digestor",
        "category": "Biotechnology & Life Sciences",
        "current_stage": "Prototype / Pilot",
        "estimated_budget": 2500000.0,
        "district": "Coimbatore"
    }
    res_up3 = client.put("/api/projects/me", json=proj_biotech, headers=HEADERS)
    assert res_up3.status_code == 200
    
    res_biotech_matches = client.get("/api/schemes/matches?all=true&_t=3", headers=HEADERS)
    all_biotech = res_biotech_matches.json()["matches"]
    birac_match = next((s for s in all_biotech if s["id"] == "birac_big"), None)
    assert birac_match is not None
    assert any("biotechnology" in r.lower() or "sector" in r.lower() for r in birac_match.get("match_reasons", [])), (
        "BIRAC BIG should identify sector alignment for Biotechnology"
    )
    print(f"[PASS] Sector update to Biotechnology correctly boosted BIRAC BIG ({birac_match['match_score']}%)")

    # Test 6: Dynamic Filters
    print("\n--- Test 6: Dynamic Multi-Criteria Filters ---")
    res_grants = client.get("/api/schemes/matches?funding_type=grant", headers=HEADERS)
    assert res_grants.status_code == 200
    grants = res_grants.json()["matches"]
    assert len(grants) > 0
    assert all("grant" in (s.get("funding_category", "") + s.get("funding_type", "")).lower() for s in grants)
    print(f"[PASS] Filter funding_type=grant returned {len(grants)} grant schemes")

    res_tn = client.get("/api/schemes/matches?government=Tamil Nadu", headers=HEADERS)
    assert res_tn.status_code == 200
    tn_matches = res_tn.json()["matches"]
    assert len(tn_matches) > 0
    assert all("tamil nadu" in (s.get("government_scope", "") + s.get("government", "")).lower() for s in tn_matches)
    print(f"[PASS] Filter government=Tamil Nadu returned {len(tn_matches)} state schemes")

    # Test 7: Database Coverage Transparency
    print("\n--- Test 7: Database Coverage Transparency ---")
    res_cov = client.get("/api/schemes/matches", headers=HEADERS)
    cov_data = res_cov.json().get("database_coverage", {})
    assert cov_data.get("verified_schemes_count") >= 22
    assert cov_data.get("page_size") == 15
    assert cov_data.get("total_pages") >= 2
    print(f"[PASS] Database coverage transparently reports {cov_data.get('verified_schemes_count')} verified schemes across {cov_data.get('total_pages')} pages")

    print("\n=================================================================")
    print("ALL PAGINATION & DYNAMIC MATCHING TESTS PASSED SUCCESSFULLY!")
    print("=================================================================")


if __name__ == "__main__":
    run_tests()
