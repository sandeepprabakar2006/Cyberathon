"""
ip_checker.py
─────────────
Network origin classifier for the Adaptive Data Protection Engine.

Determines whether a request originates from:
  - INTERNAL: An IP within a trusted VPC CIDR range
  - EXTERNAL: Any IP outside VPC ranges (public internet, unknown network)

Configuration:
  Set TRUSTED_CIDR_RANGES in the environment as a comma-separated list
  of CIDR blocks, or update VPC_CIDR_RANGES directly below.
"""

import os
import ipaddress
import logging

logger = logging.getLogger("ADPE.IPChecker")

# ─── Network Type Enum ─────────────────────────────────────────────────────────
from enum import Enum

class NetworkType(str, Enum):
    INTERNAL = "internal"   # Trusted VPC or private range
    EXTERNAL = "external"   # Public internet / untrusted network


# ─── Trusted VPC CIDR Ranges ───────────────────────────────────────────────────
# Default: AWS VPC private ranges + common on-premise subnets.
# Override at runtime via environment variable for flexibility.
_DEFAULT_CIDR_RANGES: list[str] = [
    "10.0.0.0/8",        # AWS VPC — class A private
    "172.16.0.0/12",     # AWS VPC — class B private
    "192.168.0.0/16",    # Local / on-premise private
    "100.64.0.0/10",     # AWS shared address space (VPN/Direct Connect)
]


def _load_trusted_ranges() -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """
    Load trusted CIDR ranges from environment or defaults.
    Parses and returns a list of ipaddress Network objects.
    """
    env_cidrs = os.environ.get("TRUSTED_CIDR_RANGES", "")
    raw_cidrs = (
        [c.strip() for c in env_cidrs.split(",") if c.strip()]
        if env_cidrs
        else _DEFAULT_CIDR_RANGES
    )
    networks = []
    for cidr in raw_cidrs:
        try:
            networks.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError:
            logger.warning("Invalid CIDR range ignored: '%s'", cidr)
    logger.debug("Loaded %d trusted CIDR ranges.", len(networks))
    return networks


# Pre-load trusted networks at module import time for efficiency
_TRUSTED_NETWORKS = _load_trusted_ranges()


def classify_user_network(user_ip: str) -> NetworkType:
    """
    Classify whether a user's IP belongs to a trusted internal VPC or external network.

    VPC Architecture rules:
      - Only explicitly provisioned VPC CIDR ranges are INTERNAL (trusted)
      - Loopback (127.0.0.1 / ::1): EXTERNAL — localhost is the engine's own machine,
        NOT a trusted user origin. Direct loopback access bypasses VPC routing and is
        treated as unverified external access.
      - All other IPs not matching VPC CIDRs: EXTERNAL
    """
    try:
        addr = ipaddress.ip_address(user_ip)
    except ValueError:
        logger.warning("Invalid IP address: '%s'. Treating as EXTERNAL.", user_ip)
        return NetworkType.EXTERNAL

    # Loopback explicitly classified as EXTERNAL per VPC architecture.
    # Localhost is the engine machine itself, NOT a trusted VPC user origin.
    if addr.is_loopback:
        logger.info(
            "IP %s is loopback (localhost) — classified as EXTERNAL. "
            "Localhost is not a trusted VPC user endpoint per architecture.",
            user_ip,
        )
        return NetworkType.EXTERNAL

    for network in _TRUSTED_NETWORKS:
        if addr in network:
            logger.info("IP %s matched %s — INTERNAL.", user_ip, network)
            return NetworkType.INTERNAL

    logger.info("IP %s — EXTERNAL (no VPC range match).", user_ip)
    return NetworkType.EXTERNAL


def get_ip_risk_score(user_ip: str) -> tuple[NetworkType, int]:
    """
    Returns (NetworkType, ip_risk_score) where ip_risk_score contributes to
    the combined risk score.

    VPC Architecture:
      Private subnet (internal) → trusted employee/service → score: 0
        Intent: legitimate data access
      External IP              → outside VPC → possible fraud/exfil → score: 40
        Intent: unverified, treat as high risk

    Combined with NLP score (0–60), total risk score = 0–100.

    Score bands:
      0–30  → LOW    risk
      31–60 → MEDIUM risk
      61–100→ HIGH   risk
    """
    network = classify_user_network(user_ip)
    if network == NetworkType.INTERNAL:
        logger.info("IP risk contribution: 0 (INTERNAL — VPC private subnet)")
        return network, 0
    else:
        logger.info("IP risk contribution: 20 (EXTERNAL — outside VPC, untrusted origin)")
        return network, 20


def is_ip_in_range(user_ip: str, cidr: str) -> bool:
    """
    Utility: Check if a specific IP falls within a given CIDR range.

    Args:
        user_ip: IP address to check.
        cidr:    CIDR block string (e.g. '10.0.0.0/8').

    Returns:
        True if the IP is within the CIDR, False otherwise.
    """
    try:
        return ipaddress.ip_address(user_ip) in ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return False


def get_trusted_ranges() -> list[str]:
    """Return the currently loaded trusted CIDR ranges as strings."""
    return [str(n) for n in _TRUSTED_NETWORKS]
