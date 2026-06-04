"""Tests for CreditProfile computed properties."""

from datetime import date

from ficosim.profile import (
    Account,
    AccountType,
    CreditProfile,
    PaymentRecord,
    PaymentStatus,
)

REF = date(2026, 6, 1)


def _simple_profile() -> CreditProfile:
    """Create a simple profile for testing."""
    return CreditProfile(
        accounts=[
            Account(AccountType.REVOLVING, balance=500, limit=2000, opened_date=date(2024, 6, 1)),
            Account(AccountType.INSTALLMENT, balance=10000, limit=20000, opened_date=date(2023, 6, 1)),
        ],
        payment_history=[
            PaymentRecord(date(2026, 1, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2026, 2, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2026, 3, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2026, 4, 1), PaymentStatus.LATE_30, 0),
        ],
        hard_inquiries=[date(2026, 1, 1), date(2025, 1, 1)],
    )


class TestTotalBalance:
    def test_sums_all_accounts(self):
        profile = _simple_profile()
        assert profile.total_balance == 10500

    def test_empty_accounts(self):
        profile = CreditProfile()
        assert profile.total_balance == 0


class TestTotalLimit:
    def test_only_open_revolving(self):
        profile = _simple_profile()
        # Only the revolving account's limit counts
        assert profile.total_limit == 2000

    def test_closed_revolving_excluded(self):
        profile = CreditProfile(
            accounts=[
                Account(AccountType.REVOLVING, 500, 2000, date(2024, 1, 1), is_open=False),
            ]
        )
        assert profile.total_limit == 0

    def test_installment_excluded(self):
        profile = CreditProfile(
            accounts=[
                Account(AccountType.INSTALLMENT, 5000, 10000, date(2024, 1, 1)),
            ]
        )
        assert profile.total_limit == 0


class TestUtilizationRatio:
    def test_basic_ratio(self):
        profile = _simple_profile()
        # Only revolving: balance=500, limit=2000
        assert profile.utilization_ratio == 0.25

    def test_zero_limit(self):
        profile = CreditProfile(
            accounts=[
                Account(AccountType.INSTALLMENT, 5000, 10000, date(2024, 1, 1)),
            ]
        )
        assert profile.utilization_ratio == 0.0

    def test_zero_balance(self):
        profile = CreditProfile(
            accounts=[
                Account(AccountType.REVOLVING, 0, 5000, date(2024, 1, 1)),
            ]
        )
        assert profile.utilization_ratio == 0.0

    def test_multiple_revolving(self):
        profile = CreditProfile(
            accounts=[
                Account(AccountType.REVOLVING, 300, 1000, date(2024, 1, 1)),
                Account(AccountType.REVOLVING, 700, 4000, date(2024, 1, 1)),
            ]
        )
        # (300 + 700) / (1000 + 4000) = 0.2
        assert profile.utilization_ratio == 0.2


class TestOnTimePaymentRatio:
    def test_mixed_history(self):
        profile = _simple_profile()
        # 3 on-time out of 4 total
        assert profile.on_time_payment_ratio == 0.75

    def test_perfect_history(self):
        profile = CreditProfile(
            payment_history=[
                PaymentRecord(date(2026, 1, 1), PaymentStatus.ON_TIME, 0),
                PaymentRecord(date(2026, 2, 1), PaymentStatus.ON_TIME, 0),
            ]
        )
        assert profile.on_time_payment_ratio == 1.0

    def test_no_history(self):
        profile = CreditProfile()
        assert profile.on_time_payment_ratio == 1.0


class TestAverageAccountAgeMonths:
    def test_known_ages(self):
        profile = CreditProfile(
            accounts=[
                Account(AccountType.REVOLVING, 0, 1000, opened_date=date(2024, 6, 1)),
                Account(AccountType.INSTALLMENT, 0, 5000, opened_date=date(2023, 6, 1)),
            ]
        )
        avg = profile.average_account_age_months(REF)
        # Account 1: ~24 months, Account 2: ~36 months, avg ~30
        assert 29 < avg < 31

    def test_no_accounts(self):
        profile = CreditProfile()
        assert profile.average_account_age_months(REF) == 0.0

    def test_single_account(self):
        profile = CreditProfile(
            accounts=[
                Account(AccountType.REVOLVING, 0, 1000, opened_date=date(2025, 6, 1)),
            ]
        )
        avg = profile.average_account_age_months(REF)
        # ~12 months
        assert 11.5 < avg < 12.5


class TestNumAccountTypes:
    def test_two_types(self):
        profile = _simple_profile()
        assert profile.num_account_types == 2

    def test_single_type(self):
        profile = CreditProfile(
            accounts=[
                Account(AccountType.REVOLVING, 0, 1000, date(2024, 1, 1)),
                Account(AccountType.REVOLVING, 0, 2000, date(2024, 1, 1)),
            ]
        )
        assert profile.num_account_types == 1

    def test_three_types(self):
        profile = CreditProfile(
            accounts=[
                Account(AccountType.REVOLVING, 0, 1000, date(2024, 1, 1)),
                Account(AccountType.INSTALLMENT, 0, 5000, date(2024, 1, 1)),
                Account(AccountType.MORTGAGE, 0, 200000, date(2024, 1, 1)),
            ]
        )
        assert profile.num_account_types == 3

    def test_no_accounts(self):
        profile = CreditProfile()
        assert profile.num_account_types == 0


class TestRecentInquiries:
    def test_filters_by_date(self):
        profile = _simple_profile()
        # date(2026, 1, 1) is within 12 months of REF
        # date(2025, 1, 1) is more than 12 months before REF, so excluded
        count = profile.recent_inquiries(REF)
        assert count == 1

    def test_old_inquiry_excluded(self):
        profile = CreditProfile(
            hard_inquiries=[date(2024, 1, 1)],
        )
        count = profile.recent_inquiries(REF)
        assert count == 0

    def test_no_inquiries(self):
        profile = CreditProfile()
        assert profile.recent_inquiries(REF) == 0


class TestDeepcopy:
    def test_independent_copy(self):
        profile = _simple_profile()
        copy = profile.deepcopy()
        copy.accounts[0].balance = 9999
        assert profile.accounts[0].balance == 500
