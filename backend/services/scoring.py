"""
RevGuard — Recovery probability scoring service.
All logic is deterministic arithmetic — no AI calls.
Formula: priority_score = amount_in_rupees × recovery_probability
"""

from backend.models.case import RecoveryCase, DiagnosisBucket, RecoverabilityLevel

# Base recovery probability per failure bucket
BUCKET_BASE_PROBABILITY: dict[str, float] = {
    DiagnosisBucket.TEMPORARY_FAILURE: 0.88,
    DiagnosisBucket.INSUFFICIENT_FUNDS: 0.62,
    DiagnosisBucket.PAYMENT_CREDENTIAL_EXPIRED: 0.51,
    DiagnosisBucket.MANDATE_INACTIVE: 0.15,
    DiagnosisBucket.OTP_OR_AUTHENTICATION_ISSUE: 0.70,
    DiagnosisBucket.UNKNOWN: 0.45,
}

# Penalty per extra retry attempt (beyond the first)
RETRY_PENALTY_PER_ATTEMPT: float = 0.15

# Penalty for amounts above the threshold (> Rs.10,000)
AMOUNT_ABOVE_THRESHOLD_PENALTY: float = 0.05

# Amount threshold for penalty (paise) — kept in sync with config.POLICY_MAX_AMOUNT_AUTO
AMOUNT_PENALTY_THRESHOLD: int = 1_000_000


def recoverability_from_probability(prob: float) -> RecoverabilityLevel:
    if prob >= 0.75:
        return RecoverabilityLevel.HIGH
    elif prob >= 0.50:
        return RecoverabilityLevel.MEDIUM
    elif prob >= 0.20:
        return RecoverabilityLevel.LOW
    else:
        return RecoverabilityLevel.NONE


def calculate_recovery_probability(case: RecoveryCase) -> float:
    """
    Deterministic probability estimate.
    Documented so judges and reviewers can verify the math.
    """
    if not case.diagnosis:
        return 0.0

    bucket = case.diagnosis.bucket
    base = BUCKET_BASE_PROBABILITY.get(bucket, 0.40)

    # Retry penalty: each additional attempt reduces probability
    retry_penalty = RETRY_PENALTY_PER_ATTEMPT * max(0, case.attempt_count - 1) if hasattr(case, 'attempt_count') else 0.0

    # Amount penalty: high-value payments are harder to recover via a link
    amount_penalty = AMOUNT_ABOVE_THRESHOLD_PENALTY if case.amount > AMOUNT_PENALTY_THRESHOLD else 0.0

    probability = max(0.0, min(1.0, base - retry_penalty - amount_penalty))
    return round(probability, 4)


def score(case: RecoveryCase, attempt_count: int = 1) -> RecoveryCase:
    """
    Mutate and return the case with recovery_probability, recoverability, and priority_score filled.
    """
    # Temporarily attach attempt_count for scoring
    case.attempt_count = attempt_count  # type: ignore[attr-defined]
    prob = calculate_recovery_probability(case)
    case.recovery_probability = prob
    case.recoverability = recoverability_from_probability(prob)
    # priority_score = amount_in_rupees * recovery_probability (integer)
    amount_rupees = case.amount / 100
    case.priority_score = int(amount_rupees * prob)
    return case
