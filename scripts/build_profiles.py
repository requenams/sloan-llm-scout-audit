"""
Build the player profiles used in the LLM audit.

Input:  data/derived/player_match.parquet
Output:
  data/derived/player_season.parquet   - player-season aggregates with per-90 values and percentiles
  data/audit/profiles.json             - anonymised sample (what the LLMs see)
  data/audit/profiles_key.csv          - anonymous id -> real player mapping (never used in prompts)

Usage:
  python scripts/build_profiles.py --min-minutes 900 --per-group 20 --seed 2027
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

# Metrics shown to the LLM: column name, human-readable label, source count.
METRICS = [
    ("npxg_p90", "Non-penalty xG per 90", "npxg"),
    ("shots_p90", "Shots per 90", "shots"),
    ("xa_p90", "Expected assists per 90", "xa"),
    ("key_passes_p90", "Key passes per 90", "key_passes"),
    ("touches_box_p90", "Touches in opposition box per 90", "touches_box"),
    ("progressive_passes_p90", "Progressive passes per 90", "progressive_passes"),
    ("progressive_carries_p90", "Progressive carries per 90", "progressive_carries"),
    ("dribbles_completed_p90", "Successful dribbles per 90", "dribbles_completed"),
    ("pass_completion_pct", "Pass completion %", None),
    ("pressures_p90", "Pressures per 90", "pressures"),
    ("tackles_interceptions_p90", "Tackles + interceptions per 90", None),
    ("ball_recoveries_p90", "Ball recoveries per 90", "ball_recoveries"),
    ("aerials_won_p90", "Aerial duels won per 90", "aerials_won"),
]
COUNT_COLS = [
    "shots", "npxg", "goals", "key_passes", "assists", "xa", "touches_box", "passes", "passes_completed",
    "progressive_passes", "passes_final_third", "crosses", "carries", "progressive_carries", "dribbles",
    "dribbles_completed", "dispossessed", "pressures", "pressures_att_third", "tackles", "tackles_won",
    "interceptions", "blocks", "clearances", "ball_recoveries", "dribbled_past", "fouls_committed",
    "fouls_won", "aerials_won",
]
GROUP_LABELS = {
    "CB": "Centre-back", "FB": "Full-back", "DM": "Defensive midfielder", "CM": "Central midfielder",
    "AM": "Attacking midfielder", "W": "Winger", "FW": "Forward",
}


def aggregate_seasons(pm: pd.DataFrame) -> pd.DataFrame:
    keys = ["player_id", "player", "competition", "season"]
    agg = pm.groupby(keys).agg(minutes=("minutes", "sum"), matches=("match_id", "nunique"), **{c: (c, "sum") for c in COUNT_COLS}).reset_index()
    # Main position by minutes played
    pos = pm.groupby(keys + ["pos_group"])["minutes"].sum().reset_index()
    pos = pos.sort_values("minutes", ascending=False).drop_duplicates(keys)[keys + ["pos_group"]]
    agg = agg.merge(pos, on=keys)
    # Main team by minutes played
    team = pm.groupby(keys + ["team"])["minutes"].sum().reset_index()
    team = team.sort_values("minutes", ascending=False).drop_duplicates(keys)[keys + ["team"]]
    agg = agg.merge(team, on=keys)

    per90 = 90.0 / agg["minutes"]
    for name, _, source in METRICS:
        if source:
            agg[name] = agg[source] * per90
    agg["pass_completion_pct"] = 100.0 * agg["passes_completed"] / agg["passes"].replace(0, np.nan)
    agg["tackles_interceptions_p90"] = (agg["tackles"] + agg["interceptions"]) * per90
    return agg


def add_percentiles(ps: pd.DataFrame, min_minutes: int) -> pd.DataFrame:
    """Percentile of each metric within the position group, computed over the
    population with at least min_minutes (the usual scouting reference)."""
    ref = ps[ps["minutes"] >= min_minutes]
    for name, _, _ in METRICS:
        pct = ref.groupby("pos_group")[name].rank(pct=True) * 100
        ps.loc[ref.index, f"{name}_pct"] = pct.round(0)
    return ps


def sample_profiles(ps: pd.DataFrame, min_minutes: int, per_group: int, seed: int) -> pd.DataFrame:
    """Stratified sample by position group and performance tercile (mean of
    percentiles), so the audit covers weak, average and strong players."""
    pool = ps[(ps["minutes"] >= min_minutes) & (ps["pos_group"].isin(GROUP_LABELS))].copy()
    pct_cols = [f"{n}_pct" for n, _, _ in METRICS]
    pool["level"] = pool[pct_cols].mean(axis=1)
    pool["tercile"] = pool.groupby("pos_group")["level"].transform(lambda s: pd.qcut(s, 3, labels=["low", "mid", "high"]))
    per_cell = int(np.ceil(per_group / 3))
    parts = [g.sample(min(per_cell, len(g)), random_state=seed) for _, g in pool.groupby(["pos_group", "tercile"], observed=True)]
    return pd.concat(parts).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--derived", default="data/derived")
    parser.add_argument("--out", default="data/audit")
    parser.add_argument("--min-minutes", type=int, default=900)
    parser.add_argument("--per-group", type=int, default=20)
    parser.add_argument("--seed", type=int, default=2027)
    args = parser.parse_args()
    derived, out = Path(args.derived), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    pm = pd.read_parquet(derived / "player_match.parquet")
    ps = aggregate_seasons(pm)
    ps = add_percentiles(ps, args.min_minutes)
    ps.to_parquet(derived / "player_season.parquet", index=False)

    sample = sample_profiles(ps, args.min_minutes, args.per_group, args.seed)
    sample = sample.sample(frac=1, random_state=args.seed).reset_index(drop=True)
    sample["profile_id"] = [f"P{i:03d}" for i in range(1, len(sample) + 1)]

    profiles = []
    for _, r in sample.iterrows():
        profiles.append({
            "profile_id": r["profile_id"],
            "position": GROUP_LABELS[r["pos_group"]],
            "pos_group": r["pos_group"],
            "minutes": int(round(r["minutes"])),
            "matches": int(r["matches"]),
            "metrics": [
                {"name": label, "value": round(float(r[name]), 2), "percentile": int(r[f"{name}_pct"])}
                for name, label, _ in METRICS
            ],
        })
    (out / "profiles.json").write_text(json.dumps(profiles, indent=2, ensure_ascii=False), encoding="utf-8")
    sample[["profile_id", "player_id", "player", "team", "competition", "season", "pos_group", "minutes", "level", "tercile"]].to_csv(out / "profiles_key.csv", index=False)

    ref = ps[ps["minutes"] >= args.min_minutes]
    print(f"Player-seasons: {len(ps):,}  |  with >= {args.min_minutes} min: {len(ref):,}")
    print("\nReference population per position group:")
    print(ref.groupby("pos_group").size())
    print(f"\nSampled profiles: {len(profiles)}")
    print(sample.groupby(["pos_group", "tercile"], observed=True).size().unstack())
    print(f"\nExample profile ({profiles[0]['profile_id']}, {profiles[0]['position']}):")
    for m in profiles[0]["metrics"]:
        print(f"  {m['name']:<36} {m['value']:>7}   pct {m['percentile']}")


if __name__ == "__main__":
    main()
