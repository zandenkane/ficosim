# ficosim

![CI](https://github.com/zandenkane/ficosim/actions/workflows/ci.yml/badge.svg)

Interactive credit score simulator for the terminal. Pick a starter profile, apply financial actions (miss a payment, open a card, pay down debt, apply for a mortgage), and see exactly how each decision moves your score across all five FICO categories.

## Install

```bash
git clone https://github.com/zandenkane/ficosim.git
cd ficosim
pip install -e ".[dev]"
```


## example

```
$ ficosim

pick a starter profile:
  [1] clean slate (no history, age 18)
  [2] average american (680 score, 5yr history)
  [3] recovering (520 score, missed payments, collections)
> 2

current score: 680 (fair)

  payment history  [========      ] 65%
  amounts owed     [==========    ] 72%
  credit age       [======        ] 45%
  new credit       [============  ] 85%
  credit mix       [=======       ] 55%

pick an action:
  [1] miss a credit card payment
  [2] pay off a credit card balance
  [3] open a new credit card
  [4] apply for a mortgage
  [5] max out a credit card
> 1

score: 680 -> 642 (-38 points)
payment history dropped from 65% to 48%
note: a single missed payment stays on your report for 7 years
```

## Usage

```bash
ficosim
```

Or run as a module:

```bash
python -m ficosim
```

The simulator walks you through:

1. **Pick a starter profile** (Student, Young Professional, Fresh Start, or Homeowner)
2. **See your score** with a full category breakdown
3. **Choose an action** from the menu
4. **See before/after** comparison with point delta and category changes
5. **Repeat** or reset with a different profile

## Starter Profiles

| Profile            | Score | Description                                          |
|--------------------|-------|------------------------------------------------------|
| Student            | ~656  | 1 credit card, 1 student loan, 6 months history     |
| Young Professional | ~724  | 2 credit cards, 1 auto loan, 3 years history        |
| Fresh Start        | ~585  | 1 secured card, 2 months history                    |
| Homeowner          | ~802  | 1 credit card, 1 auto loan, 1 mortgage, 8 yr history|

## Available Actions

- **Miss a payment** (30, 60, or 90 days late)
- **Open a new credit card** (specify credit limit)
- **Max out a credit card** (balance set to limit)
- **Pay down a balance** (reduce balance on any account)
- **Close an account** (marks account closed, removes limit)
- **Make a large purchase** (increase balance on a card)
- **Apply for a mortgage** (adds mortgage account and hard inquiry)
- **Transfer a balance** (move debt between two credit cards)

## How Scoring Works

The engine scores five FICO categories independently on a 0.0 to 1.0 scale, then combines them with official FICO weights and maps to the 300 to 850 range:

| Category           | Weight | What it measures                            |
|--------------------|--------|---------------------------------------------|
| Payment History    | 35%    | On-time payment ratio, recency of late pays |
| Amounts Owed       | 30%    | Credit utilization (balance / limit)         |
| Length of History   | 15%    | Average account age in months               |
| New Credit         | 10%    | Hard inquiries in the last 12 months        |
| Credit Mix         | 10%    | Variety of account types                    |

Final score = `300 + 550 * (weighted sum of category scores)`.

Score bands: Poor (300 to 579), Fair (580 to 669), Good (670 to 739), Very Good (740 to 799), Excellent (800 to 850).

## Project Structure

```
ficosim/
  __init__.py       # Package version
  __main__.py       # python -m ficosim entry point
  profile.py        # CreditProfile, Account, PaymentRecord dataclasses
  engine.py         # Five-category scoring engine
  constants.py      # Starter profiles and reference date
  scenarios.py      # Eight what-if scenario functions
  ui.py             # Rich output rendering
  cli.py            # Questionary interactive loop
tests/
  test_profile.py   # Computed property tests
  test_engine.py    # Score computation tests
  test_scenarios.py # Scenario mutation tests
  test_ui.py        # Rendering output tests
  test_cli.py       # CLI helper tests
```

## Tests

```bash
pytest
```

134 tests covering the engine, profile computed properties, all eight scenarios, UI rendering, and CLI helpers. The engine, profile, and scenario modules are pure Python with no I/O, making them fully deterministic and testable with fixed reference dates.

## Disclaimer

This is an educational estimate using a simplified model. It is not a real FICO score and is not affiliated with any credit bureau. Actual scores depend on proprietary algorithms and your full credit report.

## License

MIT
