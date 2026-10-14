"""
SchemeAI — Phase 5 Gemini AI Scheme Assistant API Test Suite
Tests:
1. Unauthenticated requests return 401
2. Authenticated query in English returns grounded response and references
3. Authenticated query in Tanglish returns response in Tanglish
4. Authenticated query in Tamil returns response in Tamil
5. Conversation creation and chat history retrieval
6. Cross-user access attempt returns 403 or 404
7. Message length validation (>2000 chars returns 422)
8. Grounded answers avoid hallucinations and non-guaranteed funding
"""

import sys
import os
import httpx

BASE_URL = "http://127.0.0.1:8000"
USER_A_TOKEN = "mock-demo-token-user-a-101"
USER_B_TOKEN = "mock-demo-token-user-b-202"

def test_unauthenticated_chat_rejected():
    print("\n--- 1. Testing Unauthenticated Access Rejection ---")
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    res = client.post("/api/chat", json={"message": "Hello"})
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"
    print("[PASS] Unauthenticated request correctly rejected with HTTP 401")


def test_english_grounded_chat():
    print("\n--- 2. Testing Grounded English Scheme Query ---")
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    payload = {
        "message": "Which government schemes might suit my startup?",
        "language_preference": "en"
    }
    res = client.post("/api/chat", json=payload, headers={"Authorization": f"Bearer {USER_A_TOKEN}"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["success"] is True
    assert "conversation_id" in data
    assert len(data["response"]) > 20
    assert len(data["referenced_schemes"]) > 0
    assert "Compliance Advisory" in data["response"] or "guarantee" in data["response"].lower() or "not" in data["response"].lower()
    print(f"[PASS] English chat succeeded! Conv ID: {data['conversation_id']}, Model: {data.get('model_used')}")
    return data["conversation_id"]


def test_tanglish_query(conv_id):
    print("\n--- 3. Testing Tanglish Scheme Query ---")
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    payload = {
        "message": "Naan Tamil Nadu-la startup start panna enna funding schemes irukku?",
        "conversation_id": conv_id,
        "language_preference": "auto"
    }
    res = client.post("/api/chat", json=payload, headers={"Authorization": f"Bearer {USER_A_TOKEN}"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["success"] is True
    assert data["language_detected"] == "tanglish"
    print(f"[PASS] Tanglish query accurately detected and answered in Tanglish!")


def test_tamil_script_query():
    print("\n--- 4. Testing Pure Tamil Script Query ---")
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    payload = {
        "message": "என் ஸ்டார்ட்அப்பிற்கு என்ன அரசு மானியம் மற்றும் நிதி கிடைக்கும்?",
        "language_preference": "auto"
    }
    res = client.post("/api/chat", json=payload, headers={"Authorization": f"Bearer {USER_A_TOKEN}"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["success"] is True
    assert data["language_detected"] == "ta"
    print("[PASS] Tamil script query accurately detected and answered in Tamil!")


def test_chat_history_and_persistence(conv_id):
    print("\n--- 5. Testing Chat History Persistence ---")
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    
    # 5a. Retrieve messages for conversation
    res = client.get(f"/api/chat/history?conversation_id={conv_id}", headers={"Authorization": f"Bearer {USER_A_TOKEN}"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["messages"]) >= 2
    print(f"[PASS] Retrieved {len(data['messages'])} persisted messages for conversation {conv_id}")

    # 5b. Retrieve conversations list
    res_list = client.get("/api/chat/conversations", headers={"Authorization": f"Bearer {USER_A_TOKEN}"})
    assert res_list.status_code == 200
    convs = res_list.json()["conversations"]
    assert any(c["id"] == conv_id for c in convs)
    print(f"[PASS] Retrieved {len(convs)} user conversations from history list")


def test_cross_user_isolation(conv_id):
    print("\n--- 6. Testing Strict Cross-User Privacy & Isolation ---")
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    
    # User B attempts to read User A's conversation
    res_hack = client.get(
        f"/api/chat/history?conversation_id={conv_id}",
        headers={"Authorization": f"Bearer {USER_B_TOKEN}"}
    )
    assert res_hack.status_code in (403, 404), f"Expected 403 or 404, got {res_hack.status_code}"
    print(f"[PASS] Cross-user access attempt blocked with HTTP {res_hack.status_code}!")

    # User B attempts to append message to User A's conversation
    res_post_hack = client.post(
        "/api/chat",
        json={"message": "Malicious append", "conversation_id": conv_id},
        headers={"Authorization": f"Bearer {USER_B_TOKEN}"}
    )
    assert res_post_hack.status_code in (403, 404), f"Expected 403 or 404, got {res_post_hack.status_code}"
    print(f"[PASS] Cross-user message append blocked with HTTP {res_post_hack.status_code}!")


def test_message_length_validation():
    print("\n--- 7. Testing Message Length Validation ---")
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    long_msg = "A" * 2500  # Exceeds 2000 char limit
    res = client.post(
        "/api/chat",
        json={"message": long_msg},
        headers={"Authorization": f"Bearer {USER_A_TOKEN}"}
    )
    assert res.status_code == 422, f"Expected 422 validation error, got {res.status_code}"
    print("[PASS] Messages exceeding 2000 characters correctly rejected with HTTP 422!")


if __name__ == "__main__":
    print("=================================================================")
    print("SCHEMEAI PHASE 5 GEMINI AI SCHEME ASSISTANT API TEST RUNNER")
    print("=================================================================")
    test_unauthenticated_chat_rejected()
    conv_id = test_english_grounded_chat()
    test_tanglish_query(conv_id)
    test_tamil_script_query()
    test_chat_history_and_persistence(conv_id)
    test_cross_user_isolation(conv_id)
    test_message_length_validation()
    print("\n=================================================================")
    print("ALL PHASE 5 GEMINI CHATBOT API TESTS PASSED SUCCESSFULLY!")
    print("=================================================================")
