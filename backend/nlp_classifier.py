"""
nlp_classifier.py — NetDictator Dynamic Inference Engine
────────────────────────────────────────────────────────
Approach:
  - Phase 1: Dynamic Semantic Scoring (Contextual Proximity + Entity Density)
  - Phase 2: Entropy Analysis (Dynamically guessing secrets/keys without keywords)
  - Phase 3: Zero-Shot Classification (Transformers-ready)
"""

import math
import re
import logging
from enum import Enum

logger = logging.getLogger("NetDictator.NLPClassifier")


# ─── Sensitivity Levels ─────────────────────────────────────────────────────────
class SensitivityLevel(str, Enum):
    IMPORTANT = "important"
    MEDIUM    = "medium"
    NORMAL    = "normal"


# ─── Keyword Dictionaries ────────────────────────────────────────────────────────
# Each keyword contributes a score; thresholds decide final level.
_IMPORTANT_KEYWORDS: list[str] = [
    # PII
    "social security", "ssn", "passport", "date of birth", "dob",
    "national id", "tax id", "driver license", "biometric",
    # Financial
    "salary", "payroll", "bank account", "routing number", "credit card",
    "cvv", "iban", "swift", "financial statement", "revenue", "tax return",
    # Credentials / Secrets
    "password", "secret key", "api key", "access token", "private key",
    "aws_secret", "credentials", "auth token", "jwt",
    # Medical / Legal
    "medical record", "diagnosis", "prescription", "hipaa", "patient",
    "legal agreement", "court order", "confidential", "classified",
    # HR
    "employee id", "performance review", "termination", "disciplinary",
]

_MEDIUM_KEYWORDS: list[str] = [
    # Customer
    "customer", "client", "account number", "invoice", "order id",
    "purchase history", "subscription", "loyalty",
    # Business Operations
    "budget", "forecast", "quarterly", "project plan", "meeting notes",
    "vendor", "contract", "proposal", "nda",
    # Audit / Compliance
    "audit log", "access log", "compliance", "policy", "regulation",
    "incident report",
]


# ─── Regex Patterns for High-confidence PII ─────────────────────────────────────
_PII_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),         # SSN
    re.compile(r"\b4[0-9]{12}(?:[0-9]{3})?\b"),   # Visa card
    re.compile(r"\b5[1-5]\d{14}\b"),               # Mastercard
    re.compile(r"\b[A-Z]{2}\d{6}[A-Z]?\b"),       # Passport
    re.compile(r"\b\d{16}\b"),                     # Generic card number
    re.compile(                                     # Email
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    ),
    re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),  # IPv4
]


def _calculate_entropy(text: str) -> float:
    """Dynamically guess if a string is a secret/key by calculating Shannon entropy."""
    if not text: return 0
    prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
    entropy = - sum([p * math.log(p) / math.log(2.0) for p in prob])
    return entropy

def _find_contextual_secrets(text: str) -> int:
    """
    Dynamically guess secrets by looking for 'Labels' near 'High-Entropy Strings'.
    Example: 'api_key: xK92jLpQ...' -> Likely a real secret.
    """
    bonus = 0
    # Search for labels followed by potential secrets (non-whitespace strings of 10+ chars)
    patterns = [r"(?:key|secret|password|token|auth|pwd)\s*[:=]\s*(\S{10,})"]
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        for m in matches:
            # If entropy is high (>3.5), it's likely a real dynamic secret
            if _calculate_entropy(m) > 3.5:
                bonus += 5
    return bonus

def _score_content(text: str) -> tuple[int, int]:
    """
    Hybrid Scoring Engine:
    1. Keywords (Baseline)
    2. Regex PII (Specifics)
    3. Entropy & Context (Dynamic Guessing)
    """
    lowered = text.lower()
    
    # Baseline
    imp_score = sum(lowered.count(kw) for kw in _IMPORTANT_KEYWORDS)
    med_score = sum(lowered.count(kw) for kw in _MEDIUM_KEYWORDS)
    
    # Specific Regex PII
    for pattern in _PII_PATTERNS:
        imp_score += len(pattern.findall(text)) * 4
        
    # Dynamic Guessing: Contextual Secrets
    secret_bonus = _find_contextual_secrets(text)
    imp_score += secret_bonus
    
    # Proximity Bonus: If multiple sensitive things are in the same snippet
    if imp_score > 5 and med_score > 5:
        imp_score += 10 # Contextual cluster detected
        
    return imp_score, med_score


def classify_sensitivity(content: str) -> SensitivityLevel:
    """
    Classify the sensitivity of file content.

    Returns:
        SensitivityLevel enum value (IMPORTANT / MEDIUM / NORMAL).
    """
    if not content or not content.strip():
        logger.warning("Empty content received; defaulting to NORMAL sensitivity.")
        return SensitivityLevel.NORMAL

    imp_score, med_score = _score_content(content)
    logger.debug("NLP scores — IMPORTANT: %d  MEDIUM: %d", imp_score, med_score)

    if imp_score >= 1:
        logger.info("Sensitivity classified as IMPORTANT (score=%d).", imp_score)
        return SensitivityLevel.IMPORTANT
    if med_score >= 1:
        logger.info("Sensitivity classified as MEDIUM (score=%d).", med_score)
        return SensitivityLevel.MEDIUM

    logger.info("Sensitivity classified as NORMAL.")
    return SensitivityLevel.NORMAL


def get_nlp_risk_score(content: str) -> tuple[SensitivityLevel, int]:
    """
    Returns (SensitivityLevel, nlp_risk_score) where nlp_risk_score is 0–60.

    Scoring:
      IMPORTANT → 40 base + min(imp_score * 4, 20) bonus  = up to 60
      MEDIUM    → 20 base + min(med_score * 4, 20) bonus  = up to 40
      NORMAL    → 0

    This score feeds into the combined risk calculator in main.py.
    """
    if not content or not content.strip():
        return SensitivityLevel.NORMAL, 0

    imp_score, med_score = _score_content(content)

    if imp_score >= 1:
        nlp_score = min(40 + imp_score * 4, 60)
        return SensitivityLevel.IMPORTANT, nlp_score
    if med_score >= 1:
        nlp_score = min(20 + med_score * 4, 40)
        return SensitivityLevel.MEDIUM, nlp_score

    return SensitivityLevel.NORMAL, 0


# ─── New: Zero-Shot Dynamic Policy Engine ────────────────────────────────────────
def classify_zero_shot(content: str, candidate_labels: list[str] = None) -> str:
    """
    The ultimate dynamic model: Uses Zero-Shot classification to guess categories 
    without ANY pre-defined keywords.
    """
    if candidate_labels is None:
        candidate_labels = ["confidential", "financial", "operational", "public"]
        
    try:
        from transformers import pipeline
        # Using a very small, fast distilled model for demo
        classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")
        
        snippet = content[:1000]
        res = classifier(snippet, candidate_labels=candidate_labels)
        top_label = res['labels'][0]
        
        logger.info("Zero-Shot Dynamic Guess: %s (confidence: %.2f)", top_label, res['scores'][0])
        return top_label
    except Exception as e:
        logger.warning("Zero-Shot Model not loaded. Using Dynamic Heuristic instead.")
        return "heuristic"
