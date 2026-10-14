"""
AI Funding & Scheme Matcher Backend — Phase 1
Smart India Hackathon: AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs
Tech Stack: Python FastAPI, Supabase PostgreSQL, Supabase Auth
"""

import os
import re
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone
import httpx
import jwt
from dotenv import load_dotenv

# Ensure environment is loaded from backend/.env or root .env
_env_candidates = [
    os.path.join(os.path.dirname(__file__), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
    os.path.join(os.getcwd(), ".env")
]
for _p in _env_candidates:
    if os.path.exists(_p):
        load_dotenv(_p, override=True)
        break
else:
    load_dotenv(override=True)

from fastapi import FastAPI, Depends, HTTPException, Header, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

try:
    from matching_service import (
        load_all_schemes,
        get_matched_schemes_for_user,
        get_scheme_by_id,
        evaluate_scheme_for_profile
    )
    from gemini_service import (
        generate_grounded_chat_response,
        detect_language
    )
    from roadmap_service import (
        find_scheme_by_id,
        build_scheme_roadmap,
        build_scheme_checklist,
        perform_eligibility_gap_analysis,
        VALID_ROADMAP_STATUSES,
        VALID_CHECKLIST_STATUSES
    )
except ImportError:
    from backend.matching_service import (
        load_all_schemes,
        get_matched_schemes_for_user,
        get_scheme_by_id,
        evaluate_scheme_for_profile
    )
    from backend.gemini_service import (
        generate_grounded_chat_response,
        detect_language
    )
    from backend.roadmap_service import (
        find_scheme_by_id,
        build_scheme_roadmap,
        build_scheme_checklist,
        perform_eligibility_gap_analysis,
        VALID_ROADMAP_STATUSES,
        VALID_CHECKLIST_STATUSES
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("schemeai_backend")

# Load environment variables
load_dotenv()

# Configuration from environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
FRONTEND_ORIGINS_RAW = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000"
)
ALLOWED_ORIGINS = [orig.strip() for orig in FRONTEND_ORIGINS_RAW.split(",") if orig.strip()]
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Initialize FastAPI Application
app = FastAPI(
    title="AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs API (AI Funding & Scheme Matcher)",
    description="Backend service for AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs (AI Funding & Scheme Matcher): Authentication verification, affirmative profile management, deterministic scheme matching, and health monitoring.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware Setup
# Restricts access to configured local frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Maximum allowed request body size: 1 MB (1,048,576 bytes) to prevent DoS
MAX_REQUEST_BODY_BYTES = 1024 * 1024

@app.middleware("http")
async def limit_request_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_BODY_BYTES:
                return JSONResponse(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    content={"detail": f"Request payload exceeds the maximum allowed size of {MAX_REQUEST_BODY_BYTES} bytes."}
                )
        except ValueError:
            pass
    return await call_next(request)


# ============================================================================
# Pydantic Request & Response Models
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    timestamp: str
    environment: str
    supabase_configured: bool
    cors_allowed_origins: List[str]


class ProfileBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150, description="Full legal name")
    email: str = Field(..., description="Registered email address")
    mobile_number: Optional[str] = Field(None, description="10-digit Indian mobile number")
    age: Optional[int] = Field(None, ge=18, le=120, description="Age in years (18-120)")
    gender: Optional[str] = Field(None, description="Gender identity")
    community: Optional[str] = Field(None, description="Community: OC, BC, MBC, SC, ST, General, Other")
    annual_income: Optional[float] = Field(None, ge=0, description="Annual family income in INR")
    district: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    education: Optional[str] = Field(None, description="Degree, Diploma, ITI, Other")
    is_student: bool = Field(default=False)
    is_registered_company: bool = Field(default=False)
    is_dpiit_recognised: bool = Field(default=False)
    existing_govt_funding_lakhs: float = Field(default=0.0, ge=0, description="Prior funding received in lakhs")
    is_first_time_entrepreneur: bool = Field(default=True)
    is_woman_led: bool = Field(default=False)
    preferred_stage: str = Field(default="Let AI Suggest")

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() != "":
            cleaned = re.sub(r"\D", "", v)
            if len(cleaned) != 10:
                raise ValueError("Mobile number must be exactly 10 digits")
            return cleaned
        return None

    @field_validator("community")
    @classmethod
    def validate_community(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"OC", "BC", "MBC", "SC", "ST", "General", "Other"}
        if v and v not in allowed:
            raise ValueError(f"Community must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("education")
    @classmethod
    def validate_education(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"Degree", "Diploma", "ITI", "Other"}
        if v and v not in allowed:
            raise ValueError(f"Education must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("preferred_stage")
    @classmethod
    def validate_stage(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"Stage 1", "Stage 2", "Stage 3", "Let AI Suggest"}
        if v and v not in allowed:
            raise ValueError(f"Stage must be one of: {', '.join(sorted(allowed))}")
        return v


class ProfileResponse(ProfileBase):
    id: str = Field(..., description="Supabase auth UUID")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProfileUpdateInput(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    mobile_number: Optional[str] = None
    age: Optional[int] = Field(None, ge=18, le=120)
    gender: Optional[str] = None
    community: Optional[str] = None
    annual_income: Optional[float] = Field(None, ge=0)
    district: Optional[str] = None
    state: Optional[str] = None
    education: Optional[str] = None
    is_student: Optional[bool] = None
    is_registered_company: Optional[bool] = None
    is_dpiit_recognised: Optional[bool] = None
    existing_govt_funding_lakhs: Optional[float] = Field(None, ge=0)
    is_first_time_entrepreneur: Optional[bool] = None
    is_woman_led: Optional[bool] = None
    preferred_stage: Optional[str] = None

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() != "":
            cleaned = re.sub(r"\D", "", v)
            if len(cleaned) != 10:
                raise ValueError("Mobile number must be exactly 10 digits")
            return cleaned
        return None

    @field_validator("community")
    @classmethod
    def validate_community(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"OC", "BC", "MBC", "SC", "ST", "General", "Other"}
        if v and v not in allowed:
            raise ValueError(f"Community must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("education")
    @classmethod
    def validate_education(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"Degree", "Diploma", "ITI", "Other"}
        if v and v not in allowed:
            raise ValueError(f"Education must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("preferred_stage")
    @classmethod
    def validate_stage(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"Stage 1", "Stage 2", "Stage 3", "Let AI Suggest"}
        if v and v not in allowed:
            raise ValueError(f"Stage must be one of: {', '.join(sorted(allowed))}")
        return v


class ChatMessageInput(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User question or scheme query (1-2000 characters)")
    conversation_id: Optional[str] = Field(None, description="Optional UUID of existing conversation")
    language_preference: Optional[str] = Field("auto", description="Language preference: auto, en, ta, tanglish, hi, te, ml, kn")
    language: Optional[str] = Field(None, description="Alias for language_preference")
    context_scheme_id: Optional[str] = Field(None, description="Optional scheme ID for contextual chat")


class ConversationCreateInput(BaseModel):
    title: Optional[str] = Field("New Scheme Inquiry", max_length=120)
    language: Optional[str] = Field("auto", max_length=20)


class RoadmapProgressUpdateInput(BaseModel):
    step_id: str = Field(..., min_length=1, max_length=50, description="Step identifier, e.g. step_1")
    status: str = Field(..., description="Status: 'Not started', 'In progress', 'Completed'")

    @field_validator("status")
    @classmethod
    def validate_roadmap_status(cls, v: str) -> str:
        allowed = {"Not started", "In progress", "Completed"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return v


class ChecklistProgressUpdateInput(BaseModel):
    item_id: str = Field(..., min_length=1, max_length=50, description="Item identifier, e.g. doc_1")
    status: str = Field(..., description="Status: 'Not checked', 'Ready', 'Needs attention', 'Needs verification'")

    @field_validator("status")
    @classmethod
    def validate_checklist_status(cls, v: str) -> str:
        allowed = {"Not checked", "Ready", "Needs attention", "Needs verification"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return v


class ProjectRegisterInput(BaseModel):
    title: str = Field(..., min_length=2, max_length=200, description="Project or startup name")
    stage: Optional[str] = Field(None, description="Stage: 'Ideation', 'Prototype / Pilot', 'Scaling / Market Expansion'")
    current_stage: Optional[str] = Field(None, description="Stage alias: 'Ideation', 'Prototype / Pilot', 'Scaling / Market Expansion'")
    category: str = Field(..., min_length=2, max_length=150, description="Business category or sector")
    description: Optional[str] = Field(None, max_length=2500, description="Idea or product description")
    problem_statement: Optional[str] = Field(None, max_length=2500, description="Problem addressed")
    proposed_solution: Optional[str] = Field(None, max_length=2500, description="Proposed solution")
    target_beneficiaries: Optional[str] = Field(None, max_length=500, description="Target customers / market")
    target_market: Optional[str] = Field(None, max_length=500, description="Target market")
    state: Optional[str] = Field(None, max_length=100, description="State of operation")
    district: Optional[str] = Field(None, max_length=100, description="District of operation")
    target_location: Optional[str] = Field(None, max_length=250, description="Business location / region")
    estimated_budget: float = Field(default=0.0, ge=0, description="Expected investment or funding requirement in INR")
    funding_required: Optional[float] = Field(None, ge=0, description="Funding required in INR")
    funding_purpose: Optional[str] = Field(None, max_length=1000, description="Purpose of funding required")
    team_details: Optional[str] = Field(None, max_length=1000, description="Founder and team background")
    founder_team_details: Optional[str] = Field(None, max_length=1000, description="Founder & team details")
    
    # Stage B (Prototype / Pilot) specific
    prototype_status: Optional[str] = Field(None, max_length=500, description="Prototype development status")
    technologies_used: Optional[str] = Field(None, max_length=500, description="Technology stack and tooling")
    technology_used: Optional[str] = Field(None, max_length=500, description="Technology used")
    testing_status: Optional[str] = Field(None, max_length=500, description="Testing and pilot results")
    testing_pilot_status: Optional[str] = Field(None, max_length=500, description="Testing & pilot status")
    demo_link: Optional[str] = Field(None, max_length=500, description="Demo video or web link")
    pitch_deck_url: Optional[str] = Field(None, max_length=500, description="Pitch deck link or upload URL")
    
    # Stage C (Scaling / Market Expansion) specific
    launch_status: Optional[str] = Field(None, max_length=500, description="Commercial launch status")
    revenue_info: Optional[str] = Field(None, max_length=500, description="Revenue and traction numbers")
    revenue_traction: Optional[str] = Field(None, max_length=500, description="Revenue traction")
    customer_info: Optional[str] = Field(None, max_length=500, description="Customer count and metrics")
    expansion_plan: Optional[str] = Field(None, max_length=1500, description="Geographic or market expansion plan")
    documents_info: Optional[str] = Field(None, max_length=1000, description="Supporting documents information")
    supporting_documents: Optional[str] = Field(None, max_length=1000, description="Supporting documents")


class ProjectUpdateInput(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    stage: Optional[str] = None
    current_stage: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    problem_statement: Optional[str] = None
    proposed_solution: Optional[str] = None
    target_beneficiaries: Optional[str] = None
    target_market: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    target_location: Optional[str] = None
    estimated_budget: Optional[float] = Field(None, ge=0)
    funding_required: Optional[float] = Field(None, ge=0)
    funding_purpose: Optional[str] = None
    team_details: Optional[str] = None
    founder_team_details: Optional[str] = None
    prototype_status: Optional[str] = None
    technologies_used: Optional[str] = None
    technology_used: Optional[str] = None
    testing_status: Optional[str] = None
    testing_pilot_status: Optional[str] = None
    demo_link: Optional[str] = None
    pitch_deck_url: Optional[str] = None
    launch_status: Optional[str] = None
    revenue_info: Optional[str] = None
    revenue_traction: Optional[str] = None
    customer_info: Optional[str] = None
    expansion_plan: Optional[str] = None
    documents_info: Optional[str] = None
    supporting_documents: Optional[str] = None



# ============================================================================
# Token Verification & Authentication Dependency
# ============================================================================

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Validates Supabase Bearer token and returns verified user payload.
    SECURITY ENFORCEMENT:
    - Never trusts any client-supplied user ID parameter.
    - User ID is derived strictly from the verified Supabase token.
    - Verifies token via Supabase Auth live endpoint or local JWT secret.
    """
    if not authorization:
        logger.warning("Request rejected: Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Please sign in to access your profile.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("Request rejected: Invalid Authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Special handling for Demo Mock Token in local development testing mode
    if token.startswith("mock-demo-token-"):
        curr_env = os.getenv("ENVIRONMENT", ENVIRONMENT).strip().lower()
        if curr_env in ("production", "prod"):
            logger.warning("Security policy violation: Mock demo token rejected in production environment")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Mock demo tokens are strictly disabled in production mode.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # For Hackathon demonstrations before live Supabase keys are configured
        demo_id = token.replace("mock-demo-token-", "")
        logger.info(f"Using mock-demo session token for local demonstration: {demo_id}")
        return {
            "id": demo_id,
            "email": "demo.entrepreneur@schemeai.gov.in",
            "is_mock": True
        }

    # Approach 1: Cryptographic JWT Secret validation if configured
    if SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
            user_id = payload.get("sub")
            if user_id:
                logger.info(f"Verified user token via JWT Secret for user {user_id}")
                return {
                    "id": user_id,
                    "email": payload.get("email"),
                    "payload": payload,
                    "is_mock": False
                }
        except jwt.PyJWTError as e:
            logger.warning(f"Local JWT decode failed: {e}. Falling back to Supabase Auth endpoint.")

    # Approach 2: Live Supabase Auth Endpoint Verification (Official & Most Reliable)
    if SUPABASE_URL:
        anon_key = SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY
        auth_url = f"{SUPABASE_URL}/auth/v1/user"
        headers = {
            "Authorization": f"Bearer {token}",
            "apikey": anon_key
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(auth_url, headers=headers)

                if res.status_code == 200:
                    user_data = res.json()
                    user_id = user_data.get("id")
                    if not user_id:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token does not contain a valid user ID."
                        )
                    logger.info(f"Verified user token via Supabase Auth: {user_id}")
                    return {
                        "id": user_id,
                        "email": user_data.get("email"),
                        "raw_user": user_data,
                        "is_mock": False
                    }
                else:
                    logger.warning(f"Supabase Auth rejected token: HTTP {res.status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid, revoked or expired Supabase authentication token.",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        except httpx.RequestError as exc:
            logger.error(f"Network error communicating with Supabase Auth: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to verify authentication with Supabase service. Check internet connectivity."
            )

    # If Supabase URL is not yet configured in .env
    logger.error("Supabase URL is not configured in backend environment variables.")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Backend is not yet configured with Supabase credentials. Please set SUPABASE_URL and keys in .env."
    )


# ============================================================================
# Database Helper Functions
# ============================================================================

async def fetch_profile_from_supabase(user_id: str, access_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches the profile for verified user_id from Supabase PostgreSQL public.profiles.
    Never accepts an arbitrary user_id from outside the verified token.
    """
    if not SUPABASE_URL:
        return None

    # Use Service Role Key if available (server-side administrative read)
    # Or forward the user's access token with the Anon Key so PostgREST enforces RLS
    headers = {}
    if SUPABASE_SERVICE_ROLE_KEY:
        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
        }
    elif SUPABASE_ANON_KEY and access_token:
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {access_token}"
        }
    else:
        logger.error("No valid Supabase keys available to query database.")
        return None

    rest_url = f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=*"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(rest_url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                return None
            else:
                logger.error(f"Supabase REST query failed: HTTP {res.status_code}")
                return None
    except httpx.RequestError as e:
        logger.error(f"Failed to query Supabase REST API: {e}")
        return None


async def upsert_profile_in_supabase(user_id: str, profile_data: Dict[str, Any], access_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Inserts or updates profile for verified user_id.
    """
    if not SUPABASE_URL:
        return None

    headers = {
        "Prefer": "return=representation,resolution=merge-duplicates"
    }

    if SUPABASE_SERVICE_ROLE_KEY:
        headers.update({
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json"
        })
    elif SUPABASE_ANON_KEY and access_token:
        headers.update({
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })
    else:
        return None

    rest_url = f"{SUPABASE_URL}/rest/v1/profiles"
    payload = {**profile_data, "id": user_id, "updated_at": datetime.now(timezone.utc).isoformat()}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(rest_url, json=payload, headers=headers)
            if res.status_code in (200, 201):
                records = res.json()
                if isinstance(records, list) and len(records) > 0:
                    return records[0]
                return payload
            else:
                logger.error(f"Supabase upsert failed: HTTP {res.status_code}")
                return None
    except Exception as e:
        logger.error(f"Exception during Supabase upsert: {e}")
        return None


# In-memory mock profiles store for local hackathon demo when testing without live Supabase
DEMO_PROFILES_STORE: Dict[str, Dict[str, Any]] = {
    "demo-entrepreneur-001": {
        "id": "demo-entrepreneur-001",
        "full_name": "Pooja Rameshwaram",
        "email": "pooja.ramesh@schemeai.demo",
        "mobile_number": "9876543210",
        "age": 28,
        "gender": "Female",
        "community": "SC",
        "annual_income": 240000.00,
        "district": "Coimbatore",
        "state": "Tamil Nadu",
        "education": "Degree",
        "is_student": False,
        "is_registered_company": True,
        "is_dpiit_recognised": True,
        "existing_govt_funding_lakhs": 0.00,
        "is_first_time_entrepreneur": True,
        "is_woman_led": True,
        "preferred_stage": "Stage 2",
        "created_at": "2026-10-12T06:00:00Z",
        "updated_at": "2026-10-12T06:00:00Z"
    }
}

DEMO_PROJECTS_STORE: Dict[str, Dict[str, Any]] = {
    "demo-entrepreneur-001": {
        "id": "demo-proj-001",
        "user_id": "demo-entrepreneur-001",
        "title": "Solar-Powered Smart Cold Storage for Agritech",
        "category": "Agritech & Clean Energy",
        "target_beneficiaries": "Small and marginal farmers in western Tamil Nadu",
        "target_location": "Coimbatore & Tiruppur, Tamil Nadu",
        "estimated_budget": 1500000.0,
        "current_stage": "Stage 2",
        "status": "In Progress"
    }
}


async def fetch_project_from_supabase(user_id: str, access_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches the latest submitted project for verified user_id from Supabase public.projects.
    """
    if not SUPABASE_URL:
        return None

    headers = {}
    if SUPABASE_SERVICE_ROLE_KEY:
        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
        }
    elif SUPABASE_ANON_KEY and access_token:
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {access_token}"
        }
    else:
        return None

    rest_url = f"{SUPABASE_URL}/rest/v1/projects?user_id=eq.{user_id}&order=created_at.desc&limit=1"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(rest_url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
            return None
    except Exception as e:
        logger.warning(f"Failed to fetch projects from Supabase: {e}")
        return None


def unpack_project_details(proj: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Unpacks any extra stage details stored in expected_impact json."""
    if not proj:
        return proj
    result = dict(proj)
    impact_raw = result.get("expected_impact")
    if impact_raw and isinstance(impact_raw, str) and (impact_raw.startswith("{") or impact_raw.startswith("[")):
        try:
            extra = json.loads(impact_raw)
            if isinstance(extra, dict):
                for k, v in extra.items():
                    if k not in result or result[k] is None:
                        result[k] = v
        except Exception:
            pass
    return result


async def upsert_project_in_supabase(
    user_id: str,
    project_payload: Dict[str, Any],
    access_token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Inserts or updates the project for user_id in public.projects.
    """
    if not SUPABASE_URL:
        return None

    headers = {
        "Prefer": "return=representation"
    }
    if SUPABASE_SERVICE_ROLE_KEY:
        headers.update({
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json"
        })
    elif SUPABASE_ANON_KEY and access_token:
        headers.update({
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })
    else:
        return None

    existing = await fetch_project_from_supabase(user_id, access_token)

    extra_details = {
        "stage_name": project_payload.get("stage_name") or project_payload.get("stage"),
        "stage": project_payload.get("stage"),
        "description": project_payload.get("description"),
        "team_details": project_payload.get("team_details"),
        "funding_purpose": project_payload.get("funding_purpose"),
        "prototype_status": project_payload.get("prototype_status"),
        "technologies_used": project_payload.get("technologies_used"),
        "testing_status": project_payload.get("testing_status"),
        "demo_link": project_payload.get("demo_link"),
        "pitch_deck_url": project_payload.get("pitch_deck_url"),
        "launch_status": project_payload.get("launch_status"),
        "revenue_info": project_payload.get("revenue_info"),
        "customer_info": project_payload.get("customer_info"),
        "expansion_plan": project_payload.get("expansion_plan"),
        "documents_info": project_payload.get("documents_info"),
        "state": project_payload.get("state"),
        "district": project_payload.get("district")
    }
    extra_details = {k: v for k, v in extra_details.items() if v is not None}

    stage_val = str(project_payload.get("stage", "Stage 1")).lower()
    if "ideation" in stage_val or stage_val == "1":
        current_stage = "Stage 1"
    elif "prototype" in stage_val or "pilot" in stage_val or stage_val == "2":
        current_stage = "Stage 2"
    elif "scale" in stage_val or "market" in stage_val or stage_val == "3":
        current_stage = "Stage 3"
    else:
        current_stage = "Stage 1"

    row = {
        "user_id": user_id,
        "title": project_payload.get("title", "My Project"),
        "problem_statement": project_payload.get("problem_statement") or project_payload.get("description") or "Problem statement documented in project dossier.",
        "proposed_solution": project_payload.get("proposed_solution") or project_payload.get("description") or "Proposed solution documented in project dossier.",
        "category": project_payload.get("category", "General"),
        "target_beneficiaries": project_payload.get("target_beneficiaries") or project_payload.get("customer_info") or "Target Customers",
        "target_location": project_payload.get("target_location") or (f"{project_payload.get('district', '')}, {project_payload.get('state', '')}".strip(" ,") or "Tamil Nadu"),
        "estimated_budget": float(project_payload.get("estimated_budget") or 0.0),
        "current_stage": current_stage,
        "status": "In Progress",
        "expected_impact": json.dumps(extra_details),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if existing and existing.get("id"):
                proj_id = existing["id"]
                url = f"{SUPABASE_URL}/rest/v1/projects?id=eq.{proj_id}&user_id=eq.{user_id}"
                res = await client.patch(url, headers=headers, json=row)
            else:
                row["created_at"] = datetime.now(timezone.utc).isoformat()
                url = f"{SUPABASE_URL}/rest/v1/projects"
                res = await client.post(url, headers=headers, json=row)

            if res.status_code in (200, 201):
                records = res.json()
                if isinstance(records, list) and len(records) > 0:
                    return unpack_project_details(records[0])
                return unpack_project_details(row)
            else:
                logger.error(f"Supabase project upsert failed HTTP {res.status_code}: {res.text}")
                return None
    except Exception as e:
        logger.error(f"Exception during project upsert in Supabase: {e}")
        return None


# ============================================================================
# Phase 5: Chat History Database Helpers & Demo In-Memory Store
# ============================================================================

DEMO_CONVERSATIONS_STORE: Dict[str, Dict[str, Any]] = {}
DEMO_MESSAGES_STORE: Dict[str, List[Dict[str, Any]]] = {}


async def fetch_conversations_from_supabase(user_id: str, access_token: Optional[str] = None) -> List[Dict[str, Any]]:
    if not SUPABASE_URL:
        return []
    headers = {}
    if SUPABASE_SERVICE_ROLE_KEY:
        headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}
    elif SUPABASE_ANON_KEY and access_token:
        headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}"}
    else:
        return []

    rest_url = f"{SUPABASE_URL}/rest/v1/conversations?user_id=eq.{user_id}&order=updated_at.desc"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(rest_url, headers=headers)
            if res.status_code == 200:
                return res.json()
    except Exception as e:
        logger.warning(f"Failed to fetch conversations from Supabase: {e}")
    return []


async def fetch_conversation_by_id(conv_id: str, user_id: str, access_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not SUPABASE_URL:
        return None
    headers = {}
    if SUPABASE_SERVICE_ROLE_KEY:
        headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}
    elif SUPABASE_ANON_KEY and access_token:
        headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}"}
    else:
        return None

    rest_url = f"{SUPABASE_URL}/rest/v1/conversations?id=eq.{conv_id}&user_id=eq.{user_id}&limit=1"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(rest_url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
    except Exception as e:
        logger.warning(f"Failed to fetch conversation {conv_id} from Supabase: {e}")
    return None


async def create_conversation_in_supabase(user_id: str, title: str, language: str = "auto", access_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not SUPABASE_URL:
        return None
    headers = {"Prefer": "return=representation"}
    if SUPABASE_SERVICE_ROLE_KEY:
        headers.update({"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}", "Content-Type": "application/json"})
    elif SUPABASE_ANON_KEY and access_token:
        headers.update({"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}", "Content-Type": "application/json"})
    else:
        return None

    rest_url = f"{SUPABASE_URL}/rest/v1/conversations"
    payload = {"user_id": user_id, "title": title, "language": language}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(rest_url, json=payload, headers=headers)
            if res.status_code in (200, 201):
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
    except Exception as e:
        logger.warning(f"Failed to create conversation in Supabase: {e}")
    return None


async def fetch_messages_from_supabase(conv_id: str, user_id: str, access_token: Optional[str] = None) -> List[Dict[str, Any]]:
    if not SUPABASE_URL:
        return []
    headers = {}
    if SUPABASE_SERVICE_ROLE_KEY:
        headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}
    elif SUPABASE_ANON_KEY and access_token:
        headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}"}
    else:
        return []

    rest_url = f"{SUPABASE_URL}/rest/v1/chat_messages?conversation_id=eq.{conv_id}&user_id=eq.{user_id}&order=created_at.asc"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(rest_url, headers=headers)
            if res.status_code == 200:
                return res.json()
    except Exception as e:
        logger.warning(f"Failed to fetch messages for conversation {conv_id} from Supabase: {e}")
    return []


async def insert_chat_message_in_supabase(conv_id: str, user_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None, access_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not SUPABASE_URL:
        return None
    headers = {"Prefer": "return=representation"}
    if SUPABASE_SERVICE_ROLE_KEY:
        headers.update({"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}", "Content-Type": "application/json"})
    elif SUPABASE_ANON_KEY and access_token:
        headers.update({"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}", "Content-Type": "application/json"})
    else:
        return None

    rest_url = f"{SUPABASE_URL}/rest/v1/chat_messages"
    payload = {
        "conversation_id": conv_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "metadata": metadata or {}
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(rest_url, json=payload, headers=headers)
            if res.status_code in (200, 201):
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
    except Exception as e:
        logger.warning(f"Failed to insert chat message in Supabase: {e}")
    return None


# ============================================================================
# Phase 6: Application Roadmap & Document Checklist Stores & Supabase Helpers
# ============================================================================

DEMO_ROADMAP_PROGRESS_STORE: Dict[str, Dict[str, Any]] = {}
DEMO_CHECKLIST_PROGRESS_STORE: Dict[str, Dict[str, Any]] = {}


async def fetch_user_roadmap_progress(
    user_id: str,
    scheme_id: str,
    access_token: Optional[str] = None,
    is_mock: bool = False
) -> Tuple[Dict[str, str], Dict[str, str]]:
    status_map: Dict[str, str] = {}
    updated_at_map: Dict[str, str] = {}

    if is_mock or not SUPABASE_URL:
        prefix = f"{user_id}:{scheme_id}:"
        for key, val in DEMO_ROADMAP_PROGRESS_STORE.items():
            if key.startswith(prefix):
                step_id = key[len(prefix):]
                status_map[step_id] = val.get("status", "Not started")
                updated_at_map[step_id] = val.get("updated_at", "")
        return status_map, updated_at_map

    headers = {}
    if SUPABASE_SERVICE_ROLE_KEY:
        headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}
    elif SUPABASE_ANON_KEY and access_token:
        headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}"}
    else:
        return status_map, updated_at_map

    rest_url = f"{SUPABASE_URL}/rest/v1/user_scheme_roadmap_progress?user_id=eq.{user_id}&scheme_id=eq.{scheme_id}&select=*"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(rest_url, headers=headers)
            if res.status_code == 200:
                rows = res.json()
                for r in rows:
                    sid = r.get("step_id")
                    if sid:
                        status_map[sid] = r.get("status", "Not started")
                        updated_at_map[sid] = r.get("updated_at", "")
    except Exception as e:
        logger.warning(f"Failed to fetch roadmap progress from Supabase: {e}")

    return status_map, updated_at_map


async def save_user_roadmap_step_progress(
    user_id: str,
    scheme_id: str,
    step_id: str,
    status_val: str,
    access_token: Optional[str] = None,
    is_mock: bool = False
) -> Dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "user_id": user_id,
        "scheme_id": scheme_id,
        "step_id": step_id,
        "status": status_val,
        "updated_at": now_iso
    }

    if is_mock or not SUPABASE_URL:
        key = f"{user_id}:{scheme_id}:{step_id}"
        DEMO_ROADMAP_PROGRESS_STORE[key] = record
        return record

    headers = {
        "Prefer": "return=representation,resolution=merge-duplicates",
        "Content-Type": "application/json"
    }
    if SUPABASE_SERVICE_ROLE_KEY:
        headers.update({"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"})
    elif SUPABASE_ANON_KEY and access_token:
        headers.update({"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}"})
    else:
        key = f"{user_id}:{scheme_id}:{step_id}"
        DEMO_ROADMAP_PROGRESS_STORE[key] = record
        return record

    rest_url = f"{SUPABASE_URL}/rest/v1/user_scheme_roadmap_progress"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(rest_url, json=record, headers=headers)
            if res.status_code in (200, 201):
                rows = res.json()
                if isinstance(rows, list) and len(rows) > 0:
                    return rows[0]
            logger.warning(f"Supabase roadmap step upsert status: HTTP {res.status_code}")
    except Exception as e:
        logger.warning(f"Failed to save roadmap progress to Supabase: {e}")

    key = f"{user_id}:{scheme_id}:{step_id}"
    DEMO_ROADMAP_PROGRESS_STORE[key] = record
    return record


async def fetch_user_checklist_progress(
    user_id: str,
    scheme_id: str,
    access_token: Optional[str] = None,
    is_mock: bool = False
) -> Tuple[Dict[str, str], Dict[str, str]]:
    status_map: Dict[str, str] = {}
    updated_at_map: Dict[str, str] = {}

    if is_mock or not SUPABASE_URL:
        prefix = f"{user_id}:{scheme_id}:"
        for key, val in DEMO_CHECKLIST_PROGRESS_STORE.items():
            if key.startswith(prefix):
                item_id = key[len(prefix):]
                status_map[item_id] = val.get("status", "Not checked")
                updated_at_map[item_id] = val.get("updated_at", "")
        return status_map, updated_at_map

    headers = {}
    if SUPABASE_SERVICE_ROLE_KEY:
        headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}
    elif SUPABASE_ANON_KEY and access_token:
        headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}"}
    else:
        return status_map, updated_at_map

    rest_url = f"{SUPABASE_URL}/rest/v1/user_scheme_checklist_progress?user_id=eq.{user_id}&scheme_id=eq.{scheme_id}&select=*"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(rest_url, headers=headers)
            if res.status_code == 200:
                rows = res.json()
                for r in rows:
                    iid = r.get("item_id")
                    if iid:
                        status_map[iid] = r.get("status", "Not checked")
                        updated_at_map[iid] = r.get("updated_at", "")
    except Exception as e:
        logger.warning(f"Failed to fetch checklist progress from Supabase: {e}")

    return status_map, updated_at_map


async def save_user_checklist_item_progress(
    user_id: str,
    scheme_id: str,
    item_id: str,
    status_val: str,
    access_token: Optional[str] = None,
    is_mock: bool = False
) -> Dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "user_id": user_id,
        "scheme_id": scheme_id,
        "item_id": item_id,
        "status": status_val,
        "updated_at": now_iso
    }

    if is_mock or not SUPABASE_URL:
        key = f"{user_id}:{scheme_id}:{item_id}"
        DEMO_CHECKLIST_PROGRESS_STORE[key] = record
        return record

    headers = {
        "Prefer": "return=representation,resolution=merge-duplicates",
        "Content-Type": "application/json"
    }
    if SUPABASE_SERVICE_ROLE_KEY:
        headers.update({"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"})
    elif SUPABASE_ANON_KEY and access_token:
        headers.update({"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}"})
    else:
        key = f"{user_id}:{scheme_id}:{item_id}"
        DEMO_CHECKLIST_PROGRESS_STORE[key] = record
        return record

    rest_url = f"{SUPABASE_URL}/rest/v1/user_scheme_checklist_progress"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(rest_url, json=record, headers=headers)
            if res.status_code in (200, 201):
                rows = res.json()
                if isinstance(rows, list) and len(rows) > 0:
                    return rows[0]
            logger.warning(f"Supabase checklist item upsert status: HTTP {res.status_code}")
    except Exception as e:
        logger.warning(f"Failed to save checklist progress to Supabase: {e}")

    key = f"{user_id}:{scheme_id}:{item_id}"
    DEMO_CHECKLIST_PROGRESS_STORE[key] = record
    return record




# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", summary="Root Health & Info")
async def root():
    """
    Root entry point providing status and documentation link.
    """
    return {
        "status": "online",
        "app": "AI Funding & Scheme Matcher (SchemeAI) Backend API",
        "version": "1.0.0",
        "message": "Welcome to AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs API (AI Funding & Scheme Matcher)",
        "project": "Smart India Hackathon — AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs",
        "documentation": "/docs",
        "health_check": "/api/health",
        "profile_endpoint": "/api/profile/me"
    }


@app.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    tags=["System"]
)
async def get_health():
    """
    Returns the operational status of the SchemeAI backend,
    including configuration indicators and allowed CORS origins.
    """
    is_supabase_ready = bool(SUPABASE_URL and (SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY))

    return HealthResponse(
        status="ok",
        app="AI Funding & Scheme Matcher (SchemeAI) Backend",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        environment=ENVIRONMENT,
        supabase_configured=is_supabase_ready,
        cors_allowed_origins=ALLOWED_ORIGINS
    )


@app.get(
    "/api/profile/me",
    summary="Get Current User Profile",
    tags=["Profile"]
)
async def get_my_profile(
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint: Fetches private profile information for the authenticated user.
    - Verifies Supabase access token in Authorization header.
    - Strictly derives user ID from verified token.
    - Enforces ownership: users can only access their own profile record.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)

    # 1. If running in local mock demo mode
    if is_mock:
        profile = DEMO_PROFILES_STORE.get(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found in demo database. Please complete registration."
            )
        return {
            "success": True,
            "source": "demo_store",
            "profile": profile
        }

    # 2. Extract bearer token for forwarding
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split()[1] if " " in auth_header else None

    # 3. Query Supabase PostgreSQL
    profile = await fetch_profile_from_supabase(user_id, access_token=token)

    if not profile:
        logger.info(f"Profile not found for authenticated user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please complete your entrepreneur profile registration."
        )

    logger.info(f"Successfully returned profile for user: {user_id}")
    return {
        "success": True,
        "source": "supabase_postgresql",
        "profile": profile
    }


@app.put(
    "/api/profile/me",
    summary="Update Current User Profile",
    tags=["Profile"]
)
async def update_my_profile(
    profile_update: ProfileUpdateInput,
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint: Updates the authenticated user's profile.
    - Strictly updates only the record matching the verified token user ID.
    - Prevents tampering with arbitrary accounts.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)

    # Filter out None values from update payload
    update_data = {k: v for k, v in profile_update.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided to update."
        )

    if is_mock:
        existing = DEMO_PROFILES_STORE.get(user_id, {"id": user_id, "email": user_auth.get("email", "")})
        existing.update(update_data)
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        DEMO_PROFILES_STORE[user_id] = existing
        return {
            "success": True,
            "message": "Profile updated successfully (Demo Store)",
            "profile": existing
        }

    auth_header = request.headers.get("authorization", "")
    token = auth_header.split()[1] if " " in auth_header else None

    updated = await upsert_profile_in_supabase(user_id, update_data, access_token=token)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile in database."
        )

    return {
        "success": True,
        "message": "Profile updated successfully",
        "profile": updated
    }


# ============================================================================
# PHASE 2 & 4: Entrepreneur Project Registration & Management Endpoints
# ============================================================================

@app.get(
    "/api/projects/me",
    summary="Get Current User Registered Project",
    tags=["Projects"]
)
async def get_my_project(
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint: Fetches private project information for the authenticated user.
    - Derived strictly from verified Bearer token.
    - Enforces ownership: users can only view their own project.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)

    project = None
    if is_mock:
        project = DEMO_PROJECTS_STORE.get(user_id)
    else:
        auth_header = request.headers.get("authorization", "")
        token = auth_header.split()[1] if " " in auth_header else None
        raw_proj = await fetch_project_from_supabase(user_id, access_token=token)
        project = unpack_project_details(raw_proj) if raw_proj else None
        if not project and is_mock:
            project = DEMO_PROJECTS_STORE.get(user_id)

    if not project:
        return {
            "success": True,
            "has_project": False,
            "project": None,
            "message": "No registered project found. Please complete project registration."
        }

    return {
        "success": True,
        "has_project": True,
        "project": project
    }


@app.post(
    "/api/projects",
    summary="Register a New Innovation Project (Ideation, Prototype/Pilot, or Scaling)",
    tags=["Projects"]
)
async def register_project(
    project_input: ProjectRegisterInput,
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint: Registers project for the authenticated user.
    - Validates stage-specific fields:
      * Stage A (Ideation): Project name, description/problem & solution, category, target customers, location, funding req, team details.
      * Stage B (Prototype/Pilot): Project name, description, prototype status, tech used, testing status, funding req, team details.
      * Stage C (Scaling/Expansion): Product details, launch status, revenue/customer info, location & target market, expansion plan, funding req.
    - Saves project to Supabase or demo store.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)

    input_data = project_input.model_dump()
    stage = input_data.get("stage") or input_data.get("current_stage") or "Ideation"
    input_data["stage"] = stage
    input_data["current_stage"] = stage

    if not input_data.get("technologies_used"):
        input_data["technologies_used"] = input_data.get("technology_used")
    if not input_data.get("technology_used"):
        input_data["technology_used"] = input_data.get("technologies_used")
    if not input_data.get("testing_status"):
        input_data["testing_status"] = input_data.get("testing_pilot_status")
    if not input_data.get("testing_pilot_status"):
        input_data["testing_pilot_status"] = input_data.get("testing_status")
    if not input_data.get("team_details"):
        input_data["team_details"] = input_data.get("founder_team_details")
    if not input_data.get("founder_team_details"):
        input_data["founder_team_details"] = input_data.get("team_details")
    if not input_data.get("estimated_budget") and input_data.get("funding_required"):
        input_data["estimated_budget"] = float(input_data["funding_required"])
    if not input_data.get("revenue_info"):
        input_data["revenue_info"] = input_data.get("revenue_traction")
    if not input_data.get("customer_info"):
        input_data["customer_info"] = input_data.get("target_market")

    # Validate stage-specific required fields
    clean_stage = stage.strip().lower()
    if "ideation" in clean_stage or clean_stage == "1" or clean_stage == "stage 1":
        # Stage A: Ideation
        if not input_data.get("title") or not input_data.get("category"):
            raise HTTPException(status_code=400, detail="Project name and business category are required for Ideation stage.")
        if not input_data.get("description") and not (input_data.get("problem_statement") and input_data.get("proposed_solution")):
            raise HTTPException(status_code=400, detail="Idea description or problem and proposed solution are required for Ideation stage.")
    elif "prototype" in clean_stage or "pilot" in clean_stage or clean_stage == "2" or clean_stage == "stage 2":
        # Stage B: Prototype / Pilot
        if not input_data.get("title") or not input_data.get("prototype_status"):
            raise HTTPException(status_code=400, detail="Project name and prototype development status are required for Prototype/Pilot stage.")
        if not input_data.get("technologies_used"):
            raise HTTPException(status_code=400, detail="Technologies used must be specified for Prototype/Pilot stage.")
    elif "scale" in clean_stage or "market" in clean_stage or clean_stage == "3" or clean_stage == "stage 3":
        # Stage C: Scaling / Market Expansion
        if not input_data.get("title") or not input_data.get("launch_status"):
            raise HTTPException(status_code=400, detail="Product details and launch status are required for Scaling stage.")
        if not input_data.get("expansion_plan"):
            raise HTTPException(status_code=400, detail="Expansion plan is required for Scaling stage.")

    if is_mock:
        proj_id = f"proj-{user_id[:8]}"
        project_obj = {
            "id": proj_id,
            "user_id": user_id,
            **input_data,
            "current_stage": "Stage 1" if "ideation" in clean_stage else ("Stage 2" if "prototype" in clean_stage or "pilot" in clean_stage else "Stage 3"),
            "status": "In Progress",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        DEMO_PROJECTS_STORE[user_id] = project_obj
        return {
            "success": True,
            "message": "Project registered successfully (Demo Store)",
            "project": project_obj
        }

    auth_header = request.headers.get("authorization", "")
    token = auth_header.split()[1] if " " in auth_header else None

    saved = await upsert_project_in_supabase(user_id, input_data, access_token=token)
    if not saved:
        # Fallback to local memory store so user isn't blocked
        proj_id = f"proj-{user_id[:8]}"
        project_obj = {
            "id": proj_id,
            "user_id": user_id,
            **input_data,
            "current_stage": "Stage 1" if "ideation" in clean_stage else ("Stage 2" if "prototype" in clean_stage or "pilot" in clean_stage else "Stage 3"),
            "status": "In Progress",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        DEMO_PROJECTS_STORE[user_id] = project_obj
        return {
            "success": True,
            "message": "Project registered successfully (Local Store)",
            "project": project_obj
        }

    return {
        "success": True,
        "message": "Project registered successfully",
        "project": saved
    }


@app.put(
    "/api/projects/me",
    summary="Update Current User Registered Project",
    tags=["Projects"]
)
async def update_my_project(
    project_update: ProjectUpdateInput,
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint: Updates registered project for authenticated user.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)

    update_data = {k: v for k, v in project_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided to update.")

    if "current_stage" in update_data and "stage" not in update_data:
        update_data["stage"] = update_data["current_stage"]
    if "stage" in update_data and "current_stage" not in update_data:
        update_data["current_stage"] = update_data["stage"]

    if is_mock:
        existing = DEMO_PROJECTS_STORE.get(user_id, {"id": f"proj-{user_id[:8]}", "user_id": user_id})
        existing.update(update_data)
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        DEMO_PROJECTS_STORE[user_id] = existing
        return {
            "success": True,
            "message": "Project updated successfully (Demo Store)",
            "project": existing
        }

    auth_header = request.headers.get("authorization", "")
    token = auth_header.split()[1] if " " in auth_header else None

    # Merge with existing project
    raw_existing = await fetch_project_from_supabase(user_id, access_token=token)
    merged = unpack_project_details(raw_existing) if raw_existing else {}
    merged.update(update_data)

    saved = await upsert_project_in_supabase(user_id, merged, access_token=token)
    if not saved:
        # Fallback to demo store
        existing_demo = DEMO_PROJECTS_STORE.get(user_id, {"id": f"proj-{user_id[:8]}", "user_id": user_id})
        existing_demo.update(update_data)
        existing_demo["updated_at"] = datetime.now(timezone.utc).isoformat()
        DEMO_PROJECTS_STORE[user_id] = existing_demo
        return {
            "success": True,
            "message": "Project updated successfully (Local Store)",
            "project": existing_demo
        }

    return {
        "success": True,
        "message": "Project updated successfully",
        "project": saved
    }


# ============================================================================
# PHASE 4: Government Scheme Matching & Discovery Endpoints
# ============================================================================

@app.get(
    "/api/schemes",
    summary="List All Verified Government Schemes",
    tags=["Schemes"]
)
async def list_all_schemes(
    funding_type: Optional[str] = None,
    government: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Public Catalog: Lists verified central and state schemes from the official dataset.
    Supports optional filtering by funding type, government level, and keyword search.
    """
    schemes = load_all_schemes()
    filtered = schemes

    if funding_type and funding_type.strip().lower() not in ("all", ""):
        ft = funding_type.strip().lower()
        filtered = [
            s for s in filtered 
            if s.get("funding_category", "").lower() == ft or ft in s.get("type", "").lower()
        ]

    if government and government.strip().lower() not in ("all", ""):
        gov = government.strip().lower()
        filtered = [
            s for s in filtered 
            if gov in s.get("government_scope", "").lower() or gov in s.get("government", "").lower()
        ]

    if search and search.strip():
        q = search.strip().lower()
        filtered = [
            s for s in filtered
            if q in s.get("name", "").lower() or q in s.get("provider", "").lower() or q in s.get("benefit", "").lower()
        ]

    return {
        "success": True,
        "total_schemes": len(schemes),
        "count": len(filtered),
        "schemes": filtered
    }


@app.get(
    "/api/schemes/matches",
    summary="Get AI-Assisted Matched Schemes for Authenticated User",
    tags=["Schemes"]
)
async def get_my_scheme_matches(
    request: Request,
    funding_type: Optional[str] = None,
    government: Optional[str] = None,
    eligibility_status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(15, ge=1, le=100, description="Schemes per page (default 15)"),
    all_schemes: bool = Query(False, alias="all", description="Return all matched schemes without pagination"),
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint:
    - Derives user ID strictly from the verified Supabase Bearer token.
    - Evaluates profile and project details against deterministic eligibility criteria.
    - MANDATORY: Requires registered project before returning scheme matches!
    - Classifies schemes into:
      * "Eligible based on available data" / "Likely Match"
      * "Potential match"
      * "Needs verification"
      * "Not eligible based on a verified rule"
    - Supports server-side pagination with default page_size=15.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)

    profile: Optional[Dict[str, Any]] = None
    project: Optional[Dict[str, Any]] = None

    if is_mock:
        profile = DEMO_PROFILES_STORE.get(user_id)
        project = DEMO_PROJECTS_STORE.get(user_id)
    else:
        auth_header = request.headers.get("authorization", "")
        token = auth_header.split()[1] if " " in auth_header else None
        profile = await fetch_profile_from_supabase(user_id, access_token=token)
        raw_project = await fetch_project_from_supabase(user_id, access_token=token)
        project = unpack_project_details(raw_project) if raw_project else None
        if not project and is_mock:
            project = DEMO_PROJECTS_STORE.get(user_id)

    if not profile:
        logger.warning(f"Scheme matching requested but profile not found for user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please complete your entrepreneur profile registration before matching schemes."
        )

    # REQUIRE registered project before showing matched schemes!
    if not project:
        logger.info(f"Scheme matching withheld: User {user_id} has not registered a project yet.")
        return {
            "success": False,
            "project_required": True,
            "message": "Project registration required before showing matched schemes. Please register your project first.",
            "pagination": {
                "page": 1,
                "page_size": page_size,
                "total_items": 0,
                "total_pages": 1,
                "has_next": False,
                "has_prev": False,
                "start_index": 0,
                "end_index": 0
            },
            "matches": [],
            "match_summary": {
                "total_schemes": 0,
                "filtered_count": 0,
                "eligible_count": 0,
                "potential_count": 0,
                "likely_match_count": 0,
                "needs_verification_count": 0,
                "not_eligible_count": 0,
                "average_fit_score": 0.0
            }
        }

    results = get_matched_schemes_for_user(
        profile=profile,
        project=project,
        funding_type=funding_type,
        government=government,
        eligibility_status=eligibility_status,
        search_query=search,
        page=page,
        page_size=page_size,
        all_items=all_schemes
    )

    logger.info(f"Generated scheme matches for user {user_id} with project {project.get('title')}: {len(results.get('matches', []))} schemes returned on page {page}")
    return results



@app.get(
    "/api/schemes/{scheme_id}",
    summary="Get Verified Scheme Details & Personalized Match Dossier",
    tags=["Schemes"]
)
async def get_single_scheme_details(
    scheme_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Retrieves full verified scheme details by ID.
    If a valid Supabase Authorization header is supplied, adds personalized profile-fit evaluation.
    """
    scheme = get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with ID '{scheme_id}' was not found in the verified dataset."
        )

    personalized_evaluation: Optional[Dict[str, Any]] = None

    # Optional authentication for personalized evaluation
    if authorization:
        try:
            user_auth = await get_current_user_id(authorization)
            user_id = user_auth["id"]
            is_mock = user_auth.get("is_mock", False)

            profile: Optional[Dict[str, Any]] = None
            project: Optional[Dict[str, Any]] = None

            if is_mock:
                profile = DEMO_PROFILES_STORE.get(user_id)
                project = DEMO_PROJECTS_STORE.get(user_id)
            else:
                token = authorization.split()[1] if " " in authorization else None
                profile = await fetch_profile_from_supabase(user_id, access_token=token)
                raw_project = await fetch_project_from_supabase(user_id, access_token=token)
                project = unpack_project_details(raw_project) if raw_project else None

            if profile:
                personalized_evaluation = evaluate_scheme_for_profile(scheme, profile, project)
        except Exception as e:
            logger.debug(f"Could not compute personalized evaluation: {e}")

    return {
        "success": True,
        "scheme": scheme,
        "personalized_evaluation": personalized_evaluation
    }


# ============================================================================
# PHASE 5: Grounded Gemini AI Scheme Assistant Endpoints
# ============================================================================

import uuid


@app.post(
    "/api/chat",
    summary="Send Message to Gemini Grounded Scheme Assistant",
    tags=["Chatbot"]
)
async def chat_with_scheme_assistant(
    chat_input: ChatMessageInput,
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint:
    - Verifies Supabase Bearer token. User ID derived strictly from token.
    - Validates message format and length (max 2000 chars).
    - Checks conversation ownership (prevents cross-user data leakage).
    - Grounds answers on verified scheme dataset and Phase 4 deterministic engine.
    - Supports English, Tamil script, and Tanglish.
    - Persists chat messages with user ownership.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split()[1] if " " in auth_header else None

    clean_message = chat_input.message.strip()
    if not clean_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty."
        )

    # 1. Fetch authenticated user profile & project server-side
    profile: Optional[Dict[str, Any]] = None
    project: Optional[Dict[str, Any]] = None

    if is_mock:
        profile = DEMO_PROFILES_STORE.get(user_id)
        project = DEMO_PROJECTS_STORE.get(user_id)
    else:
        profile = await fetch_profile_from_supabase(user_id, access_token=token)
        raw_project = await fetch_project_from_supabase(user_id, access_token=token)
        project = unpack_project_details(raw_project) if raw_project else None
        if not project and is_mock:
            project = DEMO_PROJECTS_STORE.get(user_id)

    if not profile:
        profile = {
            "id": user_id,
            "full_name": user_auth.get("email", "Founder").split("@")[0].title(),
            "email": user_auth.get("email", ""),
            "state": None,
            "community": None
        }

    # 2. Validate or create conversation
    conv_id = chat_input.conversation_id
    conv_title = " ".join(clean_message.split()[:7])[:60] or "New Scheme Inquiry"

    if conv_id:
        # Check ownership strictly
        if is_mock:
            existing_conv = DEMO_CONVERSATIONS_STORE.get(conv_id)
            if not existing_conv:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation thread not found.")
            if existing_conv.get("user_id") != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation thread.")
        else:
            existing_conv = await fetch_conversation_by_id(conv_id, user_id, access_token=token)
            if not existing_conv:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation thread not found or does not belong to the authenticated user."
                )
    else:
        # Create new conversation
        new_conv_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        eff_lang = chat_input.language if (not chat_input.language_preference or chat_input.language_preference == "auto") and chat_input.language else (chat_input.language_preference or "auto")
        if is_mock:
            DEMO_CONVERSATIONS_STORE[new_conv_id] = {
                "id": new_conv_id,
                "user_id": user_id,
                "title": conv_title,
                "language": eff_lang,
                "created_at": now_iso,
                "updated_at": now_iso
            }
            conv_id = new_conv_id
        else:
            created = await create_conversation_in_supabase(user_id, conv_title, eff_lang, access_token=token)
            conv_id = created["id"] if created else new_conv_id

    # 3. Fetch recent history for this conversation
    history_messages: List[Dict[str, str]] = []
    if is_mock:
        raw_msgs = DEMO_MESSAGES_STORE.get(conv_id, [])
        history_messages = [{"role": m["role"], "content": m["content"]} for m in raw_msgs[-12:]]
    else:
        raw_msgs = await fetch_messages_from_supabase(conv_id, user_id, access_token=token)
        history_messages = [{"role": m["role"], "content": m["content"]} for m in raw_msgs[-12:]]

    eff_lang = chat_input.language if (not chat_input.language_preference or chat_input.language_preference == "auto") and chat_input.language else (chat_input.language_preference or "auto")

    # 4. Save user message to database/mock store
    now_iso = datetime.now(timezone.utc).isoformat()
    user_msg_record = {
        "id": str(uuid.uuid4()),
        "conversation_id": conv_id,
        "user_id": user_id,
        "role": "user",
        "content": clean_message,
        "metadata": {"lang_pref": eff_lang},
        "created_at": now_iso
    }
    if is_mock:
        if conv_id not in DEMO_MESSAGES_STORE:
            DEMO_MESSAGES_STORE[conv_id] = []
        DEMO_MESSAGES_STORE[conv_id].append(user_msg_record)
    else:
        await insert_chat_message_in_supabase(
            conv_id, user_id, "user", clean_message,
            metadata={"lang_pref": eff_lang},
            access_token=token
        )

    # 5. Call Grounded Gemini Assistant Service
    ai_result = await generate_grounded_chat_response(
        user_message=clean_message,
        profile=profile,
        project=project,
        history=history_messages,
        language_preference=eff_lang
    )

    assistant_reply = ai_result.get("response", "")

    # 6. Save assistant response to database/mock store
    assistant_msg_record = {
        "id": str(uuid.uuid4()),
        "conversation_id": conv_id,
        "user_id": user_id,
        "role": "assistant",
        "content": assistant_reply,
        "metadata": {
            "model_used": ai_result.get("model_used"),
            "language_detected": ai_result.get("language_detected"),
            "live_gemini": ai_result.get("live_gemini")
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    if is_mock:
        DEMO_MESSAGES_STORE[conv_id].append(assistant_msg_record)
        if conv_id in DEMO_CONVERSATIONS_STORE:
            DEMO_CONVERSATIONS_STORE[conv_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
    else:
        await insert_chat_message_in_supabase(
            conv_id, user_id, "assistant", assistant_reply,
            metadata=assistant_msg_record["metadata"],
            access_token=token
        )

    return {
        "success": ai_result.get("success", True),
        "conversation_id": conv_id,
        "response": assistant_reply,
        "reply": assistant_reply,
        "language_detected": ai_result.get("language_detected"),
        "model_used": ai_result.get("model_used"),
        "live_gemini": ai_result.get("live_gemini", False),
        "referenced_schemes": ai_result.get("referenced_schemes", [])
    }



@app.get(
    "/api/chat/history",
    summary="Get Chat History or Specific Conversation Messages",
    tags=["Chatbot"]
)
async def get_chat_history(
    request: Request,
    conversation_id: Optional[str] = None,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint:
    - If conversation_id is provided, returns all messages for that thread after validating ownership.
    - If conversation_id is omitted, returns list of all conversations owned by the user.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split()[1] if " " in auth_header else None

    # Scenario A: Retrieve messages for a specific conversation
    if conversation_id:
        if is_mock:
            conv = DEMO_CONVERSATIONS_STORE.get(conversation_id)
            if not conv:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
            if conv.get("user_id") != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation thread.")
            messages = DEMO_MESSAGES_STORE.get(conversation_id, [])
            return {
                "success": True,
                "conversation": conv,
                "messages": messages
            }
        else:
            conv = await fetch_conversation_by_id(conversation_id, user_id, access_token=token)
            if not conv:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found or unauthorized."
                )
            messages = await fetch_messages_from_supabase(conversation_id, user_id, access_token=token)
            return {
                "success": True,
                "conversation": conv,
                "messages": messages
            }

    # Scenario B: Retrieve all conversations for this user
    if is_mock:
        user_convs = [c for c in DEMO_CONVERSATIONS_STORE.values() if c.get("user_id") == user_id]
        user_convs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return {
            "success": True,
            "conversations": user_convs
        }
    else:
        user_convs = await fetch_conversations_from_supabase(user_id, access_token=token)
        return {
            "success": True,
            "conversations": user_convs
        }


@app.get(
    "/api/chat/conversations",
    summary="List All Conversations for Authenticated User",
    tags=["Chatbot"]
)
async def list_my_conversations(
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint: Lists all conversation threads owned by the authenticated user.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split()[1] if " " in auth_header else None

    if is_mock:
        user_convs = [c for c in DEMO_CONVERSATIONS_STORE.values() if c.get("user_id") == user_id]
        user_convs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return {"success": True, "conversations": user_convs}
    else:
        user_convs = await fetch_conversations_from_supabase(user_id, access_token=token)
        return {"success": True, "conversations": user_convs}


@app.post(
    "/api/chat/conversations",
    summary="Create New Conversation Thread",
    tags=["Chatbot"]
)
async def create_new_conversation(
    conv_input: ConversationCreateInput,
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint: Initializes a new conversation thread for the authenticated user.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split()[1] if " " in auth_header else None

    new_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    title = conv_input.title or "New Scheme Inquiry"
    language = conv_input.language or "auto"

    if is_mock:
        conv_obj = {
            "id": new_id,
            "user_id": user_id,
            "title": title,
            "language": language,
            "created_at": now_iso,
            "updated_at": now_iso
        }
        DEMO_CONVERSATIONS_STORE[new_id] = conv_obj
        DEMO_MESSAGES_STORE[new_id] = []
        return {"success": True, "conversation": conv_obj}
    else:
        created = await create_conversation_in_supabase(user_id, title, language, access_token=token)
        if not created:
            created = {
                "id": new_id,
                "user_id": user_id,
                "title": title,
                "language": language,
                "created_at": now_iso,
                "updated_at": now_iso
            }
        return {"success": True, "conversation": created}


@app.get(
    "/api/chat/conversations/{conversation_id}/messages",
    summary="Get All Messages in a Conversation",
    tags=["Chatbot"]
)
async def get_conversation_messages(
    conversation_id: str,
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint: Enforces strict user ownership; returns messages for the given thread.
    """
    return await get_chat_history(request, conversation_id=conversation_id, user_auth=user_auth)


# ============================================================================
# PHASE 6: Application Roadmap, Document Checklist & Eligibility Gap Analysis
# ============================================================================

@app.get(
    "/api/schemes/{scheme_id}/roadmap",
    summary="Get Scheme Application Roadmap with User Progress",
    tags=["Phase 6: Roadmap & Checklist"]
)
async def get_scheme_roadmap_endpoint(
    scheme_id: str,
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint:
    - Derives user_id from verified Supabase token.
    - Validates scheme_id against verified dataset.
    - Loads verified application steps and overlays user's persistent progress.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split()[1] if " " in auth_header else None

    scheme = find_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' was not found in the verified dataset."
        )

    status_map, updated_at_map = await fetch_user_roadmap_progress(user_id, scheme_id, access_token=token, is_mock=is_mock)
    roadmap = build_scheme_roadmap(scheme, user_step_statuses=status_map, last_updated_map=updated_at_map)

    return {"success": True, "roadmap": roadmap}


@app.get(
    "/api/schemes/{scheme_id}/roadmap/progress",
    summary="Get User Roadmap Progress State",
    tags=["Phase 6: Roadmap & Checklist"]
)
async def get_scheme_roadmap_progress_endpoint(
    scheme_id: str,
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    return await get_scheme_roadmap_endpoint(scheme_id, request, user_auth)


@app.put(
    "/api/schemes/{scheme_id}/roadmap/progress",
    summary="Update User Application Roadmap Step Status",
    tags=["Phase 6: Roadmap & Checklist"]
)
@app.post(
    "/api/schemes/{scheme_id}/roadmap/progress",
    summary="Update User Application Roadmap Step Status (POST alias)",
    tags=["Phase 6: Roadmap & Checklist"]
)
async def update_scheme_roadmap_progress_endpoint(
    scheme_id: str,
    update_input: RoadmapProgressUpdateInput,
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint:
    - Derives user_id strictly from verified token.
    - Validates scheme_id and step_id.
    - Persists step status ('Not started', 'In progress', 'Completed').
    - Recalculates overall roadmap progress percentage.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split()[1] if " " in auth_header else None

    scheme = find_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' was not found in the verified dataset."
        )

    # Validate step_id belongs to this scheme
    raw_steps = scheme.get("apply_steps", [])
    valid_step_ids = [f"step_{i + 1}" for i in range(len(raw_steps))]
    if raw_steps and update_input.step_id not in valid_step_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid step_id '{update_input.step_id}'. Valid steps for this scheme are: {', '.join(valid_step_ids)}"
        )

    await save_user_roadmap_step_progress(
        user_id=user_id,
        scheme_id=scheme_id,
        step_id=update_input.step_id,
        status_val=update_input.status,
        access_token=token,
        is_mock=is_mock
    )

    status_map, updated_at_map = await fetch_user_roadmap_progress(user_id, scheme_id, access_token=token, is_mock=is_mock)
    updated_roadmap = build_scheme_roadmap(scheme, user_step_statuses=status_map, last_updated_map=updated_at_map)

    return {
        "success": True,
        "message": f"Step '{update_input.step_id}' marked as '{update_input.status}'",
        "roadmap": updated_roadmap
    }


@app.get(
    "/api/schemes/{scheme_id}/checklist",
    summary="Get Scheme Document Readiness Checklist with User Status",
    tags=["Phase 6: Roadmap & Checklist"]
)
async def get_scheme_checklist_endpoint(
    scheme_id: str,
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint:
    - Derives user_id from verified token.
    - Loads verified document checklist items and user's saved readiness statuses.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split()[1] if " " in auth_header else None

    scheme = find_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' was not found in the verified dataset."
        )

    status_map, updated_at_map = await fetch_user_checklist_progress(user_id, scheme_id, access_token=token, is_mock=is_mock)
    checklist = build_scheme_checklist(scheme, user_item_statuses=status_map, last_updated_map=updated_at_map)

    return {"success": True, "checklist": checklist}


@app.put(
    "/api/schemes/{scheme_id}/checklist/progress",
    summary="Update Document Checklist Item Status",
    tags=["Phase 6: Roadmap & Checklist"]
)
@app.post(
    "/api/schemes/{scheme_id}/checklist/progress",
    summary="Update Document Checklist Item Status (POST alias)",
    tags=["Phase 6: Roadmap & Checklist"]
)
async def update_scheme_checklist_progress_endpoint(
    scheme_id: str,
    update_input: ChecklistProgressUpdateInput,
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint:
    - Derives user_id from verified token.
    - Persists document item readiness status ('Not checked', 'Ready', 'Needs attention', 'Needs verification').
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split()[1] if " " in auth_header else None

    scheme = find_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' was not found in the verified dataset."
        )

    raw_docs = scheme.get("documents_required", [])
    valid_item_ids = [f"doc_{i + 1}" for i in range(len(raw_docs))]
    if raw_docs and update_input.item_id not in valid_item_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid item_id '{update_input.item_id}'. Valid items for this scheme are: {', '.join(valid_item_ids)}"
        )

    await save_user_checklist_item_progress(
        user_id=user_id,
        scheme_id=scheme_id,
        item_id=update_input.item_id,
        status_val=update_input.status,
        access_token=token,
        is_mock=is_mock
    )

    status_map, updated_at_map = await fetch_user_checklist_progress(user_id, scheme_id, access_token=token, is_mock=is_mock)
    updated_checklist = build_scheme_checklist(scheme, user_item_statuses=status_map, last_updated_map=updated_at_map)

    return {
        "success": True,
        "message": f"Document item '{update_input.item_id}' updated to '{update_input.status}'",
        "checklist": updated_checklist
    }


@app.get(
    "/api/schemes/{scheme_id}/gap-analysis",
    summary="Get Eligibility Gap Analysis Comparing Profile to Scheme Rules",
    tags=["Phase 6: Roadmap & Checklist"]
)
async def get_eligibility_gap_analysis_endpoint(
    scheme_id: str,
    request: Request,
    user_auth: Dict[str, Any] = Depends(get_current_user_id)
):
    """
    Protected Endpoint:
    - Derives user_id strictly from verified token.
    - Compares scheme's verified eligibility rules against user's saved profile & project.
    - Distinguishes satisfied rules, verified disqualifications, missing data, and third-party checks.
    """
    user_id = user_auth["id"]
    is_mock = user_auth.get("is_mock", False)
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split()[1] if " " in auth_header else None

    scheme = find_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' was not found in the verified dataset."
        )

    # Fetch user profile & project server-side
    profile: Optional[Dict[str, Any]] = None
    project: Optional[Dict[str, Any]] = None

    if is_mock:
        profile = DEMO_PROFILES_STORE.get(user_id)
        project = DEMO_PROJECTS_STORE.get(user_id)
    else:
        profile = await fetch_profile_from_supabase(user_id, access_token=token)
        raw_project = await fetch_project_from_supabase(user_id, access_token=token)
        project = unpack_project_details(raw_project) if raw_project else None
        if not project and is_mock:
            project = DEMO_PROJECTS_STORE.get(user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please complete entrepreneur profile registration first to perform eligibility gap analysis."
        )

    gap_analysis = perform_eligibility_gap_analysis(scheme, profile, project)

    return {"success": True, "gap_analysis": gap_analysis}


# ============================================================================
# Main Entry Point for Local Development
# ============================================================================


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    logger.info(f"Starting SchemeAI Backend on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
