"""Tests for CLI helper functions that do not require user interaction."""

from datetime import date

from ficosim.cli import _format_account
from ficosim.profile import Account, AccountType


class TestFormatAccount:
    def test_open_revolving(self):
        account = Account(
            account_type=AccountType.REVOLVING,
            balance=500,
            limit=2000,
            opened_date=date(2024, 1, 1),
            is_open=True,
        )
        result = _format_account(0, account)
        assert "[0]" in result
        assert "revolving" in result
        assert "open" in result
        assert "$500" in result
        assert "$2,000" in result

    def test_closed_installment(self):
        account = Account(
            account_type=AccountType.INSTALLMENT,
            balance=10000,
            limit=20000,
            opened_date=date(2023, 1, 1),
            is_open=False,
        )
        result = _format_account(1, account)
        assert "[1]" in result
        assert "installment" in result
        assert "closed" in result

    def test_mortgage_account(self):
        account = Account(
            account_type=AccountType.MORTGAGE,
            balance=280000,
            limit=320000,
            opened_date=date(2022, 1, 1),
            is_open=True,
        )
        result = _format_account(2, account)
        assert "[2]" in result
        assert "mortgage" in result
        assert "open" in result

    def test_zero_balance(self):
        account = Account(
            account_type=AccountType.REVOLVING,
            balance=0,
            limit=5000,
            opened_date=date(2024, 1, 1),
        )
        result = _format_account(0, account)
        assert "$0" in result
