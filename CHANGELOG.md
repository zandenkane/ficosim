# Changelog

All notable changes to ficosim are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-28

### Added
- Five-category FICO-aligned scoring engine: payment history (35%), amounts
  owed (30%), length of credit history (15%), new credit (10%), credit mix (10%).
- Eight what-if scenarios: miss a payment, open a new credit card, max out a card,
  pay down a balance, close an account, make a large purchase, apply for a mortgage,
  transfer a balance.
- Four starter profiles: Student (~656), Young Professional (~724),
  Fresh Start (~585), Homeowner (~802).
- Interactive CLI with questionary menus and rich terminal output.
- Before/after score comparison with category-level change breakdown.
- Plain-language explanations after every action.
- Educational disclaimer on every score display.
- `python -m ficosim` module entry point.
- 134 tests covering the engine, profile computed properties, all scenarios,
  UI rendering, and CLI helpers.
- CI pipeline with GitHub Actions.
