from __future__ import annotations

"""
Unit Tests for Prorated Refund Arithmetic, Penny Reconciliation & Invariants
Covers Cumulative Remainder Proration across 2, 3, and 7 splits, VIP waivers,
FRAUD_MISMATCH, and Shipping fee refunds.
Python 3.9+ compatible.
"""

import unittest
from core.models import OrderLine, ConditionGrade, LoyaltyTier, RefundStatus
from core.financial import RefundCalculator


class TestRefundCalculator(unittest.TestCase):

    def setUp(self):
        # 3 items purchased @ $100.00 each = $300 subtotal
        # $30 discount allocated = $10 discount per item
        # 8% tax on ($300 - $30) = $21.60 tax ($7.20 per item)
        # Net paid = $300 - $30 + $21.60 = $291.60 ($97.20 per item)
        self.order_line = OrderLine(
            order_line_id="OL-ORD-2026-000002-01",
            order_id="ORD-2026-000002",
            sku_id="SKU-ELE-5555",
            category="ELECTRONICS",
            return_window_days=15,
            purchased_qty=3,
            unit_price_cents=10000,
            allocated_discount_cents=3000,
            tax_rate_basis_points=800,
            tax_amount_cents=2160,
            net_paid_amount_cents=29160
        )

    def test_prorated_single_item_refund(self):
        """Returning 1 item out of 3: full discount clawback and tax refund proration."""
        b = RefundCalculator.calculate(
            order_line=self.order_line,
            inspected_qty=1,
            condition_grade=ConditionGrade.GRADE_A_NEW.value,
            return_reason="DEFECTIVE",
            loyalty_tier=LoyaltyTier.STANDARD.value
        )
        self.assertEqual(b.gross_merch_value, 100.00)
        self.assertEqual(b.discount_clawback, 10.00)
        self.assertEqual(b.net_merch_base, 90.00)
        self.assertEqual(b.tax_refund_amount, 7.20)
        self.assertEqual(b.restocking_fee, 0.00)
        self.assertEqual(b.net_refund_amount, 97.20)
        self.assertTrue(b.invariant_passed)

    def test_restocking_fee_for_non_vip(self):
        """15% Restocking fee on net merch base for Grade B Open Box Changed Mind."""
        b = RefundCalculator.calculate(
            order_line=self.order_line,
            inspected_qty=1,
            condition_grade=ConditionGrade.GRADE_B_OPEN_BOX.value,
            return_reason="CHANGED_MIND",
            loyalty_tier=LoyaltyTier.STANDARD.value
        )
        # Net base = $100 - $10 = $90.00. 15% of $90.00 = $13.50 fee
        # Net refund = $90.00 + $7.20 tax - $13.50 fee = $83.70
        self.assertEqual(b.net_merch_base, 90.00)
        self.assertEqual(b.restocking_fee, 13.50)
        self.assertEqual(b.net_refund_amount, 83.70)
        self.assertTrue(b.invariant_passed)

    def test_vip_restocking_fee_waiver(self):
        """VIP loyalty tier waives the 15% restocking fee."""
        b = RefundCalculator.calculate(
            order_line=self.order_line,
            inspected_qty=1,
            condition_grade=ConditionGrade.GRADE_B_OPEN_BOX.value,
            return_reason="CHANGED_MIND",
            loyalty_tier=LoyaltyTier.VIP.value
        )
        self.assertEqual(b.restocking_fee, 0.00)
        self.assertEqual(b.net_refund_amount, 97.20)
        self.assertTrue(b.invariant_passed)

    def test_fraud_mismatch_zero_disbursement(self):
        """FRAUD_MISMATCH condition grade must result in exactly $0.00 disbursement."""
        b = RefundCalculator.calculate(
            order_line=self.order_line,
            inspected_qty=1,
            condition_grade=ConditionGrade.FRAUD_MISMATCH.value,
            return_reason="DEFECTIVE"
        )
        self.assertEqual(b.net_refund_amount, 0.00)
        self.assertTrue(b.invariant_passed)

    def test_blocked_duplicate_zero_disbursement(self):
        """Refund flagged as BLOCKED_DUPLICATE results in $0.00 payout."""
        b = RefundCalculator.calculate(
            order_line=self.order_line,
            inspected_qty=1,
            condition_grade=ConditionGrade.GRADE_A_NEW.value,
            return_reason="CHANGED_MIND",
            refund_status=RefundStatus.BLOCKED_DUPLICATE.value
        )
        self.assertEqual(b.net_refund_amount, 0.00)

    def test_split_proration_reconciliation_2_parts(self):
        """Line with 2 units split into 1 + 1 parts: exact penny reconciliation."""
        line = OrderLine(
            order_line_id="OL-SPLIT-2",
            order_id="ORD-S2",
            sku_id="SKU-APP-1",
            category="APPAREL",
            return_window_days=30,
            purchased_qty=2,
            unit_price_cents=3333,
            allocated_discount_cents=777,
            tax_rate_basis_points=800,
            tax_amount_cents=471,
            net_paid_amount_cents=6360  # (3333*2) - 777 + 471 = 6666 - 777 + 471 = 6360
        )
        # Part 1
        b1 = RefundCalculator.calculate(
            order_line=line, inspected_qty=1,
            condition_grade=ConditionGrade.GRADE_A_NEW.value,
            return_reason="DEFECTIVE",
            prior_returned_qty=0, prior_discount_clawback_cents=0, prior_tax_refund_cents=0, prior_net_refund_cents=0
        )
        # Part 2
        b2 = RefundCalculator.calculate(
            order_line=line, inspected_qty=1,
            condition_grade=ConditionGrade.GRADE_A_NEW.value,
            return_reason="DEFECTIVE",
            prior_returned_qty=1, prior_discount_clawback_cents=b1.discount_clawback_cents,
            prior_tax_refund_cents=b1.tax_refund_amount_cents, prior_net_refund_cents=b1.net_refund_amount_cents
        )

        total_clawback = b1.discount_clawback_cents + b2.discount_clawback_cents
        total_tax = b1.tax_refund_amount_cents + b2.tax_refund_amount_cents
        total_refund = b1.net_refund_amount_cents + b2.net_refund_amount_cents

        self.assertEqual(total_clawback, line.allocated_discount_cents)
        self.assertEqual(total_tax, line.tax_amount_cents)
        self.assertEqual(total_refund, line.net_paid_amount_cents)

    def test_split_proration_reconciliation_3_parts(self):
        """Line with 3 units split into 1 + 1 + 1 parts: exact penny reconciliation."""
        cum_ret = 0
        cum_claw = 0
        cum_tax = 0
        cum_net = 0

        for _ in range(3):
            b = RefundCalculator.calculate(
                order_line=self.order_line, inspected_qty=1,
                condition_grade=ConditionGrade.GRADE_A_NEW.value,
                return_reason="DEFECTIVE",
                prior_returned_qty=cum_ret,
                prior_discount_clawback_cents=cum_claw,
                prior_tax_refund_cents=cum_tax,
                prior_net_refund_cents=cum_net
            )
            cum_ret += 1
            cum_claw += b.discount_clawback_cents
            cum_tax += b.tax_refund_amount_cents
            cum_net += b.net_refund_amount_cents

        self.assertEqual(cum_claw, self.order_line.allocated_discount_cents)
        self.assertEqual(cum_tax, self.order_line.tax_amount_cents)
        self.assertEqual(cum_net, self.order_line.net_paid_amount_cents)

    def test_split_proration_reconciliation_7_parts(self):
        """Odd fractional line with 7 units split 1 by 1: exact reconciliation down to 0 cents."""
        line = OrderLine(
            order_line_id="OL-SPLIT-7",
            order_id="ORD-S7",
            sku_id="SKU-HOME-7",
            category="HOME",
            return_window_days=30,
            purchased_qty=7,
            unit_price_cents=1999,
            allocated_discount_cents=1235,
            tax_rate_basis_points=800,
            tax_amount_cents=1021,
            net_paid_amount_cents=13779  # 7*1999 - 1235 + 1021 = 13993 - 1235 + 1021 = 13779
        )
        cum_ret = 0
        cum_claw = 0
        cum_tax = 0
        cum_net = 0

        for _ in range(7):
            b = RefundCalculator.calculate(
                order_line=line, inspected_qty=1,
                condition_grade=ConditionGrade.GRADE_A_NEW.value,
                return_reason="DEFECTIVE",
                prior_returned_qty=cum_ret,
                prior_discount_clawback_cents=cum_claw,
                prior_tax_refund_cents=cum_tax,
                prior_net_refund_cents=cum_net
            )
            cum_ret += 1
            cum_claw += b.discount_clawback_cents
            cum_tax += b.tax_refund_amount_cents
            cum_net += b.net_refund_amount_cents

        self.assertEqual(cum_claw, line.allocated_discount_cents)
        self.assertEqual(cum_tax, line.tax_amount_cents)
        self.assertEqual(cum_net, line.net_paid_amount_cents)

    def test_shipping_fee_refund_on_final_remaining_line(self):
        """Shipping fee refunded only on merchant fault (DEFECTIVE) and final remaining line."""
        b = RefundCalculator.calculate(
            order_line=self.order_line,
            inspected_qty=3,
            condition_grade=ConditionGrade.GRADE_A_NEW.value,
            return_reason="DEFECTIVE",
            order_shipping_fee_paid_cents=999,
            is_final_remaining_line=True
        )
        self.assertEqual(b.shipping_refund_cents, 999)
        self.assertEqual(b.net_refund_amount_cents, self.order_line.net_paid_amount_cents + 999)

    def test_strict_invariant_rejection(self):
        """Attempting to refund more than net paid amount raises ValueError at calculation time."""
        with self.assertRaises(ValueError):
            RefundCalculator.calculate(
                order_line=self.order_line,
                inspected_qty=3,
                condition_grade=ConditionGrade.GRADE_A_NEW.value,
                return_reason="DEFECTIVE",
                prior_net_refund_cents=self.order_line.net_paid_amount_cents,  # already fully refunded
                enforce_invariants=True
            )


if __name__ == "__main__":
    unittest.main()
