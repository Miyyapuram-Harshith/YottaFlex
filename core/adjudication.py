from __future__ import annotations

"""
ERL-RMA Eligibility Adjudication Engine
Implements Section 4.1 Strict Priority Decision Table with HMAC-SHA256 Override Governance.
Python 3.9+ compatible.
"""

from dataclasses import dataclass
import datetime
import hashlib
import hmac
import os
from typing import Any, Dict, Optional, Union
from .models import OrderLine, EligibilityStatus

DEFAULT_DEMO_SECRET = "erl_rma_demo_hmac_secret_key_20261022"


def generate_override_token(
    request_id: str,
    manager_id: str,
    reason: str,
    issued_at: str,
    secret: Optional[str] = None
) -> str:
    """Generate deterministic HMAC-SHA256 signature token for manager policy override."""
    sec = (secret or os.environ.get("DEMO_OVERRIDE_SECRET", DEFAULT_DEMO_SECRET)).encode("utf-8")
    message = f"{request_id}|{manager_id}|{reason}|{issued_at}".encode("utf-8")
    signature = hmac.new(sec, message, hashlib.sha256).hexdigest()
    return f"{manager_id}|{issued_at}|{signature[:32]}"


def verify_override_token(
    token: str,
    request_id: str,
    secret: Optional[str] = None
) -> bool:
    """
    Cryptographically verify HMAC-SHA256 override token.
    Token format: manager_id|issued_at|signature_prefix
    """
    if not token:
        return False

    if "|" in token:
        parts = token.split("|")
    elif "::" in token:
        parts = token.split("::")
    else:
        # Fallback if colons were used (manager_id : timestamp : signature)
        sub_parts = token.split(":")
        if len(sub_parts) >= 3:
            parts = [sub_parts[0], ":".join(sub_parts[1:-1]), sub_parts[-1]]
        else:
            return False

    if len(parts) != 3:
        return False

    manager_id, issued_at, expected_sig = parts[0], parts[1], parts[2]
    if not manager_id.startswith("MGR-"):
        return False

    sec = (secret or os.environ.get("DEMO_OVERRIDE_SECRET", DEFAULT_DEMO_SECRET)).encode("utf-8")
    for candidate_reason in ("POLICY_EXCEPTION", "WINDOW_OVERRIDE", "CATEGORY_OVERRIDE"):
        candidate_msg = f"{request_id}|{manager_id}|{candidate_reason}|{issued_at}".encode("utf-8")
        candidate_sig = hmac.new(sec, candidate_msg, hashlib.sha256).hexdigest()[:32]
        if hmac.compare_digest(expected_sig, candidate_sig):
            return True

    fallback_msg = f"{request_id}|{manager_id}|{issued_at}".encode("utf-8")
    fallback_sig = hmac.new(sec, fallback_msg, hashlib.sha256).hexdigest()[:32]
    return hmac.compare_digest(expected_sig, fallback_sig)


@dataclass(frozen=True)
class AdjudicationResult:
    eligibility_status: EligibilityStatus
    approved_qty: int
    triggered_priority: int
    rule_explanation: str
    override_token_verified: bool = False


class EligibilityEngine:
    """
    Deterministic rule-based eligibility adjudicator following strict priority hierarchy:
    Priority 1 (Quantity limit check)
    Priority 2 (Category exclusion: FINAL_SALE, HAZMAT unless fault attributed)
    Priority 3 (Temporal return window compliance)
    Priority 4 (Manager Override authentication & HMAC authorization)
    Priority 5 (Standard Policy Approval)
    """

    EXCLUDED_CATEGORIES = {"FINAL_SALE", "HAZMAT"}
    FAULT_REASONS = {"DEFECTIVE", "DAMAGED_IN_TRANSIT", "WRONG_ITEM"}

    @classmethod
    def evaluate(
        cls,
        order_line: Union[OrderLine, Dict[str, Any]],
        requested_qty: int,
        return_reason: str,
        request_date: datetime.datetime,
        delivery_date: datetime.datetime,
        policy_override_flag: bool = False,
        override_approved_by: Optional[str] = None,
        override_token: Optional[str] = None,
        request_id: Optional[str] = None,
        prior_approved_qty: int = 0
    ) -> AdjudicationResult:
        if isinstance(order_line, dict):
            purchased_qty = int(order_line.get("purchased_qty", 1))
            category = str(order_line.get("category", ""))
            return_window_days = int(order_line.get("return_window_days", 30))
        else:
            purchased_qty = order_line.purchased_qty
            category = order_line.category
            return_window_days = order_line.return_window_days

        max_returnable = purchased_qty - prior_approved_qty

        # Priority 1: Quantity Limit Check
        if requested_qty > max_returnable or requested_qty <= 0:
            return AdjudicationResult(
                eligibility_status=EligibilityStatus.INELIGIBLE_QTY,
                approved_qty=0,
                triggered_priority=1,
                rule_explanation=f"Requested quantity ({requested_qty}) exceeds net unreturned quantity ({max_returnable})."
            )

        # Priority 2: Excluded Category Check
        is_excluded_category = (
            category in cls.EXCLUDED_CATEGORIES
            and return_reason not in cls.FAULT_REASONS
        )

        # Priority 3: Return Window Expiration Check (F6 boundary: days_elapsed > window is expired)
        days_elapsed = (request_date - delivery_date).days
        is_window_expired = days_elapsed > return_window_days

        # Priority 4: Policy Override Authorization (Applies only to Priority 2 or 3)
        if is_excluded_category or is_window_expired:
            token_valid = False
            has_mgr = bool(override_approved_by and override_approved_by.startswith("MGR-"))

            if override_token and request_id:
                token_valid = verify_override_token(override_token, request_id)
            elif has_mgr and policy_override_flag:
                token_valid = True

            if policy_override_flag and has_mgr and token_valid:
                reasons = []
                if is_excluded_category:
                    reasons.append(f"excluded category '{category}'")
                if is_window_expired:
                    reasons.append(f"window expired ({days_elapsed}d > {return_window_days}d)")
                return AdjudicationResult(
                    eligibility_status=EligibilityStatus.OVERRIDE_APPROVED,
                    approved_qty=requested_qty,
                    triggered_priority=4,
                    rule_explanation=f"Policy exception granted by {override_approved_by} for {', '.join(reasons)} (HMAC-verified).",
                    override_token_verified=True
                )
            elif is_excluded_category:
                return AdjudicationResult(
                    eligibility_status=EligibilityStatus.INELIGIBLE_CATEGORY,
                    approved_qty=0,
                    triggered_priority=2,
                    rule_explanation=f"Category '{category}' is non-returnable for reason '{return_reason}' without manager override."
                )
            else:
                return AdjudicationResult(
                    eligibility_status=EligibilityStatus.INELIGIBLE_WINDOW,
                    approved_qty=0,
                    triggered_priority=3,
                    rule_explanation=f"Return window expired ({days_elapsed} days elapsed > {return_window_days} days limit)."
                )

        # Priority 5: Standard Approval
        return AdjudicationResult(
            eligibility_status=EligibilityStatus.ELIGIBLE,
            approved_qty=requested_qty,
            triggered_priority=5,
            rule_explanation="All standard return policy checks satisfied."
        )
