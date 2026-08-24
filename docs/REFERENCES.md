# BAB-CS References

This bibliography separates external foundations from repository evidence. The
external sources explain the established numerical-analysis, sparse-linear-
algebra, and circuit-simulation context. The repository sources define what
BAB-CS actually implements and what it is permitted to claim.

## External Foundations

<a id="ref-1"></a>
1. C.-W. Ho, A. E. Ruehli, and P. A. Brennan, “The Modified Nodal Approach to
   Network Analysis,” *IEEE Transactions on Circuits and Systems*, vol. 22,
   no. 6, pp. 504–509, 1975. DOI:
   [10.1109/TCS.1975.1084079](https://doi.org/10.1109/TCS.1975.1084079).

<a id="ref-2"></a>
2. L. W. Nagel, *SPICE2: A Computer Program to Simulate Semiconductor
   Circuits*, Technical Report UCB/ERL M520, University of California,
   Berkeley, 1975.
   [Berkeley report record](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1975/9602.html).

<a id="ref-3"></a>
3. G. G. Dahlquist, “A Special Stability Problem for Linear Multistep
   Methods,” *BIT Numerical Mathematics*, vol. 3, pp. 27–43, 1963. DOI:
   [10.1007/BF01963532](https://doi.org/10.1007/BF01963532).

<a id="ref-4"></a>
4. P. Bogacki and L. F. Shampine, “A 3(2) Pair of Runge–Kutta Formulas,”
   *Applied Mathematics Letters*, vol. 2, no. 4, pp. 321–325, 1989. DOI:
   [10.1016/0893-9659(89)90079-7](https://doi.org/10.1016/0893-9659(89)90079-7).

<a id="ref-5"></a>
5. L. F. Shampine and P. Bogacki, “The Effect of Changing the Stepsize in
   Linear Multistep Codes,” *SIAM Journal on Scientific and Statistical
   Computing*, vol. 10, no. 6, pp. 1010–1023, 1989. DOI:
   [10.1137/0910060](https://doi.org/10.1137/0910060).

<a id="ref-6"></a>
6. E. Eich, “Convergence Results for a Coordinate Projection Method Applied to
   Mechanical Systems with Algebraic Constraints,” *SIAM Journal on Numerical
   Analysis*, vol. 30, no. 5, pp. 1467–1482, 1993. DOI:
   [10.1137/0730076](https://doi.org/10.1137/0730076).

<a id="ref-7"></a>
7. J. W. Demmel, S. C. Eisenstat, J. R. Gilbert, X. S. Li, and J. W. Liu,
   “A Supernodal Approach to Sparse Partial Pivoting,” Technical Report
   UCB/CSD-95-883, 1995.
   [Netlib report](https://www.netlib.org/lapack/lawnspdf/lawn103.pdf).

<a id="ref-8"></a>
8. H. Vogt, G. Atkinson, D. Warning, P. Nenzi, and contributors,
   *Ngspice User’s Manual*.
   [Official manual](https://ngspice.sourceforge.io/docs/ngspice-html-manual/manual.xhtml).

<a id="ref-9"></a>
9. SciPy developers, “`scipy.sparse.linalg.splu`.”
   [SciPy API documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.splu.html).

<a id="ref-10"></a>
10. Python Packaging Authority, “Binary Distribution Format.”
    [Python packaging specification](https://packaging.python.org/en/latest/specifications/binary-distribution-format/).

## Repository Foundations

<a id="ref-11"></a>
11. [Project overview and command reference](../README.md).

<a id="ref-12"></a>
12. [BAB-CSv1 normative specification](BAB_CSV1_SPEC.md).

<a id="ref-13"></a>
13. [BAB-CSv1 error-bound model](ERROR_BOUND_MODEL.md).

<a id="ref-14"></a>
14. [Bounded candidate integrators](BOUNDED_CANDIDATES.md).

<a id="ref-15"></a>
15. [Comparison protocol](COMPARISON_PROTOCOL.md).

<a id="ref-16"></a>
16. [External comparison protocol and results](EXTERNAL_COMPARISON.md).

<a id="ref-17"></a>
17. [Performance optimization audit](PERFORMANCE_OPTIMIZATION_AUDIT.md).

<a id="ref-18"></a>
18. [Tests and comparisons qualification audit](TESTS_AND_COMPARISONS_AUDIT.md).

<a id="ref-19"></a>
19. [Release qualification plan](../BAB-CS-Release-Qualification-Plan.md).

<a id="ref-20"></a>
20. [Release qualification implementation audit](RELEASE_QUALIFICATION_IMPLEMENTATION_AUDIT.md).

<a id="ref-21"></a>
21. [Draft release document](../RELEASE.md).

<a id="ref-22"></a>
22. [Canonical benchmark manifest](../benchmarks/manifest.json).

<a id="ref-23"></a>
23. [Bounded controller implementation](../src/babcs/bounded.py).

<a id="ref-24"></a>
24. [Candidate-integrator implementation](../src/babcs/candidates.py).

<a id="ref-25"></a>
25. [Circuit model and algebraic projection implementation](../src/babcs/model.py).

<a id="ref-26"></a>
26. [Implicit integrators and replay implementation](../src/babcs/integrators.py).

<a id="ref-27"></a>
27. [Dense and optional sparse linear-algebra implementation](../src/babcs/linalg.py).

<a id="ref-28"></a>
28. [Simulation loop and event handling](../src/babcs/simulator.py).

<a id="ref-29"></a>
29. [Deterministic comparison runner](../tools/compare_methods.py).

<a id="ref-30"></a>
30. [External ngspice comparison tool](../tools/compare_external.py).

<a id="ref-31"></a>
31. [Release evidence and verification tool](../tools/release_evidence.py).

<a id="ref-32"></a>
32. [Regression and qualification test suite](../tests/).

<a id="ref-33"></a>
33. [Continuous integration workflow](../.github/workflows/ci.yml),
    [scheduled comparison workflow](../.github/workflows/comparisons.yml), and
    [release qualification workflow](../.github/workflows/release-qualification.yml).

<a id="ref-34"></a>
34. [BAB-CSv1 completion audit](BAB_CSV1_COMPLETION_AUDIT.md).
