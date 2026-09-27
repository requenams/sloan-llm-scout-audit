# Same Stats, Different Passport: Auditing Large Language Models as Football Scouts

Companion repository for the abstract submitted to the MIT Sloan Sports Analytics Conference 2027
Research Paper Competition.

**Question.** When a large language model evaluates a player from identical statistics, do its
conclusions change with a label that carries no new information (nationality), with a contextual
label (league), or simply when asked again?

**Design.** 147 anonymised player-seasons (≥ 900 minutes) from 1,517 matches of the 2015/16 La Liga,
Premier League, Serie A and Ligue 1 (StatsBomb open data), described by 13 per-90 metrics with
positional percentiles. Four models (Claude Sonnet 4.5, GPT-5, Gemini 2.5 Pro, DeepSeek V3.1) evaluated
every profile under 12 conditions that change only one line of text: no label (five repeats), six
nationalities and five leagues. 9,408 structured responses.

**Headline results.**
- With identical statistics, all four models cut the estimated value of a player labelled Nigerian
  by 21–28% and Japanese by 18–29%, and raise it by 8–15% for a German and 4–14% for a Spanish label.
  Quality ratings move by at most 0.13 points: the bias sits in the price, not in the assessment.
- In every model, changing the league label from "Segunda División" to "Premier League" moves the
  estimated value more (4.4–9.5×) than moving the player from the bottom to the top performance
  tercile (3.4–7.2×).
- Asked about the same profile five times, the models change their recommendation in 8% to 34% of
  cases and move the value by a median factor of up to 1.9.

See `results/summary.md` for every table and `abstract/` for the submitted abstract.

## Repository layout

```
scripts/
  download_statsbomb.py     # StatsBomb open-data events (resumable)
  build_player_match.py     # events -> one row per player and match (minutes + raw counts)
  build_profiles.py         # player-season aggregates, per-90, percentiles, anonymised sample
  run_audit.py              # experimental battery: profile x condition x model -> responses.jsonl
  analyze_audit.py          # consistency, label effects, numerical faithfulness -> results/
  make_figures.py           # the two abstract figures
config/models.json          # model list (API keys are read from environment variables)
data/audit/profiles.json    # the 147 anonymised profiles exactly as shown to the models
data/audit/profiles_key.csv # anonymous id -> real player mapping (never used in prompts)
data/audit/responses.jsonl  # all model responses
data/derived/               # player-match and player-season tables derived from the open data
results/                    # tables (CSV, summary.md) and figures
abstract/                   # submitted abstract (PDF)
```

Raw StatsBomb event files are not redistributed here; `scripts/download_statsbomb.py` regenerates
them from the public repository in a few minutes.

## Reproduce

```bash
pip install -r requirements.txt

python scripts/download_statsbomb.py --out data/statsbomb
python scripts/build_player_match.py --data data/statsbomb --out data/derived
python scripts/build_profiles.py --min-minutes 900 --per-group 20 --seed 2027

# set OPENROUTER_API_KEY (or the keys named in config/models.json), then:
python scripts/run_audit.py --models config/models.json --workers 12

python scripts/analyze_audit.py
python scripts/make_figures.py --results results
```

`run_audit.py` is resumable and only sends the calls missing from `responses.jsonl`; a `mock`
provider entry in `config/models.json` exercises the whole pipeline without any API cost.

## Method notes

- **Conditions.** Every prompt contains the same table (13 per-90 values with positional percentiles,
  minutes, matches, position, age fixed at 24). Conditions add exactly one line: `Nationality: X`
  or `Current league: Y`. The baseline has neither.
- **Consistency.** Intraclass correlation ICC(1) of the rating across the five baseline repeats,
  within-profile dispersion, and the share of profiles whose recommendation changes between runs.
- **Label effects.** Paired differences of each condition against the mean baseline of the same
  profile and model, bootstrap 95% confidence intervals, Friedman tests across profiles, and
  mixed-effects models with a profile random effect (`results/bias_mixed_models.csv`).
- **Label versus performance.** The value gap between the top and bottom performance terciles
  (no label) compared with the gap between the best and worst league label (identical statistics).
- **Numerical faithfulness.** Every number quoted in a justification is checked against the profile
  table; approximate thresholds, ranges and positional jargon are excluded first
  (`results/grounding_examples.md` lists flagged cases for manual review).

## Data and licences

Event data: [StatsBomb open data](https://github.com/statsbomb/open-data), used under its
non-commercial licence; please cite StatsBomb if you reuse the derived tables. Model outputs in
`data/audit/responses.jsonl` were generated by the listed models through their public APIs.
Code is released under the MIT licence.


