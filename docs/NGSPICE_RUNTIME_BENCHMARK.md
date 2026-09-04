# BAB-CS versus ngspice Runtime Benchmark

This report records a same-machine comparison between Bounded-Authority-Based Circuit Simulation (BAB-CS) and ngspice. The horizontal size coordinate is the model-declared Modified Nodal Analysis (MNA) count: BAB-CS dynamic states plus BAB-CS algebraic unknowns for the shared physical case. It keeps one case at the same horizontal position in both chart panels; it does not imply that ngspice assembles the same internal equation count. ngspice's own `Circuit Equations` value remains recorded separately. Resident set size (RSS) is the peak physical memory retained by a process.

![BAB-CS speedup versus ngspice with accuracy beside it](../artifacts/runtime/speedup-accuracy-by-size.svg)

Above `1×` means BAB-CS was faster for the measured row. Lower trajectory error is better. Timing never overrides failed accuracy, convergence, or semantic mapping.

## Equal-Accuracy Development Update — August 28, 2026

The retained publication table below is the earlier shared-timestep baseline. A
new bounded development run independently selected each tool's maximum timestep
against the same scaled trajectory-error target of 1. This is called
**fixed-accuracy comparison**: the circuit and stop time remain identical, but
each simulator may use the coarsest tested maximum timestep that still satisfies
the common accuracy requirement.

The new `active_heun_deferred4_smooth` BAB-CS profile uses **Heun's method**, a
two-stage predictor-corrector method, for smooth resistor-capacitor (`RC`),
resistor-inductor (`RL`), and coupled RC circuits. It computes an implicit
trapezoidal reference at least every four accepted steps instead of every step.
The profile remains active and bounded: embedded error, recursive bounds,
reference checkpoints, fallback, rejection, and periodic replay remain enabled.

| Family | Size | Prior BAB-CS divisor | New divisor | BAB-CS runtime gain | New speedup vs ngspice |
| --- | ---: | ---: | ---: | ---: | ---: |
| `rc_bank` | 1 | 64 | 1 | 5.28× | 0.110× |
| `rc_bank` | 4 | 64 | 1 | 5.13× | 0.079× |
| `rc_bank` | 16 | 64 | 1 | 5.24× | 0.060× |
| `rl_bank` | 1 | 32 | 1 | 2.96× | 0.130× |
| `rl_bank` | 4 | 32 | 1 | 2.94× | 0.104× |
| `rl_bank` | 16 | 32 | 1 | 2.73× | 0.073× |
| `coupled_rc_ring` | 1 | 32 | 1 | 4.20× | 0.170× |
| `coupled_rc_ring` | 4 | 128 | 1 | 9.63× | 0.601× |
| `coupled_rc_ring` | 16 | 128 | 1 | 9.32× | 0.409× |

A divisor of 1 means BAB-CS met the target at the baseline maximum timestep. All
nine rows met the common target for both tools and proved that the source and
installed-wheel trajectories were equivalent. The values use zero warm-ups and
one timed repeat, so they identify engineering direction rather than publication
medians. The retained reports are under
`artifacts/runtime/fixed-accuracy-optimized-quick/`; the runtime-gain column
comes from the exploratory profile scan, while the speedup column comes from the
retained optimized rerun.

The scheduled switched-RC profile retained Adams-Bashforth second-order (`AB2`),
a two-step explicit candidate method, and deferred ordinary references to every
four accepted steps. BAB-CS then qualified at divisor 16 with scaled error
0.995. The row remains unavailable because ngspice exceeded the bounded
calibration budget before qualifying. The diode row also remains unavailable:
its independently refined authorities differ by scaled error 6.155, above the
allowed convergence cap of 0.25.

The next highest-gain work is not another backend change, and the internal bound
must not yet be tightened. A runtime-profile extension of the Bound Coverage
Atlas found empirical external-authority coverage of 93.4% for the
resistor-capacitor (`RC`) bank, 95.5% for the resistor-inductor (`RL`) bank,
85.6% for the coupled RC ring, and 52.9% for the switched RC case. The diode
authority remains unavailable because its two refinements disagree by scaled
error 6.155 against a cap of 0.25.

