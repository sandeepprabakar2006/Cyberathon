"""
NetDictator — FastAPI Backend
main.py: Application entry point, VPC-aware security pipeline with risk scoring.

Architecture:
  - Engine runs in PRIVATE subnet of AWS VPC
  - Layer 1: NLP Model  → assigns file sensitivity + NLP risk score (0-60)
  - Layer 2: IP Verifier → detects VPC internal vs external IP + IP risk score (0-40)
  - Layer 3: Risk Score  → combined score (0-100) → LOW / MEDIUM / HIGH risk band
  - Layer 4: Protection  → Encrypt (external/HIGH), Mask (internal/MEDIUM), Plain (LOW)
"""

import logging
import uuid
from dotenv import load_dotenv
load_dotenv()  # Load .env before any module reads environment variables

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from s3_handler import fetch_file_from_s3, S3FetchError
from nlp_classifier import get_nlp_risk_score, SensitivityLevel
from ip_checker import get_ip_risk_score, NetworkType
from iam_checker import get_role_permissions, RolePermission
from security_layer import apply_security_action, SecurityAction

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("NetDictator")

# ─── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="NetDictator",
    description=(
        "A VPC-aware supreme data authority. Runs in the private subnet. "
        "Processes file access requests through a 4-layer security pipeline: "
        "NLP classification → IP verification → Risk scoring → Data protection."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS Middleware ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Lock to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Risk Score Bands ───────────────────────────────────────────────────────────────
# NLP score:  0–60  (file content sensitivity, keyword density + PII detection)
# IP score:   0–20  (external = +20, internal = 0)
# Total:      0–80
#
# Why 20 for external (not 40)?
#   With 40, even the canteen menu (NLP=24) scored 24+40=64 → always HIGH.
#   All 3 files kept hitting ENCRYPT_AND_MASK only. Masking and tokenization never fired.
#   With 20: canteen(24)+20=44 → MEDIUM, payroll(52)+20=72 → HIGH. All 3 actions trigger.
#
# Score bands:
#   0–24  : LOW    — non-sensitive data, minimal risk
#   25–55 : MEDIUM — moderate sensitivity, controlled exposure
#   56–80 : HIGH   — sensitive file from untrusted network
RISK_LOW_MAX    = 24
RISK_MEDIUM_MAX = 55
# anything > 55 = HIGH


def get_risk_band(score: int) -> str:
    if score <= RISK_LOW_MAX:   return "LOW"
    if score <= RISK_MEDIUM_MAX: return "MEDIUM"
    return "HIGH"


def compute_risk_score(nlp_score: int, raw_ip_score: int, user_role: str,
                       network: NetworkType) -> tuple[int, int, int]:
    """
    Returns (nlp_score, adjusted_ip_score, total).

    Internal VPC  : ip_score = 0 always (VPC boundary = trust boundary).
    External      : ip_score = 20 base, reduced slightly for trusted roles.
    """
    _ROLE_IP_REDUCTION = {
        "admin":           5,    # trusted but outside  → 20-5=15
        "finance-manager": 5,    # trusted but outside  → 20-5=15
        "data-analyst":    0,    # external role, no reduction
        "external-auditor":0,    # expected external, no reduction
        "guest":          -10,   # hostile → 20+10=30
    }
    if network == NetworkType.INTERNAL:
        return nlp_score, 0, nlp_score

    reduction    = _ROLE_IP_REDUCTION.get(user_role, 0)
    adjusted_ip  = max(0, min(30, raw_ip_score - reduction))
    return nlp_score, adjusted_ip, nlp_score + adjusted_ip



# ─── Request / Response Schemas ─────────────────────────────────────────────────
class FileRequest(BaseModel):
    file_name: str
    user_ip: str
    user_role: str

    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "payroll_march_2026.txt",
                "user_ip": "10.0.1.45",
                "user_role": "admin",
            }
        }


