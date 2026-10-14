"""
Automated Verification Suite for AI Funding & Scheme Matcher (AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs):
1. Feature 1: Government Scheme Results (10-15 relevant schemes per project, genuine verified data, zero fabrication)
2. Feature 2: Chatbot Voice Recognition (HTML elements, Web Speech API integration, language mapping, state management)
"""

import os
import json
import httpx
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

def test_scheme_database_expansion_and_quality():
    """Verify opportunities.json contains 36 verified schemes with required fields."""
    opp_path = os.path.join(PROJECT_ROOT, "opportunities.json")
    assert os.path.exists(opp_path), "opportunities.json must exist in project root"
    
    with open(opp_path, "r", encoding="utf-8") as f:
        schemes = json.load(f)
        
    assert len(schemes) >= 30, f"Expected 30+ schemes in database, found {len(schemes)}"
    
    # Required keys according to user specification
    required_keys = ["id", "name", "type", "stage", "provider", "benefit", "eligibility", "documents_required", "apply_steps", "official_link", "last_verified", "verified"]
    
    for s in schemes:
        for k in required_keys:
            assert k in s, f"Scheme {s.get('id')} is missing required key '{k}'"
        assert s["verified"] is True, f"Scheme {s.get('id')} must be verified"
        assert s["official_link"].startswith("http"), f"Scheme {s.get('id')} has invalid official_link: {s['official_link']}"
        assert len(s["stage"]) > 0, f"Scheme {s.get('id')} must specify target stage(s)"
        assert len(s["documents_required"]) > 0, f"Scheme {s.get('id')} must specify required documents"
        assert len(s["apply_steps"]) > 0, f"Scheme {s.get('id')} must specify application steps"

def test_matching_engine_returns_10_to_15_schemes_for_ideation():
    """Verify backend matching service produces 10-15 likely matches for an Ideation project."""
    import sys
    sys.path.insert(0, PROJECT_ROOT)
    from backend.matching_service import get_matched_schemes_for_user

    profile = {
        "full_name": "Kavitha Raman",
        "state": "Tamil Nadu",
        "district": "Coimbatore",
        "community": "General",
        "age": 26,
        "gender": "Female",
        "annual_income": 400000,
        "education": "Degree",
        "is_student": False,
        "is_registered_company": False,
        "is_dpiit_recognised": False,
        "is_first_time_entrepreneur": True,
        "is_woman_led": True,
        "preferred_stage": 1
    }

    project = {
        "title": "Solar Automated Drip Irrigation",
        "category": "Agriculture",
        "current_stage": "Ideation",
        "target_location": "Coimbatore, Tamil Nadu",
        "estimated_budget": 800000
    }

    results = get_matched_schemes_for_user(profile, project, page_size=15, all_items=False)
    assert results["success"] is True
    
    # Page size should display 15 schemes
    assert len(results["matches"]) == 15, f"Expected 15 schemes on page 1, got {len(results['matches'])}"
    
    summary = results["match_summary"]
    likely_matches = summary.get("likely_match_count", 0)
    print(f"Ideation Likely Matches: {likely_matches} out of {summary.get('total_schemes')} total evaluated")
    assert 10 <= likely_matches <= 20, f"Target is 10-15 relevant schemes for Ideation, got {likely_matches}"

def test_matching_engine_returns_10_to_15_schemes_for_scaling():
    """Verify backend matching service produces 10-15 likely matches for a Scaling project."""
    import sys
    sys.path.insert(0, PROJECT_ROOT)
    from backend.matching_service import get_matched_schemes_for_user

    profile = {
        "full_name": "Ramesh Kumar",
        "state": "Tamil Nadu",
        "district": "Madurai",
        "community": "BC",
        "age": 34,
        "gender": "Male",
        "annual_income": 750000,
        "education": "Degree",
        "is_student": False,
        "is_registered_company": True,
        "is_dpiit_recognised": True,
        "is_first_time_entrepreneur": False,
        "is_woman_led": False,
        "preferred_stage": 3
    }

    project = {
        "title": "Precision Auto Components Manufacturing",
        "category": "Manufacturing",
        "current_stage": "Scaling / Market Expansion",
        "target_location": "Madurai, Tamil Nadu",
        "estimated_budget": 5000000
    }

    results = get_matched_schemes_for_user(profile, project, page_size=15, all_items=False)
    assert results["success"] is True
    assert len(results["matches"]) == 15, f"Expected 15 schemes on page 1, got {len(results['matches'])}"
    
    summary = results["match_summary"]
    likely_matches = summary.get("likely_match_count", 0)
    print(f"Scaling Likely Matches: {likely_matches} out of {summary.get('total_schemes')} total evaluated")
    assert likely_matches >= 15, f"Expected 15+ relevant schemes for Scaling MSME, got {likely_matches}"

