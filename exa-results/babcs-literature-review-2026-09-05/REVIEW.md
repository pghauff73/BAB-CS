# BAB-CS: repository research directions and literature review

Assessment: 5 September 2026. Repository baseline: `fbf0a1e1694b9e2abceae656455b27e2187df1a3`, plus the current, extensively modified working tree.

**Recommendation.** Make *error-accountable replay for hybrid circuit simulation* the central research thesis. The strongest near-term study would connect the existing supervisory bound to actual trajectory error on a restricted circuit class, then quantify how event timing and replay scheduling affect accuracy and cost. Treat certified buck reachability as a second, related research track with its own soundness obligations and external verification baselines.

The literature already contains advanced/baseline supervisory architectures, global error estimation, validated hybrid integration, and verification of hysteretic buck converters. The research contribution must therefore be a specific theorem, algorithm, or experimentally demonstrated tradeoff beyond those foundations. The earlier repository report's description of the architecture as “original” should be treated as a hypothesis, not an established novelty finding.

**Scope and method.** I used Exa to review 63 search-result sources across eight thematic workstreams: runtime assurance; global error; hybrid reachability; converter verification; hybrid sensitivity; structure-preserving integration; current verification benchmarks; and interval wrapping. Three follow-up searches checked converter bibliographic metadata, DAE topology, and adaptive control. Eleven searches requested 63 results in total; these are search-result counts, not 63 fully read papers. Ten targeted URLs were fetched for further inspection, with bounded text extraction. Exact URL deduplication left 63 URLs, but several are versions or mirrors of the same work. The bibliography below consolidates those duplicates.

This is a targeted scoping review, not a systematic review or proof of novelty. Primary papers, author manuscripts, publisher records, and current benchmark proceedings were preferred. The search included work available through the assessment date, including June/July 2026 material; search coverage cannot establish that every relevant 2026 paper was found. Repository findings distinguish inspected code, existing documented evidence, and experiments run during this review. Existing release and performance campaigns were not rerun.

**What the repository actually supports.**

| Area | Evidence inspected | Research implication |
|---|---|---|
| Supervisory integration | [bounded.py](../../src/babcs/bounded.py), [error model](../../docs/ERROR_BOUND_MODEL.md), [README](../../README.md) | Seven candidates, correction, gates, deferred references, replay, and bound diagnostics already provide a useful experimental platform. |
| Authority lifetime | [refresh semantics](../../docs/AUTHORITY_REFRESH_SEMANTICS.md), `reset_history` and replay in `bounded.py` | Authority age and derivative-history resets are explicitly separated. The next question is how their error budgets compose. |
| State events | [state_events.py](../../src/babcs/state_events.py), [simulator.py](../../src/babcs/simulator.py) | Replay-owned threshold location exists. Crossing completeness and uncertainty are more useful next questions than merely adding a root finder. |
| Restricted certification | [intervals.py](../../src/babcs/intervals.py), [reachability.py](../../src/babcs/reachability.py), [certified_buck.py](../../src/babcs/certified_buck.py) | Outward-rounded arithmetic, Picard containment, affine Taylor endpoints, mode branching, splitting, and midpoint counterexample search exist. |
| Comparative evidence | [nonlinear authority](../../docs/INDEPENDENT_NONLINEAR_AUTHORITY.md), [decision benchmark](../../tools/benchmark_certified_decision.py) | Method diversity and finite corner campaigns are useful checks, but neither is an independent enclosure proof. |
| Existing bibliography | [REFERENCES.md](../../docs/REFERENCES.md) | Strong on classical MNA, integrators, root finding, and implementation references; missing several closest research families below. |

The roadmap is partly stale: [CURRENT_WORK.md](../../docs/CURRENT_WORK.md) says general state-triggered location is not yet implemented, and [APPLICATIONS_AND_RESEARCH_ROADMAP.md](../../docs/APPLICATIONS_AND_RESEARCH_ROADMAP.md) calls it the next modeling priority. The implemented threshold-observable scope should replace that blanket description. This does not mean arbitrary hybrid resets or complete event detection are implemented.

**A confirmed issue that should precede stronger certification claims.**

At [reachability.py](../../src/babcs/reachability.py), line 325, the Taylor coefficient is formed as `Interval.point(0.5 * step * step)`. The floating-point multiplications occur before the value enters interval arithmetic. For an accepted extreme-scale input, this coefficient underflows to zero and removes a nonzero second-order contribution.