class FileResponse(BaseModel):
    request_id:      str
    file_name:       str
    sensitivity:     str          # IMPORTANT / MEDIUM / NORMAL
    user_type:       str          # internal / external
    intent:          str          # verification / unverified (possible fraud)
    iam_permission:  str
    nlp_score:       int          # NLP layer contribution (0-60)
    ip_score:        int          # IP layer contribution after role adjustment (0-40)
    risk_score:      int          # Combined risk score (0-100)
    risk_band:       str          # LOW / MEDIUM / HIGH
    security_action: str          # none / plain_access / masking / encrypt_and_mask / hybrid_encryption
    ops_applied:     str          # Plain English description of what was done
    processed_data:  str
    message:         str


# ─── Layer 3: Corrected Decision Engine ─────────────────────────────────────────
def decide_action(
    risk_band:   str,
    network:     NetworkType,
    sensitivity: SensitivityLevel,
    permission:  RolePermission,
    user_role:   str,
) -> tuple[SecurityAction, str]:
    """
    Corrected decision matrix:

    INTERNAL (VPC trusted) — always plain/nil regardless of file sensitivity:
      Any valid role + internal IP → trust VPC boundary → no security ops needed
      Logic: the VPC perimeter is the security. If you're inside, you're approved.

    EXTERNAL (outside VPC) — risk drives action:
      Admin / Finance-Manager (trusted role, wrong network):
        → ENCRYPT_AND_MASK (mask PII first, then encrypt whole thing)
        → Reason: they're trusted enough to get data, but it must be protected in transit
      Data-Analyst / External-Auditor (external roles):
        → HYBRID_ENCRYPTION if HIGH risk
        → TOKENIZATION if MEDIUM risk
      Guest → always DENIED (handled by IAM check before this)

    Returns (SecurityAction, ops_applied_description)
    """
    # Step 0: IAM gate — DENIED roles are blocked before reaching here
    if permission == RolePermission.DENIED:
        raise HTTPException(
            status_code=403,
            detail="Access denied: IAM role does not have permission to access this resource.",
        )

    # ──────────────────────────────────────────────────
    # COMPLETE ACTION DECISION MATRIX
    # ──────────────────────────────────────────────────
    # NETWORK  | SENSITIVITY | RISK BAND  | ACTION
    # ──────────────────────────────────────────────────
    # INTERNAL | IMPORTANT   | any        | MASKING   (PII hidden, file visible)
    # INTERNAL | MEDIUM/LOW  | any        | NONE      (trusted VPC, nil ops)
    # EXTERNAL | any         | HIGH       | ENCRYPT+MASK (dual-layer)
    # EXTERNAL | any         | MEDIUM     | TOKENIZATION (PII replaced with tokens)
    # EXTERNAL | any         | LOW        | PLAIN_ACCESS (non-sensitive)
    # ──────────────────────────────────────────────────
    # Real file scores (for reference):
    #   payroll_march_2026.txt        NLP=52 (IMPORTANT) → 52+20=72 → HIGH
    #   project_titan_notes.txt       NLP~30 (MEDIUM)    → 30+20=50 → MEDIUM
    #   office_canteen_menu.txt       NLP~24 (MEDIUM)    → 24+20=44 → MEDIUM
    #   (internal users: ip=0, so payroll=52 stays MEDIUM → masking)
    # ──────────────────────────────────────────────────

    if network == NetworkType.INTERNAL:
        # VPC trusted — apply light masking for IMPORTANT files, nil for rest
        if sensitivity == SensitivityLevel.IMPORTANT:
            return (
                SecurityAction.MASKING,
                "PII fields masked (salary/email/SSN) — internal user, sensitive file"
            )
        return (SecurityAction.NONE, "nil — internal VPC trusted user, non-sensitive file")

    # EXTERNAL — risk band drives action
    if risk_band == "HIGH":
        return (
            SecurityAction.ENCRYPT_AND_MASK,
            "Step 1: PII masked (salary/email/SSN/cards) → Step 2: AES-256-CBC + RSA-2048-OAEP encryption"
        )

    if risk_band == "MEDIUM":
        return (
            SecurityAction.TOKENIZATION,
            "sensitive values (SSN, emails, card numbers) replaced with secure SHA-256 tokens"
        )

    # LOW risk external
    return (
        SecurityAction.PLAIN_ACCESS,
        "plain access — low-sensitivity file, external risk minimal"
    )


