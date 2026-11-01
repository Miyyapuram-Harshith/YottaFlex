from __future__ import annotations

"""
ERL-RMA Prorated Refund Arithmetic & Penny Reconciliation Engine
Implements Cumulative Remainder Proration (F2) & Strict Invariant Enforcement (F3).
All monetary values are integer cents or decimal.Decimal (Banker's Rounding: ROUND_HALF_EVEN).
Zero floating-point representations permitted in core financial calculations.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any, Dict, Optional, Union
from .models import OrderLine, ConditionGrade, LoyaltyTier, RefundStatus


def round_half_even_int(d: Decimal) -> int:
    """Rounds a Decimal value to the nearest integer cents using Banker's rounding."""
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def _extract_int_cents(val: Any) -> int:
    if val is None:
        return 0
    if isinstance(val, int):
        return val
    # If float or Decimal or numeric string
    d = Decimal(str(val))
    return int((d * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


@dataclass(frozen=True)
class RefundBreakdown:
    gross_merch_value_cents: int
    discount_clawback_cents: int
    net_merch_base_cents: int
    tax_refund_amount_cents: int
    restocking_fee_cents: int
    shipping_refund_cents: int
    net_refund_amount_cents: int
    invariant_passed: bool
    explanation: str

    @property
    def gross_merch_value(self) -> float:
        return self.gross_merch_value_cents / 100.0

    @property
    def discount_clawback(self) -> float:
        return self.discount_clawback_cents / 100.0

    @property
    def net_merch_base(self) -> float:
        return self.net_merch_base_cents / 100.0

    @property
    def tax_refund_amount(self) -> float:
        return self.tax_refund_amount_cents / 100.0

    @property
    def restocking_fee(self) -> float:
        return self.restocking_fee_cents / 100.0

    @property
    def shipping_refund(self) -> float:
        return self.shipping_refund_cents / 100.0

    @property
    def net_refund_amount(self) -> float:
        return self.net_refund_amount_cents / 100.0


class RefundCalculator:
    """
    Fixed-point integer cents refund calculator guaranteeing zero penny drift
    via cumulative remainder proration across split/partial returns.
    """

    RESTOCKING_FEE_RATE = Decimal("0.15")
    MERCHANT_FAULT_REASONS = {"DEFECTIVE", "DAMAGED_IN_TRANSIT", "WRONG_ITEM"}

    @classmethod
    def calculate(
        cls,
        order_line: Union[OrderLine, Dict[str, Any]],
        inspected_qty: int,
        condition_grade: str,
        return_reason: str,
        loyalty_tier: str = "STANDARD",
        refund_status: str = "PROCESSED",
        prior_returned_qty: int = 0,
        prior_discount_clawback_cents: int = 0,
        prior_tax_refund_cents: int = 0,
        prior_net_refund_cents: int = 0,
        order_shipping_fee_paid_cents: int = 0,
        prior_order_shipping_refunded_cents: int = 0,
        is_final_remaining_line: bool = False,
        enforce_invariants: bool = True
    ) -> RefundBreakdown:
        if inspected_qty <= 0:
            return RefundBreakdown(
                gross_merch_value_cents=0,
                discount_clawback_cents=0,
                net_merch_base_cents=0,
                tax_refund_amount_cents=0,
                restocking_fee_cents=0,
                shipping_refund_cents=0,
                net_refund_amount_cents=0,
                invariant_passed=True,
                explanation="Inspected quantity is zero; zero refund disbursed."
            )

        if isinstance(order_line, dict):
            purchased_qty = int(order_line.get("purchased_qty", 1))
            unit_price_cents = order_line.get("unit_price_cents")
            if unit_price_cents is None:
                unit_price_cents = _extract_int_cents(order_line.get("unit_price", 0))
            allocated_discount_cents = order_line.get("allocated_discount_cents")
            if allocated_discount_cents is None:
                allocated_discount_cents = _extract_int_cents(order_line.get("allocated_discount", 0))
            tax_amount_cents = order_line.get("tax_amount_cents")
            if tax_amount_cents is None:
                tax_amount_cents = _extract_int_cents(order_line.get("tax_amount", 0))
            net_paid_amount_cents = order_line.get("net_paid_amount_cents")
            if net_paid_amount_cents is None:
                net_paid_amount_cents = _extract_int_cents(order_line.get("net_paid_amount", 0))
        else:
            purchased_qty = order_line.purchased_qty
            unit_price_cents = getattr(order_line, "unit_price_cents", None)
            if unit_price_cents is None:
                unit_price_cents = _extract_int_cents(getattr(order_line, "unit_price", 0))
            allocated_discount_cents = getattr(order_line, "allocated_discount_cents", None)
            if allocated_discount_cents is None:
                allocated_discount_cents = _extract_int_cents(getattr(order_line, "allocated_discount", 0))
            tax_amount_cents = getattr(order_line, "tax_amount_cents", None)
            if tax_amount_cents is None:
                tax_amount_cents = _extract_int_cents(getattr(order_line, "tax_amount", 0))
            net_paid_amount_cents = getattr(order_line, "net_paid_amount_cents", None)
            if net_paid_amount_cents is None:
                net_paid_amount_cents = _extract_int_cents(getattr(order_line, "net_paid_amount", 0))

        q_purch = Decimal(purchased_qty)
        cum_qty_k = Decimal(prior_returned_qty + inspected_qty)

        # 1. Gross Merchandise Value (GMV) for this inspection tranche
        gmv_cents = inspected_qty * unit_price_cents

        # 2. Cumulative Remainder Proration for Promotional Discount (F2)
        total_discount = Decimal(allocated_discount_cents)
        cum_discount_cents = round_half_even_int((total_discount * cum_qty_k) / q_purch)
        d_claw_cents = cum_discount_cents - prior_discount_clawback_cents

        # 3. Net Refundable Base
        b_net_cents = gmv_cents - d_claw_cents

        # 4. Cumulative Remainder Proration for Tax Refund (F2, F5)
        total_tax = Decimal(tax_amount_cents)
        cum_tax_cents = round_half_even_int((total_tax * cum_qty_k) / q_purch)
        t_ref_cents = cum_tax_cents - prior_tax_refund_cents

        # 5. Conditional Restocking Fee
        is_fraud = (condition_grade == ConditionGrade.FRAUD_MISMATCH.value)
        is_blocked = refund_status in (RefundStatus.BLOCKED_DUPLICATE.value, RefundStatus.BLOCKED_FRAUD.value)

        fee_cents = 0
        fee_reason = "No restocking fee applicable."
        if not is_fraud and return_reason in ("CHANGED_MIND", "SIZE_FIT") and condition_grade == ConditionGrade.GRADE_B_OPEN_BOX.value:
            if loyalty_tier == LoyaltyTier.VIP.value:
                fee_cents = 0
                fee_reason = "Restocking fee waived for VIP loyalty tier."
            else:
                fee_cents = round_half_even_int(Decimal(b_net_cents) * cls.RESTOCKING_FEE_RATE)
                fee_reason = f"15% restocking fee applied on net merchandise base (${Decimal(b_net_cents)/100:.2f})."

        # 6. Shipping Fee Refund (F4)
        shipping_ref_cents = 0
        if (
            return_reason in cls.MERCHANT_FAULT_REASONS
            and is_final_remaining_line
            and order_shipping_fee_paid_cents > prior_order_shipping_refunded_cents
        ):
            shipping_ref_cents = order_shipping_fee_paid_cents - prior_order_shipping_refunded_cents

        # 7. Final Net Refund Disbursement
        if is_fraud:
            net_refund_cents = 0
            explanation = "Fraud mismatch detected during physical inspection. Payout blocked and goods quarantined."
        elif is_blocked:
            net_refund_cents = 0
            explanation = f"Disbursement blocked due to status: {refund_status}."
        else:
            tentative_net = b_net_cents + t_ref_cents - fee_cents + shipping_ref_cents
            net_refund_cents = max(0, tentative_net)
            explanation = (
                f"Gross ${Decimal(gmv_cents)/100:.2f} - Clawback ${Decimal(d_claw_cents)/100:.2f} "
                f"+ Tax ${Decimal(t_ref_cents)/100:.2f} - Fee ${Decimal(fee_cents)/100:.2f} "
                f"{'+ Shipping $' + str(Decimal(shipping_ref_cents)/100) if shipping_ref_cents else ''} "
                f"= Net ${Decimal(net_refund_cents)/100:.2f} ({fee_reason})"
            )

        # 8. Strict Invariant Enforcement (F3): sum(R_net) <= OrderLine.net_paid_amount (+ shipping)
        max_allowable_line_cents = net_paid_amount_cents - prior_net_refund_cents
        if enforce_invariants and not is_fraud and not is_blocked and refund_status == RefundStatus.PROCESSED.value:
            if (net_refund_cents - shipping_ref_cents) > max_allowable_line_cents:
                # Reject violation at calculation/write time
                raise ValueError(
                    f"Invariant violation: Cumulative line refunds exceed net paid amount "
                    f"(${Decimal(prior_net_refund_cents + net_refund_cents - shipping_ref_cents)/100:.2f} > "
                    f"${Decimal(net_paid_amount_cents)/100:.2f}). Disbursement rejected."
                )

        invariant_passed = ((prior_net_refund_cents + net_refund_cents - shipping_ref_cents) <= net_paid_amount_cents)

        return RefundBreakdown(
            gross_merch_value_cents=gmv_cents,
            discount_clawback_cents=d_claw_cents,
            net_merch_base_cents=b_net_cents,
            tax_refund_amount_cents=t_ref_cents,
            restocking_fee_cents=fee_cents,
            shipping_refund_cents=shipping_ref_cents,
            net_refund_amount_cents=net_refund_cents,
            invariant_passed=invariant_passed,
            explanation=explanation
        )
