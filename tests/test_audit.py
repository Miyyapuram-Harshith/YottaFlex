from __future__ import annotations

"""
Unit Tests for Independent Audit Detection, Evaluation & Cryptographic Governance
Covers Hard Negatives (zero false positives), SoD enforcement, hash-chain tamper
detection, and deterministic reproducibility.
Python 3.9+ compatible.
"""

import json
import unittest
from core.models import LabelClass
from core.audit import IndependentAuditEngine, compute_event_hash
from core.evaluate import BenchmarkEvaluator
from erl_rma_benchmark import build_benchmark, check_reproducibility


class TestAuditAndGovernance(unittest.TestCase):

    def test_independent_detector_and_evaluation(self):
        """Independent detector must find all anomalies with 0 false positives on VALID_BOUNDARY."""
        dataset, ground_truth = build_benchmark(seed=20261022, scale=0.1)

        # 1. Independent detector runs without ground truth
        detections = IndependentAuditEngine.detect(dataset)
        self.assertGreaterEqual(len(detections), 25)

        # 2. Evaluator compares detections against ground truth
        report = BenchmarkEvaluator.evaluate(detections, ground_truth)
        self.assertEqual(report.hard_negative_false_positive_count, 0)
        self.assertEqual(report.overall_precision, 1.0)
        self.assertEqual(report.overall_recall, 1.0)
        self.assertEqual(report.overall_f1, 1.0)

        # Check all 5 classes have precision 1.0 and recall 1.0
        for itype, m in report.per_class_metrics.items():
            self.assertEqual(m.precision, 1.0, f"Class {itype} precision != 1.0")
            self.assertEqual(m.recall, 1.0, f"Class {itype} recall != 1.0")

    def test_detector_zero_reference_to_ground_truth(self):
        """Verify the detector module core/audit.py contains no references to ground_truth."""
        import inspect
        import core.audit
        src = inspect.getsource(core.audit)
        self.assertNotIn("ground_truth", src.lower())
        self.assertNotIn("gt_map", src)

    def test_hash_chain_tamper_detection(self):
        """Altering any payload field in an event breaks the cryptographic hash chain."""
        seq = 2
        prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        orig_hash = compute_event_hash(
            seq=seq,
            entity_type="Order",
            entity_id="ORD-2026-000001",
            prev_state="PLACED",
            new_state="DELIVERED",
            actor_id="CARRIER",
            event_ts="2026-03-05T12:00:00Z",
            prev_event_hash=prev_hash
        )

        # Tampered state
        tampered_hash = compute_event_hash(
            seq=seq,
            entity_type="Order",
            entity_id="ORD-2026-000001",
            prev_state="PLACED",
            new_state="CANCELLED",  # Tampered!
            actor_id="CARRIER",
            event_ts="2026-03-05T12:00:00Z",
            prev_event_hash=prev_hash
        )
        self.assertNotEqual(orig_hash, tampered_hash)

    def test_deterministic_reproducibility(self):
        """Two generations with the same seed yield identical byte-level CSV checksums."""
        self.assertTrue(check_reproducibility(seed=20261022, scale=0.05))


if __name__ == "__main__":
    unittest.main()
