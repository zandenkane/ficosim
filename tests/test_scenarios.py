"""Tests for what-if scenarios.

Each test verifies that the scenario mutates the profile correctly
and moves the score in the expected direction. All tests use a fixed
reference date for deterministic results.
"""

import pytest
from datetime import date

from ficosim.constants import student_profile, young_professional_profile
from ficosim.engine import compute_score
from ficosim.profile import AccountType, PaymentStatus
from ficosim.scenarios import (
    apply_for_mortgage,
    close_account,
    make_large_purchase,
    max_out_card,
    miss_payment,
    open_card,
    pay_down_balance,
    transfer_balance,
)

REF = date(2026, 6, 1)


class TestMissPayment:
    def test_adds_late_record(self):
        profile = student_profile()
        new_profile, explanation = miss_payment(profile, 0, "30", payment_date=REF)
        late_records = [
            r for r in new_profile.payment_history
            if r.status == PaymentStatus.LATE_30
        ]
        # Original had 1 late_30, now should have 2
        assert len(late_records) == 2

    def test_lowers_score(self):
        profile = young_professional_profile()
        before = compute_score(profile, REF)
        new_profile, _ = miss_payment(profile, 0, "30", payment_date=REF)
        after = compute_score(new_profile, REF)
        assert after < before

    def test_worse_severity_hurts_more(self):
        profile = young_professional_profile()
        new_30, _ = miss_payment(profile, 0, "30", payment_date=REF)
        new_90, _ = miss_payment(profile, 0, "90", payment_date=REF)
        score_30 = compute_score(new_30, REF)
        score_90 = compute_score(new_90, REF)
        assert score_30 > score_90

    def test_original_unchanged(self):
        profile = student_profile()
        original_count = len(profile.payment_history)
        miss_payment(profile, 0, "30", payment_date=REF)
        assert len(profile.payment_history) == original_count

    def test_returns_explanation(self):
        profile = student_profile()
        _, explanation = miss_payment(profile, 0, "30", payment_date=REF)
        assert "30" in explanation
        assert len(explanation) > 20

    def test_invalid_index_raises(self):
        profile = student_profile()
        with pytest.raises(ValueError):
            miss_payment(profile, 99, "30")

    def test_invalid_severity_raises(self):
        profile = student_profile()
        with pytest.raises(ValueError):
            miss_payment(profile, 0, "45")


class TestOpenCard:
    def test_adds_account(self):
        profile = student_profile()
        new_profile, _ = open_card(profile, 5000, opened_date=REF)
        assert len(new_profile.accounts) == len(profile.accounts) + 1

    def test_new_account_is_revolving(self):
        profile = student_profile()
        new_profile, _ = open_card(profile, 5000, opened_date=REF)
        new_account = new_profile.accounts[-1]
        assert new_account.account_type == AccountType.REVOLVING
        assert new_account.balance == 0
        assert new_account.limit == 5000

    def test_adds_hard_inquiry(self):
        profile = student_profile()
        new_profile, _ = open_card(profile, 5000, opened_date=REF)
        assert len(new_profile.hard_inquiries) == len(profile.hard_inquiries) + 1

    def test_inquiry_count_increases(self):
        profile = young_professional_profile()
        before_inquiries = profile.recent_inquiries(REF)
        new_profile, _ = open_card(profile, 5000, opened_date=REF)
        after_inquiries = new_profile.recent_inquiries(REF)
        assert after_inquiries == before_inquiries + 1

    def test_utilization_decreases(self):
        profile = student_profile()
        before_util = profile.utilization_ratio
        new_profile, _ = open_card(profile, 5000, opened_date=REF)
        after_util = new_profile.utilization_ratio
        # Adding limit with $0 balance should lower utilization
        assert after_util < before_util

    def test_original_unchanged(self):
        profile = student_profile()
        original_count = len(profile.accounts)
        open_card(profile, 5000, opened_date=REF)
        assert len(profile.accounts) == original_count

    def test_returns_explanation(self):
        profile = student_profile()
        _, explanation = open_card(profile, 5000, opened_date=REF)
        assert "5,000" in explanation

    def test_invalid_limit_raises(self):
        profile = student_profile()
        with pytest.raises(ValueError):
            open_card(profile, 0)