The saved [reproducer](reproduce_affine_underflow.py) uses the scalar affine system `x' = 1e161*x`, `x(0)=1e-30`, `h=1e-162`, and `absolute_inflation=1e-45`. It returns:

- Endpoint enclosure: `[1.0999999999999997e-30, 1.1000000000000004e-30]`.
- Analytic endpoint, evaluated with 80-digit Decimal arithmetic on the exact binary-float inputs: approximately `1.105170918075647716e-30`.
- Containment: **false**.

This is a reproduced enclosure failure, not merely a suspicious line of code. It concerns the general affine-step API at extreme scales; it does not demonstrate a wrong decision on the supplied buck cases. The existing 11 reachability tests pass, showing that their present coverage does not catch this case.

Recommended remediation is to enclose every derived coefficient throughout its computation, or reject unsupported scaling before returning a validated result. Review analogous point computations used for guard margins, time bounds, and interval restrictions. Recheck the full proof chain rather than assuming that outward rounding of primitive interval operations covers ordinary floating-point calculations around them. Do not label those additional sites defective without separate evidence. Source code was left unchanged in this review.

**What the literature changes about the research position.**

*Supervision and numerical control.* Black-Box Simplex already separates advanced proposals, fallback behavior, and runtime acceptance checks; a later manuscript also considers blending [1–2]. Adaptive Simplex research explicitly seeks to maximize advanced-controller usage under correctness constraints [3]. Separately, Söderlind treats timestep adaptation as a feedback and digital-filter problem [4]. These are close conceptual precedents, although they do not establish BAB-CS's numerical error guarantees. A control system's invariant-safe fallback and a numerical reference integrator are different objects: the latter has truncation error and inherits initial-state error.

The defensible opportunity is a precise numerical contract for replay, correction, and constraint projection, with a measured reduction in reference work at fixed accuracy. “Using control theory in an integrator” or “checking a fast method with a slow one” is too broad.

*Local discrepancy versus global error.* Estep develops a posteriori bounds and global error control; Cao and Petzold use adjoint sensitivity to estimate propagated error; Neumaier develops rigorous enclosures using logarithmic norms and differential inequalities [5–7]. This literature directly addresses BAB-CS's gap between candidate/reference disagreement and exact-solution error.

For a smooth reconstructed trajectory `xhat(t)`, define the differential defect `r(t)=xhat'(t)-f(t,xhat(t))`. If a validated logarithmic-norm bound `mu` holds over a containing region, the error can be bounded by a propagated initial error plus an integral of the defect weighted by exponential growth. This is a proposed analytical route, not a theorem established for the current implementation. Algebraic residuals require conditioning factors before they can be interpreted as state error, and hybrid transitions require separate treatment.

BAB-CS's recursive contraction estimate can remain valuable even when it is not such an enclosure. Its name, reset rules, norm scaling, and relationship to `reference_uncertainty` should make that distinction explicit.

*Validated hybrid integration and set representation.* SpaceEx handles piecewise-affine hybrid dynamics using support functions and polyhedra; Flow* uses Taylor models for nonlinear polynomial hybrid flowpipes; HySon develops guaranteed integration and event detection using interpolation [8–10]. Neher, Jackson, and Nedialkov analyze Taylor-model integration and its relationship to interval overestimation [11]. Thus Picard containment, interval propagation, adaptive refinement, and hybrid branching have extensive precedent.

BAB-CS's inspectable implementation is useful, but its present boxes lose correlations between states and persistent parameters. Splitting reduces uncertainty at additional cost; it is not the only available strategy. Compare boxes with a correlation-preserving representation on exactly the same hybrid model. A generic Taylor-model implementation would be an engineering extension; a new property-directed splitting rule with established guarantees and demonstrated advantages could be research.

*Converter verification is already a mature application.* Johnson, Hong, and Kapoor applied reachability/model checking to switching converters in 2012. Hossain, Dhople, and Johnson studied closed-loop buck converters, including hysteresis, in 2013. Beg and colleagues combined uncertain-parameter hybrid models, reachability, and experimental validation of a 200 W buck prototype in 2017 [12–14]. These are essential related work, not peripheral references.