The new decomposition shows that normalized circuit residuals are negligible:
their maximum contribution is `8.88e-8`. Propagated prior uncertainty reaches
91.72 and embedded Heun-versus-Euler deviation reaches 17.14. However, all 13
eligible full-reference transfers remain uncovered against external trajectory
authority because the recursive bound is internal and reference-relative: a
reference solve can reset the internal recurrence without proving that the
reference method has zero discretization error.

The first correction experiment added a separately named, default-off
dual-resolution term. It compares one full trapezoidal reference step with two
half steps and carries the discrepancy across partial and full authority
transfers. Same-source size-one evidence found only a 0.15-percentage-point RC
coverage gain, no RL gain, and a 7.47-percentage-point coupled-RC gain obtained
only after the uncertainty grew above 500,000 scaled units. Deterministic work
increased by approximately 8% to 10%, and reference solve count tripled.

The local estimator is therefore **not promoted**. The runtime profiles and
deferred bound cap remain unchanged. The next highest-gain experiment is an
offline global dual-trajectory qualification that advances independent coarse
and refined references over the complete output-time sequence and compares
their accumulated drift with analytic or independently qualified authority. The
baseline atlas is under `artifacts/atlas/runtime-scaling-optimized/`; the failed
local experiment is retained under `artifacts/atlas/runtime-dual-reference/`.

That global experiment is now also retained. Raw factor-2-versus-factor-4 drift
raises total empirical coverage to 100.00% for RC, 100.00% for RL, and 93.77%
for the coupled RC ring. However, the added uncertainty is respectively 582,
399, and 747 times the actual authority drift at the median eligible sample.
The global estimator itself covers only 95.24%, 94.83%, and 93.00% of refined
reference error without an added safety factor. It is more stable than the local
recursive term but remains too vacuous for promotion.

The declared refinement-pair sweep is now complete. It evaluates factor pairs
2/4, 4/8, 8/16, and 16/32 with safety factors 1 through 16 for RC, RL, and
coupled RC cases at sizes 1, 4, and 16. The raw factor-2/4 policy retains the
highest worst-case total coverage, 93.77%, but its worst median uncertainty is
1,033.12 times actual authority drift. Factor 16/32 reduces that worst median to
31.15 times but lowers worst-case total coverage to 83.40% and increases maximum
pair work to 67,584 unweighted solver events and iterations. No common policy is
both informative and reliably covering, so none is promoted.

This result also clarifies the circuit-scaling deficiency. Repeated RC and RL
banks are replication-throughput controls: increasing channel count expands the
system but does not add new coupled dynamics. The atlas work counter records how
many solver events occur, not how expensive each larger matrix operation is. It
can therefore remain constant as circuit dimension grows and must not be read as
a runtime or floating-point-operation scaling measure. The coupled RC ring adds
genuine modes, but broader coupled nonlinear, switching, and oscillatory
families are still required.

The next highest-gain experiment is order-aware reference qualification. It
will use at least three refinement levels to estimate observed convergence order,
require an asymptotic regime before extrapolation, and identify interpolation or
solve floors instead of masking them with a tuned family-specific safety factor.
The single-pair evidence is retained under
`artifacts/atlas/runtime-global-dual-trajectory/`; the multi-pair evidence is
retained under `artifacts/atlas/runtime-global-refinement-pair-sweep/`.

That order-aware experiment is now complete and retained under
`artifacts/atlas/runtime-global-order-aware/`. Pointwise observed-order gating
reduces median uncertainty inflation to approximately 1.7–2.3 times actual
finest-reference error, but only about 45–52% of the worst-case samples qualify.
Grouping samples by BAB-CS anchor epoch raises the worst common qualified-sample
fraction to 69–83% with median inflation of approximately 1.4–1.7 times, but
effective reference-estimator coverage remains only 39–54%. A maximum-discrepancy
epoch envelope raises reference coverage but also raises median inflation to
roughly 3–10 times and tail inflation as high as about 164 times. All rejected
epochs remain uncovered. No order-aware variant is promoted.

