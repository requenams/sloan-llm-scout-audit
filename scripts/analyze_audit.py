"""
Audit analysis: consistency, label bias and numerical faithfulness of the LLMs.

Input:  data/audit/responses.jsonl, data/audit/profiles.json
Output: results/*.csv, results/summary.md, results/grounding_examples.md,
        results/fig1_bias.png, results/fig2_consistency_grounding.png (diagnostic figures;
        the abstract figures are produced by make_figures.py)

Usage:
  python scripts/analyze_audit.py
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RNG = np.random.default_rng(2027)
N_BOOT = 2000


# ----------------------------------------------------------------------------- loading
def load(responses_path: Path, profiles_path: Path):
    rows = []
    with responses_path.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            p = r.get("parsed") or {}
            if not p or r.get("error"):
                continue
            try:
                rating = float(p.get("overall_rating"))
                value = float(p.get("estimated_market_value_m_eur"))
            except (TypeError, ValueError):
                continue
            rows.append({
                "model": r["model"], "profile_id": r["profile_id"], "pos_group": r["pos_group"],
                "condition": r["condition"], "factor": r["factor"], "level": r["level"], "repeat": r["repeat"],
                "rating": rating, "value": value,
                "ready": 1.0 if str(p.get("top_league_ready", "")).lower().startswith("y") else 0.0,
                "sign": 1.0 if str(p.get("recommendation", "")).lower() == "sign" else 0.0,
                "recommendation": str(p.get("recommendation", "")).lower(),
                "justification": str(p.get("justification", "")),
            })
    df = pd.DataFrame(rows)
    # The bias analysis uses one value per cell: baseline repeats are averaged per profile and model
    profiles = {p["profile_id"]: p for p in json.loads(profiles_path.read_text(encoding="utf-8"))}
    return df, profiles


def boot_ci(x: np.ndarray, stat=np.mean):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return np.nan, np.nan
    idx = RNG.integers(0, len(x), size=(N_BOOT, len(x)))
    return tuple(np.percentile(stat(x[idx], axis=1), [2.5, 97.5]))


# ----------------------------------------------------------------------------- consistency
def icc1(values_by_group: list[np.ndarray]) -> float:
    """ICC(1), one-way random effects: share of rating variance explained by the
    profile rather than by the repeat."""
    groups = [np.asarray(g, dtype=float) for g in values_by_group if len(g) > 1]
    k = np.mean([len(g) for g in groups])
    grand = np.mean(np.concatenate(groups))
    msb = sum(len(g) * (g.mean() - grand) ** 2 for g in groups) / (len(groups) - 1)
    msw = sum(((g - g.mean()) ** 2).sum() for g in groups) / sum(len(g) - 1 for g in groups)
    return (msb - msw) / (msb + (k - 1) * msw)


def consistency(df: pd.DataFrame) -> pd.DataFrame:
    base = df[df["condition"] == "baseline"]
    out = []
    for model, g in base.groupby("model"):
        per = g.groupby("profile_id")
        rating_groups = [x["rating"].values for _, x in per]
        rng_rating = per["rating"].agg(lambda s: s.max() - s.min())
        cv_value = per["value"].agg(lambda s: s.std(ddof=0) / s.mean() if s.mean() > 0 else np.nan)
        same_rec = per["recommendation"].agg(lambda s: s.nunique() == 1)
        out.append({
            "model": model, "profiles": per.ngroups, "repeats_mean": per.size().mean(),
            "icc_rating": icc1(rating_groups),
            "rating_within_sd": per["rating"].std(ddof=0).mean(),
            "share_rating_range_ge2": (rng_rating >= 2).mean(),
            "value_cv_mean": cv_value.mean(),
            "value_ratio_max_min_median": per["value"].agg(lambda s: s.max() / s.min() if s.min() > 0 else np.nan).median(),
            "recommendation_stable_share": same_rec.mean(),
        })
    return pd.DataFrame(out)


# ----------------------------------------------------------------------------- label effects
def bias(df: pd.DataFrame) -> pd.DataFrame:
    """Paired difference of every condition against the baseline of the same profile and model."""
    base = (df[df["condition"] == "baseline"].groupby(["model", "profile_id"])
            .agg(b_rating=("rating", "mean"), b_value=("value", "mean"), b_ready=("ready", "mean"), b_sign=("sign", "mean")).reset_index())
    cond = df[df["condition"] != "baseline"].merge(base, on=["model", "profile_id"])
    cond["d_rating"] = cond["rating"] - cond["b_rating"]
    cond["d_logvalue"] = np.log(cond["value"].clip(lower=0.1)) - np.log(cond["b_value"].clip(lower=0.1))
    cond["d_ready"] = cond["ready"] - cond["b_ready"]
    cond["d_sign"] = cond["sign"] - cond["b_sign"]

    out = []
    for (model, factor, level), g in cond.groupby(["model", "factor", "level"]):
        lo, hi = boot_ci(g["d_rating"].values)
        vlo, vhi = boot_ci(g["d_logvalue"].values)
        t = stats.ttest_1samp(g["d_rating"], 0.0, nan_policy="omit")
        out.append({
            "model": model, "factor": factor, "level": level, "n": len(g),
            "d_rating": g["d_rating"].mean(), "d_rating_lo": lo, "d_rating_hi": hi, "p_rating": t.pvalue,
            "d_value_pct": 100 * (np.exp(g["d_logvalue"].mean()) - 1),
            "d_value_pct_lo": 100 * (np.exp(vlo) - 1), "d_value_pct_hi": 100 * (np.exp(vhi) - 1),
            "d_ready_pp": 100 * g["d_ready"].mean(), "d_sign_pp": 100 * g["d_sign"].mean(),
        })
    res = pd.DataFrame(out)

    # Global test per factor: do the levels differ from each other? (Friedman across profiles)
    tests = []
    for (model, factor), g in cond.groupby(["model", "factor"]):
        wide = g.pivot_table(index="profile_id", columns="level", values="rating", aggfunc="mean").dropna()
        if wide.shape[1] >= 2 and len(wide) >= 5:
            fr = stats.friedmanchisquare(*[wide[c].values for c in wide.columns])
            wide_v = g.pivot_table(index="profile_id", columns="level", values="value", aggfunc="mean").dropna()
            frv = stats.friedmanchisquare(*[np.log(wide_v[c].clip(lower=0.1)).values for c in wide_v.columns])
            tests.append({"model": model, "factor": factor, "n_profiles": len(wide),
                          "friedman_rating_p": fr.pvalue, "friedman_value_p": frv.pvalue,
                          "rating_spread_between_levels": wide.mean().max() - wide.mean().min(),
                          "value_ratio_between_levels": np.exp(np.log(wide_v.clip(lower=0.1)).mean().max() - np.log(wide_v.clip(lower=0.1)).mean().min())})
    return res, pd.DataFrame(tests), cond


def mixed_models(cond: pd.DataFrame) -> pd.DataFrame:
    """Mixed-effects model rating ~ level with a profile random effect (if statsmodels is available)."""
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        return pd.DataFrame()
    out = []
    for (model, factor), g in cond.groupby(["model", "factor"]):
        g = g.copy()
        g["level_c"] = pd.Categorical(g["level"])
        try:
            m = smf.mixedlm("rating ~ C(level_c)", g, groups=g["profile_id"]).fit(reml=False)
            for name, coef in m.params.items():
                if name.startswith("C(level_c)"):
                    lvl = name.split("[T.")[1].rstrip("]")
                    out.append({"model": model, "factor": factor, "level_vs_reference": lvl,
                                "reference": g["level_c"].cat.categories[0], "coef": coef, "p": m.pvalues[name]})
        except Exception as exc:  # noqa: BLE001
            out.append({"model": model, "factor": factor, "level_vs_reference": "ERROR", "coef": np.nan, "p": np.nan, "reference": repr(exc)})
    return pd.DataFrame(out)


# ----------------------------------------------------------------------------- numerical faithfulness
NUM_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?:st|nd|rd|th)?(%)?")
THOUSANDS_RE = re.compile(r"(\d),(\d{3})\b")
# Digit-bearing fragments that are not numerical claims about the profile. They are
# removed before extracting numbers; order matters ("/90" first).
IGNORE_PATTERNS = [
    r"(?:per|/)\s*90\b|\bp90\b",                                        # 2.21 dribbles/90, per 90
    r"\b\d+\s*-?\s*(?:v|on)\s*-?\s*\d+s?\b",                              # 1v1, 1v1s, 1-on-1, 1-v-1
    r"\b\d+(?:st|nd|rd|th)?\s*[-–]\s*\d+(?:st|nd|rd|th)?\b",              # ranges: 16–24th, 20th-40th
    r"\b(?:below|bottom|under|top|above|over|near|nearly|around|about|roughly|within|almost|approximately|circa|under)"
    r"\s+(?:the\s+)?\d+(?:\.\d+)?(?:st|nd|rd|th)?\s*(?:%|percent|percentile)?\b",  # approximate thresholds
    r"[<>~≈]\s*\d+(?:\.\d+)?|\b\d+(?:\.\d+)?\s*\+(?!\s*\d)",              # >90%, ~10th, 3000+
    r"(?<![\d.])\b\d+\s*/\s*\d+\b",                                     # 6/8, 7/10 (not preceded by a digit)
    r"\b(?:a|an|the|as|number|no\.?|deep-lying|box-to-box|classic|traditional|modern|false|starting|holding|advanced|creative|attacking|central)\s+(?:6|8|9|10)s?\b",  # positional jargon
    r"\b(?:1-10|out of 10|top[-\s]?(?:five|\d+)|u-?\d{2}|\d+-year-old)\b",
    r"\d+(?:\.\d+)?\s*(?:m\b|million|k\b|€|eur\b)|[€$£]\s*\d+(?:\.\d+)?",  # money
]
IGNORE_RE = [re.compile(pat, re.I) for pat in IGNORE_PATTERNS]


def clean_for_extraction(text: str) -> str:
    text = THOUSANDS_RE.sub(r"\1\2", text)
    for rx in IGNORE_RE:
        text = rx.sub(" ", text)
    return text


def supported_numbers(profile: dict) -> tuple[set, list]:
    pcts = {float(m["percentile"]) for m in profile["metrics"]}
    vals = [float(m["value"]) for m in profile["metrics"]]
    pcts |= {float(profile["minutes"]), float(profile["matches"]), 24.0}
    return pcts, vals


def grounding(df: pd.DataFrame, profiles: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for _, r in df.iterrows():
        prof = profiles[r["profile_id"]]
        exact, vals = supported_numbers(prof)
        text = clean_for_extraction(r["justification"])
        claims = [float(m.group(1)) for m in NUM_RE.finditer(text)]
        n_ok, bad = 0, []
        for c in claims:
            ok = (c in exact) or any(abs(c - v) <= 0.011 or (v > 0 and abs(c - v) / v <= 0.015) for v in vals)
            n_ok += ok
            if not ok:
                bad.append(c)
        rows.append({"model": r["model"], "profile_id": r["profile_id"], "condition": r["condition"],
                     "n_claims": n_ok + len(bad), "n_unsupported": len(bad), "any_unsupported": len(bad) > 0,
                     "unsupported_numbers": " ".join(f"{b:g}" for b in bad), "justification": r["justification"]})
    g = pd.DataFrame(rows)
    summ = g.groupby("model").agg(
        responses=("n_claims", "size"), claims_per_response=("n_claims", "mean"),
        unsupported_claim_rate=("n_unsupported", lambda s: s.sum() / max(1, g.loc[s.index, "n_claims"].sum())),
        share_responses_with_unsupported=("any_unsupported", "mean"),
    ).reset_index()
    return summ, g


def grounding_examples(gr_detail: pd.DataFrame, profiles: dict, out: Path, per_model: int = 8) -> None:
    """Readable examples to check by hand whether flagged numbers are fabricated or merely derived."""
    lines = ["# Examples of unsupported numbers (check by hand)\n"]
    flagged = gr_detail[gr_detail["n_unsupported"] > 0]
    for model, g in flagged.groupby("model"):
        lines.append(f"\n## {model}  ({len(g)} flagged responses out of {int((gr_detail['model'] == model).sum())})\n")
        for _, r in g.sort_values("n_unsupported", ascending=False).head(per_model).iterrows():
            prof = profiles[r["profile_id"]]
            table = "; ".join(f"{m['name']}={m['value']} (p{m['percentile']})" for m in prof["metrics"])
            lines.append(f"**{r['profile_id']} / {r['condition']}** — flagged numbers: `{r['unsupported_numbers']}`\n")
            lines.append(f"> {r['justification']}\n")
            lines.append(f"Profile ({prof['position']}, {prof['minutes']} min, {prof['matches']} matches): {table}\n")
    out.write_text("\n".join(lines), encoding="utf-8")


def label_vs_performance(df: pd.DataFrame, res: pd.DataFrame, key_path: Path) -> pd.DataFrame:
    """Compare the label effect with the effect of real performance: difference in
    rating and value (baseline) between the top and bottom terciles, per model."""
    if not key_path.exists():
        return pd.DataFrame()
    key = pd.read_csv(key_path)[["profile_id", "tercile"]]
    base = df[df["condition"] == "baseline"].merge(key, on="profile_id")
    out = []
    for model, g in base.groupby("model"):
        t = g.groupby("tercile").agg(rating=("rating", "mean"), logvalue=("value", lambda s: np.log(s.clip(lower=0.1)).mean()))
        if not {"low", "high"} <= set(t.index):
            continue
        perf_rating = t.loc["high", "rating"] - t.loc["low", "rating"]
        perf_value_pct = 100 * (np.exp(t.loc["high", "logvalue"] - t.loc["low", "logvalue"]) - 1)
        r = res[res["model"] == model]
        best = r.loc[r["d_value_pct"].idxmax()]
        worst = r.loc[r["d_value_pct"].idxmin()]
        out.append({"model": model,
                    "perf_low_to_high_rating": perf_rating, "perf_low_to_high_value_pct": perf_value_pct,
                    "label_max_rating": r["d_rating"].max(), "label_max_level": r.loc[r["d_rating"].idxmax(), "level"],
                    "label_value_spread_pct": 100 * ((1 + best["d_value_pct"] / 100) / (1 + worst["d_value_pct"] / 100) - 1),
                    "label_value_best": best["level"], "label_value_worst": worst["level"]})
    return pd.DataFrame(out)


# ----------------------------------------------------------------------------- figures
def fig_bias(res: pd.DataFrame, out: Path):
    models = sorted(res["model"].unique())
    factors = [("nationality", "Nationality label"), ("league", "League label")]
    fig, axes = plt.subplots(len(factors), len(models), figsize=(max(7.5, 3.2 * len(models)), 3.1 * len(factors)), sharey="row", squeeze=False)
    for i, (factor, title) in enumerate(factors):
        levels = sorted(res[res["factor"] == factor]["level"].unique())
        for j, model in enumerate(models):
            ax = axes[i][j]
            g = res[(res["factor"] == factor) & (res["model"] == model)].set_index("level").reindex(levels)
            y = np.arange(len(levels))
            ax.errorbar(g["d_rating"], y, xerr=[g["d_rating"] - g["d_rating_lo"], g["d_rating_hi"] - g["d_rating"]],
                        fmt="o", color="#1f3a5f", ecolor="#8aa1bf", capsize=3)
            ax.axvline(0, color="grey", lw=0.8, ls="--")
            ax.set_yticks(y)
            ax.set_yticklabels(levels if j == 0 else [])
            ax.set_title(model if i == 0 else "", fontsize=11)
            ax.grid(axis="x", alpha=0.3)
            if i == len(factors) - 1:
                ax.set_xlabel("Δ rating vs. no label (1-10)")
            if j == 0:
                ax.set_ylabel(title, fontsize=10)
    fig.suptitle("Same statistics, different label: change in LLM rating (mean, 95% CI)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out, dpi=200)
    plt.close(fig)


def fig_consistency_grounding(cons: pd.DataFrame, gr: pd.DataFrame, out: Path):
    models = list(cons["model"])
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    x = np.arange(len(models))
    axes[0].bar(x, cons["icc_rating"], color="#1f3a5f")
    axes[0].set_title("Rating consistency\n(ICC across 5 repeats,\n1 = perfectly stable)")
    axes[0].set_ylim(0, 1)
    axes[1].bar(x, cons["value_ratio_max_min_median"], color="#c05621")
    axes[1].set_title("Market value instability\n(median max/min ratio,\nsame profile, 5 repeats)")
    axes[1].axhline(1, color="grey", lw=0.8, ls="--")
    g = gr.set_index("model").reindex(models)
    axes[2].bar(x, 100 * g["share_responses_with_unsupported"], color="#7b1e1e")
    axes[2].set_title("Grounding\n(% responses with a number\nnot present in the profile)")
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(models, rotation=0)
        ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


# ----------------------------------------------------------------------------- main
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--responses", default="data/audit/responses.jsonl")
    parser.add_argument("--profiles", default="data/audit/profiles.json")
    parser.add_argument("--out", default="results")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    df, profiles = load(Path(args.responses), Path(args.profiles))
    print(f"Valid responses: {len(df):,} | models: {df['model'].nunique()} | profiles: {df['profile_id'].nunique()}")
    print(df.groupby("model").size().to_string())

    cons = consistency(df)
    res, tests, cond = bias(df)
    mm = mixed_models(cond)
    gr, gr_detail = grounding(df, profiles)
    lvp = label_vs_performance(df, res, Path(args.profiles).parent / "profiles_key.csv")

    cons.to_csv(out / "consistency.csv", index=False)
    res.to_csv(out / "bias_by_level.csv", index=False)
    tests.to_csv(out / "bias_tests.csv", index=False)
    mm.to_csv(out / "bias_mixed_models.csv", index=False)
    gr.to_csv(out / "grounding.csv", index=False)
    gr_detail.to_csv(out / "grounding_detail.csv", index=False)
    grounding_examples(gr_detail, profiles, out / "grounding_examples.md")
    lvp.to_csv(out / "label_vs_performance.csv", index=False)
    fig_bias(res, out / "fig1_bias.png")
    fig_consistency_grounding(cons, gr, out / "fig2_consistency_grounding.png")

    pd.set_option("display.width", 200)
    md = ["# Audit results\n", f"Valid responses: {len(df):,}\n",
          "## Consistency (baseline repeats)\n", cons.round(3).to_markdown(index=False), "\n",
          "## Label effects: global test per factor (Friedman across profiles)\n", tests.round(4).to_markdown(index=False), "\n",
          "## Label effects: each label versus baseline\n", res.round(3).to_markdown(index=False), "\n",
          "## Numerical faithfulness\n", gr.round(3).to_markdown(index=False), "\n"]
    if len(lvp):
        md += ["## Label versus real performance\n", lvp.round(3).to_markdown(index=False), "\n"]
    if len(mm):
        md += ["## Mixed models (rating ~ level + (1|profile))\n", mm.round(4).to_markdown(index=False), "\n"]
    (out / "summary.md").write_text("\n".join(md), encoding="utf-8")

    print("\n== Consistency ==")
    print(cons.round(3).to_string(index=False))
    print("\n== Label effects: global tests ==")
    print(tests.round(4).to_string(index=False))
    print("\n== Label effects: largest rating shifts (|Δ rating|) ==")
    print(res.reindex(res["d_rating"].abs().sort_values(ascending=False).index).head(12).round(3).to_string(index=False))
    print("\n== Numerical faithfulness ==")
    print(gr.round(3).to_string(index=False))
    if len(lvp):
        print("\n== Label versus real performance (baseline: top tercile - bottom tercile) ==")
        print(lvp.round(2).to_string(index=False))
    print(f"\nTables and figures written to {out}/")


if __name__ == "__main__":
    main()
