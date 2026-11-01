from __future__ import annotations

"""
ERL-RMA Inventory Disposition Routing Matrix Engine
Implements Section 4.3 Warehouse Bin Allocation & Accounting Impact.
Python 3.9+ compatible.
"""

from dataclasses import dataclass
from .models import ConditionGrade, DispositionAction, Category


@dataclass(frozen=True)
class DispositionResult:
    action: DispositionAction
    warehouse_bin_prefix: str
    warehouse_loc_id: str
    accounting_impact: str
    rationale: str
    recovery_rate_pct: float


class DispositionEngine:
    """
    Deterministically routes inspected goods into warehouse bin partitions based on
    condition grade and product taxonomy.
    """

    @classmethod
    def route(
        cls,
        condition_grade: str,
        category: str,
        bin_slot_number: int = 12
    ) -> DispositionResult:
        slot = f"{bin_slot_number:02d}"

        if condition_grade == ConditionGrade.FRAUD_MISMATCH.value:
            return DispositionResult(
                action=DispositionAction.QUARANTINE,
                warehouse_bin_prefix="QRN",
                warehouse_loc_id=f"WH-QRN-{slot}",
                accounting_impact="Loss Prevention Evidence Hold (Zero Payout)",
                rationale="Counterfeit or mismatched item held for loss prevention chain of custody.",
                recovery_rate_pct=0.0
            )

        if condition_grade == ConditionGrade.GRADE_A_NEW.value:
            return DispositionResult(
                action=DispositionAction.RESTOCK,
                warehouse_bin_prefix="RST",
                warehouse_loc_id=f"WH-RST-{slot}",
                accounting_impact="100% Inventory Asset Recovery",
                rationale="Factory sealed and pristine; immediate return to active pickable bins.",
                recovery_rate_pct=100.0
            )

        if condition_grade == ConditionGrade.GRADE_B_OPEN_BOX.value:
            if category == Category.ELECTRONICS.value:
                return DispositionResult(
                    action=DispositionAction.REFURBISH,
                    warehouse_bin_prefix="RFB",
                    warehouse_loc_id=f"WH-RFB-{slot}",
                    accounting_impact="Secondary Outlet / Recertification Queue",
                    rationale="Open-box electronics require functional diagnostics and recertification.",
                    recovery_rate_pct=70.0
                )
            else:
                return DispositionResult(
                    action=DispositionAction.RESTOCK,
                    warehouse_bin_prefix="RST",
                    warehouse_loc_id=f"WH-RST-{slot}",
                    accounting_impact="Steam/Repackage & Full Asset Recovery",
                    rationale="Soft goods / home items inspected, sanitized, repackaged for inventory relisting.",
                    recovery_rate_pct=100.0
                )

        if condition_grade in (ConditionGrade.GRADE_C_DAMAGED.value, ConditionGrade.GRADE_D_DEFECTIVE.value):
            if category in (Category.ELECTRONICS.value, Category.HAZMAT.value):
                return DispositionResult(
                    action=DispositionAction.QUARANTINE,
                    warehouse_bin_prefix="QRN",
                    warehouse_loc_id=f"WH-QRN-{slot}",
                    accounting_impact="Hold for Vendor Return-to-Vendor (RTV) Credit",
                    rationale="Damaged electronics / hazardous materials staged for OEM vendor chargeback or safe disposal.",
                    recovery_rate_pct=40.0
                )
            else:
                return DispositionResult(
                    action=DispositionAction.SCRAP,
                    warehouse_bin_prefix="SCR",
                    warehouse_loc_id=f"WH-SCR-{slot}",
                    accounting_impact="Write-off to Defective COGS Ledger",
                    rationale="Non-recoverable damaged consumer goods designated for ecological recycling/scrap.",
                    recovery_rate_pct=0.0
                )

        # Fallback default
        return DispositionResult(
            action=DispositionAction.QUARANTINE,
            warehouse_bin_prefix="QRN",
            warehouse_loc_id=f"WH-QRN-{slot}",
            accounting_impact="Unclassified Exception Hold",
            rationale="Unrecognized condition grade quarantined for supervisor review.",
            recovery_rate_pct=0.0
        )
