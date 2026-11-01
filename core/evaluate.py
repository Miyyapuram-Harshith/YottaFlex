from __future__ import annotations

"""
ERL-RMA Benchmark Evaluation & Conformance Module
This is the ONLY module authorized to read ground_truth.
Computes per-class precision, recall, F1, confusion matrix,
and audits false positives against hard-negative VALID_BOUNDARY sets.
Python 3.9+ compatible.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set
from .audit import Detection


@dataclass(frozen=True)
class ClassMetrics:
    issue_type: str
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float


@dataclass(frozen=True)
class EvaluationReport:
    per_class_metrics: Dict[str, ClassMetrics]
    overall_precision: float
    overall_recall: float
    overall_f1: float
    confusion_matrix: Dict[str, Dict[str, int]]
    hard_negative_false_positive_count: int
    false_positives: List[Dict[str, Any]]
    false_negatives: List[Dict[str, Any]]
    total_anomalies_ground_truth: int
    total_valid_boundaries: int
    conformance_explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "per_class_metrics": {k: v.__dict__ for k, v in self.per_class_metrics.items()},
            "overall_precision": self.overall_precision,
            "overall_recall": self.overall_recall,
            "overall_f1": self.overall_f1,
            "confusion_matrix": self.confusion_matrix,
            "hard_negative_false_positive_count": self.hard_negative_false_positive_count,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "total_anomalies_ground_truth": self.total_anomalies_ground_truth,
            "total_valid_boundaries": self.total_valid_boundaries,
            "conformance_explanation": self.conformance_explanation,
        }


class BenchmarkEvaluator:
    """
    Evaluator comparing independent detector detections against isolated ground truth.
    Strictly isolates evaluation logic from operational detection.
    """

    KNOWN_ANOMALY_TYPES = [
        "ANOM_QTY_EXCEEDS_PURCHASED",
        "ANOM_LATE_RETURN_NO_OVERRIDE",
        "ANOM_RESTOCK_BEFORE_INSP",
        "ANOM_REFUND_EXCEEDS_PAID",
        "ANOM_DUPLICATE_REFUND",
    ]

    @classmethod
    def evaluate(
        cls,
        detections: List[Detection],
        ground_truth: List[Dict[str, Any]]
    ) -> EvaluationReport:
        # Separate ground truth by label_class
        gt_anomalies: Dict[str, str] = {}  # entity_id -> issue_type
        gt_boundary_entities: Set[str] = set()

        for g in ground_truth:
            l_class = g.get("label_class", "ANOMALY")
            entity_id = g.get("entity_id", "")
            issue_type = g.get("issue_type", "")

            if l_class == "ANOMALY":
                gt_anomalies[entity_id] = issue_type
            elif l_class == "VALID_BOUNDARY":
                gt_boundary_entities.add(entity_id)

        detected_map: Dict[str, str] = {d.record_id: d.detected_type for d in detections}
        detected_entities = set(detected_map.keys())

        # Initialize per-class counts
        tp: Dict[str, int] = {k: 0 for k in cls.KNOWN_ANOMALY_TYPES}
        fp: Dict[str, int] = {k: 0 for k in cls.KNOWN_ANOMALY_TYPES}
        fn: Dict[str, int] = {k: 0 for k in cls.KNOWN_ANOMALY_TYPES}

        # Confusion matrix: actual -> predicted -> count
        confusion: Dict[str, Dict[str, int]] = {
            act: {pred: 0 for pred in cls.KNOWN_ANOMALY_TYPES + ["NORMAL"]}
            for act in cls.KNOWN_ANOMALY_TYPES + ["VALID_BOUNDARY", "NORMAL"]
        }

        false_positives: List[Dict[str, Any]] = []
        false_negatives: List[Dict[str, Any]] = []
        hard_neg_fp_count = 0

        # Check detected vs ground truth
        for d in detections:
            rec_id = d.record_id
            pred_type = d.detected_type

            if rec_id in gt_anomalies:
                actual_type = gt_anomalies[rec_id]
                if actual_type == pred_type:
                    tp[pred_type] += 1
                    confusion[actual_type][pred_type] += 1
                else:
                    fp[pred_type] += 1
                    confusion[actual_type][pred_type] += 1
                    false_positives.append({
                        "record_id": rec_id,
                        "detected_type": pred_type,
                        "actual_type": actual_type,
                        "evidence": d.evidence,
                    })
            else:
                # Detected something that is not an anomaly in ground truth
                fp[pred_type] += 1
                is_boundary = rec_id in gt_boundary_entities
                if is_boundary:
                    hard_neg_fp_count += 1
                    confusion["VALID_BOUNDARY"][pred_type] += 1
                else:
                    confusion["NORMAL"][pred_type] += 1

                false_positives.append({
                    "record_id": rec_id,
                    "detected_type": pred_type,
                    "actual_type": "VALID_BOUNDARY" if is_boundary else "NORMAL",
                    "evidence": d.evidence,
                })

        # Check ground truth anomalies that were missed (FN)
        for entity_id, actual_type in gt_anomalies.items():
            if entity_id not in detected_entities:
                fn[actual_type] += 1
                confusion[actual_type]["NORMAL"] += 1
                false_negatives.append({
                    "record_id": entity_id,
                    "expected_type": actual_type,
                    "evidence": "Not flagged by independent detector",
                })

        # Compute per-class precision, recall, F1
        per_class: Dict[str, ClassMetrics] = {}
        for itype in cls.KNOWN_ANOMALY_TYPES:
            c_tp = tp[itype]
            c_fp = fp[itype]
            c_fn = fn[itype]
            prec = (c_tp / (c_tp + c_fp)) if (c_tp + c_fp) > 0 else 1.0
            rec = (c_tp / (c_tp + c_fn)) if (c_tp + c_fn) > 0 else 1.0
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            per_class[itype] = ClassMetrics(
                issue_type=itype,
                true_positives=c_tp,
                false_positives=c_fp,
                false_negatives=c_fn,
                precision=round(prec, 4),
                recall=round(rec, 4),
                f1_score=round(f1, 4),
            )

        total_tp = sum(tp.values())
        total_fp = sum(fp.values())
        total_fn = sum(fn.values())
        overall_prec = (total_tp / (total_tp + total_fp)) if (total_tp + total_fp) > 0 else 1.0
        overall_rec = (total_tp / (total_tp + total_fn)) if (total_tp + total_fn) > 0 else 1.0
        overall_f1 = (2 * overall_prec * overall_rec / (overall_prec + overall_rec)) if (overall_prec + overall_rec) > 0 else 0.0

        explanation = (
            "Rule-engine conformance vs. ground truth: deterministic rules are expected to score "
            "1.0 on injected rule violations. The operational robustness test is the hard-negative set "
            "(VALID_BOUNDARY), where false positive count must strictly remain 0."
        )

        return EvaluationReport(
            per_class_metrics=per_class,
            overall_precision=round(overall_prec, 4),
            overall_recall=round(overall_rec, 4),
            overall_f1=round(overall_f1, 4),
            confusion_matrix=confusion,
            hard_negative_false_positive_count=hard_neg_fp_count,
            false_positives=false_positives,
            false_negatives=false_negatives,
            total_anomalies_ground_truth=len(gt_anomalies),
            total_valid_boundaries=len(gt_boundary_entities),
            conformance_explanation=explanation,
        )
