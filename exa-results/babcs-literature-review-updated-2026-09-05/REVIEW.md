# BAB-CS research directions and literature review — updated assessment

**Assessment date:** 5 September 2026. **Scope:** current working tree, including the new affine replay theorem and pilot. Base commit remains `fbf0a1e1694b9e2abceae656455b27e2187df1a3`; that commit alone does not identify the extensive uncommitted development.

**Recommendation.** The strongest next project is to connect a proved total-error ledger to actual BAB-CS affine replay traces, beginning with the existing switched-RC stress cases. The standalone theorem/pilot is a useful foundation, but it does not certify the production controller. A second promising direction is to recover dissipative contraction using verified weighted norms. A third is to allocate computation against an explicit whole-trajectory or event-time error budget.

This assessment updates the priorities in the [earlier review](../babcs-literature-review-2026-09-05/REVIEW.md). It preserves that review and its 20-source reading list rather than silently rewriting the research history.

**Review method.** I used Exa to review 36 search-result sources across six additional search workstreams: Hermite defect control, deferred correction, adaptive Parareal/error decomposition, weighted logarithmic norms, machine-verified ODE solvers, and time-to-threshold error estimation. Six searches requested six results each; all 36 URLs were distinct, but some describe the same paper. Nine selected URLs were fetched for bounded text inspection. The [search log](search-log.json) records the queries and results. These counts describe search results, not 36 fully read papers. This is a targeted literature review, not a systematic review or an exhaustive novelty search.

The earlier review supplies the broader MNA, runtime assurance, hybrid reachability, converter verification, and 2026 benchmark context. The additional searches address gaps exposed by the new pilot. Publisher records, author manuscripts, and research papers support the synthesis; aggregator-only results were used as leads, not evidence for technical claims.

**Repository assessment: what is established and what is missing.**

| Finding | Repository evidence | Research consequence |
|---|---|---|
| The affine error-accounting pilot is reproducible and internally scoped | [Theorem](../../docs/REPLAY_ERROR_BUDGET_THEOREM.md), [results](../../docs/REPLAY_ERROR_BUDGET_RESULTS.md), [executable](../../tools/replay_error_budget.py) | A starting point for integration, not a replacement for production error bounds. |
| Production replay does not implement the pilot's certificate | [bounded.py](../../src/babcs/bounded.py), especially refresh/reset logic near lines 1344–1423 | It resets `estimated_bound` and retains `reference_uncertainty`; it does not construct the pilot's independently certified inherited-plus-fresh replay budget. This is a scope distinction, not proof that every production output is wrong. |
| Existing stress cases challenge optimistic bound claims | [Stress study documentation](../../docs/AUTHORITY_STRESS_SCALING.md) and its [stored report](../../artifacts/repository-improvement-2026-09-03/imp-07-authority-stress-full-fresh-circuit/study-report.json) | Use the unfavorable existing cases as the next evaluation set. |
| The interval underflow issue remains reproducible | [reachability.py](../../src/babcs/reachability.py), line 325, and the [saved reproducer](../babcs-literature-review-2026-09-05/reproduce_affine_underflow.py) | Repair and audit the arithmetic before broadening the restricted certification claim. |
| Events already exist, but full hybrid guarantees do not follow | [state_events.py](../../src/babcs/state_events.py), [simulator.py](../../src/babcs/simulator.py), [certified_buck.py](../../src/babcs/certified_buck.py) | Investigate crossing completeness, uncertainty, and sensitivity; “add a root finder” is obsolete as a general roadmap item. |
| Stronger refinement does not necessarily produce useful authority | [Finer ladder](../../docs/FINER_ASYMPTOTIC_LADDER.md), [nonlinear authority](../../docs/INDEPENDENT_NONLINEAR_AUTHORITY.md) | Separate availability, tightness, and computational cost instead of reporting only coverage among selected samples. |

I checked the stored stress report's SHA-256 against its documentation: `6e7455f6b1be79a106d694380e624ae090f0fb11e037978126f0d06ff8572b08`. It contains 28 rows, of which eight have qualified comparison authority and twenty do not. Its documentation reports only about 3.97–3.98% recursive-bound coverage for the analytically qualified switched-RC family. These are measurements of that historical source snapshot, metric definition, and configuration; they are not fresh benchmark results for every current configuration.

The finer-ladder documentation records a nine-case campaign in which one case remained vacuous, leaving the complete study diagnostic-unqualified despite favorable holdout coverage elsewhere. That distinction matters: conditional coverage can look excellent while most of the target population remains unqualified.

**What the new replay study actually contributes.**

The theorem carries initial/anchor uncertainty through exact-flow sensitivity and adds a bound on replay defect. It makes the mathematical meaning of a refresh explicit. Its basic variation-of-constants argument belongs to established global-error analysis. Its immediate contribution to this repository is a concrete, inspectable contract and a small executable model.

