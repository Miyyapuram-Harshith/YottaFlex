from __future__ import annotations

"""
ERL-RMA Domain Models & Value Objects
Enterprise-Grade Type System compliant with ISO/IEC/IEEE 29148 practice.
Strictly integer cents and Decimal representation - no floating-point money.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from enum import Enum
from typing import Optional


def cents_to_str(cents: int) -> str:
    """Format integer cents into a fixed 2-decimal USD string (e.g. 1050 -> '10.50')."""
    d = Decimal(cents) / Decimal(100)
    return f"{d.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN):.2f}"


def str_to_cents(val: str | int | Decimal) -> int:
    """Convert string, integer cents, or Decimal to exact integer cents."""
    if isinstance(val, int):
        return val
    d = Decimal(str(val))
    return int((d * Decimal(100)).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN))


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    FLAGGED = "FLAGGED"


class LoyaltyTier(str, Enum):
    STANDARD = "STANDARD"
    SILVER = "SILVER"
    GOLD = "GOLD"
    VIP = "VIP"


class OrderStatus(str, Enum):
    PLACED = "PLACED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Category(str, Enum):
    ELECTRONICS = "ELECTRONICS"
    APPAREL = "APPAREL"
    HOME = "HOME"
    FINAL_SALE = "FINAL_SALE"
    HAZMAT = "HAZMAT"


class RequestType(str, Enum):
    REFUND = "REFUND"
    EXCHANGE = "EXCHANGE"


class ResolutionType(str, Enum):
    REFUND = "REFUND"
    EXCHANGE = "EXCHANGE"
    STORE_CREDIT = "STORE_CREDIT"


class RequestStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PARTIALLY_APPROVED = "PARTIALLY_APPROVED"
    REJECTED = "REJECTED"


class ReturnReason(str, Enum):
    DEFECTIVE = "DEFECTIVE"
    DAMAGED_IN_TRANSIT = "DAMAGED_IN_TRANSIT"
    WRONG_ITEM = "WRONG_ITEM"
    CHANGED_MIND = "CHANGED_MIND"
    SIZE_FIT = "SIZE_FIT"


class EligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE_WINDOW = "INELIGIBLE_WINDOW"
    INELIGIBLE_CATEGORY = "INELIGIBLE_CATEGORY"
    INELIGIBLE_QTY = "INELIGIBLE_QTY"
    OVERRIDE_APPROVED = "OVERRIDE_APPROVED"


class RMAStatus(str, Enum):
    ISSUED = "ISSUED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    INSPECTED = "INSPECTED"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class Carrier(str, Enum):
    UPS = "UPS"
    FEDEX = "FEDEX"
    USPS = "USPS"
    DHL = "DHL"
    IN_STORE_DROP = "IN_STORE_DROP"


class ShipmentStatus(str, Enum):
    LABEL_CREATED = "LABEL_CREATED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    DELIVERED_TO_WH = "DELIVERED_TO_WH"
    LOST_IN_TRANSIT = "LOST_IN_TRANSIT"
    NEVER_SHIPPED = "NEVER_SHIPPED"


class ConditionGrade(str, Enum):
    GRADE_A_NEW = "GRADE_A_NEW"
    GRADE_B_OPEN_BOX = "GRADE_B_OPEN_BOX"
    GRADE_C_DAMAGED = "GRADE_C_DAMAGED"
    GRADE_D_DEFECTIVE = "GRADE_D_DEFECTIVE"
    FRAUD_MISMATCH = "FRAUD_MISMATCH"


class RefundMethod(str, Enum):
    ORIGINAL_PAYMENT = "ORIGINAL_PAYMENT"
    STORE_CREDIT = "STORE_CREDIT"
    EXCHANGE_CREDIT = "EXCHANGE_CREDIT"


class RefundStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    BLOCKED_DUPLICATE = "BLOCKED_DUPLICATE"
    BLOCKED_FRAUD = "BLOCKED_FRAUD"


class DispositionAction(str, Enum):
    RESTOCK = "RESTOCK"
    REFURBISH = "REFURBISH"
    QUARANTINE = "QUARANTINE"
    SCRAP = "SCRAP"


class LabelClass(str, Enum):
    ANOMALY = "ANOMALY"
    SCENARIO = "SCENARIO"
    VALID_BOUNDARY = "VALID_BOUNDARY"


@dataclass(frozen=True)
class Customer:
    customer_id: str
    account_status: str
    loyalty_tier: str
    risk_score_basis_points: int  # 0 to 10000 (0.00% to 100.00%)
    created_at: str

    @property
    def risk_score(self) -> Decimal:
        return Decimal(self.risk_score_basis_points) / Decimal(100)


@dataclass(frozen=True)
class Order:
    order_id: str
    customer_id: str
    order_date: str
    delivery_date: Optional[str]
    order_status: str
    subtotal_cents: int
    discount_total_cents: int
    tax_total_cents: int
    shipping_fee_paid_cents: int
    paid_total_cents: int


@dataclass(frozen=True)
class OrderLine:
    order_line_id: str
    order_id: str
    sku_id: str
    category: str
    return_window_days: int
    purchased_qty: int
    unit_price_cents: int
    allocated_discount_cents: int
    tax_rate_basis_points: int  # e.g. 800 = 8.00%
    tax_amount_cents: int
    net_paid_amount_cents: int


@dataclass(frozen=True)
class ReturnRequest:
    return_request_id: str
    order_id: str
    customer_id: str
    request_date: str
    request_type: str
    request_status: str
    policy_override_flag: bool
    override_approved_by: Optional[str] = None
    override_token: Optional[str] = None


@dataclass(frozen=True)
class ReturnLine:
    return_line_id: str
    return_request_id: str
    order_line_id: str
    requested_qty: int
    approved_qty: int
    return_reason: str
    eligibility_status: str
    resolution_type: str = "REFUND"
    exchange_order_id: Optional[str] = None


@dataclass(frozen=True)
class ReturnAuthorization:
    rma_id: str
    return_request_id: str
    authorized_at: str
    expiration_date: str
    rma_status: str


@dataclass(frozen=True)
class ReturnShipment:
    shipment_id: str
    rma_id: str
    carrier: str
    tracking_number: str
    shipped_at: Optional[str]
    received_at: Optional[str]
    shipment_status: str


@dataclass(frozen=True)
class Inspection:
    inspection_id: str
    return_line_id: str
    shipment_id: str
    inspector_id: str
    inspected_at: str
    condition_grade: str
    inspected_qty: int


@dataclass(frozen=True)
class Refund:
    refund_id: str
    rma_id: str
    return_line_id: str
    gross_merch_value_cents: int
    discount_clawback_cents: int
    tax_refund_amount_cents: int
    restocking_fee_cents: int
    shipping_refund_cents: int
    net_refund_amount_cents: int
    refund_method: str
    refund_status: str
    processed_at: Optional[str]
    idempotency_key: Optional[str] = None


@dataclass(frozen=True)
class InventoryDisposition:
    disposition_id: str
    inspection_id: str
    return_line_id: str
    disposition_action: str
    disposition_qty: int
    warehouse_loc_id: str
    disposed_at: str


@dataclass(frozen=True)
class EntityStateEvent:
    event_id: str
    entity_type: str
    entity_id: str
    previous_state: str
    new_state: str
    actor_id: str
    event_timestamp: str
    seq: int
    prev_event_hash: Optional[str]
    event_hash: str