The signed statewise four-level experiment is now complete and retained under
`artifacts/atlas/runtime-global-statewise-four-level/`. It preserves each
state's error direction, compares adjacent observed orders, checks leading-error
coefficient stability, and compares two adjacent extrapolated trajectories. A
sample qualifies only when every state passes every gate.

| Common four-level policy | Minimum sample qualification | Minimum state qualification | Minimum effective reference coverage | Worst median inflation | Worst p95 inflation |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2/4/8/16 | 0.00% | 3.28% | 0.00% | 3.63x | 33.28x |
| 4/8/16/32 | 0.22% | 1.70% | 0.22% | 3.94x | 97.39x |

Only 292 of 14,238 eligible sample-policy evaluations qualified. Signed
difference inconsistency caused 74,173 state rejections, while only 287 state
rejections reached a direct numerical-difference floor. Nearly every adaptive
BAB-CS sample required interpolation from at least one refined trajectory, but
the 18 evaluations at common native endpoints also failed sign or order gates.
Interpolation therefore contributes to the problem but does not explain it
alone. The stronger scaling failure is the joint-state requirement: as coupled
state count grows, one unstable state rejects the complete system sample. No
statewise four-level policy is promoted.

The epoch-aligned statewise experiment is now complete and retained under
`artifacts/atlas/runtime-global-statewise-epoch/`. Each refinement integrates
with 2, 4, 8, 16, or 32 local substeps inside every BAB-CS diagnostic interval,
so every comparison is native without collapsing the refinement factors onto an
identical output grid. Redundant periodic replay is disabled for these already
implicit offline authorities, while forced event re-anchors remain available.

| Common four-level policy | Qualified epochs | Qualified state epochs | Qualified samples | Minimum effective reference coverage | Worst useful-case median inflation | Worst useful-case p95 inflation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2/4/8/16 | 13/483 | 85/3,630 | 193/7,119 | 0.00% | 1.00x | 16,532.33x |
| 4/8/16/32 | 49/483 | 412/3,630 | 725/7,119 | 0.00% | 1.00x | 2.60x |

The finer policy qualifies 12 of 40 RL epochs and 3 of 42 RC epochs across each
replicated size, but its reference-error estimates remain slightly below the
independent authority error and therefore cover none of those qualified samples
without an added safety multiplier. The size-one coupled RC ring reaches 1.69%
effective reference coverage. Coupled sizes 4 and 16 qualify no complete epoch,
even though 63 of 368 and 30 of 1,488 state epochs respectively qualify. The
common fail-closed frontier is empty. Native integration therefore proves that
interpolation was not the root cause; joint-state asymptotic instability remains.

The mode-aligned experiment is now complete and retained under
`artifacts/atlas/runtime-global-modal-epoch/`. It admits only homogeneous-unit,
smooth linear circuits with a symmetric differential Jacobian. A deterministic
Jacobi eigendecomposition must pass symmetry, residual, orthogonality, and sweep
limits. Repeated eigenvalues remain grouped, and reconstructed state errors use a
conservative absolute basis transform.

| Common four-level policy | Qualified joint epochs | Qualified modal-group epochs | Qualified samples | Minimum effective reference coverage | Worst reported median inflation | Worst reported p95 inflation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2/4/8/16 | 13/483 | 13/2,154 | 193/7,119 | 0.00% | 1.00x | 16,532.33x |
| 4/8/16/32 | 50/483 | 209/2,154 | 740/7,119 | 0.00% | 1.00x | 9.41x |

The finer modal policy adds one qualified size-four coupled RC epoch, covering 15
of 1,368 samples with 0.51% effective reference coverage and 0.88% effective
total coverage. Size 16 improves from 30 qualified state epochs to 96 qualified
modal-group epochs but still qualifies no complete system epoch. RC and RL
results remain unchanged, confirming invariance for their repeated subspaces.
The common fail-closed frontier remains empty, so no modal policy is promoted.

