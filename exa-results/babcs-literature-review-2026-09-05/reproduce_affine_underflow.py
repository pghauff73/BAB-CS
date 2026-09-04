"""Review reproducer: an accepted affine endpoint excludes the exact solution.

Run from the repository root:
PYTHONPATH=src python exa-results/babcs-literature-review-2026-09-05/reproduce_affine_underflow.py
"""
from decimal import Decimal, localcontext

from babcs.intervals import Interval, IntervalBox
from babcs.reachability import AffineIntervalSystem, validated_affine_step

a, h, x0 = 1e161, 1e-162, 1e-30
system = AffineIntervalSystem.from_numeric(("x",), ((a,),), (0.0,))
result = validated_affine_step(
    system,
    IntervalBox(("x",), (Interval.point(x0),)),
    h,
    absolute_inflation=1e-45,
)
with localcontext() as context:
    context.prec = 80
    exact = Decimal.from_float(x0) * (
        Decimal.from_float(a) * Decimal.from_float(h)
    ).exp()
    endpoint = result.endpoint["x"]
    contained = Decimal.from_float(endpoint.lower) <= exact <= Decimal.from_float(endpoint.upper)
    print("computed Taylor coefficient:", 0.5 * h * h)
    print("returned endpoint:", endpoint)
    print("analytic endpoint (80-digit Decimal):", exact)
    print("analytic endpoint contained:", contained)
    assert not contained, "Original defect no longer reproduced; investigate the change."
