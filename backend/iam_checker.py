"""
iam_checker.py
──────────────
IAM role-based access control module for the Adaptive Data Protection Engine.

Responsibilities:
  - Maps user IAM role strings to permission levels (READ, RESTRICTED, DENIED)
  - Optionally calls the AWS IAM API to validate live role policies
  - Provides a simple, extensible role permission registry

Permission Levels:
  READ        → User may access file content (protection still applied)
  RESTRICTED  → User may access masked/tokenized version only
  DENIED      → Access is blocked regardless of sensitivity level
"""

import os
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger("ADPE.IAMChecker")


# ─── Permission Levels ─────────────────────────────────────────────────────────
class RolePermission(str, Enum):
    READ       = "read"        # Full access (protection applied separately)
    RESTRICTED = "restricted"  # Partial access (masking/tokenization enforced)
    DENIED     = "denied"      # No access


# ─── Role Permission Registry ──────────────────────────────────────────────────
# In production, this should be replaced with an AWS IAM policy lookup.
# Role names are normalised to lowercase before lookup.
_ROLE_PERMISSION_MAP: dict[str, RolePermission] = {
    # Administrators / IT
    "admin":                  RolePermission.READ,
    "it-administrator":       RolePermission.READ,
    "administrator":          RolePermission.READ,
    "sysadmin":               RolePermission.READ,
    "cloud-admin":            RolePermission.READ,

    # Finance & HR (internal sensitive roles)
    "finance-manager":        RolePermission.READ,
    "hr-manager":             RolePermission.READ,
    "payroll-officer":        RolePermission.READ,

    # Analysts (restricted — see only masked/tokenized data)
    "data-analyst":           RolePermission.RESTRICTED,
    "business-analyst":       RolePermission.RESTRICTED,
    "security-analyst":       RolePermission.RESTRICTED,
    "compliance-officer":     RolePermission.RESTRICTED,

    # External / Auditor (restricted)
    "external-auditor":       RolePermission.RESTRICTED,
    "external-reviewer":      RolePermission.RESTRICTED,
    "vendor":                 RolePermission.RESTRICTED,

    # Denied roles
    "guest":                  RolePermission.DENIED,
    "unknown":                RolePermission.DENIED,
    "anonymous":              RolePermission.DENIED,
    "unauthenticated":        RolePermission.DENIED,
}

# Fallback permission for roles not in the registry
_DEFAULT_PERMISSION: RolePermission = RolePermission.DENIED


def get_role_permissions(user_role: str) -> RolePermission:
    """
    Resolve the permission level for a given IAM role name.

    Lookup order:
      1. Normalised role name in the local registry
      2. (Optional) Live AWS IAM policy check if ENABLE_AWS_IAM_CHECK=true
      3. Default DENIED for unknown roles

    Args:
        user_role: IAM role string from the request.

    Returns:
        RolePermission enum value.
    """
    normalised = user_role.strip().lower()

    permission = _ROLE_PERMISSION_MAP.get(normalised)
    if permission is not None:
        logger.info(
            "IAM role '%s' resolved to permission '%s' (registry lookup).",
            user_role, permission.value,
        )
        return permission

    # Optional: Live AWS IAM check
    if os.environ.get("ENABLE_AWS_IAM_CHECK", "false").lower() == "true":
        live_permission = _check_aws_iam_policy(user_role)
        if live_permission is not None:
            return live_permission

    logger.warning(
        "IAM role '%s' not found in registry. Defaulting to DENIED.", user_role
    )
    return _DEFAULT_PERMISSION


def _check_aws_iam_policy(role_name: str) -> Optional[RolePermission]:
    """
    [Optional] Query AWS IAM to verify whether a role has S3 GetObject permission.

    Requires:
      - boto3 installed
      - Lambda/EC2 role with iam:SimulatePrincipalPolicy attached

    Returns:
        RolePermission if resolvable, None if check fails or unavailable.
    """
    try:
        import boto3
        from botocore.exceptions import ClientError, BotoCoreError

        iam = boto3.client("iam")
        arn_prefix = os.environ.get("AWS_ACCOUNT_ARN_PREFIX", "arn:aws:iam::123456789012:role")
        role_arn = f"{arn_prefix}/{role_name}"

        bucket = os.environ.get("S3_BUCKET_NAME", "adpe-secure-bucket")
        resource_arn = f"arn:aws:s3:::{bucket}/*"

        response = iam.simulate_principal_policy(
            PolicySourceArn=role_arn,
            ActionNames=["s3:GetObject"],
            ResourceArns=[resource_arn],
        )

        for result in response.get("EvaluationResults", []):
            decision: str = result.get("EvalDecision", "implicitDeny")
            if decision == "allowed":
                logger.info("AWS IAM: role '%s' → ALLOWED → READ", role_name)
                return RolePermission.READ
            else:
                logger.info("AWS IAM: role '%s' → DENIED", role_name)
                return RolePermission.DENIED

    except Exception as exc:
        logger.warning("AWS IAM policy check failed for '%s': %s", role_name, exc)

    return None


def list_registered_roles() -> dict[str, str]:
    """Return all roles and their permissions from the registry (for auditing)."""
    return {role: perm.value for role, perm in _ROLE_PERMISSION_MAP.items()}
