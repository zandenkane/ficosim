"""Tests for the scoring engine.

All tests use a fixed reference date so scores are deterministic
regardless of when CI runs.
"""

from datetime import date

from ficosim.constants import (
    fresh_start_profile,
    homeowner_profile,
    student_profile,
    young_professional_profile,
)
from ficosim.engine import (
    WEIGHTS,
    _amounts_owed_score,
    _credit_mix_score,
    _length_of_history_score,
    _new_credit_score,
    _payment_history_score,
    compute_score,
    compute_score_breakdown,
    score_band,
)
from ficosim.profile import (
    Account,
    AccountType,
    CreditProfile,
    PaymentRecord,
    PaymentStatus,
)

REF = date(2026, 6, 1)


class TestScoreBand:
    def test_excellent(self):
        assert score_band(800) == "Excellent"
        assert score_band(850) == "Excellent"

    def test_very_good(self):
        assert score_band(740) == "Very Good"
        assert score_band(799) == "Very Good"

    def test_good(self):
        assert score_band(670) == "Good"
        assert score_band(739) == "Good"

    def test_fair(self):
        assert score_band(580) == "Fair"
        assert score_band(669) == "Fair"

    def test_poor(self):
        assert score_band(300) == "Poor"
        assert score_band(579) == "Poor"


class TestWeights:
    def test_weights_sum_to_one(self):
        assert abs(sum(WEIGHTS.values()) - 1.0) < 0.001


class TestPaymentHistoryScore:
    def test_perfect_history(self):
        profile = CreditProfile(
            payment_history=[
                PaymentRecord(date(2026, 1, 1), PaymentStatus.ON_TIME, 0),
                PaymentRecord(date(2026, 2, 1), PaymentStatus.ON_TIME, 0),
                PaymentRecord(date(2026, 3, 1), PaymentStatus.ON_TIME, 0),
            ]
        )
        score = _payment_history_score(profile, REF)
        assert score == 1.0

    def test_no_history(self):
        profile = CreditProfile()
        score = _payment_history_score(profile, REF)
        assert score == 0.7

    def test_late_payment_reduces_score(self):
        profile = CreditProfile(
            payment_history=[
                PaymentRecord(date(2026, 1, 1), PaymentStatus.ON_TIME, 0),
                PaymentRecord(date(2026, 2, 1), PaymentStatus.ON_TIME, 0),
                PaymentRecord(date(2026, 3, 1), PaymentStatus.LATE_30, 0),
            ]
        )
        score = _payment_history_score(profile, REF)
        assert score < 1.0

    def test_worse_severity_hurts_more(self):
        base_history = [
            PaymentRecord(date(2026, 1, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2026, 2, 1), PaymentStatus.ON_TIME, 0),
        ]
        profile_30 = CreditProfile(
            payment_history=base_history + [
                PaymentRecord(date(2026, 3, 1), PaymentStatus.LATE_30, 0),
            ]
        )
        profile_90 = CreditProfile(
            payment_history=base_history + [
                PaymentRecord(date(2026, 3, 1), PaymentStatus.LATE_90, 0),
            ]
        )
        score_30 = _payment_history_score(profile_30, REF)
        score_90 = _payment_history_score(profile_90, REF)
        assert score_30 > score_90


class TestAmountsOwedScore:
    def test_zero_utilization(self):
        profile = CreditProfile(
            accounts=[Account(AccountType.REVOLVING, 0, 5000, date(2024, 1, 1))]
        )
        assert _amounts_owed_score(profile) == 1.0

    def test_low_utilization(self):
        profile = CreditProfile(
            accounts=[Account(AccountType.REVOLVING, 250, 5000, date(2024, 1, 1))]
        )
        score = _amounts_owed_score(profile)
        assert 0.9 <= score <= 1.0

    def test_high_utilization(self):
        profile = CreditProfile(
            accounts=[Account(AccountType.REVOLVING, 4500, 5000, date(2024, 1, 1))]
        )
        score = _amounts_owed_score(profile)
        assert score < 0.3

    def test_maxed_out(self):
        profile = CreditProfile(
            accounts=[Account(AccountType.REVOLVING, 5000, 5000, date(2024, 1, 1))]
        )
        score = _amounts_owed_score(profile)
        assert score < 0.1

    def test_no_revolving(self):
        profile = CreditProfile(
            accounts=[Account(AccountType.INSTALLMENT, 5000, 10000, date(2024, 1, 1))]
        )
        assert _amounts_owed_score(profile) == 1.0


class TestLengthOfHistoryScore:
    def test_new_account(self):
        profile = CreditProfile(
            accounts=[Account(AccountType.REVOLVING, 0, 1000, date(2026, 5, 1))]
        )
        score = _length_of_history_score(profile, REF)
        assert score < 0.1

    def test_established_accounts(self):
        profile = CreditProfile(
            accounts=[Account(AccountType.REVOLVING, 0, 1000, date(2020, 6, 1))]
        )
        score = _length_of_history_score(profile, REF)
        # ~72 months
        assert score > 0.7

    def test_very_old_account(self):
        profile = CreditProfile(
            accounts=[Account(AccountType.REVOLVING, 0, 1000, date(2014, 6, 1))]
        )
        score = _length_of_history_score(profile, REF)
        # ~144 months, should be at or near 1.0
        assert score >= 1.0

    def test_no_accounts(self):
        profile = CreditProfile()
        assert _length_of_history_score(profile, REF) == 0.0


