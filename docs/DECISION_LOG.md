# Research decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-10-17 | Adopt limited-demand-data decision-sensitive inventory policy learning | Latest supplied research brief; earlier rolling-service-control idea is not the active main contribution |

| 2026-10-17 | Adopt GitHub-first canonical LaTeX, one-writer local execution and reviewed evidence handoffs | User requests ChatGPT web + GitHub + SeneraAiServer + optional local Codex; research scope unchanged |
| 2026-10-17 | M1 *engineering* convention selected for validation: after-arrival decision state, order at t received start t+L, demand after order, lost sales, holding before next receipt; no additional terminal valuation | Previous model brief left event timing and terminal treatment unspecified. Explicitly documented with independent hand fixture and tests; **not claimed to be author-approved final scientific convention**. Confirm before M2/theory comparisons. |
| 2026-10-17 | Retain two external real-sales datasets only (M5 primary, original 2017 item-level Favorita frozen external validation) plus one synthetic data track | User requested acquiring all *planned* data ahead of M2. M5 files were verified; Favorita remains blocked by required Kaggle rules/account. Data acquisition does not authorize leakage-unsafe preprocessing, new empirical claims or substitutions. |
