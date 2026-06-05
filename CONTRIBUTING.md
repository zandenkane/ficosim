# contributing

`pip install -e .[dev]` and `pytest` to get going.

The scoring engine is in ficosim/engine.py. If you want to add new financial scenarios, add them to ficosim/scenarios.py. Each scenario is a function that modifies a profile and returns the score delta.
