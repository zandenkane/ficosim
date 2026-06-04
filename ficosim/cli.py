"""Interactive CLI loop using questionary for input and rich for output."""

from __future__ import annotations

import sys

import questionary
from rich.console import Console

from ficosim.constants import REFERENCE_DATE, STARTER_PROFILES
from ficosim.engine import compute_score_breakdown
from ficosim.profile import AccountType, CreditProfile
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
from ficosim.ui import render_comparison, render_score, render_welcome

console = Console()

# Use the fixed reference date from constants for deterministic scoring.
REF = REFERENCE_DATE


def _pick_starter() -> CreditProfile:
    choices = list(STARTER_PROFILES.keys())
    answer = questionary.select(
        "Choose a starter profile:",
        choices=choices,
    ).ask()

    if answer is None:
        sys.exit(0)

    return STARTER_PROFILES[answer]()


def _format_account(index: int, account) -> str:
    status = "open" if account.is_open else "closed"
    return (
        f"[{index}] {account.account_type.value} "
        f"- ${account.balance:,.0f}/${account.limit:,.0f} ({status})"
    )


def _pick_account(profile: CreditProfile, filter_type=None, must_be_open=True) -> int | None:
    choices = []
    index_map = {}

    for i, account in enumerate(profile.accounts):
        if must_be_open and not account.is_open:
            continue
        if filter_type and account.account_type != filter_type:
            continue
        label = _format_account(i, account)
        choices.append(label)
        index_map[label] = i

    if not choices:
        console.print("[red]No eligible accounts for this action.[/red]")
        return None

    answer = questionary.select("Choose an account:", choices=choices).ask()
    if answer is None:
        return None
    return index_map[answer]


def _handle_miss_payment(profile: CreditProfile):
    idx = _pick_account(profile)
    if idx is None:
        return None

    severity = questionary.select(
        "How many days late?",
        choices=["30", "60", "90"],
    ).ask()
    if severity is None:
        return None

    return miss_payment(profile, idx, severity, payment_date=REF)


def _handle_open_card(profile: CreditProfile):
    limit_str = questionary.text(
        "Credit limit for the new card ($):",
        validate=lambda x: x.replace(".", "").replace(",", "").isdigit(),
    ).ask()
    if limit_str is None:
        return None

    limit = float(limit_str.replace(",", ""))
    return open_card(profile, limit, opened_date=REF)


def _handle_max_out_card(profile: CreditProfile):
    idx = _pick_account(profile, filter_type=AccountType.REVOLVING)
    if idx is None:
        return None
    return max_out_card(profile, idx)


def _handle_pay_down(profile: CreditProfile):
    idx = _pick_account(profile)
    if idx is None:
        return None

    account = profile.accounts[idx]
    amount_str = questionary.text(
        f"Amount to pay (balance is ${account.balance:,.0f}):",
        validate=lambda x: x.replace(".", "").replace(",", "").isdigit(),
    ).ask()
    if amount_str is None:
        return None

    amount = float(amount_str.replace(",", ""))
    return pay_down_balance(profile, idx, amount)


def _handle_close_account(profile: CreditProfile):
    idx = _pick_account(profile, must_be_open=True)
    if idx is None:
        return None
    return close_account(profile, idx)


def _handle_large_purchase(profile: CreditProfile):
    idx = _pick_account(profile, filter_type=AccountType.REVOLVING)
    if idx is None:
        return None

    account = profile.accounts[idx]
    remaining = account.limit - account.balance
    amount_str = questionary.text(
        f"Purchase amount (${remaining:,.0f} available):",
        validate=lambda x: x.replace(".", "").replace(",", "").isdigit(),
    ).ask()
    if amount_str is None:
        return None

    amount = float(amount_str.replace(",", ""))
    return make_large_purchase(profile, idx, amount)


def _handle_mortgage(profile: CreditProfile):
    home_str = questionary.text(
        "Home value ($):",
        validate=lambda x: x.replace(".", "").replace(",", "").isdigit(),
    ).ask()
    if home_str is None:
        return None

    home_value = float(home_str.replace(",", ""))

    loan_str = questionary.text(
        f"Loan amount (max ${home_value:,.0f}):",
        validate=lambda x: x.replace(".", "").replace(",", "").isdigit(),
    ).ask()
    if loan_str is None:
        return None

    loan_amount = float(loan_str.replace(",", ""))
    return apply_for_mortgage(profile, loan_amount, home_value, opened_date=REF)


def _handle_transfer(profile: CreditProfile):
    console.print("[bold]Select the source card:[/bold]")
    from_idx = _pick_account(profile, filter_type=AccountType.REVOLVING)
    if from_idx is None:
        return None

    console.print("[bold]Select the destination card:[/bold]")
    to_idx = _pick_account(profile, filter_type=AccountType.REVOLVING)
    if to_idx is None:
        return None

    if from_idx == to_idx:
        console.print("[red]Source and destination must be different accounts.[/red]")
        return None

    source = profile.accounts[from_idx]
    amount_str = questionary.text(
        f"Amount to transfer (source balance: ${source.balance:,.0f}):",
        validate=lambda x: x.replace(".", "").replace(",", "").isdigit(),
    ).ask()
    if amount_str is None:
        return None

    amount = float(amount_str.replace(",", ""))
    return transfer_balance(profile, from_idx, to_idx, amount)


ACTION_MAP = {
    "Miss a payment": _handle_miss_payment,
    "Open a new credit card": _handle_open_card,
    "Max out a credit card": _handle_max_out_card,
    "Pay down a balance": _handle_pay_down,
    "Close an account": _handle_close_account,
    "Make a large purchase": _handle_large_purchase,
    "Apply for a mortgage": _handle_mortgage,
    "Transfer a balance": _handle_transfer,
    "Reset profile": None,
    "Quit": None,
}


def main() -> None:
    """Run the interactive credit score simulator."""
    render_welcome()

    profile = _pick_starter()
    breakdown = compute_score_breakdown(profile, REF)

    console.print()
    render_score(breakdown)

    while True:
        console.print()
        action = questionary.select(
            "What do you want to try?",
            choices=list(ACTION_MAP.keys()),
        ).ask()

        if action is None or action == "Quit":
            console.print("[bold]Goodbye![/bold]")
            break

        if action == "Reset profile":
            profile = _pick_starter()
            breakdown = compute_score_breakdown(profile, REF)
            console.print()
            render_score(breakdown)
            continue

        handler = ACTION_MAP[action]
        result = handler(profile)

        if result is None:
            continue

        new_profile, explanation = result
        new_breakdown = compute_score_breakdown(new_profile, REF)

        render_comparison(breakdown, new_breakdown, explanation)

        # Update state
        profile = new_profile
        breakdown = new_breakdown


if __name__ == "__main__":
    main()
