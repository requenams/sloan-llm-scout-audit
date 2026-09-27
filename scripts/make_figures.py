"""
Abstract figures, built from the CSV files written by analyze_audit.py.

  Figure 1: change in estimated market value (%) when a nationality or league
            label is added to an identical profile, per model.
  Figure 2: (a) consistency across repeats, (b) recommendation and value
            instability, (c) league label versus real performance.

Usage:
  python scripts/make_figures.py --results results
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

MODEL_LABELS = {"claude": "Claude Sonnet 4.5", "gpt": "GPT-5", "gemini": "Gemini 2.5 Pro", "deepseek": "DeepSeek V3.1"}
MODEL_ORDER = ["claude", "gpt", "gemini", "deepseek"]
NAVY, RUST, GREY = "#1f3a5f", "#c05621", "#8a8f98"

plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "axes.spines.top": False, "axes.spines.right": False})


def order_models(df: pd.DataFrame) -> list:
    present = list(df["model"].unique())
    return [m for m in MODEL_ORDER if m in present] + [m for m in present if m not in MODEL_ORDER]


def fig1_value_bias(res: pd.DataFrame, out: Path) -> None:
    models = order_models(res)
    factors = [("nationality", "Nationality label"), ("league", "League label")]
    fig, axes = plt.subplots(2, len(models), figsize=(max(8, 2.9 * len(models)), 5.6), squeeze=False)
    for i, (factor, title) in enumerate(factors):
        sub = res[res["factor"] == factor]
        # Order labels by their mean effect across models
        levels = sub.groupby("level")["d_value_pct"].mean().sort_values().index.tolist()
        xmax = float(np.ceil(sub["d_value_pct_hi"].max() / 25) * 25) + (60 if factor == "league" else 12)
        xmin = -135.0 if factor == "league" else float(np.floor(sub["d_value_pct_lo"].min() / 10) * 10) - 14
        for j, model in enumerate(models):
            ax = axes[i][j]
            g = sub[sub["model"] == model].set_index("level").reindex(levels)
            y = np.arange(len(levels))
            colors = [RUST if v < 0 else NAVY for v in g["d_value_pct"]]
            ax.barh(y, g["d_value_pct"], color=colors, alpha=0.9, height=0.62)
            ax.errorbar(g["d_value_pct"], y, xerr=[g["d_value_pct"] - g["d_value_pct_lo"], g["d_value_pct_hi"] - g["d_value_pct"]],
                        fmt="none", ecolor="black", elinewidth=0.8, capsize=2)
            ax.axvline(0, color="black", lw=0.8)
            ax.set_yticks(y)
            ax.set_yticklabels(levels if j == 0 else [])
            ax.set_xlim(xmin, xmax)
            ax.grid(axis="x", alpha=0.3)
            if i == 0:
                ax.set_title(MODEL_LABELS.get(model, model))
            if j == 0:
                ax.set_ylabel(title, fontweight="bold")
            for yy, v, lo, hi in zip(y, g["d_value_pct"], g["d_value_pct_lo"], g["d_value_pct_hi"]):
                pad = (xmax - xmin) * 0.015
                if v >= 0:
                    ax.text(hi + pad, yy, f"{v:+.0f}%", va="center", ha="left", fontsize=7.5)
                else:
                    ax.text(lo - pad, yy, f"{v:+.0f}%", va="center", ha="right", fontsize=7.5)
    fig.suptitle("Same statistics, different label: change in LLM-estimated market value (mean, 95% bootstrap CI, 147 profiles)", fontsize=10.5)
    fig.supxlabel("Δ estimated market value vs. the same profile with no label (%)", fontsize=9)
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    fig.savefig(out, dpi=220)
    plt.close(fig)


def fig2_consistency_and_label_vs_performance(cons: pd.DataFrame, lvp: pd.DataFrame, out: Path) -> None:
    models = order_models(cons)
    cons = cons.set_index("model").reindex(models)
    lvp = lvp.set_index("model").reindex(models)
    names = [MODEL_LABELS.get(m, m).replace(" ", "\n", 1) for m in models]
    x = np.arange(len(models))

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6))

    ax = axes[0]
    ax.bar(x, cons["icc_rating"], color=NAVY, width=0.6)
    ax.set_ylim(0, 1.05)
    ax.set_title("(a) Rating consistency\nICC across 5 identical runs (1 = perfectly stable)")
    for xi, v in zip(x, cons["icc_rating"]):
        ax.text(xi, v + 0.02, f"{v:.2f}", ha="center", fontsize=8)

    ax = axes[1]
    w = 0.36
    unstable = 100 * (1 - cons["recommendation_stable_share"])
    ax.bar(x - w / 2, unstable, width=w, color=RUST, label="Profiles whose recommendation\nchanges across runs (%)")
    ax2 = ax.twinx()
    ax2.bar(x + w / 2, cons["value_ratio_max_min_median"], width=w, color=GREY, label="Median max/min market value\nfor the same profile (×)")
    ax2.set_ylim(0, max(2.2, cons["value_ratio_max_min_median"].max() * 1.15))
    ax2.axhline(1, color="black", lw=0.6, ls="--")
    ax2.spines["right"].set_visible(True)
    ax.set_ylim(0, max(50, unstable.max() * 1.2))
    ax.set_ylabel("% of profiles")
    ax.set_title("(b) Same profile, five runs:\nrecommendation and value instability")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="upper left", frameon=False)
    for xi, v in zip(x, unstable):
        ax.text(xi - w / 2, v + 1, f"{v:.0f}%", ha="center", fontsize=7.5)
    for xi, v in zip(x, cons["value_ratio_max_min_median"]):
        ax2.text(xi + w / 2, v + 0.04, f"{v:.2f}×", ha="center", fontsize=7.5)

    ax = axes[2]
    perf = 1 + lvp["perf_low_to_high_value_pct"] / 100
    label = 1 + lvp["label_value_spread_pct"] / 100
    ax.bar(x - w / 2, perf, width=w, color=NAVY, label="Bottom → top performance tercile\n(no label)")
    ax.bar(x + w / 2, label, width=w, color=RUST, label="\"Segunda División\" → \"Premier League\"\n(identical statistics)")
    ax.axhline(1, color="black", lw=0.6)
    ax.set_ylabel("Market value multiplier (×)")
    ax.set_title("(c) What moves the price more:\nthe numbers or the league label?")
    ax.legend(fontsize=7, loc="upper right", frameon=False)
    ax.set_ylim(0, max(perf.max(), label.max()) * 1.4)
    for xi, v in zip(x, perf):
        ax.text(xi - w / 2, v + 0.1, f"{v:.1f}×", ha="center", fontsize=7.5)
    for xi, v in zip(x, label):
        ax.text(xi + w / 2, v + 0.1, f"{v:.1f}×", ha="center", fontsize=7.5)

    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(names, fontsize=8)
        ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    args = parser.parse_args()
    r = Path(args.results)
    res = pd.read_csv(r / "bias_by_level.csv")
    cons = pd.read_csv(r / "consistency.csv")
    lvp = pd.read_csv(r / "label_vs_performance.csv")
    fig1_value_bias(res, r / "fig1_value_bias.png")
    fig2_consistency_and_label_vs_performance(cons, lvp, r / "fig2_consistency_label_vs_performance.png")
    print(f"Figures written to {r}/fig1_value_bias.png and {r}/fig2_consistency_label_vs_performance.png")


if __name__ == "__main__":
    main()