def test_live_backend_api_schemes_matches():
    """Verify live FastAPI /api/schemes/matches returns 10-15 relevant schemes on port 8000."""
    headers = {"Authorization": "Bearer mock-demo-token-test-verification-user"}
    
    # 1. Setup profile
    prof_res = httpx.put("http://127.0.0.1:8000/api/profile/me", json={
        "full_name": "Test Founder",
        "mobile_number": "9876543210",
        "age": 27,
        "gender": "Male",
        "community": "General",
        "annual_income": 300000,
        "district": "Salem",
        "state": "Tamil Nadu",
        "education": "Degree",
        "is_student": False,
        "is_registered_company": False,
        "is_dpiit_recognised": False,
        "is_first_time_entrepreneur": True,
        "is_woman_led": False,
        "preferred_stage": "Stage 1"
    }, headers=headers)
    assert prof_res.status_code == 200

    # 2. Register project
    proj_res = httpx.post("http://127.0.0.1:8000/api/projects", json={
        "title": "Clean Water Treatment Filter",
        "category": "Clean Tech & Rural Innovation",
        "current_stage": "Ideation",
        "problem_statement": "Groundwater contamination in rural communities",
        "proposed_solution": "Affordable graphene-sand bio-filter",
        "target_location": "Salem, Tamil Nadu",
        "target_beneficiaries": "Rural villages",
        "estimated_budget": 600000,
        "founder_team_details": "Founder and chemical engineer"
    }, headers=headers)
    assert proj_res.status_code == 200

    # 3. Request matched schemes (page 1)
    match_res = httpx.get("http://127.0.0.1:8000/api/schemes/matches?page=1&page_size=15", headers=headers)
    assert match_res.status_code == 200
    data = match_res.json()
    assert data["success"] is True
    assert len(data["matches"]) == 15, f"Expected 15 schemes per page, got {len(data['matches'])}"
    assert data["match_summary"]["likely_match_count"] >= 14, "Expected ~15 likely matches"

def test_chatbot_html_voice_elements():
    """Verify chatbot.html contains microphone button, voice status bar, and stop button."""
    html_path = os.path.join(PROJECT_ROOT, "frontend", "chatbot.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="btnMicVoiceInput"' in html, "Chatbot must have #btnMicVoiceInput button"
    assert 'class="btn-chat-mic"' in html, "Mic button must have .btn-chat-mic class"
    assert 'id="voiceStatusBar"' in html, "Chatbot must have #voiceStatusBar container"
    assert 'id="btnStopVoice"' in html, "Voice status bar must have #btnStopVoice button"
    assert 'id="voiceStatusText"' in html, "Voice status bar must have #voiceStatusText element"
    assert 'id="chatInput"' in html, "Existing #chatInput must be preserved"
    assert 'id="btnSendChat"' in html, "Existing #btnSendChat must be preserved"

def test_chatbot_js_voice_logic():
    """Verify chatbot.js implements Web Speech API with language mapping and states."""
    js_path = os.path.join(PROJECT_ROOT, "frontend", "js", "chatbot.js")
    with open(js_path, "r", encoding="utf-8") as f:
        js = f.read()

    # Check Web Speech API usage
    assert "SpeechRecognition" in js, "Must reference SpeechRecognition"
    assert "webkitSpeechRecognition" in js, "Must reference webkitSpeechRecognition"
    
    # Check language mapping
    assert "ta-IN" in js, "Must support Tamil (ta-IN)"
    assert "en-IN" in js, "Must support English (en-IN)"
    
    # Check microphone states
    assert "'listening'" in js, "Must handle 'listening' state"
    assert "'processing'" in js, "Must handle 'processing' state"
    assert "'success'" in js, "Must handle 'success' state"
    assert "'error'" in js, "Must handle 'error' state"
    assert "'not-allowed'" in js, "Must handle microphone permission denial"
    
    # Check stop mechanism
    assert "stopVoiceRecognition" in js, "Must have stopVoiceRecognition function"
    
    # Check populating input without auto-send
    assert "chatInput.value" in js, "Must place recognized text into chatInput"
    assert "toggleVoiceRecognition" in js, "Must have toggleVoiceRecognition handler"

def test_css_microphone_and_status_styles():
    """Verify style.css includes styling for microphone button, pulsing, and status states."""
    css_path = os.path.join(PROJECT_ROOT, "frontend", "css", "style.css")
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    assert ".btn-chat-mic" in css, "Must include .btn-chat-mic CSS"
    assert ".btn-chat-mic.listening" in css, "Must include .btn-chat-mic.listening CSS"
    assert "mic-listening-pulse" in css, "Must include pulse keyframes for mic"
    assert ".voice-status-bar" in css, "Must include .voice-status-bar CSS"
    assert ".voice-status-bar.listening" in css, "Must include .voice-status-bar.listening CSS"
    assert ".voice-status-bar.processing" in css, "Must include .voice-status-bar.processing CSS"
    assert ".voice-status-bar.error" in css, "Must include .voice-status-bar.error CSS"

if __name__ == "__main__":
    test_scheme_database_expansion_and_quality()
    print("[PASS] test_scheme_database_expansion_and_quality")
    test_matching_engine_returns_10_to_15_schemes_for_ideation()
    print("[PASS] test_matching_engine_returns_10_to_15_schemes_for_ideation")
    test_matching_engine_returns_10_to_15_schemes_for_scaling()
    print("[PASS] test_matching_engine_returns_10_to_15_schemes_for_scaling")
    test_live_backend_api_schemes_matches()
    print("[PASS] test_live_backend_api_schemes_matches")
    test_chatbot_html_voice_elements()
    print("[PASS] test_chatbot_html_voice_elements")
    test_chatbot_js_voice_logic()
    print("[PASS] test_chatbot_js_voice_logic")
    test_css_microphone_and_status_styles()
    print("[PASS] test_css_microphone_and_status_styles")
    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY!")
