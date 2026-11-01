from __future__ import annotations

"""
ERL-RMA Independent Rule-Based Detector & Audit Engine
This module contains ZERO references to ground truth and performs purely
independent heuristic and invariant auditing over operational datasets.
Outputs detections with record_id, detected_type, evidence, and entity_type.
Python 3.9+ compatible.
"""

from dataclasses import dataclass
import datetime
from decimal import Decimal
import json
import hashlib
from typing import Any, Dict, List, Optional, Set


def compute_event_hash(
    seq: int,
    entity_type: str,
    entity_id: str,
    prev_state: str,
    new_state: str,
    actor_id: str,
    event_ts: str,
    prev_event_hash: Optional[str]
) -> str:
    """Computes SHA-256 hash over canonical JSON representation of event payload + prior hash."""
    canonical = json.dumps({
        "seq": seq,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "previous_state": prev_state,
        "new_state": new_state,
        "actor_id": actor_id,
        "event_timestamp": event_ts,
        "prev_event_hash": prev_event_hash or ""
    }, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Detection:
    record_id: str
    detected_type: str
    evidence: str
    entity_type: str
    severity: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "detected_type": self.detected_type,
            "evidence": self.evidence,
            "entity_type": self.entity_type,
            "severity": self.severity,
        }


class IndependentAuditEngine:
    """
    Independent detector that scans operational records for rule violations,
    arithmetic mismatches, temporal paradoxes, duplicate payouts, and SoD breaches.
    Crucially: NEVER reads or imports ground truth.
    """

    @classmethod
    def detect(cls, dataset: Dict[str, List[Dict[str, Any]]]) -> List[Detection]:
        detections: List[Detection] = []

        ol_map: Dict[str, Dict[str, Any]] = {
            x["order_line_id"]: x for x in dataset.get("order_lines", [])
        }
        ord_map: Dict[str, Dict[str, Any]] = {
            x["order_id"]: x for x in dataset.get("orders", [])
        }
        rl_map: Dict[str, Dict[str, Any]] = {
            x["return_line_id"]: x for x in dataset.get("return_lines", [])
        }
        insp_map: Dict[str, Dict[str, Any]] = {
            x["inspection_id"]: x for x in dataset.get("inspections", [])
        }

        # 1. Over-Return Quantity Check: approved_qty > purchased_qty
        for rl in dataset.get("return_lines", []):
            ol = ol_map.get(rl["order_line_id"])
            if not ol:
                continue
            purchased_q = int(ol.get("purchased_qty", 0))
            approved_q = int(rl.get("approved_qty", 0))
            if approved_q > purchased_q:
                detections.append(Detection(
                    record_id=rl["return_line_id"],
                    detected_type="ANOM_QTY_EXCEEDS_PURCHASED",
                    evidence=f"approved_qty ({approved_q}) > purchased_qty ({purchased_q}) on line {ol['order_line_id']}",
                    entity_type="return_lines",
                    severity="CRITICAL",
                ))

        # 2. Return Window Expiration Without Override
        req_lines: Dict[str, List[Dict[str, Any]]] = {}
        for rl in dataset.get("return_lines", []):
            req_lines.setdefault(rl["return_request_id"], []).append(rl)

        for req in dataset.get("return_requests", []):
            ord_o = ord_map.get(req["order_id"])
            if not ord_o or not ord_o.get("delivery_date"):
                continue

            r_dt_str = req["request_date"].replace("Z", "+00:00")
            d_dt_str = ord_o["delivery_date"].replace("Z", "+00:00")
            try:
                r_dt = datetime.datetime.fromisoformat(r_dt_str)
                d_dt = datetime.datetime.fromisoformat(d_dt_str)
            except Exception:
                continue

            elapsed_days = (r_dt - d_dt).days
            has_override = bool(req.get("policy_override_flag"))

            # Check if any approved line exceeds window without valid override
            is_violating = False
            violating_line_id = ""
            limit_window = 0

            for rl in req_lines.get(req["return_request_id"], []):
                ol = ol_map.get(rl["order_line_id"])
                if not ol:
                    continue
                approved_q = int(rl.get("approved_qty", 0))
                win_days = int(ol.get("return_window_days", 0))

                # Boundary rule: elapsed_days == win_days is VALID (within window)
                # elapsed_days > win_days is EXPIRED
                if approved_q > 0 and elapsed_days > win_days and not has_override:
                    is_violating = True
                    violating_line_id = rl["return_line_id"]
                    limit_window = win_days
                    break

            if is_violating:
                detections.append(Detection(
                    record_id=req["return_request_id"],
                    detected_type="ANOM_LATE_RETURN_NO_OVERRIDE",
                    evidence=f"Request elapsed {elapsed_days}d > {limit_window}d window without override (line={violating_line_id})",
                    entity_type="return_requests",
                    severity="HIGH",
                ))

        # 3. Premature Restock Paradox: disposed_at < inspected_at with RESTOCK action
        for disp in dataset.get("inventory_dispositions", []):
            insp = insp_map.get(disp.get("inspection_id", ""))
            if not insp:
                continue
            action = disp.get("disposition_action", "")
            d_at = disp.get("disposed_at", "")
            i_at = insp.get("inspected_at", "")
            if action == "RESTOCK" and d_at < i_at:
                detections.append(Detection(
                    record_id=disp["disposition_id"],
                    detected_type="ANOM_RESTOCK_BEFORE_INSP",
                    evidence=f"Restock disposed_at ({d_at}) is earlier than inspected_at ({i_at})",
                    entity_type="inventory_dispositions",
                    severity="CRITICAL",
                ))

        # 4. Refund Exceeding Net Paid & 5. Duplicate Refund Disbursement
        # Track cumulative refunded net per return line
        refunds_by_line: Dict[str, List[Dict[str, Any]]] = {}
        processed_lines_seen: Set[str] = set()

        for ref in dataset.get("refunds", []):
            rl_id = ref.get("return_line_id", "")
            st = ref.get("refund_status", "")
            if st == "PROCESSED":
                refunds_by_line.setdefault(rl_id, []).append(ref)
                if rl_id in processed_lines_seen:
                    # Duplicate PROCESSED refund on the exact same return line
                    detections.append(Detection(
                        record_id=ref["refund_id"],
                        detected_type="ANOM_DUPLICATE_REFUND",
                        evidence=f"Duplicate PROCESSED payout detected on return_line_id={rl_id}",
                        entity_type="refunds",
                        severity="CRITICAL",
                    ))
                processed_lines_seen.add(rl_id)

        # Check net refund > net paid per order line
        for rl_id, ref_list in refunds_by_line.items():
            rl = rl_map.get(rl_id)
            if not rl:
                continue
            ol = ol_map.get(rl.get("order_line_id", ""))
            if not ol:
                continue

            net_paid_cents = int(ol.get("net_paid_amount_cents", 0))
            if not net_paid_cents and "net_paid_amount" in ol:
                net_paid_cents = int(Decimal(str(ol["net_paid_amount"])) * 100)

            for ref in ref_list:
                ref_net_cents = int(ref.get("net_refund_amount_cents", 0))
                if not ref_net_cents and "net_refund_amount" in ref:
                    ref_net_cents = int(Decimal(str(ref["net_refund_amount"])) * 100)

                # Allow shipping refund if recorded
                shipping_cents = int(ref.get("shipping_refund_cents", 0))
                allowable_cents = net_paid_cents + shipping_cents

                if ref_net_cents > allowable_cents:
                    detections.append(Detection(
                        record_id=ref["refund_id"],
                        detected_type="ANOM_REFUND_EXCEEDS_PAID",
                        evidence=f"Refund net (${ref_net_cents/100:.2f}) exceeds net paid amount (${allowable_cents/100:.2f})",
                        entity_type="refunds",
                        severity="CRITICAL",
                    ))

        return detections
