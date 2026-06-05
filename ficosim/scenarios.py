"""What-if scenarios that mutate a CreditProfile copy and return the result.

Each scenario is a pure function: takes a CreditProfile and parameters,
returns a (new_profile, explanation) tuple. The original profile is never modified.
"""

from __future__ import annotations

from datetime import date
from typing import Tuple

from ficosim.profile import (
    Account,
    AccountType,
    CreditProfile,
    PaymentRecord,
    PaymentStatus,
)


def miss_payment(
    profile: CreditProfile,
    account_index: int,
    severity: str = "30",
    payment_date: date | None = None,
) -> Tuple[CreditProfile, str]:
    """Simulate missing a payment on an account.

    Args:
        profile: Current credit profile.
        account_index: Which account missed the payment.
        severity: "30", "60", or "90" for days late.
        payment_date: Date of the missed payment (defaults to today).

    Returns:
        Tuple of (new_profile, explanation_string).
    """
    if account_index < 0 or account_index >= len(profile.accounts):
        raise ValueError(f"Invalid account index: {account_index}")

    status_map = {
        "30": PaymentStatus.LATE_30,
        "60": PaymentStatus.LATE_60,
        "90": PaymentStatus.LATE_90,
    }
    if severity not in status_map:
        raise ValueError(f"Severity must be '30', '60', or '90', got '{severity}'")

    new_profile = profile.deepcopy()
    pdate = payment_date or date.today()
    record = PaymentRecord(pdate, status_map[severity], account_index)
    new_profile.payment_history.append(record)

    account = new_profile.accounts[account_index]
    explanation = (
        f"Missed a payment on account {account_index} "
        f"({account.account_type.value}, ${account.limit:,.0f} limit) "
        f"by {severity} days. "
        f"Payment history is the largest factor in your score (35%). "
        f"Even a single late payment can cause a significant drop, "
        f"especially if it is recent."
    )
    return new_profile, explanation


def open_card(
    profile: CreditProfile,
    limit: float,
    opened_date: date | None = None,
) -> Tuple[CreditProfile, str]:
    """Simulate opening a new credit card.

    Adds a new revolving account with $0 balance and a hard inquiry.

    Args:
        profile: Current credit profile.
        limit: Credit limit on the new card.
        opened_date: When the card was opened (defaults to today).

    Returns:
        Tuple of (new_profile, explanation_string).
    """
    if limit <= 0:
        raise ValueError("Credit limit must be positive")

    new_profile = profile.deepcopy()
    odate = opened_date or date.today()

    new_account = Account(
        account_type=AccountType.REVOLVING,
        balance=0,
        limit=limit,
        opened_date=odate,
    )
    new_profile.accounts.append(new_account)
    new_profile.hard_inquiries.append(odate)

    explanation = (
        f"Opened a new credit card with a ${limit:,.0f} limit. "
        f"This adds a hard inquiry (affects New Credit, 10% of score) "
        f"and lowers your average account age (Length of History, 15%). "
        f"However, it increases your total available credit, "
        f"which can lower your utilization ratio (Amounts Owed, 30%)."
    )
    return new_profile, explanation


def max_out_card(
    profile: CreditProfile,
    account_index: int,
) -> Tuple[CreditProfile, str]:
    """Simulate maxing out a credit card (balance = limit).

    Args:
        profile: Current credit profile.
        account_index: Which revolving account to max out.

    Returns:
        Tuple of (new_profile, explanation_string).
    """
    if account_index < 0 or account_index >= len(profile.accounts):
        raise ValueError(f"Invalid account index: {account_index}")

    account = profile.accounts[account_index]
    if account.account_type != AccountType.REVOLVING:
        raise ValueError("Can only max out revolving (credit card) accounts")

    new_profile = profile.deepcopy()
    old_balance = new_profile.accounts[account_index].balance
    new_profile.accounts[account_index].balance = account.limit

    explanation = (
        f"Maxed out account {account_index} "
        f"(balance went from ${old_balance:,.0f} to ${account.limit:,.0f}). "
        f"Credit utilization is the main factor in Amounts Owed (30% of score). "
        f"Maxing out a card pushes utilization toward 100%, "
        f"which is one of the fastest ways to lower your score."
    )
    return new_profile, explanation