The [current verification question](../../docs/CERTIFIED_BUCK_VERIFICATION_QUESTION.md) reports a midpoint, zero-delay/zero-jitter witness violating the proposed 0.65 V limit over 300–301 microseconds. That is existing repository evidence, not rerun here. Such an admissible witness can refute a universal property even when a complete uncertain-set PASS analysis is difficult. However, its validity remains conditional on the enclosing algorithm's soundness. Finite corners and point simulation should be used to challenge implementations or find witness candidates, not as equivalent competitors for proving a continuum property.

*Event sensitivity and completeness.* The saltation-matrix literature explains why perturbations in event time alter post-event sensitivity even when a reset map is simple [15]. This supports adding event-sensitive error propagation to BAB-CS. A small scalar root residual alone does not bound trajectory error; near grazing, the guard derivative can become small and timing sensitivity can grow sharply.

The inspected general event path first requires an endpoint bracket. Equal endpoint signs do not rule out two crossings inside a step, and grazing can lack a sign change entirely. This identifies an algorithmic coverage question, not a reproduced end-to-end event failure in this review. Guaranteed interpolation, interval guard evaluation, and explicit UNKNOWN/refinement behavior are appropriate directions. The general threshold locator and specialized buck mode engine must be assessed separately.

*Energy structure and DAE assumptions.* Circuit topology affects the DAE index and solver assumptions [16]. Port-Hamiltonian circuit formulations and splitting methods provide established ways to preserve energy structure [17]. A June 2026 preprint proposes an enhanced JR decomposition tailored to circuit MNA [18]. This is directly relevant to LC/RLC experiments but remains preprint evidence.

A passivity monitor checks a property after the step; structure-preserving integration attempts to enforce an appropriate discrete identity by construction. Compare both approaches, while reporting phase separately. Energy behavior alone cannot establish waveform accuracy. Expanding to higher-index circuits would need an explicit formulation and consistency analysis, not just more devices.

*Current external baselines.* The 2026 ARCH nonlinear report covers Ariadne, CORA, DynIbex, JuliaReach, KeYmaera X, and PRoTECT. Its linear report covers CORA and JuliaReach [19–20]. The reports deliberately avoid a universal ranking. Use them to select compatible baselines and benchmark conventions; do not infer that all tools support the exact BAB-CS request semantics or the same arithmetic guarantees.

**Ranked research directions.** Priority reflects fit to existing code, scientific value, and prerequisite cost; it is an assessment rather than a measured score.

| Priority | Research question and hypothesis | Smallest useful experiment | Baselines and success evidence |
|---|---|---|---|
| Prerequisite | Is the restricted certification chain sound throughout its admitted numeric domain? | Audit derived coefficients; add exact/high-precision scalar cases, scale changes, underflow/overflow, boundary guards, and invalid-domain rejection. | Independently computed solutions and a second validated implementation. No silent enclosure exclusions; explicit domain assumptions and proof obligations. |
| 1 | Can replay carry a defensible total-error budget without paying for a reference at every step? | Prove a result first for affine RC/RL and damped RLC, with fixed norms and scheduled transitions. Track anchor uncertainty separately from within-epoch discrepancy. | Current bound, always-reference mode, fixed replay, defect-based enclosure. Report error/upper-bound ratio, bound width, completed horizon, reference work, and failures. |
| 2 | Can event uncertainty be propagated tightly enough to improve hybrid decisions? | Controlled hysteretic buck cases varying threshold widths, delay, jitter, dwell time, and near-grazing trajectories. Add an explicit timer-based reference model for delay. | Current margin/branch scheme versus compatible SpaceEx/CORA/JuliaReach or validated event integration. Report missed events, timing enclosure width, branching, UNKNOWN causes, and cost. |
| 3 | Can property-directed refinement beat dynamics-width splitting? | Compare current coefficient-width ranking with output/energy sensitivity and guard-distance ranking on the same uncertain request families. | Equal partition budgets; boxes versus a correlation-preserving representation. Measure time to decision, unresolved fraction, memory, and enclosure width. |
| 4 | Can scheduling reference work improve the accuracy-cost frontier? | Compare fixed intervals with defect/age/event-sensitive scheduling; retain an unconditional maximum age and mandatory event checks. | Always-reference and fixed-replay controls; PI-style adaptation informed by [4]. Include tuning cost, rejected work, elapsed simulated time, and complete-process time. |
| 5 | Does preserving energy structure reduce fallback without sacrificing phase? | Add one suitable structure-preserving method on LC, damped RLC, and switched passive circuits. | Existing trapezoidal/BDF2 and supervised candidates. Joint phase, amplitude, energy-balance, residual, replay, and work results. |

