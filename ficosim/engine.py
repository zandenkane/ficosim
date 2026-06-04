"""Scoring engine: computes a credit score from a CreditProfile.

Uses five FICO-aligned categories with official weights.
The engine is pure (no I/O), deterministic, and fully testable.
"""

from __future__ import annotations

from datetime import date
from typing import Dict, Tuple

from ficosim.profile import CreditProfile, PaymentStatus

# FICO category weights
WEIGHTS: Dict[str, float] = {
    "payment_history": 0.35,
    "amounts_owed": 0.30,
    "length_of_history": 0.15,
    "new_credit": 0.10,
    "credit_mix": 0.10,
}

# Score band definitions
BANDS: list[Tuple[int, str]] = [
    (800, "Excellent"),
    (740, "Very Good"),
    (670, "Good"),
    (580, "Fair"),
    (300, "Poor"),
]


def score_band(score: int) -> str:
    for threshold, label in BANDS:
        if score >= threshold:
            return label
    return "Poor"


def _payment_history_score(profile: CreditProfile, reference_date: date | None = None) -> float:
    """Score payment history on a 0.0-1.0 scale.

    Based on the ratio of on-time payments, weighted by recency and
    severity of any delinquencies.
    if not profile.payment_history:
        # No history means no negatives, but not a perfect track record.
        return 0.7

    on_time_ratio = profile.on_time_payment_ratio
    base = on_time_ratio

    # Penalize based on severity of worst recent delinquency
    ref = reference_date or date.today()
    worst_severity = 0.0

    for record in profile.payment_history:
        severity = 0.0
        if record.status == PaymentStatus.LATE_30:
            severity = 0.15
        elif record.status == PaymentStatus.LATE_60:
            severity = 0.25
        elif record.status == PaymentStatus.LATE_90:
            severity = 0.40

        if severity > 0:
            months_ago = (ref - record.payment_date).days / 30.44
            # More recent delinquencies hurt more
            if months_ago < 6:
                recency_mult = 1.0
            elif months_ago < 12:
                recency_mult = 0.8
            elif months_ago < 24:
                recency_mult = 0.5
            else:
                recency_mult = 0.3

            weighted = severity * recency_mult
            if weighted > worst_severity:
                worst_severity = weighted

    result = base - worst_severity
    return max(0.0, min(1.0, result))


def _amounts_owed_score(profile: CreditProfile) -> float:
    """Score amounts owed (utilization) on a 0.0-1.0 scale.

    Thresholds: under 10% excellent, under 30% good,
    over 50% poor, over 75% very poor.
    """
    util = profile.utilization_ratio

    if util <= 0.0:
        return 1.0
    elif util <= 0.10:
        # 0-10%: excellent range, score 0.9-1.0
        return 1.0 - (util / 0.10) * 0.10
    elif util <= 0.30:
        # 10-30%: good range, score 0.65-0.9
        return 0.90 - ((util - 0.10) / 0.20) * 0.25
    elif util <= 0.50:
        # 30-50%: fair range, score 0.4-0.65
        return 0.65 - ((util - 0.30) / 0.20) * 0.25
    elif util <= 0.75:
        # 50-75%: poor range, score 0.2-0.4
        return 0.40 - ((util - 0.50) / 0.25) * 0.20
    else:
        # 75-100%+: very poor, score 0.0-0.2
        return max(0.0, 0.20 - ((util - 0.75) / 0.25) * 0.20)


def _length_of_history_score(
    profile: CreditProfile, reference_date: date | None = None
) -> float:
    """Score length of credit history on a 0.0-1.0 scale.

    Based on average account age in months. Diminishing returns past 7 years (84 months).
    """
    avg_months = profile.average_account_age_months(reference_date)

    if avg_months <= 0:
        return 0.0

    # Scale: 0 months = 0.0, 84 months (7 years) = 0.9, 120+ months = 1.0
    if avg_months >= 120:
        return 1.0
    elif avg_months >= 84:
        return 0.90 + (avg_months - 84) / (120 - 84) * 0.10
    else:
        # Linear from 0 to 0.9 over 84 months
        return (avg_months / 84) * 0.90


def _new_credit_score(profile: CreditProfile, reference_date: date | None = None) -> float:
    """Score new credit activity on a 0.0-1.0 scale.

    Based on number of hard inquiries in the last 12 months.
    Each inquiry past the first reduces the sub-score.
    """
    count = profile.recent_inquiries(reference_date)

    if count == 0:
        return 1.0
    elif count == 1:
        return 0.85
    elif count == 2:
        return 0.70
    elif count == 3:
        return 0.55
    elif count == 4:
        return 0.40
    elif count == 5:
        return 0.25
    else:
        return max(0.0, 0.25 - (count - 5) * 0.05)


def _credit_mix_score(profile: CreditProfile) -> float:
    """Score credit mix on a 0.0-1.0 scale.

    Based on variety of account types. More types is better, up to 3-4 types.
    """
    num_types = profile.num_account_types

    if num_types == 0:
        return 0.0
    elif num_types == 1:
        return 0.4
    elif num_types == 2:
        return 0.7
    elif num_types >= 3:
        return 1.0


def compute_category_scores(
    profile: CreditProfile, reference_date: date | None = None
) -> Dict[str, float]:
    """Compute each category's sub-score (0.0-1.0)."""
    return {
        "payment_history": _payment_history_score(profile, reference_date),
        "amounts_owed": _amounts_owed_score(profile),
        "length_of_history": _length_of_history_score(profile, reference_date),
        "new_credit": _new_credit_score(profile, reference_date),
        "credit_mix": _credit_mix_score(profile),
    }