def pay_down_balance(
    profile: CreditProfile,
    account_index: int,
    amount: float,
) -> Tuple[CreditProfile, str]:
    """Simulate paying down a balance on an account.

    Args:
        profile: Current credit profile.
        account_index: Which account to pay down.
        amount: Dollar amount to pay.

    Returns:
        Tuple of (new_profile, explanation_string).
    """
    if account_index < 0 or account_index >= len(profile.accounts):
        raise ValueError(f"Invalid account index: {account_index}")
    if amount <= 0:
        raise ValueError("Payment amount must be positive")

    new_profile = profile.deepcopy()
    account = new_profile.accounts[account_index]
    old_balance = account.balance
    account.balance = max(0, account.balance - amount)
    actual_paid = old_balance - account.balance

    explanation = (
        f"Paid ${actual_paid:,.0f} on account {account_index} "
        f"(balance went from ${old_balance:,.0f} to ${account.balance:,.0f}). "
        f"Lowering your balance reduces your utilization ratio, "
        f"which is a major part of Amounts Owed (30% of score). "
        f"Getting under 30% utilization is good; under 10% is ideal."
    )
    return new_profile, explanation


def close_account(
    profile: CreditProfile,
    account_index: int,
) -> Tuple[CreditProfile, str]:
    """Simulate closing an account.

    The account stays in the profile (closed accounts remain on credit reports)
    but is marked as closed, removing its limit from available credit.

    Args:
        profile: Current credit profile.
        account_index: Which account to close.

    Returns:
        Tuple of (new_profile, explanation_string).
    """
    if account_index < 0 or account_index >= len(profile.accounts):
        raise ValueError(f"Invalid account index: {account_index}")

    account = profile.accounts[account_index]
    if not account.is_open:
        raise ValueError("Account is already closed")

    new_profile = profile.deepcopy()
    new_profile.accounts[account_index].is_open = False

    explanation = (
        f"Closed account {account_index} "
        f"({account.account_type.value}, ${account.limit:,.0f} limit). "
        f"Closing an account removes its limit from your available credit, "
        f"which can increase your utilization ratio (Amounts Owed, 30%). "
        f"It also reduces your credit mix (10%) if it was your only account "
        f"of that type. The account's age still counts in your history."
    )
    return new_profile, explanation


def make_large_purchase(
    profile: CreditProfile,
    account_index: int,
    amount: float,
) -> Tuple[CreditProfile, str]:
    """Simulate making a large purchase on a revolving account.

    Args:
        profile: Current credit profile.
        account_index: Which revolving account to charge.
        amount: Dollar amount of the purchase.

    Returns:
        Tuple of (new_profile, explanation_string).
    """
    if account_index < 0 or account_index >= len(profile.accounts):
        raise ValueError(f"Invalid account index: {account_index}")
    if amount <= 0:
        raise ValueError("Purchase amount must be positive")

    account = profile.accounts[account_index]
    if account.account_type != AccountType.REVOLVING:
        raise ValueError("Can only make purchases on revolving (credit card) accounts")

    new_profile = profile.deepcopy()
    old_balance = new_profile.accounts[account_index].balance
    new_balance = old_balance + amount
    # Cap at limit (can't spend over limit in this simulation)
    new_profile.accounts[account_index].balance = min(new_balance, account.limit)
    actual_added = new_profile.accounts[account_index].balance - old_balance

    explanation = (
        f"Made a ${actual_added:,.0f} purchase on account {account_index} "
        f"(balance went from ${old_balance:,.0f} "
        f"to ${new_profile.accounts[account_index].balance:,.0f}). "
        f"Large purchases increase your utilization ratio. "
        f"If utilization jumps above 30%, your Amounts Owed sub-score (30%) drops. "
        f"Paying the balance before the statement closes can prevent the hit."
    )
    return new_profile, explanation