class TestMaxOutCard:
    def test_sets_balance_to_limit(self):
        profile = student_profile()
        new_profile, _ = max_out_card(profile, 0)
        assert new_profile.accounts[0].balance == new_profile.accounts[0].limit

    def test_lowers_score(self):
        profile = young_professional_profile()
        before = compute_score(profile, REF)
        new_profile, _ = max_out_card(profile, 0)
        after = compute_score(new_profile, REF)
        assert after < before

    def test_only_revolving(self):
        profile = student_profile()
        # Account 1 is installment
        with pytest.raises(ValueError, match="revolving"):
            max_out_card(profile, 1)

    def test_original_unchanged(self):
        profile = student_profile()
        original_balance = profile.accounts[0].balance
        max_out_card(profile, 0)
        assert profile.accounts[0].balance == original_balance


class TestPayDownBalance:
    def test_reduces_balance(self):
        profile = student_profile()
        new_profile, _ = pay_down_balance(profile, 0, 200)
        assert new_profile.accounts[0].balance == profile.accounts[0].balance - 200

    def test_cannot_go_negative(self):
        profile = student_profile()
        new_profile, _ = pay_down_balance(profile, 0, 999999)
        assert new_profile.accounts[0].balance == 0

    def test_raises_score(self):
        profile = student_profile()
        before = compute_score(profile, REF)
        new_profile, _ = pay_down_balance(profile, 0, 300)
        after = compute_score(new_profile, REF)
        assert after >= before

    def test_original_unchanged(self):
        profile = student_profile()
        original_balance = profile.accounts[0].balance
        pay_down_balance(profile, 0, 100)
        assert profile.accounts[0].balance == original_balance

    def test_invalid_amount_raises(self):
        profile = student_profile()
        with pytest.raises(ValueError):
            pay_down_balance(profile, 0, -100)


class TestCloseAccount:
    def test_marks_account_closed(self):
        profile = student_profile()
        new_profile, _ = close_account(profile, 0)
        assert not new_profile.accounts[0].is_open

    def test_increases_utilization(self):
        profile = young_professional_profile()
        before_util = profile.utilization_ratio
        # Close account 1 (revolving, $1000/$5000) so that the remaining
        # revolving balance ($2200) is measured against a smaller limit ($8000)
        new_profile, _ = close_account(profile, 1)
        after_util = new_profile.utilization_ratio
        # $2200/$8000 = 0.275 > $3200/$13000 = 0.246
        assert after_util > before_util

    def test_already_closed_raises(self):
        profile = student_profile()
        new_profile, _ = close_account(profile, 0)
        with pytest.raises(ValueError, match="already closed"):
            close_account(new_profile, 0)

    def test_original_unchanged(self):
        profile = student_profile()
        close_account(profile, 0)
        assert profile.accounts[0].is_open is True


class TestMakeLargePurchase:
    def test_increases_balance(self):
        profile = student_profile()
        new_profile, _ = make_large_purchase(profile, 0, 500)
        assert new_profile.accounts[0].balance > profile.accounts[0].balance

    def test_capped_at_limit(self):
        profile = student_profile()
        new_profile, _ = make_large_purchase(profile, 0, 999999)
        assert new_profile.accounts[0].balance == profile.accounts[0].limit

    def test_lowers_score(self):
        profile = young_professional_profile()
        before = compute_score(profile, REF)
        new_profile, _ = make_large_purchase(profile, 0, 5000)
        after = compute_score(new_profile, REF)
        assert after < before

    def test_only_revolving(self):
        profile = student_profile()
        with pytest.raises(ValueError, match="revolving"):
            make_large_purchase(profile, 1, 1000)

    def test_original_unchanged(self):
        profile = student_profile()
        original_balance = profile.accounts[0].balance
        make_large_purchase(profile, 0, 500)
        assert profile.accounts[0].balance == original_balance

    def test_returns_explanation(self):
        profile = student_profile()
        _, explanation = make_large_purchase(profile, 0, 500)
        assert len(explanation) > 20


