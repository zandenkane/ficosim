"""Credit profile data model with Account, PaymentRecord, and CreditProfile."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List


class AccountType(Enum):

    REVOLVING = "revolving"
    INSTALLMENT = "installment"
    MORTGAGE = "mortgage"


class PaymentStatus(Enum):
    """Payment status for a single payment event."""

    ON_TIME = "on_time"
    LATE_30 = "late_30"
    LATE_60 = "late_60"
    LATE_90 = "late_90"


@dataclass
class Account:

    account_type: AccountType
    balance: float
    limit: float
    opened_date: date
    is_open: bool = True
    monthly_payment: float = 0.0


@dataclass
class PaymentRecord:

    payment_date: date
    status: PaymentStatus
    account_index: int


@dataclass
class CreditProfile:

    accounts: List[Account] = field(default_factory=list)
    payment_history: List[PaymentRecord] = field(default_factory=list)
    hard_inquiries: List[date] = field(default_factory=list)

    @property
    def total_balance(self) -> float:
        """Sum of balances across all accounts."""
        return sum(a.balance for a in self.accounts)

    @property
    def total_limit(self) -> float:
        """Sum of credit limits across all open revolving accounts."""
        total = sum(
            a.limit
            for a in self.accounts
            if a.account_type == AccountType.REVOLVING and a.is_open
        )
        return total

    @property
    def utilization_ratio(self) -> float:
        """Total revolving balance divided by total revolving limit."""
        revolving_balance = sum(
            a.balance
            for a in self.accounts
            if a.account_type == AccountType.REVOLVING and a.is_open
        )
        revolving_limit = self.total_limit
        if revolving_limit == 0:
            return 0.0
        return revolving_balance / revolving_limit

    @property
    def on_time_payment_ratio(self) -> float:
        if not self.payment_history:
            return 1.0
        on_time = sum(
            1 for p in self.payment_history if p.status == PaymentStatus.ON_TIME
        )
        return on_time / len(self.payment_history)

    def average_account_age_months(self, reference_date: date | None = None) -> float:
        if not self.accounts:
            return 0.0
        ref = reference_date or date.today()
        total_months = 0.0
        for account in self.accounts:
            delta = ref - account.opened_date
            total_months += delta.days / 30.44  # average days per month
        return total_months / len(self.accounts)

    @property
    def num_account_types(self) -> int:
        return len({a.account_type for a in self.accounts})

    def recent_inquiries(self, reference_date: date | None = None) -> int:
        """Number of hard inquiries in the last 12 months."""
        ref = reference_date or date.today()
        cutoff = date(ref.year - 1, ref.month, ref.day)
        return sum(1 for d in self.hard_inquiries if d >= cutoff)

    def deepcopy(self) -> CreditProfile:
        """Return an independent deep copy of this profile."""
        return copy.deepcopy(self)
