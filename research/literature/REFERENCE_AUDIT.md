# Reference audit

## Scope of the 2026-10-17 Introduction revision

The 16 records originated in the supplied Word draft. This revision adds scoped checks against primary publication pages, author manuscripts and official proceedings. The table records what was actually checked and the limited claim supported. Selected-text or abstract checks are not full-paper replication, a complete metadata audit or proof that the proposed research is novel. No numerical findings from the cited papers were imported into the Introduction.

The Introduction's research question, inventory-sensitivity objective, candidate method and evaluation protocol are the project's proposals. They are not results established by the citations below. The original source archive has not been changed.

Access/check date for the entries below: 2026-10-17.

| Key | Primary source and inspection level | Claim supported in the Introduction | Limits / follow-up |
|---|---|---|---|
| bijvank2011 | https://research.rug.nl/en/publications/lost-sales-inventory-theory-a-review/ ; university publication record/abstract and publisher metadata | Lost-sales inventory has a distinct sequential stock-flow and policy context. | Review article, not a guarantee for our model. DOI 10.1016/j.ejor.2011.02.004. |
| prak2017 | https://pure.rug.nl/ws/files/77757714/On_the_calculation_of_safety_stocks_when_demand_is_forecasted.pdf ; published paper, relevant abstract and opening analysis | Parameter-estimation uncertainty affects lead-time forecast-error dependence and safety-stock calculations. | Do not transfer its formulas to our policy-comparison setting without analysis. DOI 10.1016/j.ejor.2016.06.035. |
| theodorou2025 | https://www.sciencedirect.com/science/article/pii/S0377221724009755 ; indexed publisher abstract/highlights and metadata; direct page returned access error | M5-based analysis links forecast accuracy and inventory performance to product/setting/cost characteristics. | No result table independently reviewed in this revision. Recheck full published protocol before reproduction. DOI 10.1016/j.ejor.2024.12.033. |
| deisenroth2011 | https://icml.cc/2011/papers/323_icmlpaper.pdf ; official paper, opening argument and probabilistic-model discussion | PILCO already uses model uncertainty to address model bias and data-efficient policy learning. | Not inventory evidence and not a guarantee for a different GP likelihood or policy optimizer. |
| boute2022 | https://research.tue.nl/en/publications/deep-reinforcement-learning-for-inventory-control-a-roadmap/ ; author-institution record/abstract and publisher metadata | Inventory structure and algorithm-design choices matter for inventory DRL. | A roadmap/review, not a new performance result of our method. DOI 10.1016/j.ejor.2021.07.016. |
| dehaybe2024 | https://research.dial.uclouvain.be/entities/publication/184d6f34-1b43-4e70-b963-f6edc1e37e1d ; author-institution record/abstract and publisher metadata | Forecast-conditioned inventory learning addresses nonstationary uncertain demand. | No claim that its formulation equals ours. DOI 10.1016/j.ejor.2023.10.007. |
| temizoz2025 | https://pure.tue.nl/ws/files/362749586/1-s2.0-S0377221725000463-main.pdf ; published article, relevant method text | DCL uses approximate policy iteration, sequential halving and common random numbers for inventory action evaluation. | No reproduction performed and no transfer of known-model accuracy to unknown demand. DOI 10.1016/j.ejor.2025.01.026. |
| temizoz2026 | https://arxiv.org/html/2411.00515v3 ; author manuscript Sections 1-2; publication checked at https://research.tue.nl/en/publications/zero-shot-generalization-in-inventory-management-train-then-estim/ | TED combines general-policy training with online parameter estimation and explicitly includes limited/censored-information settings. | Small data, unknown demand and zero-shot deployment are not claimed as new. Author manuscript and final EJOR version should be reconciled for detailed theorem comparisons. DOI 10.1016/j.ejor.2025.12.033. |
| alvo2025 | https://arxiv.org/abs/2306.11246v3 and https://arxiv.org/html/2306.11246v3 ; version metadata and selected Sections 2.4, 3.3 and 8.2 | Differentiable/structure-informed inventory policy learning, data requirements and Favorita sales experiments. | Version 3 dated 2025-09-10; treated as a preprint, not an EJOR publication. Sales are an imperfect demand proxy. No raw data downloaded. |
| rasmussen2006 | https://gaussianprocess.org/gpml/chapters/ ; authors' book page and contents | Background role of covariance and posterior inference in GP modeling. | Chapter-level statement/page audit remains pending; do not infer universal calibration or small-data superiority. |
| price2019 | https://www.sciencedirect.com/science/article/pii/S0377221718310063 and https://arxiv.org/abs/1711.10910 ; publisher/author abstracts | GP modeling of demand unconstraining under a specified observation problem. | Demand censoring is outside our core model; this reference does not make it solved here. DOI 10.1016/j.ejor.2018.11.065. |
| lin2022 | https://papers.neurips.cc/paper_files/paper/2022/hash/6f7d90b1198fec96defd80b5ebd5bc81-Abstract-Conference.html ; official proceedings abstract | Bayesian Risk MDPs apply risk functionals to posterior parameter uncertainty and include an inventory example. | Repaired the inaccessible legacy URL; detailed risk-functional equivalence is still a research task. |
| petrik2016 | https://papers.neurips.cc/paper/6294-safe-policy-improvement-by-minimizing-robust-baseline-regret.pdf ; official PDF, opening sections and baseline-regret formulation | Robust baseline regret already compares policies under the same uncertain model; shared uncertainty can affect their difference less than separate extremes. | Not a new principle of this project. PDF author order is Petrik, Ghavamzadeh, Chow; retained despite a different order on the abstract-page metadata. Full generality/computational limitations need equation-level comparison before novelty claims. |
| laroche2019 | https://proceedings.mlr.press/v97/laroche19a.html ; official proceedings record/abstract | Baseline bootstrapping restricts policy deviations when evidence is insufficient. | Its assumptions and guarantees are not assigned to our proposal. |
| makridakis2022 | https://www.sciencedirect.com/science/article/pii/S0169207021001874 ; indexed publisher abstract and metadata | M5 is a documented retail-sales forecasting competition. | Not a logged inventory-control dataset or proof of uncensored demand. Raw-data access, licenses and split design remain unperformed project tasks. DOI 10.1016/j.ijforecast.2021.11.013. |
| agarwal2021 | https://papers.neurips.cc/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html ; official proceedings abstract | Finite-run uncertainty should be accounted for in DRL evaluation. | Temporal/cross-item dependence controls in our historical study are our protocol choices, not a claimed result of this paper. |

## Journal guidance

EURO's EJOR scope/editorial-policy page was checked: https://www.euro-online.org/web/pages/518/european-journal-of-operational-research-ejor . It supports an OR methodology/decision-science orientation, not acceptance predictions.

The full Guide for Authors endpoint returned an access error during this revision: https://www.sciencedirect.com/journal/european-journal-of-operational-research/publish/guide-for-authors . The existing elsarticle scaffold was retained. Formatting compliance, declarations and submission details must be checked again before submission.

## Explicit boundaries

- No new citation keys were added; all 16 existing keys remain cited.
- Publication status and the claims used in the Introduction were checked at the levels recorded above. Some page counts, author initials and other fields remain inherited rather than independently audited field-by-field.
- The initial Word-derived prose is archived. Current framing edits and the policy-cost equation are a user-requested revision, not a claim of verbatim conversion.
- The equation defining a policy-cost difference is notation, not a theorem or novelty claim.
- The most important unresolved overlap checks are robust baseline regret, Bayesian risk, DCL/TED and data-efficient GP policy learning. Absence of a matching result in this scoped check is not proof of novelty.
- The bibliography is not a completed systematic review; method-level comparison and final version reconciliation remain required before submission.
