"""
security_layer.py
─────────────────
Data protection module for the Adaptive Data Protection Engine.

Implements five protection techniques:
  1. AES-256 Encryption            → for raw content encryption
  2. RSA Key Encryption            → for hybrid encryption key wrapping
  3. Hybrid Encryption (AES+RSA)   → IMPORTANT sensitivity level
  4. Data Masking                  → MEDIUM + Internal user
  5. Tokenization                  → MEDIUM + External user
  6. Pseudonymization              → Utility for PII field replacement
  7. Plain Access                  → NORMAL — no transformation
"""

import os
import re
import json
import base64
import hashlib
import logging
import secrets
import string
from enum import Enum
from typing import Any

# Cryptography library — install: pip install cryptography
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger("ADPE.SecurityLayer")

# ─── Security Action Enum ──────────────────────────────────────────────────────
class SecurityAction(str, Enum):
    HYBRID_ENCRYPTION  = "hybrid_encryption"    # AES-256 + RSA-2048 full encryption
    ENCRYPT_AND_MASK   = "encrypt_and_mask"      # External trusted admin → mask then encrypt
    MASKING            = "masking"               # Medium sensitivity, internal
    TOKENIZATION       = "tokenization"          # Medium sensitivity, external
    PSEUDONYMIZATION   = "pseudonymization"      # PII field replacement
    PLAIN_ACCESS       = "plain_access"          # Low risk, internal trusted user
    NONE               = "none"                  # Internal + zero NLP risk — nil operations


# ─── RSA Key Loading / Generation ─────────────────────────────────────────────
def _load_or_generate_rsa_keys() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """
    Load RSA keys from environment-specified PEM files, or generate an
    ephemeral 2048-bit keypair for demonstration.

    In production:
      Set RSA_PRIVATE_KEY_PATH and RSA_PUBLIC_KEY_PATH environment variables
      pointing to PEM files managed by AWS KMS or Secrets Manager.
    """
    priv_path = os.environ.get("RSA_PRIVATE_KEY_PATH")
    pub_path  = os.environ.get("RSA_PUBLIC_KEY_PATH")

    if priv_path and pub_path and os.path.exists(priv_path) and os.path.exists(pub_path):
        with open(priv_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(pub_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
        logger.info("Loaded RSA keys from filesystem.")
    else:
        logger.warning("RSA key files not configured — generating ephemeral 2048-bit keypair.")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )
        public_key = private_key.public_key()
    return private_key, public_key


# Generate keys once at module load
_RSA_PRIVATE_KEY, _RSA_PUBLIC_KEY = _load_or_generate_rsa_keys()


# ─── 1. AES-256 Encryption ────────────────────────────────────────────────────
def aes_encrypt(plaintext: str, key: bytes | None = None) -> dict[str, str]:
    """
    Encrypt plaintext using AES-256-CBC.

    Args:
        plaintext: UTF-8 text to encrypt.
        key:       32-byte AES key. If None, a random key is generated.

    Returns:
        Dict with 'ciphertext_b64', 'iv_b64', and 'key_b64' (base64-encoded).
    """
    if key is None:
        key = os.urandom(32)  # 256-bit random key

    iv = os.urandom(16)  # 128-bit IV
    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode("utf-8")) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return {
        "ciphertext_b64": base64.b64encode(ciphertext).decode(),
        "iv_b64":         base64.b64encode(iv).decode(),
        "key_b64":        base64.b64encode(key).decode(),
    }


def aes_decrypt(ciphertext_b64: str, key_b64: str, iv_b64: str) -> str:
    """
    Decrypt AES-256-CBC ciphertext.

    Args:
        ciphertext_b64: Base64-encoded ciphertext.
        key_b64:        Base64-encoded 32-byte AES key.
        iv_b64:         Base64-encoded 16-byte IV.

    Returns:
        Decrypted plaintext string.
    """
    key        = base64.b64decode(key_b64)
    iv         = base64.b64decode(iv_b64)
    ciphertext = base64.b64decode(ciphertext_b64)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = sym_padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded) + unpadder.finalize()
    return plaintext.decode("utf-8")


