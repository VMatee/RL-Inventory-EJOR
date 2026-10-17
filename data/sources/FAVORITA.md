# Corporación Favorita Grocery Sales Forecasting (2017) — external validation

**Acquisition status (2026-10-17): BLOCKED by Kaggle account access; no raw Favorita competition files downloaded.**

The exact required source is https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting/data. This is the historical *item/store* competition (`train.csv` fields `date, store_nbr, item_nbr, unit_sales, onpromotion`), **NOT** https://www.kaggle.com/competitions/store-sales-time-series-forecasting/data, which has **family-level** daily sales.

The original item-level competition is used in the HDPO inventory-control research manuscript (Alvo et al., arXiv:2306.11246v3, Section 8.2). It supports a defensible external-retailer robustness test but is not directly an observed inventory-cost log. Alvo et al. filter and aggregate data to weeks, excluding certain traces and dates; those transformations are not directly applicable to our short-data design until prespecified.

## Kaggle account action required

1. Sign in to your own Kaggle account at https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting/data and **accept the competition rules** if asked.
2. On Kaggle's account settings/API page, create Kaggle CLI credentials that work with the installed **Kaggle CLI 1.7.4 (Python 3.10)**. Legacy credentials may be saved at `~/.kaggle/kaggle.json` with permissions `chmod 600 ~/.kaggle/kaggle.json`; alternatively configure `KAGGLE_USERNAME` and `KAGGLE_KEY` privately. Do **not** paste tokens into ChatGPT or add credentials to this Git repository.
3. From the Git checkout, run:

```bash
cd "$HOME/Desktop/work/research journal/RL-Inventory-EJOR/github"
../code/.venv/bin/python scripts/fetch_favorita.py --status
../code/.venv/bin/python scripts/fetch_favorita.py --download
../code/.venv/bin/python scripts/fetch_favorita.py --verify
```

The download step uses only the official Kaggle CLI and requires an authenticated, rules-accepted account; it does not submit competition entries or bypass terms. A full ZIP is approximately 480 MB compressed and the original `train.csv.7z` alone expands to multiple GB. `--verify` checks the Kaggle ZIP's inner filenames and CRC and records local SHA256; deeper `.7z` and CSV schema checks follow only after a successful download.

**Blocked today:** SeneraAiServer detected neither legacy token files nor Kaggle environment authentication. The CLI was installed to the project's isolated `code/.venv`, but neither agent nor script can accept competition rules for you. No unverified third-party mirror was substituted.

## Important data limitations

Negative `unit_sales` indicate returns; weight-based product sales can be fractional; rows with zero sales for a store/item/date are omitted and stock availability is unobserved. Future study must explicitly specify valid SKU/unit selection, negative and missing records treatment, handling promotions, calendar cutoffs, censoring and test leakage **before** applying M1's integer-demand simulator. `train.csv`, `items.csv`, `stores.csv`, `transactions.csv`, `holidays_events.csv`, and `oil.csv` are informative; do not merge another Favorita dataset or assume the competition test file includes observed outcomes.
