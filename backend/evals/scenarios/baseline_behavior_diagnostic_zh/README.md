# baseline_behavior_diagnostic_zh

Traditional Chinese language mirror of the `baseline_behavior_diagnostic` scenario — the
same 30 rows, ids, and 15-column schema; only `question`, `expected_answer_type`,
`draft_pass_signals`, and `why_baseline_might_fail_or_pass` are translated (with company
names in `question` localized to their customary Taiwanese Mandarin form, e.g. Tesla →
特斯拉 — names habitually used in English in Taiwan, like Google or Netflix, are kept
as-is). `company_universe` intentionally stays in English, byte-identical to the source
dataset, since it is a ticker/company-identity key rather than display prose. All other
taxonomy/structural columns are also byte-identical to the English `dataset.csv`.

Runs as a first-class scenario with its own diagnostic identity
(`dataset_name: baseline_behavior_diagnostic_zh`), so Chinese-run traces never share
session ids with English runs and the two experiments can be compared side by side
(same agent, English vs Chinese prompts).

```bash
uv run python -m backend.evals.eval_runner baseline_behavior_diagnostic_zh
```

Maintenance rule: keep this dataset row-aligned with the English scenario's
`dataset.csv` — any curation change to a taxonomy column there must be applied here
verbatim; free-text columns get a matching translation. See the English scenario's
README for the full per-column annotation guide, which applies unchanged.