The 49-run pilot uses exact rational proof quantities, rounded rational endpoints, cubic Hermite reconstruction, Bernstein coefficient bounds, and a high-precision diagnostic comparison. All recorded diagnostic trajectories are covered, and its three recorded source hashes still match. I reran its 14 tests successfully. This is stronger than checking ordinary float trajectories alone, but the code and proof have not been machine verified.

The pilot's principal negative result should shape the research agenda. With h=0.05 and replay refinement four, the RC study gives:

| Replay interval | Peak accepted-state error, diagnostic | Fine replay steps | Proposal steps |
|---|---:|---:|---:|
| Every step | 0.000004790 | 160 | 40 |
| Every 4 steps | 0.003333 | 160 | 40 |
| Every 16 steps | 0.009075 | 160 | 40 |
| Pure refined trapezoidal baseline | 0.000004790 | 160 | 0 |

Longer windows do not save fine integration work under this policy. They reduce window count while allowing larger provisional errors. Refining replay improves final anchor accuracy but leaves the early proposal-dominated peak error unchanged in the tested RC sweep. This does not rule out production savings from cache reuse, lower overhead, higher-order candidates, or adaptive replay. It means such savings remain to be demonstrated at matched accuracy.

**Literature synthesis and novelty boundaries.**

*1. Supervisory authority has close precedents.* Simplex separates advanced and fallback controllers with decision logic; Black-Box Simplex moves more assurance work into runtime checks. This is a conceptual precedent, not a theorem about numerical integrator error. BAB-CS needs a numerical contract for approximation, replay, and algebraic consistency to distinguish its contribution. See [Mehmood et al., 2022](https://doi.org/10.1007/978-3-031-06773-0_12).

*2. Residual-to-global-error analysis is established.* Neumaier develops rigorous dissipative ODE enclosures using logarithmic norms. Cao and Petzold develop sensitivity/adjoint-based global-error estimation. These motivate preserving inherited uncertainty and weighting new error by system dynamics; a discrepancy between two methods alone is not an exact-solution enclosure. See [Neumaier manuscript](https://arnold-neumaier.at/ms/ode.pdf) and [Cao and Petzold, 2004](https://doi.org/10.1137/S1064827503420969).

The closer missing comparison is Hermite defect control. Higham's 1991 work uses Hermite–Birkhoff interpolation for Runge–Kutta defect control. Wu and Yang's 2018 manuscript explicitly connects piecewise Hermite residuals to forward error for linear ODEs. The pilot's use of Hermite reconstruction should be placed in this lineage; it is not evidence that the construction itself is new. See [Higham](https://doi.org/10.1137/0912053) and [Wu and Yang](https://arxiv.org/abs/1804.03363).

*3. Correction and coarse/fine propagation require a fair comparison set.* Spectral deferred correction improves solutions through corrections to an integral formulation, rather than simply replacing a provisional endpoint. Adaptive Parareal varies fine-solver accuracy to improve parallel efficiency, and a posteriori Parareal analysis can distinguish discretization error from incomplete iteration error. These are useful algorithmic and accounting precedents. They are not interchangeable with BAB-CS: Parareal is parallel-in-time, while the present pilot replays sequentially. See [Dutt, Greengard, and Rokhlin, 2000](https://doi.org/10.1023/A:1022338906936), [Maday and Mula, 2019 preprint](https://arxiv.org/abs/1909.08333), and [Chaudhry, Estep, and Tavener, 2021 preprint](https://arxiv.org/abs/2111.00606).

A useful experiment would compare certified error budgets at equal work among direct refined integration, BAB-CS-style replay, and a correction method compatible with the same model and output contract. It should count verification and discarded proposal work as well as implicit solves.

*4. Weighted norms offer a concrete improvement opportunity.* The pilot's two-state Euclidean branch checks dissipativity and returns mu=0, including for damped RLC. This is valid but gives no strict exponential contraction. Weighted logarithmic norms constructed through Lyapunov equations can improve semigroup bounds. See [Hu and Mitsui, 2012](https://www.kybernetika.cz/content/2012/5/865).

For the actual pilot matrix, the improvement can be made explicit. I checked with exact rational arithmetic:

```text
A = [[0, 1], [-1, -2]]
P = [[3/2, 1/2], [1/2, 1/2]]
A^T P + P A = -I
(1/4) I <= P <= 2 I
```

Thus, with ||e||_P = sqrt(e^T P e), d||e||_P/dt <= -(1/4)||e||_P for the homogeneous error equation. The resulting semigroup bound is exp(-t/4), rather than 1. The positivity checks had exact determinants 1/16 for P-I/4 and 1/2 for 2I-P. This calculation is a new repository-specific research observation, not a new Lyapunov theorem.

The benefit still needs measurement: defect norms and conversion back to physical units can offset a smaller growth rate over short horizons. Changing norms between events also requires conversion factors. Neutral LC cannot be made strictly contractive by merely relabeling the norm.

*5. Event time is its own error quantity.* First-threshold-time error analysis treats the event time as a quantity of interest, with adjoint and root-based estimators. Saltation matrices describe sensitivity across hybrid transitions, including the effects of perturbed event timing. These complement guaranteed guard-crossing methods; they do not themselves prove that all events were detected. See [Chaudhry et al., 2020 manuscript](https://arxiv.org/abs/2001.11139) and [Kong et al., 2024](https://doi.org/10.1109/JPROC.2024.3440211).

BAB-CS should distinguish localization error within a detected bracket, failure to detect a crossing, and uncertainty in which transition occurs. An endpoint sign test can miss two crossings or a grazing event. The earlier review identified this coverage question; no new end-to-end missed-event counterexample was executed in this update.

*6. Hybrid reachability and buck verification are established applications.* SpaceEx and Flow* provide affine and nonlinear hybrid flowpipe precedents. Hossain and colleagues studied closed-loop hysteretic buck reachability in 2013; Beg and colleagues combined converter reachability, parameter uncertainty, and experimental model validation in 2017. A new buck paper therefore needs a particular improvement in timing semantics, uncertainty representation, decision cost, or independent evidence. See [SpaceEx](http://www-verimag.imag.fr/%7Etdang/Papers/CAV2011.pdf), [Flow*](https://plv.colorado.edu/papers/flowstar-cav13.pdf), [Hossain et al.](https://doi.org/10.1109/PECI.2013.6506047), and [Beg et al.](https://doi.org/10.1109/TIE.2017.2688961).

The current numerical FAIL for the proposed buck property is a useful result if its witness is sound. An admissible point witness can refute a universal property; proving PASS requires covering the entire declared model family. Timing corners, Monte Carlo, and point traces cannot be assigned the same proof task as continuous-set reachability.

*7. Exact arithmetic and formally verified software are different assurance levels.* Immler and Hölzl formalized ODE existence and one-step global-error reasoning in Isabelle/HOL; Immler's later work formally verified continuous reachability with adaptive integration and affine arithmetic. These precedents show what a stronger implementation assurance claim entails. See [Immler and Hölzl, 2012](https://www.cs.vu.nl/~jhl890/pub/immler2012ode.pdf) and [Immler, 2015](https://saloranta.de/immler/fabian/documents/immler2015reachability.pdf).

A realistic near-term improvement is a small independent certificate checker for affine replay traces. Formalizing an entire circuit simulator is a much larger project. Neither matching hashes nor a large test suite substitutes for numerical soundness.

**Ranked research directions.**

| Priority | Research question | First experiment | Decision criterion |
|---|---|---|---|
| Prerequisite | Does restricted interval certification preserve enclosure throughout its admitted domain? | Repair the reproduced pre-interval Taylor-coefficient underflow; audit analogous derived quantities and guard restrictions. | Exact/high-precision counterexamples eliminated by sound enclosure or explicit domain rejection. |
| 1 | Can a total-error ledger explain actual BAB-CS replay and event-boundary behavior? | Export accepted and replay substep traces for scalar RC, then `switched_rc_bank-n001`; reconstruct defects in declared physical coordinates and carry anchor radii. | Verified correspondence of model, state order, norm, rounding, time segmentation, and replay ownership; containment with useful widths. |
| 2 | Can weighted norms recover practically useful contraction? | Compare mu=0 and verified P-norm bounds for damped RLC, then coupled affine circuits; include norm-conversion costs. | Smaller physical-unit enclosures over the declared horizon without a prohibitive computation cost. |
| 3 | Can adaptive verification beat direct integration at fixed whole-trajectory accuracy? | Higher-order proposals plus defect-driven reference frequency/refinement, compared with a pure reference and a correction baseline. | Improved error/work or error/time frontier after all certificate, rejection, and proposal costs are counted. |
| 4 | Can event-time error become an explicit part of the budget? | Threshold crossings with known solutions, paired crossings, grazing, simultaneous guards, then uncertain buck delay and jitter. | Reliable distinction between detected, proved absent, and unresolved events; preserved transition uncertainty and measured timing bounds. |
| 5 | Can certification decisions be made cheaper without weakening their meaning? | Property-directed splitting and correlation-preserving sets on the exact existing buck request, plus independent verification-tool mapping. | Better time-to-PASS/FAIL or fewer UNKNOWN results at equal budgets and identical quantifiers. |

Priority 1 should initially be an offline audit tool, so it can study existing behavior before influencing acceptance. Its output should preserve separate fields for inherited anchor radius, continuous defect, endpoint/model-reduction uncertainty, norm conversion, and event/reset transfer. Unknown or unsupported contributions should remain explicitly unqualified.

For priority 3, tuning reference frequency to final-time error alone is insufficient if intermediate outputs are consumed. Select the actual quantity of interest in advance: complete trajectory, selected samples, energy, or first event time. A method can be good on one and poor on another.

**A practical first study.**

Use the current rational pilot as the verifier reference and an actual BAB-CS RC trace as the first integration target. Establish the exact reduced equations from the chosen MNA case, including the interpretation of input floats. Map every stored state and time into the verifier, and account for projection/endpoint residuals rather than assuming them away. At replay, certify from the old anchor and retain previous samples' original bounds.

Next apply the same policy to the stored switched-RC family. Verify the analytic model mapping and event-side conventions before diagnosing a solver defect. Preserve the adverse baseline and report whether gaps originate in inherited uncertainty, reference discretization, interpolation, event semantics, or norm scaling.

Use damped and neutral RLC as discriminating follow-ups: the first should benefit from a suitable dissipative metric, while the second should expose the absence of asymptotic contraction. Keep the same comparison tolerances and physical units when judging the new bound.

Report source identity, complete configuration, completed/unqualified rows, bound width, peak and final error, replay work, rejected work, memory, and complete-process timing. Include independent repeated timings only when a performance experiment is actually run. Do not extrapolate the rational pilot's deterministic operation counts to sparse production runtime.

**Additional reading, in useful order.**

| Source | Why it matters now | Reading status |
|---|---|---|
| Higham (1991), [Hermite–Birkhoff defect control](https://doi.org/10.1137/0912053) | Closest established reconstruction/defect-control comparison. | Publisher record/abstract and author-paper search extracts. |
| Wu and Yang (2018), [linear ODE solver error estimation](https://arxiv.org/abs/1804.03363) | Direct Hermite-residual-to-forward-error comparison. | Preprint opening sections. |
| Hu and Mitsui (2012), [Lyapunov-based exponential bounds](https://www.kybernetika.cz/content/2012/5/865) | Basis for the concrete weighted-norm RLC experiment. | Journal abstract and paper extracts. |
| Dutt, Greengard, Rokhlin (2000), [spectral deferred correction](https://doi.org/10.1023/A:1022338906936) | Correction-method baseline and novelty boundary. | Publisher abstract and reference context. |
| Maday and Mula (2019), [adaptive Parareal](https://arxiv.org/abs/1909.08333) | Accuracy allocation in coarse/fine computation. | Preprint abstract/opening material; no claim about latest publication version. |
| Chaudhry, Estep, Tavener (2021), [Parareal error analysis](https://arxiv.org/abs/2111.00606) | Separating numerical and iteration error sources. | Preprint abstract/opening material; PDE setting is adjacent, not identical. |
| Chaudhry, Estep, Stevens, Tavener (2020), [first-threshold-time error](https://arxiv.org/abs/2001.11139) | Event time as a separate quantity of interest. | Manuscript abstract/opening material. |
| Immler and Hölzl (2012), [ODE analysis in Isabelle/HOL](https://www.cs.vu.nl/~jhl890/pub/immler2012ode.pdf) | Formal proof versus tested arithmetic. | Author manuscript opening sections. |
| Immler (2015), [verified continuous reachability](https://saloranta.de/immler/fabian/documents/immler2015reachability.pdf) | Stronger future assurance and independent-checker context. | Author manuscript opening sections. |

The earlier review remains the reading map for numerical foundations, [2026 ARCH benchmarks](https://doi.org/10.29007/f5l7), and the [2026 circuit structure-preserving preprint](https://arxiv.org/abs/2606.06153). These were reviewed earlier in this conversation, not newly rediscovered or fully revalidated in this update.

**Validation and limits.** This review reran the 14 replay-pilot tests and 11 existing reachability tests; all 25 passed. The saved underflow reproducer still returns an endpoint interval excluding the high-precision analytic solution. It remains an extreme-scale general affine API failure, not a demonstrated incorrect supplied buck decision. The 49-row pilot and stress campaign were inspected and source/hash checked as described; the full campaigns were not rerun. The weighted RLC identity and matrix inequalities were checked with exact rational arithmetic. No production source or existing research result was modified.

**Overall assessment.** BAB-CS has enough infrastructure to support a credible numerical-method research program. The strongest paper-sized target is now a trace-based, independently checked total-error budget for affine switched circuits, followed by an accuracy/work comparison that can retain negative results. A new general solver, broader device library, or broad “bounded authority is novel” claim would be less well supported by the current evidence.
