"""Project matplotlib style. Call use() once per notebook or script.

Semantic colors keep the observed / modelled / forecast distinction visible
in every figure, matching the site rule that the three are never presented
interchangeably.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

OBSERVED = "#1a659e"
MODELLED = "#7d8597"
FORECAST = "#e07a1f"
ACCENT = "#2a9d8f"
ALERT = "#c1121f"

RC = {
    "figure.figsize": (11, 5),
    "figure.dpi": 110,
    "figure.facecolor": "white",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.prop_cycle": plt.cycler(color=[OBSERVED, FORECAST, ACCENT, MODELLED, ALERT]),
    "legend.frameon": False,
    "font.family": "sans-serif",
    "date.autoformatter.day": "%b %d",
    "date.autoformatter.hour": "%b %d %H:%M",
}


def use() -> None:
    plt.rcParams.update(RC)  # type: ignore[arg-type]


def source_note(ax, text: str) -> None:
    """Attribution line under a figure, e.g. 'Data: SKSM METAR via NOAA'."""
    ax.annotate(
        text,
        xy=(0, -0.18),
        xycoords="axes fraction",
        fontsize=8,
        color="#666666",
    )