The temporally aligned modal experiment is now complete and retained under
`artifacts/atlas/runtime-global-temporal-modal-epoch/`. It permits a lag of at
most one diagnostic sample, only for scalar modal groups with one unique,
monotone, one-to-one zero-crossing match. Direction cosines use the common
retained interval; observed order, coefficient agreement, extrapolant residual,
error estimates, and reconstructed-state bounds remain unshifted.

| Common four-level policy | Qualified joint epochs | Qualified modal-group epochs | Qualified samples | Alignment attempts | Unique crossing matches | Alignments applied | Discarded endpoints |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2/4/8/16 | 13/483 | 13/2,154 | 193/7,119 | 1,861 | 1 | 0 | 3 |
| 4/8/16/32 | 50/483 | 209/2,154 | 740/7,119 | 1,844 | 3 | 0 | 6 |

Every qualification, coverage, and inflation result is identical to the
unshifted modal study. Under the finer policy, 1,400 attempted groups have no
crossing evidence, 304 exhibit sign chatter, 128 repeated modal subspaces retain
the unshifted fallback, and 9 have no one-to-one crossing match. The three
uniquely matched scalar groups still fail the aligned left-direction cosine
gate. The common fail-closed frontier remains empty, so the temporal policy is
not promoted.

The five-level two-term modal experiment is now complete and retained under
`artifacts/atlas/runtime-global-two-term-modal/`. Qualified Loop 5G groups keep
their existing estimate. Rejected groups fit
`Y_f = Y_inf + C f^-2 + D f^-q` with factors 2 through 16, while factor 32 is
excluded from fitting and used as the independent holdout. Secondary orders 3
and 4 are common policies across all nine cases.

| Common policy | Qualified joint epochs | Qualified modal-group epochs | Qualified samples | Loop 5G fallback groups | Fits attempted | Two-term fits qualified | Maximum training residual ratio | Maximum holdout residual ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `p=2, q=3` | 50/483 | 209/2,154 | 740/7,119 | 209 | 1,945 | 0 | 4.93 | 1,573.78 |
| `p=2, q=4` | 50/483 | 209/2,154 | 740/7,119 | 209 | 1,945 | 0 | 4.76 | 2,025.41 |

The deterministic condition numbers, 230.85 and 269.69, remain below the common
limit of 1,000. Conditioning is therefore not the failure. For both policies,
1,656 groups fail the training-residual gate. The factor-32 holdout rejects 242
additional `q=3` groups and 232 `q=4` groups. No rejected Loop 5G group is
recovered, every coverage and inflation result remains unchanged, and the common
fail-closed frontier remains empty. The two-term policies are not promoted.

The next highest-gain diagnostic is a finer-level asymptotic-entry ladder. It
will add native factors 64 and 128, test one-term modal policies ending at each
new level, and repeat the two-term fit with factor 128 reserved as the holdout.
This directly tests whether factor 32 remains pre-asymptotic, while publishing
the added integration work and every numerical-floor rejection instead of
relaxing a residual gate or tuning a family-specific multiplier.

## Retained Fixed-Config Publication Results

The following table is the earlier publication-profile, shared-timestep
baseline. It remains useful as historical fixed-configuration evidence, but it
does not represent the optimized fixed-accuracy profile described above.