def compute_score(
    profile: CreditProfile, reference_date: date | None = None
) -> int:
    """Compute a credit score (300-850) from a CreditProfile.

    Score = 300 + 550 * (weighted sum of category scores).
    scores = compute_category_scores(profile, reference_date)
    weighted_sum = sum(scores[cat] * WEIGHTS[cat] for cat in WEIGHTS)
    raw = 300 + 550 * weighted_sum
    return max(300, min(850, round(raw)))


def compute_score_breakdown(
    profile: CreditProfile, reference_date: date | None = None
) -> Dict[str, object]:
    """Return a full breakdown: score, band, and per-category details."""
    scores = compute_category_scores(profile, reference_date)
    total = compute_score(profile, reference_date)
    band = score_band(total)

    categories = {}
    notes = {
        "payment_history": _payment_history_note(scores["payment_history"]),
        "amounts_owed": _amounts_owed_note(profile.utilization_ratio),
        "length_of_history": _length_of_history_note(
            profile.average_account_age_months(reference_date)
        ),
        "new_credit": _new_credit_note(profile.recent_inquiries(reference_date)),
        "credit_mix": _credit_mix_note(profile.num_account_types),
    }

    for cat in WEIGHTS:
        categories[cat] = {
            "weight": WEIGHTS[cat],
            "sub_score": scores[cat],
            "note": notes[cat],
        }

    return {
        "score": total,
        "band": band,
        "categories": categories,
    }


# --- Note generators for each category ---


def _payment_history_note(sub_score: float) -> str:
    if sub_score >= 0.95:
        return "Perfect payment record"
    elif sub_score >= 0.8:
        return "Strong payment history"
    elif sub_score >= 0.6:
        return "Some late payments on record"
    else:
        return "Significant delinquencies"


def _amounts_owed_note(utilization: float) -> str:
    pct = round(utilization * 100)
    if utilization <= 0.10:
        return f"Very low utilization ({pct}%)"
    elif utilization <= 0.30:
        return f"Good utilization ({pct}%)"
    elif utilization <= 0.50:
        return f"Moderate utilization ({pct}%)"
    else:
        return f"High utilization ({pct}%)"


def _length_of_history_note(avg_months: float) -> str:
    years = avg_months / 12
    if avg_months < 6:
        return f"Very new accounts ({avg_months:.0f} months avg)"
    elif years < 2:
        return f"Building history ({avg_months:.0f} months avg)"
    elif years < 7:
        return f"Established history ({years:.1f} years avg)"
    else:
        return f"Long history ({years:.1f} years avg)"


def _new_credit_note(inquiry_count: int) -> str:
    if inquiry_count == 0:
        return "No recent inquiries"
    elif inquiry_count == 1:
        return "1 recent inquiry"
    else:
        return f"{inquiry_count} recent inquiries"


def _credit_mix_note(num_types: int) -> str:
    if num_types == 0:
        return "No accounts"
    elif num_types == 1:
        return "Only one account type"
    elif num_types == 2:
        return "Two account types"
    else:
        return "Good mix of account types"
