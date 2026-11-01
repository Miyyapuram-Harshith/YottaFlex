from __future__ import annotations

"""
Unit Tests for Eligibility Adjudication Decision Table (Priorities 1 to 5)
Including Temporal Boundary Days (W-1, W, W+1) and HMAC-SHA256 Token Verification.
Python 3.9+ compatible.
"""

import datetime
import unittest
from core.models import OrderLine, EligibilityStatus
from core.adjudication import EligibilityEngine, generate_override_token, verify_override_token


class TestEligibilityEngine(unittest.TestCase):

    def setUp(self):
        self.delivery_dt = datetime.datetime(2026, 3, 1, 10, 0, 0)
        self.standard_line = OrderLine(
            order_line_id="OL-ORD-2026-000001-01",
            order_id="ORD-2026-000001",
            sku_id="SKU-APP-1234",
            category="APPAREL",
            return_window_days=30,
            purchased_qty=3,
            unit_price_cents=8000,
            allocated_discount_cents=1500,
            tax_rate_basis_points=800,
            tax_amount_cents=1800,
            net_paid_amount_cents=24300
        )

        self.final_sale_line = OrderLine(
            order_line_id="OL-ORD-2026-000001-02",
            order_id="ORD-2026-000001",
            sku_id="SKU-FIN-9999",
            category="FINAL_SALE",
            return_window_days=0,
            purchased_qty=2,
            unit_price_cents=4000,
            allocated_discount_cents=0,
            tax_rate_basis_points=800,
            tax_amount_cents=640,
            net_paid_amount_cents=8640
        )

    def test_priority_1_quantity_overflow(self):
        """Priority 1: requested_qty > net unreturned purchased quantity."""
        req_dt = self.delivery_dt + datetime.timedelta(days=5)
        res = EligibilityEngine.evaluate(
            order_line=self.standard_line,
            requested_qty=4,  # purchased is 3
            return_reason="CHANGED_MIND",
            request_date=req_dt,
            delivery_date=self.delivery_dt
        )
        self.assertEqual(res.eligibility_status, EligibilityStatus.INELIGIBLE_QTY)
        self.assertEqual(res.approved_qty, 0)
        self.assertEqual(res.triggered_priority, 1)

    def test_priority_2_final_sale_exclusion(self):
        """Priority 2: FINAL_SALE category with customer remorse reason is rejected."""
        req_dt = self.delivery_dt + datetime.timedelta(days=1)
        res = EligibilityEngine.evaluate(
            order_line=self.final_sale_line,
            requested_qty=1,
            return_reason="CHANGED_MIND",
            request_date=req_dt,
            delivery_date=self.delivery_dt,
            policy_override_flag=False
        )
        self.assertEqual(res.eligibility_status, EligibilityStatus.INELIGIBLE_CATEGORY)
        self.assertEqual(res.approved_qty, 0)
        self.assertEqual(res.triggered_priority, 2)

    def test_priority_2_exception_for_defective_item(self):
        """Priority 2: FINAL_SALE permitted if merchant fault (DEFECTIVE)."""
        req_dt = self.delivery_dt + datetime.timedelta(days=1)
        res = EligibilityEngine.evaluate(
            order_line=self.final_sale_line,
            requested_qty=1,
            return_reason="DEFECTIVE",
            request_date=req_dt,
            delivery_date=self.delivery_dt,
            policy_override_flag=False
        )
        # Category check passes; window check for 0 days: 1 day > 0 days -> INELIGIBLE_WINDOW
        self.assertEqual(res.eligibility_status, EligibilityStatus.INELIGIBLE_WINDOW)

    def test_priority_3_window_expiration(self):
        """Priority 3: Return requested 45 days after delivery on 30-day window."""
        req_dt = self.delivery_dt + datetime.timedelta(days=45)
        res = EligibilityEngine.evaluate(
            order_line=self.standard_line,
            requested_qty=1,
            return_reason="CHANGED_MIND",
            request_date=req_dt,
            delivery_date=self.delivery_dt,
            policy_override_flag=False
        )
        self.assertEqual(res.eligibility_status, EligibilityStatus.INELIGIBLE_WINDOW)
        self.assertEqual(res.approved_qty, 0)
        self.assertEqual(res.triggered_priority, 3)

    def test_boundary_day_w_minus_1(self):
        """Boundary check day W - 1 (day 29 of 30-day window): Eligible."""
        req_dt = self.delivery_dt + datetime.timedelta(days=29)
        res = EligibilityEngine.evaluate(
            order_line=self.standard_line,
            requested_qty=1,
            return_reason="CHANGED_MIND",
            request_date=req_dt,
            delivery_date=self.delivery_dt
        )
        self.assertEqual(res.eligibility_status, EligibilityStatus.ELIGIBLE)
        self.assertEqual(res.approved_qty, 1)
        self.assertEqual(res.triggered_priority, 5)

    def test_boundary_day_w_exact(self):
        """Boundary check day W exact (day 30 of 30-day window): Eligible."""
        req_dt = self.delivery_dt + datetime.timedelta(days=30)
        res = EligibilityEngine.evaluate(
            order_line=self.standard_line,
            requested_qty=1,
            return_reason="CHANGED_MIND",
            request_date=req_dt,
            delivery_date=self.delivery_dt
        )
        self.assertEqual(res.eligibility_status, EligibilityStatus.ELIGIBLE)
        self.assertEqual(res.approved_qty, 1)
        self.assertEqual(res.triggered_priority, 5)

    def test_boundary_day_w_plus_1(self):
        """Boundary check day W + 1 (day 31 of 30-day window): Ineligible Window."""
        req_dt = self.delivery_dt + datetime.timedelta(days=31)
        res = EligibilityEngine.evaluate(
            order_line=self.standard_line,
            requested_qty=1,
            return_reason="CHANGED_MIND",
            request_date=req_dt,
            delivery_date=self.delivery_dt
        )
        self.assertEqual(res.eligibility_status, EligibilityStatus.INELIGIBLE_WINDOW)
        self.assertEqual(res.approved_qty, 0)
        self.assertEqual(res.triggered_priority, 3)

    def test_priority_4_hmac_manager_override_valid(self):
        """Priority 4: Valid HMAC-SHA256 manager override approved."""
        req_dt = self.delivery_dt + datetime.timedelta(days=45)
        req_id = "RMA-REQ-2026-999001"
        mgr_id = "MGR-101"
        ts_str = req_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        valid_token = generate_override_token(req_id, mgr_id, "POLICY_EXCEPTION", ts_str)

        self.assertTrue(verify_override_token(valid_token, req_id))

        res = EligibilityEngine.evaluate(
            order_line=self.standard_line,
            requested_qty=1,
            return_reason="CHANGED_MIND",
            request_date=req_dt,
            delivery_date=self.delivery_dt,
            policy_override_flag=True,
            override_approved_by=mgr_id,
            override_token=valid_token,
            request_id=req_id
        )
        self.assertEqual(res.eligibility_status, EligibilityStatus.OVERRIDE_APPROVED)
        self.assertEqual(res.approved_qty, 1)
        self.assertEqual(res.triggered_priority, 4)
        self.assertTrue(res.override_token_verified)

    def test_priority_4_hmac_manager_override_invalid(self):
        """Priority 4: Invalid/tampered override token is rejected."""
        req_dt = self.delivery_dt + datetime.timedelta(days=45)
        req_id = "RMA-REQ-2026-999001"
        tampered_token = "MGR-101:2026-04-15T10:00:00Z:badhash0000000000000000000000"

        self.assertFalse(verify_override_token(tampered_token, req_id))

    def test_priority_5_standard_eligibility(self):
        """Priority 5: Standard compliant return within 30-day window."""
        req_dt = self.delivery_dt + datetime.timedelta(days=10)
        res = EligibilityEngine.evaluate(
            order_line=self.standard_line,
            requested_qty=2,
            return_reason="SIZE_FIT",
            request_date=req_dt,
            delivery_date=self.delivery_dt
        )
        self.assertEqual(res.eligibility_status, EligibilityStatus.ELIGIBLE)
        self.assertEqual(res.approved_qty, 2)
        self.assertEqual(res.triggered_priority, 5)


if __name__ == "__main__":
    unittest.main()