class TestNewCreditScore:
    def test_no_inquiries(self):
        profile = CreditProfile()
        assert _new_credit_score(profile, REF) == 1.0

    def test_one_inquiry(self):
        profile = CreditProfile(hard_inquiries=[date(2026, 1, 1)])
        assert _new_credit_score(profile, REF) == 0.85

    def test_many_inquiries(self):
        profile = CreditProfile(
            hard_inquiries=[
                date(2026, 1, 1),
                date(2026, 2, 1),
                date(2026, 3, 1),
                date(2026, 4, 1),
                date(2026, 5, 1),
            ]
        )
        score = _new_credit_score(profile, REF)
        assert score == 0.25


class TestCreditMixScore:
    def test_no_accounts(self):
        profile = CreditProfile()
        assert _credit_mix_score(profile) == 0.0

    def test_one_type(self):
        profile = CreditProfile(
            accounts=[Account(AccountType.REVOLVING, 0, 1000, date(2024, 1, 1))]
        )
        assert _credit_mix_score(profile) == 0.4

    def test_two_types(self):
        profile = CreditProfile(
            accounts=[
                Account(AccountType.REVOLVING, 0, 1000, date(2024, 1, 1)),
                Account(AccountType.INSTALLMENT, 0, 5000, date(2024, 1, 1)),
            ]
        )
        assert _credit_mix_score(profile) == 0.7

    def test_three_types(self):
        profile = CreditProfile(
            accounts=[
                Account(AccountType.REVOLVING, 0, 1000, date(2024, 1, 1)),
                Account(AccountType.INSTALLMENT, 0, 5000, date(2024, 1, 1)),
                Account(AccountType.MORTGAGE, 0, 200000, date(2024, 1, 1)),
            ]
        )
        assert _credit_mix_score(profile) == 1.0


class TestComputeScore:
    def test_score_in_range(self):
        profile = CreditProfile(
            accounts=[Account(AccountType.REVOLVING, 500, 2000, date(2024, 1, 1))],
            payment_history=[
                PaymentRecord(date(2026, 1, 1), PaymentStatus.ON_TIME, 0),
            ],
        )
        score = compute_score(profile, REF)
        assert 300 <= score <= 850

    def test_min_score(self):
        # Worst possible profile
        profile = CreditProfile()
        score = compute_score(profile, REF)
        assert score >= 300

    def test_deterministic(self):
        profile = CreditProfile(
            accounts=[Account(AccountType.REVOLVING, 500, 2000, date(2024, 1, 1))],
            payment_history=[
                PaymentRecord(date(2026, 1, 1), PaymentStatus.ON_TIME, 0),
            ],
        )
        score1 = compute_score(profile, REF)
        score2 = compute_score(profile, REF)
        assert score1 == score2


class TestStarterProfiles:
    """Verify starter profiles land in the expected score bands."""

    def test_student_score_band(self):
        profile = student_profile()
        score = compute_score(profile, REF)
        # Target ~650 (Fair band: 580-669)
        assert 630 <= score <= 670
        assert score_band(score) == "Fair"

    def test_young_professional_score_band(self):
        profile = young_professional_profile()
        score = compute_score(profile, REF)
        # Target ~720 (Good band: 670-739)
        assert 700 <= score <= 740
        assert score_band(score) == "Good"

    def test_fresh_start_score_band(self):
        profile = fresh_start_profile()
        score = compute_score(profile, REF)
        # Target ~580 (Fair band: 580-669)
        assert 570 <= score <= 610
        assert score_band(score) == "Fair"

    def test_homeowner_score_band(self):
        profile = homeowner_profile()
        score = compute_score(profile, REF)
        # Target ~802 (Excellent band: 800+)
        assert 790 <= score <= 820
        assert score_band(score) == "Excellent"


class TestComputeScoreBreakdown:
    def test_breakdown_structure(self):
        profile = student_profile()
        breakdown = compute_score_breakdown(profile, REF)
        assert "score" in breakdown
        assert "band" in breakdown
        assert "categories" in breakdown
        assert len(breakdown["categories"]) == 5

    def test_breakdown_has_all_categories(self):
        profile = student_profile()
        breakdown = compute_score_breakdown(profile, REF)
        expected = {
            "payment_history",
            "amounts_owed",
            "length_of_history",
            "new_credit",
            "credit_mix",
        }
        assert set(breakdown["categories"].keys()) == expected

    def test_category_has_required_fields(self):
        profile = student_profile()
        breakdown = compute_score_breakdown(profile, REF)
        for cat in breakdown["categories"].values():
            assert "weight" in cat
            assert "sub_score" in cat
            assert "note" in cat