# ─── 2. RSA Key Wrapping ──────────────────────────────────────────────────────
def rsa_encrypt_key(aes_key_bytes: bytes) -> str:
    """
    Encrypt an AES key using RSA-OAEP with SHA-256.
    This is the 'key wrapping' step of hybrid encryption.

    Args:
        aes_key_bytes: Raw 32-byte AES key.

    Returns:
        Base64-encoded RSA-encrypted key.
    """
    encrypted = _RSA_PUBLIC_KEY.encrypt(
        aes_key_bytes,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return base64.b64encode(encrypted).decode()


def rsa_decrypt_key(encrypted_key_b64: str) -> bytes:
    """
    Decrypt an RSA-OAEP encrypted AES key using the private key.

    Args:
        encrypted_key_b64: Base64-encoded encrypted AES key.

    Returns:
        Raw AES key bytes.
    """
    encrypted = base64.b64decode(encrypted_key_b64)
    return _RSA_PRIVATE_KEY.decrypt(
        encrypted,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


# ─── 3. Hybrid Encryption (AES + RSA) ────────────────────────────────────────
def hybrid_encrypt(plaintext: str) -> str:
    """
    Apply hybrid encryption:
      - Generate random AES-256 key
      - Encrypt content with AES-256-CBC
      - Wrap AES key with RSA-2048-OAEP public key
      - Return JSON bundle with all components

    Used for IMPORTANT sensitivity level.

    Args:
        plaintext: Raw file content.

    Returns:
        JSON string containing encrypted ciphertext, IV, and wrapped key.
    """
    aes_key = os.urandom(32)
    aes_result = aes_encrypt(plaintext, key=aes_key)
    wrapped_key = rsa_encrypt_key(aes_key)

    bundle = {
        "algorithm": "AES-256-CBC + RSA-2048-OAEP",
        "ciphertext": aes_result["ciphertext_b64"],
        "iv":         aes_result["iv_b64"],
        "wrapped_key": wrapped_key,
        "protection": "hybrid_encryption",
    }
    logger.info("Hybrid encryption applied successfully.")
    return json.dumps(bundle)


# ─── 4. Data Masking ──────────────────────────────────────────────────────────
# Regex patterns for common sensitive fields to mask
_MASK_PATTERNS: list[tuple[re.Pattern, Any]] = [
    # SSN: 123-45-6789 → ***-**-****
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),     lambda m: "***-**-****"),
    # Visa card
    (re.compile(r"\b4[0-9]{12}(?:[0-9]{3})?\b"), lambda m: "**** **** **** ****"),
    # Mastercard
    (re.compile(r"\b5[1-5]\d{14}\b"),            lambda m: "**** **** **** ****"),
    # Generic 16-digit card
    (re.compile(r"\b\d{16}\b"),                  lambda m: "**** **** **** ****"),
    # salary/payroll followed by number: "salary: 95000" → "salary: ****"
    (re.compile(r"(salary\s*[:\s])\s*[\d,\.]+",   re.IGNORECASE),
     lambda m: m.group(1) + "****"),
    (re.compile(r"(payroll\s*[:\s])\s*[\d,\.]+",  re.IGNORECASE),
     lambda m: m.group(1) + "****"),
    # password = secret → password = ********
    (re.compile(r"(password\s*[=:\s])\s*\S+",     re.IGNORECASE),
     lambda m: m.group(1) + "********"),
    # api_key = abc123 → api_key = ********
    (re.compile(r"(api.?key\s*[=:\s])\s*\S+",     re.IGNORECASE),
     lambda m: m.group(1) + "********"),
    # Email: john@example.com → jo****@example.com
    (re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
     lambda m: m.group()[:2] + "****@" + m.group().split("@")[-1]),
]


def mask_data(content: str) -> str:
    """
    Apply pattern-based masking to sensitive fields in text content.
    Sensitive values are replaced with masked placeholders.

    Used for MEDIUM sensitivity + Internal user.

    Args:
        content: Raw file content.

    Returns:
        Content with sensitive fields masked.
    """
    result = content
    for pattern, replacement in _MASK_PATTERNS:
        if callable(replacement):
            result = pattern.sub(replacement, result)
        else:
            result = pattern.sub(replacement, result)
    logger.info("Data masking applied.")
    return result


