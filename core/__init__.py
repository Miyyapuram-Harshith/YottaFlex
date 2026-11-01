from __future__ import annotations

"""
ERL-RMA Core Domain Package
Event-Sourced Domain-Driven Design (DDD) Reference Architecture
Python 3.9+ compatible.
"""

from .models import (
    Customer, Order, OrderLine, ReturnRequest, ReturnLine,
    ReturnAuthorization, ReturnShipment, Inspection, Refund,
    InventoryDisposition, EntityStateEvent, Category, LoyaltyTier,
    ReturnReason, EligibilityStatus, ConditionGrade, DispositionAction,
    RefundStatus, RequestStatus, ShipmentStatus, RMAStatus,
    ResolutionType, RefundMethod, LabelClass,
    cents_to_str, str_to_cents
)
from .adjudication import (
    EligibilityEngine, AdjudicationResult,
    generate_override_token, verify_override_token
)
from .financial import RefundCalculator, RefundBreakdown, round_half_even_int
from .disposition import DispositionEngine, DispositionResult
from .audit import IndependentAuditEngine, Detection, compute_event_hash
from .evaluate import BenchmarkEvaluator, EvaluationReport, ClassMetrics

__all__ = [
    "Customer", "Order", "OrderLine", "ReturnRequest", "ReturnLine",
    "ReturnAuthorization", "ReturnShipment", "Inspection", "Refund",
    "InventoryDisposition", "EntityStateEvent", "Category", "LoyaltyTier",
    "ReturnReason", "EligibilityStatus", "ConditionGrade", "DispositionAction",
    "RefundStatus", "RequestStatus", "ShipmentStatus", "RMAStatus",
    "ResolutionType", "RefundMethod", "LabelClass",
    "cents_to_str", "str_to_cents",
    "EligibilityEngine", "AdjudicationResult",
    "generate_override_token", "verify_override_token",
    "RefundCalculator", "RefundBreakdown", "round_half_even_int",
    "DispositionEngine", "DispositionResult",
    "IndependentAuditEngine", "Detection",
    "BenchmarkEvaluator", "EvaluationReport", "ClassMetrics"
]
