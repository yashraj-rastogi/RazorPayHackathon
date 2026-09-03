"""
RevGuard — Synthetic Data Generator
Generates reproducible datasets of NormalizedRevenueEvent records.

Usage:
    python data/generator.py --seed 42 --count 250 --out data/generated/v1.json
"""

import argparse
import json
import random
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATASET_VERSION = "v1"

# Distribution of failure types (percentages)
FAILURE_DISTRIBUTION = [
    # (failure_type, reason_code, gateway_messages, percent, policy_expectation)
    ("temporary_failure",         "BANK_TIMEOUT",          ["Issuer response unavailable", "Bank timeout error"], 0.34, "AUTO"),
    ("insufficient_funds",        "INSUFFICIENT_FUNDS",    ["Insufficient funds", "Balance too low"],              0.24, "AUTO"),
    ("payment_credential_expired","CARD_EXPIRED",          ["Card expired", "Credential expired"],                 0.09, "REVIEW"),
    ("mandate_inactive",          "MANDATE_CANCELLED",     ["Mandate not active", "Mandate cancelled"],            0.07, "BLOCKED"),
    ("otp_or_authentication_issue","OTP_FAILED",           ["OTP verification failed", "Authentication failed"],   0.05, "REVIEW"),
    ("unknown",                   "UNKNOWN_GATEWAY_ERROR", None,                                                   0.08, "REVIEW"),  # → Gemini
    ("already_successful",        "ALREADY_PAID",          ["Payment already processed"],                          0.05, "BLOCKED"),
    ("customer_opted_out",        "OPT_OUT",               ["Customer opted out"],                                 0.04, "BLOCKED"),
    ("retry_limit",               "RETRY_LIMIT",           ["Max retries exceeded"],                               0.04, "REVIEW"),
]

# Ambiguous gateway messages that should trigger Gemini
AMBIGUOUS_GATEWAY_MESSAGES = [
    "Unexpected issuer response while processing mandate debit.",
    "Transaction could not be processed at this time.",
    "Gateway processing error, please try again.",
    "Payment declined by issuer for unknown reason.",
    "System error during debit processing.",
    "Unclassified payment failure from acquiring bank.",
]

LANGUAGE_PREFS = ["english", "hindi", "hinglish"]
LANGUAGE_WEIGHTS = [0.4, 0.25, 0.35]

MERCHANT_IDS = ["m_001", "m_002", "m_003"]
BASE_DATE = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)

# Amount ranges in paise (Rs.199 to Rs.49,999)
# Mix above/below Rs.10,000 threshold (1,000,000 paise)
AMOUNT_RANGES = [
    (19900, 99900, 0.5),     # Rs.199–999 (below threshold)
    (100000, 999900, 0.35),  # Rs.1,000–9,999 (below threshold)
    (1000000, 4999900, 0.15),# Rs.10,000–49,999 (above threshold → REVIEW)
]