# ─── Main Endpoint ──────────────────────────────────────────────────────────────
@app.post("/request-file", response_model=FileResponse, status_code=200)
async def request_file(payload: FileRequest, request: Request):
    """
    POST /request-file

    4-Layer Security Pipeline (VPC Architecture):
      Layer 1 → NLP Model:     Read file content → sensitivity + NLP score (0-60)
      Layer 2 → IP Verifier:   Check if IP is VPC internal → IP score (0-40)
      Layer 3 → Risk Scorer:   Combined score (0-100) → LOW / MEDIUM / HIGH band
      Layer 4 → Protector:     Apply Encrypt / Mask / Tokenize / Plain Access
    """
    request_id = str(uuid.uuid4())[:8].upper()
    logger.info(
        "▶ [%s] Incoming request — file='%s'  ip='%s'  role='%s'",
        request_id, payload.file_name, payload.user_ip, payload.user_role,
    )

    # ── Layer 0: Fetch file from S3 (Private Subnet → S3 via VPC Endpoint) ──────
    try:
        logger.info("[%s] Fetching '%s' from S3...", request_id, payload.file_name)
        raw_content: str = await fetch_file_from_s3(payload.file_name)
        logger.info("[%s] File fetched (%d chars)", request_id, len(raw_content))
    except S3FetchError as exc:
        logger.error("[%s] S3 fetch failed: %s", request_id, exc)
        raise HTTPException(status_code=404, detail=str(exc))

    # ── Layer 1: NLP Model — Sensitivity + NLP Risk Score ─────────────────────
    logger.info("[%s] LAYER 1 → NLP Analysis...", request_id)
    sensitivity, raw_nlp_score = get_nlp_risk_score(raw_content)
    logger.info(
        "[%s] LAYER 1 ✓ Sensitivity=%s  NLP Score=%d/60",
        request_id, sensitivity.value.upper(), raw_nlp_score,
    )

    # ── Layer 2: IP Verification — VPC Internal vs External ──────────────────
    logger.info("[%s] LAYER 2 → IP Verification for %s...", request_id, payload.user_ip)
    network_type, raw_ip_score = get_ip_risk_score(payload.user_ip)

    intent = (
        "verification — trusted VPC internal"
        if network_type == NetworkType.INTERNAL
        else "unverified — possible fraud/exfiltration"
    )
    logger.info(
        "[%s] LAYER 2 ✓ Network=%s  Raw IP Score=%d/40  Intent=%s",
        request_id, network_type.value.upper(), raw_ip_score, intent,
    )

    # ── Layer 3: IAM Check + Risk Scoring ────────────────────────────────
    logger.info("[%s] LAYER 3 → IAM + Risk Scoring...", request_id)
    permission = get_role_permissions(payload.user_role)

    nlp_score, ip_score, risk_score = compute_risk_score(
        raw_nlp_score, raw_ip_score, payload.user_role, network_type
    )
    risk_band = get_risk_band(risk_score)

    logger.info(
        "[%s] LAYER 3 ✓ IAM=%s  NLP(%d) + IP(%d, role-adjusted) = Risk %d/100 → %s RISK",
        request_id, permission.value.upper(),
        nlp_score, ip_score, risk_score, risk_band,
    )

    # ── Layer 4: Decide + Apply Protection ──────────────────────────────
    logger.info("[%s] LAYER 4 → Applying data protection...", request_id)
    action, ops_applied = decide_action(
        risk_band, network_type, sensitivity, permission, payload.user_role
    )

    processed_data = apply_security_action(action, raw_content)
    logger.info(
        "[%s] LAYER 4 ✓ Action=%s  Ops: %s",
        request_id, action.value.upper(), ops_applied,
    )

    # ── Response ──────────────────────────────────────────────────────────────────
    response = FileResponse(
        request_id=request_id,
        file_name=payload.file_name,
        sensitivity=sensitivity.value,
        user_type=network_type.value,
        intent=intent,
        iam_permission=permission.value,
        nlp_score=nlp_score,
        ip_score=ip_score,
        risk_score=risk_score,
        risk_band=risk_band,
        security_action=action.value,
        ops_applied=ops_applied,
        processed_data=processed_data,
        message=(
            f"[RISK:{risk_band}|SCORE:{risk_score}/100] "
            f"Sensitivity: {sensitivity.value.upper()} | "
            f"Action: {action.value.replace('_', ' ').title()} | "
            f"Ops: {ops_applied}"
        ),
    )

    logger.info(
        "✅ [%s] COMPLETE — risk=%s(%d)  sensitivity=%s  ip=%s  action=%s",
        request_id, risk_band, risk_score,
        sensitivity.value, network_type.value, action.value,
    )
    return response


