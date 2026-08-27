# BAB-CS Power-Stage Sandbox

> These are reduced-order numerical experiments, not production device models.

The sandbox contains three scheduled transient experiments built only from the
currently supported BAB-CS resistor, capacitor, inductor, independent-source,
Shockley-diode, and time-controlled resistive-switch semantics:

- `buck_like_reduced_order.json`
- `h_bridge_rl_reduced_order.json`
- `dc_link_rlc_reduced_order.json`

Each input records its educational purpose and omitted effects. The examples do
not model transistor charge, switching loss, body-diode recovery, magnetic
saturation, ESR/ESL, thermal behavior, EMI, control loops, protection systems,
or hardware safety. They are intended to exercise event alignment, continuity,
energy accounting, fallback, and independent replay in a bounded numerical
setting.

Run any case with:

```bash
PYTHONPATH=src python -m babcs simulate \
  examples/power_stage/buck_like_reduced_order.json \
  --csv /tmp/buck-trace.csv \
  --summary /tmp/buck-summary.json
```