def pick_amount(rng: random.Random) -> int:
    """Returns an amount in paise."""
    roll = rng.random()
    cumulative = 0.0
    for low, high, weight in AMOUNT_RANGES:
        cumulative += weight
        if roll < cumulative:
            return rng.randint(low // 100, high // 100) * 100
    return 49900 * 100


def pick_attempt_count(rng: random.Random, failure_type: str) -> int:
    if failure_type == "retry_limit":
        return rng.randint(3, 5)
    elif failure_type == "temporary_failure":
        return rng.randint(1, 2)
    else:
        return rng.randint(1, 3)


def build_event(idx: int, seed: int, failure_type: str, reason_code: str, gateway_messages,
                rng: random.Random, is_duplicate: bool = False) -> dict:
    """Build one NormalizedRevenueEvent dict."""
    seed_str = f"{DATASET_VERSION}-{seed}-{idx}"
    event_id = f"evt_{hashlib.sha256(seed_str.encode()).hexdigest()[:8]}"

    merchant_id = rng.choice(MERCHANT_IDS)
    customer_id = f"c_{rng.randint(1, 60):03d}"
    subscription_id = f"sub_{rng.randint(1, 80):03d}"
    amount = pick_amount(rng)
    attempt_count = pick_attempt_count(rng, failure_type)
    language_pref = rng.choices(LANGUAGE_PREFS, weights=LANGUAGE_WEIGHTS)[0]
    occurred_at = BASE_DATE + timedelta(hours=rng.randint(0, 720))

    # Ambiguous → no fixed reason code, use ambiguous message
    if failure_type == "unknown":
        gw_message = rng.choice(AMBIGUOUS_GATEWAY_MESSAGES)
        actual_reason = "UNKNOWN_GATEWAY_ERROR"
    elif gateway_messages:
        gw_message = rng.choice(gateway_messages)
        actual_reason = reason_code
    else:
        gw_message = reason_code
        actual_reason = reason_code

    return {
        "event_id": event_id,
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "subscription_id": subscription_id,
        "revenue_type": "recurring_payment",
        "amount": amount,
        "currency": "INR",
        "status": "failed",
        "reason": actual_reason,
        "gateway_message": gw_message,
        "attempt_count": attempt_count,
        "occurred_at": occurred_at.isoformat(),
        "_meta": {
            "dataset_version": DATASET_VERSION,
            "seed": 42,
            "failure_type": failure_type,
            "language_pref": language_pref,
            "is_duplicate": is_duplicate,
        }
    }


def expected_policy(failure_type: str, amount: int, attempt_count: int) -> str:
    """Deterministic expected policy outcome for labeling."""
    if failure_type in ("already_successful", "customer_opted_out", "mandate_inactive"):
        return "BLOCKED"
    if failure_type == "retry_limit" or attempt_count >= 3:
        return "QUEUE_FOR_REVIEW"
    if failure_type in ("payment_credential_expired", "otp_or_authentication_issue"):
        return "QUEUE_FOR_REVIEW"
    if amount >= 1_000_000:  # >= Rs.10,000
        return "QUEUE_FOR_REVIEW"
    if failure_type == "unknown":
        return "QUEUE_FOR_REVIEW"  # Gemini may vary; conservative label
    return "AUTO"


def generate(seed: int, count: int) -> tuple[list[dict], dict]:
    """Returns (events_list, labels_dict)."""
    rng = random.Random(seed)
    events = []
    labels = {}  # event_id → {failure_type, expected_policy, expected_bucket}

    # Build weighted pool
    pool: list[tuple] = []
    for item in FAILURE_DISTRIBUTION:
        n = max(1, round(item[4 - 1] * count))  # item[3] is percent... reindex
        pool.extend([item] * n)

    # Rebuild properly
    pool = []
    for failure_type, reason_code, gateway_messages, pct, _ in FAILURE_DISTRIBUTION:
        n = max(1, round(pct * count))
        pool.extend([(failure_type, reason_code, gateway_messages)] * n)

    # Shuffle and trim/pad to count
    rng.shuffle(pool)
    while len(pool) < count:
        pool.append(pool[rng.randint(0, len(pool) - 1)])
    pool = pool[:count]

    # Designate 3 duplicate indices
    duplicate_targets = rng.sample(range(5, min(count, 50)), 3)
    duplicate_sources = {duplicate_targets[i]: duplicate_targets[i] - 3 for i in range(3)}

    for i, (failure_type, reason_code, gateway_messages) in enumerate(pool):
        is_dup = i in duplicate_sources
        event = build_event(i, seed, failure_type, reason_code, gateway_messages, rng, is_dup)

        # For duplicates, reuse source event_id
        if is_dup:
            source_idx = i - 3
            if source_idx >= 0 and source_idx < len(events):
                event["event_id"] = events[source_idx]["event_id"]
                event["_meta"]["is_duplicate"] = True

        events.append(event)
        expected_p = expected_policy(failure_type, event["amount"], event["attempt_count"])
        labels[event["event_id"]] = {
            "failure_type": failure_type,
            "expected_policy": expected_p,
            "expected_bucket": failure_type if failure_type not in ("already_successful", "customer_opted_out", "retry_limit") else "unknown",
        }

    return events, labels


def main():
    parser = argparse.ArgumentParser(description="RevGuard synthetic data generator")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--out", type=str, default="data/generated/v1.json")
    args = parser.parse_args()

    events, labels = generate(args.seed, args.count)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "metadata": {
            "dataset_version": DATASET_VERSION,
            "seed": args.seed,
            "count": len(events),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "events": events,
    }, indent=2))

    labels_path = Path("evaluation/labels.json")
    labels_path.write_text(json.dumps(labels, indent=2))

    # Print summary
    from collections import Counter
    type_counts = Counter(e["_meta"]["failure_type"] for e in events)
    policy_counts = Counter(labels[eid]["expected_policy"] for eid in labels)
    dup_count = sum(1 for e in events if e["_meta"].get("is_duplicate"))

    print(f"Generated {len(events)} events -> {args.out}")
    print(f"Labels -> evaluation/labels.json")
    print(f"\nFailure type distribution:")
    for k, v in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print(f"\nExpected policy distribution:")
    for k, v in sorted(policy_counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print(f"\nDuplicate events: {dup_count}")


if __name__ == "__main__":
    main()