For priority 1, a plausible paper claim is: *Under stated affine/index-1 and event assumptions, a replay controller maintains an explicit total-error enclosure and reduces independent reference work on declared workloads.* The theorem and the reduction both remain to be established. A proof only about the controller's recursive scalar is insufficient unless that scalar is linked to solution error.

For priority 2, nonzero delay is especially important: an admissible zero-delay counterexample can settle a FAIL without testing tightness across the full timing range. A successful current FAIL should not be mistaken for evidence that uncertain timing is efficiently enclosed.

For priority 3, validate witness candidates independently. A wide outer enclosure intersecting an unsafe set does not establish a realizable violation. Conversely, a verified violating witness can finish a universal-property refutation early; report time-to-counterexample separately from time-to-complete-flowpipe.

**Experimental design that would make a paper convincing.**

Use a frozen source snapshot and machine-readable cases with equations, state order, units, initial sets, fixed parameters versus time-varying inputs, guards, reset maps, dwell/delay rules, horizon, and property quantifiers. A dirty development tree can be studied, but its source identity must include the changes; the base commit alone does not identify it.

Maintain three separate comparisons: trajectory accuracy, formal property decisions, and model agreement with external simulation or measurement. For trajectory studies use analytic/manufactured solutions where possible and independently converged external results elsewhere. For property studies compare methods capable of the same quantifier and uncertainty semantics. ngspice remains valuable for semantic/model checks, not as a proof of universal reachability.

Include RC, RL, damped RLC, neutral LC, non-normal affine coupling, nonlinear diode cases, frequent scheduled events, paired crossings, grazing, simultaneous guards, uncertain buck timing, and budget exhaustion. Vary horizon, stiffness, damping, uncertainty width, and event density independently. The [nonlinear-authority document](../../docs/INDEPENDENT_NONLINEAR_AUTHORITY.md) already records a useful adverse case: small residuals with failed refinement/cross-method gates. Preserve such unavailable rows.

Use paired ablations of correction, reference frequency, replay refinement, event verification, set representation, and split policy in a research harness. Any removal of safeguards should be identified as an experimental ablation, not a supported operating mode. Separate exploratory tuning cases from evaluation cases.

Report complete-process time, kernel time, memory, deterministic work, failures, and UNKNOWN outcomes. Repeated timing should include variability and hardware/backend versions. A native point solver, a corner campaign, and a certified set solver answer different questions; their speed ratios describe workload costs, not interchangeable solver capability.

**Suggested sequence.**

1. First, document and repair the reproduced arithmetic failure, audit the admitted certification domain, reconcile the stale roadmap, and freeze a compact evidence snapshot.
2. Then build the affine error-budget theorem and benchmark it before adding nonlinear claims.
3. Next, add adversarial event cases and translate one exact buck model into an independent verification tool.
4. Finally, evaluate property-directed splitting and replay scheduling. Pursue structure-preserving methods if the phase/energy data justify that branch.

These are work packages, not calendar promises. More transistor models, general higher-index support, learned proposal methods, or a full native rewrite are lower priorities until one of the central research questions has a defensible result.

**Annotated reading list.**

