from __future__ import annotations

"""
Unit Tests for Inventory Disposition Routing Matrix
Exhaustively covers every condition grade x category combination.
Python 3.9+ compatible.
"""

import unittest
from core.models import ConditionGrade, Category, DispositionAction
from core.disposition import DispositionEngine


class TestDispositionEngine(unittest.TestCase):

    def test_grade_a_new_all_categories(self):
        """Pristine condition routes to RESTOCK (WH-RST-XX) across all categories."""
        for cat in [Category.ELECTRONICS.value, Category.APPAREL.value, Category.HOME.value]:
            res = DispositionEngine.route(ConditionGrade.GRADE_A_NEW.value, cat, 15)
            self.assertEqual(res.action, DispositionAction.RESTOCK)
            self.assertEqual(res.warehouse_bin_prefix, "RST")
            self.assertEqual(res.recovery_rate_pct, 100.0)

    def test_grade_b_open_box_electronics(self):
        """Open-box electronics route to REFURBISH (WH-RFB-XX) for recertification."""
        res = DispositionEngine.route(ConditionGrade.GRADE_B_OPEN_BOX.value, Category.ELECTRONICS.value, 8)
        self.assertEqual(res.action, DispositionAction.REFURBISH)
        self.assertEqual(res.warehouse_bin_prefix, "RFB")
        self.assertEqual(res.recovery_rate_pct, 70.0)

    def test_grade_b_open_box_apparel_and_home(self):
        """Open-box soft goods route to RESTOCK (WH-RST-XX) after sanitization."""
        for cat in [Category.APPAREL.value, Category.HOME.value]:
            res = DispositionEngine.route(ConditionGrade.GRADE_B_OPEN_BOX.value, cat, 20)
            self.assertEqual(res.action, DispositionAction.RESTOCK)
            self.assertEqual(res.warehouse_bin_prefix, "RST")
            self.assertEqual(res.recovery_rate_pct, 100.0)

    def test_damaged_defective_electronics_and_hazmat(self):
        """Damaged electronics and hazmat route to QUARANTINE (WH-QRN-XX) for vendor RTV."""
        for grade in [ConditionGrade.GRADE_C_DAMAGED.value, ConditionGrade.GRADE_D_DEFECTIVE.value]:
            for cat in [Category.ELECTRONICS.value, Category.HAZMAT.value]:
                res = DispositionEngine.route(grade, cat, 42)
                self.assertEqual(res.action, DispositionAction.QUARANTINE)
                self.assertEqual(res.warehouse_bin_prefix, "QRN")

    def test_damaged_defective_apparel_and_home(self):
        """Damaged apparel and home items route to SCRAP (WH-SCR-XX) for COGS write-off."""
        for grade in [ConditionGrade.GRADE_C_DAMAGED.value, ConditionGrade.GRADE_D_DEFECTIVE.value]:
            for cat in [Category.APPAREL.value, Category.HOME.value, Category.FINAL_SALE.value]:
                res = DispositionEngine.route(grade, cat, 33)
                self.assertEqual(res.action, DispositionAction.SCRAP)
                self.assertEqual(res.warehouse_bin_prefix, "SCR")
                self.assertEqual(res.recovery_rate_pct, 0.0)

    def test_fraud_mismatch_all_categories(self):
        """Fraud mismatch always routes to QUARANTINE (WH-QRN-XX) with 0% recovery."""
        for cat in [Category.APPAREL.value, Category.ELECTRONICS.value, Category.HOME.value, Category.FINAL_SALE.value]:
            res = DispositionEngine.route(ConditionGrade.FRAUD_MISMATCH.value, cat, 99)
            self.assertEqual(res.action, DispositionAction.QUARANTINE)
            self.assertEqual(res.warehouse_bin_prefix, "QRN")
            self.assertEqual(res.recovery_rate_pct, 0.0)


if __name__ == "__main__":
    unittest.main()
