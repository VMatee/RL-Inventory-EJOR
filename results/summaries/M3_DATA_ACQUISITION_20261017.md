# M3 public-source acquisition audit — 2026-10-17

**Status:** M5 primary dataset acquired and verified in full; original item-level 2017 Corporación Favorita external dataset **NOT acquired** (Kaggle credentials/rule acceptance absent). Synthetic experiment track requires no downloaded dataset. This is **data acquisition only**, not completion of M3 scientific data governance or M2 policy baselines.

## Frozen dataset count (do not quietly expand)

1. M5 Walmart (primary real-sales track).
2. Corporación Favorita 2017 Grocery Sales Forecasting (external item-by-store retailer; NOT the different later Store Sales product-family dataset).
3. Synthetic known-distribution demand (locally generated experiments, no externally acquired dataset).

Original competition pages:
- M5: https://www.kaggle.com/competitions/m5-forecasting-accuracy/data
- Favorita: https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting/data

The M5 primary source for verification is University of Nicosia's Zenodo record 10203108: https://doi.org/10.5281/zenodo.10203108. Larger M5 CSVs were transported through a pinned Hugging Face mirror and checked against the Zenodo record's MD5 hashes. See source paths and full SHA256 in `data/manifests/m5_verified_20261017.json`.

## M5 results observed on the connected PC

| File | Bytes (exact) | Rows (excluding header) | Columns | MD5 verified |
|---|---:|---:|---:|---|
| calendar.csv | 103,469 | 1,969 | 14 | Yes |
| sales_train_validation.csv | 120,007,726 | 30,490 | 1,919 | Yes |
| sales_train_evaluation.csv | 121,736,518 | 30,490 | 1,947 | Yes |
| sell_prices.csv | 203,395,785 | 6,841,121 | 4 | Yes |
| sample_submission.csv | 5,228,786 | 60,980 | 29 | Yes |
| **TOTAL** | **450,472,284** | | | **5 / 5** |

Each raw CSV is stored under Git-ignored `data/raw/m5/`, with a local checksum manifest `data/raw/m5/manifest.json`. Public source links, checksum values and schema counts are tracked separately as small metadata; no raw sales or raw customer records were committed. `git check-ignore` confirmed raw CSV exclusion.

Acquisition: Zenodo provided `calendar.csv` and `sample_submission.csv` directly. One large-file Zenodo request timed out and left a partial file; after the full file was acquired via pinned Hugging Face range requests and **passed the independent Zenodo MD5 check**, only the stale partial was removed. The three large files were cross-mirror verified and installed atomically after checksum validation. The pinned mirror SHA256 for `sales_train_validation.csv` also matched the Hugging Face file metadata. Re-check via:

```bash
cd "$HOME/Desktop/work/research journal/RL-Inventory-EJOR/github"
../code/.venv/bin/python scripts/fetch_m5.py --verify-only
```

**Unresolved legal detail:** the original Kaggle entry states `Subject to Competition Rules`; the Zenodo record does not provide an independent license. The downloaded dataset is kept locally for project evaluation, not redistributed. Review licensing/citation and any institutional use restrictions before publishing raw excerpts, derivative products or sharing archives.

**Critical scientific limitation:** these are realized *sales* series, which can be censored by stockouts, not guaranteed latent demand. `sales_train_evaluation.csv` extends the historical sequence beyond validation and **must not contaminate training or tuning before a chosen cutoff**. No temporal splits, product eligibility, historical censorship inference, cost scenarios, GP modeling or policy training have been performed.

## Favorita: accurately blocked, no substitution

The required 2017 original `favorita-grocery-sales-forecasting` Kaggle competition lists 8 `.csv.7z` files, about **479.88 MB compressed** with multiple GB after extraction. Its data are subject to competition rules, and the logged-in user must accept them before an authorized API download. The PC had **no usable `~/.kaggle/kaggle.json` or `KAGGLE_USERNAME/KAGGLE_KEY`** during this session; no private values were read or printed. The file `data/raw/favorita/favorita-grocery-sales-forecasting.zip` does not yet exist.

Installed Kaggle CLI **1.7.4** and py7zr **1.1.2** in the isolated Python 3.10 environment; the compatible CLI recognizes legacy username/key credentials. `scripts/fetch_favorita.py --status` reports the missing access; `--download` refuses without them. The CLI can download and validate original ZIP membership/CRC only after the account owner accepts the competition rules and configures local credentials. The script does not circumvent access or download some different family-level Favorita competition.

Follow `data/sources/FAVORITA.md` and run from the user terminal after authorization:

```bash
cd "$HOME/Desktop/work/research journal/RL-Inventory-EJOR/github"
../code/.venv/bin/python scripts/fetch_favorita.py --status
../code/.venv/bin/python scripts/fetch_favorita.py --download
../code/.venv/bin/python scripts/fetch_favorita.py --verify
```

Do not paste tokens into chat/Git. Python `code/.venv` and all credentials remain local.

The original Favorita training data omit zero-sales item–store–day rows, include negative sales as returns and allow fractional quantities; they do not directly meet M1's nonnegative integer **demand** assumption. Before using them in a scientific experiment, specify conversion, missingness, filtering and strict time cuts **without future information**.

## Local checks

- Repeated verification of all five M5 files: `status=complete`, `verified_count=5`, `total_verified_bytes=450472284`, no invalid files.
- Header, row count, first sales fields, final day-column checks: passed for five CSVs.
- Unit test suite: **39 tests** (34 preexisting + 5 offline acquisition guards) passed at time of report, including offline ZIP CRC/test fixtures and refusal to attempt uncredentialed Kaggle download.
- Ruff lint for new scripts and data tests: passed after import formatting.
- `pip check`: no broken dependencies.
- The GitHub Actions workflow was not triggered; local tests only.
- Raw files explicitly ignored by `.gitignore`. Only checksum/source metadata and source code are planned for publication in Git.

## Scientific next actions

1. Do not block M2 finite-support exact DP on external data; M2 can proceed with synthetic, known-demand instances after approving M1 timing/boundary conventions.
2. User must accept the **original 2017 Favorita** competition rules and configure local Kaggle credentials before it can be downloaded; then verify ZIP and nested files.
3. Freeze a leakage-safe data protocol and development/test cutoffs, count all pretraining/validation data, define product eligibility and documented sales-vs-demand assumptions. External Favorita must stay held out from method design/tuning.
4. No GP, RL training, real-data policy performance or EJOR acceptance claim has been inferred from these download/integrity checks.