| Ref. | Source | Why read it / evidence boundary |
|---|---|---|
| 1 | Mehmood et al. (2022), [The Black-Box Simplex Architecture for Runtime Assurance of Autonomous CPS](https://doi.org/10.1007/978-3-031-06773-0_12) | Closest supervisory-architecture precedent. Its control safety theorem is not a numerical error theorem. |
| 2 | Sheikhi et al., [The Black-Box Simplex Architecture for Runtime Assurance of Multi-Agent CPS](https://www3.cs.stonybrook.edu/~stoller/papers/black-box-simplex-2024.pdf) | Author manuscript, 2024 filename; runtime checking and blending. Not counted as wholly independent evidence from [1]. |
| 3 | [An adaptive, provable correct simplex architecture](https://link.springer.com/article/10.1007/s10009-025-00779-0) (2025) | Recoverable regions and proofs on demand; useful precedent for reducing fallback use. |
| 4 | Söderlind (2003), [Digital filters in adaptive time-stepping](https://doi.org/10.1145/641876.641877) | Feedback design for numerical adaptation; useful scheduling baseline. |
| 5 | Estep (1995), [A Posteriori Error Bounds and Global Error Control for Approximation of Ordinary Differential Equations](https://doi.org/10.1137/0732001) | Global-error theory, including contractive problems. Publisher abstract inspected. |
| 6 | Cao and Petzold (2004), [A Posteriori Error Estimation and Global Error Control for Ordinary Differential Equations by the Adjoint Method](https://doi.org/10.1137/S1064827503420969) | Sensitivity-weighted error estimation. Author manuscript inspected; estimation must not automatically be called enclosure. |
| 7 | Neumaier (1993 manuscript), [Global, rigorous and realistic bounds for the solution of dissipative differential equations. Part I: Theory](https://arnold-neumaier.at/ms/ode.pdf) | Logarithmic norms, differential inequalities, and rigorous propagation bounds. |
| 8 | Frehse et al. (2011), [SpaceEx: Scalable Verification of Hybrid Systems](http://www-verimag.imag.fr/%7Etdang/Papers/CAV2011.pdf) | Piecewise-affine reachability and external comparison context. |
| 9 | Chen, Ábrahám, and Sankaranarayanan (2013), [Flow*: An Analyzer for Non-Linear Hybrid Systems](https://plv.colorado.edu/papers/flowstar-cav13.pdf) | Taylor flowpipes, guards, and aggregation. |
| 10 | Bouissou, Chapoutot, and Mimram, [Computing Flow Pipe of Nonlinear Hybrid Systems](https://www.lix.polytechnique.fr/Labo/Samuel.Mimram/docs/mimram_flowpipe.pdf) | HySon's guaranteed interpolation and event detection. Year omitted because it was not confirmed in fetched material. |
| 11 | Neher, Jackson, and Nedialkov, [On Taylor Model Based Integration of ODEs](https://doi.org/10.1137/050638448) | Dependency/wrapping analysis; publisher abstract inspected, not the full proof. |
| 12 | Johnson, Hong, and Kapoor (2012), [Design Verification Methods for Switching Power Converters](http://www.taylortjohnson.com/research/johnson2012peci.pdf) | Early converter reachability and the distinction between spurious intersections and violations. |
| 13 | Hossain, Dhople, and Johnson (2013), [Reachability Analysis of Closed-Loop Switching Power Converters](https://doi.org/10.1109/PECI.2013.6506047) | Direct hysteretic-buck predecessor. |
| 14 | Beg, Abbas, Johnson, and Davoudi (2017), [Model Validation of PWM DC–DC Converters](https://doi.org/10.1109/TIE.2017.2688961) | Essential application baseline: uncertain parameters, hybrid modes, and experimental conformance. |
| 15 | Kong, Payne, Zhu, and Johnson (2024; 2023 preprint), [Saltation Matrices: The Essential Tool for Linearizing Hybrid Dynamical Systems](https://doi.org/10.1109/JPROC.2024.3440211) | Event-time sensitivity and conditions under which smooth linearization fails. Preprint text inspected. |
| 16 | Tischendorf (1998), [Topological index-calculation of DAEs in circuit simulation](https://doi.org/10.1002/zamm.199807815118) | Topological assumptions for circuit DAEs. Issue year differs from the later online-posting date. |
| 17 | [Dynamic iteration schemes and port-Hamiltonian formulation in coupled differential-algebraic equation circuit simulation](https://doi.org/10.1002/cta.2870) (2021) | Circuit structure and subsystem coupling. |
| 18 | Bartel and Diab (2026), [Structure-Preserving Operator Splitting via JR-Decomposition for Circuit Models](https://arxiv.org/abs/2606.06153) | Recent MNA-specific approach; explicitly a preprint. |
| 19 | Geretti et al. (2026), [ARCH-COMP26: Continuous and Hybrid Systems with Nonlinear Dynamics](https://doi.org/10.29007/f5l7) | Current benchmark/tool landscape; proceedings record published July 3, distinct from workshop date. |
| 20 | [ARCH-COMP26: Continuous and Hybrid Systems with Linear Continuous Dynamics](https://eraw.easychair.org/publications/paper/hFjB/download) (2026) | Current linear verification comparisons and compatible baseline candidates. |

**Review artifacts and validation.** [search-log.json](search-log.json) records queries, requested counts, titles, and URLs without copying paper text. [reproduce_affine_underflow.py](reproduce_affine_underflow.py) preserves the confirmed defect. The reproducer ran successfully and the existing 11 reachability tests passed. No full-suite, release, performance, or external-tool campaign was run, and no existing source or documentation was changed.
