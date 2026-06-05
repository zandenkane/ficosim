"""Integration test proving that ficosim actually simulates credit score changes.

This test exercises the full pipeline: create a profile, compute a score,
apply scenarios, and verify the score moves in the expected direction.
"""

from datetime import date

from ficosim.engine import compute_score, score_band
from ficosim.profile import (
    Account,
    AccountType,
    CreditProfile,
    PaymentRecord,
    PaymentStatus,
)
from ficosim.scenarios import miss_payment, pay_down_balance

REF = date(2026, 6, 1)


def _good_credit_profile() -> CreditProfile:
    """Build a profile with a good credit history (score in the 670-739 range).

    Two revolving accounts with low utilization, one installment loan,
    three years of perfect payment history, and one older hard inquiry.
    """
    payments = []
    # Quarterly on-time payments for account 0 over ~3 years
    for year in range(2023, 2027):
        for month in (1, 4, 7, 10):
            if date(year, month, 1) > date(2026, 5, 1):
                break
            payments.append(
                PaymentRecord(date(year, month, 1), PaymentStatus.ON_TIME, 0)
            )
    # Quarterly on-time payments for account 1
    for year in range(2024, 2027):
        for month in (1, 4, 7, 10):
            if date(year, month, 1) > date(2026, 5, 1):
                break
            payments.append(
                PaymentRecord(date(year, month, 1), PaymentStatus.ON_TIME, 1)
            )
    # Quarterly on-time payments for account 2
    for year in range(2023, 2027):
        for month in (1, 4, 7, 10):
            if date(year, month, 1) > date(2026, 5, 1):
                break
            payments.append(
                PaymentRecord(date(year, month, 1), PaymentStatus.ON_TIME, 2)
            )

    return CreditProfile(
        accounts=[
            Account(
                account_type=AccountType.REVOLVING,
                balance=2000,
                limit=8000,
                opened_date=date(2023, 6, 1),
            ),
            Account(
                account_type=AccountType.REVOLVING,
                balance=800,
                limit=5000,
                opened_date=date(2024, 3, 1),
            ),
            Account(
                account_type=AccountType.INSTALLMENT,
                balance=12000,
                limit=25000,
                opened_date=date(2023, 9, 1),
                monthly_payment=450,
            ),
        ],
        payment_history=payments,
        hard_inquiries=[date(2024, 3, 1)],
    )


class TestCreditScoreSimulationIntegration:
    """End-to-end test proving ficosim simulates credit score changes."""

    def test_good_profile_then_miss_payment_then_pay_off(self):
        # Step 1: Create a profile with good credit history
        profile = _good_credit_profile()
        initial_score = compute_score(profile, REF)

        # Verify the score is in the "Good" range (670-739)
        assert 670 <= initial_score <= 739, (
            f"Expected initial score in Good range (670-739), got {initial_score}"
        )
        assert score_band(initial_score) == "Good"

        # Step 2: Apply "miss a payment" scenario
        missed_profile, explanation = miss_payment(
            profile, 0, severity="30", payment_date=REF
        )
        missed_score = compute_score(missed_profile, REF)

        # Verify the score dropped
        assert missed_score < initial_score, (
            f"Expected score to drop after missed payment, "
            f"but went from {initial_score} to {missed_score}"
        )

        # Step 3: Apply "pay off balance" scenario -- pay off the revolving
        # balance on account 0 to reduce utilization and help recover
        recovered_profile, pay_explanation = pay_down_balance(
            missed_profile, 0, missed_profile.accounts[0].balance
        )
        recovered_score = compute_score(recovered_profile, REF)

        # Verify the score recovered somewhat (higher than the missed score)
        assert recovered_score > missed_score, (
            f"Expected score to recover after paying off balance, "
            f"but went from {missed_score} to {recovered_score}"
        )