| Case | Family | Size | MNA unknowns | Status | BAB-CS median (s) | ngspice median (s) | Speedup × | BAB-CS scaled error | ngspice scaled error |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| rc_bank-n001 | rc_bank | 1 | 5 | success | 0.00944445 | 0.000628621 | 0.0665598 | 401.884 | 23.593 |
| rc_bank-n002 | rc_bank | 2 | 8 | success | 0.0107041 | 0.000634121 | 0.0592412 | 401.884 | 23.593 |
| rc_bank-n004 | rc_bank | 4 | 14 | success | 0.013238 | 0.000646564 | 0.0488415 | 401.884 | 23.593 |
| rc_bank-n008 | rc_bank | 8 | 26 | success | 0.0196408 | 0.000673314 | 0.0342813 | 401.884 | 23.593 |
| rc_bank-n016 | rc_bank | 16 | 50 | success | 0.0367185 | 0.000732295 | 0.0199435 | 401.884 | 23.593 |
| rc_bank-n032 | rc_bank | 32 | 98 | success | 0.0912027 | 0.000832661 | 0.00912978 | 401.884 | 23.593 |
| rc_bank-n064 | rc_bank | 64 | 194 | success | 0.291845 | 0.00104237 | 0.00357165 | 401.884 | 23.593 |
| rl_bank-n001 | rl_bank | 1 | 4 | success | 0.00921964 | 0.000650392 | 0.0705442 | 379.119 | 23.4069 |
| rl_bank-n002 | rl_bank | 2 | 6 | success | 0.0101999 | 0.000658237 | 0.0645337 | 379.119 | 23.4069 |
| rl_bank-n004 | rl_bank | 4 | 10 | success | 0.0118644 | 0.000672633 | 0.0566933 | 379.119 | 23.4069 |
| rl_bank-n008 | rl_bank | 8 | 18 | success | 0.0157166 | 0.000714491 | 0.0454608 | 379.119 | 23.4069 |
| rl_bank-n016 | rl_bank | 16 | 34 | success | 0.0253709 | 0.000784782 | 0.0309324 | 379.119 | 23.4069 |
| rl_bank-n032 | rl_bank | 32 | 66 | success | 0.0539536 | 0.000922087 | 0.0170904 | 379.119 | 23.4069 |
| rl_bank-n064 | rl_bank | 64 | 130 | success | 0.17097 | 0.00120273 | 0.00703473 | 379.119 | 23.4069 |
| diode_rc_bank-n001 | diode_rc_bank | 1 | 5 | success | 0.0325329 | 0.00100245 | 0.0308135 | 7819.57 | 6896.65 |
| diode_rc_bank-n002 | diode_rc_bank | 2 | 8 | success | 0.0452995 | 0.0010301 | 0.0227398 | 7819.57 | 6896.65 |
| diode_rc_bank-n004 | diode_rc_bank | 4 | 14 | success | 0.0735071 | 0.00108279 | 0.0147304 | 7819.57 | 6896.65 |
| diode_rc_bank-n008 | diode_rc_bank | 8 | 26 | success | 0.165712 | 0.00119101 | 0.00718724 | 7819.57 | 6896.65 |
| diode_rc_bank-n016 | diode_rc_bank | 16 | 50 | success | 0.529582 | 0.00139088 | 0.00262637 | 7819.57 | 6896.65 |
| diode_rc_bank-n032 | diode_rc_bank | 32 | 98 | success | 2.31809 | 0.00179484 | 0.000774277 | 7819.57 | 6896.65 |
| diode_rc_bank-n064 | diode_rc_bank | 64 | 194 | success | 12.7876 | 0.00261811 | 0.000204738 | 7819.57 | 6896.65 |
| switched_rc_bank-n001 | switched_rc_bank | 1 | 6 | success | 0.0104565 | 0.000895806 | 0.0856697 | 9655.58 | 9899.94 |
| switched_rc_bank-n002 | switched_rc_bank | 2 | 10 | success | 0.0132709 | 0.000915242 | 0.0689659 | 9653.94 | 9899.94 |
| switched_rc_bank-n004 | switched_rc_bank | 4 | 18 | success | 0.0177245 | 0.000963402 | 0.0543542 | 9653.94 | 9899.94 |
| switched_rc_bank-n008 | switched_rc_bank | 8 | 34 | success | 0.029396 | 0.00104904 | 0.0356865 | 9653.94 | 9899.94 |
| switched_rc_bank-n016 | switched_rc_bank | 16 | 66 | success | 0.0645797 | 0.00120418 | 0.0186464 | 9653.94 | 9899.94 |
| switched_rc_bank-n032 | switched_rc_bank | 32 | 130 | success | 0.193123 | 0.00152802 | 0.00791215 | 9653.94 | 9899.94 |
| switched_rc_bank-n064 | switched_rc_bank | 64 | 258 | success | 0.780528 | 0.00225641 | 0.00289088 | 9653.94 | 9899.94 |
| rc_step | — | — | 5 | success | 0.00117379 | 0.000241288 | 0.205563 | 868.923 | 37.9744 |
| rc_discharge | — | — | 3 | success | 0.00846995 | 0.000619442 | 0.0731341 | 19.7138 | 5.9283 |
| driven_rc | — | — | 5 | success | 0.0175035 | 0.000977578 | 0.0558504 | 6848.59 | 381.693 |
| current_driven_rc | — | — | 3 | success | 0.0204109 | 0.00103566 | 0.0507406 | 2767.5 | 261.593 |
| rl_step | — | — | 4 | success | 0.00117793 | 0.000251337 | 0.213372 | 787.822 | 37.4763 |
| rl_decay | — | — | 2 | success | 0.0132628 | 0.000961558 | 0.0725002 | 19.8478 | 8.79759 |
| lc_long | — | — | 4 | success | 0.356588 | 0.0100556 | 0.0281995 | 8934.88 | 9928.92 |
| lc_offset | — | — | 4 | success | 0.140716 | 0.00507391 | 0.0360578 | 1270.58 | 10242.1 |
| rlc_damped | — | — | 4 | success | 0.0379399 | 0.00117144 | 0.0308762 | 3726 | 8938.68 |
| rlc_overdamped | — | — | 4 | success | 0.020308 | 0.000964434 | 0.0474903 | 6097.47 | 940.378 |
| rlc_driven | — | — | 7 | success | 0.14203 | 0.00355237 | 0.0250114 | 473.21 | 255.55 |
| diode_clip | — | — | 5 | success | 0.0751269 | 0.00224355 | 0.0298635 | 3134.89 | 224.54 |
| diode_rectifier | — | — | 6 | success | 0.286595 | 0.0083782 | 0.0292336 | 54.0649 | 214.644 |
| diode_bias_recovery | — | — | 5 | success | 0.120965 | 0.0043109 | 0.0356376 | 41.7189 | 299.271 |
| switched_rc | — | — | 5 | success | 0.0142059 | 0.000831427 | 0.058527 | 9481.29 | 7109.62 |
| switched_rl | — | — | 5 | success | 0.0820105 | 0.00265859 | 0.0324177 | 30.7663 | 3161.31 |
| switched_rlc | — | — | 8 | success | 0.244519 | 0.00335301 | 0.0137127 | 11351.2 | 11476.4 |
| buck_like_reduced_order | — | — | 7 | success | 0.0942436 | 0.00366604 | 0.0388996 | 261.528 | 3198.53 |
| h_bridge_rl_reduced_order | — | — | 6 | success | 0.0778088 | 0.00405196 | 0.0520758 | 10032.1 | 10001.2 |
| dc_link_rlc_reduced_order | — | — | 8 | success | 0.0726296 | 0.00251481 | 0.0346251 | 651.722 | 3166.67 |

## Measurement Contract

- Machine: `AMD Ryzen 9 7900X 12-Core Processor` on `7.1.3-2-cachyos`.
- Profile: `publication` with 5 warmups, 15 repeats, and 3 rounds.
- Accuracy grid: 201 shared samples with absolute tolerance `1e-08` and relative tolerance `0.0001`.
- BAB-CS wheel SHA-256: `ca5d648e60dfd9923deadc85fb304b45dc9ecf87aecc982a369d3766542806f2`.
- ngspice: `ngspice-46 : Circuit level simulation program`.
- Runtime: analysis-only medians use BAB-CS `perf_counter_ns` timing around `Simulator.run` and ngspice `Total analysis time (seconds)` from `rusage all`.
- Memory: both fresh child processes use GNU Time maximum RSS in kibibytes.

## Claim Boundary

Runtime evidence characterizes one recorded machine and software snapshot. It is not a universal speed or correctness claim, and ngspice is not treated as an exact physical oracle.
