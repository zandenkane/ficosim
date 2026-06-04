"""Tests for the UI rendering module.

Captures rich console output to a StringIO buffer and verifies
that the expected text appears in score displays and comparisons.
"""

from io import StringIO

from rich.console import Console

from ficosim.constants import REFERENCE_DATE, student_profile
from ficosim.engine import compute_score_breakdown
from ficosim.scenarios import miss_payment, pay_down_balance
from ficosim.ui import _bar, _score_color, render_comparison, render_score, render_welcome

REF = REFERENCE_DATE


def _capture(render_fn, *args):
    """Call a render function and return its captured text output."""
    buf = StringIO()
    import ficosim.ui as ui_mod

    original = ui_mod.console
    ui_mod.console = Console(file=buf, width=120, force_terminal=True)
    try:
        render_fn(*args)
    finally:
        ui_mod.console = original
    return buf.getvalue()


class TestScoreColor:
    def test_excellent(self):
        assert _score_color(850) == "bold green"
        assert _score_color(800) == "bold green"

    def test_very_good(self):
        assert _score_color(740) == "green"
        assert _score_color(799) == "green"

    def test_good(self):
        assert _score_color(670) == "yellow"

    def test_fair(self):
        assert _score_color(580) == "dark_orange"

    def test_poor(self):
        assert _score_color(300) == "bold red"
        assert _score_color(579) == "bold red"


class TestBar:
    def test_full_bar(self):
        result = _bar(1.0, 10)
        assert len(result) == 10

    def test_empty_bar(self):
        result = _bar(0.0, 10)
        assert len(result) == 10

    def test_half_bar(self):
        result = _bar(0.5, 10)
        assert len(result) == 10

    def test_default_width(self):
        result = _bar(0.5)
        assert len(result) == 20


class TestRenderScore:
    def test_contains_score_value(self):
        profile = student_profile()
        breakdown = compute_score_breakdown(profile, REF)
        output = _capture(render_score, breakdown)
        score_str = str(breakdown["score"])
        assert score_str in output

    def test_contains_band_label(self):
        profile = student_profile()
        breakdown = compute_score_breakdown(profile, REF)
        output = _capture(render_score, breakdown)
        assert breakdown["band"] in output

    def test_contains_category_names(self):
        profile = student_profile()
        breakdown = compute_score_breakdown(profile, REF)
        output = _capture(render_score, breakdown)
        assert "Payment History" in output
        assert "Amounts Owed" in output
        assert "Length of History" in output
        assert "New Credit" in output
        assert "Credit Mix" in output

    def test_contains_disclaimer(self):
        profile = student_profile()
        breakdown = compute_score_breakdown(profile, REF)
        output = _capture(render_score, breakdown)
        # Check that at least part of the disclaimer appears
        assert "educational" in output.lower()


class TestRenderComparison:
    def test_shows_before_and_after(self):
        profile = student_profile()
        before = compute_score_breakdown(profile, REF)
        new_profile, explanation = miss_payment(profile, 0, "90", payment_date=REF)
        after = compute_score_breakdown(new_profile, REF)
        output = _capture(render_comparison, before, after, explanation)
        assert "Before" in output
        assert "After" in output

    def test_shows_explanation(self):
        profile = student_profile()
        before = compute_score_breakdown(profile, REF)
        new_profile, explanation = pay_down_balance(profile, 0, 200)
        after = compute_score_breakdown(new_profile, REF)
        output = _capture(render_comparison, before, after, explanation)
        assert "What Happened" in output

    def test_shows_score_change(self):
        profile = student_profile()
        before = compute_score_breakdown(profile, REF)
        new_profile, explanation = miss_payment(profile, 0, "90", payment_date=REF)
        after = compute_score_breakdown(new_profile, REF)
        output = _capture(render_comparison, before, after, explanation)
        assert "Change" in output
        assert "points" in output


class TestRenderWelcome:
    def test_contains_title(self):
        output = _capture(render_welcome)
        assert "Credit Score Simulator" in output

    def test_contains_instructions(self):
        output = _capture(render_welcome)
        assert "starter profile" in output.lower()