# ─── Auto-detect Caller IP ──────────────────────────────────────────────────────
@app.get("/my-ip", tags=["Monitoring"])
async def get_my_ip(request: Request):
    """
    Returns the real IP address of whoever is calling this endpoint.
    The dashboard uses this to auto-fill the user_ip field.
    """
    # Check X-Forwarded-For header first (for requests behind a load balancer/proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host

    network_type, ip_score = get_ip_risk_score(ip)
    return {
        "ip": ip,
        "network_type": network_type.value,
        "ip_risk_score": ip_score,
        "intent": (
            "verification (trusted VPC internal)"
            if network_type == NetworkType.INTERNAL
            else "unverified — possible fraud/exfiltration"
        ),
    }


# ─── List S3 Bucket Files ───────────────────────────────────────────────────────
@app.get("/list-files", tags=["Monitoring"])
async def list_s3_files():
    """
    Returns the list of files available in the S3 bucket.
    The dashboard uses this to populate the file selector dropdown.
    """
    import boto3, os
    from botocore.exceptions import NoCredentialsError, ClientError
    try:
        s3 = boto3.client("s3", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        bucket = os.environ.get("S3_BUCKET_NAME", "")
        resp = s3.list_objects_v2(Bucket=bucket)
        files = [
            {
                "name": obj["Key"],
                "size_bytes": obj["Size"],
                "last_modified": obj["LastModified"].strftime("%Y-%m-%d %H:%M UTC"),
            }
            for obj in resp.get("Contents", [])
        ]
        return {"bucket": bucket, "file_count": len(files), "files": files}
    except (NoCredentialsError, ClientError) as e:
        raise HTTPException(status_code=503, detail=f"S3 connection error: {e}")


# ─── Health Check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Returns operational status of all 4 engine layers."""
    return {
        "status": "operational",
        "engine": "Adaptive Data Protection Engine",
        "version": "2.0.0",
        "architecture": "VPC private-subnet deployment",
        "layers": {
            "layer_1_nlp":      "online — keyword + PII regex scorer (0-60)",
            "layer_2_ip":       "online — VPC CIDR verifier (0-40)",
            "layer_3_risk":     "online — combined risk scorer (0-100)",
            "layer_4_protect":  "online — AES-256 + RSA-2048 + Masking + Tokenization",
        },
        "risk_bands": {
            "LOW":    "0–30   → Plain Access",
            "MEDIUM": "31–60  → Masking (internal) / Tokenization (external)",
            "HIGH":   "61–100 → Hybrid Encryption",
        },
    }


# ─── Dev runner ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