def apply_for_mortgage(
    profile: CreditProfile,
    loan_amount: float,
    home_value: float,
    opened_date: date | None = None,
) -> Tuple[CreditProfile, str]:
    """Simulate applying for a mortgage.

    Adds a mortgage account and a hard inquiry. Mortgages improve credit mix
    but add a new inquiry and lower average account age.

    Args:
        profile: Current credit profile.
        loan_amount: Size of the mortgage loan.
        home_value: Appraised value of the home (used as the limit).
        opened_date: When the mortgage was opened (defaults to today).

    Returns:
        Tuple of (new_profile, explanation_string).
    """
    if loan_amount <= 0:
        raise ValueError("Loan amount must be positive")
    if home_value <= 0:
        raise ValueError("Home value must be positive")
    if loan_amount > home_value:
        raise ValueError("Loan amount cannot exceed home value")

    new_profile = profile.deepcopy()
    odate = opened_date or date.today()

    mortgage = Account(
        account_type=AccountType.MORTGAGE,
        balance=loan_amount,
        limit=home_value,
        opened_date=odate,
        monthly_payment=round(loan_amount / 360, 2),  # rough 30-year estimate
    )
    new_profile.accounts.append(mortgage)
    new_profile.hard_inquiries.append(odate)

    had_mortgage = any(
        a.account_type == AccountType.MORTGAGE for a in profile.accounts
    )
    mix_note = (
        "You already had a mortgage, so credit mix is unchanged."
        if had_mortgage
        else "Adding a mortgage improves your credit mix (10% of score)."
    )

    explanation = (
        f"Applied for a ${loan_amount:,.0f} mortgage on a ${home_value:,.0f} home. "
        f"This adds a hard inquiry (New Credit, 10%) "
        f"and lowers average account age (Length of History, 15%). "
        f"{mix_note} "
        f"Mortgages do not count toward revolving utilization."
    )
    return new_profile, explanation


def transfer_balance(
    profile: CreditProfile,
    from_index: int,
    to_index: int,
    amount: float,
) -> Tuple[CreditProfile, str]:
    """Simulate a balance transfer between two revolving accounts.

    Moves balance from one card to another. Useful for shifting debt
    to a lower-utilization card.

    Args:
        profile: Current credit profile.
        from_index: Source account index.
        to_index: Destination account index.
        amount: Dollar amount to transfer.

    Returns:
        Tuple of (new_profile, explanation_string).
    """
    if from_index < 0 or from_index >= len(profile.accounts):
        raise ValueError(f"Invalid source account index: {from_index}")
    if to_index < 0 or to_index >= len(profile.accounts):
        raise ValueError(f"Invalid destination account index: {to_index}")
    if from_index == to_index:
        raise ValueError("Source and destination must be different accounts")
    if amount <= 0:
        raise ValueError("Transfer amount must be positive")

    source = profile.accounts[from_index]
    dest = profile.accounts[to_index]
    if source.account_type != AccountType.REVOLVING:
        raise ValueError("Source account must be revolving")
    if dest.account_type != AccountType.REVOLVING:
        raise ValueError("Destination account must be revolving")

    new_profile = profile.deepcopy()
    actual_transfer = min(amount, new_profile.accounts[from_index].balance)
    dest_room = dest.limit - dest.balance
    actual_transfer = min(actual_transfer, dest_room)

    new_profile.accounts[from_index].balance -= actual_transfer
    new_profile.accounts[to_index].balance += actual_transfer

    explanation = (
        f"Transferred ${actual_transfer:,.0f} from account {from_index} "
        f"to account {to_index}. "
        f"Balance transfers move debt between cards but do not change "
        f"your total balance or overall utilization ratio. "
        f"However, spreading balances more evenly can help if a lender "
        f"looks at per-card utilization."
    )
    return new_profile, explanation
