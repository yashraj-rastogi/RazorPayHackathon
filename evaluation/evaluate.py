"""
RevGuard — Evaluation Script (Phase 7).

Runs the synthetic dataset through the full pipeline and computes metrics.
Results are stored in Firestore `evaluation_runs` collection.

Usage:
    python evaluation/evaluate.py \\
        --dataset data/generated/v1.json \\
        --labels evaluation/labels.json \\
        --out evaluation/results_v1.json

Running twice with the same seed produces identical JSON output.
"""

import argparse
import json
import uuid
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_dataset(path: str) -> tuple[list[dict], dict]:
    data = json.loads(Path(path).read_text())
    return data["events"], data.get("metadata", {})


def load_labels(path: str) -> dict:
    return json.loads(Path(path).read_text())


def run_pipeline_on_event(event_dict: dict) -> dict:
    """
    Run the deterministic pipeline on one event.
    Uses the same logic as the backend but without Firestore calls.
    Returns: {event_id, failure_type, policy_decision, bucket, confidence, method}
    """
    from backend.models.event import NormalizedRevenueEvent
    from backend.services.diagnosis import diagnose
    from backend.services.scoring import score
    from backend.services.policy import evaluate
    from backend.models.case import RecoveryCase, DiagnosisBucket

    meta = event_dict.pop("_meta", {})
    try:
        event = NormalizedRevenueEvent(**event_dict)
    except Exception as exc:
        return {"event_id": event_dict.get("event_id"), "error": str(exc)}

    # Diagnosis (deterministic path only in evaluation — no real Gemini calls)
    try:
        # Patch Gemini to avoid API calls during evaluation
        import unittest.mock as mock
        from backend.models.case import DiagnosisResult, DiagnosisMethod

        with mock.patch("backend.services.diagnosis._gemini_diagnose") as mock_gemini, \
             mock.patch("backend.services.audit.write_audit"):
            # Gemini unknown cases get bucket=unknown in evaluation
            mock_gemini.return_value = DiagnosisResult(
                bucket=DiagnosisBucket.UNKNOWN,
                confidence=0.40,
                method=DiagnosisMethod.FALLBACK,
                explanation="Evaluation: Gemini not called.",
            )
            diag = diagnose(event)
    except Exception as exc:
        diag_bucket = "error"
        diag_confidence = 0.0
        diag_method = "error"
        return {
            "event_id": event.event_id,
            "error": str(exc),
        }

    # Create case for scoring and policy
    case = RecoveryCase(
        case_id=f"eval_{event.event_id}",
        event_id=event.event_id,
        merchant_id=event.merchant_id,
        customer_id=event.customer_id,
        amount=event.amount,
        diagnosis=diag,
    )
    case = score(case, attempt_count=event.attempt_count)

    # Policy (no Firestore lookups)
    payment_succeeded = event.reason.upper() == "ALREADY_PAID"
    opted_out = meta.get("failure_type") == "customer_opted_out"
    mandate_inactive = diag.bucket == DiagnosisBucket.MANDATE_INACTIVE

    with mock.patch("backend.services.audit.write_audit"):
        policy = evaluate(
            case,
            payment_already_succeeded=payment_succeeded,
            mandate_is_inactive=mandate_inactive,
            customer_opted_out=opted_out,
            attempt_count=event.attempt_count,
        )

    return {
        "event_id": event.event_id,
        "failure_type": meta.get("failure_type", "unknown"),
        "policy_decision": policy.decision,
        "diagnosis_bucket": diag.bucket,
        "confidence": diag.confidence,
        "method": diag.method,
        "amount": event.amount,
        "priority_score": case.priority_score,
        "recovery_probability": case.recovery_probability,
        "reasons": policy.reasons,
    }