# ─── 5. Tokenization ──────────────────────────────────────────────────────────
def tokenize_data(content: str) -> tuple[str, dict[str, str]]:
    """
    Replace identified sensitive values with opaque cryptographic tokens.
    Returns the tokenised content and a token vault mapping.

    In production:
      - Store the token vault in an encrypted database (DynamoDB/RDS)
      - Use the vault for controlled de-tokenization by authorised services

    Used for MEDIUM sensitivity + External user.

    Args:
        content: Raw file content.

    Returns:
        (tokenised_content, token_vault) where token_vault maps
        token → original value (keep this secure).
    """
    vault: dict[str, str] = {}

    def make_token(value: str) -> str:
        """Generate a deterministic token from a value using SHA-256."""
        digest = hashlib.sha256(value.encode()).hexdigest()[:16].upper()
        token = f"TKN-{digest}"
        vault[token] = value
        return token

    result = content

    # Tokenise SSN, card numbers, emails
    tokenise_patterns = [
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        re.compile(r"\b\d{16}\b"),
        re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    ]
    for pattern in tokenise_patterns:
        result = pattern.sub(lambda m: make_token(m.group()), result)

    logger.info("Tokenization applied — %d tokens generated.", len(vault))
    return result, vault


# ─── 6. Pseudonymization ──────────────────────────────────────────────────────
def pseudonymize_data(content: str, seed: str = "adpe-seed") -> str:
    """
    Replace PII names and identifiers with consistent pseudonyms.
    Same input always produces same pseudonym (seeded hashing).

    Useful for analytics and testing pipelines.

    Args:
        content:  Raw file content.
        seed:     Seed string to make pseudonyms consistent per deployment.

    Returns:
        Content with PII replaced by pseudonyms.
    """
    name_pattern = re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b")

    def to_pseudonym(m: re.Match) -> str:
        combined = seed + m.group()
        digest = hashlib.md5(combined.encode()).hexdigest()[:6]
        return f"User_{digest.upper()}"

    result = name_pattern.sub(to_pseudonym, content)
    logger.info("Pseudonymization applied.")
    return result


# ─── 7. Plain Access ──────────────────────────────────────────────────────────
def plain_access(content: str) -> str:
    """
    Return raw content without any transformation.
    Only applied to NORMAL sensitivity files for authenticated users.

    Args:
        content: Raw file content.

    Returns:
        Unchanged content.
    """
    logger.info("Plain access granted — no transformation applied.")
    return content


# ─── Dispatcher ───────────────────────────────────────────────────────────────
def apply_security_action(action: SecurityAction, content: str) -> str:
    """
    Apply the appropriate data protection technique based on the security action.

    Actions:
      NONE             → Internal trusted user, no risk — return raw content, nil ops
      PLAIN_ACCESS     → Low-risk file, trusted user — return raw content
      MASKING          → Medium sensitivity + internal — mask PII fields, preserve structure
      TOKENIZATION     → Medium sensitivity + external — replace values with tokens
      ENCRYPT_AND_MASK → External admin — mask sensitive fields then fully encrypt result
      HYBRID_ENCRYPTION→ High risk external — full AES-256 + RSA-2048 encryption
    """
    if action == SecurityAction.NONE:
        logger.info("No security operation — internal trusted user, nil ops.")
        return content                       # raw content, zero transformation

    if action == SecurityAction.PLAIN_ACCESS:
        return plain_access(content)

    if action == SecurityAction.MASKING:
        return mask_data(content)

    if action == SecurityAction.TOKENIZATION:
        tokenised, vault = tokenize_data(content)
        logger.debug("Token vault entries: %d", len(vault))
        return tokenised

    if action == SecurityAction.ENCRYPT_AND_MASK:
        # Step 1: mask PII fields first (partial visibility)
        masked = mask_data(content)
        # Step 2: encrypt the masked version
        encrypted = hybrid_encrypt(masked)
        logger.info("Encrypt-and-mask applied — masked PII then encrypted for external admin.")
        return encrypted

    if action == SecurityAction.HYBRID_ENCRYPTION:
        return hybrid_encrypt(content)

    if action == SecurityAction.PSEUDONYMIZATION:
        return pseudonymize_data(content)

    logger.error("Unknown SecurityAction: %s", action)
    raise ValueError(f"Unknown security action: {action}")
