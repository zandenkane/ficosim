"""Rich-based UI rendering for score displays and comparisons.

All terminal output goes through this module. The engine and profile
modules have zero I/O dependencies.
"""

from __future__ import annotations

from typing import Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ficosim.constants import DISCLAIMER

console = Console()


def _score_color(score: int) -> str:
    if score >= 800:
        return "bold green"
    elif score >= 740:
        return "green"
    elif score >= 670:
        return "yellow"
    elif score >= 580:
        return "dark_orange"
    else:
        return "bold red"


def _bar(value: float, width: int = 20) -> str:
    filled = round(value * width)
    return "█" * filled + "░" * (width - filled)


def render_score(
    breakdown: Dict[str, object],
) -> None:
    """Display the current score with category breakdown."""
    score = breakdown["score"]
    band = breakdown["band"]
    color = _score_color(score)

    # Score panel
    score_text = Text(f"  {score}  ", style=color)
    score_text.append(f"  {band}", style="bold")
    panel = Panel(
        score_text,
        title="Credit Score",
        border_style=color,
        padding=(1, 4),
    )
    console.print(panel)

    # Category breakdown table
    table = Table(title="Score Breakdown", show_header=True, header_style="bold")
    table.add_column("Category", style="cyan", min_width=22)
    table.add_column("Weight", justify="center", min_width=8)
    table.add_column("Sub-Score", min_width=24)
    table.add_column("Note", min_width=30)

    category_labels = {
        "payment_history": "Payment History",
        "amounts_owed": "Amounts Owed",
        "length_of_history": "Length of History",
        "new_credit": "New Credit",
        "credit_mix": "Credit Mix",
    }

    categories = breakdown["categories"]
    for cat_key, label in category_labels.items():
        info = categories[cat_key]
        weight_pct = f"{info['weight'] * 100:.0f}%"
        sub = info["sub_score"]
        bar = _bar(sub)
        sub_display = f"{bar} {sub:.0%}"
        table.add_row(label, weight_pct, sub_display, info["note"])

    console.print(table)

    # Disclaimer
    console.print()
    console.print(
        Panel(DISCLAIMER, title="Disclaimer", border_style="dim", padding=(0, 2))
    )


def render_comparison(
    before_breakdown: Dict[str, object],
    after_breakdown: Dict[str, object],
    explanation: str,
) -> None:
    """Display before/after score comparison with category-level changes."""
    before_score = before_breakdown["score"]
    after_score = after_breakdown["score"]
    delta = after_score - before_score

    # Delta display
    if delta > 0:
        delta_str = f"+{delta}"
        delta_color = "green"
    elif delta < 0:
        delta_str = str(delta)
        delta_color = "red"
    else:
        delta_str = "0"
        delta_color = "yellow"

    # Side by side scores
    before_color = _score_color(before_score)
    after_color = _score_color(after_score)

    comparison = Text()
    comparison.append("Before: ", style="bold")
    comparison.append(f"{before_score} ({before_breakdown['band']})", style=before_color)
    comparison.append("    ")
    comparison.append("After: ", style="bold")
    comparison.append(f"{after_score} ({after_breakdown['band']})", style=after_color)
    comparison.append("    ")
    comparison.append("Change: ", style="bold")
    comparison.append(f"{delta_str} points", style=delta_color)

    console.print()
    console.print(Panel(comparison, title="Score Impact", border_style=delta_color))

    # Category changes table
    table = Table(title="Category Changes", show_header=True, header_style="bold")
    table.add_column("Category", style="cyan", min_width=22)
    table.add_column("Before", justify="center", min_width=10)
    table.add_column("After", justify="center", min_width=10)
    table.add_column("Change", justify="center", min_width=10)

    category_labels = {
        "payment_history": "Payment History",
        "amounts_owed": "Amounts Owed",
        "length_of_history": "Length of History",
        "new_credit": "New Credit",
        "credit_mix": "Credit Mix",
    }

    before_cats = before_breakdown["categories"]
    after_cats = after_breakdown["categories"]

    for cat_key, label in category_labels.items():
        b_val = before_cats[cat_key]["sub_score"]
        a_val = after_cats[cat_key]["sub_score"]
        cat_delta = a_val - b_val

        if abs(cat_delta) < 0.001:
            change_str = "-"
            change_style = "dim"
        elif cat_delta > 0:
            change_str = f"+{cat_delta:.0%}"
            change_style = "green"
        else:
            change_str = f"{cat_delta:.0%}"
            change_style = "red"

        table.add_row(
            label,
            f"{b_val:.0%}",
            f"{a_val:.0%}",
            Text(change_str, style=change_style),
        )

    console.print(table)

    # Explanation
    console.print()
    console.print(Panel(explanation, title="What Happened", border_style="blue"))

    # Disclaimer
    console.print()
    console.print(
        Panel(DISCLAIMER, title="Disclaimer", border_style="dim", padding=(0, 2))
    )


def render_welcome() -> None:
    """Display the welcome banner."""
    console.print()
    console.print(
        Panel(
            "[bold]Credit Score Simulator[/bold]\n\n"
            "Explore how financial decisions affect your credit score.\n"
            "Pick a starter profile, then try different actions to see their impact.",
            title="Welcome",
            border_style="blue",
            padding=(1, 4),
        )
    )
    console.print()
