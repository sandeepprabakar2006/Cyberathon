"""
nlp_classifier.py
─────────────────
NLP-based file sensitivity classifier for the Adaptive Data Protection Engine.

Approach:
  - Uses a keyword/phrase scoring heuristic (deployable without GPU/model weights)
  - Optionally upgrades to a transformers-based BERT classifier when available
  - Returns one of three sensitivity levels: IMPORTANT | MEDIUM | NORMAL

Sensitivity Rules:
  IMPORTANT  → Contains PII, financial, credentials, medical, or legal data
  MEDIUM     → Contains operational, business, or customer data
  NORMAL     → General purpose documents with no sensitive indicators
"""

import re
import logging
from enum import Enum

logger = logging.getLogger("ADPE.NLPClassifier")


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


def _score_content(text: str) -> tuple[int, int]:
    """
    Score the text against IMPORTANT and MEDIUM keyword lists.
    Returns (important_score, medium_score).
    """
    lowered = text.lower()
    imp_score = sum(lowered.count(kw) for kw in _IMPORTANT_KEYWORDS)
    med_score = sum(lowered.count(kw) for kw in _MEDIUM_KEYWORDS)
    # Bonus points for regex PII matches (weighted higher)
    for pattern in _PII_PATTERNS:
        imp_score += len(pattern.findall(text)) * 3
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


# ─── Optional: BERT-based upgrade ───────────────────────────────────────────────
def classify_with_bert(content: str) -> SensitivityLevel:
    """
    Advanced classifier using a fine-tuned BERT model (requires transformers).
    Falls back to keyword-based classification if model is unavailable.

    Install: pip install transformers torch
    Fine-tune a BERT model on sensitivity labelled data and point MODEL_PATH
    to its directory.

    Args:
        content: Raw text content.

    Returns:
        SensitivityLevel enum value.
    """
    try:
        from transformers import pipeline  # type: ignore
        import os

        model_path = os.environ.get("BERT_MODEL_PATH", "./sensitivity_model")
        classifier = pipeline("text-classification", model=model_path)

        # Truncate to 512 tokens (BERT limit)
        snippet = content[:2000]
        result = classifier(snippet)[0]
        label: str = result["label"].lower()

        mapping = {"important": SensitivityLevel.IMPORTANT,
                   "medium":    SensitivityLevel.MEDIUM,
                   "normal":    SensitivityLevel.NORMAL}
        level = mapping.get(label, SensitivityLevel.NORMAL)
        logger.info("BERT classifier result: %s (confidence=%.2f)", label, result["score"])
        return level

    except Exception as exc:
        logger.warning("BERT classifier unavailable (%s). Falling back to keyword heuristic.", exc)
        return classify_sensitivity(content)
