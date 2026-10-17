# Datasets for the fixed EJOR research plan (2026-10-17)

**Frozen scope recommendation: TWO real retail-sales datasets, plus ONE synthetic experiment track.** Dataset quantity itself is not an EJOR publication criterion. The study's credibility depends on design, information parity, baselines, statistical treatment and auditability. Do not add another real dataset just to increase the count.

| Experimental track | Source | Role | Acquisition status |
|---|---|---|---|
| A: synthetic known demand | Self-generated with documented seeds and distributions | Ground truth; exact DP on small instances; GP misspecification and lead-time sensitivity | No external download; generator is NOT implemented (M2/M4) |
| B: M5 Walmart | University of Nicosia M5 accuracy competition, DOI 10.5281/zenodo.10203108 and original Kaggle M5 competition | **Primary**: limited-demand-history cost–data curves, n=28,56,112,224 days | Five unmodified CSVs downloaded locally (450,472,284 bytes) and byte/MD5-verified, with SHA256 manifest. No final evaluation split yet |
| C: Corporación Favorita **Grocery Sales Forecasting (2017, item-by-store)** | Kaggle competition `favorita-grocery-sales-forecasting` | **External retailer**: locked-model robustness/generalization, after M5 method/protocol frozen | Original 8 .csv.7z files require Kaggle account and accepted competition rules; no credentials detected, **NOT DOWNLOADED** |

## Two similar but DISTINCT Favorita datasets

Use **`https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting/data`**, NOT `store-sales-time-series-forecasting`. The original competition provides `unit_sales` at `date × store_nbr × item_nbr`, plus product metadata; the later competition aggregates at product-family level and is **not equivalent** for reproducing the item-level inventory setting in Alvo et al.'s available manuscript (arXiv:2306.11246v3, Section 8.2).

Original 2017 Favorita data list: `train.csv.7z`, `test.csv.7z`, `items.csv.7z`, `stores.csv.7z`, `transactions.csv.7z`, `oil.csv.7z`, `holidays_events.csv.7z`, `sample_submission.csv.7z`. Kaggle lists approximately 479.88 MB compressed, with substantial uncompressed disk usage (multi-GB). It is **subject to competition rules**; never circumvent access/redistribute an unauthorized copy.

The original Favorita sales data omit store/item/date records with zero unit sales and can include **negative `unit_sales` as returns** and fractional sales of weight-based products. These facts are not automatically consistent with M1's nonnegative integer **latent demand**. Define a prespecified inclusion, unit transformation and missing-day protocol, with censoring assumptions and leakage controls, before evaluating Favorita. Do not silently fill missing records with known-zero demand, clip negatives or claim deployment effects.

## Research boundaries

- M5, Favorita are **sales**, not directly observed uncensored demand or true retailer inventory policy logs. Inventory cost parameters are scenarios, not operational accounting.
- Raw data, restricted derivative data, extracts and credentials stay local under `github/data/raw/` or `github/data/processed/`, both Git-ignored. Only source links, hashes, non-sensitive metadata and later reviewed statistical summaries may be tracked.
- Chronological cutoffs and development/test separation must be frozen before model selection. For each method, account for per-series history, cross-series priors, hyperparameter searches, pretrained weights, and simulated rollouts. The 28/56/112/224-day budgets count **real** initial observations, not simulated transitions.
- Do NOT re-use all 1941 days for both model development and evaluation, or choose SKUs based on future outcomes. The last-28-day M5 competition split is a known reference but not an automatic split for our proposed cost–data design.
- The M1 positive lead-time stock-flow simulator does not learn demand; no demand data is required to validate its equations. M2 exact DP also uses controlled synthetic distributions.

## Acquisition commands (Git checkout is in workspace/github)

```bash
cd "$HOME/Desktop/work/research journal/RL-Inventory-EJOR/github"
../code/.venv/bin/python scripts/fetch_m5.py --verify-only
../code/.venv/bin/python scripts/fetch_favorita.py --status
```

See `data/sources/M5.md` and `data/sources/FAVORITA.md` for complete, authenticated acquisition guidance. See `data/manifests/m5_verified_20261017.json` for public source hashes only (no data bytes). `scripts/fetch_m5_hf.py` uses a pinned Hugging Face mirror for efficient segmented transport and verifies output against the University of Nicosia's Zenodo MD5. The pinned mirror does not supersede the original source or alter its legal terms.