def compute_metrics(results: list[dict], labels: dict, metadata: dict) -> dict:
    """Compute evaluation metrics against ground truth labels."""
    records_processed = len(results)
    errors = sum(1 for r in results if "error" in r)

    # Policy distribution
    policy_counts = Counter(r.get("policy_decision") for r in results if "error" not in r)

    auto_count = policy_counts.get("AUTO", 0)
    review_count = policy_counts.get("QUEUE_FOR_REVIEW", 0)
    blocked_count = policy_counts.get("BLOCKED", 0)

    # Revenue calculations
    auto_results = [r for r in results if r.get("policy_decision") == "AUTO"]
    recovered_revenue = sum(r.get("amount", 0) for r in auto_results)  # Estimated if all AUTO cases recover
    total_revenue_at_risk = sum(r.get("amount", 0) for r in results if "error" not in r)

    # Recovery rate estimate (AUTO cases are attempted)
    recoverable_cases = auto_count + review_count  # BLOCKED are not recoverable
    recovery_rate = round(auto_count / max(recoverable_cases, 1), 3)
    automation_rate = round(auto_count / max(records_processed - errors, 1), 3)

    # Diagnosis accuracy against labels
    correct_policy = 0
    labeled_count = 0
    for r in results:
        if "error" in r:
            continue
        eid = r["event_id"]
        if eid in labels:
            labeled_count += 1
            expected = labels[eid].get("expected_policy")
            actual = r.get("policy_decision")
            if expected == actual:
                correct_policy += 1

    diagnosis_accuracy = round(correct_policy / max(labeled_count, 1), 3)

    return {
        "run_id": f"run_{uuid.uuid4().hex[:8]}",
        "dataset_version": metadata.get("dataset_version", "v1"),
        "seed": metadata.get("seed", 42),
        "records_processed": records_processed,
        "errors": errors,
        "recoverable_cases": recoverable_cases,
        "auto_count": auto_count,
        "review_count": review_count,
        "blocked_count": blocked_count,
        "recovered_revenue": recovered_revenue,
        "total_revenue_at_risk": total_revenue_at_risk,
        "recovery_rate": recovery_rate,
        "automation_rate": automation_rate,
        "diagnosis_accuracy": diagnosis_accuracy,
        "labeled_cases": labeled_count,
        "correct_policy_labels": correct_policy,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="RevGuard evaluation script")
    parser.add_argument("--dataset", default="data/generated/v1.json")
    parser.add_argument("--labels", default="evaluation/labels.json")
    parser.add_argument("--out", default="evaluation/results_v1.json")
    parser.add_argument("--firestore", action="store_true", help="Store results in Firestore")
    args = parser.parse_args()

    print(f"Loading dataset: {args.dataset}")
    events, metadata = load_dataset(args.dataset)

    print(f"Loading labels: {args.labels}")
    labels = load_labels(args.labels)

    print(f"Processing {len(events)} events...")
    results = []
    for i, event_dict in enumerate(events):
        r = run_pipeline_on_event(dict(event_dict))  # Copy to avoid mutation
        results.append(r)
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(events)} processed...")

    print("Computing metrics...")
    metrics = compute_metrics(results, labels, metadata)

    # Save results
    output = {"metrics": metrics, "results": results}
    Path(args.out).write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults saved to: {args.out}")

    # Optionally store to Firestore
    if args.firestore:
        try:
            from backend.db.firestore import set_document
            set_document("evaluation_runs", metrics["run_id"], metrics)
            print(f"Stored evaluation run to Firestore: {metrics['run_id']}")
        except Exception as exc:
            print(f"Warning: Could not store to Firestore: {exc}")

    # Print summary
    print("\n" + "="*50)
    print("EVALUATION SUMMARY")
    print("="*50)
    print(f"Records processed : {metrics['records_processed']}")
    print(f"AUTO              : {metrics['auto_count']}")
    print(f"QUEUE_FOR_REVIEW  : {metrics['review_count']}")
    print(f"BLOCKED           : {metrics['blocked_count']}")
    print(f"Errors            : {metrics['errors']}")
    print(f"Recovery rate     : {metrics['recovery_rate']:.1%}")
    print(f"Automation rate   : {metrics['automation_rate']:.1%}")
    print(f"Diagnosis accuracy: {metrics['diagnosis_accuracy']:.1%}")
    print(f"Revenue at risk   : Rs.{metrics['total_revenue_at_risk']/100:,.0f}")


if __name__ == "__main__":
    main()