class TestApplyForMortgage:
    def test_adds_mortgage_account(self):
        profile = student_profile()
        new_profile, _ = apply_for_mortgage(profile, 250000, 300000, opened_date=REF)
        assert len(new_profile.accounts) == len(profile.accounts) + 1
        assert new_profile.accounts[-1].account_type == AccountType.MORTGAGE

    def test_adds_hard_inquiry(self):
        profile = student_profile()
        new_profile, _ = apply_for_mortgage(profile, 250000, 300000, opened_date=REF)
        assert len(new_profile.hard_inquiries) == len(profile.hard_inquiries) + 1

    def test_mortgage_balance_and_limit(self):
        profile = student_profile()
        new_profile, _ = apply_for_mortgage(profile, 250000, 300000, opened_date=REF)
        mortgage = new_profile.accounts[-1]
        assert mortgage.balance == 250000
        assert mortgage.limit == 300000

    def test_does_not_affect_utilization(self):
        profile = student_profile()
        before_util = profile.utilization_ratio
        new_profile, _ = apply_for_mortgage(profile, 250000, 300000, opened_date=REF)
        # Mortgage is not revolving, so utilization should stay the same
        assert new_profile.utilization_ratio == before_util

    def test_improves_credit_mix(self):
        profile = student_profile()
        before_types = profile.num_account_types
        new_profile, _ = apply_for_mortgage(profile, 250000, 300000, opened_date=REF)
        assert new_profile.num_account_types == before_types + 1

    def test_original_unchanged(self):
        profile = student_profile()
        original_count = len(profile.accounts)
        apply_for_mortgage(profile, 250000, 300000, opened_date=REF)
        assert len(profile.accounts) == original_count

    def test_returns_explanation(self):
        profile = student_profile()
        _, explanation = apply_for_mortgage(profile, 250000, 300000, opened_date=REF)
        assert "250,000" in explanation
        assert "mortgage" in explanation.lower()

    def test_invalid_loan_amount_raises(self):
        profile = student_profile()
        with pytest.raises(ValueError):
            apply_for_mortgage(profile, 0, 300000)

    def test_invalid_home_value_raises(self):
        profile = student_profile()
        with pytest.raises(ValueError):
            apply_for_mortgage(profile, 250000, 0)

    def test_loan_exceeds_value_raises(self):
        profile = student_profile()
        with pytest.raises(ValueError, match="cannot exceed"):
            apply_for_mortgage(profile, 400000, 300000)


class TestTransferBalance:
    def test_moves_balance(self):
        profile = young_professional_profile()
        # Account 0: $2200/$8000, Account 1: $1000/$5000
        new_profile, _ = transfer_balance(profile, 0, 1, 500)
        assert new_profile.accounts[0].balance == 2200 - 500
        assert new_profile.accounts[1].balance == 1000 + 500

    def test_total_balance_unchanged(self):
        profile = young_professional_profile()
        before_total = sum(
            a.balance for a in profile.accounts if a.account_type == AccountType.REVOLVING
        )
        new_profile, _ = transfer_balance(profile, 0, 1, 500)
        after_total = sum(
            a.balance for a in new_profile.accounts if a.account_type == AccountType.REVOLVING
        )
        assert before_total == after_total

    def test_capped_at_source_balance(self):
        profile = young_professional_profile()
        # Try to transfer more than source balance
        new_profile, _ = transfer_balance(profile, 0, 1, 999999)
        assert new_profile.accounts[0].balance == 0

    def test_capped_at_destination_room(self):
        # Account 0: $2200/$8000, Account 1: $1000/$5000
        # Dest room = $4000, but source only has $2200 so the transfer
        # is limited to $2200. To test the dest cap we need a source
        # with enough balance. We'll use a custom profile.
        from ficosim.profile import CreditProfile, Account

        big_profile = CreditProfile(
            accounts=[
                Account(AccountType.REVOLVING, 9000, 10000, REF),
                Account(AccountType.REVOLVING, 4000, 5000, REF),
            ],
        )
        # Dest room is only $1000
        new_profile, _ = transfer_balance(big_profile, 0, 1, 5000)
        assert new_profile.accounts[1].balance == 5000
        assert new_profile.accounts[0].balance == 8000

    def test_original_unchanged(self):
        profile = young_professional_profile()
        original_b0 = profile.accounts[0].balance
        transfer_balance(profile, 0, 1, 500)
        assert profile.accounts[0].balance == original_b0

    def test_same_index_raises(self):
        profile = young_professional_profile()
        with pytest.raises(ValueError, match="different"):
            transfer_balance(profile, 0, 0, 500)

    def test_invalid_amount_raises(self):
        profile = young_professional_profile()
        with pytest.raises(ValueError):
            transfer_balance(profile, 0, 1, -100)

    def test_non_revolving_source_raises(self):
        profile = young_professional_profile()
        # Account 2 is installment
        with pytest.raises(ValueError, match="revolving"):
            transfer_balance(profile, 2, 0, 500)

    def test_returns_explanation(self):
        profile = young_professional_profile()
        _, explanation = transfer_balance(profile, 0, 1, 500)
        assert "500" in explanation
