"""Starter profiles representing common credit situations.

Each profile is built with a fixed reference date so scores are deterministic
in tests. The REFERENCE_DATE should be passed to engine functions.
"""

from datetime import date

from ficosim.profile import (
    Account,
    AccountType,
    CreditProfile,
    PaymentRecord,
    PaymentStatus,
)

REFERENCE_DATE = date(2026, 6, 1)

DISCLAIMER = (
    "This is an educational estimate using a simplified model. "
    "It is not a real FICO score and is not affiliated with any credit bureau. "
    "Actual scores depend on proprietary algorithms and your full credit report."
)


def student_profile() -> CreditProfile:
    """Student: 1 credit card (low limit), 1 student loan, ~6 months history.

    Approximate score: ~656 (Fair).
    """
    return CreditProfile(
        accounts=[
            Account(
                account_type=AccountType.REVOLVING,
                balance=350,
                limit=1500,
                opened_date=date(2025, 12, 1),
            ),
            Account(
                account_type=AccountType.INSTALLMENT,
                balance=15000,
                limit=20000,
                opened_date=date(2025, 12, 1),
                monthly_payment=200,
            ),
        ],
        payment_history=[
            PaymentRecord(date(2026, 1, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2026, 2, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2026, 3, 1), PaymentStatus.LATE_30, 0),
            PaymentRecord(date(2026, 4, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2026, 5, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2026, 1, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2026, 2, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2026, 3, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2026, 4, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2026, 5, 1), PaymentStatus.ON_TIME, 1),
        ],
        hard_inquiries=[date(2025, 12, 1)],
    )


def young_professional_profile() -> CreditProfile:
    """Young Professional: 2 credit cards, 1 auto loan, ~3 years history.

    Approximate score: ~724 (Good).
    """
    return CreditProfile(
        accounts=[
            Account(
                account_type=AccountType.REVOLVING,
                balance=2200,
                limit=8000,
                opened_date=date(2023, 6, 1),
            ),
            Account(
                account_type=AccountType.REVOLVING,
                balance=1000,
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
        payment_history=[
            PaymentRecord(date(2024, 1, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2024, 4, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2024, 7, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2024, 10, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2025, 1, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2025, 4, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2025, 7, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2025, 10, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2026, 1, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2026, 4, 1), PaymentStatus.ON_TIME, 0),
            PaymentRecord(date(2024, 4, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2024, 7, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2024, 10, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2025, 1, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2025, 4, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2025, 7, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2025, 10, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2026, 1, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2026, 4, 1), PaymentStatus.ON_TIME, 1),
            PaymentRecord(date(2024, 1, 1), PaymentStatus.ON_TIME, 2),
            PaymentRecord(date(2024, 4, 1), PaymentStatus.ON_TIME, 2),
            PaymentRecord(date(2024, 7, 1), PaymentStatus.ON_TIME, 2),
            PaymentRecord(date(2024, 10, 1), PaymentStatus.ON_TIME, 2),
            PaymentRecord(date(2025, 1, 1), PaymentStatus.ON_TIME, 2),
            PaymentRecord(date(2025, 4, 1), PaymentStatus.ON_TIME, 2),
            PaymentRecord(date(2025, 7, 1), PaymentStatus.ON_TIME, 2),
            PaymentRecord(date(2025, 10, 1), PaymentStatus.ON_TIME, 2),
            PaymentRecord(date(2026, 1, 1), PaymentStatus.ON_TIME, 2),
            PaymentRecord(date(2026, 4, 1), PaymentStatus.ON_TIME, 2),
        ],
        hard_inquiries=[date(2024, 3, 1), date(2025, 9, 1)],
    )


def fresh_start_profile() -> CreditProfile:
    """Fresh Start: 1 secured credit card, no other accounts, ~2 months.

    Approximate score: ~585 (Fair, near the bottom).
    """
    return CreditProfile(
        accounts=[
            Account(
                account_type=AccountType.REVOLVING,
                balance=250,
                limit=300,
                opened_date=date(2026, 4, 1),
            ),
        ],
        payment_history=[
            PaymentRecord(date(2026, 5, 1), PaymentStatus.ON_TIME, 0),
        ],
        hard_inquiries=[date(2026, 4, 1)],
    )


def homeowner_profile() -> CreditProfile:
    """Homeowner: 1 credit card, 1 auto loan, 1 mortgage, ~8 years history.

    Approximate score: ~802 (Excellent).
    """
    payments = []
    # Monthly credit card payments for 5+ years (account 0)
    for year in range(2020, 2027):
        for month in range(1, 13):
            if date(year, month, 1) > date(2026, 5, 1):
                break
            payments.append(
                PaymentRecord(date(year, month, 1), PaymentStatus.ON_TIME, 0)
            )
    # Quarterly auto loan payments for 3 years (account 1)
    for year in range(2023, 2027):
        for month in (1, 4, 7, 10):
            if date(year, month, 1) > date(2026, 5, 1):
                break
            payments.append(
                PaymentRecord(date(year, month, 1), PaymentStatus.ON_TIME, 1)
            )
    # Monthly mortgage payments for 2 years (account 2)
    for year in range(2024, 2027):
        for month in range(1, 13):
            if date(year, month, 1) < date(2024, 7, 1):
                continue
            if date(year, month, 1) > date(2026, 5, 1):
                break
            payments.append(
                PaymentRecord(date(year, month, 1), PaymentStatus.ON_TIME, 2)
            )

    return CreditProfile(
        accounts=[
            Account(
                account_type=AccountType.REVOLVING,
                balance=1200,
                limit=15000,
                opened_date=date(2018, 6, 1),
            ),
            Account(
                account_type=AccountType.INSTALLMENT,
                balance=8000,
                limit=30000,
                opened_date=date(2023, 1, 1),
                monthly_payment=500,
            ),
            Account(
                account_type=AccountType.MORTGAGE,
                balance=280000,
                limit=320000,
                opened_date=date(2024, 6, 1),
                monthly_payment=1800,
            ),
        ],
        payment_history=payments,
        hard_inquiries=[],  # no recent inquiries
    )


STARTER_PROFILES = {
    "Student": student_profile,
    "Young Professional": young_professional_profile,
    "Fresh Start": fresh_start_profile,
    "Homeowner": homeowner_profile,
}
