window.BABCS_DOCUMENTS = {
  "categories": [
    {
      "documents": [
        "index.md"
      ],
      "name": "Documentation Home"
    },
    {
      "documents": [
        "CURRENT_WORK.md",
        "NUMERICAL_METHODS_ESSAY.md",
        "ENGINEERING_AND_PERFORMANCE_ESSAY.md",
        "VALIDATION_RELEASE_AND_CLAIMS_ESSAY.md",
        "APPLICATIONS_AND_RESEARCH_ROADMAP.md",
        "REFERENCES.md"
      ],
      "name": "Current Work Essays"
    },
    {
      "documents": [
        "BAB_CSV1_SPEC.md"
      ],
      "name": "Start Here"
    },
    {
      "documents": [
        "ARCHITECTURE.md",
        "ERROR_BOUND_MODEL.md",
        "BOUNDED_CANDIDATES.md",
        "BOUNDED_NEWTON.md",
        "MINIMAL_REPRODUCIBLE_RESEARCH.md"
      ],
      "name": "Numerical Design"
    },
    {
      "documents": [
        "COMPARISON_PROTOCOL.md",
        "METHOD_OBSERVATORY.md",
        "BOUND_COVERAGE_ATLAS.md",
        "POWER_STAGE_SANDBOX.md",
        "TEACHING_AND_REPRODUCIBILITY_LAB.md",
        "NGSPICE_CASE_ATLAS.md",
        "NGSPICE_RUNTIME_BENCHMARK.md",
        "OBSERVATORY_ATLAS_SANDBOX_LAB_IMPLEMENTATION_AUDIT.md",
        "EXTERNAL_COMPARISON.md",
        "TESTS_AND_COMPARISONS_AUDIT.md",
        "PERFORMANCE_OPTIMIZATION_AUDIT.md",
        "QUALIFICATION_SUMMARY.md"
      ],
      "name": "Tests and Comparisons"
    },
    {
      "documents": [
        "TUTORIAL_SCIENTIFIC_RESULTS_REPORT.md",
        "tutorials/01_MNA_STATE_OWNERSHIP.md",
        "tutorials/02_CONVERGENCE_BY_REFINEMENT.md",
        "tutorials/03_PHASE_VERSUS_ENERGY.md",
        "tutorials/04_SHADOW_AUTHORITY.md",
        "tutorials/05_DETERMINISTIC_PACKAGING.md",
        "tutorials/06_SOURCE_WHEEL_EQUIVALENCE.md",
        "tutorials/07_EVENT_ALIGNMENT.md",
        "tutorials/08_EMPIRICAL_BOUND_COVERAGE.md",
        "tutorials/09_FALLBACK_AND_REJECTION_FORENSICS.md",
        "tutorials/10_SEMANTIC_NGSPICE_MAPPING.md"
      ],
      "name": "Teaching Lab Tutorials"
    },
    {
      "documents": [
        "BAB_CSV1_COMPLETION_AUDIT.md",
        "RELEASE_QUALIFICATION_IMPLEMENTATION_AUDIT.md",
        "LICENCE_DECISION.md"
      ],
      "name": "Qualification and Release"
    },
    {
      "documents": [
        "GITHUB_GOVERNANCE.md"
      ],
      "name": "Additional Documents"
    }
  ],
  "conceptGlossary": [
    {
      "aliases": [
        "OURD",
        "OURD Coding Agent"
      ],
      "definition": "The governed local advisory coding agent used to review evidence and propose changes without receiving final approval authority.",
      "id": "ourd",
      "term": "OURD Coding Agent"
    },
    {
      "aliases": [
        "BAB-CS",
        "BAB-CSv1",
        "Bounded-Authority-Based-Circuit-Simulation"
      ],
      "definition": "A circuit-simulation architecture where numerical methods may propose states, but independent checks control which state is accepted.",
      "id": "babcs",
      "term": "BAB-CS"
    },
    {
      "aliases": [
        "candidate method",
        "candidate methods",
        "candidate integrator",
        "candidate integrators"
      ],
      "definition": "The numerical formula that proposes the next capacitor voltages and inductor currents without approving its own result.",
      "id": "candidate-method",
      "term": "Candidate method"
    },
    {
      "aliases": [
        "numerical authority",
        "reference authority",
        "accepted-state authority"
      ],
      "definition": "The independent calculations and rules that decide whether a proposed timestep is accepted, corrected, recomputed, or rejected.",
      "id": "numerical-authority",
      "term": "Numerical authority"
    },
    {
      "aliases": [
        "projection",
        "projections"
      ],
      "definition": "A circuit-equation solve that restores node-voltage and branch-current consistency for a proposed dynamic state.",
      "id": "projection",
      "term": "Projection"
    },
    {
      "aliases": [
        "replay",
        "replays"
      ],
      "definition": "An independent recomputation of a recent interval from a trusted state, usually with a different implicit method and smaller internal steps.",
      "id": "replay",
      "term": "Replay"
    },
    {
      "aliases": [
        "anchor",
        "anchors"
      ],
      "definition": "A retained accepted state used as the starting point for an independent replay check.",
      "id": "anchor",
      "term": "Anchor"
    },
    {
      "aliases": [
        "recursive internal bound",
        "recursive internal bounds",
        "recursive bound",
        "recursive bounds"
      ],
      "definition": "A running estimate of how previously modeled numerical error and the newest local defect may combine.",
      "id": "recursive-bound",
      "term": "Recursive internal bound"
    },
    {
      "aliases": [
        "residual",
        "residuals"
      ],
      "definition": "The mismatch left when the circuit equations are evaluated at a computed solution.",
      "id": "residual",
      "term": "Residual"
    },
    {
      "aliases": [
        "Jacobian",
        "Jacobians"
      ],
      "definition": "A matrix of local sensitivities showing how each equation changes when each unknown changes.",
      "id": "jacobian",
      "term": "Jacobian"
    },
    {
      "aliases": [
        "Newton iteration",
        "Newton iterations",
        "Newton solve",
        "Newton solves",
        "Newton method",
        "Newton methods"
      ],
      "definition": "A repeated linearization process used to solve nonlinear equations such as diode circuit equations.",
      "id": "newton-iteration",
      "term": "Newton iteration"
    },
    {
      "aliases": [
        "nonlinear convergence",
        "converged nonlinear"
      ],
      "definition": "The condition reached when an iterative nonlinear solve satisfies its declared equation-mismatch and update tolerances.",
      "id": "nonlinear-convergence",
      "term": "Nonlinear convergence"
    },
    {
      "aliases": [
        "stiffness",
        "stiff"
      ],
      "definition": "The presence of fast and slow behavior together, which can force some numerical methods to use very small timesteps for stability.",
      "id": "stiffness",
      "term": "Stiffness"
    },
    {
      "aliases": [
        "passivity",
        "passive"
      ],
      "definition": "The physical rule that a passive declared model may not create net energy from nothing.",
      "id": "passivity",
      "term": "Passivity"
    },
    {
      "aliases": [
        "reduced-order model",
        "reduced-order models",
        "reduced-order numerical experiment",
        "reduced-order numerical experiments",
        "reduced-order"
      ],
      "definition": "A deliberately simplified model that retains only the behavior needed for the stated engineering question.",
      "id": "reduced-order-model",
      "term": "Reduced-order model"
    },
    {
      "aliases": [
        "deterministic evidence",
        "deterministic report",
        "deterministic output",
        "deterministic"
      ],
      "definition": "Evidence designed to repeat for the same declared source, configuration, and environment rather than depending on incidental execution order.",
      "id": "deterministic-evidence",
      "term": "Deterministic evidence"
    },
    {
      "aliases": [
        "fixed-step",
        "fixed timestep",
        "fixed-timestep"
      ],
      "definition": "A comparison in which methods use the same declared nominal advance in simulated time.",
      "id": "fixed-step",
      "term": "Fixed-step comparison"
    },
    {
      "aliases": [
        "fixed-accuracy"
      ],
      "definition": "A comparison that selects results against the same declared error target.",
      "id": "fixed-accuracy",
      "term": "Fixed-accuracy comparison"
    },
    {
      "aliases": [
        "fixed-work"
      ],
      "definition": "A comparison under the same deterministic operation budget rather than the same wall-clock time.",
      "id": "fixed-work",
      "term": "Fixed-work comparison"
    },
    {
      "aliases": [
        "phase error",
        "phase errors",
        "phase drift",
        "phase"
      ],
      "definition": "The timing shift of an oscillation relative to the chosen authority or expected waveform.",
      "id": "phase-error",
      "term": "Phase error"
    },
    {
      "aliases": [
        "energy drift",
        "energy error",
        "energy errors"
      ],
      "definition": "Numerical gain or loss of stored capacitor and inductor energy that is not caused by the declared model.",
      "id": "energy-drift",
      "term": "Energy drift"
    },
    {
      "aliases": [
        "empirical coverage",
        "coverage ratio"
      ],
      "definition": "The measured fraction of eligible samples for which an internal bound covered independently observed authority error.",
      "id": "empirical-coverage",
      "term": "Empirical coverage"
    },
    {
      "aliases": [
        "shadow mode",
        "shadow authority"
      ],
      "definition": "An observe-only mode where a candidate runs and records evidence while a trusted reference still owns the accepted state.",
      "id": "shadow-mode",
      "term": "Shadow mode"
    },
    {
      "aliases": [
        "fail closed",
        "fail-closed"
      ],
      "definition": "Refuse to produce an accepted result when required evidence, convergence, or support is missing.",
      "id": "fail-closed",
      "term": "Fail closed"
    },
    {
      "aliases": [
        "factorization",
        "factorisation",
        "refactor"
      ],
      "definition": "Rewriting a matrix into parts that make one or more equation solves more efficient.",
      "id": "factorization",
      "term": "Matrix factorization"
    },
    {
      "aliases": [
        "source-versus-wheel equivalence",
        "source and installed",
        "source-versus-installed"
      ],
      "definition": "A check that the source checkout and an isolated installation of the built Python package produce the same declared evidence.",
      "id": "source-wheel-equivalence",
      "term": "Source-versus-wheel equivalence"
    },
    {
      "aliases": [
        "Python wheel",
        "Python wheels",
        "wheel",
        "wheels"
      ],
      "definition": "An installable Python package file containing code and package metadata.",
      "id": "python-wheel",
      "term": "Python wheel"
    },
    {
      "aliases": [
        "RSS",
        "resident set size"
      ],
      "definition": "Resident set size: the physical memory occupied by a process at a measured time; maximum RSS records its observed peak.",
      "id": "rss",
      "term": "RSS"
    },
    {
      "aliases": [
        "GNU",
        "GNU Time"
      ],
      "definition": "The GNU Project's command-line utility for measuring process runtime and resource use, including maximum resident memory.",
      "id": "gnu-time",
      "term": "GNU Time"
    },
    {
      "aliases": [
        "MNA",
        "modified nodal analysis"
      ],
      "definition": "Modified nodal analysis: a standard way to turn a circuit into equations for node voltages and selected branch currents.",
      "id": "mna",
      "term": "MNA"
    },
    {
      "aliases": [
        "DAE",
        "DAEs",
        "differential-algebraic equation",
        "differential-algebraic equations"
      ],
      "definition": "Differential-algebraic equation: a model combining time-evolution equations with constraints that must hold immediately.",
      "id": "dae",
      "term": "DAE"
    },
    {
      "aliases": [
        "ODE",
        "ODEs",
        "ordinary differential equation",
        "ordinary differential equations"
      ],
      "definition": "Ordinary differential equation: an equation describing how a state changes with time without a separate algebraic constraint system.",
      "id": "ode",
      "term": "ODE"
    },
    {
      "aliases": [
        "SPICE",
        "SPICE2"
      ],
      "definition": "Simulation Program with Integrated Circuit Emphasis: a widely used family of circuit-simulation methods and tools.",
      "id": "spice",
      "term": "SPICE"
    },
    {
      "aliases": [
        "RC"
      ],
      "definition": "Resistor-capacitor: a circuit containing resistance and electrical energy storage in a capacitor.",
      "id": "rc",
      "term": "RC"
    },
    {
      "aliases": [
        "RL",
        "R-L"
      ],
      "definition": "Resistor-inductor: a circuit containing resistance and magnetic energy storage in an inductor.",
      "id": "rl",
      "term": "RL"
    },
    {
      "aliases": [
        "RLC"
      ],
      "definition": "Resistor-inductor-capacitor: a circuit containing resistance and both magnetic and electrical energy storage.",
      "id": "rlc",
      "term": "RLC"
    },
    {
      "aliases": [
        "LC",
        "C+L"
      ],
      "definition": "Inductor-capacitor: a circuit in which energy moves between magnetic and electrical storage.",
      "id": "lc",
      "term": "LC"
    },
    {
      "aliases": [
        "DC",
        "direct current"
      ],
      "definition": "Direct current: electrical voltage or current whose intended direction does not alternate periodically.",
      "id": "dc",
      "term": "DC"
    },
    {
      "aliases": [
        "PWL",
        "piecewise linear"
      ],
      "definition": "Piecewise linear: a waveform made from straight-line segments joined at declared breakpoints.",
      "id": "pwl",
      "term": "PWL"
    },
    {
      "aliases": [
        "KCL",
        "Kirchhoff current law",
        "Kirchhoff's current law"
      ],
      "definition": "Kirchhoff current law: current entering and leaving a circuit node must balance.",
      "id": "kcl",
      "term": "KCL"
    },
    {
      "aliases": [
        "AB2",
        "Adams-Bashforth order two",
        "Adams–Bashforth order two"
      ],
      "definition": "Adams-Bashforth order two: an explicit two-step method that predicts a new state from current and previous derivative information.",
      "id": "ab2",
      "term": "AB2"
    },
    {
      "aliases": [
        "AB",
        "Adams-Bashforth",
        "Adams–Bashforth"
      ],
      "definition": "Adams-Bashforth: a family of explicit multistep methods that predict a new state from stored derivative history.",
      "id": "adams-bashforth",
      "term": "AB"
    },
    {
      "aliases": [
        "AB3"
      ],
      "definition": "Adams-Bashforth order three: an explicit three-step proposal method using three derivative-history points.",
      "id": "ab3",
      "term": "AB3"
    },
    {
      "aliases": [
        "BE",
        "backward Euler"
      ],
      "definition": "Backward Euler: a first-order implicit method that solves an equation containing the new state.",
      "id": "be",
      "term": "BE"
    },
    {
      "aliases": [
        "BDF2",
        "backward differentiation formula order two"
      ],
      "definition": "Backward differentiation formula order two: a second-order implicit method that uses the current and previous accepted states.",
      "id": "bdf2",
      "term": "BDF2"
    },
    {
      "aliases": [
        "RK23",
        "Bogacki-Shampine",
        "Bogacki–Shampine"
      ],
      "definition": "A Runge-Kutta method with related second- and third-order results that can estimate local error.",
      "id": "rk23",
      "term": "RK23"
    },
    {
      "aliases": [
        "CSC",
        "compressed sparse column"
      ],
      "definition": "Compressed sparse column: a matrix format that stores nonzero values by column instead of storing every zero.",
      "id": "csc",
      "term": "CSC"
    },
    {
      "aliases": [
        "KLU",
        "SuiteSparse KLU"
      ],
      "definition": "A sparse linear solver designed for circuit-like matrices with repeated structure.",
      "id": "klu",
      "term": "KLU"
    },
    {
      "aliases": [
        "SuperLU"
      ],
      "definition": "A software library for factoring and solving sparse linear equation systems.",
      "id": "superlu",
      "term": "SuperLU"
    },
    {
      "aliases": [
        "SciPy"
      ],
      "definition": "A Python scientific-computing library that provides numerical algorithms and sparse matrix tools.",
      "id": "scipy",
      "term": "SciPy"
    },
    {
      "aliases": [
        "COLAMD"
      ],
      "definition": "Column approximate minimum degree: a matrix-ordering strategy intended to reduce extra nonzero work during sparse factorization.",
      "id": "colamd",
      "term": "COLAMD"
    },
    {
      "aliases": [
        "LRU",
        "least-recently-used"
      ],
      "definition": "Least recently used: a bounded cache policy that evicts the entry unused for the longest time.",
      "id": "lru",
      "term": "LRU"
    },
    {
      "aliases": [
        "RMS",
        "root-mean-square"
      ],
      "definition": "Root mean square: a way to combine several values by averaging their squares and then taking a square root.",
      "id": "rms",
      "term": "RMS"
    },
    {
      "aliases": [
        "WRMS",
        "weighted RMS",
        "weighted root-mean-square"
      ],
      "definition": "Weighted root mean square: an RMS measure after each component is scaled by its allowed tolerance.",
      "id": "wrms",
      "term": "WRMS"
    },
    {
      "aliases": [
        "ULP",
        "unit in the last place"
      ],
      "definition": "Unit in the last place: the gap between adjacent floating-point numbers near a value.",
      "id": "ulp",
      "term": "ULP"
    },
    {
      "aliases": [
        "JSON",
        "JavaScript Object Notation"
      ],
      "definition": "JavaScript Object Notation: a text format for structured data made from objects, arrays, numbers, strings, and booleans.",
      "id": "json",
      "term": "JSON"
    },
    {
      "aliases": [
        "CSV",
        "comma-separated values",
        "comma-separated-value"
      ],
      "definition": "Comma-separated values: a plain-text table format where each row is a line and columns are separated by commas.",
      "id": "csv",
      "term": "CSV"
    },
    {
      "aliases": [
        "SVG",
        "Scalable Vector Graphics"
      ],
      "definition": "Scalable Vector Graphics: a text-based vector image format that stays sharp when resized.",
      "id": "svg",
      "term": "SVG"
    },
    {
      "aliases": [
        "SHA-256",
        "SHA256",
        "SHA"
      ],
      "definition": "Secure Hash Algorithm: a cryptographic fingerprint family; BAB-CS evidence uses the 256-bit SHA-256 form to identify exact digital content.",
      "id": "sha256",
      "term": "SHA-256"
    },
    {
      "aliases": [
        "CI",
        "continuous integration"
      ],
      "definition": "Continuous integration: automated building and testing triggered by repository events.",
      "id": "ci",
      "term": "CI"
    },
    {
      "aliases": [
        "CLI",
        "command-line interface"
      ],
      "definition": "Command-line interface: a text-based way to run a program by typing commands and options.",
      "id": "cli",
      "term": "CLI"
    },
    {
      "aliases": [
        "API",
        "APIs",
        "application programming interface",
        "application programming interfaces"
      ],
      "definition": "Application programming interface: a defined way for software components to call and exchange data with one another.",
      "id": "api",
      "term": "API"
    },
    {
      "aliases": [
        "URL",
        "URLs"
      ],
      "definition": "Uniform Resource Locator: the address of a resource such as a web page or downloadable artifact.",
      "id": "url",
      "term": "URL"
    },
    {
      "aliases": [
        "UTC"
      ],
      "definition": "Coordinated Universal Time: the global time standard commonly used for unambiguous timestamps.",
      "id": "utc",
      "term": "UTC"
    },
    {
      "aliases": [
        "YAML"
      ],
      "definition": "A human-readable structured-data format commonly used for configuration files and automation workflows.",
      "id": "yaml",
      "term": "YAML"
    },
    {
      "aliases": [
        "HTML",
        "HyperText Markup Language"
      ],
      "definition": "HyperText Markup Language: the standard markup used to structure web pages.",
      "id": "html",
      "term": "HTML"
    },
    {
      "aliases": [
        "ZIP"
      ],
      "definition": "A compressed archive format that packages multiple files into one container.",
      "id": "zip",
      "term": "ZIP"
    },
    {
      "aliases": [
        "PYTHONPATH"
      ],
      "definition": "An environment variable that tells Python which additional directories to search when importing modules.",
      "id": "pythonpath",
      "term": "PYTHONPATH"
    },
    {
      "aliases": [
        "BABCS_LONG_TESTS",
        "BABCS_VERY_LONG_TESTS"
      ],
      "definition": "Environment-variable switches that enable longer BAB-CS qualification tiers which are intentionally omitted from the default fast suite.",
      "id": "long-test-flags",
      "term": "BABCS_LONG_TESTS and BABCS_VERY_LONG_TESTS"
    },
    {
      "aliases": [
        "DOI"
      ],
      "definition": "Digital Object Identifier: a persistent identifier used to locate a published research work.",
      "id": "doi",
      "term": "DOI"
    },
    {
      "aliases": [
        "SPDX"
      ],
      "definition": "Software Package Data Exchange: a standard vocabulary for identifying software licenses and supply-chain information.",
      "id": "spdx",
      "term": "SPDX"
    },
    {
      "aliases": [
        "MPL-2.0",
        "MPL 2.0",
        "MPL",
        "Mozilla Public License 2.0"
      ],
      "definition": "Mozilla Public License 2.0: a file-level open-source license used by this project.",
      "id": "mpl2",
      "term": "MPL-2.0"
    },
    {
      "aliases": [
        "HIL",
        "hardware-in-the-loop"
      ],
      "definition": "Hardware-in-the-loop: testing real controller hardware against a simulated plant.",
      "id": "hil",
      "term": "HIL"
    },
    {
      "aliases": [
        "ITP"
      ],
      "definition": "Interpolate, Truncate, and Project: a bracketed root-finding method that combines interpolation speed with guaranteed interval reduction.",
      "id": "itp",
      "term": "ITP"
    },
    {
      "aliases": [
        "OS",
        "operating system"
      ],
      "definition": "Operating system: the base software that manages the computer, files, processes, and hardware used for a qualification run.",
      "id": "os",
      "term": "OS"
    },
    {
      "aliases": [
        "Git HEAD",
        "HEAD"
      ],
      "definition": "Git HEAD: the Git reference identifying the currently checked-out commit.",
      "id": "git-head",
      "term": "Git HEAD"
    },
    {
      "aliases": [
        "POST",
        "PUT"
      ],
      "definition": "HTTP request methods: POST commonly creates or triggers work, while PUT commonly replaces or updates a named resource.",
      "id": "http-methods",
      "term": "POST and PUT"
    },
    {
      "aliases": [
        "WHEEL",
        "METADATA"
      ],
      "definition": "Standard files inside a Python wheel that describe the wheel format, package identity, dependencies, and other installation metadata.",
      "id": "wheel-metadata-files",
      "term": "WHEEL and METADATA"
    },
    {
      "aliases": [
        "NATURAL",
        "natural ordering"
      ],
      "definition": "A sparse-solver ordering that keeps the matrix columns in their original declared order instead of applying a fill-reducing permutation.",
      "id": "natural-ordering",
      "term": "NATURAL ordering"
    },
    {
      "aliases": [
        "ID",
        "identifier"
      ],
      "definition": "Identifier: a name or number used to distinguish one requirement, case, run, record, or artifact from another.",
      "id": "identifier",
      "term": "ID"
    },
    {
      "aliases": [
        "IEEE"
      ],
      "definition": "Institute of Electrical and Electronics Engineers: a professional organization and publisher of engineering standards and research.",
      "id": "ieee",
      "term": "IEEE"
    },
    {
      "aliases": [
        "ACM"
      ],
      "definition": "Association for Computing Machinery: a professional computing organization and research publisher.",
      "id": "acm",
      "term": "ACM"
    },
    {
      "aliases": [
        "SIAM"
      ],
      "definition": "Society for Industrial and Applied Mathematics: a professional organization and publisher focused on applied mathematics.",
      "id": "siam",
      "term": "SIAM"
    },
    {
      "aliases": [
        "UCB"
      ],
      "definition": "University of California, Berkeley: the institution identified by the UCB report prefix in historical circuit-simulation references.",
      "id": "ucb",
      "term": "UCB"
    },
    {
      "aliases": [
        "AMD"
      ],
      "definition": "Advanced Micro Devices: the processor manufacturer named in the local performance-test environment.",
      "id": "amd",
      "term": "AMD"
    },
    {
      "aliases": [
        "BIT",
        "BIT Numerical Mathematics"
      ],
      "definition": "A peer-reviewed journal that publishes research in numerical analysis and scientific computing.",
      "id": "bit-journal",
      "term": "BIT Numerical Mathematics"
    },
    {
      "aliases": [
        "ngspice"
      ],
      "definition": "An open-source SPICE-family circuit simulator used here for mapped cross-implementation comparison evidence.",
      "id": "ngspice",
      "term": "ngspice"
    },
    {
      "aliases": [
        "LTspice"
      ],
      "definition": "A circuit-simulation and schematic-capture environment commonly used with Analog Devices models and example circuits.",
      "id": "ltspice",
      "term": "LTspice"
    },
    {
      "aliases": [
        "PLECS"
      ],
      "definition": "A power-electronics system simulation environment covering converters, controls, switching, thermal behavior, and deployment workflows.",
      "id": "plecs",
      "term": "PLECS"
    },
    {
      "aliases": [
        "Simscape Electrical"
      ],
      "definition": "A MathWorks environment for electrical systems that can interact with mechanical, thermal, control, motor, and grid models.",
      "id": "simscape-electrical",
      "term": "Simscape Electrical"
    },
    {
      "aliases": [
        "Xyce"
      ],
      "definition": "A SPICE-compatible high-performance circuit simulator designed for very large serial and parallel problems.",
      "id": "xyce",
      "term": "Xyce"
    }
  ],
  "diagramAssets": [
    "authority-loop.svg",
    "engineering-workflow.svg",
    "evidence-hierarchy.svg",
    "external-comparison.svg",
    "qualification-surface.svg",
    "software-landscape.svg",
    "speedup-accuracy-by-size-blueprint.svg",
    "circuit-rc-step.svg",
    "result-rc-step.svg",
    "circuit-rl-step.svg",
    "result-rl-step.svg",
    "circuit-rlc-damped.svg",
    "result-rlc-damped.svg",
    "circuit-lc-long.svg",
    "result-lc-long.svg",
    "circuit-diode-clip.svg",
    "result-diode-clip.svg",
    "circuit-switched-rc.svg",
    "result-switched-rc.svg",
    "circuit-buck-like.svg",
    "result-buck-like.svg",
    "circuit-h-bridge-rl.svg",
    "result-h-bridge-rl.svg",
    "circuit-dc-link-rlc.svg",
    "result-dc-link-rlc.svg",
    "result-observatory-accuracy-work.svg",
    "result-bound-coverage.svg",
    "result-coverage-by-age.svg",
    "result-phase-energy.svg",
    "result-rejection-causes.svg",
    "tutorial-01-mna.svg",
    "tutorial-02-convergence.svg",
    "tutorial-03-phase-energy.svg",
    "tutorial-04-shadow-authority.svg",
    "tutorial-05-deterministic-packaging.svg",
    "tutorial-06-source-wheel-equivalence.svg",
    "tutorial-07-event-alignment.svg",
    "tutorial-08-bound-coverage.svg",
    "tutorial-09-fallback-forensics.svg",
    "tutorial-10-ngspice-mapping.svg",
    "ngspice-case-atlas.svg",
    "ngspice-feature-coverage.svg",
    "ngspice-error-overview.svg"
  ],
  "documentCount": 40,
  "documents": [
    {
      "category": "Additional Documents",
      "conceptIds": [
        "python-wheel",
        "klu",
        "scipy",
        "json",
        "api",
        "identifier"
      ],
      "headings": [
        {
          "id": "github-governance-controls",
          "level": 1,
          "text": "GitHub Governance Controls"
        },
        {
          "id": "applied-state",
          "level": 2,
          "text": "Applied State"
        },
        {
          "id": "main-protection",
          "level": 2,
          "text": "`main` Protection"
        },
        {
          "id": "release-tag-protection",
          "level": 2,
          "text": "Release Tag Protection"
        },
        {
          "id": "topics-and-security-reporting",
          "level": 2,
          "text": "Topics and Security Reporting"
        }
      ],
      "kind": "Policy",
      "markdown": "# GitHub Governance Controls\n\nLive governance settings are applied from reviewable payloads in\n`.github/governance/`.\n\n## Applied State\n\nOwner API readback on August 27, 2026 confirmed:\n\n- `main` protection is active with strict status checks for Python 3.11,\n  Python 3.12, Python 3.13, Python 3.14, validated-wheel construction, and the\n  optional SciPy/KLU backend job;\n- protected updates use pull-request flow with zero mandatory second-person\n  approvals, stale-review dismissal, conversation resolution, and administrator\n  enforcement;\n- force pushes and branch deletion are disabled;\n- repository ruleset `21646558`, `Protect release tags`, is active for\n  `refs/tags/v*`, blocks deletion and non-fast-forward updates, and has no\n  bypass actor;\n- private vulnerability reporting is enabled; and\n- the topic set recorded below is applied.\n\nThese settings are external mutable state. Re-read them before release rather\nthan treating this dated record as permanent proof.\n\n## `main` Protection\n\n`.github/governance/main-protection.json` configures:\n\n- the four Python matrix checks;\n- validated wheel construction;\n- optional SciPy and KLU sparse qualification;\n- strict up-to-date status checks;\n- pull-request flow with no second-person approval requirement;\n- stale-review dismissal and conversation resolution;\n- administrator inclusion;\n- no force pushes or branch deletion.\n\nApply and verify with:\n\n```bash\ngh api --method PUT \\\n  repos/pghauff73/Bounded-Authority-Based-Circuit-Simulation/branches/main/protection \\\n  --input .github/governance/main-protection.json\n\ngh api repos/pghauff73/Bounded-Authority-Based-Circuit-Simulation/branches/main/protection\n```\n\n## Release Tag Protection\n\n`.github/governance/release-tag-ruleset.json` prevents deletion and\nnon-fast-forward updates of tags matching `v*`, while still allowing a new\nrelease tag to be created after exact-hash approval.\n\n```bash\ngh api --method POST \\\n  repos/pghauff73/Bounded-Authority-Based-Circuit-Simulation/rulesets \\\n  --input .github/governance/release-tag-ruleset.json\n\ngh api repos/pghauff73/Bounded-Authority-Based-Circuit-Simulation/rulesets/21646558\n```\n\nUse `POST` only when the named ruleset does not exist. Update an existing\nruleset by its read-back identifier to avoid duplicate policies.\n\nRead back settings after every mutation. GitHub settings are live external\nstate; the JSON files record intent but do not prove the settings remain\napplied.\n\n## Topics and Security Reporting\n\nThe intended topic set is:\n\n```text\ncircuit-simulation\nerror-bounds\nmodified-nodal-analysis\nnumerical-methods\npython\nreproducible-research\nscientific-computing\ntransient-analysis\n```\n\nPrivate vulnerability reporting is enabled so `SECURITY.md` can direct\nsensitive reports away from public issues.\n",
      "order": 0,
      "path": "GITHUB_GOVERNANCE.md",
      "readingMinutes": 2,
      "sha256": "2cf3593363a37fc13e4dd9939dae44f951cc791ebbda94a8aecbda4bc29812ac",
      "summary": "Live governance settings are applied from reviewable payloads in .github/governance/.",
      "title": "GitHub Governance Controls",
      "wordCount": 336
    },
    {
      "category": "Current Work Essays",
      "conceptIds": [
        "babcs",
        "candidate-method",
        "projection",
        "replay",
        "anchor",
        "recursive-bound",
        "residual",
        "stiffness",
        "passivity",
        "reduced-order-model",
        "deterministic-evidence",
        "fixed-step",
        "fixed-accuracy",
        "fixed-work",
        "phase-error",
        "energy-drift",
        "empirical-coverage",
        "shadow-mode",
        "fail-closed",
        "factorization",
        "source-wheel-equivalence",
        "python-wheel",
        "mna",
        "dae",
        "spice",
        "rc",
        "rl",
        "rlc",
        "lc",
        "pwl",
        "ab2",
        "adams-bashforth",
        "be",
        "bdf2",
        "rk23",
        "klu",
        "scipy",
        "ngspice",
        "ltspice",
        "plecs",
        "simscape-electrical",
        "xyce"
      ],
      "headings": [
        {
          "id": "bounded-authority-based-circuit-simulation-current-work",
          "level": 1,
          "text": "Bounded-Authority-Based-Circuit-Simulation: Current Work"
        },
        {
          "id": "why-this-work-matters",
          "level": 2,
          "text": "Why This Work Matters"
        },
        {
          "id": "the-circuit-model-in-plain-words",
          "level": 2,
          "text": "The Circuit Model in Plain Words"
        },
        {
          "id": "the-authority-loop",
          "level": 2,
          "text": "The Authority Loop"
        },
        {
          "id": "bounds-anchors-and-replay",
          "level": 2,
          "text": "Bounds, Anchors, and Replay"
        },
        {
          "id": "engineering-evidence-surfaces",
          "level": 2,
          "text": "Engineering Evidence Surfaces"
        },
        {
          "id": "method-observatory",
          "level": 3,
          "text": "Method Observatory"
        },
        {
          "id": "bound-coverage-atlas",
          "level": 3,
          "text": "Bound Coverage Atlas"
        },
        {
          "id": "power-stage-sandbox",
          "level": 3,
          "text": "Power-Stage Sandbox"
        },
        {
          "id": "teaching-and-reproducibility-lab",
          "level": 3,
          "text": "Teaching and Reproducibility Lab"
        },
        {
          "id": "engineering-projects-suited-to-bab-cs",
          "level": 2,
          "text": "Engineering Projects Suited to BAB-CS"
        },
        {
          "id": "current-limits-and-next-work",
          "level": 2,
          "text": "Current Limits and Next Work"
        }
      ],
      "kind": "Essay",
      "markdown": "# Bounded-Authority-Based-Circuit-Simulation: Current Work\n\n## Why This Work Matters\n\nBounded-Authority-Based-Circuit-Simulation (`BAB-CS`) is a transient circuit\nsimulator designed for engineering studies in which the numerical decision must\nremain inspectable after the waveform has been produced. A transient simulation\ncalculates how voltages and currents change with time. In an ordinary workflow,\none numerical method often proposes the next state and effectively approves its\nown answer. BAB-CS separates those roles: a **candidate method** proposes the\nnext state, while independent calculations decide whether that proposal may\nbecome the accepted result.\n\nThis separation matters because a waveform can look plausible while hiding a\nnumerical failure. A switching event may be crossed at the wrong time. A\nnonlinear device solve may stop before its equations are consistent. A resonant\nwaveform may gradually shift in time, which is called **phase drift**. Stored\nelectrical energy may grow or decay because of the numerical method rather than\nthe circuit. A packaged release may also produce different evidence from the\nsource tree used to qualify it. BAB-CS makes these risks visible through\nevent-aligned steps, convergence checks, separate phase and energy reports,\nindependent replay, deterministic work counts, and source-versus-package\ncomparison.\n\nThe project began with Adams-Bashforth order two (`AB2`), an explicit two-step\nintegration formula that uses present and previous derivative information to\npredict the next state. **Explicit** means that the formula directly computes a\nproposal from known information. AB2 is economical, but it has a limited\nstability region and is not A-stable, meaning it cannot remain stable for every\nstable linear problem at every timestep [[3]](REFERENCES.md#ref-3). BAB-CS does\nnot claim to change that mathematics. It limits how much authority AB2 receives\nby checking, correcting, replacing, or independently rebuilding its proposed\ntrajectory [[12]](REFERENCES.md#ref-12) [[23]](REFERENCES.md#ref-23).\n\n## The Circuit Model in Plain Words\n\nBAB-CS follows **modified nodal analysis** (`MNA`), a standard method for turning\na circuit diagram into equations for node voltages and selected branch currents\n[[1]](REFERENCES.md#ref-1). MNA is part of the historical foundation of SPICE,\nwhose name means *Simulation Program with Integrated Circuit Emphasis*, a widely\nused family of circuit simulators [[2]](REFERENCES.md#ref-2).\n\nThe simulator separates two kinds of unknowns:\n\n- **Differential state** contains quantities that store memory: capacitor\n  voltages and inductor currents.\n- **Algebraic state** contains quantities that must satisfy the circuit\n  equations immediately: node voltages and currents through voltage-defined\n  branches.\n\nThis combination is a **differential-algebraic equation** (`DAE`): part of the\nmodel evolves through derivatives, while another part must satisfy simultaneous\nconstraints. BAB-CS performs **projection**, which means solving the circuit\nconstraints for every proposed state before that state can be accepted. A\nprojection can restore Kirchhoff current and voltage consistency, but it cannot\nby itself prove that the trajectory is accurate. The simulator therefore keeps\nprojection, local error evidence, independent authority, energy checks, and\nperiodic replay as separate controls [[6]](REFERENCES.md#ref-6)\n[[25]](REFERENCES.md#ref-25).\n\nThe current device set is intentionally bounded. It includes resistors,\ncapacitors, inductors, independent voltage and current sources, idealized\nShockley diodes, and time-controlled resistive switches. A Shockley diode is a\nsimple exponential diode model used to study nonlinear circuit behavior.\nSources and controls can be constant, sinusoidal, pulsed, or piecewise linear.\nUnsupported floating, singular, conflicting, or mathematically higher-index\ntopologies—systems whose constraints require extra differentiation before a\nstandard time step can be computed—fail explicitly rather than being changed through hidden\nconductances or hidden energy storage [[11]](REFERENCES.md#ref-11).\n\n## The Authority Loop\n\nBAB-CS currently supervises seven candidate methods:\n\n1. explicit Euler, a first-order one-step proposal;\n2. Heun, a second-order predictor-corrector proposal;\n3. Bogacki-Shampine order 2/3 (`RK23`), a Runge-Kutta method with paired\n   second- and third-order estimates;\n4. variable-step AB2;\n5. backward Euler, a first-order implicit method;\n6. trapezoidal integration, a second-order implicit method; and\n7. backward differentiation formula order two (`BDF2`), a second-order\n   implicit multistep method [[4]](REFERENCES.md#ref-4)\n   [[14]](REFERENCES.md#ref-14).\n\nAn **implicit method** solves an equation containing the new unknown state. It\nusually costs more per step than a simple explicit proposal, but it is valuable\nas an independent reference when the problem is stiff. **Stiffness** means that\na model contains fast and slow behavior together, forcing some methods to use\nvery small timesteps for stability rather than for visible waveform detail.\n\nFor an ordinary active step, BAB-CS performs this sequence:\n\n1. The candidate method proposes the next capacitor voltages and inductor\n   currents.\n2. Projection solves the circuit equations associated with that proposal.\n3. A different implicit method computes an independent reference state.\n4. The controller estimates how errors may amplify through the candidate.\n5. The candidate is blended toward the reference when correction can make the\n   modeled propagation contractive. **Contractive** means that the model expects\n   earlier error to shrink rather than grow.\n6. A second projection restores circuit consistency after correction.\n7. Residual, convergence, finiteness, passivity, and error gates decide whether\n   to accept, retry with a smaller step, or give full authority to the reference.\n\n**Passivity** means that a passive declared model may not create net energy from\nnothing. A passivity gate checks that numerical behavior does not contradict\nthat property beyond the configured allowance.\n\nThe accepted state therefore belongs to the controller, not to the candidate.\nAn implicit candidate is paired with a different implicit reference so that a\nzero difference cannot be manufactured by comparing a method with itself\n[[13]](REFERENCES.md#ref-13) [[23]](REFERENCES.md#ref-23).\n\n## Bounds, Anchors, and Replay\n\nThe controller carries a **recursive internal bound**, a running estimate of\nhow previously modeled error and the newest local defect may combine. A\n**defect** is the measured disagreement between a proposal and an independent\nor lower-order calculation. In simplified form, the update is\n`B_next = q B + delta`, where `B` is the previous bound, `q` is the modeled\npropagation factor after correction, and `delta` is the new local contribution.\nThe production implementation also includes normalized circuit-equation\nresiduals and roundoff protection [[13]](REFERENCES.md#ref-13)\n[[15]](REFERENCES.md#ref-15).\n\nThis bound is intentionally limited. It applies to the implemented numerical\nerror model relative to declared internal authority. It is not a mathematical\ninterval guaranteed to contain the unknown exact physical trajectory. The\nBound Coverage Atlas reports how often the recursive bound covers independently\nmeasured authority error so that weak coverage is visible rather than hidden.\n\nAn **anchor** is a previously accepted state from which BAB-CS can independently\nrecompute a recent interval. That recomputation is called **replay**. Replay uses\nan implicit method and controlled subdivisions, meaning smaller internal steps,\nto challenge the accumulated candidate path. It measures anchor deviation,\nrefreshes authority, and can expose errors that a local candidate/reference\ncomparison did not reveal. Scheduled source and switch breakpoints are reached\nexactly, and each accepted event forces independent replay before multistep\nhistory is cleared [[5]](REFERENCES.md#ref-5)\n[[28]](REFERENCES.md#ref-28).\n\n## Engineering Evidence Surfaces\n\nFour connected facilities make the current behavior reviewable.\n\n### Method Observatory\n\nThe BAB-CS Method Observatory runs resistor-capacitor (`RC`),\nresistor-inductor (`RL`), resistor-inductor-capacitor (`RLC`),\ninductor-capacitor (`LC`), diode-clip, and switched-RC cases across all seven\ncandidate profiles. It produces:\n\n- **fixed-step reports**, where methods receive the same nominal timestep;\n- **fixed-accuracy reports**, where rows are selected against a declared error\n  target; and\n- **fixed-work reports**, where methods are compared under a deterministic\n  operation budget rather than variable wall-clock time.\n\nThe observatory does not declare one universal winner. It preserves the exact\nconfiguration and measured row used for each engineering conclusion.\n\n### Bound Coverage Atlas\n\nThe Bound Coverage Atlas aligns actual authority error, recursive internal\nbound, anchor deviation, phase, energy, empirical coverage ratio, and the causes\nof fallback or rejection. **Empirical coverage ratio** means the measured\nfraction of eligible samples for which the internal bound was at least as large\nas the independently observed authority error. It is characterization of the\ndeclared cases, not a formal proof for arbitrary circuits.\n\n### Power-Stage Sandbox\n\nThe Power-Stage Sandbox provides a simplified buck-like converter, a scheduled\nH-bridge with an RL load, and a direct-current-link RLC startup and interruption\ncase. An H-bridge is a four-switch arrangement that can apply positive or\nnegative voltage to a load. These are **reduced-order numerical experiments,\nnot production device models**. A reduced-order model is a deliberate\nsimplification that retains only the behavior required for the numerical\nquestion. Semiconductor switching loss, magnetic saturation, electromagnetic\ninterference, detailed thermal behavior, protection hardware, and safety signoff\nremain outside these examples.\n\n### Teaching and Reproducibility Lab\n\nThe Teaching and Reproducibility Lab contains ten compact exercises covering\nmodified nodal analysis (`MNA`), measured convergence, phase versus energy,\nshadow authority, deterministic packaging, source-versus-wheel equivalence,\nexact event alignment, empirical bound coverage, fallback and rejection\nforensics, and semantic mapping to ngspice. **Shadow authority** means that a\ncandidate runs and records evidence while a trusted reference still owns the\naccepted state. A Python **wheel** is an installable package file. Source-versus-\nwheel equivalence checks that the source checkout and the isolated installed\npackage produce the same declared numerical evidence. **Event alignment** means\nending a numerical step exactly where a scheduled circuit change occurs.\n**Empirical coverage** means the measured fraction of eligible samples for\nwhich the recorded internal bound was at least as large as the independently\nmeasured authority error; it is observed evidence, not a formal proof.\n**Semantic mapping** means translating the meaning and state order of a BAB-CS\ncase into another simulator rather than merely copying similarly named fields.\n\n## Engineering Projects Suited to BAB-CS\n\nThe current system is especially useful for the following bounded projects:\n\n- screening a commanded buck-converter switching schedule before detailed\n  semiconductor and thermal modeling;\n- checking H-bridge dead time, polarity reversal, current continuity, and event\n  handling in a simplified RL load;\n- studying direct-current-link inrush, stored energy, interruption, and decay;\n- comparing diode-clamp convergence, residuals, fallback, and timestep\n  sensitivity;\n- separating phase drift from energy drift in LC or lightly damped RLC systems;\n- selecting a candidate method under fixed-step, fixed-accuracy, or fixed-work\n  constraints;\n- qualifying whether a solver backend or packaging change altered numerical\n  evidence; and\n- teaching circuit equations and reproducible numerical claims in an executable\n  laboratory.\n\nBAB-CS complements rather than replaces specialist simulation software.\nngspice supplies an independent SPICE implementation for mapped comparison\ncases. LTspice is better suited to interactive schematic work and vendor device\nmodels. PLECS is designed for broad power-electronics systems and real-time\ncontroller workflows. Simscape Electrical supports larger multidomain plants,\nwhere electrical behavior interacts with mechanical, thermal, or control\nsystems. Xyce targets very large SPICE-compatible circuit simulation, including\nparallel execution. BAB-CS adds value when the engineering question depends on\nwhy a numerical step passed, changed authority, replayed, or failed.\n\n## Current Limits and Next Work\n\nThe strongest current result is architectural: multiple proposal methods share\none explicit authority system, independent replay path, failure taxonomy, and\ndeterministic evidence surface. The strongest limits are also explicit. The\ndevice library is small, general state-triggered event location is not yet\nimplemented, higher-index DAEs fail closed, the recursive bound is not a formal\nphysical enclosure, and performance measurements apply only to named workloads.\n\nSparse execution is available through SciPy and an optional SuiteSparse KLU\nadapter. SciPy is a Python scientific-computing library. KLU is a sparse linear\nsolver specialized for circuit-like matrices. The highest-value performance\nwork remains measured rather than speculative: preserve resident solver data,\nmove residual ownership closer to native factorization, improve cache\nobservability, and retain an optimization only when complete simulations gain\nwithout weakening authority [[7]](REFERENCES.md#ref-7)\n[[17]](REFERENCES.md#ref-17) [[35]](REFERENCES.md#ref-35).\n\nRelease automation builds and checks evidence, but it cannot approve a release.\nThe proposed `1.1.0` release still requires one clean source commit, complete\nqualification on that exact commit, hashes that identify the source and built\nartifacts, and explicit human approval [[19]](REFERENCES.md#ref-19)\n[[21]](REFERENCES.md#ref-21). In BAB-CS, a passing script is evidence; it is not\nscientific, engineering, or publication authority by itself.\n",
      "order": 0,
      "path": "CURRENT_WORK.md",
      "readingMinutes": 9,
      "sha256": "68a52efcf6603fe999e0a516dcfb6d9eabb45c7e071fbbadf9ccd467526d2f91",
      "summary": "Bounded-Authority-Based-Circuit-Simulation (BAB-CS) is a transient circuit simulator designed for engineering studies in which the numerical decision must remain inspectable after the waveform has been produced. A transient simulation…",
      "title": "Bounded-Authority-Based-Circuit-Simulation: Current Work",
      "wordCount": 1932
    },
    {
      "category": "Current Work Essays",
      "conceptIds": [
        "babcs",
        "candidate-method",
        "numerical-authority",
        "projection",
        "replay",
        "anchor",
        "recursive-bound",
        "residual",
        "jacobian",
        "newton-iteration",
        "nonlinear-convergence",
        "stiffness",
        "passivity",
        "fixed-step",
        "fixed-accuracy",
        "fixed-work",
        "phase-error",
        "energy-drift",
        "empirical-coverage",
        "mna",
        "dae",
        "ab2",
        "adams-bashforth",
        "be",
        "bdf2",
        "rk23"
      ],
      "headings": [
        {
          "id": "numerical-methods-and-error-bounding-in-bounded-authority-based-circuit-simulation",
          "level": 1,
          "text": "Numerical Methods and Error Bounding in Bounded-Authority-Based-Circuit-Simulation"
        },
        {
          "id": "five-engineering-decisions-bab-cs-makes-reviewable",
          "level": 2,
          "text": "Five Engineering Decisions BAB-CS Makes Reviewable"
        },
        {
          "id": "read-bab-cs-as-a-supervised-timestep",
          "level": 2,
          "text": "Read BAB-CS as a Supervised Timestep"
        },
        {
          "id": "follow-one-timestep-from-proposal-to-replay",
          "level": 2,
          "text": "Follow One Timestep from Proposal to Replay"
        },
        {
          "id": "circuit-equations-and-projection",
          "level": 2,
          "text": "Circuit Equations and Projection"
        },
        {
          "id": "candidate-methods",
          "level": 2,
          "text": "Candidate Methods"
        },
        {
          "id": "explicit-euler",
          "level": 3,
          "text": "Explicit Euler"
        },
        {
          "id": "heun",
          "level": 3,
          "text": "Heun"
        },
        {
          "id": "bogacki-shampine-rk23",
          "level": 3,
          "text": "Bogacki-Shampine RK23"
        },
        {
          "id": "variable-step-ab2",
          "level": 3,
          "text": "Variable-Step AB2"
        },
        {
          "id": "backward-euler-trapezoidal-and-bdf2",
          "level": 3,
          "text": "Backward Euler, Trapezoidal, and BDF2"
        },
        {
          "id": "amplification-correction-and-accepted-authority",
          "level": 2,
          "text": "Amplification, Correction, and Accepted Authority"
        },
        {
          "id": "recursive-internal-bound",
          "level": 2,
          "text": "Recursive Internal Bound"
        },
        {
          "id": "nonlinear-solves",
          "level": 2,
          "text": "Nonlinear Solves"
        },
        {
          "id": "events-anchors-and-replay",
          "level": 2,
          "text": "Events, Anchors, and Replay"
        },
        {
          "id": "phase-energy-and-coverage",
          "level": 2,
          "text": "Phase, Energy, and Coverage"
        },
        {
          "id": "where-the-numerical-claim-stops",
          "level": 2,
          "text": "Where the Numerical Claim Stops"
        }
      ],
      "kind": "Essay",
      "markdown": "# Numerical Methods and Error Bounding in Bounded-Authority-Based-Circuit-Simulation\n\n## Five Engineering Decisions BAB-CS Makes Reviewable\n\nChoose a numerical method by asking what engineering decision its evidence must\nsupport. Bounded-Authority-Based-Circuit-Simulation (`BAB-CS`) makes five\nquestions reviewable:\n\n1. How can a fast method propose a circuit state without being allowed to approve\n   its own answer?\n2. How does the simulator keep voltages and currents consistent with the circuit\n   equations after every timestep?\n3. What happens when two methods disagree, a nonlinear solve fails, or a switch\n   changes the circuit suddenly?\n4. How can phase, stored energy, and error-bound coverage be inspected separately\n   instead of being hidden inside one accuracy number?\n5. Which claim is justified by the evidence, and which stronger claim remains\n   unproved?\n\nThese questions matter in engineering projects where an attractive waveform is\nnot enough. The result must also show why the timestep was accepted, what\nindependent check challenged it, and what failure path remained available.\n\n## Read BAB-CS as a Supervised Timestep\n\nBounded-Authority-Based-Circuit-Simulation (`BAB-CS`) separates **proposal** from\n**authority**. A candidate numerical method proposes the next circuit state.\nIndependent equations, reference methods, and gates decide whether that proposal\nis accepted, corrected, recomputed, or rejected. This design does not make every\ncandidate stable or accurate. It makes the candidate’s authority conditional and\nobservable [[12]](REFERENCES.md#ref-12) [[13]](REFERENCES.md#ref-13).\n\nThe word **bound** also has a specific meaning. BAB-CS maintains an internal\nestimate of error relative to its implemented numerical authority model. That\nestimate is useful for diagnostics and control, but it is not a proof that the\nunknown exact physical trajectory lies inside a formal interval. Empirical\ncoverage is reported separately so readers can see where the implemented bound\ndoes and does not cover independently measured authority error.\n\n## Follow One Timestep from Proposal to Replay\n\nFollow one attempted timestep from start to finish:\n\n1. **A candidate proposes.** A selected numerical formula predicts the next\n   capacitor voltages and inductor currents. At this point the values are only a\n   proposal, not an accepted result.\n2. **Projection restores circuit consistency.** The circuit equations are solved\n   so node voltages and branch currents satisfy the declared electrical\n   constraints. This prevents an internally inconsistent state from advancing.\n3. **An independent reference challenges the proposal.** A different numerical\n   method computes its own answer. The disagreement exposes error that the\n   candidate cannot measure by comparing only with itself.\n4. **The controller corrects or transfers authority.** If the candidate remains\n   within the declared model, the controller can move its result toward the\n   reference. If contraction cannot be established, the reference receives full\n   authority.\n5. **Hard gates make the final decision.** Failed projection, excessive equation\n   mismatch, invalid history, nonfinite values, failed nonlinear convergence,\n   or an energy-rule violation can reject the attempt or invoke a safer fallback.\n6. **Replay checks accumulated behavior.** At declared intervals and events, an\n   independent recomputation starts from a retained anchor and checks whether the\n   accepted path has drifted.\n\nEach control addresses a visible engineering failure: projection addresses\nequation inconsistency, method comparison addresses unchecked local error,\ncontraction addresses error growth, hard gates address invalid states, and\nreplay addresses accumulated drift. Later sections explain the mathematics\nbehind each control.\n\n## Circuit Equations and Projection\n\nBAB-CS represents a circuit as a semiexplicit differential-algebraic equation\n(`DAE`). A DAE combines differential equations, which describe change with time,\nwith algebraic equations, which must be satisfied immediately. Conceptually,\n\n```text\nz' = f(t, z, y)\n0  = g(t, z, y)\n```\n\nHere `z` contains capacitor voltages and inductor currents, and `y` contains node\nvoltages and currents through voltage-defined branches. The prime in `z'` means\nthe time derivative. The equation `g(t, z, y) = 0` states the circuit constraints.\n\nThe equation system follows modified nodal analysis (`MNA`), a standard way to\nconvert a circuit into equations while retaining useful sparse structure\n[[1]](REFERENCES.md#ref-1) [[25]](REFERENCES.md#ref-25). **Sparse** means that\nmost entries in the equation matrix are zero because each component connects to\nonly a small part of the circuit.\n\nGiven a proposed `z`, BAB-CS performs **projection** by solving\n`g(t, z, y) = 0`. In a linear resistor, capacitor, and inductor network, this is\na linear solve. With a diode, it becomes a nonlinear iterative solve. Projection\nprevents departure from the circuit-equation surface, but it does not prevent\nerror along that surface. A state can satisfy Kirchhoff’s laws and still have the\nwrong phase, amplitude, or stored energy [[6]](REFERENCES.md#ref-6). Projection\ntherefore supports authority; it does not replace authority.\n\n## Candidate Methods\n\nBAB-CS supervises seven numerical candidates. A **candidate** is the formula\nallowed to propose the next dynamic state.\n\n### Explicit Euler\n\nExplicit Euler uses the present derivative to take one forward step. It is\nfirst-order, meaning its accumulated error normally decreases roughly in\nproportion to the timestep. It is simple and useful as a control case, but it\ncan require very small steps on stiff problems.\n\n### Heun\n\nHeun’s method first makes an Euler proposal and then averages the starting and\nending slopes. It is second-order, so its accumulated error normally decreases\nroughly with the square of the timestep. The difference between the Euler and\nHeun results supplies an embedded error estimate, meaning two accuracy levels\nare obtained from related work [[4]](REFERENCES.md#ref-4).\n\n### Bogacki-Shampine RK23\n\nBogacki-Shampine order 2/3 (`RK23`) is a Runge-Kutta method. A Runge-Kutta method\nsamples several intermediate slopes within one timestep. RK23 produces related\nsecond- and third-order results, allowing their difference to estimate local\nerror [[24]](REFERENCES.md#ref-24).\n\n### Variable-Step AB2\n\nAdams-Bashforth order two (`AB2`) is an explicit multistep method. **Multistep**\nmeans it reuses information from an earlier accepted step. For current timestep\n`h_n`, previous timestep `h_(n-1)`, current derivative `f_n`, and previous\nderivative `f_(n-1)`, the proposal is\n\n```text\nr = h_n / h_(n-1)\nz_ab = z_n + h_n [(1 + r/2) f_n - (r/2) f_(n-1)].\n```\n\nThe ratio `r` changes the coefficients when the timestep changes. BAB-CS rejects\ninvalid history and excessive step-ratio changes. Startup, rejection, accepted\nevents, and replay resets transfer authority to an implicit method until safe\nmultistep history has been rebuilt [[5]](REFERENCES.md#ref-5)\n[[23]](REFERENCES.md#ref-23).\n\n### Backward Euler, Trapezoidal, and BDF2\n\nBackward Euler, trapezoidal integration, and backward differentiation formula\norder two (`BDF2`) are implicit methods. **Implicit** means that the new state\nappears inside the equation being solved. Backward Euler is first-order and\nstrongly damping. Trapezoidal integration is second-order and often preserves\noscillatory amplitude better. BDF2 is a second-order multistep method and uses\nbackward Euler when valid history is unavailable [[26]](REFERENCES.md#ref-26).\n\nThese methods may serve as candidates or references. An implicit candidate is\npaired with a different reference method. Comparing a method with itself would\nproduce a misleading zero difference rather than independent evidence.\n\n## Amplification, Correction, and Accepted Authority\n\nThe controller estimates a conservative candidate amplification `G_c`.\n**Amplification** describes how existing error may grow through one numerical\nstep. The estimate uses the timestep and a norm of the differential Jacobian.\nA **Jacobian** is a matrix of local sensitivities: it records how each derivative\nchanges when each state variable changes. The infinity norm used here is the\nlargest absolute row sum.\n\nFor explicit methods, BAB-CS evaluates a stability-polynomial model at\n`h ||J||`, where `h` is the timestep and `J` is the Jacobian. AB2 also includes\nthe previous Jacobian norm and the step ratio. Implicit amplification estimates\nare used only where their denominator models remain valid\n[[14]](REFERENCES.md#ref-14). These are conservative runtime models, not exact\nspectral decompositions of the circuit transition.\n\nWhen a candidate state `z_c` and independent reference state `z_r` are\navailable, the corrected proposal is\n\n```text\nz_* = (1 - gamma) z_c + gamma z_r.\n```\n\nThe correction gain `gamma` determines how far the state moves toward the\nreference. BAB-CS chooses it so the modeled corrected propagation\n`q = (1 - gamma) G_c` meets the configured contraction target. **Contraction**\nmeans that the model expects inherited error to decrease. If the controller\ncannot establish `q < 1`, the reference receives full authority. The corrected\nstate is projected again before acceptance [[13]](REFERENCES.md#ref-13).\n\n## Recursive Internal Bound\n\nThe recursive bound carries modeled uncertainty from one accepted state to the\nnext. In simplified form,\n\n```text\nB_next = q B + delta.\n```\n\n`B` is the previous bound, `q` is corrected propagation, and `delta` is the new\nlocal contribution. The contribution can include candidate/reference\ndisagreement, an embedded lower-order difference, normalized algebraic residual,\nand floating-point allowance. A **residual** is the mismatch left when the\ncircuit equations are evaluated at the computed solution. **Floating-point**\nnumbers are the finite-precision values used by the computer.\n\nThe controller also uses a scaled norm so large and small state components can\nbe compared against absolute and relative tolerances. A finite bound does not\noverride hard gates. Nonfinite values, failed projection, excessive residual,\nfailed nonlinear convergence, invalid history, passivity violations, and replay\nfailure can all reject a step or transfer authority to a safer method\n[[15]](REFERENCES.md#ref-15).\n\n**Passivity** means that a passive circuit model may not create net energy from\nnothing. A passivity violation indicates that the numerical result conflicts\nwith that declared physical property beyond its allowed tolerance.\n\n## Nonlinear Solves\n\nDiodes make the algebraic equations nonlinear. BAB-CS uses Newton iteration,\nwhich repeatedly linearizes the equations around a current guess and solves for\nan update. A line search reduces the update when the full Newton step does not\nimprove the residual. **Convergence** means that the iteration reaches the\ndeclared residual and update tolerances before its iteration limit.\n\nNonlinear convergence is evidence, not a cosmetic status flag. If the solve\ndoes not converge, the state cannot be accepted merely because the waveform\nlooks smooth. Candidate and reference solves record iteration counts, residuals,\nfallbacks, and rejection causes so an engineer can distinguish physical\nclipping from numerical failure [[18]](REFERENCES.md#ref-18).\n\n## Events, Anchors, and Replay\n\nA commanded source or switch breakpoint is an **event**: a declared time at\nwhich the model changes formula or value. BAB-CS shortens the current step so it\nlands exactly on the event. Exact event alignment prevents a multistep method\nfrom averaging unknowingly across a discontinuity. After an accepted event,\nmultistep history is invalidated.\n\nAn **anchor** is a retained accepted state used as the start of an independent\ncheck. **Replay** recomputes the interval from that anchor with an implicit\nmethod and smaller internal steps. Replay serves three purposes:\n\n- it challenges accumulated candidate behavior independently;\n- it measures anchor deviation, the distance between the accepted path and the\n  replayed path; and\n- it refreshes authority before the candidate continues.\n\nCurrent event handling forces independent replay before event-driven history is\ncleared. This prevents an event reset from accidentally removing the very\nindependent check needed at a discontinuity [[28]](REFERENCES.md#ref-28).\n\n## Phase, Energy, and Coverage\n\nOne error number cannot explain every engineering failure. BAB-CS therefore\nreports several dimensions separately:\n\n- **state error** measures voltage and current disagreement;\n- **phase error** measures the timing shift of an oscillation;\n- **energy error** measures numerical change in capacitor and inductor energy;\n- **anchor deviation** measures disagreement with independent replay;\n- **authority age** measures elapsed time since the last independent refresh;\n  and\n- **empirical coverage** measures how often the recursive bound covers observed\n  authority error on eligible samples.\n\nThis separation is especially important for an inductor-capacitor (`LC`)\noscillator. A method can preserve total energy while accumulating phase error,\nor damp energy while keeping short-term zero crossings close. The correct metric\ndepends on the engineering decision.\n\n## Where the Numerical Claim Stops\n\nBAB-CS supports a bounded multi-method control claim: candidate authority is\nlimited by projection, independent reference calculations, correction, hard\ngates, and replay. It does not support a claim that raw AB2 has become A-stable,\nwhich would mean stable for every stable linear problem at every timestep,\nthat the recursive bound encloses exact physical truth, or that one candidate is\nbest for every circuit.\n\nThe Method Observatory and Bound Coverage Atlas are therefore essential. They\nshow fixed-step, fixed-accuracy, and fixed-work behavior across resistor-\ncapacitor, resistor-inductor, resistor-inductor-capacitor, inductor-capacitor,\ndiode, and switched cases. Negative results, weak coverage, fallback causes, and\nrejections remain part of the evidence rather than being removed from the\nstory.\n",
      "order": 1,
      "path": "NUMERICAL_METHODS_ESSAY.md",
      "readingMinutes": 9,
      "sha256": "3e52e60f7d799a27e6b6c7c8466de05a2605d61721406e0dbdc2dc7163c96a22",
      "summary": "Choose a numerical method by asking what engineering decision its evidence must support. Bounded-Authority-Based-Circuit-Simulation (BAB-CS) makes five questions reviewable:",
      "title": "Numerical Methods and Error Bounding in Bounded-Authority-Based-Circuit-Simulation",
      "wordCount": 1976
    },
    {
      "category": "Current Work Essays",
      "conceptIds": [
        "babcs",
        "candidate-method",
        "projection",
        "replay",
        "anchor",
        "residual",
        "jacobian",
        "newton-iteration",
        "deterministic-evidence",
        "fixed-work",
        "factorization",
        "source-wheel-equivalence",
        "mna",
        "be",
        "bdf2",
        "csc",
        "klu",
        "superlu",
        "scipy",
        "rms",
        "wrms",
        "ulp",
        "hil"
      ],
      "headings": [
        {
          "id": "circuit-engineering-and-performance-in-bounded-authority-based-circuit-simulation",
          "level": 1,
          "text": "Circuit Engineering and Performance in Bounded-Authority-Based-Circuit-Simulation"
        },
        {
          "id": "why-authority-must-survive-optimization",
          "level": 2,
          "text": "Why Authority Must Survive Optimization"
        },
        {
          "id": "follow-one-timestep-through-its-decision-owners",
          "level": 2,
          "text": "Follow One Timestep Through Its Decision Owners"
        },
        {
          "id": "build-the-circuit-in-a-repeatable-order",
          "level": 2,
          "text": "Build the Circuit in a Repeatable Order"
        },
        {
          "id": "solve-small-systems-with-the-dense-baseline",
          "level": 2,
          "text": "Solve Small Systems with the Dense Baseline"
        },
        {
          "id": "scale-repeated-solves-with-sparse-execution",
          "level": 2,
          "text": "Scale Repeated Solves with Sparse Execution"
        },
        {
          "id": "accelerate-nonlinear-solves-without-weakening-replay",
          "level": 2,
          "text": "Accelerate Nonlinear Solves without Weakening Replay"
        },
        {
          "id": "measure-the-whole-simulation-not-one-fast-kernel",
          "level": 2,
          "text": "Measure the Whole Simulation, Not One Fast Kernel"
        },
        {
          "id": "separate-algorithmic-work-from-wall-clock-time",
          "level": 2,
          "text": "Separate Algorithmic Work from Wall-Clock Time"
        },
        {
          "id": "keep-only-end-to-end-improvements",
          "level": 2,
          "text": "Keep Only End-to-End Improvements"
        },
        {
          "id": "prioritize-the-remaining-measured-costs",
          "level": 2,
          "text": "Prioritize the Remaining Measured Costs"
        },
        {
          "id": "know-where-this-engineering-claim-stops",
          "level": 2,
          "text": "Know Where This Engineering Claim Stops"
        }
      ],
      "kind": "Essay",
      "markdown": "# Circuit Engineering and Performance in Bounded-Authority-Based-Circuit-Simulation\n\n## Why Authority Must Survive Optimization\n\nBounded-Authority-Based-Circuit-Simulation (`BAB-CS`) is engineered so that a\nfaster numerical path cannot quietly bypass the checks that make a result\nreviewable. The project treats performance as an optimization problem inside a\nfixed authority architecture. A proposed acceleration is retained only when it\nimproves complete workloads, preserves numerical behavior, keeps failure modes\nvisible, and leaves a safe fallback available.\n\nFor a novice, the central rule is simple: **the part that runs faster is not\nallowed to redefine what counts as correct**. Candidate methods propose states.\nThe circuit model enforces electrical equations. Independent methods and replay\nchallenge the proposal. The controller owns acceptance. The simulator owns\nevent alignment and retry behavior [[23]](REFERENCES.md#ref-23)\n[[28]](REFERENCES.md#ref-28).\n\n## Follow One Timestep Through Its Decision Owners\n\nFive owners divide the decisions made during one timestep. An **owner** is the\npart of the software allowed to make one specific class of decision.\n\n1. The **simulator** chooses the attempted timestep and shortens it when needed\n   to land exactly on a declared source or switch event.\n2. A **candidate integrator** applies one numerical formula and proposes the next\n   dynamic state. It also records how much numerical work it performed, but it\n   cannot accept its own proposal.\n3. The **circuit model** applies topology and component equations, projects the\n   proposal onto the circuit constraints, and computes stored energy, source\n   power, dissipated power, and sensitivity.\n4. An **independent integrator** computes a reference or replay result. The\n   implicit integrators own backward Euler, trapezoidal integration, backward\n   differentiation formula order two (`BDF2`), nonlinear iteration, and replay.\n   An implicit method solves an equation that contains the new state itself.\n5. The **bounded controller** compares the evidence, applies correction and hard\n   gates, updates the recursive error bound, and either accepts, falls back to a\n   safer method, or rejects the attempt for retry.\n\nThis ownership chain prevents a convenient fast path from changing a circuit\nequation, weakening an acceptance rule, or approving its own answer without the\nrest of the authority system noticing [[24]](REFERENCES.md#ref-24)\n[[25]](REFERENCES.md#ref-25) [[26]](REFERENCES.md#ref-26).\n\n## Build the Circuit in a Repeatable Order\n\nThe `Circuit` constructor validates component values, normalizes node names,\nestablishes a repeatable node and branch order, and separates dynamic variables\nfrom algebraic variables. Capacitor voltages and inductor currents are the\ndynamic state because they store electrical memory. Node voltages and currents\nthrough voltage-defined branches are algebraic unknowns because they must satisfy\nthe circuit equations at each evaluation.\n\nThe formulation uses modified nodal analysis (`MNA`), a standard method that\nturns a circuit into equations while retaining the sparse connectivity of the\nnetwork [[1]](REFERENCES.md#ref-1). **Deterministic ordering** means that the\nsame declared circuit produces the same internal ordering rather than depending\non incidental container or allocation behavior. That property supports stable\nreports, repeatable hashes, and reliable comparison between source and installed\npackages.\n\nAt each evaluation, the model samples sources and switch controls, solves the\nalgebraic equations, calculates the dynamic derivative, and reports stored\nenergy, source power, and dissipated power. The accepted evaluation therefore\ncontains both the state and the diagnostics required to judge it. Public output\nretains meaningful node and branch names; optimized internal paths use ordered\narrays so they do not rebuild dictionaries during every solve.\n\n## Solve Small Systems with the Dense Baseline\n\nBAB-CS solves small systems with dependency-free linear algebra. **Linear\nalgebra** is the matrix-based mathematics used to solve simultaneous circuit\nequations. The dense implementation stores every matrix entry, including zeros,\nand provides:\n\n- partial pivoting, which rearranges equations to avoid weak division points;\n- singularity detection, which identifies an unsolvable or underdetermined\n  equation system;\n- factored solves for one or several right-hand sides;\n- finite-difference Jacobians, which estimate sensitivities by small input\n  changes;\n- infinity norms; and\n- weighted root-mean-square scaling, which combines component errors after\n  applying absolute and relative tolerances [[27]](REFERENCES.md#ref-27).\n\nThis path is not merely a convenience. It gives small circuits, tests, and clean\npackage installations an auditable implementation that does not require a\ncompiled third-party solver.\n\n## Scale Repeated Solves with Sparse Execution\n\nA **sparse matrix** contains mostly zeros. Larger circuit equations are usually\nsparse because each device connects only a few nodes. BAB-CS can use SciPy, a\nPython scientific-computing library, to store a matrix in compressed sparse\ncolumn (`CSC`) form. CSC stores nonzero values by column rather than storing the\nwhole matrix. SciPy supplies the SuperLU sparse factorization interface.\n**Factorization** rewrites a matrix into parts that make repeated equation solves\nmore efficient\n[[7]](REFERENCES.md#ref-7) [[9]](REFERENCES.md#ref-9).\n\nBAB-CS also supports an optional SuiteSparse KLU adapter. KLU is a sparse linear\nsolver designed for circuit-like matrices. The adapter reaches a compatible\nsystem library through `ctypes`, Python’s standard interface for calling compiled\nC functions [[35]](REFERENCES.md#ref-35). Users may select `dense`, `scipy`,\n`klu`, or `auto`. The `auto` policy considers size, density, structural reuse,\nand the number of right-hand sides. It does not assume that sparse execution is\nalways faster.\n\nOne important optimization compiles circuit topology once. The compiler records\nCSC row indices, column pointers, device stamp locations, constraint locations,\nand sensitivity structure. Repeated evaluations then change only numeric values.\nComponent parameters remain live: compilation records where a value belongs,\nnot what the future value must be [[17]](REFERENCES.md#ref-17)\n[[25]](REFERENCES.md#ref-25).\n\nSparse workspaces are bounded. A **workspace** is reusable memory associated\nwith a matrix structure. A bounded cache limits how many workspaces a thread may\nretain, preventing a speed optimization from becoming unbounded memory growth.\nKLU can reuse symbolic analysis, which studies the nonzero pattern, and then\nrefactor only new numeric values for the same pattern. If KLU fails in automatic\nmode, BAB-CS falls back to SciPy rather than converting an optional accelerator\ninto a single point of failure.\n\n## Accelerate Nonlinear Solves without Weakening Replay\n\nA diode makes the circuit equations nonlinear. BAB-CS uses Newton iteration,\nwhich repeatedly linearizes the equations and solves for a correction. The\nimplementation preserves damping, limiting, finite-value checks, iteration\nlimits, and residual gates while optimizing repeated assembly work. A\n**residual** is the remaining equation mismatch at the computed state.\n\nReplay is an independent recomputation from a trusted anchor. Mixed capacitor-\nand-inductor trapezoidal replay now uses derivative-defect evidence to decide\nwhether a complete replay window needs finer internal subdivisions. A\n**derivative defect** is disagreement between the derivative behavior implied by\ndifferent points or methods. Piecewise-switched BDF2 replay has separate startup,\norder, and event evidence because a multistep method cannot safely reuse history\nacross a discontinuity.\n\nEvent handling preserves authority before it preserves speed. An accepted switch\nor source breakpoint forces independent replay before multistep history is\ncleared. The next startup step uses the reference method. This prevents a fast\nevent reset from erasing the independent check that should have occurred at the\nevent.\n\n## Measure the Whole Simulation, Not One Fast Kernel\n\nA **kernel** is a small, frequently executed operation such as assembling a\nmatrix, calculating a norm, or solving a factored equation. Making a kernel\nfaster can be valuable, but an engineering project pays for the complete\nsimulation: setup, candidate work, projection, reference work, replay, event\nhandling, rejected attempts, report generation, and data movement.\n\nFor example, a faster matrix solve may provide little complete-run benefit if it\nrequires repeated format conversion or causes more reference recomputations. A\ncache can reduce setup work but become harmful if it grows without a limit or\nreuses data after component values change. BAB-CS therefore retains an\noptimization only after end-to-end workloads show a gain and the authority path\nstill produces equivalent accepted results and failure causes.\n\nFor a novice engineer, the practical test is: **did the whole declared workload\nbecome faster while producing the same governed result?** A microbenchmark of one\ninner operation cannot answer that question by itself.\n\n## Separate Algorithmic Work from Wall-Clock Time\n\nWall-clock time changes with processor load, operating-system scheduling,\nlibrary versions, and hardware. BAB-CS therefore records **deterministic work\ncounters** alongside timing. These counters include candidate solves, reference\nsolves, circuit evaluations, algebraic iterations, projections, Jacobian\nevaluations, replay steps, accepted steps, and rejected attempts\n[[15]](REFERENCES.md#ref-15).\n\nA fixed-work report compares methods under a declared operation budget. A timing\nreport measures elapsed time on a named machine and environment. The two answer\ndifferent questions. Work counts help explain algorithmic cost. Timing helps\ncharacterize one implementation on one system. Neither is allowed to replace\ncorrectness evidence.\n\n## Keep Only End-to-End Improvements\n\nBAB-CS keeps a chain of guarded improvements rather than one dramatic shortcut.\nRetained work includes compiled sparse topology, batched sensitivity solves,\nreusable sparse workspaces, bounded KLU reuse, direct access to generated numeric\nstamp values, compiled built-in event schedules, and roundoff-aware evidence\nwindows. A **unit in the last place** (`ULP`) is the gap between adjacent\nfloating-point numbers near a value; ULP-aware comparisons avoid treating\nrepresentational rounding as a large physical difference.\n\nSeveral plausible optimizations were rejected after end-to-end measurement:\n\n- broad array batching of the current diode workload did not improve the\n  qualified 32-channel crossover and changed floating-operation ordering at\n  larger sizes;\n- carrying replay subdivision choices across anchors reduced some replay counts\n  but slowed measured complete workloads and did not improve authority agreement\n  consistently;\n- a general backward-Euler defect policy over-refined a simple resistor-\n  capacitor replay and increased work;\n- dynamic anchor intervals appeared faster in some switched runs only because\n  event resets suppressed independent replay; and\n- several isolated copy, norm, and residual kernels improved microbenchmarks but\n  did not produce a reliable full-simulation gain.\n\nThese negative results are engineering evidence. They show why a fast inner\noperation is not automatically a faster complete simulation or a better\nengineering result.\n\n## Prioritize the Remaining Measured Costs\n\nThe next performance work should target costs that remain visible in complete\nprofiles:\n\n1. keep KLU numeric buffers resident without weakening independent factor\n   ownership;\n2. move residual calculation closer to native factorization so the same matrix\n   data does not cross language boundaries repeatedly;\n3. expose cache hits, misses, refactors, evictions, and fallbacks before making\n   cache policy more automatic;\n4. continue method-specific replay research while enforcing a maximum elapsed\n   authority age; and\n5. expand nonlinear batching only at a larger evidence-gated workload where\n   complete simulation gains can be demonstrated.\n\nEach direction must preserve mutable parameters, deterministic failure behavior,\nsource-versus-installed equivalence, nonlinear qualification, exact event\nalignment, and generic fallback.\n\n## Know Where This Engineering Claim Stops\n\nBAB-CS is not presented as the fastest circuit simulator in general. Its current\nperformance evidence is local to declared workloads, hardware, software, and\nbackend configurations. It is also not a production semiconductor, thermal,\nelectromagnetic, or hardware-in-the-loop environment. Hardware-in-the-loop means\ntesting real controller hardware against a simulated plant.\n\nThe engineering contribution is narrower and more defensible: BAB-CS shows how\nto accelerate a circuit simulation while preserving a visible chain from model\nequations to proposed state, independent authority, accepted result, work report,\nartifact identity, and fallback behavior.\n",
      "order": 2,
      "path": "ENGINEERING_AND_PERFORMANCE_ESSAY.md",
      "readingMinutes": 9,
      "sha256": "ee0181ce6c4910918074b1bb1df91cd0ccc4eba0a0443afabe25ee0eceb65571",
      "summary": "Bounded-Authority-Based-Circuit-Simulation (BAB-CS) is engineered so that a faster numerical path cannot quietly bypass the checks that make a result reviewable. The project treats performance as an optimization problem inside a fixed…",
      "title": "Circuit Engineering and Performance in Bounded-Authority-Based-Circuit-Simulation",
      "wordCount": 1786
    },
    {
      "category": "Current Work Essays",
      "conceptIds": [
        "babcs",
        "candidate-method",
        "numerical-authority",
        "projection",
        "replay",
        "recursive-bound",
        "residual",
        "jacobian",
        "nonlinear-convergence",
        "passivity",
        "deterministic-evidence",
        "fixed-step",
        "fixed-accuracy",
        "fixed-work",
        "phase-error",
        "shadow-mode",
        "fail-closed",
        "source-wheel-equivalence",
        "python-wheel",
        "spice",
        "rc",
        "rl",
        "ab2",
        "adams-bashforth",
        "bdf2",
        "klu",
        "scipy",
        "json",
        "csv",
        "svg",
        "sha256",
        "ci",
        "ngspice"
      ],
      "headings": [
        {
          "id": "validation-release-and-claim-discipline-in-bab-cs",
          "level": 1,
          "text": "Validation, Release, and Claim Discipline in BAB-CS"
        },
        {
          "id": "why-does-validation-need-layers",
          "level": 2,
          "text": "Why Does Validation Need Layers?"
        },
        {
          "id": "how-does-the-evidence-ladder-build-confidence",
          "level": 2,
          "text": "How Does the Evidence Ladder Build Confidence?"
        },
        {
          "id": "what-does-each-test-layer-prove",
          "level": 2,
          "text": "What Does Each Test Layer Prove?"
        },
        {
          "id": "formula-and-component-tests",
          "level": 3,
          "text": "Formula and Component Tests"
        },
        {
          "id": "circuit-and-controller-tests",
          "level": 3,
          "text": "Circuit and Controller Tests"
        },
        {
          "id": "analytic-and-refined-authority-tests",
          "level": 3,
          "text": "Analytic and Refined-Authority Tests"
        },
        {
          "id": "long-horizon-and-optional-backend-tests",
          "level": 3,
          "text": "Long-Horizon and Optional-Backend Tests"
        },
        {
          "id": "fail-closed-tests",
          "level": 3,
          "text": "Fail-Closed Tests"
        },
        {
          "id": "which-question-does-each-numerical-comparison-answer",
          "level": 2,
          "text": "Which Question Does Each Numerical Comparison Answer?"
        },
        {
          "id": "what-can-external-comparison-show",
          "level": 2,
          "text": "What Can External Comparison Show?"
        },
        {
          "id": "how-does-deterministic-evidence-support-review",
          "level": 2,
          "text": "How Does Deterministic Evidence Support Review?"
        },
        {
          "id": "does-the-installed-wheel-match-the-source",
          "level": 2,
          "text": "Does the Installed Wheel Match the Source?"
        },
        {
          "id": "what-can-continuous-integration-prove",
          "level": 2,
          "text": "What Can Continuous Integration Prove?"
        },
        {
          "id": "how-do-exact-hashes-identify-artifacts",
          "level": 2,
          "text": "How Do Exact Hashes Identify Artifacts?"
        },
        {
          "id": "why-do-humans-retain-release-authority",
          "level": 2,
          "text": "Why Do Humans Retain Release Authority?"
        },
        {
          "id": "where-does-the-claim-stop",
          "level": 2,
          "text": "Where Does the Claim Stop?"
        }
      ],
      "kind": "Essay",
      "markdown": "# Validation, Release, and Claim Discipline in BAB-CS\n\n## Why Does Validation Need Layers?\n\nBounded-Authority-Based-Circuit-Simulation (`BAB-CS`) treats validation as a\nhierarchy of questions rather than one pass/fail label. A unit test can show that\none formula behaves as expected. A comparison can show that one declared case\nagrees with an independent result. A package check can show that the installable\nartifact reproduces the source evidence. A human release decision can approve\none exact set of artifacts. These are related, but they are not interchangeable.\n\nFor a novice, **validation** means collecting evidence that a declared behavior\nmatches a declared expectation. It does not mean proving that every future use\nis correct. **Qualification** means running a specified evidence process for a\nspecific source and environment. **Certification** is an independent formal\napproval process; BAB-CS does not claim certification.\n\n## How Does the Evidence Ladder Build Confidence?\n\nTreat evidence as a ladder. Each rung answers a larger question, but a convincing\nhigher-level plot cannot replace a lower-level check.\n\n1. **Formula test — was one calculation implemented correctly?** A small test\n   checks a coefficient, matrix operation, component equation, or failure rule\n   in isolation.\n2. **Circuit test — do the parts cooperate in a complete simulation path?** A\n   circuit-level test exercises proposal, projection, reference comparison,\n   acceptance, fallback, rejection, events, and reporting together.\n3. **Analytic or refined authority — is the accepted trajectory close to an\n   independently justified result?** An analytic solution is a known formula. A\n   refined authority is a more carefully recomputed numerical result.\n4. **External comparison — does a separately implemented simulator agree on the\n   same translated engineering case?** This checks for shared behavior without\n   treating the external tool as unquestionable truth.\n5. **Source-versus-wheel equivalence — does the installable package reproduce the\n   checked-out source evidence?** A wheel is the installable Python package file\n   delivered to users.\n6. **Exact-hash human approval — should this precise source and artifact set be\n   published?** A cryptographic hash is a digital fingerprint that identifies\n   exact bytes. Automation prepares this evidence; a person retains release\n   authority.\n\nThe ladder prevents a common mistake: turning “one test passed” into “the product\nis ready.” Each step records both what has been demonstrated and what remains\noutside the claim.\n\n## What Does Each Test Layer Prove?\n\nThe repository uses several layers of automated tests.\n\n### Formula and Component Tests\n\nSmall tests check variable-step Adams-Bashforth order two (`AB2`) coefficients,\nimplicit-method startup, backward differentiation formula order two (`BDF2`)\nhistory, waveform breakpoints, component validation, matrix operations, and\nfailure messages. These tests isolate one behavior so a regression can be\nlocated precisely.\n\n### Circuit and Controller Tests\n\nIntegration tests run complete circuit paths. They cover projection, candidate\nand reference pairing, correction, recursive bounds, nonlinear convergence,\npassivity, event alignment, replay, fallback, rejection, and work counters.\n**Passivity** means that a passive declared circuit may not create net energy\nfrom nothing. A **fallback** transfers authority to a safer method. A\n**rejection** refuses the current attempt and normally retries with a smaller\ntimestep.\n\n### Analytic and Refined-Authority Tests\n\nSome resistor-capacitor (`RC`), resistor-inductor (`RL`), and resonant circuits\nhave known analytic solutions, meaning formulas can calculate the expected\ntrajectory directly. Other cases use refined implicit replay, which recomputes\nthe same interval with smaller trusted steps. Analytic truth and refined replay\nare kept as different evidence types because they have different assumptions.\n\n### Long-Horizon and Optional-Backend Tests\n\nLong-horizon tests inspect accumulated phase, energy, authority age, and replay\nbehavior. Optional-backend tests exercise SciPy and SuiteSparse KLU. SciPy is a\nPython scientific-computing library. KLU is a sparse matrix solver specialized\nfor circuit-like equation systems. A skipped optional test is recorded as a\nmissing qualification tier, not silently treated as a pass.\n\n### Fail-Closed Tests\n\n**Fail closed** means refusing to produce an accepted result when required\nevidence is missing or invalid. Tests deliberately trigger nonfinite values,\nsingular equations, unsupported topologies, failed nonlinear iteration,\nexcessive residuals, invalid multistep history, passivity violations, and replay\nfailure. These tests are essential because an error message is part of the\nsimulator’s safety boundary.\n\n## Which Question Does Each Numerical Comparison Answer?\n\nThe canonical comparison matrix covers linear, nonlinear, switched, and\nlong-horizon cases. It includes raw methods, bounded candidates, reference\nmethods, active BAB-CS, and shadow BAB-CS. **Shadow mode** runs candidate logic\nand records diagnostics while the trusted reference retains accepted-state\nauthority. This supports staged adoption of a new method without allowing it to\nchange the official trajectory immediately [[15]](REFERENCES.md#ref-15).\n\nReports provide three views:\n\n- **fixed-step**, where methods receive the same nominal timestep;\n- **fixed-accuracy**, where rows are selected against a declared error target;\n  and\n- **fixed-work**, where methods are compared under a deterministic operation\n  budget.\n\nThese views answer different engineering questions. Fixed-step isolates method\nbehavior at a common resolution. Fixed-accuracy asks what work is required to\nreach a target. Fixed-work asks what result can be achieved for a controlled\nalgorithmic cost. No one view proves universal superiority.\n\n## What Can External Comparison Show?\n\nBAB-CS maps four cases to ngspice: RC step, RL step, diode clip, and switched RC.\nngspice is an open-source implementation in the SPICE family; SPICE means\n*Simulation Program with Integrated Circuit Emphasis*. The comparison requires a\ndocumented semantic translation: topology, source waveform, switch schedule,\ninitial state, output quantity, sample grid, and comparison norm must represent\nthe same engineering case [[16]](REFERENCES.md#ref-16).\n\nngspice provides independent evidence, not unquestionable truth or BAB-CS\naccepted-state authority. Agreement can increase confidence in a mapped case.\nDisagreement directs the engineer to inspect modeling semantics, tolerances,\nevent handling, interpolation, and numerical behavior. Two plots do not provide\nvalidation when the underlying models are not equivalent.\n\n## How Does Deterministic Evidence Support Review?\n\nBAB-CS produces machine-readable JavaScript Object Notation (`JSON`) and\ncomma-separated-value (`CSV`) reports, plus Scalable Vector Graphics (`SVG`)\nfigures. JSON records structured data, CSV records tables, and SVG records vector\ngraphics. Deterministic generation means that the same declared source,\nconfiguration, and environment reproduces the same required artifact bytes where\nthe format is defined as deterministic.\n\nWork counts are kept separate from timing. Timing is local characterization and\ncan vary with the machine. Deterministic work counts identify how many candidate,\nreference, projection, Jacobian, algebraic, and replay operations occurred. A\nperformance claim must name its workload, backend, hardware, software, warmup,\nrepetition policy, and comparator [[17]](REFERENCES.md#ref-17).\n\n## Does the Installed Wheel Match the Source?\n\nA Python **wheel** is an installable package file. Source-versus-wheel\nequivalence compares the checked-out source with an isolated installation of the\nbuilt wheel. The release process does more than import the wheel and run one\nexample. It rebuilds evidence from the installed artifact and compares required\nJSON, CSV, and SVG outputs with the source results [[20]](REFERENCES.md#ref-20)\n[[31]](REFERENCES.md#ref-31).\n\nWheel inspection also checks the filename, metadata, command-line entry point,\nincluded files, timestamps, and file modes. Building twice and comparing bytes\ntests **reproducible packaging**, meaning the build process creates the same\nartifact from the same frozen inputs.\n\n## What Can Continuous Integration Prove?\n\nContinuous integration (`CI`) is automated testing triggered by repository\nevents. The pull-request workflow runs the dependency-free suite, static\ncompilation checks, generation checks, package installation, and an optional\nSciPy/KLU tier. Third-party workflow actions are pinned to exact revisions so\ntheir code cannot change unnoticed [[33]](REFERENCES.md#ref-33).\n\nScheduled workflows add long-horizon tests, the complete numerical matrix,\ntiming evidence, and all mapped ngspice cases. They upload reports, figures,\nlogs, and checksums. Scheduled evidence is useful for regression detection, but\nit may run on a moving branch. It does not approve a release.\n\n## How Do Exact Hashes Identify Artifacts?\n\nA cryptographic hash is a fixed-length fingerprint of digital content. BAB-CS\nuses Secure Hash Algorithm 256-bit (`SHA-256`) values to identify source and\nartifacts. If one byte changes, the fingerprint should change. A deterministic\nmanifest records file roles, sizes, hashes, source identity, package identity,\nenvironment data, test summaries, and comparison summaries.\n\nThe verifier rejects missing, duplicate, modified, unexpected, nonfinite,\nfailed, or identity-mismatched evidence. A sorted checksum file binds the public\ncontents of the evidence bundle without attempting to include its own checksum\nrecursively [[31]](REFERENCES.md#ref-31).\n\n## Why Do Humans Retain Release Authority?\n\nFour words describe different stages and must not be blurred:\n\n- **validation** collects evidence that a declared behavior meets a declared\n  expectation;\n- **qualification** runs a named validation process for an exact source,\n  environment, and artifact set;\n- **certification** is an independent formal approval against an external\n  standard, which BAB-CS does not claim; and\n- **publication** makes an approved tag, package, release, or evidence bundle\n  available to others.\n\nAutomation deliberately stops before publication. A successful workflow may\nshow that a candidate satisfied the declared mechanical checks. It cannot decide\nthat the scientific interpretation, engineering scope, release notes, and claim\nboundary are acceptable.\n\nRelease approval must identify one exact source commit, the intended version\ntag, the wheel SHA-256 value, the manifest SHA-256 value, the workflow run, and\nthe reviewed evidence set [[19]](REFERENCES.md#ref-19)\n[[21]](REFERENCES.md#ref-21). A branch name, short hash, mutable artifact link,\ngreen status badge, or previous tag is not enough.\n\nThe repository may encode version `1.1.0` and contain complete qualification\ninfrastructure while the actual `1.1.0` release remains unapproved. The states\nmust stay separate:\n\n1. implementation exists;\n2. local tests pass;\n3. exact-commit qualification runs;\n4. evidence is reviewed;\n5. a human approves exact hashes;\n6. the tag and release are published; and\n7. the public artifact is downloaded and independently checked.\n\n## Where Does the Claim Stop?\n\nCurrent evidence supports these structural claims:\n\n- BAB-CS supervises multiple explicit and implicit candidate methods;\n- projection and independent replay are implemented;\n- failure gates and cause reporting are tested;\n- deterministic comparison and packaging tools exist; and\n- a release-evidence pipeline can bind source, wheel, environment, tests, and\n  reports.\n\nCurrent evidence does not support claims of production-SPICE replacement,\nuniversal speed superiority, arbitrary device coverage, formal enclosure of the\nunknown exact physical trajectory, hardware safety approval, or automatic\nrelease authority.\n\nThis separation is part of the project’s value. “A test passed,” “one case was\naccurate,” “the package built,” and “the release is justified” are different\nstatements. BAB-CS records the evidence and authority required for each instead\nof compressing them into one informal success label.\n",
      "order": 3,
      "path": "VALIDATION_RELEASE_AND_CLAIMS_ESSAY.md",
      "readingMinutes": 8,
      "sha256": "43db2e2ff5b7e90b6558016e714eb9cdb1530f53add5b4477b91b6478dc9b0a8",
      "summary": "Bounded-Authority-Based-Circuit-Simulation (BAB-CS) treats validation as a hierarchy of questions rather than one pass/fail label. A unit test can show that one formula behaves as expected. A comparison can show that one declared case…",
      "title": "Validation, Release, and Claim Discipline in BAB-CS",
      "wordCount": 1654
    },
    {
      "category": "Current Work Essays",
      "conceptIds": [
        "babcs",
        "candidate-method",
        "replay",
        "anchor",
        "recursive-bound",
        "residual",
        "reduced-order-model",
        "deterministic-evidence",
        "fixed-step",
        "fixed-accuracy",
        "fixed-work",
        "phase-error",
        "energy-drift",
        "empirical-coverage",
        "shadow-mode",
        "fail-closed",
        "source-wheel-equivalence",
        "python-wheel",
        "mna",
        "dae",
        "spice",
        "rc",
        "rl",
        "rlc",
        "lc",
        "dc",
        "ab2",
        "adams-bashforth",
        "be",
        "bdf2",
        "rk23",
        "klu",
        "scipy",
        "hil",
        "ngspice",
        "ltspice",
        "plecs",
        "simscape-electrical",
        "xyce"
      ],
      "headings": [
        {
          "id": "engineering-applications-and-research-roadmap-for-bab-cs",
          "level": 1,
          "text": "Engineering Applications and Research Roadmap for BAB-CS"
        },
        {
          "id": "plain-language-scope",
          "level": 2,
          "text": "Plain-Language Scope"
        },
        {
          "id": "engineering-projects-suited-to-bab-cs",
          "level": 2,
          "text": "Engineering Projects Suited to BAB-CS"
        },
        {
          "id": "1-buck-converter-schedule-screening",
          "level": 3,
          "text": "1. Buck-Converter Schedule Screening"
        },
        {
          "id": "2-h-bridge-dead-time-and-load-reversal",
          "level": 3,
          "text": "2. H-Bridge Dead Time and Load Reversal"
        },
        {
          "id": "3-direct-current-link-startup-and-interruption",
          "level": 3,
          "text": "3. Direct-Current-Link Startup and Interruption"
        },
        {
          "id": "4-diode-clamped-interface-transient",
          "level": 3,
          "text": "4. Diode-Clamped Interface Transient"
        },
        {
          "id": "5-resonant-phase-and-energy-retention",
          "level": 3,
          "text": "5. Resonant Phase and Energy Retention"
        },
        {
          "id": "6-numerical-method-selection",
          "level": 3,
          "text": "6. Numerical-Method Selection"
        },
        {
          "id": "7-solver-and-packaging-regression-qualification",
          "level": 3,
          "text": "7. Solver and Packaging Regression Qualification"
        },
        {
          "id": "8-teaching-and-reproducibility",
          "level": 3,
          "text": "8. Teaching and Reproducibility"
        },
        {
          "id": "choosing-bab-cs-or-another-simulator",
          "level": 2,
          "text": "Choosing BAB-CS or Another Simulator"
        },
        {
          "id": "current-research-facilities",
          "level": 2,
          "text": "Current Research Facilities"
        },
        {
          "id": "method-observatory",
          "level": 3,
          "text": "Method Observatory"
        },
        {
          "id": "bound-coverage-atlas",
          "level": 3,
          "text": "Bound Coverage Atlas"
        },
        {
          "id": "power-stage-sandbox",
          "level": 3,
          "text": "Power-Stage Sandbox"
        },
        {
          "id": "teaching-and-reproducibility-lab",
          "level": 3,
          "text": "Teaching and Reproducibility Lab"
        },
        {
          "id": "near-term-roadmap",
          "level": 2,
          "text": "Near-Term Roadmap"
        },
        {
          "id": "release-one-exact-candidate",
          "level": 3,
          "text": "Release One Exact Candidate"
        },
        {
          "id": "strengthen-event-authority",
          "level": 3,
          "text": "Strengthen Event Authority"
        },
        {
          "id": "improve-replay-evidence",
          "level": 3,
          "text": "Improve Replay Evidence"
        },
        {
          "id": "advance-measured-performance",
          "level": 3,
          "text": "Advance Measured Performance"
        },
        {
          "id": "medium-term-roadmap",
          "level": 2,
          "text": "Medium-Term Roadmap"
        },
        {
          "id": "long-term-roadmap",
          "level": 2,
          "text": "Long-Term Roadmap"
        }
      ],
      "kind": "Essay",
      "markdown": "# Engineering Applications and Research Roadmap for BAB-CS\n\n## Plain-Language Scope\n\nBounded-Authority-Based-Circuit-Simulation (`BAB-CS`) is best used when an\nengineering team needs to understand not only *what waveform appeared*, but also\n*why each numerical step was trusted*. A candidate method proposes the next\ncapacitor voltages and inductor currents. Independent circuit solves, reference\nmethods, correction, gates, and replay decide whether that proposal becomes the\naccepted state.\n\nThe current simulator is deliberately a **reduced-order** environment. A\nreduced-order model is a simplified model that retains the behavior needed for a\nspecific question while leaving out detail that does not belong to that study.\nThis makes BAB-CS useful for numerical qualification, early engineering\nscreening, and reproducible research. It does not make the present examples\nproduction semiconductor, magnetic, thermal, electromagnetic, protection, or\nsafety models [[11]](REFERENCES.md#ref-11)\n[[25]](REFERENCES.md#ref-25).\n\n## Engineering Projects Suited to BAB-CS\n\n### 1. Buck-Converter Schedule Screening\n\nA buck converter reduces a direct-current voltage by switching energy through\nan inductor and capacitor. BAB-CS can study a simplified scheduled converter to\ncheck event alignment, inductor-current continuity, output ripple, diode\nconduction, stored energy, fallback, and replay. The useful result is not only a\nvoltage trace; it is a record of which candidate method proposed each state and\nwhich independent authority accepted it.\n\nUse this project before detailed semiconductor loss, magnetic saturation,\nelectromagnetic-interference, and thermal studies. The sandbox example is a\n**reduced-order numerical experiment, not a production device model**.\n\n### 2. H-Bridge Dead Time and Load Reversal\n\nAn H-bridge is a four-switch arrangement that can apply positive or negative\nvoltage to a load. **Dead time** is a short interval in which opposing switches\nare both off to avoid a direct supply short. The scheduled H-bridge experiment\nuses a resistor-inductor (`RL`) load and can expose polarity changes, current\ncontinuity, exact event arrival, history resets, rejected steps, and replay work.\n\nThis is suitable for testing numerical handling of a declared switching\nschedule. It does not model body diodes, gate-driver timing uncertainty,\nshoot-through, motor mechanics, device parasitics, or hardware faults.\n\n### 3. Direct-Current-Link Startup and Interruption\n\nA direct-current link, often called a DC link, is the energy-storage path between\nparts of a power system. The BAB-CS example uses a simplified resistor-inductor-\ncapacitor (`RLC`) circuit with a declared path for continuing current after an\ninterruption. It supports studies of startup inrush, stored energy, interruption\ntiming, decay, phase, and candidate robustness.\n\nUse it to qualify the numerical experiment and the commanded event schedule.\nDo not use it as a contactor, battery, fuse, insulation, arc, fault-current, or\nhardware-safety model.\n\n### 4. Diode-Clamped Interface Transient\n\nA diode clamp limits a voltage by conducting strongly after the voltage crosses\nits operating region. The idealized Shockley diode in BAB-CS supplies a compact\nnonlinear case. **Nonlinear** means that output is not proportional to input and\nthe circuit equations require iteration.\n\nThis project can compare candidate methods, Newton convergence, residuals,\ntimestep refinement, safer-method fallback, and mapped ngspice results. A\n**residual** is the remaining mismatch in the circuit equations. Production work\nrequiring manufacturer models, package parasitics, temperature corners, or\nelectrostatic-discharge signoff belongs in a specialist SPICE workflow. SPICE\nmeans *Simulation Program with Integrated Circuit Emphasis*.\n\n### 5. Resonant Phase and Energy Retention\n\nAn inductor-capacitor (`LC`) circuit exchanges energy between a magnetic field\nand an electric field. It is useful for separating **phase drift**, the numerical\nshift in oscillation timing, from **energy drift**, numerical gain or loss of\nstored energy not caused by the declared model.\n\nBAB-CS reports phase, energy, state error, recursive bound, anchor deviation,\nand time since independent authority refresh separately. This makes it suitable\nfor long-horizon studies where one combined error norm would hide the reason a\ntrajectory is unacceptable.\n\n### 6. Numerical-Method Selection\n\nThe Method Observatory runs all seven candidate methods under the same authority\ncontroller. A team can compare:\n\n- fixed-step behavior, where every method receives the same nominal timestep;\n- fixed-accuracy behavior, where rows are selected against a declared target;\n  and\n- fixed-work behavior, where rows are compared under a deterministic operation\n  budget.\n\nThis supports selecting a method for a simplified simulation component or early\ndigital-twin prototype. A **digital twin** is software intended to represent and\npossibly track a physical system. A successful reduced-order method study does\nnot by itself validate an operational digital twin.\n\n### 7. Solver and Packaging Regression Qualification\n\nA **regression** is an unintended change in behavior after source, dependency,\nsolver, or packaging work. BAB-CS can determine whether a change altered\ntrajectories, residuals, fallback causes, work counts, deterministic reports, or\naccepted authority.\n\nThe release tooling compares the source checkout with an isolated installation\nof the built Python wheel. A **wheel** is an installable Python package file.\nSource-versus-wheel equivalence checks that the packaged implementation\nreproduces the declared source evidence rather than merely importing\nsuccessfully [[20]](REFERENCES.md#ref-20)\n[[31]](REFERENCES.md#ref-31).\n\n### 8. Teaching and Reproducibility\n\nThe Teaching and Reproducibility Lab connects modified nodal analysis (`MNA`),\na standard way to turn circuits into equations, with measured convergence,\nphase versus energy, shadow authority, deterministic packaging, and isolated\nwheel checks. **Convergence** describes how error decreases when the timestep is\nrefined. **Shadow authority** means a candidate runs and records evidence while\na trusted reference still owns the accepted state.\n\nThe lab is suitable for numerical methods, circuit simulation, software\nqualification, and reproducible research courses. It is not a substitute for\nproduction device-design or safety-validation training.\n\n## Choosing BAB-CS or Another Simulator\n\nThe tools below overlap, but their strongest roles differ. This is a workflow\nmap, not a product ranking.\n\n| Environment | Strongest role | Relationship to BAB-CS | Prefer it when |\n|---|---|---|---|\n| BAB-CS | Inspectable proposal, independent authority, replay, failure causes, deterministic work, and reproducible reduced-order experiments | Primary environment for bounded numerical-method studies | The decision depends on why a timestep passed, changed authority, replayed, or failed |\n| ngspice | Open-source SPICE simulation with device, behavioral, scripting, and mixed-signal capabilities | Current independent comparison implementation for 20 manifest-owned BAB-CS cases | Broader device and analysis coverage or a cross-implementation challenge is needed |\n| LTspice | Interactive schematic capture, SPICE simulation, waveform viewing, and vendor models | Complementary device-design and schematic environment | Engineers need vendor macromodels, rapid schematic exploration, and production-oriented analog investigation |\n| PLECS | Complete power-electronics systems, controls, thermal behavior, code generation, and hardware-in-the-loop work | Natural handoff after a bounded simplified converter study | The project needs system-level converter design, controller deployment, or real-time testing |\n| Simscape Electrical | Electrical systems connected to mechanical, thermal, hydraulic, control, motor, and grid models | Broader multidomain environment | Electrical behavior must interact with other physical domains or a larger virtual plant |\n| Xyce | SPICE-compatible simulation of extremely large circuits on serial and parallel computers | Complementary scale-oriented environment | Circuit scale and parallel execution exceed the intended BAB-CS qualification surface |\n\n**Hardware-in-the-loop** means testing real controller hardware against a\nsimulated plant. **Multidomain** means that several kinds of physics, such as\nelectrical and mechanical behavior, are solved together. BAB-CS should hand off\nto these environments when required model fidelity, deployment, or scale grows\nbeyond its declared boundary.\n\n## Current Research Facilities\n\n### Method Observatory\n\nThe observatory covers resistor-capacitor (`RC`), RL, RLC, LC, diode-clip, and\nswitched-RC cases across explicit Euler, Heun, Bogacki-Shampine order 2/3\n(`RK23`), Adams-Bashforth order two (`AB2`), backward Euler, trapezoidal\nintegration, and backward differentiation formula order two (`BDF2`). RK23 is a\nRunge-Kutta method with paired second- and third-order estimates. AB2 is an\nexplicit two-step predictor. BDF2 is an implicit two-step method.\n\n### Bound Coverage Atlas\n\nThe atlas reports actual authority error, recursive internal bound, authority-\nepoch drift, anchor deviation, phase, energy, empirical coverage, fallback, and\nrejection causes. An **authority epoch** is the interval since the current\nindependent authority basis was established. **Empirical coverage** is the\nmeasured fraction of eligible samples for which the internal bound covered the\nobserved authority error. It is not a formal enclosure theorem.\n\n### Power-Stage Sandbox\n\nThe sandbox contains the three bounded examples described above: buck-like,\nscheduled H-bridge RL, and DC-link RLC. Their classification is fixed:\n**reduced-order numerical experiments, not production device models**.\n\n### Teaching and Reproducibility Lab\n\nThe ten exercises cover MNA, fixed-step convergence, phase versus energy,\nshadow authority, deterministic wheel packaging, isolated source-versus-wheel\nequivalence, event alignment, empirical bound coverage, fallback forensics, and\nsemantic mapping of 20 ngspice cases. Each exercise includes conservative\ninterpretation prompts so students distinguish evidence from a claim.\n\n## Near-Term Roadmap\n\n### Release One Exact Candidate\n\nThe immediate release objective is to qualify version `1.1.0` from one clean,\nfrozen source commit. The complete dependency-free and optional SciPy/KLU tiers\nmust run on that commit. Numerical reports, ngspice comparisons, two wheel\nbuilds, installed-wheel results, manifests, and checksums must be reviewed. A\nhuman approver must name the exact source and artifact hashes before tagging or\npublication [[19]](REFERENCES.md#ref-19)\n[[21]](REFERENCES.md#ref-21).\n\n### Strengthen Event Authority\n\nThe next modeling priority is state-triggered event location. A state-triggered\nevent occurs when a simulated quantity crosses a condition, rather than at a\ntime known in advance. Root finding would locate that crossing accurately.\nThis work is more important than indiscriminate device count because event timing\ndirectly affects multistep history and accepted authority.\n\n### Improve Replay Evidence\n\nReplay subdivision is already method-specific for selected capacitor-and-\ninductor and switched BDF2 cases. The next step is to preserve independent event\nrefresh, enforce a maximum elapsed authority age, and generalize evidence without\nletting an adaptive schedule silently omit replay.\n\n### Advance Measured Performance\n\nThe next performance studies should focus on resident KLU numeric buffers,\nnative residual calculation, and cache observability. KLU is a sparse matrix\nsolver specialized for circuit-like systems. Cache observability means reporting\nhits, misses, refactors, evictions, and fallbacks so a cache policy can be judged\nrather than assumed [[17]](REFERENCES.md#ref-17)\n[[35]](REFERENCES.md#ref-35).\n\n## Medium-Term Roadmap\n\nDevice expansion should be ordered by evidence needs. Controlled sources,\nadditional diode behavior, and selected transistor models can follow after\nstate-triggered event handling. Every new device should arrive with analytic,\nrefined-authority, or external comparison cases. Unsupported higher-index\ndifferential-algebraic equations should continue to fail closed until a clear\nformulation and qualification plan exists.\n\nThe Bound Coverage Atlas should be used to investigate why the recursive bound\ncovers some cases and misses others. Possible research includes local Lipschitz\nestimates, which bound how strongly derivatives change; componentwise bounds,\nwhich treat state variables separately; energy-weighted norms; probabilistic\ncoverage models; and rigorous enclosures for restricted linear circuit classes.\nAny stronger claim must state its assumptions and may not generalize measured\ncoverage to arbitrary nonlinear physical error.\n\n## Long-Term Roadmap\n\nOnce circuit authority semantics, event behavior, and release evidence are\nstable, the architecture may transfer to other differential-algebraic domains.\nThe portable contribution is not the present device list. It is the separation\nof fast proposal, constraint consistency, independent correction, replay,\ndiagnostics, deterministic artifacts, and human-controlled claims.\n\nFuture work should preserve the same fail-closed gates:\n\n- no new candidate without an amplification and history model;\n- no new device without authority cases;\n- no adaptive anchor policy without independent replay control;\n- no optimization without end-to-end gain and numerical equivalence; and\n- no release claim without exact artifact review and human approval.\n\nThis roadmap keeps BAB-CS focused on its critical engineering value: making the\nreason for numerical trust as reviewable as the waveform itself.\n",
      "order": 4,
      "path": "APPLICATIONS_AND_RESEARCH_ROADMAP.md",
      "readingMinutes": 9,
      "sha256": "895f5557e7d05ab0d219cb60ce0d7ce9f417e4aee95a62424ebdfeb8a87e7941",
      "summary": "Bounded-Authority-Based-Circuit-Simulation (BAB-CS) is best used when an engineering team needs to understand not only what waveform appeared, but also why each numerical step was trusted. A candidate method proposes the next capacitor…",
      "title": "Engineering Applications and Research Roadmap for BAB-CS",
      "wordCount": 1806
    },
    {
      "category": "Current Work Essays",
      "conceptIds": [
        "babcs",
        "candidate-method",
        "projection",
        "replay",
        "newton-iteration",
        "deterministic-evidence",
        "spice",
        "klu",
        "scipy",
        "ci",
        "api",
        "doi",
        "ieee",
        "acm",
        "siam",
        "ucb",
        "bit-journal",
        "ngspice"
      ],
      "headings": [
        {
          "id": "bounded-authority-based-circuit-simulation-references",
          "level": 1,
          "text": "Bounded-Authority-Based-Circuit-Simulation References"
        },
        {
          "id": "external-foundations",
          "level": 2,
          "text": "External Foundations"
        },
        {
          "id": "repository-foundations",
          "level": 2,
          "text": "Repository Foundations"
        },
        {
          "id": "root-finding-foundations",
          "level": 2,
          "text": "Root-Finding Foundations"
        }
      ],
      "kind": "Reference",
      "markdown": "# Bounded-Authority-Based-Circuit-Simulation References\n\nThis bibliography separates external foundations from repository evidence. The\nexternal sources explain the established numerical-analysis, sparse-linear-\nalgebra, and circuit-simulation context. The repository sources define what\nBAB-CS actually implements and what it is permitted to claim.\n\n## External Foundations\n\n<a id=\"ref-1\"></a>\n1. C.-W. Ho, A. E. Ruehli, and P. A. Brennan, “The Modified Nodal Approach to\n   Network Analysis,” *IEEE Transactions on Circuits and Systems*, vol. 22,\n   no. 6, pp. 504–509, 1975. DOI:\n   [10.1109/TCS.1975.1084079](https://doi.org/10.1109/TCS.1975.1084079).\n\n<a id=\"ref-2\"></a>\n2. L. W. Nagel, *SPICE2: A Computer Program to Simulate Semiconductor\n   Circuits*, Technical Report UCB/ERL M520, University of California,\n   Berkeley, 1975.\n   [Berkeley report record](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1975/9602.html).\n\n<a id=\"ref-3\"></a>\n3. G. G. Dahlquist, “A Special Stability Problem for Linear Multistep\n   Methods,” *BIT Numerical Mathematics*, vol. 3, pp. 27–43, 1963. DOI:\n   [10.1007/BF01963532](https://doi.org/10.1007/BF01963532).\n\n<a id=\"ref-4\"></a>\n4. P. Bogacki and L. F. Shampine, “A 3(2) Pair of Runge–Kutta Formulas,”\n   *Applied Mathematics Letters*, vol. 2, no. 4, pp. 321–325, 1989. DOI:\n   [10.1016/0893-9659(89)90079-7](https://doi.org/10.1016/0893-9659(89)90079-7).\n\n<a id=\"ref-5\"></a>\n5. L. F. Shampine and P. Bogacki, “The Effect of Changing the Stepsize in\n   Linear Multistep Codes,” *SIAM Journal on Scientific and Statistical\n   Computing*, vol. 10, no. 6, pp. 1010–1023, 1989. DOI:\n   [10.1137/0910060](https://doi.org/10.1137/0910060).\n\n<a id=\"ref-6\"></a>\n6. E. Eich, “Convergence Results for a Coordinate Projection Method Applied to\n   Mechanical Systems with Algebraic Constraints,” *SIAM Journal on Numerical\n   Analysis*, vol. 30, no. 5, pp. 1467–1482, 1993. DOI:\n   [10.1137/0730076](https://doi.org/10.1137/0730076).\n\n<a id=\"ref-7\"></a>\n7. J. W. Demmel, S. C. Eisenstat, J. R. Gilbert, X. S. Li, and J. W. Liu,\n   “A Supernodal Approach to Sparse Partial Pivoting,” Technical Report\n   UCB/CSD-95-883, 1995.\n   [Netlib report](https://www.netlib.org/lapack/lawnspdf/lawn103.pdf).\n\n<a id=\"ref-8\"></a>\n8. H. Vogt, G. Atkinson, D. Warning, P. Nenzi, and contributors,\n   *Ngspice User’s Manual*.\n   [Official manual](https://ngspice.sourceforge.io/docs/ngspice-html-manual/manual.xhtml).\n\n<a id=\"ref-9\"></a>\n9. SciPy developers, “`scipy.sparse.linalg.splu`.”\n   [SciPy API documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.splu.html).\n\n<a id=\"ref-10\"></a>\n10. Python Packaging Authority, “Binary Distribution Format.”\n    [Python packaging specification](https://packaging.python.org/en/latest/specifications/binary-distribution-format/).\n\n## Repository Foundations\n\n<a id=\"ref-11\"></a>\n11. [Project overview and command reference](../README.md).\n\n<a id=\"ref-12\"></a>\n12. [BAB-CSv1 normative specification](BAB_CSV1_SPEC.md).\n\n<a id=\"ref-13\"></a>\n13. [BAB-CSv1 error-bound model](ERROR_BOUND_MODEL.md).\n\n<a id=\"ref-14\"></a>\n14. [Bounded candidate integrators](BOUNDED_CANDIDATES.md).\n\n<a id=\"ref-15\"></a>\n15. [Comparison protocol](COMPARISON_PROTOCOL.md).\n\n<a id=\"ref-16\"></a>\n16. [External comparison protocol and results](EXTERNAL_COMPARISON.md).\n\n<a id=\"ref-17\"></a>\n17. [Performance optimization audit](PERFORMANCE_OPTIMIZATION_AUDIT.md).\n\n<a id=\"ref-18\"></a>\n18. [Tests and comparisons qualification audit](TESTS_AND_COMPARISONS_AUDIT.md).\n\n<a id=\"ref-19\"></a>\n19. [Release qualification plan](../BAB-CS-Release-Qualification-Plan.md).\n\n<a id=\"ref-20\"></a>\n20. [Release qualification implementation audit](RELEASE_QUALIFICATION_IMPLEMENTATION_AUDIT.md).\n\n<a id=\"ref-21\"></a>\n21. [Draft release document](../RELEASE.md).\n\n<a id=\"ref-22\"></a>\n22. [Canonical benchmark manifest](../benchmarks/manifest.json).\n\n<a id=\"ref-23\"></a>\n23. [Bounded controller implementation](../src/babcs/bounded.py).\n\n<a id=\"ref-24\"></a>\n24. [Candidate-integrator implementation](../src/babcs/candidates.py).\n\n<a id=\"ref-25\"></a>\n25. [Circuit model and algebraic projection implementation](../src/babcs/model.py).\n\n<a id=\"ref-26\"></a>\n26. [Implicit integrators and replay implementation](../src/babcs/integrators.py).\n\n<a id=\"ref-27\"></a>\n27. [Dense and optional sparse linear-algebra implementation](../src/babcs/linalg.py).\n\n<a id=\"ref-28\"></a>\n28. [Simulation loop and event handling](../src/babcs/simulator.py).\n\n<a id=\"ref-29\"></a>\n29. [Deterministic comparison runner](../tools/compare_methods.py).\n\n<a id=\"ref-30\"></a>\n30. [External ngspice comparison tool](../tools/compare_external.py).\n\n<a id=\"ref-31\"></a>\n31. [Release evidence and verification tool](../tools/release_evidence.py).\n\n<a id=\"ref-32\"></a>\n32. [Regression and qualification test suite](../tests/).\n\n<a id=\"ref-33\"></a>\n33. [Continuous integration workflow](../.github/workflows/ci.yml),\n    [scheduled comparison workflow](../.github/workflows/comparisons.yml), and\n    [release qualification workflow](../.github/workflows/release-qualification.yml).\n\n<a id=\"ref-34\"></a>\n34. [BAB-CSv1 completion audit](BAB_CSV1_COMPLETION_AUDIT.md).\n\n<a id=\"ref-35\"></a>\n35. [Optional SuiteSparse KLU adapter](../src/babcs/_klu.py).\n\n## Root-Finding Foundations\n\n<a id=\"ref-36\"></a>\n36. L. V. Kantorovich, “On Newton's Method,” *Trudy Matematicheskogo\n    Instituta imeni V. A. Steklova*, vol. 28, pp. 104–144, 1949.\n    [Steklov Institute record](https://www.mathnet.ru/eng/tm/v28/p104).\n\n<a id=\"ref-37\"></a>\n37. R. P. Brent, “An Algorithm with Guaranteed Convergence for Finding a Zero\n    of a Function,” *The Computer Journal*, vol. 14, no. 4, pp. 422–425,\n    1971. DOI:\n    [10.1093/comjnl/14.4.422](https://doi.org/10.1093/comjnl/14.4.422).\n\n<a id=\"ref-38\"></a>\n38. J. C. P. Bus and T. J. Dekker, “Two Efficient Algorithms with Guaranteed\n    Convergence for Finding a Zero of a Function,” *ACM Transactions on\n    Mathematical Software*, vol. 1, no. 4, pp. 330–345, 1975. DOI:\n    [10.1145/355656.355659](https://doi.org/10.1145/355656.355659).\n\n<a id=\"ref-39\"></a>\n39. C. J. F. Ridders, “A New Algorithm for Computing a Single Root of a Real\n    Continuous Function,” *IEEE Transactions on Circuits and Systems*,\n    vol. 26, no. 11, pp. 979–980, 1979. DOI:\n    [10.1109/TCS.1979.1084580](https://doi.org/10.1109/TCS.1979.1084580).\n\n<a id=\"ref-40\"></a>\n40. G. E. Alefeld, F. A. Potra, and Y. Shi, “Algorithm 748: Enclosing Zeros of\n    Continuous Functions,” *ACM Transactions on Mathematical Software*,\n    vol. 21, no. 3, pp. 327–344, 1995. DOI:\n    [10.1145/210089.210111](https://doi.org/10.1145/210089.210111).\n\n<a id=\"ref-41\"></a>\n41. S. C. Eisenstat and H. F. Walker, “Globally Convergent Inexact Newton\n    Methods,” *SIAM Journal on Optimization*, vol. 4, no. 2, pp. 393–422,\n    1994. DOI:\n    [10.1137/0804022](https://doi.org/10.1137/0804022).\n\n<a id=\"ref-42\"></a>\n42. R. E. Moore, “A Test for Existence of Solutions to Nonlinear Systems,”\n    *SIAM Journal on Numerical Analysis*, vol. 14, no. 4, pp. 611–615, 1977.\n    DOI: [10.1137/0714040](https://doi.org/10.1137/0714040).\n\n<a id=\"ref-43\"></a>\n43. R. Krawczyk, “Newton-Algorithmen zur Bestimmung von Nullstellen mit\n    Fehlerschranken,” *Computing*, vol. 4, pp. 187–201, 1969. DOI:\n    [10.1007/BF02234767](https://doi.org/10.1007/BF02234767).\n\n<a id=\"ref-44\"></a>\n44. I. F. D. Oliveira and R. H. C. Takahashi, “An Enhancement of the\n    Bisection Method Average Performance Preserving Minmax Optimality,”\n    *ACM Transactions on Mathematical Software*, vol. 47, no. 1, article 5,\n    pp. 1–24, 2021. DOI:\n    [10.1145/3423597](https://doi.org/10.1145/3423597).\n\n<a id=\"ref-45\"></a>\n45. E. R. Hansen and R. I. Greenberg, “An Interval Newton Method,”\n    *Applied Mathematics and Computation*, vol. 12, nos. 2–3, pp. 89–98,\n    1983. DOI:\n    [10.1016/0096-3003(83)90001-2](https://doi.org/10.1016/0096-3003(83)90001-2).\n",
      "order": 5,
      "path": "REFERENCES.md",
      "readingMinutes": 6,
      "sha256": "4e7467d8e31475dc4bf9afa0ba3f8a94b2a5002547a450215e0a22b2205c3ce5",
      "summary": "This bibliography separates external foundations from repository evidence. The external sources explain the established numerical-analysis, sparse-linear- algebra, and circuit-simulation context. The repository sources define what…",
      "title": "Bounded-Authority-Based-Circuit-Simulation References",
      "wordCount": 1158
    },
    {
      "category": "Documentation Home",
      "conceptIds": [
        "ourd",
        "babcs",
        "candidate-method",
        "replay",
        "reduced-order-model",
        "deterministic-evidence",
        "phase-error",
        "energy-drift",
        "shadow-mode",
        "python-wheel",
        "mna",
        "spice",
        "svg",
        "html",
        "hil",
        "ngspice"
      ],
      "headings": [
        {
          "id": "bounded-authority-based-circuit-simulation-documentation",
          "level": 1,
          "text": "Bounded-Authority-Based-Circuit-Simulation Documentation"
        },
        {
          "id": "current-work-essays",
          "level": 2,
          "text": "Current Work Essays"
        },
        {
          "id": "start-here",
          "level": 2,
          "text": "Start Here"
        },
        {
          "id": "numerical-design",
          "level": 2,
          "text": "Numerical Design"
        },
        {
          "id": "tests-and-comparisons",
          "level": 2,
          "text": "Tests and Comparisons"
        },
        {
          "id": "teaching-lab-tutorials",
          "level": 2,
          "text": "Teaching Lab Tutorials"
        },
        {
          "id": "qualification-and-release",
          "level": 2,
          "text": "Qualification and Release"
        },
        {
          "id": "project-policies",
          "level": 2,
          "text": "Project Policies"
        }
      ],
      "kind": "Overview",
      "markdown": "# Bounded-Authority-Based-Circuit-Simulation Documentation\n\nBounded-Authority-Based-Circuit-Simulation (`BAB-CS`) is a transient circuit\nsimulator for engineering studies in which the reason for trusting a numerical\nresult must remain visible. A candidate method proposes the next capacitor\nvoltages and inductor currents. Separate circuit-equation solves, reference\nmethods, correction rules, rejection gates, and independent replay decide\nwhether that proposal becomes the accepted state.\n\nBAB-CS is particularly suited to reduced-order models: deliberately simplified\ncircuits that retain the behavior needed for one engineering question. Current\nuses include power-conversion schedule screening, analog and resonant transients,\nnumerical-method qualification, failure diagnosis, and reproducible comparison\nbetween source code and the installed Python wheel. A wheel is an installable\nPython package file.\n\nBAB-CS complements rather than replaces SPICE, power-electronics, multidomain,\nhardware-in-the-loop, and large-scale parallel simulation software. SPICE means\n*Simulation Program with Integrated Circuit Emphasis*. Hardware-in-the-loop\nmeans testing real controller hardware against a simulated plant. Multidomain\nmeans solving interacting electrical, mechanical, thermal, or other physical\nsystems together. The BAB-CS bound applies to its implemented numerical error\nmodel, not to the unknown exact physical trajectory.\n\n## Current Work Essays\n\n- [Current project and integrated design](CURRENT_WORK.md)\n- [Numerical methods and error bounding](NUMERICAL_METHODS_ESSAY.md)\n- [Circuit engineering and performance work](ENGINEERING_AND_PERFORMANCE_ESSAY.md)\n- [Validation, release, and claim discipline](VALIDATION_RELEASE_AND_CLAIMS_ESSAY.md)\n- [Applications and research roadmap](APPLICATIONS_AND_RESEARCH_ROADMAP.md)\n- [Shared bibliography and repository references](REFERENCES.md)\n\n## Start Here\n\n- [Searchable HTML document tree](html/index.html)\n- [HTML documentation redesign and rewrite plan](../HTML_DOCUMENT_REDESIGN_AND_REWRITE_PLAN.md)\n- [In-text learning guide and novice essay plan](../INTEXT_LEARNING_GUIDE_AND_NOVICE_ESSAY_PLAN.md)\n- [OURD Coding Agent-guided visual and grammar redesign plan](../OURD_HTML_TREE_VISUAL_GRAMMAR_REDESIGN_PLAN.md) — the OURD Coding Agent is the governed local advisory agent used for the review; it did not approve or mutate the redesign.\n- [SVG circuit and simulation figures implementation plan](../SVG_CIRCUIT_AND_SIMULATION_FIGURES_IMPLEMENTATION_PLAN.md)\n- [ngspice and teaching-tutorial expansion plan](../NGSPICE_AND_TEACHING_TUTORIAL_EXPANSION_PLAN.md)\n- [Project overview and usage](../README.md)\n- [Version 1 normative specification](BAB_CSV1_SPEC.md)\n- [Version 1 implementation plan](../IMPLEMENTATION_PLAN.md)\n- [Release draft](../RELEASE.md)\n\n## Numerical Design\n\n- [Architecture and authority flow](ARCHITECTURE.md)\n- [Error-bound model](ERROR_BOUND_MODEL.md)\n- [Bounded candidate integrators](BOUNDED_CANDIDATES.md)\n- [Bounded and interval Newton research](BOUNDED_NEWTON.md)\n- [Minimal reproducible research example](MINIMAL_REPRODUCIBLE_RESEARCH.md)\n\n## Tests and Comparisons\n\n- [Comparison protocol](COMPARISON_PROTOCOL.md)\n- [Method Observatory](METHOD_OBSERVATORY.md)\n- [Bound Coverage Atlas](BOUND_COVERAGE_ATLAS.md)\n- [Power-Stage Sandbox](POWER_STAGE_SANDBOX.md)\n- [Teaching and Reproducibility Lab](TEACHING_AND_REPRODUCIBILITY_LAB.md)\n- [ngspice 20-case mapping atlas](NGSPICE_CASE_ATLAS.md)\n- [BAB-CS versus ngspice runtime benchmark](NGSPICE_RUNTIME_BENCHMARK.md)\n- [BAB-CS versus ngspice runtime benchmark plan](../BABCS_NGSPICE_RUNTIME_BENCHMARK_PLAN.md)\n- [Observatory, atlas, sandbox, and lab implementation audit](OBSERVATORY_ATLAS_SANDBOX_LAB_IMPLEMENTATION_AUDIT.md)\n- [ngspice and teaching-tutorial expansion plan](../NGSPICE_AND_TEACHING_TUTORIAL_EXPANSION_PLAN.md)\n- [External comparison](EXTERNAL_COMPARISON.md)\n- [Tests and comparisons implementation plan](../TESTS_AND_COMPARISONS_IMPLEMENTATION_PLAN.md)\n- [Tests and comparisons qualification audit](TESTS_AND_COMPARISONS_AUDIT.md)\n- [Performance optimization audit](PERFORMANCE_OPTIMIZATION_AUDIT.md)\n- [Qualification summary evidence](QUALIFICATION_SUMMARY.md)\n\n## Teaching Lab Tutorials\n\n- [Scientific results report for Tutorials 1–10](TUTORIAL_SCIENTIFIC_RESULTS_REPORT.md)\n- [Tutorial 1: Modified nodal analysis and state ownership](tutorials/01_MNA_STATE_OWNERSHIP.md)\n- [Tutorial 2: Convergence by measured refinement](tutorials/02_CONVERGENCE_BY_REFINEMENT.md)\n- [Tutorial 3: Phase error versus energy error](tutorials/03_PHASE_VERSUS_ENERGY.md)\n- [Tutorial 4: Shadow authority](tutorials/04_SHADOW_AUTHORITY.md)\n- [Tutorial 5: Deterministic packaging](tutorials/05_DETERMINISTIC_PACKAGING.md)\n- [Tutorial 6: Source versus installed-wheel equivalence](tutorials/06_SOURCE_WHEEL_EQUIVALENCE.md)\n- [Tutorial 7: Exact event alignment](tutorials/07_EVENT_ALIGNMENT.md)\n- [Tutorial 8: Empirical bound coverage](tutorials/08_EMPIRICAL_BOUND_COVERAGE.md)\n- [Tutorial 9: Fallback and rejection forensics](tutorials/09_FALLBACK_AND_REJECTION_FORENSICS.md)\n- [Tutorial 10: Semantic mapping to ngspice](tutorials/10_SEMANTIC_NGSPICE_MAPPING.md)\n\n## Qualification and Release\n\n- [Version 1 completion audit](BAB_CSV1_COMPLETION_AUDIT.md)\n- [Release qualification plan](../BAB-CS-Release-Qualification-Plan.md)\n- [Release qualification implementation plan](../BAB-CS-Release-Qualification-Implementation-Plan.md)\n- [Release qualification implementation audit](RELEASE_QUALIFICATION_IMPLEMENTATION_AUDIT.md)\n- [Repository audit implementation plan](../REPOSITORY_AUDIT_IMPLEMENTATION_PLAN.md)\n- [Licence decision record](LICENCE_DECISION.md)\n\n## Project Policies\n\n- [Citation metadata](../CITATION.cff)\n- [Changelog](../CHANGELOG.md)\n- [Contribution guide](../CONTRIBUTING.md)\n- [Security policy](../SECURITY.md)\n",
      "order": 0,
      "path": "index.md",
      "readingMinutes": 3,
      "sha256": "4cb11fe9e00338aca1d755294923859b0ea984bf2f73fd98e53260de4c76630d",
      "summary": "Bounded-Authority-Based-Circuit-Simulation (BAB-CS) is a transient circuit simulator for engineering studies in which the reason for trusting a numerical result must remain visible. A candidate method proposes the next capacitor…",
      "title": "Bounded-Authority-Based-Circuit-Simulation Documentation",
      "wordCount": 582
    },
    {
      "category": "Numerical Design",
      "conceptIds": [
        "babcs",
        "candidate-method",
        "numerical-authority",
        "projection",
        "replay",
        "anchor",
        "residual",
        "passivity",
        "deterministic-evidence",
        "mna",
        "klu",
        "scipy"
      ],
      "headings": [
        {
          "id": "bounded-authority-based-circuit-simulation-architecture",
          "level": 1,
          "text": "Bounded-Authority-Based-Circuit-Simulation Architecture"
        },
        {
          "id": "authority-layers",
          "level": 2,
          "text": "Authority Layers"
        },
        {
          "id": "acceleration-boundary",
          "level": 2,
          "text": "Acceleration Boundary"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Design",
      "markdown": "# Bounded-Authority-Based-Circuit-Simulation Architecture\n\nBounded-Authority-Based-Circuit-Simulation is a supervisory\ntransient-integration architecture. Candidate methods may propose work, but\nindependently checked evidence controls acceptance.\n\n```mermaid\nflowchart TD\n    A[JSON circuit and simulation configuration] --> B[Semiexplicit MNA model]\n    B --> C[Candidate integrator]\n    B --> D[Independent implicit reference]\n    C --> E[Algebraic projection]\n    D --> F[Reference residual gate]\n    E --> G[Candidate/reference comparison]\n    F --> G\n    G --> H[Contractive correction]\n    H --> I[Corrected algebraic projection]\n    I --> J{Acceptance gates}\n    J -->|pass| K[Accepted state and recursive bound]\n    J -->|fail| L[Implicit reference authority or timestep rejection]\n    K --> M{Anchor or event boundary?}\n    M -->|periodic/safety anchor| N[Independent refined replay]\n    M -->|event| O[Exact boundary and history reset]\n    M -->|no| C\n    N --> P{Replay evidence passes?}\n    P -->|yes| Q[Replace endpoint with replay authority]\n    P -->|no| L\n    Q --> C\n    O --> C\n\n    R[Dense solver] --> B\n    S[SciPy SuperLU] --> B\n    T[SuiteSparse KLU] --> B\n    U[Guarded chord and Schur predictors] --> B\n    S -. acceleration only .-> R\n    T -. failure restores validated fallback .-> S\n    U -. proposal only .-> R\n```\n\n## Authority Layers\n\n1. **Model authority:** circuit topology, values, source waveforms, and the\n   semiexplicit MNA partition define the equations.\n2. **Projection authority:** every accepted candidate endpoint must satisfy the\n   algebraic manifold and full residual gates.\n3. **Reference authority:** an independently solved implicit method owns shadow\n   mode and controls active-mode comparison and fallback.\n4. **Bound authority:** contraction, recursive-error, passivity, residual, and\n   work caps control whether a candidate can remain active.\n5. **Replay authority:** periodic and safety anchors independently replay the\n   interval, replace provisional endpoints, and rebuild multistep history.\n6. **Release authority:** deterministic tests and artifacts are evidence; exact\n   hash human approval controls tagging and publication.\n\n## Acceleration Boundary\n\nDense, SciPy, KLU, topology caching, batched sensitivity, sparse workspaces,\nquartic guesses, chord factors, and Schur updates reduce work. None becomes a\nnew acceptance authority. Structural mismatch, singularity, residual failure,\nline-search failure, or stale evidence restores a validated path or rejects the\nstep.\n\n## Claim Boundary\n\nBAB-CS reports several distinct numerical bounds. It does not claim exact\nindefinite trajectory accuracy, unconditional stability of an explicit method,\nor a machine-checked interval proof for the complete nonlinear circuit solver.\nSee `ERROR_BOUND_MODEL.md`, `BOUNDED_CANDIDATES.md`, and\n`VALIDATION_RELEASE_AND_CLAIMS_ESSAY.md` for the detailed boundaries.\n",
      "order": 0,
      "path": "ARCHITECTURE.md",
      "readingMinutes": 2,
      "sha256": "2576961ff6f36bdea5ea6bfdb9c1a8e7f8a7e1c288cdf6b87e502700d54f0234",
      "summary": "Bounded-Authority-Based-Circuit-Simulation is a supervisory transient-integration architecture. Candidate methods may propose work, but independently checked evidence controls acceptance.",
      "title": "Bounded-Authority-Based-Circuit-Simulation Architecture",
      "wordCount": 357
    },
    {
      "category": "Numerical Design",
      "conceptIds": [
        "babcs",
        "replay",
        "anchor",
        "recursive-bound",
        "residual",
        "jacobian",
        "stiffness",
        "passivity",
        "phase-error",
        "empirical-coverage",
        "mna",
        "ab2"
      ],
      "headings": [
        {
          "id": "bounded-authority-based-circuit-simulation-v1-error-bound-model",
          "level": 1,
          "text": "Bounded-Authority-Based-Circuit-Simulation v1 Error-Bound Model"
        },
        {
          "id": "predictor",
          "level": 2,
          "text": "Predictor"
        },
        {
          "id": "correction",
          "level": 2,
          "text": "Correction"
        },
        {
          "id": "recursive-bound",
          "level": 2,
          "text": "Recursive Bound"
        },
        {
          "id": "independent-anchor",
          "level": 2,
          "text": "Independent Anchor"
        },
        {
          "id": "passivity-defect",
          "level": 2,
          "text": "Passivity Defect"
        },
        {
          "id": "limits",
          "level": 2,
          "text": "Limits"
        },
        {
          "id": "empirical-coverage-interpretation",
          "level": 2,
          "text": "Empirical Coverage Interpretation"
        }
      ],
      "kind": "Design",
      "markdown": "# Bounded-Authority-Based-Circuit-Simulation v1 Error-Bound Model\n\n## Predictor\n\nFor an index-1 reduced system `z' = f(t, z)`, variable-step AB2 produces\n\n```text\nz_ab = z_n + h * ((1 + r/2) f_n - (r/2) f_(n-1)).\n```\n\nThe implementation estimates a conservative predictor amplification from the\ninfinity norms of finite-difference differential Jacobians:\n\n```text\nG = max(1, 1 + h * ((1 + r/2) ||J_n|| + (r/2) ||J_(n-1)||)).\n```\n\nThis is deliberately conservative and is used as a runtime gate rather than a\nclaim that the estimate is spectrally exact.\n\n## Correction\n\nWith correction gain `gamma`, the provisional closed-loop estimate is\n\n```text\nq = (1 - gamma) G.\n```\n\nThe integrator increases `gamma` to target `q <= target_contraction`. If the\nconfigured correction range cannot establish `q < 1`, or if the stiffness gate\nfires, the implicit reference receives full authority and `q` becomes zero\nrelative to that local reference.\n\n## Recursive Bound\n\nThe accepted-step estimate is\n\n```text\ndelta = corrected_reference_error + normalized_residual\nB_next = q * B_current + delta.\n```\n\nIf `q <= q_max < 1` and `delta <= delta_max`, then\n\n```text\nB_n <= q_max^n B_0 + delta_max / (1 - q_max).\n```\n\nThe recorded estimate is reset after independent re-anchoring and multistep\nhistory resets. Event processing first performs an independent replay refresh;\nthe subsequent history reset does not create a second authority generation.\n\n## Independent Anchor\n\nThe local implicit reference used in each step begins from the accepted current\nstate and therefore is not fully independent of accumulated trajectory error.\nThe periodic anchor addresses this by replaying from an earlier trusted\ncheckpoint using smaller implicit steps.\n\nThe anchor deviation is\n\n```text\neta_anchor = ||z_provisional - z_replay||_W.\n```\n\nThe replay state replaces the provisional state whether the anchor is routine\nor exceeds the safety cap. Exceeding the cap is recorded as a safety re-anchor.\n\nFor mixed capacitor/inductor circuits using trapezoidal replay, BAB-CS can start\nat the configured minimum refinement and estimate the local replay error without\nanother circuit solve. For consecutive replay derivatives `f_(k-1)`, `f_k`, and\n`f_(k+1)` separated by `h_0` and `h_1`, it estimates the trapezoidal quadrature\ndefect as\n\n```text\nd_k = h_1^3 / (6 (h_0 + h_1))\n      * ((f_(k+1) - f_k) / h_1 - (f_k - f_(k-1)) / h_0).\n```\n\n`||d_k||_W` is scaled with the same state tolerances as the controller. If the\nmaximum replay defect exceeds `anchor_embedded_error_cap`, the complete replay\nrestarts from the trusted anchor with a finer subdivision predicted from the\ncubic local-error model. The subdivision is capped at `anchor_substeps`; that\ncap is the previous fixed-resolution authority, so estimator failure falls back\nto the prior design rather than accepting an unqualified coarser replay.\nNon-finite replay evidence still rejects the step. Known event boundaries force\nan independent replay from the trusted anchor to the exact event time with at\nleast eight refinement subdivisions. This forced replay does not use adaptive\nsubdivision reduction. Replay-native energy evidence and the final anchored\nalgebraic/full residuals are checked before the event state is accepted. Only\nafter that replacement does the simulator clear multistep history; the trusted\nanchor and generation remain those established by the replay. The next step\nuses the configured reference method for implicit startup.\n\n## Passivity Defect\n\nFor stored energy `H`, source power `P_s`, and dissipated power `P_d`, BAB-CS\nuses the trapezoidal work estimate\n\n```text\ndefect = H_(n+1) - H_n - h/2 * ((P_s,n - P_d,n) + (P_s,n+1 - P_d,n+1)).\n```\n\nOnly positive defect is treated as artificial numerical energy injection for\nthe hard passivity gate. Signed balance error is still logged so numerical\ndamping remains visible.\n\n## Limits\n\n- A small MNA residual does not imply a small trajectory error.\n- Bounded energy does not imply bounded oscillator phase.\n- A local implicit corrector is not an independent global anchor.\n- Chaotic or physically unstable circuits cannot have indefinite exact\n  trajectory agreement guaranteed by this mechanism.\n- The finite-difference Jacobian norm is a conservative stiffness indicator,\n  not a complete absolute-stability analysis.\n\n## Empirical Coverage Interpretation\n\nThe Bound Coverage Atlas compares two different quantities without conflating\nthem. `actual_authority_error` measures distance from the declared analytic or\nrefined-replay authority. `authority_epoch_drift_error` measures accumulated\ndrift since the latest independent anchor. The recursive internal bound is\ncompared with epoch drift only on eligible non-anchor, non-event, finite,\npositive-bound samples.\n\nThe reported empirical coverage ratio is therefore a measured property of the\ndeclared cases, configurations, source state, and authority. It is not a formal\nenclosure theorem, does not convert the reference method into exact physical\ntruth, and does not justify extrapolation to unmeasured circuits. Anchor\ndeviation, phase, and energy remain separate evidence because none is a\nsubstitute for the others.\n",
      "order": 1,
      "path": "ERROR_BOUND_MODEL.md",
      "readingMinutes": 4,
      "sha256": "26ca9448f38565554a154b280c6fe4fc39f6f16a4f109cf216d6832ce3d28eb4",
      "summary": "For an index-1 reduced system z' = f(t, z), variable-step AB2 produces",
      "title": "Bounded-Authority-Based-Circuit-Simulation v1 Error-Bound Model",
      "wordCount": 721
    },
    {
      "category": "Numerical Design",
      "conceptIds": [
        "babcs",
        "numerical-authority",
        "projection",
        "replay",
        "recursive-bound",
        "residual",
        "jacobian",
        "stiffness",
        "passivity",
        "deterministic-evidence",
        "shadow-mode",
        "factorization",
        "mna",
        "rc",
        "lc",
        "ab2",
        "ab3",
        "be",
        "bdf2",
        "rk23"
      ],
      "headings": [
        {
          "id": "bounded-candidate-integrators",
          "level": 1,
          "text": "Bounded Candidate Integrators"
        },
        {
          "id": "candidate-set",
          "level": 2,
          "text": "Candidate Set"
        },
        {
          "id": "shared-correction",
          "level": 2,
          "text": "Shared Correction"
        },
        {
          "id": "amplification-models",
          "level": 2,
          "text": "Amplification Models"
        },
        {
          "id": "embedded-fast-path",
          "level": 2,
          "text": "Embedded Fast Path"
        },
        {
          "id": "selection-guidance",
          "level": 2,
          "text": "Selection Guidance"
        },
        {
          "id": "local-characterization",
          "level": 2,
          "text": "Local Characterization"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Design",
      "markdown": "# Bounded Candidate Integrators\n\nBAB-CS keeps one error-bounding controller and attaches it to multiple candidate\nintegrators. The candidate proposes the differential state; the controller owns\nalgebraic projection, independent reference authority, correction, residual and\npassivity gates, recursive error modeling, event resets, and periodic replay.\n\n## Candidate Set\n\n| Candidate | Nominal order | Candidate work | Embedded estimate | Deferred-reference eligible |\n| --- | ---: | --- | --- | --- |\n| `explicit_euler` | 1 | one projected endpoint | none | no |\n| `heun` | 2 | Euler stage plus projected Heun endpoint | Euler/Heun difference | yes |\n| `rk23` | 3 | three projected Bogacki-Shampine stages | embedded order-2 state | yes |\n| `ab2` | 2 | one projected endpoint after implicit startup | Euler/AB2 difference | yes |\n| `backward_euler` | 1 | one implicit candidate solve | none | no |\n| `trapezoidal` | 2 | one implicit candidate solve | none | no |\n| `bdf2` | 2 | one implicit candidate solve with BE startup | none | no |\n\nAn active implicit candidate must use a different implicit `reference_method`.\nThis prevents a zero candidate/reference difference from being mislabeled as an\nindependent defect estimate. The comparison runner uses trapezoidal reference\nfor backward Euler and BDF2 candidates, and BDF2 reference for trapezoidal.\n\n## Shared Correction\n\nFor candidate endpoint `z_c`, independent reference endpoint `z_r`, and\ncorrection gain `gamma`, the accepted differential proposal is\n\n```text\nz_* = (1 - gamma) z_c + gamma z_r\n```\n\nThe circuit then projects `z_*` onto the algebraic MNA manifold. If projection,\npassivity, stiffness, amplification, or the recursive bound fails its gate,\n`gamma = 1` transfers full authority to `z_r`.\n\nWith candidate amplification estimate `G_c`, the corrected propagation model is\n\n```text\nG_closed = (1 - gamma) G_c\nB_(n+1) = G_closed B_n + d_n\n```\n\nwhere `d_n` is corrected/reference scaled deviation plus the normalized\nalgebraic/full-residual contribution. The default fixed target chooses `gamma`\nso `G_closed <= target_contraction`. Setting `contraction_rate = mu` instead\nuses `exp(-mu h)`, making `gamma = O(h)` for a smooth high-order candidate and\navoiding an unnecessary fixed blend that can reduce observed order.\n\n## Amplification Models\n\nLet `x = h L`, where `L` is the differential Jacobian infinity norm multiplied\nby `jacobian_safety_factor`. Built-in `Circuit` models calculate this Jacobian\nfrom exact MNA sensitivities at the accepted algebraic solution. Circuit\nsubclasses retain the finite-difference fallback unless they provide their own\n`differential_jacobian` implementation. Linear built-in circuits share one\nfactorization across all sensitivity columns and reuse Jacobians and algebraic\nor implicit factors for matching component values, switch topology, method,\nand step shape. Each internal cache is capped at 128 entries.\n\n```text\nEuler:       G <= 1 + x\nHeun:        G <= 1 + x + x^2/2\nRK23:        G <= 1 + x + x^2/2 + x^3/6\nAB2:         G <= 1 + h[(1+r/2)L_n + (r/2)L_(n-1)]\nBackward E.: G <= 1 / (1 - x)\nTrapezoidal: G <= (1 + x/2) / (1 - x/2)\n```\n\nFor variable-step BDF2, with step ratio `r`, BAB-CS bounds the augmented\ntwo-state recurrence by\n\n```text\nG <= [(1+r) + r^2/(1+r)] / [(1+2r)/(1+r) - x]\n```\n\nImplicit denominators must remain positive. Otherwise stiffness/reference\nauthority takes over or the step is rejected and retried smaller. These are\ncomputable conservative norm models, not exact spectral radii.\n\n## Embedded Fast Path\n\n`reference_interval_steps = N > 1` is allowed only for `ab2`, `heun`, and\n`rk23`. On a deferred step,\n\n```text\ngamma = 0\nB_(n+1) = G_c B_n + E_embedded + residual_ratio\n```\n\nThe step is not labeled contractive when `G_c >= 1`; instead it is bounded over\nthe finite interval to the next authority checkpoint. A reference is promoted\nimmediately when any of these conditions holds:\n\n- the configured interval is due;\n- stiffness or the amplification domain requires implicit authority;\n- the projected or post-correction recursive bound would exceed\n  `deferred_reference_bound_cap`;\n- shadow mode requires reference authority.\n\nWhen the hard bound cap triggers, the accepted state is the full reference and\nthe propagation term resets to zero. Independent refined replay still runs at\n`anchor_interval_steps`, replaces the provisional endpoint, rebuilds multistep\nhistory, and resets the recursive bound.\n\nReplay refinement is evidence-controlled but not optional. Pure-C and pure-L\nbuilt-in topologies retain the qualified `minimum_anchor_substeps` policy. A\nmixed C+L trapezoidal replay starts at that minimum and estimates the local\nquadrature defect from three independent replay derivatives. Evidence above\n`anchor_embedded_error_cap` restarts the whole replay with a cubically predicted\nfiner subdivision. Refinement never exceeds `anchor_substeps`; reaching that\nvalue restores the previous fixed-resolution authority even when the estimator\nremains conservative. Backward-Euler and BDF2 references retain the full\nrefinement. `adaptive_anchor_refinement = false` restores one fixed refinement\ncount for every topology.\n\nAfter two matching uniform replay substeps, an AB3 extrapolation supplies only\nthe Newton initial guess. Variable or nonmatching substeps use the existing\nvariable-step AB2 extrapolation, and the first replay step remains unpredicted.\nAfter four matching uniform substeps, eligible large sparse systems also use a\nquartic extrapolation of accepted algebraic solutions. A failed algebraic guess\nis retried from the current accepted solution. The implicit reference residual\nand convergence gates still decide whether any guess is accepted or corrected.\n\nThe fast path is therefore adaptive: smooth regions skip references; nonlinear\nor poorly modeled regions automatically spend the reference work.\n\n## Selection Guidance\n\n- Use default `ab2` for backward-compatible BAB-CS behavior and low candidate\n  work when one implicit startup is acceptable.\n- Use `rk23` when accuracy per accepted timestep matters more than three stage\n  projections. It is the strongest embedded fast-path candidate in the current\n  implementation.\n- Use `heun` when two projections are preferable and second-order accuracy is\n  sufficient.\n- Use implicit candidates to compare bounded wrappers around familiar circuit\n  methods, not as expected speed winners: candidate and reference solves both\n  contribute work.\n- Keep `reference_interval_steps = 1` for strongest every-step contractive\n  evidence. Increase it only for embedded candidates and retain periodic replay.\n- Tighten `deferred_reference_bound_cap` for nonlinear devices or when monotone\n  refinement is more important than skipped reference solves.\n\n## Local Characterization\n\nThe following rows were measured on August 24, 2026 with the repository's quick\ncomparison cases. Timing is the median of seven RC runs or five diode runs and\nis local characterization only. `rk23-fast` uses `reference_interval_steps = 4`\nand the default hard deferred bound cap of 100 normalized units.\n\n| Case and step | Method | Maximum absolute error | Deterministic work | Reference solves | Median seconds |\n| --- | --- | ---: | ---: | ---: | ---: |\n| RC, `5e-5` | bounded RK23 | `2.920279e-4` | 808 | 20 | `0.006604` |\n| RC, `5e-5` | bounded RK23 fast | `2.891316e-4` | 724 | 6 | `0.005199` |\n| Diode clip, `2e-6` | bounded RK23 | `3.239952e-5` | 25,920 | 500 | `0.219980` |\n| Diode clip, `2e-6` | bounded RK23 fast | `7.728687e-5` | 24,071 | 180 | `0.187978` |\n| Diode clip, `2e-6` | bounded Heun | `1.032475e-4` | 23,968 | 500 | `0.206141` |\n| Diode clip, `2e-6` | bounded Heun fast | `7.729736e-5` | 22,794 | 309 | `0.184959` |\n| Diode clip, `2e-6` | active bounded AB2 | `5.659887e-4` | 22,426 | 512 | `0.193724` |\n| Diode clip, `2e-6` | bounded AB2 fast | `3.493050e-4` | 21,428 | 314 | `0.176195` |\n\nAt the fine RC step, RK23 fast reduced median time by 21.3%, deterministic work\nby 10.4%, and reference solves by 70% relative to bounded every-step RK23, with\nessentially unchanged error. At the fine nonlinear diode step, it reduced time\nby 14.5%, work by 7.1%, and references by 64%; maximum error was 2.39 times the\nevery-step RK23 error but remained 7.32 times smaller than active bounded AB2.\nThe maximum recursive bound for every fast diode row remained below the hard\nconfigured cap of 100.\n\n## Claim Boundary\n\nThe recursive bound is relative to the implemented local amplification,\nembedded/reference defect, residual, and replay model. It does not prove error\nagainst an unknown exact physical trajectory. Fast-path steps can be\nnoncontractive, but their growth is capped by dynamic reference promotion and a\nfinite independent replay interval. Benchmark timing is characterization, not a\nportable performance guarantee.\n",
      "order": 2,
      "path": "BOUNDED_CANDIDATES.md",
      "readingMinutes": 6,
      "sha256": "bd88d20ce0c5eaebb3926318822cb6ea1d9d9258e9d85fc1d4f60e8ddfc9963a",
      "summary": "BAB-CS keeps one error-bounding controller and attaches it to multiple candidate integrators. The candidate proposes the differential state; the controller owns algebraic projection, independent reference authority, correction, residual…",
      "title": "Bounded Candidate Integrators",
      "wordCount": 1204
    },
    {
      "category": "Numerical Design",
      "conceptIds": [
        "babcs",
        "projection",
        "residual",
        "jacobian",
        "newton-iteration",
        "deterministic-evidence",
        "fail-closed",
        "mna",
        "ulp",
        "api",
        "itp"
      ],
      "headings": [
        {
          "id": "bounded-and-interval-newton-research",
          "level": 1,
          "text": "Bounded and Interval Newton Research"
        },
        {
          "id": "algorithm",
          "level": 2,
          "text": "Algorithm"
        },
        {
          "id": "bracket-invariant-and-global-bound",
          "level": 2,
          "text": "Bracket Invariant and Global Bound"
        },
        {
          "id": "highest-gain-direction-interval-newton",
          "level": 2,
          "text": "Highest-Gain Direction: Interval Newton"
        },
        {
          "id": "local-newton-rate",
          "level": 2,
          "text": "Local Newton Rate"
        },
        {
          "id": "work-bound",
          "level": 2,
          "text": "Work Bound"
        },
        {
          "id": "method-comparison",
          "level": 2,
          "text": "Method Comparison"
        },
        {
          "id": "ranked-research-directions",
          "level": 2,
          "text": "Ranked Research Directions"
        },
        {
          "id": "deterministic-experiments",
          "level": 2,
          "text": "Deterministic Experiments"
        },
        {
          "id": "proof-boundary",
          "level": 2,
          "text": "Proof Boundary"
        }
      ],
      "kind": "Design",
      "markdown": "# Bounded and Interval Newton Research\n\nBAB-CS includes two scalar bounded-Newton research paths that apply the\nproject's candidate/authority pattern to root finding:\n\n- `bounded_newton_raphson` uses ordinary endpoint Newton proposals, while a\n  sign-changing bracket and mandatory midpoint step retain authority.\n- `interval_newton` accepts a derivative enclosure over the complete current\n  bracket and uses the interval-Newton operator to contract both sides at once.\n  The contraction controls the result only when it earns at least the same\n  half-width reduction as bisection; otherwise bisection takes authority.\n\nThis is deliberately separate from the circuit solver's vector Newton systems.\nThe scalar methods establish one-dimensional enclosure results under their\nstated assumptions; they do not turn damped MNA Newton iteration into an\ninterval proof.\n\n## Algorithm\n\nFor a continuous real function `f`, derivative `f'`, and initial bracket\n`[a_0, b_0]` satisfying\n\n```text\na_0 < b_0\nf(a_0) f(b_0) < 0,\n```\n\none bounded Newton iteration performs the following operations:\n\n1. Order the two bracket endpoints by increasing `|f|`.\n2. Try an ordinary Newton proposal from the better endpoint,\n   `x_N = x - f(x) / f'(x)`.\n3. If that derivative is zero or nonfinite, or `x_N` is outside the bracket,\n   try the other endpoint. If neither proposal is admissible, skip Newton.\n4. If an admissible Newton proposal is finite and strictly inside the bracket,\n   evaluate it and retain the sign-changing sub-bracket.\n5. Evaluate the midpoint of the resulting bracket and again retain the\n   sign-changing sub-bracket.\n\nAn exact sampled zero terminates immediately. Invalid derivative evidence never\ncontrols the result; the method falls back to bisection. Invalid function\nevaluations fail closed because the sign argument is then unavailable.\n\nThe implementation is `bounded_newton_raphson` in\n`src/babcs/rootfinding.py`. The same module provides `interval_newton`, pure\nNewton-Raphson, secant, bisection, and Ridders methods with common deterministic\ndiagnostics.\n\n## Bracket Invariant and Global Bound\n\n**Theorem 1.** Let `f` be continuous on `[a_0, b_0]` with opposite nonzero\nendpoint signs. If bounded Newton-Raphson completes `k` authority iterations\nwithout sampling an exact zero, then its brackets are nested, each bracket\ncontains at least one zero of `f`, and\n\n```text\nb_k - a_k <= 2^(-k) (b_0 - a_0).\n```\n\n**Proof.** The intermediate value theorem gives at least one zero in the\ninitial bracket. An accepted Newton point lies strictly inside the current\nbracket. Replacing the endpoint with the same sign as the new point preserves a\nsign change and cannot increase the width. The mandatory midpoint then divides\nthat retained bracket into two equal halves; choosing the sign-changing half\npreserves a zero and reduces the width by at least one half. Induction gives the\nstated nesting and width bound. The nested-interval theorem and continuity then\ngive convergence of the enclosures to a zero. No uniqueness claim follows from\nthe sign change alone.\n\nFor the returned rounded midpoint `m_k`, BAB-CS reports\n\n```text\nE_k = max(m_k - a_k, b_k - m_k).\n```\n\nTherefore every mathematical zero retained in the numerical bracket is within\n`E_k` of the returned point. Using the maximum rounded side rather than the\nsymbolic half-width avoids a one-ULP understatement when the floating midpoint\nis not exactly centered.\n\nThe theorem is intentionally simpler and more conservative than Brent's method\nor high-order enclosing algorithms. Brent combines interpolation with\nbisection, giving guaranteed convergence and usually superlinear practical\nbehavior [[37]](REFERENCES.md#ref-37). Bus and Dekker established explicit\nworst-case evaluation bounds for related interpolation/bisection hybrids\n[[38]](REFERENCES.md#ref-38). Algorithm 748 goes further by proving high-order\nconvergence of enclosing-interval diameters [[40]](REFERENCES.md#ref-40).\n\n## Highest-Gain Direction: Interval Newton\n\nThe highest-gain extension found in the research audit is not a more permissive\nclip for an ordinary endpoint Newton point. It is an interval-Newton contractor\nthat can move both enclosure endpoints from one center evaluation. For current\ninterval `X = [a, b]`, center `m`, and a derivative enclosure `D(X)` that\ncontains every derivative value on `X` and excludes zero, define\n\n```text\nN(X) = m - f(m) / D(X)\nX_new = X intersect N(X).\n```\n\nBAB-CS widens the scalar division and subtraction endpoints by one\n`math.nextafter` step. It accepts `X_new` only when\n\n```text\nwidth(X_new) <= width(X) / 2.\n```\n\nAn invalid derivative interval, an interval containing zero, an empty or\nstagnant operator result, or a contraction weaker than one half cannot control\nthe result. The implementation recovers any unsampled endpoint signs and takes\na midpoint bisection step instead.\n\n**Theorem 2.** Let `f` be differentiable on `X`, let `alpha` be a zero in `X`,\nand let `D(X)` contain `f'(x)` for every `x` in `X`, with `0` not in `D(X)`.\nThen `alpha` is in `N(X)`, so `X intersect N(X)` retains the zero. Every\ncompleted BAB-CS interval-Newton authority iteration also satisfies\n\n```text\nwidth(X_(k+1)) <= width(X_k) / 2.\n```\n\n**Proof.** The mean value theorem gives a point `xi` between `m` and `alpha`\nsuch that\n\n```text\nf(m) - f(alpha) = f'(xi) (m - alpha).\n```\n\nSince `f(alpha) = 0` and `f'(xi)` is in `D(X)`, rearrangement places `alpha` in\n`m - f(m) / D(X)`. Intersecting with `X` therefore retains it. The\nimplementation accepts that interval only when its width is at most one half\nof the prior width. Every other completed iteration is a sign-preserving\nbisection step, which has the same width bound. Induction gives nested\nroot-containing enclosures and the stated global contraction. Because the\nderivative enclosure excludes zero, it also establishes uniqueness inside that\nspecific interval under the oracle assumptions. This is the scalar\nmean-value/interval-Newton construction developed in the interval literature\n[[42]](REFERENCES.md#ref-42) [[45]](REFERENCES.md#ref-45).\n\n## Local Newton Rate\n\nSuppose `alpha` is a simple zero, `|f'(x)| >= m > 0` near `alpha`, and `f'` is\nLipschitz there with constant `L`. For an accepted ordinary Newton proposal,\nTaylor's theorem gives\n\n```text\n|x_(n+1) - alpha| <= L / (2m) |x_n - alpha|^2.\n```\n\nThus the Newton proposal subsequence can retain the classical local quadratic\nrate when the endpoint is close enough and the proposal remains inside the\nbracket. The certified enclosure radius is different: this implementation only\nclaims the unconditional geometric factor from Theorem 1. A fast point estimate\nmust not be mislabeled as a quadratically shrinking enclosure.\n\nKantorovich's theorem supplies a stronger semilocal Newton result when an\ninvertible derivative, a derivative-Lipschitz bound, and a sufficiently small\ninitial Newton correction are available [[36]](REFERENCES.md#ref-36). Those\nhypotheses can prove existence, uniqueness in a specified neighborhood,\nwell-defined iterates, and computable error bounds, but they are problem data,\nnot properties that a step clip creates automatically.\n\n## Work Bound\n\nAfter the two endpoint evaluations, each completed bounded-Newton authority\niteration uses at most:\n\n- two derivative evaluations, because both endpoints may be tried;\n- one Newton-candidate function evaluation;\n- one midpoint function evaluation.\n\nFor `k` completed iterations and one final midpoint evaluation,\n\n```text\nfunction evaluations   <= 3 + 2k\nderivative evaluations <= 2k.\n```\n\nThis bound is deterministic, but bounded Newton is not guaranteed to be the\ncheapest bracketed method. Its purpose is a transparent Newton-plus-authority\nconstruction whose proof mirrors BAB-CS candidate/reference separation.\n\nFor interval Newton, the accepted fast path uses one center function evaluation\nand one derivative-interval evaluation per completed authority iteration. With\ntwo initial endpoint evaluations and one final midpoint evaluation, a run of\n`k` continuously accepted contractions satisfies\n\n```text\nfunction evaluations            <= 3 + k\nderivative-interval evaluations <= k.\n```\n\nIf a fallback follows an accepted interval contraction, up to two unsampled\nendpoint values are recovered before bisection. The conservative general bound\nis therefore `3 + 3k` function evaluations, although repeated bisection from an\nalready sampled sign bracket still uses only one new function value per\niteration.\n\n## Method Comparison\n\n| Method | Derivative | Retains bracket | Broad guarantee | Local behavior near a simple root |\n| --- | --- | --- | --- | --- |\n| Newton-Raphson | yes | no | local only without globalization assumptions | quadratic |\n| Secant | no | no | local; denominator and basin failures remain possible | superlinear |\n| Bisection | no | yes | geometric enclosure for a continuous sign change | linear, factor `1/2` |\n| Bounded Newton-Raphson | yes | yes | geometric enclosure, factor at most `1/2` per authority iteration | quadratic Newton proposals, linearly certified enclosure |\n| BAB-CS interval Newton | derivative enclosure | yes | interval-operator retention plus factor at most `1/2` per authority iteration | often rapid two-sided contraction; bisection when the derivative interval includes zero |\n| Ridders | no | yes | bracket retained; original analysis gives quadratic or better local rate | quadratic or better [[39]](REFERENCES.md#ref-39) |\n| Brent | no | yes | guaranteed convergence with a bisection-class safeguard | usually superlinear [[37]](REFERENCES.md#ref-37) |\n| Interval Newton/Krawczyk | interval Jacobian | interval box | can verify existence, uniqueness, and error bounds under interval hypotheses | often rapid local contraction [[42]](REFERENCES.md#ref-42) [[43]](REFERENCES.md#ref-43) |\n\nFor vector nonlinear systems, residual-decreasing line searches and trust\nregions are globalizations, not root enclosures. Eisenstat and Walker prove\nconditional global convergence results for inexact Newton methods with adequate\nprogress tests [[41]](REFERENCES.md#ref-41). Interval Newton and Krawczyk\noperators provide the stronger existence/uniqueness machinery when rigorous\ninterval Jacobians are available [[42]](REFERENCES.md#ref-42). Merely clipping a\nvector Newton step does not establish either theorem\n[[43]](REFERENCES.md#ref-43).\n\n## Ranked Research Directions\n\n1. **Interval Newton with an explicit derivative enclosure — implemented.** It\n   offers the largest measured reduction because one center evaluation can\n   contract both sides, and it strengthens the mathematical oracle from a point\n   derivative to a complete derivative range.\n2. **Minmax-projected Newton/ITP safeguard — retained as future work.** The ITP\n   result characterizes non-midpoint queries that preserve bisection's minmax\n   iteration bound [[44]](REFERENCES.md#ref-44). Applying that projection to an\n   endpoint Newton point saves a mandatory midpoint evaluation in principle,\n   but it can repeatedly tighten only the near-root side while leaving the\n   opposite enclosure endpoint wide. It was therefore not selected as the\n   primary bounded-Newton upgrade.\n3. **Algorithm 748 or Brent-class derivative-free fallback — future work.** A\n   high-order enclosing fallback could reduce the multiple-root and\n   zero-containing-derivative cases where interval Newton must currently\n   bisect, at the cost of materially more state and proof complexity\n   [[37]](REFERENCES.md#ref-37) [[40]](REFERENCES.md#ref-40).\n4. **Vector Krawczyk/Hansen-Sengupta authority — separate project.** This is the\n   appropriate direction for existence and uniqueness of full nonlinear MNA\n   systems, but it requires interval Jacobians, outward-rounded linear algebra,\n   and box-level validation rather than a scalar API retrofit\n   [[43]](REFERENCES.md#ref-43) [[45]](REFERENCES.md#ref-45).\n\n## Deterministic Experiments\n\nRun the comparison with:\n\n```bash\nPYTHONPATH=src python tools/compare_rootfinders.py \\\n  --output /tmp/babcs-rootfinders.json \\\n  --csv-output /tmp/babcs-rootfinders.csv\n```\n\nThe August 27, 2026 working-tree run used absolute, relative, and residual\ntolerances of `1e-12` with an 80-iteration budget. The columns below are\n`iterations / function evaluations / derivative evaluations`.\n\n| Case | Newton | Bounded Newton | Interval Newton | Secant | Bisection | Ridders |\n| --- | --- | --- | --- | --- | --- | --- |\n| `square_root_two` | `5 / 6 / 5` | `6 / 14 / 7` | `5 / 8 / 5` | `7 / 9 / 0` | `39 / 42 / 0` | `6 / 15 / 0` |\n| `exponential_root` | `5 / 6 / 5` | `7 / 16 / 8` | `5 / 8 / 5` | `8 / 10 / 0` | `39 / 42 / 0` | `5 / 13 / 0` |\n| `newton_cycle` | failed budget | `5 / 11 / 5` | `5 / 8 / 5` | `50 / 52 / 0` | `39 / 42 / 0` | `7 / 16 / 0` |\n| `multiple_root` | `22 / 23 / 22` | `33 / 69 / 33` | `39 / 42 / 39` | `30 / 32 / 0` | `39 / 42 / 0` | `32 / 67 / 0` |\n| `diode_operating_point` | failed budget | `33 / 44 / 61` | `9 / 12 / 9` | failed denominator | `39 / 42 / 0` | `13 / 23 / 0` |\n\nThe comparison exposes three important boundaries:\n\n1. Pure Newton is cheapest on the smooth easy roots, but the selected cubic\n   cycles and the diode initial value exhaust its budget.\n2. A residual-only stop is not a position certificate at a multiple root. Pure\n   Newton stopped with about `6.68e-5` position error because cubing makes the\n   residual tiny; the bracketed methods returned approximately `1e-12`\n   enclosures.\n3. Across these five fixed cases, interval Newton reduced function evaluations\n   from `154` to `78` (`49.4%`) and equally weighted total oracle calls from\n   `268` to `141` (`47.4%`) versus bounded Newton. On the diode case alone, the\n   reductions were `44` to `12` function evaluations and `105` to `21` total\n   calls.\n4. The multiple root is the important limitation. Its derivative enclosure\n   contains zero at every retained interval, so interval Newton correctly\n   degenerates to bisection. It still returns a positional enclosure, but it\n   provides no interval-Newton acceleration there.\n\nThese are deterministic case results, not a universal ranking.\n\n## Proof Boundary\n\nThe sign-bracket methods assume a continuous mathematical function and\ntrustworthy finite signs. `interval_newton` additionally assumes that every\nreturned derivative interval encloses the complete mathematical derivative\nrange on the requested bracket. A wrong enclosure can invalidate root\nretention; the callback is authority-bearing problem evidence, not a heuristic.\n\nThe implementation widens the interval division and subtraction results by one\nfloating-point step to prevent a correctly rounded simple-root contraction from\ncollapsing spuriously to an uncertified singleton. Python `float` evaluation of\n`f(m)` and the user callback is still not an outward-rounded interval extension\nof arbitrary code. The returned bracket is therefore a numerical enclosure\nunder the stated function and oracle assumptions, not a machine-checked proof\nagainst all rounding error. A proof-producing extension would need\ninterval-valued function and derivative evaluation with directed rounding,\nfollowed by the interval Newton or Krawczyk inclusion machinery from the cited\nliterature [[42]](REFERENCES.md#ref-42) [[43]](REFERENCES.md#ref-43).\n",
      "order": 3,
      "path": "BOUNDED_NEWTON.md",
      "readingMinutes": 10,
      "sha256": "a6ae497fc3f0c1696b6d19df23d2177ca4c241271445cb1973956949b15473d7",
      "summary": "BAB-CS includes two scalar bounded-Newton research paths that apply the project's candidate/authority pattern to root finding:",
      "title": "Bounded and Interval Newton Research",
      "wordCount": 2107
    },
    {
      "category": "Numerical Design",
      "conceptIds": [
        "replay",
        "recursive-bound",
        "deterministic-evidence",
        "python-wheel",
        "rc",
        "ab2",
        "json",
        "csv",
        "sha256",
        "ngspice"
      ],
      "headings": [
        {
          "id": "minimal-reproducible-research-example",
          "level": 1,
          "text": "Minimal Reproducible Research Example"
        },
        {
          "id": "1-record-the-exact-source",
          "level": 2,
          "text": "1. Record the exact source"
        },
        {
          "id": "2-run-the-deterministic-example-twice",
          "level": 2,
          "text": "2. Run the deterministic example twice"
        },
        {
          "id": "3-check-the-authority-summary",
          "level": 2,
          "text": "3. Check the authority summary"
        },
        {
          "id": "4-interpret-the-result-conservatively",
          "level": 2,
          "text": "4. Interpret the result conservatively"
        },
        {
          "id": "5-extend-to-the-observatory-and-lab",
          "level": 2,
          "text": "5. Extend to the observatory and lab"
        }
      ],
      "kind": "Design",
      "markdown": "# Minimal Reproducible Research Example\n\nThis walkthrough runs the dependency-free RC step case twice, proves the\ngenerated CSV and JSON are byte-identical, and checks core authority fields.\n\n## 1. Record the exact source\n\n```bash\ngit rev-parse HEAD\ngit status --short\npython --version\n```\n\nFor publication evidence, use a clean full commit SHA. A dirty tree is suitable\nfor development evidence only.\n\n## 2. Run the deterministic example twice\n\n```bash\nrm -rf /tmp/babcs-minimal-a /tmp/babcs-minimal-b\nmkdir -p /tmp/babcs-minimal-a /tmp/babcs-minimal-b\n\nPYTHONPATH=src python -m babcs simulate examples/rc_step.json \\\n  --mode shadow \\\n  --csv /tmp/babcs-minimal-a/trace.csv \\\n  --summary /tmp/babcs-minimal-a/summary.json\n\nPYTHONPATH=src python -m babcs simulate examples/rc_step.json \\\n  --mode shadow \\\n  --csv /tmp/babcs-minimal-b/trace.csv \\\n  --summary /tmp/babcs-minimal-b/summary.json\n\ncmp /tmp/babcs-minimal-a/trace.csv /tmp/babcs-minimal-b/trace.csv\ncmp /tmp/babcs-minimal-a/summary.json /tmp/babcs-minimal-b/summary.json\nsha256sum /tmp/babcs-minimal-a/trace.csv /tmp/babcs-minimal-a/summary.json\n```\n\n## 3. Check the authority summary\n\n```bash\npython - <<'PY'\nimport json\nfrom pathlib import Path\n\nsummary = json.loads(Path(\"/tmp/babcs-minimal-a/summary.json\").read_text())\nassert summary[\"accepted_steps\"] > 0\nassert summary[\"rejected_steps\"] == 0\nassert summary[\"contractive_steps\"] == summary[\"accepted_steps\"]\nassert summary[\"implicit_fallbacks\"] >= 1\nassert summary[\"periodic_reanchors\"] >= 1\nassert summary[\"maximum_algebraic_residual\"] >= 0.0\nassert summary[\"maximum_full_residual\"] >= 0.0\nassert summary[\"maximum_estimated_bound\"] >= 0.0\nprint(json.dumps(summary, indent=2, sort_keys=True))\nPY\n```\n\nThe startup fallback is expected: AB2 has insufficient history on the first\nstep, so the implicit reference controls startup. Periodic replay then refreshes\nauthority and resets the recursive bound.\n\n## 4. Interpret the result conservatively\n\nThis example proves deterministic execution and the reported local authority\nbehavior for one RC input and one exact source state. It does not qualify sparse\nbackends, nonlinear devices, long-horizon oscillators, external ngspice\nagreement, an installed wheel, or a release.\n\n## 5. Extend to the observatory and lab\n\nAfter the minimal RC check, run the compact numerical teaching path:\n\n```bash\nPYTHONPATH=src python lab/support/verify.py \\\n  --exercise 01-mna \\\n  --exercise 02-convergence \\\n  --exercise 03-phase-versus-energy \\\n  --exercise 04-shadow-authority\n```\n\nThen generate the complete Method Observatory and Bound Coverage Atlas using\nthe commands in `docs/METHOD_OBSERVATORY.md` and\n`docs/BOUND_COVERAGE_ATLAS.md`. Full packaging exercises require a clean exact\nsource commit for release evidence; `--development` labels dirty-tree output as\nnon-release evidence. Fixture regeneration is explicit and never constitutes\napproval by itself.\n",
      "order": 4,
      "path": "MINIMAL_REPRODUCIBLE_RESEARCH.md",
      "readingMinutes": 2,
      "sha256": "92454b1e8e6050fe23cdad1d57a16b652df5fd90e8fa35dc5fbb361ab44eb3d6",
      "summary": "This walkthrough runs the dependency-free RC step case twice, proves the generated CSV and JSON are byte-identical, and checks core authority fields.",
      "title": "Minimal Reproducible Research Example",
      "wordCount": 371
    },
    {
      "category": "Qualification and Release",
      "conceptIds": [
        "babcs",
        "numerical-authority",
        "projection",
        "replay",
        "anchor",
        "recursive-bound",
        "residual",
        "jacobian",
        "newton-iteration",
        "stiffness",
        "passivity",
        "deterministic-evidence",
        "shadow-mode",
        "fail-closed",
        "python-wheel",
        "mna",
        "rc",
        "lc",
        "kcl",
        "ab2",
        "adams-bashforth",
        "be",
        "bdf2",
        "json",
        "csv",
        "sha256",
        "cli"
      ],
      "headings": [
        {
          "id": "bounded-authority-based-circuit-simulation-v1-completion-audit",
          "level": 1,
          "text": "Bounded-Authority-Based-Circuit-Simulation v1 Completion Audit"
        },
        {
          "id": "scope",
          "level": 2,
          "text": "Scope"
        },
        {
          "id": "requirement-matrix",
          "level": 2,
          "text": "Requirement Matrix"
        },
        {
          "id": "bab-001-dynamic-state-achieved",
          "level": 3,
          "text": "BAB-001 — Dynamic State: Achieved"
        },
        {
          "id": "bab-002-algebraic-projection-achieved",
          "level": 3,
          "text": "BAB-002 — Algebraic Projection: Achieved"
        },
        {
          "id": "bab-003-adams-bashforth-predictor-achieved",
          "level": 3,
          "text": "BAB-003 — Adams-Bashforth Predictor: Achieved"
        },
        {
          "id": "bab-004-reference-authority-achieved",
          "level": 3,
          "text": "BAB-004 — Reference Authority: Achieved"
        },
        {
          "id": "bab-005-contractive-correction-achieved",
          "level": 3,
          "text": "BAB-005 — Contractive Correction: Achieved"
        },
        {
          "id": "bab-006-runtime-bounds-achieved",
          "level": 3,
          "text": "BAB-006 — Runtime Bounds: Achieved"
        },
        {
          "id": "bab-007-hard-failure-gates-achieved",
          "level": 3,
          "text": "BAB-007 — Hard Failure Gates: Achieved"
        },
        {
          "id": "bab-008-independent-re-anchor-achieved",
          "level": 3,
          "text": "BAB-008 — Independent Re-Anchor: Achieved"
        },
        {
          "id": "bab-009-event-safety-achieved",
          "level": 3,
          "text": "BAB-009 — Event Safety: Achieved"
        },
        {
          "id": "bab-010-stiffness-fallback-achieved",
          "level": 3,
          "text": "BAB-010 — Stiffness Fallback: Achieved"
        },
        {
          "id": "bab-011-passivity-monitor-achieved",
          "level": 3,
          "text": "BAB-011 — Passivity Monitor: Achieved"
        },
        {
          "id": "bab-012-rollout-modes-achieved",
          "level": 3,
          "text": "BAB-012 — Rollout Modes: Achieved"
        },
        {
          "id": "bab-013-deterministic-diagnostics-achieved",
          "level": 3,
          "text": "BAB-013 — Deterministic Diagnostics: Achieved"
        },
        {
          "id": "bab-014-fail-closed-topology-handling-achieved",
          "level": 3,
          "text": "BAB-014 — Fail-Closed Topology Handling: Achieved"
        },
        {
          "id": "completion-gates",
          "level": 2,
          "text": "Completion Gates"
        },
        {
          "id": "validation-evidence",
          "level": 2,
          "text": "Validation Evidence"
        },
        {
          "id": "boundary-statement",
          "level": 2,
          "text": "Boundary Statement"
        }
      ],
      "kind": "Audit",
      "markdown": "# Bounded-Authority-Based-Circuit-Simulation v1 Completion Audit\n\nAudit date: August 24, 2026\n\n## Scope\n\nThis audit evaluates the current `/home/pamela/Projects/BAB-CS` filesystem\nagainst `docs/BAB_CSV1_SPEC.md` and `IMPLEMENTATION_PLAN.md`. The directory is a\nstandalone source tree and is not currently a Git repository, so the built wheel\nhash and deterministic simulation-output hashes are the release evidence.\n\n## Requirement Matrix\n\n### BAB-001 — Dynamic State: Achieved\n\n- `src/babcs/model.py` defines capacitor-voltage and inductor-current ordering,\n  names, initial state, derivatives, and stored energy.\n- `tests/test_model.py::test_lc_dynamic_coordinates_follow_passive_sign_convention`\n  verifies the state convention and derivative signs.\n\n### BAB-002 — Algebraic Projection: Achieved\n\n- `Circuit.solve_algebraic` assembles KCL, voltage constraints, nonlinear device\n  Jacobians, damped Newton iteration, and explicit singular/failure exceptions.\n- Every model evaluation calls the algebraic solve before derivatives or\n  diagnostics are produced.\n- RC projection and singular failure are tested in `tests/test_model.py`.\n\n### BAB-003 — Adams-Bashforth Predictor: Achieved\n\n- `variable_step_ab2_predict` implements the required variable-step AB2 formula.\n- `BoundedAdamsBashforthIntegrator.step` uses that function only when valid\n  previous derivative and step history exists.\n- `test_variable_step_ab2_coefficients` directly verifies the coefficient\n  contract.\n\n### BAB-004 — Reference Authority: Achieved\n\n- `src/babcs/integrators.py` implements backward Euler, trapezoidal, and\n  variable-step BDF2 with damped Newton solution.\n- Tests verify the backward-Euler analytic step, trapezoidal second-order\n  convergence, and variable-step BDF2 history.\n\n### BAB-005 — Contractive Correction: Achieved\n\n- The active integrator derives a correction gain from the conservative\n  predictor amplification and configured target contraction.\n- Stiffness or `closed_loop_gain >= 1` transfers full authority to the implicit\n  reference.\n- Active-mode tests verify every AB step has gain below one and correction does\n  not increase reference deviation.\n\n### BAB-006 — Runtime Bounds: Achieved\n\n- `StepMetrics` separately records predictor/reference error,\n  corrected/reference error, algebraic residual, full residual, signed energy\n  defect, positive injection ratio, stiffness, amplification, closed-loop gain,\n  recursive estimated bound, and anchor deviation.\n- CSV and JSON outputs preserve these diagnostics.\n\n### BAB-007 — Hard Failure Gates: Achieved\n\n- Predictor, residual, energy, projection, reference, re-anchor, rejection-count,\n  minimum-step, and all non-finite metric failures are fail closed.\n- `test_hard_predictor_cap_rejects_large_step` and\n  `test_non_finite_amplification_fails_closed` exercise hard rejection paths.\n\n### BAB-008 — Independent Re-Anchor: Achieved\n\n- `reanchor_if_due` calls `integrate_reference_window` from the saved trusted\n  anchor, using smaller implicit steps rather than the provisional current state.\n- The replay endpoint replaces the candidate, previous derivative history is\n  rebuilt when available, the recursive bound is cleared, and generation and\n  anchor counters are advanced.\n- Periodic and forced safety-anchor behavior is covered in `tests/test_babcs.py`.\n\n### BAB-009 — Event Safety: Achieved\n\n- `Simulator.run` splits steps at waveform breakpoints and resets history only\n  when the accepted endpoint actually reaches the event.\n- Tests verify post-event implicit startup and ensure a rejected shortened step\n  is not mislabeled as an event.\n\n### BAB-010 — Stiffness Fallback: Achieved\n\n- Differential Jacobian infinity norms produce the runtime stiffness indicator.\n- Exceeding `stiffness_limit` gives full authority to the implicit reference.\n- `test_stiffness_gate_uses_implicit_authority` verifies the transition.\n\n### BAB-011 — Passivity Monitor: Achieved\n\n- Circuit evaluation reports capacitor/inductor energy, source power, and\n  resistive, switch, and diode dissipation.\n- BAB-CS calculates signed discrete energy balance and gates positive numerical\n  energy injection.\n- The LC regression verifies bounded energy with periodic independent anchors.\n\n### BAB-012 — Rollout Modes: Achieved\n\n- `BABCSConfig.rollout_mode` accepts `disabled`, `shadow`, and `active` and\n  defaults to `shadow`.\n- Tests prove disabled mode does not execute AB and shadow mode always accepts\n  the implicit reference state.\n\n### BAB-013 — Deterministic Diagnostics: Achieved\n\n- The CLI loads JSON circuit cases and writes per-step CSV plus aggregate JSON.\n- Two independent installed-wheel executions of every included example produced\n  byte-identical CSV and JSON files.\n- CLI output and file creation are covered by `tests/test_cli.py`.\n\n### BAB-014 — Fail-Closed Topology Handling: Achieved\n\n- Dense linear solves use partial pivoting and reject singular systems.\n- BAB-CS does not add hidden shunts or parasitic components.\n- A floating current-source topology deterministically raises\n  `CircuitSolveError` in the regression suite.\n\n## Completion Gates\n\n- Variable-step AB2 coefficient test: passed.\n- Algebraic KCL and constraint projection: passed.\n- Backward Euler analytic result: passed.\n- Trapezoidal second-order convergence: passed.\n- Variable-step BDF2: passed.\n- Contractive active AB steps: passed.\n- Hard error and non-finite rejection: passed.\n- Independent periodic and safety anchors: passed.\n- Breakpoint history reset: passed.\n- Stiffness fallback: passed.\n- Passive LC energy bound: passed.\n- Singular topology failure: passed.\n- JSON CLI and installed wheel: passed.\n- Deterministic example replay: passed.\n\n## Validation Evidence\n\nFinal source-suite command:\n\n```text\nPYTHONPATH=src python -m unittest discover -s tests -v\nRan 25 tests in 0.469s\nOK\n```\n\nPackaging and installed execution:\n\n```text\npython -m pip wheel . --no-deps --wheel-dir dist\npython -m venv /tmp/babcs-release-venv\n/tmp/babcs-release-venv/bin/python -m pip install --no-deps \\\n  dist/bab_cs-1.0.0-py3-none-any.whl\n/tmp/babcs-release-venv/bin/python -m pip check\nNo broken requirements found.\n```\n\nWheel SHA-256:\n\n```text\n242e04db7fa3422f8552f914b7abbf0773cfa51faa5a9d530bbcae9450a1b5ac\n```\n\nDeterministic summary SHA-256 values:\n\n```text\nrc_step.json    69b38db644fac821b9020d1309a0e4932918b360e8b0e236e5548eef2e67c8c8\nlc_tank.json    796436d7e57b2f804a441f5aac31c698da990d760594c64d623a83a716b8543b\npulsed_rc.json  17624f04e5f23bc04c6de9d06d873753391db032f28d37fb9ea251184414c8ca\n```\n\nRepresentative runtime evidence:\n\n- RC: 500 accepted steps, 499 AB steps, 500 contractive steps, zero rejected\n  steps, maximum full residual `2.168404344971009e-19`.\n- LC: 4,019 accepted steps, 4,017 AB steps, 4,019 contractive steps, 200\n  periodic anchors, maximum full residual `1.1102230246251565e-16`.\n- Pulsed RC: 318 accepted steps, 298 AB steps, 44 implicit fallbacks, 54\n  rejected/reduced attempts, 16 periodic anchors, maximum full residual\n  `2.168404344971009e-19`.\n\n## Boundary Statement\n\nBAB-CSv1 is complete for the stated reference-implementation scope. It does not\nclaim production-scale sparse performance, support for arbitrary higher-index\nMNA topologies, arbitrary analog event root finding, or unconditional exact\ntrajectory bounds. Those remain explicit future-version boundaries rather than\nsilent partial implementations.\n",
      "order": 0,
      "path": "BAB_CSV1_COMPLETION_AUDIT.md",
      "readingMinutes": 4,
      "sha256": "25f81ea8cd77f75da739126be1ee3c439966c107ec5def87e2ea31f7f9447f05",
      "summary": "Audit date: August 24, 2026",
      "title": "Bounded-Authority-Based-Circuit-Simulation v1 Completion Audit",
      "wordCount": 841
    },
    {
      "category": "Qualification and Release",
      "conceptIds": [
        "babcs",
        "replay",
        "anchor",
        "deterministic-evidence",
        "fail-closed",
        "source-wheel-equivalence",
        "python-wheel",
        "klu",
        "scipy",
        "json",
        "csv",
        "svg",
        "sha256",
        "ci",
        "cli",
        "url",
        "utc",
        "os",
        "wheel-metadata-files",
        "identifier"
      ],
      "headings": [
        {
          "id": "bounded-authority-based-circuit-simulation-release-qualification-implementation-audit",
          "level": 1,
          "text": "Bounded-Authority-Based-Circuit-Simulation Release Qualification Implementation Audit"
        },
        {
          "id": "scope",
          "level": 2,
          "text": "Scope"
        },
        {
          "id": "implementation-requirements",
          "level": 2,
          "text": "Implementation Requirements"
        },
        {
          "id": "ip-1-canonical-package-metadata-implemented",
          "level": 3,
          "text": "IP-1 — Canonical package metadata: Implemented"
        },
        {
          "id": "ip-2-deterministic-evidence-manifest-implemented",
          "level": 3,
          "text": "IP-2 — Deterministic evidence manifest: Implemented"
        },
        {
          "id": "ip-3-qualification-workflow-closure-implemented",
          "level": 3,
          "text": "IP-3 — Qualification workflow closure: Implemented"
        },
        {
          "id": "ip-4-ci-and-tests-implemented",
          "level": 3,
          "text": "IP-4 — CI and tests: Implemented"
        },
        {
          "id": "ip-5-documentation-alignment-implemented",
          "level": 3,
          "text": "IP-5 — Documentation alignment: Implemented"
        },
        {
          "id": "release-requirement-matrix",
          "level": 2,
          "text": "Release Requirement Matrix"
        },
        {
          "id": "release-state-conclusion",
          "level": 2,
          "text": "Release-State Conclusion"
        }
      ],
      "kind": "Audit",
      "markdown": "# Bounded-Authority-Based-Circuit-Simulation Release Qualification Implementation Audit\n\nAudit date: August 24, 2026\n\n## Scope\n\nThis audit evaluates the repository implementation of\n`BAB-CS-Release-Qualification-Plan.md`. It does not approve `v1.1.0`, select a\nfinal source commit, authorize a tag, publish a GitHub release, or treat local\nimplementation validation as release qualification.\n\nThe implementation boundary is deliberate:\n\n- automation may build, test, inspect, hash, compare, summarize, and verify;\n- the evidence manifest status is always `candidate`;\n- threshold and mapping review remain semantic human decisions;\n- tag creation and publication require exact-hash human approval; and\n- public asset identity and installation are post-publication observations.\n\n## Implementation Requirements\n\n### IP-1 — Canonical package metadata: Implemented\n\n- `src/babcs/_project.py` owns distribution name, package name, version,\n  summary, Python requirement, sparse extra, wheel tag, and console entry point.\n- `build_backend.py` derives wheel and `.dist-info` identity plus METADATA,\n  WHEEL, and entry-point content from that module.\n- `src/babcs/__init__.py` exports the same version as `babcs.__version__`.\n- `pyproject.toml` declares `1.1.0`, with consistency enforced by\n  `tests/test_build_backend.py`.\n\n### IP-2 — Deterministic evidence manifest: Implemented\n\n- `tools/release_evidence.py` records environment and workflow identity,\n  validates exact source/tag binding, inspects wheels, validates the complete\n  comparison matrix, compares artifacts byte-for-byte, parses successful test\n  and comparison summaries, writes deterministic manifests and checksums, and\n  reconstructs the manifest during verification.\n- `release-evidence-required.txt` is the canonical complete-bundle profile.\n- Duplicate requirements, missing files, unexpected roles, modified or\n  unlisted files, nonfinite JSON, failed test summaries, incomplete comparison\n  matrices, mismatched workflow/source SHAs, and incorrect wheel identity fail\n  closed.\n- The tool cannot emit an `approved` manifest.\n\n### IP-3 — Qualification workflow closure: Implemented\n\n`.github/workflows/release-qualification.yml` now:\n\n- validates exact `v<package-version>` tags and exact candidate/SHA prefixes;\n- supports non-publishing manual candidate runs;\n- installs SciPy, SuiteSparse KLU, and `ngspice`;\n- records UTC creation time, OS, platform, Python, pip, SciPy, KLU, `ngspice`,\n  and GitHub workflow identity;\n- compiles production, tool, test, and backend sources;\n- runs dependency-free and SciPy/KLU long/very-long source suites;\n- generates numerical and timing evidence and inspects the full matrix;\n- runs all 20 manifest-owned external mappings;\n- builds the wheel twice and compares exact bytes;\n- inspects and retains one exact wheel;\n- performs dependency-free and SciPy/KLU installed-wheel qualification;\n- compares source and installed JSON, CSV, and SVG bytes;\n- writes and re-verifies the complete evidence manifest; and\n- uploads the evidence with 90-day Actions retention while retaining\n  `contents: read` and performing no publication.\n\n### IP-4 — CI and tests: Implemented\n\n- Normal CI compiles `build_backend.py` with source, tests, and tools.\n- Normal unittest discovery includes metadata and release-evidence tests.\n- `tests/test_release_evidence.py` uses temporary directories and covers\n  deterministic output, checksum ordering, wheel identity, exact\n  source/candidate binding, complete comparison matrices, artifact equality,\n  missing and duplicate requirements, unexpected files, modified evidence,\n  nonfinite JSON, failed test logs, workflow SHA mismatch, and the canonical\n  required-file profile.\n\n### IP-5 — Documentation alignment: Implemented\n\n- `README.md` documents canonical identity, the complete workflow, evidence\n  tooling, required-file profile, and non-publication boundary.\n- `RELEASE.md` describes the current `1.1.0` candidate and exact lifecycle from\n  frozen commit through public-download verification.\n- `BAB-CS-Release-Qualification-Plan.md` uses the implemented commands and no\n  longer describes resolved workflow gaps as current deficiencies.\n- This audit maps every `RQ-*` requirement to implementation and remaining\n  execution authority.\n\n## Release Requirement Matrix\n\nThe `Implementation` column evaluates whether the repository now contains a\ncorrectly scoped mechanism for the requirement. The `Release evidence` column\nstates what is still required for an actual `v1.1.0` decision.\n\n| ID | Implementation | Direct implementation evidence | Release evidence state |\n| --- | --- | --- | --- |\n| `RQ-001` | Implemented | `src/babcs/_project.py`, `build_backend.py`, `pyproject.toml`, `tests/test_build_backend.py`, wheel inspection | Pending final frozen-commit search, test log, and retained-wheel inspection |\n| `RQ-002` | Implemented with operator gate | Workflow records full checked-out SHA; comparison inspection rejects dirty source; manifest binds workflow and source SHA | Pending selection of one clean pushed final SHA and proof it remained unchanged |\n| `RQ-003` | Implemented with human gate | `validate_release_identity` accepts only `v1.1.0` or exact `candidate-<SHA-prefix>` identity | Pending annotated tag creation after approval and remote tag resolution |\n| `RQ-004` | Implemented | Workflow writes `compile.log` from forced `compileall` over `src`, `tests`, `tools`, and `build_backend.py` | Pending final exact-commit workflow log |\n| `RQ-005` | Implemented | Workflow enables both long tiers; manifest parser requires one successful unittest summary | Pending final source test log and reviewer confirmation of skips |\n| `RQ-006` | Implemented | Clean SciPy environment, installed system KLU, recorded versions, install log, and full source suite | Pending final SciPy/KLU source evidence |\n| `RQ-007` | Implemented | `tests/test_candidates.py`, comparison manifest, complete-matrix inspector | Pending final discovery and comparison reports |\n| `RQ-008` | Implemented | `tests/test_bound_model.py` reconstructs recurrence; comparison reports retain bound metrics | Pending final test and numerical evidence |\n| `RQ-009` | Implemented | BAB-CS and long-horizon tests cover replay, pre-reset evidence, history rebuild, and reset; comparison metrics retain anchors | Pending final test and comparison evidence |\n| `RQ-010` | Implemented | `tests/test_failure_gates.py`, model/integrator boundary tests, and fail-closed evidence verification | Pending final suite log |\n| `RQ-011` | Implemented | `tests/test_nonlinear.py` and external diode/switch cases | Pending final source, installed, and external evidence review |\n| `RQ-012` | Implemented | `tests/test_long_horizon.py` includes ten-, hundred-, and thousand-period cases | Pending final long/very-long logs |\n| `RQ-013` | Implemented | Deterministic backend test plus workflow double build, byte comparison, retained hash, and manifest binding | Pending two wheel files and hashes from the final commit |\n| `RQ-014` | Implemented | Canonical metadata tests and `inspect-wheel` validate filename, members, METADATA, WHEEL, entry point, timestamps, and modes | Pending retained final-wheel inspection |\n| `RQ-015` | Implemented | Workflow creates a fresh venv and records `--no-deps` installation plus `pip check` in `installed-wheel-install.log` | Pending final installation log |\n| `RQ-016` | Implemented | Workflow records `INSTALLED_PACKAGE_PATH` and runs full installed-wheel long tiers without `PYTHONPATH=src` | Pending final installed-wheel logs and provenance review |\n| `RQ-017` | Implemented | `compare-artifacts` requires byte equality for source/installed JSON, CSV, and SVG and records `artifact-comparison.json` | Pending final paired artifacts |\n| `RQ-018` | Implemented | `inspect-comparison` derives every expected case/method/step/anchor key from `benchmarks/manifest.json`, rejects omissions/duplicates, and checks analysis sections | Pending final `comparison-inspection.json` and semantic report review |\n| `RQ-019` | Evidence support implemented; approval cannot be automated | Deterministic reports, source diff, retained thresholds, hashes, and manifest support review | Pending human rationale and approval for every changed threshold or baseline |\n| `RQ-020` | Evidence generation implemented; semantic review remains human | Workflow produces JSON, netlist, raw waveform, and log bundles for all 20 manifest-owned cases, retains a suite summary, preserves canonical state order, and records `ngspice` version | Pending exact-commit execution and human mapping/waveform review |\n| `RQ-021` | Implemented with claim-review gate | Separate `source-timing.json`, recorded environment, scoped wording in `RELEASE.md`, and no timing correctness gate | Pending final timing report and human confirmation that each published claim names workload, size, backend, environment, statistic, and comparator |\n| `RQ-022` | Implemented | Canonical required-file profile; deterministic manifest records path, role, size, hash, package/source identity, environment, workflow, tests, and comparisons; manifest hash and checksums bind control files | Pending final complete bundle and independent verification |\n| `RQ-023` | Implemented; tag execution pending | Workflow records run ID, URL, event, ref, and exact checked-out SHA; manifest requires and verifies them | Pending successful tag-triggered run for exact `v1.1.0` commit |\n| `RQ-024` | Human-only authority | Plan and release draft define exact SHA, tag, wheel hash, manifest hash, and workflow-run approval text; tooling never synthesizes approval | Pending authenticated human approval record |\n| `RQ-025` | Publication and observation gate | Procedure forbids rebuild/replacement and requires exact approved assets | Pending publication approval, release creation, download, and fresh hash comparison |\n| `RQ-026` | Post-publication observation gate | Procedure specifies fresh downloaded-wheel environment, `pip check`, and CLI smoke | Pending public release and fresh download/install log |\n\n## Release-State Conclusion\n\nThe implementation can produce and independently verify the evidence required\nthrough candidate and tag qualification. It correctly leaves semantic review,\napproval, tagging, publication, durable retention, public checksum comparison,\nand public installation outside automation authority.\n\nTherefore the qualification implementation can be complete while the proposed\nrelease remains `DRAFT`. No `RQ-*` item that requires a final frozen commit,\nhuman decision, tag-triggered run, published asset, or public download is marked\n`PROVEN` by this document.\n",
      "order": 1,
      "path": "RELEASE_QUALIFICATION_IMPLEMENTATION_AUDIT.md",
      "readingMinutes": 6,
      "sha256": "5704e021d592dd117c3bc98e17239539b21aa99edfb56201c593b741273e2cb1",
      "summary": "Audit date: August 24, 2026",
      "title": "Bounded-Authority-Based-Circuit-Simulation Release Qualification Implementation Audit",
      "wordCount": 1277
    },
    {
      "category": "Qualification and Release",
      "conceptIds": [
        "python-wheel",
        "spdx",
        "mpl2"
      ],
      "headings": [
        {
          "id": "licence-decision-record",
          "level": 1,
          "text": "Licence Decision Record"
        },
        {
          "id": "selected-terms",
          "level": 2,
          "text": "Selected Terms"
        },
        {
          "id": "canonical-text-correction",
          "level": 2,
          "text": "Canonical Text Correction"
        },
        {
          "id": "distribution-consequences",
          "level": 2,
          "text": "Distribution Consequences"
        },
        {
          "id": "remaining-release-gate",
          "level": 2,
          "text": "Remaining Release Gate"
        }
      ],
      "kind": "Policy",
      "markdown": "# Licence Decision Record\n\n## Selected Terms\n\nThe repository owner selected the Mozilla Public License 2.0 on August 27,\n2026. The live authority is commit\n`2eab2dc2306a7ccd9e034b2f1343d1afd559dd22`, whose message is\n`Change license to Mozilla Public License 2.0`.\n\nThe selected SPDX expression is:\n\n```text\nMPL-2.0\n```\n\nThe public project name is\n`Bounded-Authority-Based-Circuit-Simulation`. The compatible Python\ndistribution, import package, and command remain `bab-cs`, `babcs`, and\n`babcs`.\n\n## Canonical Text Correction\n\nThe first owner-selected `LICENSE` file was materially different from\nMozilla's published MPL 2.0 text and therefore could not be represented safely\nas the SPDX expression `MPL-2.0`. The implementation replaces it with Mozilla's\nunmodified canonical text, records `MPL-2.0` in `pyproject.toml`,\n`CITATION.cff`, and wheel core metadata, and includes `LICENSE` under the\nwheel's `.dist-info/licenses/` directory.\n\nThis correction implements the owner's selected licence; it does not choose a\ndifferent licence or add custom terms.\n\n## Distribution Consequences\n\n- Source and distribution archives identify `MPL-2.0` using the standard SPDX\n  expression.\n- The wheel uses Core Metadata 2.4 `License-Expression` and `License-File`\n  fields and carries the exact `LICENSE` bytes.\n- Contributors must preserve the licence text and applicable notices.\n- Commercial use is not separately prohibited; all use and distribution remain\n  subject to MPL 2.0.\n\nThis record documents repository authority and implementation provenance; it is\nnot legal advice.\n\n## Remaining Release Gate\n\nLicence selection is complete. Because the canonical-text and packaging changes\nalter the source and wheel bytes, `v1.1.0` still requires fresh exact-commit\nqualification, evidence review, tagging, tag-triggered qualification, explicit\npublication approval, and public-download verification.\n",
      "order": 2,
      "path": "LICENCE_DECISION.md",
      "readingMinutes": 2,
      "sha256": "fa1a46aae433b898d6347bfcf374fe29684786f753f79ac37002bd39d797f70c",
      "summary": "The repository owner selected the Mozilla Public License 2.0 on August 27, 2026. The live authority is commit 2eab2dc2306a7ccd9e034b2f1343d1afd559dd22, whose message is Change license to Mozilla Public License 2.0.",
      "title": "Licence Decision Record",
      "wordCount": 249
    },
    {
      "category": "Start Here",
      "conceptIds": [
        "babcs",
        "numerical-authority",
        "projection",
        "replay",
        "anchor",
        "recursive-bound",
        "residual",
        "jacobian",
        "stiffness",
        "passivity",
        "deterministic-evidence",
        "phase-error",
        "fail-closed",
        "ab2",
        "adams-bashforth",
        "be",
        "bdf2",
        "json",
        "csv",
        "cli"
      ],
      "headings": [
        {
          "id": "bounded-authority-based-circuit-simulation-v1-normative-specification",
          "level": 1,
          "text": "Bounded-Authority-Based-Circuit-Simulation v1 Normative Specification"
        },
        {
          "id": "requirements",
          "level": 2,
          "text": "Requirements"
        },
        {
          "id": "bab-001-dynamic-state",
          "level": 3,
          "text": "BAB-001 — Dynamic State"
        },
        {
          "id": "bab-002-algebraic-projection",
          "level": 3,
          "text": "BAB-002 — Algebraic Projection"
        },
        {
          "id": "bab-003-adams-bashforth-predictor",
          "level": 3,
          "text": "BAB-003 — Adams-Bashforth Predictor"
        },
        {
          "id": "bab-004-reference-authority",
          "level": 3,
          "text": "BAB-004 — Reference Authority"
        },
        {
          "id": "bab-005-contractive-correction",
          "level": 3,
          "text": "BAB-005 — Contractive Correction"
        },
        {
          "id": "bab-006-runtime-bounds",
          "level": 3,
          "text": "BAB-006 — Runtime Bounds"
        },
        {
          "id": "bab-007-hard-failure-gates",
          "level": 3,
          "text": "BAB-007 — Hard Failure Gates"
        },
        {
          "id": "bab-008-independent-re-anchor",
          "level": 3,
          "text": "BAB-008 — Independent Re-Anchor"
        },
        {
          "id": "bab-009-event-safety",
          "level": 3,
          "text": "BAB-009 — Event Safety"
        },
        {
          "id": "bab-010-stiffness-fallback",
          "level": 3,
          "text": "BAB-010 — Stiffness Fallback"
        },
        {
          "id": "bab-011-passivity-monitor",
          "level": 3,
          "text": "BAB-011 — Passivity Monitor"
        },
        {
          "id": "bab-012-rollout-modes",
          "level": 3,
          "text": "BAB-012 — Rollout Modes"
        },
        {
          "id": "bab-013-deterministic-diagnostics",
          "level": 3,
          "text": "BAB-013 — Deterministic Diagnostics"
        },
        {
          "id": "bab-014-fail-closed-topology-handling",
          "level": 3,
          "text": "BAB-014 — Fail-Closed Topology Handling"
        },
        {
          "id": "bound-semantics",
          "level": 2,
          "text": "Bound Semantics"
        },
        {
          "id": "supported-topology-boundary",
          "level": 2,
          "text": "Supported Topology Boundary"
        }
      ],
      "kind": "Design",
      "markdown": "# Bounded-Authority-Based-Circuit-Simulation v1 Normative Specification\n\n## Requirements\n\n### BAB-001 — Dynamic State\n\nThe canonical differential state shall consist of capacitor voltages followed\nby inductor currents. Algebraic node voltages and voltage-defined branch\ncurrents shall be recomputed from the circuit constraints.\n\n### BAB-002 — Algebraic Projection\n\nEvery predicted, corrected, implicit, and re-anchored differential state shall\nbe projected by solving the algebraic circuit equations. Failure or singularity\nshall reject the operation without committing partial state.\n\n### BAB-003 — Adams-Bashforth Predictor\n\nThe active predictor shall be variable-step AB2:\n\n```text\nz_(n+1) = z_n + h_n * ((1 + r/2) f_n - (r/2) f_(n-1))\nr = h_n / h_(n-1)\n```\n\nAB history shall be invalid until two consistent accepted derivative samples\nexist.\n\n### BAB-004 — Reference Authority\n\nBackward Euler shall be available for startup and recovery. Trapezoidal and\nvariable-step BDF2 shall be available as second-order reference methods.\n\n### BAB-005 — Contractive Correction\n\nActive mode shall correct the AB state toward the implicit reference. If the\nestimated corrected transition is not contractive, the implicit reference\nshall receive full state authority.\n\n### BAB-006 — Runtime Bounds\n\nThe implementation shall separately report predictor/reference error,\ncorrected/reference error, algebraic residual, full residual, positive energy\ninjection, stiffness, amplification, closed-loop gain, and recursive estimated\nbound.\n\n### BAB-007 — Hard Failure Gates\n\nNon-finite metrics, exceeded predictor caps, exceeded residual caps, excessive\npositive energy injection, failed projection, failed reference solve, and\nfailed independent replay shall reject the candidate step.\n\n### BAB-008 — Independent Re-Anchor\n\nAt the configured interval, the solver shall reintegrate from the previous\ntrusted anchor with smaller implicit steps. It shall replace the provisional\nendpoint, rebuild the previous derivative state when available, clear the\nrecursive bound, and increment the anchor generation.\n\n### BAB-009 — Event Safety\n\nKnown waveform breakpoints shall terminate integration steps exactly. No AB\nhistory may cross an event boundary. Before multistep history is cleared, the\nsolver shall independently replay from the trusted anchor to the exact event\ntime, replace the provisional event state, and reapply energy and residual\ngates. Event replay shall use at least eight refinement subdivisions. The next\nstep shall use the configured reference method for implicit startup. An event\nhistory reset shall not, by itself, advance authority generation or replace the\ntrusted anchor.\n\n### BAB-010 — Stiffness Fallback\n\nWhen the timestep multiplied by the differential Jacobian norm exceeds the\nconfigured stiffness limit, the implicit reference shall receive full state\nauthority.\n\n### BAB-011 — Passivity Monitor\n\nStored capacitor and inductor energy, source work, and resistive/device\ndissipation shall be used to detect positive numerical energy injection. The\nenergy monitor shall not be represented as a phase-error bound.\n\n### BAB-012 — Rollout Modes\n\nThe implementation shall provide `disabled`, `shadow`, and `active` modes.\n`shadow` shall be the default and shall never accept an AB-predicted state.\n\n### BAB-013 — Deterministic Diagnostics\n\nThe CLI shall write deterministic CSV step metrics and a JSON summary containing\naccepted steps, rejected steps, anchors, safety anchors, implicit fallbacks,\nmaximum errors, maximum residuals, and contractive/AB step counts.\n\n### BAB-014 — Fail-Closed Topology Handling\n\nUnsupported or singular circuit topologies shall raise an explicit solve error.\nBAB-CSv1 shall not silently add shunt conductance or parasitic storage.\n\n## Bound Semantics\n\nFor the augmented AB history error `E_n`, BAB-CS records a recurrence\n\n```text\nB_(n+1) = q_n B_n + delta_n\n```\n\nwhere `q_n` is the estimated corrected transition gain and `delta_n` contains\nthe measured corrected/reference deviation plus normalized residual defect.\n`certified_contractive` may be true only when `q_n < 1` and the bound is finite.\n\nThis is an internal numerical bound relative to the implemented reference\nsystem. It is not an unconditional proof of exact physical trajectory error.\n\n## Supported Topology Boundary\n\nThe semiexplicit formulation supports circuits for which capacitor voltages and\ninductor currents determine a unique algebraic operating state. Capacitor loops,\ninductor cutsets, conflicting ideal voltage constraints, floating nodes, and\nother singular or higher-index structures may be rejected.\n",
      "order": 0,
      "path": "BAB_CSV1_SPEC.md",
      "readingMinutes": 3,
      "sha256": "96846ac4613100aca580a0ccb65d08ef8a95fff0cf625abb8996034b25e8d615",
      "summary": "The canonical differential state shall consist of capacitor voltages followed by inductor currents. Algebraic node voltages and voltage-defined branch currents shall be recomputed from the circuit constraints.",
      "title": "Bounded-Authority-Based-Circuit-Simulation v1 Normative Specification",
      "wordCount": 604
    },
    {
      "category": "Teaching Lab Tutorials",
      "conceptIds": [
        "babcs",
        "candidate-method",
        "numerical-authority",
        "replay",
        "anchor",
        "recursive-bound",
        "residual",
        "reduced-order-model",
        "deterministic-evidence",
        "phase-error",
        "energy-drift",
        "empirical-coverage",
        "shadow-mode",
        "fail-closed",
        "source-wheel-equivalence",
        "python-wheel",
        "mna",
        "rc",
        "rl",
        "rlc",
        "be",
        "rms",
        "sha256",
        "ngspice"
      ],
      "headings": [
        {
          "id": "scientific-results-report-for-the-ten-bab-cs-tutorials",
          "level": 1,
          "text": "Scientific Results Report for the Ten BAB-CS Tutorials"
        },
        {
          "id": "abstract",
          "level": 2,
          "text": "Abstract"
        },
        {
          "id": "research-questions",
          "level": 2,
          "text": "Research Questions"
        },
        {
          "id": "methods",
          "level": 2,
          "text": "Methods"
        },
        {
          "id": "expected-results",
          "level": 2,
          "text": "Expected Results"
        },
        {
          "id": "actual-results",
          "level": 2,
          "text": "Actual Results"
        },
        {
          "id": "detailed-results-and-interpretation",
          "level": 2,
          "text": "Detailed Results and Interpretation"
        },
        {
          "id": "1-modified-nodal-analysis-and-state-ownership",
          "level": 3,
          "text": "1. Modified Nodal Analysis and State Ownership"
        },
        {
          "id": "2-convergence-by-refinement",
          "level": 3,
          "text": "2. Convergence by Refinement"
        },
        {
          "id": "3-phase-error-versus-energy-error",
          "level": 3,
          "text": "3. Phase Error Versus Energy Error"
        },
        {
          "id": "4-shadow-authority",
          "level": 3,
          "text": "4. Shadow Authority"
        },
        {
          "id": "5-deterministic-packaging",
          "level": 3,
          "text": "5. Deterministic Packaging"
        },
        {
          "id": "6-source-versus-installed-wheel-equivalence",
          "level": 3,
          "text": "6. Source Versus Installed-Wheel Equivalence"
        },
        {
          "id": "7-exact-event-alignment",
          "level": 3,
          "text": "7. Exact Event Alignment"
        },
        {
          "id": "8-empirical-bound-coverage",
          "level": 3,
          "text": "8. Empirical Bound Coverage"
        },
        {
          "id": "9-fallback-and-rejection-forensics",
          "level": 3,
          "text": "9. Fallback and Rejection Forensics"
        },
        {
          "id": "10-external-comparison-with-ngspice",
          "level": 3,
          "text": "10. External Comparison with ngspice"
        },
        {
          "id": "reasons-expected-and-actual-results-differed",
          "level": 2,
          "text": "Reasons Expected and Actual Results Differed"
        },
        {
          "id": "theory-and-practical-outcomes",
          "level": 2,
          "text": "Theory and Practical Outcomes"
        },
        {
          "id": "theoretical-outcomes",
          "level": 3,
          "text": "Theoretical Outcomes"
        },
        {
          "id": "practical-outcomes",
          "level": 3,
          "text": "Practical Outcomes"
        },
        {
          "id": "limitations",
          "level": 2,
          "text": "Limitations"
        },
        {
          "id": "conclusions",
          "level": 2,
          "text": "Conclusions"
        },
        {
          "id": "tutorial-sources",
          "level": 2,
          "text": "Tutorial Sources"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Guide",
      "markdown": "# Scientific Results Report for the Ten BAB-CS Tutorials\n\n**Experiment date:** August 27, 2026\n**System under study:** Bounded-Authority-Based-Circuit-Simulation (`BAB-CS`)\n\n## Abstract\n\nThis report evaluates ten reproducible tutorials that exercise circuit\nformulation, numerical convergence, phase and energy behavior, authority\nseparation, deterministic packaging, source-versus-package equivalence, event\nalignment, empirical bound coverage, rejection forensics, and external\ncomparison with ngspice. BAB-CS is a circuit-simulation architecture in which a\ncandidate numerical method may propose the next state, but separate checks\ndecide whether that state is accepted.\n\nAll ten tutorial verifiers completed successfully. Most numerical expectations\nwere met. The second-order convergence exercise measured orders of\n`2.0011734866053392` and `2.000293128382485`. The phase-and-energy exercise\nshowed that backward Euler dissipated most of the oscillator energy while the\ntrapezoidal method preserved energy to floating-point precision but retained a\nmeasurable phase error. Deterministic package builds produced identical Secure\nHash Algorithm 256-bit (`SHA-256`) fingerprints, and the selected source and\ninstalled-wheel runs produced identical artifacts.\n\nTwo results require special attention. The empirical bound covered `0` of `17`\neligible samples, with the largest measured authority-epoch drift about\n`17.904031990116184` times the largest recursive internal bound. The external\nngspice suite completed all `20` mapped cases, but the reduced-order H-bridge\ncase produced a maximum native-unit difference of `3.730147981349861`. These\nresults are retained as research findings rather than hidden or converted into\nrelease claims.\n\n![BAB-CS bounded-authority workflow](html/assets/authority-loop.svg \"A candidate method proposes a state, while independent projection, reference, correction, rejection, and replay paths control acceptance.\")\n\n## Research Questions\n\nThe tutorials address five scientific questions:\n\n1. Does the implemented circuit formulation preserve the intended ownership of\n   dynamic states and algebraic unknowns?\n2. Do measured refinement, phase, and energy results agree with the known\n   mathematical behavior of the tested integration methods?\n3. Does BAB-CS preserve a separation between proposal authority and accepted\n   state authority, including shadow calculations, fallbacks, and rejections?\n4. Can the same declared source produce deterministic packages and equivalent\n   source-versus-installed-package results?\n5. Do empirical internal-bound and external-simulator comparisons expose both\n   agreement and disagreement without overstating what the evidence proves?\n\n## Methods\n\nThe primary tutorial suite was executed with:\n\n```bash\nPYTHONPATH=src python lab/support/verify.py \\\n  --exercise all --development \\\n  --output /tmp/babcs-scientific-tutorials.json\n```\n\nThe verifier completed all ten exercises and reported `all_passed: true`.\nDevelopment mode was used because the working tree contained uncommitted work;\nit permits reproducibility experiments without claiming release qualification.\n\nThe live external comparison was executed with:\n\n```bash\nPYTHONPATH=src python tools/run_external_suite.py \\\n  benchmarks/external/manifest.json \\\n  --output-root /tmp/babcs-scientific-ngspice\n```\n\nngspice is an open-source simulator from the Simulation Program with Integrated\nCircuit Emphasis (`SPICE`) family. The installed tool identified itself as\n`ngspice-46 : Circuit level simulation program`. It completed all `20` cases\nand produced `81` retained files, including generated netlists, logs, raw data,\nand comparison reports.\n\nThe tutorials use deliberately bounded examples. Resistor-capacitor (`RC`),\nresistor-inductor (`RL`), inductor-capacitor (`LC`), and\nresistor-inductor-capacitor (`RLC`) circuits isolate first-order, oscillatory,\nand damped behavior. The buck-like converter, H-bridge RL load, and direct\ncurrent (`DC`)-link RLC cases are reduced-order numerical experiments. A\nreduced-order experiment intentionally omits device detail that is unnecessary\nfor the stated numerical question. These cases are not production\nsemiconductor, protection, thermal, or electromagnetic models.\n\n## Expected Results\n\nThe expectations were derived from circuit equations, numerical-method theory,\nand the repository's declared evidence contracts.\n\n| Tutorial | Expected result |\n| --- | --- |\n| 1. Modified nodal analysis | The capacitor voltage is the dynamic state, algebraic variables remain separate, the initial derivative is `1000` volts per second, and the circuit-equation residual is zero within floating-point precision. |\n| 2. Convergence by refinement | Halving the step size reduces the error by about four for a second-order method, giving a measured order near two. |\n| 3. Phase versus energy | Backward Euler is numerically dissipative. The trapezoidal method preserves oscillator energy much better, but energy preservation does not eliminate phase error. |\n| 4. Shadow authority | Enabling a non-authoritative shadow method does not change the accepted state beyond floating-point tolerance, while still producing separate diagnostics. |\n| 5. Deterministic packaging | Two builds from the same controlled source and metadata produce byte-identical wheel files and equal SHA-256 fingerprints. A wheel is an installable Python package file. |\n| 6. Source versus wheel equivalence | Selected simulations run from the source tree and from an isolated installed wheel produce identical summary and trace artifacts. |\n| 7. Event alignment | Every scheduled discontinuity up to the stop time is accepted at its declared time, history is reset at each event, and no step silently crosses an event. |\n| 8. Empirical bound coverage | An optimistic conservative-bound hypothesis predicts that most eligible samples are covered. The stricter requirement is honest reporting even if coverage is poor. |\n| 9. Fallback and rejection forensics | The scheduled H-bridge challenges the candidate method, produces visible rejections and fallbacks, and still reaches the declared stop time. |\n| 10. Semantic ngspice mapping | All 20 cases preserve component meaning and state order. Smooth cases should generally agree more closely than event-dominated or reduced-order switching cases, without assuming either tool is an unquestionable oracle. |\n\n## Actual Results\n\n| Tutorial | Principal measured result | Outcome against expectation |\n| --- | --- | --- |\n| 1. Modified nodal analysis | One dynamic coordinate, four algebraic coordinates, derivative `1000.0000000000001` volts per second, residual `0.0`. | Matched within floating-point precision. |\n| 2. Convergence by refinement | Errors `3.068987885731511e-4`, `7.666231473091312e-5`, and `1.9161684994717376e-5`; orders `2.0011734866053392` and `2.000293128382485`. | Matched second-order theory. |\n| 3. Phase versus energy | Backward Euler phase error `0.08248810247463056` radians and energy error/span `0.9805531365134604`; trapezoidal phase error `0.020658618955850548` radians and final energy error `6.352747104407253e-16`. | Matched the expected distinction between phase and energy. |\n| 4. Shadow authority | Active-to-shadow accepted-state difference `1.3877787807814457e-17`; tolerance `3.552713678800501e-15`; ratio `0.00390625`. | Matched; no accepted-state authority leak was observed. |\n| 5. Deterministic packaging | Two 19-member wheels had the same SHA-256 fingerprint: `ca5d648e60dfd9923deadc85fb304b45dc9ecf87aecc982a369d3766542806f2`. | Matched; release evidence remained false in development mode. |\n| 6. Source versus wheel equivalence | Five selected cases had matching summary and trace artifacts; the isolated run confirmed `source_tree_excluded: true`; the observatory smoke artifacts also matched. | Matched the numerical and isolation expectations. |\n| 7. Event alignment | Five scheduled events were accepted at `0.0001`, `0.0002`, `0.0005`, `0.0006000000000000001`, and `0.0009000000000000001` seconds; five event resets and four startup steps were recorded. | Matched; the final event coincided with the stop time. |\n| 8. Empirical bound coverage | `0` of `17` eligible samples covered; maximum drift `11512.211750693821`; maximum bound `642.995485991595`; ratio `17.904031990116184`; formal enclosure `false`. | The optimistic coverage expectation failed; the reporting-integrity expectation passed. |\n| 9. Fallback and rejection forensics | Nine rejected candidate attempts, eight implicit fallbacks, eight event resets, twelve periodic reanchors, and completion at `0.0004` seconds. | Matched the qualitative robustness and evidence-retention expectation. |\n| 10. Semantic ngspice mapping | All `20` cases, `14` feature types, and `28` dynamic coordinates mapped and ran. The H-bridge maximum difference was `3.730147981349861`; its root-mean-square difference was `0.23016505280206029`. | Structural expectation passed; the H-bridge difference exceeded a close-agreement expectation. |\n\nRoot-mean-square (`RMS`) difference is the square root of the average squared\ndifference across compared samples. The external maximum differences retain\nthe native unit of the selected state coordinate. They are not dimensionless\naccuracy scores and should not be averaged into a universal ranking across\nvoltages and currents.\n\n## Detailed Results and Interpretation\n\n### 1. Modified Nodal Analysis and State Ownership\n\nModified nodal analysis (`MNA`) writes circuit equations in terms of node\nvoltages, selected branch currents, and energy-storage states. The tutorial\nidentified capacitor voltage `v(C1)` as the single dynamic state while keeping\nnode voltages and source current in the algebraic solve.\n\nFor a one-volt step across a `1000`-ohm resistor and a `1e-6`-farad capacitor,\nthe expected initial derivative is:\n\n```text\n(1 volt - 0 volts) / (1000 ohms * 1e-6 farads) = 1000 volts per second\n```\n\nThe observed value, `1000.0000000000001`, differs from the exact decimal result\nonly because most decimal fractions cannot be represented exactly in binary\nfloating-point arithmetic. The zero residual shows that the tested equation\nownership and algebraic reconstruction were internally consistent.\n\n### 2. Convergence by Refinement\n\n![Measured second-order convergence](html/assets/tutorial-02-convergence.svg \"The measured error decreases by approximately four whenever the timestep is halved, producing an observed order near two.\")\n\nThe step size was halved from `1e-4` to `5e-5` and then to `2.5e-5` seconds. The\nmeasured error ratios were `4.003254919322154` and `4.000812807018167`, close to\nthe theoretical ratio of four for a second-order method. The corresponding\norders were slightly above two because a finite refinement sequence contains\nhigher-order error terms and floating-point effects in addition to the leading\nsecond-order term.\n\nThe practical conclusion is stronger than a method label alone: this exact\nimplementation, circuit, interval, norm, and refinement sequence displayed the\nexpected second-order trend.\n\n### 3. Phase Error Versus Energy Error\n\n![Phase and energy comparison](html/assets/tutorial-03-phase-energy.svg \"Backward Euler loses oscillator energy, while trapezoidal integration preserves energy much more closely but retains phase error.\")\n\nPhase error measures how far an oscillation is shifted in time. Energy error\nmeasures how much the computed electrical and magnetic energy differs from its\nreference behavior. These quantities answer different questions.\n\nBackward Euler, an implicit first-order method, produced about\n`4.726220131838973` degrees of phase error and an energy error/span of\n`0.9805531365134604`. The trapezoidal method produced a smaller phase error of\nabout `1.183651676739196` degrees and preserved final energy to approximately\n`6.35e-16` relative error. The trapezoidal result still had nonzero phase error,\nconfirming that excellent energy behavior cannot be used as a substitute for\ntiming accuracy.\n\n### 4. Shadow Authority\n\nA shadow method is executed for comparison but is not permitted to approve the\naccepted state. The active bounded configuration and the shadow-enabled\nconfiguration each recorded `19` candidate steps, while the independent\nauthority performed `20` reference solves.\n\nThe accepted-state difference was approximately 256 times smaller than the\ndeclared comparison tolerance. The small nonzero value is consistent with\nfloating-point evaluation and solve ordering. It is not evidence that the\nshadow method changed the accepted trajectory.\n\n### 5. Deterministic Packaging\n\nDeterministic packaging means that the same declared source and controlled\nmetadata produce the same package bytes. Both builds contained `19` members and\nhad the same SHA-256 fingerprint. The result demonstrates byte-level\nrepeatability for the measured build path.\n\nThe verifier correctly retained `release_evidence: false`. A deterministic\ndevelopment build is useful evidence, but a dirty working tree is not an\napproved release snapshot.\n\n### 6. Source Versus Installed-Wheel Equivalence\n\nThe source and installed-wheel runs matched for all five selected cases, and\nthe isolated wheel process confirmed that it did not import BAB-CS from the\nsource tree. This separates package behavior from accidental local imports.\n\nOne expected difference is provenance rather than simulation output. A report\nthat records the source-tree fingerprint changes when documentation, tests, or\nother tracked source inputs change. That changing report fingerprint is correct\nbehavior because it preserves source identity; it is not a numerical\nsource-versus-wheel mismatch.\n\n### 7. Exact Event Alignment\n\nAn event is a declared time at which a source or switch schedule changes. The\nrun accepted all five events exactly as represented by the floating-point time\ngrid. The long forms `0.0006000000000000001` and\n`0.0009000000000000001` are binary floating-point representations of intended\ndecimal schedule values, not extra physical delays.\n\nThe run recorded five history resets but four startup steps because the final\nevent occurred at the stop time. No subsequent integration step was needed\nafter that last reset.\n\n### 8. Empirical Bound Coverage\n\n![Empirical recursive-bound coverage](html/assets/tutorial-08-bound-coverage.svg \"The measured authority-epoch drift exceeds the recursive internal bound on all eligible samples in this tutorial run.\")\n\nThe recursive internal bound is BAB-CS's running estimate of accumulated\nmodeled numerical error since a trusted anchor. An anchor is a retained\naccepted state used to start an independent replay. Authority-epoch drift is\nthe independently measured difference accumulated since that anchor.\n\nNone of the `17` eligible samples satisfied:\n\n```text\nauthority-epoch drift <= recursive internal bound\n```\n\nThe largest measured drift was about `17.9` times the largest bound. This\nfalsifies the optimistic hypothesis that the current bound and configuration\nare conservative for this experiment. It does not establish one root cause.\nControlled follow-up should separately test local-to-global error propagation,\nanchor-age scaling, omitted error sources, and bound-configuration parameters.\n\nThe reporting behavior passed its stricter requirement: the zero coverage was\nretained, and no formal enclosure was claimed.\n\n### 9. Fallback and Rejection Forensics\n\n![Fallback and rejection evidence](html/assets/tutorial-09-fallback-forensics.svg \"Rejected candidate work, implicit fallbacks, event resets, and periodic reanchors remain separately visible.\")\n\nA rejected candidate attempt is a proposal that failed a declared gate. An\nimplicit fallback transfers authority to a method that solves equations\ncontaining the new state. The two counts need not match one-for-one because a\nrejected attempt can be followed by a smaller successful retry, and several\nattempts can precede one accepted state.\n\nEight rejections were attributed to the embedded candidate cap and one to a\nreference-solve failure. The simulation still reached `0.0004` seconds through\ncontrolled retries and eight fallbacks. This is evidence of fail-closed\nprogress: unsuccessful proposals remained visible and were not silently\npromoted.\n\n### 10. External Comparison with ngspice\n\n![BAB-CS versus ngspice maximum differences](html/assets/ngspice-error-overview.svg \"A logarithmic graph compares the maximum native-unit BAB-CS-versus-ngspice difference for all twenty mapped cases.\")\n\nThe structural mapper preserved all `20` declared cases and the canonical order\nof `28` dynamic coordinates. Smooth first-order cases had maximum native-unit\ndifferences between approximately `6.54e-5` and `5.13e-3`. Scheduled cases were\ngenerally larger, including `0.11593356837261994` for switched RC. The\nreduced-order H-bridge had the largest maximum difference,\n`3.730147981349861`, although its final absolute error was approximately\n`3.02e-9`.\n\nThe retained summary does not record the exact time of the maximum H-bridge\ndifference. Event-step placement, output interpolation, method-specific damping\nor phase, and ideal-switch execution are plausible hypotheses, but the present\ndata cannot select among them. A follow-up experiment should retain the time\nand state coordinate of every maximum, then compare traces immediately before\nand after each scheduled switch.\n\n## Reasons Expected and Actual Results Differed\n\nThe observed departures have different scientific meanings and should not be\ncombined into one generic error category.\n\n1. **Binary floating-point representation.** Tiny differences in Tutorials 1,\n   4, and 7 arise because the computer stores finite binary approximations to\n   decimal values and may evaluate equivalent operations in different orders.\n2. **Finite refinement and higher-order terms.** Tutorial 2 measured orders\n   slightly above two because the theoretical order describes the leading\n   behavior as the step size approaches zero, while the experiment uses three\n   finite step sizes.\n3. **Intrinsic integration-method behavior.** Tutorial 3 differs by design:\n   backward Euler adds numerical damping, while trapezoidal integration largely\n   preserves oscillator energy but still accumulates phase error.\n4. **Evidence identity versus numerical identity.** Tutorial 6 permits a\n   provenance-bearing report fingerprint to change when the source snapshot\n   changes, even when the compared numerical artifacts remain equal.\n5. **Attempts versus accepted steps.** Tutorial 9 recorded nine rejections and\n   eight fallbacks because rejection, retry, fallback, and acceptance are\n   distinct events rather than one-to-one counters.\n6. **Insufficient empirical bound coverage.** Tutorial 8 found that the current\n   recursive bound was too small for every eligible measured drift sample. The\n   experiment narrows the valid claim but does not by itself prove whether the\n   deficiency lies in propagation, scaling, omitted terms, or configuration.\n7. **Independent simulator semantics.** Tutorial 10 compares different\n   integration, event, interpolation, and nonlinear-solve implementations. The\n   H-bridge difference is therefore an investigation target, not proof that one\n   simulator is universally correct and the other is wrong.\n\n## Theory and Practical Outcomes\n\n### Theoretical Outcomes\n\n- Dynamic-state ownership can be tested independently from algebraic circuit\n  reconstruction.\n- Measured convergence order provides implementation evidence that a method\n  name alone cannot supply.\n- Phase accuracy and energy behavior are independent axes of oscillator\n  quality.\n- A shadow calculation can produce comparative evidence without receiving\n  accepted-state authority.\n- Internal error bounds require empirical coverage studies and cannot become\n  formal proofs through measurement alone.\n- External simulators are most useful as independent falsification tools when\n  disagreement remains visible.\n\n### Practical Outcomes\n\n- Engineers can use the tutorials as compact regression experiments when\n  changing matrix assembly, integration methods, event handling, packaging, or\n  comparison tooling.\n- The event and fallback tutorials show how BAB-CS supports auditable\n  reduced-order studies of switched systems without silently accepting failed\n  proposals.\n- The deterministic build and source-wheel exercises support reproducible\n  review, distribution, and rollback.\n- The zero bound coverage identifies a concrete research priority before the\n  internal bound is used for stronger engineering claims.\n- The H-bridge difference identifies a specific external-comparison case for\n  time-localized investigation.\n\n## Limitations\n\nThe evidence is bounded by the declared tutorial inputs, software versions,\nstep controls, tolerances, and measured environment. The package tests were run\nin development mode and do not constitute release qualification. Empirical\ncoverage is not formal enclosure. ngspice is independent comparison evidence,\nnot an oracle. The reduced-order power-stage examples do not model production\nsemiconductor switching, parasitics, thermal limits, magnetic saturation,\nprotection, electromagnetic interference, or hardware safety.\n\nThe external comparison reports the largest difference across native voltage\nand current coordinates. Because those coordinates have different units, the\nvalues support case-level diagnosis but not a universal cross-case accuracy\nranking. The retained H-bridge summary also lacks the time and coordinate of\nthe maximum, limiting causal interpretation.\n\n## Conclusions\n\nThe ten tutorials form a coherent scientific evidence set rather than ten\nisolated demonstrations. Circuit ownership, second-order refinement, phase and\nenergy interpretation, shadow separation, deterministic packaging,\nsource-wheel equivalence, event alignment, and rejection forensics behaved as\nexpected in the measured runs.\n\nThe most important negative result is the empirical bound coverage of `0` from\n`17` eligible samples. The correct conclusion is not that BAB-CS has a proven\nenclosure, but that the current recursive bound remains diagnostic for this\nconfiguration and requires refinement or a narrower applicability claim. The\nlargest external discrepancy, the reduced-order H-bridge maximum of\n`3.730147981349861`, similarly defines a follow-up investigation rather than a\nuniversal simulator ranking.\n\nBAB-CS is useful because it keeps these distinctions explicit: a candidate may\npropose, independent authority may correct or reject, and evidence may reveal\nboth strengths and limits. The completed tutorials demonstrate that this\narchitecture supports reproducible engineering investigation while preserving\nthe reasons a result should—or should not—be trusted.\n\n## Tutorial Sources\n\n1. [Modified nodal analysis and state ownership](tutorials/01_MNA_STATE_OWNERSHIP.md)\n2. [Convergence by measured refinement](tutorials/02_CONVERGENCE_BY_REFINEMENT.md)\n3. [Phase error versus energy error](tutorials/03_PHASE_VERSUS_ENERGY.md)\n4. [Shadow authority](tutorials/04_SHADOW_AUTHORITY.md)\n5. [Deterministic packaging](tutorials/05_DETERMINISTIC_PACKAGING.md)\n6. [Source versus installed-wheel equivalence](tutorials/06_SOURCE_WHEEL_EQUIVALENCE.md)\n7. [Exact event alignment](tutorials/07_EVENT_ALIGNMENT.md)\n8. [Empirical bound coverage](tutorials/08_EMPIRICAL_BOUND_COVERAGE.md)\n9. [Fallback and rejection forensics](tutorials/09_FALLBACK_AND_REJECTION_FORENSICS.md)\n10. [Semantic mapping to ngspice](tutorials/10_SEMANTIC_NGSPICE_MAPPING.md)\n\n## Claim Boundary\n\nThis report records measured development evidence from the declared tutorials\nand live ngspice suite on August 27, 2026. It does not claim formal numerical\nenclosure, exact physical-model truth, production power-device fidelity,\nhardware safety, release qualification, certification, or universal\nsuperiority over another simulator.\n",
      "order": 0,
      "path": "TUTORIAL_SCIENTIFIC_RESULTS_REPORT.md",
      "readingMinutes": 14,
      "sha256": "3eaf0d4bb72909f41061a3e93d0bcb4c90ab2a127b26b0c4272bbef4001de5fc",
      "summary": "Experiment date: August 27, 2026 System under study: Bounded-Authority-Based-Circuit-Simulation (BAB-CS)",
      "title": "Scientific Results Report for the Ten BAB-CS Tutorials",
      "wordCount": 3064
    },
    {
      "category": "Teaching Lab Tutorials",
      "conceptIds": [
        "babcs",
        "projection",
        "residual",
        "deterministic-evidence",
        "mna",
        "dae",
        "rc",
        "kcl",
        "ngspice"
      ],
      "headings": [
        {
          "id": "tutorial-1-modified-nodal-analysis-and-state-ownership",
          "level": 1,
          "text": "Tutorial 1: Modified Nodal Analysis and State Ownership"
        },
        {
          "id": "what-you-will-learn",
          "level": 2,
          "text": "What You Will Learn"
        },
        {
          "id": "run-the-exercise",
          "level": 2,
          "text": "Run the Exercise"
        },
        {
          "id": "expected-results",
          "level": 2,
          "text": "Expected Results"
        },
        {
          "id": "observed-data",
          "level": 2,
          "text": "Observed Data"
        },
        {
          "id": "expected-versus-actual-results",
          "level": 2,
          "text": "Expected Versus Actual Results"
        },
        {
          "id": "follow-the-equation-ownership",
          "level": 2,
          "text": "Follow the Equation Ownership"
        },
        {
          "id": "read-the-evidence",
          "level": 2,
          "text": "Read the Evidence"
        },
        {
          "id": "theory-and-practical-outcomes",
          "level": 2,
          "text": "Theory and Practical Outcomes"
        },
        {
          "id": "conclusion",
          "level": 2,
          "text": "Conclusion"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Guide",
      "markdown": "# Tutorial 1: Modified Nodal Analysis and State Ownership\n\nModified nodal analysis (`MNA`) is a way to write circuit equations using node\nvoltages plus the extra branch currents required by elements such as ideal\nvoltage sources. In plain words, it turns a circuit drawing into a system of\nequations that a computer can solve. This tutorial shows why the values that\nstore energy are not always the same thing as the complete set of unknowns in\nthose equations.\n\n![Modified nodal analysis state ownership](html/assets/tutorial-01-mna.svg \"Modified nodal analysis separates dynamic state, algebraic projection, and derivative evaluation.\")\n\n## What You Will Learn\n\nYou will distinguish four ideas:\n\n1. a **dynamic state**, meaning a value that carries stored energy from one\n   time to the next;\n2. an **algebraic unknown**, meaning a value solved from the circuit constraints\n   at the current time;\n3. a **projection**, meaning the solve that makes a proposed state consistent\n   with all circuit equations; and\n4. a **derivative**, meaning the instantaneous rate at which the dynamic state\n   is changing.\n\nThe exercise uses a resistor-capacitor (`RC`) circuit. A resistor-capacitor\ncircuit contains a resistor, which dissipates energy, and a capacitor, which\nstores electric-field energy.\n\n## Run the Exercise\n\n```bash\nPYTHONPATH=src python lab/support/verify.py --exercise 01-mna\n```\n\n`PYTHONPATH=src` tells Python to import the BAB-CS package from the repository's\n`src` directory. The command runs a deterministic verifier rather than asking\nyou to judge a plot by eye.\n\n## Expected Results\n\nThe circuit has one capacitor, so theory predicts one dynamic state:\n`v(C1)`. Modified nodal analysis should require additional algebraic unknowns\nfor node voltages and ideal-source branch current. With a 1-volt source, a\n1000-ohm resistor, a 1-microfarad capacitor, and zero initial capacitor voltage,\nthe expected initial derivative is:\n\n```text\n(1 volt - 0 volts) / (1000 ohms × 0.000001 farads) = 1000 volts per second\n```\n\nThe algebraic residual is expected to be zero or below the declared numerical\ntolerance if projection solves the initial circuit constraints correctly.\n\n## Observed Data\n\nThe exercise was run on August 27, 2026. It returned the following values:\n\n| Measurement | Observed value |\n| --- | --- |\n| Dynamic-state name | `v(C1)` |\n| Ordered circuit nodes | `vin`, `out` |\n| Dynamic-state dimension | `1` |\n| Algebraic dimension | `4` |\n| Initial capacitor-voltage derivative | `1000.0000000000001` volts per second |\n| Algebraic residual | `0.0` |\n| Dynamic state differs from the node-voltage vector | `true` |\n\nThe one dynamic coordinate stores the capacitor's memory. The four algebraic\ncoordinates reconstruct the two node voltages and the additional branch\ncurrents needed by the modified nodal analysis equations. The zero residual\nmeans the algebraic equations were satisfied to the reported numerical\nprecision at the initial evaluation. The derivative means the capacitor voltage\ninitially rises by about 1000 volts per second; it does not mean the voltage\nwill continue rising at that constant rate.\n\n## Expected Versus Actual Results\n\nThe state dimensions, state name, node order, and zero residual matched the\nexpectation exactly. The computed derivative was\n`1000.0000000000001` rather than the decimal value `1000`. The difference is\napproximately `1.1e-13` volts per second and is caused by binary\nfloating-point representation, not by a physically meaningful circuit error.\nNo discrepancy requiring a model or solver correction was observed.\n\n## Follow the Equation Ownership\n\nThe declared capacitor voltage, `v(C1)`, is the only dynamic state in this\nexample. It must be retained because the capacitor's next current depends on\nhow its voltage changes over time.\n\nThe node voltages and ideal-source branch current are algebraic unknowns. They\nare reconstructed at each evaluation so that Kirchhoff current law (`KCL`) is\nsatisfied. Kirchhoff current law means that current entering a node must balance\ncurrent leaving that node.\n\nThe algebraic projection therefore answers a different question from the time\nintegrator. The time integrator asks, “What state should be proposed next?” The\nprojection asks, “If that state were used, can the complete circuit equations\nbe satisfied?” BAB-CS keeps these responsibilities separate so that a candidate\nmethod cannot approve an inconsistent state merely because its time-update\nformula returned a number.\n\n## Read the Evidence\n\nThe verifier reports:\n\n- the dynamic-state names;\n- the ordered circuit nodes;\n- the dynamic and algebraic dimensions;\n- the initial state derivative; and\n- the algebraic residual.\n\nA residual is the equation mismatch left after a solve. A small algebraic\nresidual proves that the circuit constraints were solved closely for that\nevaluation. It does **not** prove that the transient trajectory is accurate over\nthe complete time interval.\n\n## Theory and Practical Outcomes\n\nThe theoretical outcome is that stored-energy coordinates and instantaneous\ncircuit constraints have distinct ownership. Time integration advances the\ncapacitor voltage, while projection reconstructs a constraint-consistent\nalgebraic solution. This separation is necessary for circuit equations that\ncombine derivatives with simultaneous algebraic constraints.\n\nState ownership matters when a circuit contains several capacitors, inductors,\nideal sources, controlled switches, or nonlinear devices. Confusing a node\nvoltage with a canonical state coordinate can reorder data, compare the wrong\nquantities, or hide an invalid external mapping. The 20-case ngspice work in\nTutorial 10 uses the same rule: capacitor voltages come before inductor currents\nin the exported BAB-CS state vector.\n\n## Conclusion\n\nThe experiment supports the expected modified-nodal-analysis ownership model.\nIt provides a practical baseline for interpreting every later tutorial because\nexternal mappings, error measurements, and authority comparisons are valid only\nwhen they compare the same canonical state coordinates.\n\n## Claim Boundary\n\nThis exercise proves formulation consistency for one small RC model. It does\nnot establish support for every differential-algebraic equation, every circuit\ntopology, or every physical parasitic effect.\n",
      "order": 1,
      "path": "tutorials/01_MNA_STATE_OWNERSHIP.md",
      "readingMinutes": 5,
      "sha256": "5cbd3770eac29e6a73002dcf071ac39cb296ef799cf71ea76b69b6a0b7d46cd8",
      "summary": "Modified nodal analysis (MNA) is a way to write circuit equations using node voltages plus the extra branch currents required by elements such as ideal voltage sources. In plain words, it turns a circuit drawing into a system of…",
      "title": "Tutorial 1: Modified Nodal Analysis and State Ownership",
      "wordCount": 886
    },
    {
      "category": "Teaching Lab Tutorials",
      "conceptIds": [
        "babcs",
        "replay",
        "fixed-step",
        "rc"
      ],
      "headings": [
        {
          "id": "tutorial-2-convergence-by-measured-refinement",
          "level": 1,
          "text": "Tutorial 2: Convergence by Measured Refinement"
        },
        {
          "id": "what-you-will-learn",
          "level": 2,
          "text": "What You Will Learn"
        },
        {
          "id": "run-the-exercise",
          "level": 2,
          "text": "Run the Exercise"
        },
        {
          "id": "expected-results",
          "level": 2,
          "text": "Expected Results"
        },
        {
          "id": "observed-data",
          "level": 2,
          "text": "Observed Data"
        },
        {
          "id": "expected-versus-actual-results",
          "level": 2,
          "text": "Expected Versus Actual Results"
        },
        {
          "id": "understand-the-refinement-test",
          "level": 2,
          "text": "Understand the Refinement Test"
        },
        {
          "id": "why-fixed-inputs-matter",
          "level": 2,
          "text": "Why Fixed Inputs Matter"
        },
        {
          "id": "theory-and-practical-outcomes",
          "level": 2,
          "text": "Theory and Practical Outcomes"
        },
        {
          "id": "conclusion",
          "level": 2,
          "text": "Conclusion"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Guide",
      "markdown": "# Tutorial 2: Convergence by Measured Refinement\n\nConvergence means that a numerical result approaches an independent authority\nas the timestep becomes smaller. A timestep is the amount of simulated time\nadvanced in one accepted step. One small error at one timestep is not a\nconvergence result because it does not show a trend.\n\n![Convergence by measured refinement](html/assets/tutorial-02-convergence.svg \"Maximum resistor-capacitor error decreases over three fixed-step refinements.\")\n\n## What You Will Learn\n\nThis tutorial measures a fixed-step trapezoidal method on a resistor-capacitor\n(`RC`) charging problem. Trapezoidal integration uses the average of the state\nrate at the beginning and end of a timestep. For a smooth linear problem, its\nglobal error is expected to decrease approximately with the square of the\ntimestep.\n\nThe analytic authority is the closed-form RC charging equation. Analytic means\nthat the reference value comes from a known mathematical formula rather than a\nsecond numerical run.\n\n## Run the Exercise\n\n```bash\nPYTHONPATH=src python lab/support/verify.py --exercise 02-convergence\n```\n\nThe verifier runs the same circuit and time interval with three progressively\nsmaller fixed timesteps. Every run uses the same analytic authority and the\nsame error measurement.\n\n## Expected Results\n\nTrapezoidal integration has second-order global accuracy on this smooth linear\nproblem. The theoretical error model is proportional to the square of the\ntimestep. Halving the timestep should therefore reduce the maximum error by\napproximately four, and the observed order should approach `2`.\n\n## Observed Data\n\nThe exercise was run on August 27, 2026. A microsecond is one millionth of a\nsecond.\n\n| Fixed timestep | Maximum voltage error | Error reduction from previous run |\n| ---: | ---: | ---: |\n| `100` microseconds | `3.068987885731511e-4` volts | not applicable |\n| `50` microseconds | `7.666231473091312e-5` volts | `4.003254919322154` times smaller |\n| `25` microseconds | `1.9161684994717376e-5` volts | `4.000812807018167` times smaller |\n\n| Refinement interval | Observed order |\n| --- | ---: |\n| `100` to `50` microseconds | `2.0011734866053392` |\n| `50` to `25` microseconds | `2.000293128382485` |\n\nEach halving reduces the maximum error by approximately four. That repeated\nratio produces an observed order near two, which is the measured evidence for\nsecond-order behavior on this smooth case.\n\n## Expected Versus Actual Results\n\nThe expected and actual trends agree. The measured reduction factors were\n`4.003254919322154` and `4.000812807018167`, slightly larger than the ideal\nfactor of four. The corresponding orders were `2.0011734866053392` and\n`2.000293128382485`, slightly above two.\n\nThe small difference from exactly second order is expected in a finite\nrefinement study. The total error contains the leading square-of-timestep term,\nsmaller higher-order terms, and floating-point effects. As the timestep becomes\nsmaller, the higher-order contribution changes the ratio slightly before the\neventual roundoff floor is reached.\n\n## Understand the Refinement Test\n\nThe exercise records the maximum voltage error over the complete accepted\ntrajectory. It then calculates observed order from neighboring refinements:\n\n```text\nobserved order = log(coarse error / fine error) / log(2)\n```\n\nThe denominator uses `log(2)` because each refinement halves the timestep. If\nhalving the timestep reduces error by roughly four, the observed order is near\ntwo.\n\nThe test requires both of these conditions:\n\n1. every finer run has a smaller maximum error; and\n2. the measured order remains consistent with second-order behavior.\n\nThis is stronger than reporting the finest error alone. It can reveal a\nmistaken reference, a coding defect, a changed method, or a regime where the\nexpected asymptotic trend has not yet appeared.\n\n## Why Fixed Inputs Matter\n\nA refinement study becomes misleading if several things change at once. Do not\nchange the model, stop time, authority, tolerance scaling, or measured state\nwhile claiming that only the timestep caused the difference.\n\nNonlinear diode and switched cases usually do not have a convenient exact\nformula over the whole run. For them, BAB-CS uses a refined replay: a separate\nnumerical recomputation with a declared implicit method and smaller internal\nsteps. That is useful evidence, but it must be labeled numerical rather than\nanalytic.\n\n## Theory and Practical Outcomes\n\nThe theoretical outcome is a measured confirmation of the method's expected\nglobal order for a smooth resistor-capacitor transient. It does not rely on one\nsmall error value; it relies on a repeatable refinement slope.\n\nConvergence studies help choose a timestep for filter startup, resonant\ntransients, switching schedules, and controller test models. They also reveal\nwhen a method's formal order is not being achieved because discontinuities,\nnonlinear solves, or event handling dominate the error.\n\n## Conclusion\n\nThe experiment met its expected second-order result. In practice, the data\nsupports using refinement studies to select a timestep and to detect when a\nmethod, reference, or implementation no longer exhibits its expected behavior.\n\n## Claim Boundary\n\nThe measured second-order trend applies to this declared smooth RC case and\nthese three timesteps. It does not prove second-order behavior for every\ncircuit, switching event, nonlinear solve, or adaptive execution path.\n",
      "order": 2,
      "path": "tutorials/02_CONVERGENCE_BY_REFINEMENT.md",
      "readingMinutes": 4,
      "sha256": "2334c586297a09fbcdd372852c111bd6f693bdc1a8934cbda966bf4c5c4a4749",
      "summary": "Convergence means that a numerical result approaches an independent authority as the timestep becomes smaller. A timestep is the amount of simulated time advanced in one accepted step. One small error at one timestep is not a…",
      "title": "Tutorial 2: Convergence by Measured Refinement",
      "wordCount": 770
    },
    {
      "category": "Teaching Lab Tutorials",
      "conceptIds": [
        "babcs",
        "phase-error",
        "energy-drift",
        "lc",
        "be"
      ],
      "headings": [
        {
          "id": "tutorial-3-phase-error-versus-energy-error",
          "level": 1,
          "text": "Tutorial 3: Phase Error Versus Energy Error"
        },
        {
          "id": "what-you-will-learn",
          "level": 2,
          "text": "What You Will Learn"
        },
        {
          "id": "run-the-exercise",
          "level": 2,
          "text": "Run the Exercise"
        },
        {
          "id": "expected-results",
          "level": 2,
          "text": "Expected Results"
        },
        {
          "id": "observed-data",
          "level": 2,
          "text": "Observed Data"
        },
        {
          "id": "expected-versus-actual-results",
          "level": 2,
          "text": "Expected Versus Actual Results"
        },
        {
          "id": "read-the-two-measurements-separately",
          "level": 2,
          "text": "Read the Two Measurements Separately"
        },
        {
          "id": "theory-and-practical-outcomes",
          "level": 2,
          "text": "Theory and Practical Outcomes"
        },
        {
          "id": "conclusion",
          "level": 2,
          "text": "Conclusion"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Guide",
      "markdown": "# Tutorial 3: Phase Error Versus Energy Error\n\nPhase error measures whether an oscillation is early or late. Energy error\nmeasures whether the simulated stored electrical energy is too high or too low.\nThey are related in an oscillator, but they are not interchangeable.\n\n![Phase and energy comparison](html/assets/tutorial-03-phase-energy.svg \"Backward Euler and trapezoidal integration show different phase and energy behavior.\")\n\n## What You Will Learn\n\nThe exercise uses an inductor-capacitor (`LC`) tank. An inductor stores magnetic\nenergy and a capacitor stores electric-field energy. In an ideal lossless LC\nmodel, energy moves back and forth between them while the total remains\nconstant.\n\nTwo implicit methods are compared:\n\n- **backward Euler**, which uses the state rate at the end of the timestep and\n  usually adds strong numerical damping; and\n- **trapezoidal integration**, which averages beginning and ending rates and\n  often preserves oscillatory energy much better.\n\nNumerical damping means that the method removes simulated energy even when the\ndeclared model contains no resistor.\n\n## Run the Exercise\n\n```bash\nPYTHONPATH=src python lab/support/verify.py --exercise 03-phase-versus-energy\n```\n\nThe verifier runs ten oscillation periods. A period is the time required for\none complete oscillation.\n\n## Expected Results\n\nFor a lossless linear inductor-capacitor oscillator, backward Euler is expected\nto damp the numerical oscillation because its amplification magnitude is less\nthan one on a purely oscillatory problem. Trapezoidal integration is expected\nto preserve the oscillator's energy much more closely, but its approximate\nrotation angle still permits phase error. The expected qualitative result is\ntherefore strong backward-Euler energy loss, near-roundoff trapezoidal energy\ndrift, and nonzero phase error for both methods.\n\n## Observed Data\n\nThe exercise was run on August 27, 2026 over ten periods.\n\n| Method | Final phase error | Final relative energy error | Relative energy span |\n| --- | ---: | ---: | ---: |\n| Backward Euler | `0.08248810247463056` radians, or about `4.7262` degrees | `0.9805531365134604` | `0.9805531365134604` |\n| Trapezoidal | `0.020658618955850548` radians, or about `1.1837` degrees | `6.352747104407253e-16` | `4.658681209898652e-15` |\n\nA relative error of `0.980553` means that backward Euler lost about 98.1\npercent of the ideal stored energy by the final sample. Trapezoidal integration\nkept energy variation at the scale of floating-point roundoff, but its phase\nstill shifted by about 1.18 degrees. Floating-point roundoff is the small\narithmetic error caused by storing real numbers with a finite number of binary\ndigits. The data therefore demonstrates why phase and energy must remain\nseparate measurements.\n\n## Expected Versus Actual Results\n\nThe actual behavior matches the theoretical expectation. Backward Euler lost\nabout 98.1 percent of the ideal stored energy and accumulated about 4.73 degrees\nof phase error. Trapezoidal integration retained energy to floating-point\nroundoff while accumulating about 1.18 degrees of phase error.\n\nThe important difference from a naive expectation is that near-perfect energy\nretention did not imply perfect timing. Trapezoidal integration maps the ideal\ncontinuous rotation to a discrete rotation with nearly unit magnitude but a\nslightly different angle. That angle error accumulates over repeated periods\neven while energy remains nearly constant.\n\n## Read the Two Measurements Separately\n\nThe final phase error is calculated from the simulated capacitor voltage and\ninductor current, then compared with the known oscillator angle. The relative\nenergy span is the difference between the largest and smallest stored-energy\nvalues divided by the initial energy.\n\nBackward Euler strongly reduces energy in this exercise. Trapezoidal\nintegration keeps the energy span near floating-point roundoff, but its phase\nerror remains nonzero. Floating-point roundoff is the tiny arithmetic error\ncaused by representing real numbers with a finite number of binary digits.\n\nThis distinction matters:\n\n- small energy drift does not prove small timing error;\n- strong damping may make a trace look calm while moving it away from the\n  declared lossless model; and\n- a phase-accurate method could still violate an energy requirement.\n\n## Theory and Practical Outcomes\n\nThe theoretical outcome separates amplification magnitude from phase angle.\nOne controls numerical energy behavior; the other controls oscillation timing.\n\nSeparate phase and energy reporting is important for resonant converters,\nfilters, oscillators, motor-current models, and grid-frequency studies. A\ncontrol design may depend on zero-crossing time even when stored energy looks\nreasonable. A protection study may depend on peak energy even when phase looks\nreasonable.\n\nBAB-CS therefore retains phase and energy as separate evidence channels. It\ndoes not collapse them into one score that hides which engineering property\nchanged.\n\n## Conclusion\n\nThe experiment confirms that phase and energy are independent engineering\nrequirements. Trapezoidal integration is preferable for this ideal energy\nstudy, but its remaining phase error must still be measured when timing,\nzero-crossings, or synchronization matter.\n\n## Claim Boundary\n\nThis exercise uses an ideal lossless LC model. Real inductors and capacitors\nhave resistance, saturation, dielectric loss, temperature effects, and\nfrequency-dependent behavior that are outside this tutorial model.\n",
      "order": 3,
      "path": "tutorials/03_PHASE_VERSUS_ENERGY.md",
      "readingMinutes": 4,
      "sha256": "cbf66ca069c05bd9165f02c4bec993f7f86c26cae8d8e7644af08ab03a11ea49",
      "summary": "Phase error measures whether an oscillation is early or late. Energy error measures whether the simulated stored electrical energy is too high or too low. They are related in an oscillator, but they are not interchangeable.",
      "title": "Tutorial 3: Phase Error Versus Energy Error",
      "wordCount": 768
    },
    {
      "category": "Teaching Lab Tutorials",
      "conceptIds": [
        "babcs",
        "candidate-method",
        "numerical-authority",
        "stiffness",
        "shadow-mode",
        "ulp"
      ],
      "headings": [
        {
          "id": "tutorial-4-shadow-authority",
          "level": 1,
          "text": "Tutorial 4: Shadow Authority"
        },
        {
          "id": "what-you-will-learn",
          "level": 2,
          "text": "What You Will Learn"
        },
        {
          "id": "run-the-exercise",
          "level": 2,
          "text": "Run the Exercise"
        },
        {
          "id": "expected-results",
          "level": 2,
          "text": "Expected Results"
        },
        {
          "id": "observed-data",
          "level": 2,
          "text": "Observed Data"
        },
        {
          "id": "expected-versus-actual-results",
          "level": 2,
          "text": "Expected Versus Actual Results"
        },
        {
          "id": "follow-the-accepted-state",
          "level": 2,
          "text": "Follow the Accepted State"
        },
        {
          "id": "theory-and-practical-outcomes",
          "level": 2,
          "text": "Theory and Practical Outcomes"
        },
        {
          "id": "conclusion",
          "level": 2,
          "text": "Conclusion"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Guide",
      "markdown": "# Tutorial 4: Shadow Authority\n\nShadow authority means that a candidate method runs beside the accepted\nnumerical authority without owning the accepted state. The candidate produces\ndiagnostics, cost, and a proposed trajectory. The independent implicit method\nstill decides the state that the simulation records.\n\n![Shadow authority flow](html/assets/tutorial-04-shadow-authority.svg \"Candidate and implicit paths run in parallel while only the implicit path owns the accepted state.\")\n\n## What You Will Learn\n\nBAB-CS has three rollout modes:\n\n- **disabled mode** does not execute the candidate and accepts the implicit\n  reference result;\n- **shadow mode** executes the candidate for observation but still accepts the\n  implicit reference result; and\n- **active mode** may accept a bounded candidate result after correction and\n  independent gates pass.\n\nA candidate method is the numerical formula being studied. Numerical authority\nis the independent calculation and rule set that owns acceptance.\n\n## Run the Exercise\n\n```bash\nPYTHONPATH=src python lab/support/verify.py --exercise 04-shadow-authority\n```\n\nThe verifier runs one resistor-capacitor (`RC`) circuit in all three modes.\n\n## Expected Results\n\nDisabled and shadow modes should accept the same implicit trajectory because\nthe candidate is observational only in shadow mode. Their accepted states are\nexpected to differ by no more than ordinary solver roundoff. Shadow mode should\nstill record candidate steps and independent reference solves. Active mode is\nexpected to report bounded candidate authority when its correction and gates\npermit candidate promotion.\n\n## Observed Data\n\nThe exercise was run on August 27, 2026.\n\n| Measurement | Observed value |\n| --- | --- |\n| Disabled-mode accepted authority | implicit method |\n| Shadow-mode accepted authority | implicit method |\n| Active-mode accepted authority | bounded candidate path |\n| Candidate steps observed in shadow mode | `19` |\n| Candidate steps used in active mode | `19` |\n| Independent reference solves in shadow mode | `20` |\n| Maximum shadow-versus-disabled state difference | `1.3877787807814457e-17` |\n| Recorded 16-unit-in-the-last-place (`ULP`) tolerance | `3.552713678800501e-15` |\n| Shadow match within solver roundoff | `true` |\n\nThe maximum state difference was only `0.00390625` of the allowed tolerance,\nwhich is 256 times smaller than the gate. Candidate diagnostics were still\ngenerated for 19 steps, but the shadow candidate did not gain authority over\nthe accepted state.\n\n## Expected Versus Actual Results\n\nAll authority assignments matched the expectation. The shadow and disabled\nstates were not bit-for-bit identical, but their maximum difference was\n`1.3877787807814457e-17`, far below the\n`3.552713678800501e-15` tolerance. That nonzero difference is consistent with\nminor changes in floating-point evaluation or nonlinear-solve ordering and is\nnot evidence that the shadow candidate altered acceptance.\n\n## Follow the Accepted State\n\nShadow mode is designed for safe observation. It can answer questions such as:\n\n- How often would the candidate have been used?\n- How expensive is the candidate?\n- How large is its defect against the reference?\n- Where does it encounter stiffness or nonlinear difficulty?\n\nStiffness means that fast and slow behavior occur together, forcing some\nmethods to take very small steps for stability.\n\nThe verifier requires the shadow time grid to match disabled mode exactly. It\nalso compares every accepted state component using a 16-unit-in-the-last-place\ngate. A unit in the last place (`ULP`) is the spacing between neighboring\nfloating-point numbers near a value. The gate allows ordinary solver roundoff\nwithout allowing the candidate to alter the accepted trajectory.\n\nCandidate diagnostics must still be present. Otherwise the run would merely be\ndisabled mode with a different label.\n\n## Theory and Practical Outcomes\n\nThe theoretical outcome is separation of observation from authority. A method\ncan be measured without allowing its proposal to modify the accepted state.\n\nShadow operation is useful before enabling a new numerical method in a\nqualification or production workflow. Engineers can collect method-specific\nevidence on real workloads while preserving the established accepted-state\nauthority. The same pattern is useful for comparing sparse solvers, nonlinear\nstrategies, or alternative error estimators.\n\n## Conclusion\n\nThe experiment met the expected authority-separation result. Shadow mode\nprovides a practical migration path for collecting candidate evidence under\nreal workloads before active acceptance is considered.\n\n## Claim Boundary\n\nShadow agreement proves that the accepted state remained under the implicit\nauthority for the measured case. It does not prove that the candidate would be\nsafe in active mode, because active acceptance introduces additional\ncorrection, bounds, gates, and fallback behavior.\n",
      "order": 4,
      "path": "tutorials/04_SHADOW_AUTHORITY.md",
      "readingMinutes": 4,
      "sha256": "eabc5060e7fb733f79b49ea375c6c3184dd779ddc9cd4f58c72a3f44e211ad88",
      "summary": "Shadow authority means that a candidate method runs beside the accepted numerical authority without owning the accepted state. The candidate produces diagnostics, cost, and a proposed trajectory. The independent implicit method still…",
      "title": "Tutorial 4: Shadow Authority",
      "wordCount": 668
    },
    {
      "category": "Teaching Lab Tutorials",
      "conceptIds": [
        "deterministic-evidence",
        "python-wheel",
        "sha256",
        "zip",
        "os"
      ],
      "headings": [
        {
          "id": "tutorial-5-deterministic-packaging",
          "level": 1,
          "text": "Tutorial 5: Deterministic Packaging"
        },
        {
          "id": "what-you-will-learn",
          "level": 2,
          "text": "What You Will Learn"
        },
        {
          "id": "run-the-exercise",
          "level": 2,
          "text": "Run the Exercise"
        },
        {
          "id": "expected-results",
          "level": 2,
          "text": "Expected Results"
        },
        {
          "id": "observed-data",
          "level": 2,
          "text": "Observed Data"
        },
        {
          "id": "expected-versus-actual-results",
          "level": 2,
          "text": "Expected Versus Actual Results"
        },
        {
          "id": "understand-the-build-contract",
          "level": 2,
          "text": "Understand the Build Contract"
        },
        {
          "id": "theory-and-practical-outcomes",
          "level": 2,
          "text": "Theory and Practical Outcomes"
        },
        {
          "id": "conclusion",
          "level": 2,
          "text": "Conclusion"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Guide",
      "markdown": "# Tutorial 5: Deterministic Packaging\n\nDeterministic packaging means that two builds from the same declared source\nstate produce exactly the same installable package bytes. The Python package\nformat used here is a wheel: a ZIP-based archive containing modules and package\nmetadata.\n\n![Deterministic packaging flow](html/assets/tutorial-05-deterministic-packaging.svg \"Two independent wheel builds from one frozen source are compared byte-for-byte.\")\n\n## What You Will Learn\n\nReproducible numerical evidence can be weakened if the distributed package is\nnot reproducible. A package might accidentally include a stale file, omit a\nmodule, reorder archive members, preserve local timestamps, or change file\npermissions.\n\nThe exercise checks:\n\n- fixed archive timestamps;\n- fixed file permissions;\n- deterministic member order;\n- the declared wheel filename; and\n- byte-identical Secure Hash Algorithm 256-bit (`SHA-256`) fingerprints.\n\nSHA-256 is a cryptographic fingerprint. If two package files have the same\nSHA-256 value, they are treated as the same exact byte sequence for this\nevidence workflow.\n\n## Run the Exercise\n\nFrom a clean source tree:\n\n```bash\nPYTHONPATH=src python lab/support/verify.py --exercise 05-deterministic-packaging\n```\n\nFor an explicitly non-release experiment in a dirty tree:\n\n```bash\nPYTHONPATH=src python lab/support/verify.py \\\n  --exercise 05-deterministic-packaging \\\n  --development\n```\n\nDevelopment mode records that the result is not release evidence.\n\n## Expected Results\n\nIf timestamps, permissions, member ordering, package metadata, and included\nfiles are deterministic, two independent builds from the same source should\nhave identical bytes and therefore identical SHA-256 fingerprints. Because the\nworking tree is dirty and development mode is explicit, the expected release\nevidence flag is `false` even if the wheel bytes match.\n\n## Observed Data\n\nThe development-mode command was run on August 27, 2026 because the repository\ncontained uncommitted work.\n\n| Measurement | Observed value |\n| --- | --- |\n| Wheel filename | `bab_cs-1.1.0-py3-none-any.whl` |\n| Archive members | `19` |\n| Fixed timestamps | `true` |\n| Fixed permissions | `true` |\n| Member order matches the build-backend contract | `true` |\n| First wheel SHA-256 | `ca5d648e60dfd9923deadc85fb304b45dc9ecf87aecc982a369d3766542806f2` |\n| Second wheel SHA-256 | `ca5d648e60dfd9923deadc85fb304b45dc9ecf87aecc982a369d3766542806f2` |\n| Wheel hashes match | `true` |\n| Release evidence | `false` |\n\nThe two complete 64-character fingerprints are identical, so the two measured\nwheel files were byte-for-byte identical. The `release evidence` field remains\nfalse because development mode permits a dirty source tree. Deterministic bytes\ndo not override the clean-source and human-approval release gates.\n\n## Expected Versus Actual Results\n\nThe two wheel fingerprints matched exactly, and every archive-control check\nreturned `true`. The result therefore met the deterministic-build expectation.\nThe release flag also matched the expected `false` value.\n\nA common but incorrect expectation is that reproducible bytes automatically\nmake a package releasable. The actual result demonstrates why that is false:\nbyte identity answers a packaging question, while release qualification also\nrequires a clean exact source commit, complete evidence, and human approval.\n\n## Understand the Build Contract\n\nThe verifier builds the wheel twice into different directories. It compares the\ncomplete byte sequences and then inspects the archives. Sorting members alone\nis not enough: timestamps, permissions, generated metadata, and version fields\nmust also be controlled.\n\nThe reviewed build backend defines the authoritative member order. A test that\nmerely compares extracted source text would miss archive-level differences.\n\n## Theory and Practical Outcomes\n\nThe theoretical outcome follows from hashing: identical byte sequences produce\nthe same SHA-256 fingerprint. The practical outcome depends on controlling\nevery source of archive variation rather than only the Python module text.\n\nDeterministic packaging supports regulated review, long-lived research\nartifacts, exact rollback, and independent reproduction. A reviewer can tie a\npublished wheel fingerprint to the exact source and evidence that were\napproved.\n\n## Conclusion\n\nThe development wheel is reproducible under the measured build environment.\nThis supports repeatable installation and rollback, but the result deliberately\nremains development evidence rather than release evidence.\n\n## Claim Boundary\n\nMatching wheel hashes prove byte identity for the two measured builds. They do\nnot prove numerical correctness, security, release approval, or reproducibility\non every operating system and Python version.\n",
      "order": 5,
      "path": "tutorials/05_DETERMINISTIC_PACKAGING.md",
      "readingMinutes": 3,
      "sha256": "3b32ea408caac1019fb8fbaf51afb570e6145c6e2038b7860faf6951978c6fe4",
      "summary": "Deterministic packaging means that two builds from the same declared source state produce exactly the same installable package bytes. The Python package format used here is a wheel: a ZIP-based archive containing modules and package…",
      "title": "Tutorial 5: Deterministic Packaging",
      "wordCount": 609
    },
    {
      "category": "Teaching Lab Tutorials",
      "conceptIds": [
        "candidate-method",
        "reduced-order-model",
        "deterministic-evidence",
        "fixed-step",
        "fixed-accuracy",
        "fixed-work",
        "source-wheel-equivalence",
        "python-wheel",
        "rc",
        "rl",
        "rlc",
        "dc",
        "json",
        "csv",
        "sha256",
        "os"
      ],
      "headings": [
        {
          "id": "tutorial-6-source-versus-installed-wheel-equivalence",
          "level": 1,
          "text": "Tutorial 6: Source Versus Installed-Wheel Equivalence"
        },
        {
          "id": "what-you-will-learn",
          "level": 2,
          "text": "What You Will Learn"
        },
        {
          "id": "run-the-exercise",
          "level": 2,
          "text": "Run the Exercise"
        },
        {
          "id": "expected-results",
          "level": 2,
          "text": "Expected Results"
        },
        {
          "id": "observed-data",
          "level": 2,
          "text": "Observed Data"
        },
        {
          "id": "expected-versus-actual-results",
          "level": 2,
          "text": "Expected Versus Actual Results"
        },
        {
          "id": "why-isolation-is-necessary",
          "level": 2,
          "text": "Why Isolation Is Necessary"
        },
        {
          "id": "read-the-evidence",
          "level": 2,
          "text": "Read the Evidence"
        },
        {
          "id": "theory-and-practical-outcomes",
          "level": 2,
          "text": "Theory and Practical Outcomes"
        },
        {
          "id": "conclusion",
          "level": 2,
          "text": "Conclusion"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Guide",
      "markdown": "# Tutorial 6: Source Versus Installed-Wheel Equivalence\n\nSource-versus-wheel equivalence asks whether the repository code and the\ninstalled package produce the same declared numerical artifacts. The wheel is\nthe installable Python package produced in Tutorial 5.\n\n![Source and installed-wheel equivalence](html/assets/tutorial-06-source-wheel-equivalence.svg \"Source, isolated module, and installed console paths must reproduce the same selected artifacts.\")\n\n## What You Will Learn\n\nThree execution paths are compared:\n\n1. the package imported directly from the repository source tree;\n2. the package imported from an isolated installed wheel; and\n3. the installed `babcs` console command.\n\nA console command is the user-facing command-line entry point. The command-line\ninterface (`CLI`) is the text-based interface used to invoke it. The application\nprogramming interface (`API`) is the Python interface imported by code.\n\n## Run the Exercise\n\nFrom a clean source tree:\n\n```bash\nPYTHONPATH=src python lab/support/verify.py --exercise 06-source-wheel-equivalence\n```\n\nThe exercise builds the wheel if Tutorial 5 has not already done so. It creates\nan isolated virtual environment, removes `PYTHONPATH`, and runs outside the\nrepository. A virtual environment is a separate Python installation directory\nused to prevent imports from leaking in from the development tree.\n\nFor an explicitly non-release experiment in a dirty tree, add `--development`:\n\n```bash\nPYTHONPATH=src python lab/support/verify.py \\\n  --exercise 06-source-wheel-equivalence \\\n  --development\n```\n\n## Expected Results\n\nThe source module, isolated installed module, and installed console command are\nexpected to produce byte-identical waveform and summary artifacts for every\nselected deterministic case. The imported module path should resolve inside\nthe isolated virtual environment, and the quick Method Observatory report\nshould also match. Development mode is expected to mark the result as\nnon-release evidence.\n\n## Observed Data\n\nThe development-mode command was run on August 27, 2026. Secure Hash Algorithm\n256-bit (`SHA-256`) values identify the exact compared output bytes. The case\nnames use resistor-capacitor (`RC`), resistor-inductor (`RL`), and\nresistor-inductor-capacitor (`RLC`) to name their component families.\n`summary.json` is a JavaScript Object Notation (`JSON`) summary file, and\n`trace.csv` is a comma-separated values (`CSV`) waveform table.\n\n| Case | `summary.json` SHA-256 | `trace.csv` SHA-256 | All three paths match |\n| --- | --- | --- | --- |\n| RC step | `117e0894bbf6de91245c9194e6d5041a0c3aae08587361d89ca43fe35f643721` | `8be378115e723467d723077c83b500c247277eb5bb266d22764e5bd4b5b7c8fe` | `true` |\n| Switched RC | `2c40ae734a64d44688ff53969579d3132909819f0d27d29afce803e2f4e725db` | `8481e2c2c90f0498d4b2495988108a01d95d85d391d8e3f84122bc1939f41679` | `true` |\n| Buck-like reduced order | `75623566cec8bc832da44f3881e7369b5fb23f9bd0723de0a3e5d224f9c5f88c` | `3a01ac1cf5df963883a04af2f90cf97bc02b28abd4f0d4520422efa9bde48221` | `true` |\n| H-bridge RL reduced order | `e2bb0ec5ca71ceb79ca6266bf1f7cb870c2f238d1c53d1909863f32479914300` | `fbbe47484d4228515896e188dff40a70421224e01287d6c96837a69dc1ff29ae` | `true` |\n| DC-link RLC reduced order | `cc05c2ed46bb3f959425095e0c403e221531dcc1ab7d5011029073c3949016e1` | `c1497960280b0fbf1b8a81c3397c11b51546f96c66e4f692cba47023fce04a5d` | `true` |\n\nThe quick Method Observatory report also matched byte-for-byte. The Method\nObservatory is the deterministic matrix that compares numerical methods under\ndeclared work and accuracy controls. Its complete report hash is intentionally\nnot copied into this tutorial because the report records source provenance, so\nediting this tutorial correctly changes that hash. The command output remains\nthe authoritative value for the exact source state being checked.\n\nThe installed module path resolved to\n`<isolated-venv>/lib/python3.14/site-packages/babcs/__init__.py`, and the verifier\nreported `source_tree_excluded: true`. These values show that the installed\nmodule and console did not silently import the repository copy.\n\n## Expected Versus Actual Results\n\nAll five selected simulations and the Method Observatory smoke report matched\nbyte-for-byte, so the behavioral expectation was met. The isolated path also\nconfirmed that the installed package, rather than the repository source, was\nexecuted.\n\nOne result differs from a naive expectation: the complete Observatory report\nhash is not stable after an unrelated source-provenance change. That behavior is\nintentional because the report records which source state produced it. The\nscientifically stable claim is that source and installed reports match for the\nsame source state, not that one provenance-bearing report hash remains constant\nafter the repository changes.\n\n## Why Isolation Is Necessary\n\nRunning an installed package while the current directory is the repository can\naccidentally import the source tree. That produces a false equivalence result:\nthe command appears to test the wheel but actually runs the development files.\n\nThe verifier therefore checks the imported module path and requires it to live\ninside the isolated environment. It then compares trace files and summary files\nbyte-for-byte.\n\nThe selected cases include a resistor-capacitor (`RC`) transient, a switched RC\ntransient, and three reduced-order power-stage experiments. Reduced order means\nthat the model intentionally keeps only the behavior needed for the stated\nnumerical question.\n\nThe quick Method Observatory smoke is also compared. The Method Observatory is\nthe deterministic matrix that runs candidate methods under fixed-step,\nfixed-accuracy, and fixed-work views.\n\n## Read the Evidence\n\nThe verifier reports whether every selected artifact matches and whether the\nsource tree was excluded. Environment-specific temporary paths are normalized\nto a stable placeholder before evidence is compared.\n\nNormalization is allowed only for declared provenance fields. Numerical values,\naccepted time grids, method diagnostics, and output ordering must not be\nsilently normalized.\n\n## Theory and Practical Outcomes\n\nThe theoretical outcome is observational equivalence across three delivery\npaths under fixed inputs. The practical test closes two common loopholes:\naccidentally importing the source tree and testing only one entry point.\n\nThis exercise detects packaging omissions, import-path leaks, console-option\ndrift, and source-versus-distribution behavior changes. It is valuable before a\nrelease candidate is reviewed or an experiment is shared with another team.\n\n## Conclusion\n\nThe selected source, installed module, and installed console paths were\nequivalent for the measured artifacts. This supports distribution confidence\nfor the declared cases while preserving a separate release-qualification gate.\n\n## Claim Boundary\n\nThe result proves equivalence for the selected deterministic cases and the\nmeasured package. It does not prove equivalence for every optional sparse\nbackend, Python version, operating system, or user configuration.\n",
      "order": 6,
      "path": "tutorials/06_SOURCE_WHEEL_EQUIVALENCE.md",
      "readingMinutes": 4,
      "sha256": "5ca9200e5dd26477fc29956de699191058584b3dee452329136feae1e80a99e1",
      "summary": "Source-versus-wheel equivalence asks whether the repository code and the installed package produce the same declared numerical artifacts. The wheel is the installable Python package produced in Tutorial 5.",
      "title": "Tutorial 6: Source Versus Installed-Wheel Equivalence",
      "wordCount": 871
    },
    {
      "category": "Teaching Lab Tutorials",
      "conceptIds": [
        "babcs",
        "adams-bashforth"
      ],
      "headings": [
        {
          "id": "tutorial-7-exact-event-alignment",
          "level": 1,
          "text": "Tutorial 7: Exact Event Alignment"
        },
        {
          "id": "what-you-will-learn",
          "level": 2,
          "text": "What You Will Learn"
        },
        {
          "id": "run-the-exercise",
          "level": 2,
          "text": "Run the Exercise"
        },
        {
          "id": "expected-results",
          "level": 2,
          "text": "Expected Results"
        },
        {
          "id": "observed-data",
          "level": 2,
          "text": "Observed Data"
        },
        {
          "id": "expected-versus-actual-results",
          "level": 2,
          "text": "Expected Versus Actual Results"
        },
        {
          "id": "follow-one-event",
          "level": 2,
          "text": "Follow One Event"
        },
        {
          "id": "why-interpolation-is-not-enough",
          "level": 2,
          "text": "Why Interpolation Is Not Enough"
        },
        {
          "id": "read-the-evidence",
          "level": 2,
          "text": "Read the Evidence"
        },
        {
          "id": "theory-and-practical-outcomes",
          "level": 2,
          "text": "Theory and Practical Outcomes"
        },
        {
          "id": "conclusion",
          "level": 2,
          "text": "Conclusion"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Guide",
      "markdown": "# Tutorial 7: Exact Event Alignment\n\nAn event is a declared time at which a source, switch, or other scheduled input\nchanges its behavior. Event alignment means that the simulator lands exactly on\nthat time rather than stepping past it and treating the change as if it occurred\nsomewhere inside a long timestep.\n\n![Exact event alignment timeline](html/assets/tutorial-07-event-alignment.svg \"Five switch events are reached exactly and followed by multistep startup behavior.\")\n\n## What You Will Learn\n\nThe exercise uses a scheduled switched resistor-capacitor (`RC`) circuit. The\nswitch control is a pulse waveform: a repeating low and high schedule with\ndeclared transition times.\n\nAdams-Bashforth is a multistep method. A multistep method uses information from\nearlier accepted steps to propose the next state. That history becomes invalid\nwhen a switch changes the circuit equations.\n\n## Run the Exercise\n\n```bash\nPYTHONPATH=src python lab/support/verify.py --exercise 07-event-alignment\n```\n\nThe nominal timestep is deliberately chosen so that ordinary steps do not land\nnaturally on every scheduled transition. The simulator must shorten a step when\nnecessary.\n\n## Expected Results\n\nThe pulse schedule contains five transitions within the simulated interval.\nThe simulator is expected to accept a point at every declared transition,\nrecord five event history resets, and restart the multistep method after the\nfirst four events. The fifth event coincides with the stop time, so no startup\nstep is expected after it.\n\n## Observed Data\n\nThe exercise was run on August 27, 2026.\n\n| Event | Scheduled time | Accepted boundary time | Exact match |\n| ---: | ---: | ---: | --- |\n| 1 | `0.0001` seconds | `0.0001` seconds | `true` |\n| 2 | `0.0002` seconds | `0.0002` seconds | `true` |\n| 3 | `0.0005` seconds | `0.0005` seconds | `true` |\n| 4 | `0.0006000000000000001` seconds | `0.0006000000000000001` seconds | `true` |\n| 5 | `0.0009000000000000001` seconds | `0.0009000000000000001` seconds | `true` |\n\nThe report recorded five event history resets and four startup steps after\nevents. The fifth event is the stop time, so the simulation ends there and does\nnot need another startup step.\n\n## Expected Versus Actual Results\n\nThe event count, accepted times, history-reset count, and startup count matched\nthe expectation exactly. The displayed values\n`0.0006000000000000001` and `0.0009000000000000001` differ from the shorter\nhuman decimal forms `0.0006` and `0.0009` only because those decimals do not have\nexact finite binary floating-point representations. Scheduled and accepted\nvalues use the same representation and therefore still match exactly under the\ndeclared comparison.\n\n## Follow One Event\n\nAt each switch transition, BAB-CS performs this sequence:\n\n1. identify the next breakpoint, meaning the next declared event time;\n2. shorten the proposed step so its endpoint equals the event;\n3. solve and accept the event-boundary state under the declared authority;\n4. record `history_reset_reason = event`; and\n5. take a startup step before using multistep history again.\n\nThe verifier compares the scheduled and accepted event lists to an absolute\ntolerance of one femtosecond. A femtosecond is `10^-15` seconds. The tight gate\nis appropriate because these event times are declared inputs, not measured\nphysical events with uncertainty.\n\n## Why Interpolation Is Not Enough\n\nIf a step crosses a switch event, the differential equations used before and\nafter the transition are different. Interpolating a state backward from the end\nof the step does not undo the fact that the wrong equations were integrated\nover part of the interval.\n\nExact alignment is therefore both a numerical and an engineering requirement.\nIt supports repeatable switching loss studies, dead-time studies, protection\nlogic experiments, and controller schedule screening.\n\n## Read the Evidence\n\nThe exercise reports five scheduled events, five accepted event boundaries,\nfive history resets, and four post-event startup steps. The last event is also\nthe simulation stop time, so no step follows it.\n\n## Theory and Practical Outcomes\n\nThe theoretical requirement is piecewise integration: each smooth interval is\nintegrated under one circuit configuration, and the step ends before the\nconfiguration changes. The practical outcome is a reproducible event boundary\nthat supports switching schedules, dead-time experiments, and controller\ntiming studies without hiding a transition inside a longer step.\n\n## Conclusion\n\nThe experiment met every event-alignment expectation. It demonstrates that\nscheduled changes are treated as integration boundaries and that invalid\nmultistep history is discarded immediately after each change.\n\n## Claim Boundary\n\nExact schedule alignment proves timing consistency for the declared ideal\nswitch model. It does not model contact bounce, semiconductor transition\ndynamics, propagation delay, thermal behavior, or uncertain hardware timing.\n",
      "order": 7,
      "path": "tutorials/07_EVENT_ALIGNMENT.md",
      "readingMinutes": 4,
      "sha256": "103f6d87c0572c1b1704a903b6ca03accb26fe9d7ae0e6114fc27e626262cc1e",
      "summary": "An event is a declared time at which a source, switch, or other scheduled input changes its behavior. Event alignment means that the simulator lands exactly on that time rather than stepping past it and treating the change as if it…",
      "title": "Tutorial 7: Exact Event Alignment",
      "wordCount": 704
    },
    {
      "category": "Teaching Lab Tutorials",
      "conceptIds": [
        "babcs",
        "replay",
        "anchor",
        "recursive-bound",
        "empirical-coverage",
        "rc"
      ],
      "headings": [
        {
          "id": "tutorial-8-empirical-bound-coverage",
          "level": 1,
          "text": "Tutorial 8: Empirical Bound Coverage"
        },
        {
          "id": "what-you-will-learn",
          "level": 2,
          "text": "What You Will Learn"
        },
        {
          "id": "run-the-exercise",
          "level": 2,
          "text": "Run the Exercise"
        },
        {
          "id": "expected-results",
          "level": 2,
          "text": "Expected Results"
        },
        {
          "id": "observed-data",
          "level": 2,
          "text": "Observed Data"
        },
        {
          "id": "expected-versus-actual-results",
          "level": 2,
          "text": "Expected Versus Actual Results"
        },
        {
          "id": "understand-eligibility",
          "level": 2,
          "text": "Understand Eligibility"
        },
        {
          "id": "interpret-the-result-honestly",
          "level": 2,
          "text": "Interpret the Result Honestly"
        },
        {
          "id": "theory-and-practical-outcomes",
          "level": 2,
          "text": "Theory and Practical Outcomes"
        },
        {
          "id": "conclusion",
          "level": 2,
          "text": "Conclusion"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Guide",
      "markdown": "# Tutorial 8: Empirical Bound Coverage\n\nThe recursive internal bound is BAB-CS's running estimate of how modeled\nnumerical error can accumulate between trusted anchors. Empirical coverage asks\nhow often an independently measured authority-epoch drift error is less than or\nequal to that bound.\n\n![Empirical bound coverage](html/assets/tutorial-08-bound-coverage.svg \"The measured authority-epoch drift error exceeds the recursive internal bound on the eligible tutorial samples.\")\n\n## What You Will Learn\n\nAn anchor is a retained accepted state from which an independent replay can\nstart. An authority epoch is the interval since the current anchor. Drift error\nwithin the epoch compares two changes:\n\n- how far the accepted candidate state moved from the anchor; and\n- how far the independent authority moved from its corresponding anchor.\n\nThis subtraction matters because the recursive bound describes accumulated\ndrift from the current anchor, not necessarily total error from time zero.\n\n## Run the Exercise\n\n```bash\nPYTHONPATH=src python lab/support/verify.py --exercise 08-bound-coverage\n```\n\nThe tutorial uses a resistor-capacitor (`RC`) case with an analytic authority.\nThe state difference is scaled with the same absolute and relative tolerances\nused by BAB-CS.\n\n## Expected Results\n\nAn optimistic expectation for a conservative recursive bound is that it covers\nmost or all eligible authority-epoch drift samples. The stricter scientific\nexpectation is only that the measurement reports coverage honestly and does not\nturn empirical evidence into a formal proof. The exercise therefore tests both\nthe numerical coverage ratio and the integrity of the claim boundary.\n\n## Observed Data\n\nThe exercise was run on August 27, 2026.\n\n| Measurement | Observed value |\n| --- | ---: |\n| Eligible samples | `17` |\n| Covered samples | `0` |\n| Empirical coverage ratio | `0.0` |\n| Maximum authority-epoch drift error | `11512.211750693821` |\n| Maximum recursive internal bound | `642.995485991595` |\n| Formal enclosure claimed | `false` |\n\nAt the largest recorded values, the measured drift error was about\n`17.904031990116184` times the internal bound. Coverage was therefore zero, not\nbecause the run lacked eligible samples, but because none of the 17 measured\nsamples satisfied the coverage inequality. The values are scaled error units,\nnot volts or amperes, because absolute and relative tolerances normalize each\nstate component before comparison.\n\n## Expected Versus Actual Results\n\nThe optimistic coverage expectation was not met: zero of 17 eligible samples\nwere covered, and the maximum measured drift was about 17.9 times the maximum\nrecursive bound. The reporting expectation was met because the verifier\nretained the zero ratio and explicitly set the formal-enclosure claim to\n`false`.\n\nThe current experiment does not isolate one proven cause for the shortfall.\nPlausible contributors include incomplete local-to-global error propagation,\nanchor-epoch scaling, omitted error sources, or a configuration whose bound\nparameters are too small for the measured drift. These are hypotheses for\ncontrolled follow-up experiments, not conclusions established by this one\nratio.\n\n## Understand Eligibility\n\nNot every accepted point is an ordinary coverage sample. The verifier excludes:\n\n- the initial state;\n- an event boundary, because the governing schedule changes there; and\n- a re-anchor point, because the authority epoch is reset there.\n\nFor each remaining point, the verifier records whether:\n\n```text\nauthority-epoch drift error <= recursive internal bound\n```\n\nThe empirical coverage ratio is the number of covered samples divided by the\nnumber of eligible samples.\n\n## Interpret the Result Honestly\n\nIn the reviewed fixture, none of the 17 eligible samples are covered. This is\nnot hidden or converted into a favorable score. It is evidence that the current\nrecursive model, configuration, and scaling do not enclose the independently\nmeasured epoch drift for this tutorial run.\n\nThat result is useful. It identifies a concrete research direction: improve the\nbound model, change the configuration, narrow the applicability claim, or use a\ndifferent authority strategy.\n\nEmpirical means observed in experiments. A formal enclosure proof would require\na mathematical argument that covers every allowed state and step under stated\nassumptions. A measured ratio—even 100 percent—cannot become that proof by\nitself.\n\n## Theory and Practical Outcomes\n\nThe theoretical distinction is between an internal modeled bound and an\nindependently observed error. Coverage measures their relationship; it does not\nguarantee enclosure outside the measured samples.\n\nCoverage analysis helps determine whether a numerical bound is conservative\nenough for a declared operating region. Grouping results by anchor age,\ncircuit class, method, or rejection cause can show where the internal model is\nstrong and where it needs refinement.\n\n## Conclusion\n\nThis is the only tutorial in which the optimistic numerical expectation failed.\nThe practical outcome is still valuable: the recursive bound must remain a\ndiagnostic quantity for this configuration, and improving or narrowing the\nbound model is a clearly identified research task.\n\n## Claim Boundary\n\nThis tutorial reports measured coverage for one RC run. It makes no formal\nenclosure claim and no statement about unknown physical-model error.\n",
      "order": 8,
      "path": "tutorials/08_EMPIRICAL_BOUND_COVERAGE.md",
      "readingMinutes": 4,
      "sha256": "2e91a7931e3c2d883f248275b59c4f1300506b5824c0da80b028e1a56f10c677",
      "summary": "The recursive internal bound is BAB-CS's running estimate of how modeled numerical error can accumulate between trusted anchors. Empirical coverage asks how often an independently measured authority-epoch drift error is less than or…",
      "title": "Tutorial 8: Empirical Bound Coverage",
      "wordCount": 763
    },
    {
      "category": "Teaching Lab Tutorials",
      "conceptIds": [
        "babcs",
        "candidate-method",
        "newton-iteration",
        "nonlinear-convergence",
        "reduced-order-model",
        "fail-closed",
        "rl"
      ],
      "headings": [
        {
          "id": "tutorial-9-fallback-and-rejection-forensics",
          "level": 1,
          "text": "Tutorial 9: Fallback and Rejection Forensics"
        },
        {
          "id": "what-you-will-learn",
          "level": 2,
          "text": "What You Will Learn"
        },
        {
          "id": "run-the-exercise",
          "level": 2,
          "text": "Run the Exercise"
        },
        {
          "id": "expected-results",
          "level": 2,
          "text": "Expected Results"
        },
        {
          "id": "observed-data",
          "level": 2,
          "text": "Observed Data"
        },
        {
          "id": "expected-versus-actual-results",
          "level": 2,
          "text": "Expected Versus Actual Results"
        },
        {
          "id": "separate-the-evidence-channels",
          "level": 2,
          "text": "Separate the Evidence Channels"
        },
        {
          "id": "why-rejected-work-must-stay-visible",
          "level": 2,
          "text": "Why Rejected Work Must Stay Visible"
        },
        {
          "id": "theory-and-practical-outcomes",
          "level": 2,
          "text": "Theory and Practical Outcomes"
        },
        {
          "id": "conclusion",
          "level": 2,
          "text": "Conclusion"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Guide",
      "markdown": "# Tutorial 9: Fallback and Rejection Forensics\n\nA rejection means that one proposed step did not satisfy the declared rules. A\nfallback means that BAB-CS transferred the step to an implicit authority rather\nthan accepting the candidate proposal. Neither event automatically means that\nthe complete simulation failed.\n\n![Fallback and rejection forensics](html/assets/tutorial-09-fallback-forensics.svg \"Rejected work, implicit fallbacks, event resets, and periodic reanchors remain separately visible.\")\n\n## What You Will Learn\n\nThe exercise uses the scheduled H-bridge resistor-inductor (`RL`) load. An\nH-bridge is a four-switch arrangement that can apply either voltage polarity to\na load. The example is a reduced-order numerical experiment: it represents\nscheduled resistive switches and an RL load without claiming transistor,\ndead-time, thermal, protection, or electromagnetic device fidelity.\n\n## Run the Exercise\n\n```bash\nPYTHONPATH=src python lab/support/verify.py --exercise 09-fallback-forensics\n```\n\n## Expected Results\n\nThe scheduled reduced-order H-bridge contains discontinuous switch changes and\nis expected to challenge the candidate method. Some rejected attempts,\nfallbacks, event resets, and periodic reanchors are therefore expected. The\ncomplete simulation is still expected to reach `0.0004` seconds, and every\nrejection should retain a stable cause rather than disappear from the work\nrecord.\n\n## Observed Data\n\nThe exercise was run on August 27, 2026.\n\n| Evidence channel | Observed count or value |\n| --- | ---: |\n| Rejected candidate steps | `9` |\n| Implicit fallbacks | `8` |\n| Event history resets | `8` |\n| Periodic reanchors | `12` |\n| Embedded-candidate-cap rejections | `8` |\n| Reference-solve failures | `1` |\n| Accepted stop time | `0.0004` seconds |\n| Reduced-order numerical experiment | `true` |\n| Production device claim | `false` |\n\nEight of the nine rejected attempts were associated with the embedded\ncandidate cap, and one was associated with a reference-solve failure. The run\nstill reached its declared stop time because controlled retries and eight\nimplicit fallbacks supplied accepted states where candidate proposals could not\nbe promoted.\n\n## Expected Versus Actual Results\n\nThe run matched the qualitative expectation and reached the stop time. It\nrecorded nine rejected attempts but eight implicit fallbacks. These counts are\nnot expected to be equal because a rejected attempt is not an accepted step: a\nsmaller retry can succeed, and one accepted state can follow several attempts.\nThe evidence attributes eight rejections to the embedded candidate cap and one\nto a reference-solve failure.\n\nThe actual counts show that candidate difficulty dominated this run, while the\nindependent reference encountered one failed attempt. The data does not prove\nthat the same proportions will occur under another schedule, timestep, device\nmodel, or solver configuration.\n\n## Separate the Evidence Channels\n\nThe reviewed run records:\n\n- rejected candidate steps;\n- implicit fallbacks;\n- exact event resets;\n- periodic reanchors;\n- candidate-cap causes; and\n- a reference-solve cause.\n\nThe embedded candidate cap is a limit on the candidate method's own local error\nestimate. When that estimate is too large, BAB-CS can reduce the step, retry, or\ntransfer authority.\n\nA reference-solve failure is different. It means the independent implicit solve\ndid not meet its nonlinear convergence contract at the attempted time and\nstep. Nonlinear convergence means that repeated Newton iterations reduced the\ncircuit-equation mismatch and update size below declared tolerances.\n\n## Why Rejected Work Must Stay Visible\n\nCounting only accepted steps makes a difficult method look cheaper than it was.\nRejected attempts still used circuit evaluations, linear solves, and nonlinear\niterations. They also identify operating regions that challenge the candidate\nor authority.\n\nBAB-CS retains causes instead of reducing everything to a generic “solver\nfailed” message. Engineering teams can then distinguish:\n\n- candidate instability;\n- nonlinear device difficulty;\n- event-related restart;\n- overly strict gates;\n- minimum-step exhaustion; and\n- authority nonconvergence.\n\n## Theory and Practical Outcomes\n\nThe theoretical outcome is fail-closed authority transfer: a rejected proposal\ndoes not become accepted merely because work has already been spent on it. The\npractical outcome is an auditable cost and failure record.\n\nForensics are useful when selecting a method for converter schedules, load\ninterruption, fault studies, or controller testing. A method with a low accepted\nstep count may still perform poorly if it creates many expensive retries.\n\n## Conclusion\n\nThe reduced-order H-bridge completed successfully through controlled retries\nand fallback. The experiment confirms that rejected work and its causes remain\nvisible, which is necessary for honest method-cost and robustness comparisons.\n\n## Claim Boundary\n\nThe verifier proves that the reduced-order example reaches its declared stop\ntime while preserving rejection and fallback evidence. It does not validate a\nproduction H-bridge, semiconductor stress, hardware safety, or control-system\ncertification.\n",
      "order": 9,
      "path": "tutorials/09_FALLBACK_AND_REJECTION_FORENSICS.md",
      "readingMinutes": 4,
      "sha256": "315ccc7f3283491247cc5048c7146c76dc93a62a36197be1ef8e9f5b8a0f12d6",
      "summary": "A rejection means that one proposed step did not satisfy the declared rules. A fallback means that BAB-CS transferred the step to an implicit authority rather than accepting the candidate proposal. Neither event automatically means that…",
      "title": "Tutorial 9: Fallback and Rejection Forensics",
      "wordCount": 699
    },
    {
      "category": "Teaching Lab Tutorials",
      "conceptIds": [
        "babcs",
        "reduced-order-model",
        "deterministic-evidence",
        "phase-error",
        "fail-closed",
        "rlc",
        "rms",
        "ngspice"
      ],
      "headings": [
        {
          "id": "tutorial-10-semantic-mapping-to-ngspice",
          "level": 1,
          "text": "Tutorial 10: Semantic Mapping to ngspice"
        },
        {
          "id": "what-you-will-learn",
          "level": 2,
          "text": "What You Will Learn"
        },
        {
          "id": "run-the-mapping-exercise",
          "level": 2,
          "text": "Run the Mapping Exercise"
        },
        {
          "id": "expected-results",
          "level": 2,
          "text": "Expected Results"
        },
        {
          "id": "observed-data",
          "level": 2,
          "text": "Observed Data"
        },
        {
          "id": "expected-versus-actual-results",
          "level": 2,
          "text": "Expected Versus Actual Results"
        },
        {
          "id": "preserve-canonical-state-order",
          "level": 2,
          "text": "Preserve Canonical State Order"
        },
        {
          "id": "preserve-nonlinear-meaning",
          "level": 2,
          "text": "Preserve Nonlinear Meaning"
        },
        {
          "id": "retain-reproducible-evidence",
          "level": 2,
          "text": "Retain Reproducible Evidence"
        },
        {
          "id": "interpret-differences",
          "level": 2,
          "text": "Interpret Differences"
        },
        {
          "id": "theory-and-practical-outcomes",
          "level": 2,
          "text": "Theory and Practical Outcomes"
        },
        {
          "id": "conclusion",
          "level": 2,
          "text": "Conclusion"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Guide",
      "markdown": "# Tutorial 10: Semantic Mapping to ngspice\n\nngspice is an open-source circuit simulator from the Simulation Program with\nIntegrated Circuit Emphasis (`SPICE`) family. A semantic mapping translates a\nBAB-CS case into an ngspice netlist while preserving the meaning of component\nvalues, node orientation, waveforms, initial conditions, and dynamic-state\ncoordinates.\n\n![Semantic ngspice mapping](html/assets/tutorial-10-ngspice-mapping.svg \"BAB-CS JSON is mapped to an ngspice netlist, executed independently, and retained as scoped comparison evidence.\")\n\n## What You Will Learn\n\nThe external manifest owns 20 mapped cases. A manifest is a machine-readable\ninventory that names every required input and its intended role. The suite\ncovers linear, resonant, nonlinear diode, scheduled switching, and reduced-order\npower-stage cases.\n\n## Run the Mapping Exercise\n\n```bash\nPYTHONPATH=src python lab/support/verify.py --exercise 10-ngspice-mapping\n```\n\nThis dependency-light exercise generates every netlist and checks mapping\ncontracts without requiring ngspice itself.\n\nTo execute all 20 comparisons when ngspice is installed:\n\n```bash\nPYTHONPATH=src python tools/run_external_suite.py \\\n  benchmarks/external/manifest.json \\\n  --output-root artifacts/external\n```\n\n## Expected Results\n\nThe structural expectation is that all 20 manifest-owned cases translate\nwithout changing component values, waveform schedules, initial conditions, or\ncanonical state order. The live expectation is not exact waveform identity:\nBAB-CS and ngspice use different integration, event, and nonlinear-solve paths.\nSmooth linear cases are expected to agree more closely than cases dominated by\nscheduled discontinuities or reduced-order switching configurations.\n\n## Observed Data\n\nBoth commands were run on August 27, 2026. The structural exercise reported:\n\n| Measurement | Observed value |\n| --- | ---: |\n| Mapped cases | `20` |\n| First-order linear cases | `6` |\n| Resonant and resistor-inductor-capacitor (`RLC`) cases | `5` |\n| Nonlinear diode cases | `3` |\n| Scheduled-switching cases | `3` |\n| Reduced-order power-stage cases | `3` |\n| Distinct mapped feature types | `14` |\n| Total dynamic-state coordinates | `28` |\n| External tool treated as an oracle | `false` |\n\nThe live suite used `ngspice-46 : Circuit level simulation program`, completed\nall 20 cases, and wrote 81 files. Root-mean-square (`RMS`) difference is the\nsquare root of the average squared state difference over the compared samples.\n\n| Case | Maximum absolute difference | RMS absolute difference | Samples |\n| --- | ---: | ---: | ---: |\n| `rc_step` | `0.0051291682323232057` | `0.0033464012529142739` | `24` |\n| `rc_discharge` | `0.0014134357468059688` | `0.00058899739135542708` | `72` |\n| `driven_rc` | `0.0014401525975176639` | `0.000611823698698551` | `115` |\n| `current_driven_rc` | `6.5365032747677354e-05` | `3.2776060941444924e-05` | `124` |\n| `rl_step` | `0.000512916823232323` | `0.00033464012529142994` | `24` |\n| `rl_decay` | `0.00014146597091121982` | `4.6017717728039629e-05` | `111` |\n| `lc_long` | `0.013130326422457698` | `0.0054753273479576483` | `1211` |\n| `lc_offset` | `0.001101557552985015` | `0.00048623547719068655` | `611` |\n| `rlc_damped` | `0.0071763452565745123` | `0.0022849129475191704` | `136` |\n| `rlc_overdamped` | `0.015911107856226181` | `0.0038731901233796402` | `111` |\n| `rlc_driven` | `0.00020125793767961087` | `0.00011724872569275529` | `418` |\n| `diode_clip` | `0.0031177968773050506` | `0.0005379440652499948` | `265` |\n| `diode_rectifier` | `0.00025825500840270799` | `0.00020269449181182741` | `1011` |\n| `diode_bias_recovery` | `0.0018060735306290043` | `0.00031152329235558225` | `523` |\n| `switched_rc` | `0.11593356837261994` | `0.033962482648523362` | `96` |\n| `switched_rl` | `0.0090394634303352372` | `0.006639984445535505` | `300` |\n| `switched_rlc` | `0.025442652271918664` | `0.016758263125078453` | `372` |\n| `buck_like_reduced_order` | `0.0055742268408994489` | `0.0027573672746739708` | `411` |\n| `h_bridge_rl_reduced_order` | `3.730147981349861` | `0.23016505280206029` | `450` |\n| `dc_link_rlc_reduced_order` | `0.018367492321976098` | `0.0075241352548316787` | `281` |\n\nThe H-bridge case has the largest maximum difference. That value occurs in a\nscheduled reduced-order experiment and is an investigation target around event\nhandling and independent integration behavior. It is not converted into a\nclaim that either simulator is universally more accurate. Absolute differences\nretain each state coordinate's native unit. In a mixed RLC case, the reported\nmaximum is the largest difference among voltage and current coordinates, so the\ntable is evidence for case-by-case review rather than a single cross-case score.\n\n## Expected Versus Actual Results\n\nThe structural expectation was met: 20 cases, 14 mapped feature types, and 28\ndynamic coordinates completed with preserved state ordering. Smooth first-order\nand diode cases showed relatively small native-unit maximum differences. The\nscheduled-switching family showed larger differences, and the reduced-order\nH-bridge produced the largest maximum difference, `3.730147981349861`, with an\nRMS difference of `0.23016505280206029`.\n\nThe broad expected pattern was therefore observed, but the H-bridge maximum was\nlarger than a close-agreement expectation. The retained summary does not locate\nthe exact sample or prove one cause. Plausible explanations include different\nstep placement around switch events, different interpolation onto comparison\ntimes, method-specific damping or phase behavior, and small semantic\ndifferences in ideal-switch execution. Identifying the cause requires a\ntime-localized trace study; it cannot be concluded from the maximum alone.\n\n## Preserve Canonical State Order\n\nBAB-CS stores capacitor voltages first and inductor currents second. The mapper\nmust export ngspice vectors in that same order. Comparing values in element-file\norder can silently compare an inductor current with a capacitor voltage when a\nmixed resistor-inductor-capacitor (`RLC`) case lists the inductor first.\n\nThe exercise requires every generated state-name tuple to equal the BAB-CS\ndynamic-state tuple exactly.\n\n## Preserve Nonlinear Meaning\n\nThe BAB-CS diode uses saturation current and thermal voltage in the Shockley\nequation. ngspice exposes saturation current and a diode ideality factor. The\nmapper converts the declared thermal voltage into the corresponding ideality\nfactor instead of rejecting or silently changing non-default cases.\n\nUnsupported parameters still fail closed. Fail closed means stop with an\nexplicit error rather than guess a translation.\n\n## Retain Reproducible Evidence\n\nFor every case, the suite retains:\n\n- the generated netlist;\n- ngspice raw output;\n- the ngspice log;\n- the BAB-CS-versus-ngspice report;\n- component and artifact Secure Hash Algorithm 256-bit (`SHA-256`)\n  fingerprints; and\n- the tool version and executed command.\n\nThe deterministic `wrdata` vectors create one time column followed by the\ncanonical state columns.\n\n## Interpret Differences\n\nAgreement supports implementation consistency for the declared mapping. A\nlarge difference identifies a case that needs investigation. Possible causes\ninclude integration method, event interpolation, nonlinear iteration, source\nconventions, or device-model details.\n\nngspice is independent comparison evidence, not an oracle. An oracle would be\nan authority assumed to provide the unquestionably correct answer. This\nworkflow makes no such assumption.\n\n## Theory and Practical Outcomes\n\nThe theoretical outcome is cross-implementation falsification: an independent\nsimulator can expose translation or numerical differences that an internal\nreference might share. The practical outcome is a 20-case evidence package with\nnetlists, logs, raw outputs, state order, tool identity, and measured\ndifferences. Large discrepancies become investigation targets rather than being\ndiscarded or converted into a universal ranking.\n\n## Conclusion\n\nThe mapping program met its structural coverage goal and produced complete live\nevidence. Numerical agreement is case dependent. The H-bridge result shows why\nexternal comparison is most useful when it preserves disagreement and directs\nthe next experiment instead of treating either implementation as an oracle.\n\n## Claim Boundary\n\nThe mapping exercise proves structural coverage of 20 declared cases. The live\nsuite proves that ngspice 46 executed all 20 in the measured environment. The\nthree power-stage cases remain reduced-order numerical experiments, not\nproduction device models.\n",
      "order": 10,
      "path": "tutorials/10_SEMANTIC_NGSPICE_MAPPING.md",
      "readingMinutes": 5,
      "sha256": "e3db9db93c354c8390edf8b356b0814c87f2cf2fd5d1a7d8313c1b9192b01dbe",
      "summary": "ngspice is an open-source circuit simulator from the Simulation Program with Integrated Circuit Emphasis (SPICE) family. A semantic mapping translates a BAB-CS case into an ngspice netlist while preserving the meaning of component…",
      "title": "Tutorial 10: Semantic Mapping to ngspice",
      "wordCount": 1033
    },
    {
      "category": "Tests and Comparisons",
      "conceptIds": [
        "babcs",
        "candidate-method",
        "projection",
        "replay",
        "anchor",
        "jacobian",
        "reduced-order-model",
        "deterministic-evidence",
        "fixed-step",
        "fixed-accuracy",
        "fixed-work",
        "phase-error",
        "fail-closed",
        "factorization",
        "python-wheel",
        "mna",
        "rc",
        "rl",
        "rlc",
        "lc",
        "pwl",
        "ab2",
        "be",
        "bdf2",
        "rk23",
        "superlu",
        "scipy",
        "rms",
        "json",
        "csv",
        "svg",
        "sha256",
        "ci"
      ],
      "headings": [
        {
          "id": "bounded-authority-based-circuit-simulation-comparison-protocol",
          "level": 1,
          "text": "Bounded-Authority-Based-Circuit-Simulation Comparison Protocol"
        },
        {
          "id": "purpose",
          "level": 2,
          "text": "Purpose"
        },
        {
          "id": "authority-hierarchy",
          "level": 2,
          "text": "Authority Hierarchy"
        },
        {
          "id": "compared-methods",
          "level": 2,
          "text": "Compared Methods"
        },
        {
          "id": "circuit-matrix",
          "level": 2,
          "text": "Circuit Matrix"
        },
        {
          "id": "common-sampling",
          "level": 2,
          "text": "Common Sampling"
        },
        {
          "id": "three-controls",
          "level": 2,
          "text": "Three Controls"
        },
        {
          "id": "fixed-timestep",
          "level": 3,
          "text": "Fixed Timestep"
        },
        {
          "id": "fixed-accuracy",
          "level": 3,
          "text": "Fixed Accuracy"
        },
        {
          "id": "fixed-work",
          "level": 3,
          "text": "Fixed Work"
        },
        {
          "id": "metrics",
          "level": 2,
          "text": "Metrics"
        },
        {
          "id": "determinism-and-provenance",
          "level": 2,
          "text": "Determinism and Provenance"
        },
        {
          "id": "threshold-policy",
          "level": 2,
          "text": "Threshold Policy"
        },
        {
          "id": "performance-boundary",
          "level": 2,
          "text": "Performance Boundary"
        },
        {
          "id": "qualification-tiers",
          "level": 2,
          "text": "Qualification Tiers"
        },
        {
          "id": "observatory-and-atlas-profiles",
          "level": 2,
          "text": "Observatory and Atlas Profiles"
        }
      ],
      "kind": "Evidence",
      "markdown": "# Bounded-Authority-Based-Circuit-Simulation Comparison Protocol\n\n## Purpose\n\nThe comparison harness characterizes accuracy, boundedness, robustness, and\ndeterministic work for BAB-CS and its authority integrators. It does not turn a\nlocal predictor/reference deviation into a proof of exact physical trajectory\nerror.\n\nThe canonical matrix is `benchmarks/manifest.json`; circuit inputs are under\n`benchmarks/cases/`. The runner is `tools/compare_methods.py`.\n\n## Authority Hierarchy\n\nEvery reported error names its authority source.\n\n1. **Analytic solution** for supported closed-form linear circuits.\n2. **Independent refined replay** from the trusted initial condition with a\n   separately configured smaller implicit timestep.\n3. **External simulator** as optional cross-implementation evidence when device\n   semantics can be mapped without alteration.\n4. **BAB-CS implicit authority** using backward Euler, trapezoidal, or BDF2.\n5. **BAB-CS local step reference** for runtime gating only; it is not an\n   independent accumulated-trajectory authority.\n\nThe deterministic runner currently uses analytic or refined-replay authorities.\nExternal results are produced separately by `tools/compare_external.py` so that\ntheir toolchain and semantic-mapping provenance remain explicit.\n\n## Compared Methods\n\n- `backward_euler`: production implicit reference in disabled rollout mode.\n- `trapezoidal`: production implicit reference in disabled rollout mode.\n- `bdf2`: production variable-step BDF2 reference in disabled rollout mode.\n- `shadow`: AB2 diagnostics run while the implicit reference remains\n  authoritative.\n- `active`: projected and contractively corrected AB2 with every-step implicit\n  reference and independent periodic replay anchors.\n- `bounded_explicit_euler`, `bounded_heun`, and `bounded_rk23`: explicit\n  candidates using the shared every-step reference/correction controller.\n- `bounded_backward_euler`, `bounded_trapezoidal`, and `bounded_bdf2`: implicit\n  candidates paired with a distinct implicit reference.\n- `bounded_ab2_fast`, `bounded_heun_fast`, and `bounded_rk23_fast`: embedded\n  candidates with four-step scheduled references, dynamic bound checkpoints,\n  and periodic independent replay.\n- `raw_ab2`: test-only reduced-system variable-step AB2. It is not a production\n  rollout mode and cannot bypass production safety gates.\n\nThe manifest rejects unknown methods, missing inputs, duplicate case IDs,\ninvalid authorities, and unsupported raw-model mappings.\n\n## Circuit Matrix\n\nThe standard matrix includes RC and RL steps, underdamped and overdamped RLC,\nsinusoidally driven RC, ideal LC long-horizon oscillation, diode clipping, and a\nrepeated switched RC case. Unit and qualification tests additionally cover\ncharge/discharge, pulse and PWL boundaries, closely spaced events, nonlinear\nrecovery, topology failures, and isolated hard-gate failures.\n\n## Common Sampling\n\nFor each case, every method uses the same circuit parameters, initial state,\nstart and stop times, event boundaries, selected state indices, and common\noutput sample times. Method traces are interpolated only for evaluation at those\ncommon times. Authority construction is independent of the candidate method.\n\n## Three Controls\n\n### Fixed Timestep\n\nResults with equal `nominal_step` expose method behavior under equal temporal\ndiscretization. Event boundaries are still reached exactly.\n\n### Fixed Accuracy\n\nFor each declared target in `accuracy_targets`, the report selects the least\ndeterministic-work result that reaches the target. Failure to reach a target is\nreported rather than silently relaxed.\n\n### Fixed Work\n\nFor each declared `work_budgets` value, the report selects the most accurate\nresult within the budget. Deterministic work is the sum of accepted steps,\ncandidate and reference circuit evaluations and algebraic iterations,\npredictor/corrected projection iterations, differential Jacobian evaluations,\nand replay steps, circuit evaluations, and algebraic iterations. Each source\ncounter is also reported independently. Wall time is excluded so hardware noise\ncannot change qualification.\n\n## Metrics\n\nAccuracy fields include final-state maximum absolute error, maximum waveform\nerror, RMS waveform error, per-state scaled error, and observed convergence\norder. Oscillator cases report sampled amplitude error, final phase error,\nrelative period error, and relative energy span as separate quantities.\n\nBound fields include candidate/reference error, embedded error,\ncorrected/reference error, recursive estimated bound, dynamic reference\ncheckpoints, pre-reset bound, independent anchor deviation, and the empirical\nanchor-error-to-pre-reset-bound ratio. That ratio is characterization evidence,\nnot a formal coverage proof.\n\nRobustness fields include accepted/rejected attempts, rejection categories,\nhistory-reset reasons, implicit fallbacks, periodic/safety anchors, and accepted\ntimestep statistics.\n\nWork fields include candidate solves/evaluations/iterations, projection counts\nand iterations, reference solves, reference Newton and algebraic iterations,\nreplay work, differential Jacobian evaluations, and a deterministic aggregate\nwork unit.\n\n## Determinism and Provenance\n\nRun the complete matrix:\n\n```bash\nPYTHONPATH=src python tools/compare_methods.py \\\n  --output artifacts/numerical.json \\\n  --csv-output artifacts/numerical.csv \\\n  --plot-output artifacts/error-by-step.svg\n```\n\nAdd separate timing characterization:\n\n```bash\nPYTHONPATH=src python tools/compare_methods.py \\\n  --output artifacts/numerical.json \\\n  --timing-output artifacts/timing.json \\\n  --timing-repeats 3\n```\n\nUse `--case CASE_ID` repeatedly to select cases and `--quick` for the smallest\nconfigured timestep/anchor subset. Outputs fail closed on overwrite unless\n`--overwrite` is explicit.\n\nThe numerical report records the source commit, dirty state, deterministic\nsource-tree SHA-256, manifest hash, runner identity, interpreter/platform\nmetadata, case input hashes, circuit elements, simulation settings, complete\nmethod configuration, and authority. The source-tree hash covers Git tracked and\nuntracked non-ignored files while excluding generated build/evidence directories\nand the self-referential qualification and performance audit documents.\nIt contains no wall-clock measurements. Under an identical environment, the\nnumerical JSON, flattened CSV, and SVG are expected to reproduce byte-for-byte.\n\nThe timing report records repeated elapsed samples separately. Wall time is\nnever a correctness or release threshold.\n\n## Threshold Policy\n\n- Mathematical identities and mode semantics use deterministic tolerances\n  derived from machine precision and problem scale.\n- Convergence is gated by an order range across refinements, not one golden\n  output value.\n- Long-horizon phase, energy, and bound checks use explicit tolerances.\n- Empirical bound coverage remains characterization until a documented\n  derivation supports a hard relationship.\n- Threshold or baseline changes require rationale, before/after evidence, and\n  human review; regenerating expected output alone is insufficient.\n\n## Performance Boundary\n\nThe default active mode performs an implicit reference solve on every candidate\nstep and may also perform candidate/correction projections, differential\nJacobian evaluation, and periodic refined replay. Built-in circuits use exact\nMNA sensitivity Jacobians plus bounded topology/factorization caches; extension\nsubclasses retain a finite-difference fallback unless they provide an override.\nThe deterministic default uses the built-in dense solver. An explicit optional\n`auto` backend uses SciPy SuperLU only beyond measured matrix-size, sparsity, and\nright-hand-side crossovers; `scipy` forces that backend. Diode circuits bypass\nthe linear caches but may use the optional sparse backend for sufficiently large\nfresh Newton systems. Embedded AB2, Heun, and RK23\nvariants may defer references, but dynamic bound checkpoints deliberately\nrestore reference work in difficult regions. Work comparisons describe the cost\nof bounded, inspectable behavior; timing rows remain local characterization, not\na general speed claim.\n\n## Qualification Tiers\n\n- Pull-request CI runs Python 3.11 through 3.14 tests, deterministic examples,\n  a deterministic comparison smoke, optional SciPy backend qualification, and\n  installed-wheel smoke.\n- Scheduled CI enables `BABCS_LONG_TESTS=1`, runs the full comparison/timing\n  matrix, runs `ngspice` mappings, hashes evidence, and uploads artifacts.\n- Release qualification enables both `BABCS_LONG_TESTS=1` and\n  `BABCS_VERY_LONG_TESTS=1`, builds the wheel, runs tests with the installed\n  wheel, generates comparison evidence, and records exact hashes.\n\nRelease publication still requires human review of changed thresholds,\nbaselines, and deterministic artifacts.\n\n## Observatory and Atlas Profiles\n\n`benchmarks/observatory/manifest.json` is the canonical six-case,\nseven-candidate profile. `tools/method_observatory.py` requires all 126\nfixed-step rows and derives fixed-accuracy and fixed-work selections only from\nmeasured rows, preserving each selected `row_id`. A missing, duplicate, or\nunexpected row is a qualification failure.\n\n`tools/bound_coverage_atlas.py` consumes those exact row IDs, rejects a\nsource-tree hash mismatch, replays each exact configuration, and reconciles\nsample diagnostics and deterministic work before reporting. Its empirical\ncoverage fraction compares authority-epoch drift with the recursive internal\nbound only on documented eligible samples. It is characterization evidence,\nnot a proof of physical-trajectory enclosure.\n\n`benchmarks/power_stage/manifest.json` separately characterizes three\nreduced-order numerical experiments. It is not part of the production-device\nmodel surface and must retain that classification in inputs, reports, and\nreview language.\n",
      "order": 0,
      "path": "COMPARISON_PROTOCOL.md",
      "readingMinutes": 6,
      "sha256": "5c531d70f1423be596a3e24fce157c9323c1c83ed1c858f4c055b2e8d1042808",
      "summary": "The comparison harness characterizes accuracy, boundedness, robustness, and deterministic work for BAB-CS and its authority integrators. It does not turn a local predictor/reference deviation into a proof of exact physical trajectory error.",
      "title": "Bounded-Authority-Based-Circuit-Simulation Comparison Protocol",
      "wordCount": 1210
    },
    {
      "category": "Tests and Comparisons",
      "conceptIds": [
        "babcs",
        "candidate-method",
        "numerical-authority",
        "projection",
        "replay",
        "nonlinear-convergence",
        "deterministic-evidence",
        "fixed-step",
        "phase-error",
        "rc",
        "rl",
        "rlc",
        "lc",
        "ab2",
        "bdf2",
        "rk23",
        "json"
      ],
      "headings": [
        {
          "id": "bab-cs-method-observatory",
          "level": 1,
          "text": "BAB-CS Method Observatory"
        },
        {
          "id": "circuit-and-result-figures",
          "level": 2,
          "text": "Circuit and Result Figures"
        },
        {
          "id": "rc-step",
          "level": 3,
          "text": "RC Step"
        },
        {
          "id": "rl-step",
          "level": 3,
          "text": "RL Step"
        },
        {
          "id": "damped-rlc",
          "level": 3,
          "text": "Damped RLC"
        },
        {
          "id": "lossless-lc-long-horizon",
          "level": 3,
          "text": "Lossless LC Long Horizon"
        },
        {
          "id": "diode-clip",
          "level": 3,
          "text": "Diode Clip"
        },
        {
          "id": "switched-rc",
          "level": 3,
          "text": "Switched RC"
        },
        {
          "id": "run",
          "level": 2,
          "text": "Run"
        },
        {
          "id": "reports",
          "level": 2,
          "text": "Reports"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Evidence",
      "markdown": "# BAB-CS Method Observatory\n\nThe Method Observatory runs every implemented BAB-CS candidate method on the\ncanonical RC, RL, damped RLC, lossless LC, diode-clip, and switched-RC cases.\nEvery case has at least three fixed-step refinements. The complete required\nmatrix contains 126 rows: six cases, seven bounded candidates, and three steps.\n\nThe seven candidate profiles are explicit Euler, Heun, RK23, AB2, backward\nEuler, trapezoidal, and BDF2. Each remains supervised by projection, independent\nreference authority, correction, hard gates, and replay. Trapezoidal candidates\nuse BDF2 authority; the other profiles use trapezoidal authority so an implicit\ncandidate is never compared with an identical local reference method.\n\n## Circuit and Result Figures\n\nEach schematic below is generated from the exact checked-in JSON case. Each\nresult graph runs that case through the current BAB-CS simulator and plots its\naccepted states. The graphs are representative trajectories for understanding\nthe cases; the full Observatory report remains the authority for the complete\n126-row method and refinement matrix.\n\n### RC Step\n\nThe resistor-capacitor (`RC`) case applies a one-volt step through a one-kilohm\nresistor to a one-microfarad capacitor. The accepted state is the capacitor\nvoltage, which rises toward the source voltage.\n\n![RC step circuit showing the source, resistor, capacitor, output node, and accepted capacitor-voltage state](html/assets/circuit-rc-step.svg \"RC step schematic generated from the canonical case values and topology.\")\n\n![BAB-CS accepted RC capacitor-voltage trace](html/assets/result-rc-step.svg \"Representative accepted BAB-CS capacitor-voltage result for the RC step case.\")\n\n### RL Step\n\nThe resistor-inductor (`RL`) case applies a one-volt step to a ten-ohm resistor\nand one-millihenry inductor. The accepted state is inductor current, which must\nremain continuous while it approaches its steady value.\n\n![RL step circuit showing the source, resistor, inductor, and current direction](html/assets/circuit-rl-step.svg \"RL step schematic generated from the canonical case values and topology.\")\n\n![BAB-CS accepted RL inductor-current trace](html/assets/result-rl-step.svg \"Representative accepted BAB-CS inductor-current result for the RL step case.\")\n\n### Damped RLC\n\nThe damped resistor-inductor-capacitor (`RLC`) case begins with stored capacitor\nenergy. Voltage and current oscillate while the declared resistor removes\nenergy. The graph keeps voltage and current in separate panels because they use\ndifferent physical units.\n\n![Parallel damped RLC circuit with resistor, capacitor, and inductor branches](html/assets/circuit-rlc-damped.svg \"Damped RLC schematic showing the exact parallel topology and initial state.\")\n\n![BAB-CS damped RLC voltage and current traces](html/assets/result-rlc-damped.svg \"Representative accepted BAB-CS capacitor-voltage and inductor-current results for the damped RLC case.\")\n\n### Lossless LC Long Horizon\n\nThe inductor-capacitor (`LC`) case has no declared resistor. Electrical and\nmagnetic energy exchange for ten periods, making phase drift and stored-energy\ndrift separately visible.\n\n![Parallel lossless LC circuit with declared initial capacitor voltage](html/assets/circuit-lc-long.svg \"Lossless LC schematic generated from the canonical topology and initial state.\")\n\n![BAB-CS long-horizon LC voltage and current traces](html/assets/result-lc-long.svg \"Representative accepted BAB-CS LC trajectory; phase and energy are evaluated separately.\")\n\n### Diode Clip\n\nThe diode-clip case drives an RC output with a sinusoidal source and a Shockley\ndiode. A Shockley diode is a simplified exponential diode equation used here to\nexercise nonlinear convergence and clipping behavior.\n\n![Diode-clip circuit showing the sine source, resistor, diode, and capacitor](html/assets/circuit-diode-clip.svg \"Diode-clip schematic generated from the canonical nonlinear case.\")\n\n![BAB-CS diode-clip input and output voltage traces](html/assets/result-diode-clip.svg \"Representative accepted BAB-CS input and clipped-output result for the diode case.\")\n\n### Switched RC\n\nThe switched-RC case adds a scheduled resistive switch across the capacitor.\nThe switch command repeatedly discharges the output, and every commanded\ntransition is an exact event boundary rather than an event crossed inside one\ntimestep.\n\n![Switched RC circuit showing the scheduled discharge switch](html/assets/circuit-switched-rc.svg \"Switched-RC schematic generated from the canonical case and pulse schedule.\")\n\n![BAB-CS switched-RC voltage and command traces with event boundaries](html/assets/result-switched-rc.svg \"Representative accepted BAB-CS switched-RC result; orange rules mark accepted event boundaries.\")\n\n## Run\n\n```bash\nPYTHONPATH=src python tools/method_observatory.py \\\n  --output artifacts/observatory/numerical.json \\\n  --fixed-step-csv artifacts/observatory/fixed-step.csv \\\n  --fixed-accuracy-csv artifacts/observatory/fixed-accuracy.csv \\\n  --fixed-work-csv artifacts/observatory/fixed-work.csv \\\n  --plot-output artifacts/observatory/accuracy-by-work.svg \\\n  --markdown-output artifacts/observatory/report.md\n```\n\nUse `--case CASE_ID` to select cases and `--quick` to run the first two step\nsizes. Add `--timing-repeats N --timing-output PATH` only for separate local\ntiming characterization.\n\n## Reports\n\n- **Fixed step** preserves every measured configuration and its accuracy,\n  internal-bound, phase/energy, robustness, and deterministic-work evidence.\n- **Fixed accuracy** selects the least-work measured row that meets a target.\n- **Fixed work** selects the smallest-error measured row within a work budget.\n\nEvery selected row records its canonical `row_id`. No qualification selection\nuses interpolation or extrapolation. `no_qualifying_row` is emitted when the\nmeasured grid does not satisfy a target or budget.\n\n![Method Observatory fixed-step accuracy versus deterministic work](html/assets/result-observatory-accuracy-work.svg \"Representative RC fixed-step view of all seven bounded candidate profiles; this graph is a measured workflow view, not a universal ranking.\")\n\n## Claim Boundary\n\nThe observatory characterizes the declared cases, configurations, authority,\nsource tree, and environment. It does not prove that one method is universally\nbetter. Deterministic work is a reproducible counter; elapsed time is separate\nmachine-local evidence and is not a correctness gate.\n",
      "order": 1,
      "path": "METHOD_OBSERVATORY.md",
      "readingMinutes": 4,
      "sha256": "e4e58a691029ccb752c604a954682cc8dc17fba2f06621e71994fc2ccf68aa07",
      "summary": "The Method Observatory runs every implemented BAB-CS candidate method on the canonical RC, RL, damped RLC, lossless LC, diode-clip, and switched-RC cases. Every case has at least three fixed-step refinements. The complete required…",
      "title": "BAB-CS Method Observatory",
      "wordCount": 838
    },
    {
      "category": "Tests and Comparisons",
      "conceptIds": [
        "babcs",
        "replay",
        "anchor",
        "recursive-bound",
        "residual",
        "deterministic-evidence",
        "phase-error",
        "energy-drift",
        "empirical-coverage",
        "rc",
        "lc",
        "rms",
        "wrms",
        "svg"
      ],
      "headings": [
        {
          "id": "bab-cs-bound-coverage-atlas",
          "level": 1,
          "text": "BAB-CS Bound Coverage Atlas"
        },
        {
          "id": "metrics",
          "level": 2,
          "text": "Metrics"
        },
        {
          "id": "run",
          "level": 2,
          "text": "Run"
        },
        {
          "id": "anchor-evidence",
          "level": 2,
          "text": "Anchor Evidence"
        },
        {
          "id": "views",
          "level": 2,
          "text": "Views"
        },
        {
          "id": "authority-error-and-recursive-bound",
          "level": 3,
          "text": "Authority Error and Recursive Bound"
        },
        {
          "id": "empirical-coverage-by-authority-age",
          "level": 3,
          "text": "Empirical Coverage by Authority Age"
        },
        {
          "id": "phase-and-energy",
          "level": 3,
          "text": "Phase and Energy"
        },
        {
          "id": "rejection-and-fallback-causes",
          "level": 3,
          "text": "Rejection and Fallback Causes"
        }
      ],
      "kind": "Evidence",
      "markdown": "# BAB-CS Bound Coverage Atlas\n\nThe Bound Coverage Atlas replays the exact configurations and canonical row IDs\nfrom a Method Observatory report. It aligns analytic or refined-replay authority\nat every accepted time and reports the relationship between observed authority\nerror and BAB-CS internal evidence.\n\n## Metrics\n\nFor each accepted bounded step, the atlas reports:\n\n- `actual_authority_error`, the weighted distance from the declared authority;\n- `authority_epoch_drift_error`, the weighted trajectory drift since the last\n  independent anchor;\n- `recursive_internal_bound`, the accepted BAB-CS recursive bound;\n- anchor deviation and pre-reset bound;\n- phase and energy separately where applicable;\n- empirical error-to-bound and bound-to-error ratios;\n- fallback, rejection, event, and history-reset causes; and\n- requested and suggested steps for each rejected attempt.\n\nCoverage excludes zero-bound, anchor/reset, event, unavailable, and non-finite\nsamples and counts them separately. The empirical coverage fraction is the\nfraction of eligible samples where authority epoch drift does not exceed the\nrecursive internal bound. This is characterization evidence, not a formal\nenclosure theorem or a guarantee against an unknown physical trajectory.\n\n## Run\n\nFirst generate the Method Observatory report, then run:\n\n```bash\nPYTHONPATH=src python tools/bound_coverage_atlas.py \\\n  --observatory-report artifacts/observatory/numerical.json \\\n  --output artifacts/bound-atlas/atlas.json \\\n  --sample-csv artifacts/bound-atlas/samples.csv \\\n  --plot-directory artifacts/bound-atlas/plots\n```\n\nThe generator refuses an Observatory report whose source-tree hash differs from\nthe current source. It replays every exact configuration and requires diagnostic\nand deterministic-work reconciliation before producing atlas evidence.\n\n## Anchor Evidence\n\nEvery periodic, safety, and event-forced anchor records authority age, pre-reset\nbound, provisional-to-replay deviation, actual authority error before and after\nreplacement, replay subdivisions and retries, replay-native energy evidence,\nand final residuals. Event history reset remains distinct from authority refresh.\n\n## Views\n\nThe deterministic SVG set contains error versus bound, empirical coverage by\nanchor age, phase versus energy, and rejection/fallback cause views. Timing is\nnot included in atlas evidence.\n\n### Authority Error and Recursive Bound\n\nThis representative RC view uses the Atlas weighted root-mean-square scaling.\nWeighted root-mean-square means the state differences are normalized by the\ndeclared absolute and relative tolerances before they are combined. The graph\ndoes not convert measured coverage into a mathematical enclosure theorem.\n\n![Bound Coverage Atlas authority error and recursive internal bound graph](html/assets/result-bound-coverage.svg \"Representative RC authority-error and recursive-bound traces using the Atlas scaling rules.\")\n\n### Empirical Coverage by Authority Age\n\nAuthority age is the number of accepted steps since independent replay last\nrefreshed the retained authority basis. This view groups eligible lossless-LC\nsamples into the same age buckets used by the Atlas.\n\n![Bound Coverage Atlas empirical coverage fraction by authority-age bucket](html/assets/result-coverage-by-age.svg \"Representative lossless-LC empirical coverage grouped by accepted steps since authority refresh.\")\n\n### Phase and Energy\n\nPhase error measures timing displacement in the oscillation. Relative energy\nerror measures numerical gain or loss of stored electrical and magnetic energy.\nThey remain separate because either measurement can be small while the other is\nlarge.\n\n![Bound Coverage Atlas phase and relative stored-energy error graphs](html/assets/result-phase-energy.svg \"Representative lossless-LC phase and stored-energy evidence shown as separate quantities.\")\n\n### Rejection and Fallback Causes\n\nThe cause chart groups exact rejection records through the canonical Atlas\nreason taxonomy. The representative scheduled H-bridge case exercises\ncandidate-cap and nonlinear-reference rejection paths; the complete raw\nmessages remain in the numerical report.\n\n![Bound Coverage Atlas rejection and fallback cause counts](html/assets/result-rejection-causes.svg \"Classified rejection and fallback causes observed in the scheduled H-bridge reduced-order numerical experiment.\")\n",
      "order": 2,
      "path": "BOUND_COVERAGE_ATLAS.md",
      "readingMinutes": 3,
      "sha256": "00896fdf9864cdae7ab3e1682e9bddb5f16890c927681ec72bbe57ebb29b1d99",
      "summary": "The Bound Coverage Atlas replays the exact configurations and canonical row IDs from a Method Observatory report. It aligns analytic or refined-replay authority at every accepted time and reports the relationship between observed…",
      "title": "BAB-CS Bound Coverage Atlas",
      "wordCount": 548
    },
    {
      "category": "Tests and Comparisons",
      "conceptIds": [
        "babcs",
        "replay",
        "residual",
        "passivity",
        "reduced-order-model",
        "deterministic-evidence",
        "rl",
        "rlc",
        "dc",
        "json",
        "csv"
      ],
      "headings": [
        {
          "id": "bab-cs-power-stage-sandbox",
          "level": 1,
          "text": "BAB-CS Power-Stage Sandbox"
        },
        {
          "id": "simplified-buck-like-converter",
          "level": 2,
          "text": "Simplified Buck-Like Converter"
        },
        {
          "id": "scheduled-h-bridge-rl-load",
          "level": 2,
          "text": "Scheduled H-Bridge RL Load"
        },
        {
          "id": "dc-link-rlc-startup-and-interruption",
          "level": 2,
          "text": "DC-Link RLC Startup and Interruption"
        },
        {
          "id": "qualification",
          "level": 2,
          "text": "Qualification"
        }
      ],
      "kind": "Evidence",
      "markdown": "# BAB-CS Power-Stage Sandbox\n\n> These are reduced-order numerical experiments, not production device models.\n\nThe Power-Stage Sandbox extends BAB-CS event, authority, passivity, and\ndeterminism evidence without claiming production semiconductor or hardware\nfidelity. Every case uses only the currently implemented R, L, C, independent\nsource, Shockley diode, and scheduled resistive-switch semantics.\n\n## Simplified Buck-Like Converter\n\n`examples/power_stage/buck_like_reduced_order.json` contains a scheduled\nhigh-side resistive switch, freewheel Shockley diode, output inductor,\ncapacitor, load, and a declared reduced-order switch-node bleed path. It is used\nto observe inductor-current continuity, output ripple, diode conduction,\nevent-forced replay, and energy accounting.\n\n![Simplified buck-like reduced-order circuit with scheduled switch, freewheel diode, inductor, capacitor, bleed path, and load](html/assets/circuit-buck-like.svg \"Simplified buck-like schematic generated from the checked-in reduced-order experiment.\")\n\n![BAB-CS simplified buck-like output-voltage and inductor-current results](html/assets/result-buck-like.svg \"Representative BAB-CS result for the reduced-order buck-like experiment; orange rules mark accepted switching events.\")\n\n## Scheduled H-Bridge RL Load\n\n`examples/power_stage/h_bridge_rl_reduced_order.json` contains four scheduled\nresistive switches, explicit dead-time intervals, midpoint bleed resistors, and\na series RL load. The schedule produces positive and negative load voltage while\nforbidding same-leg upper/lower overlap. It does not model body diodes,\nshoot-through physics, or gate-driver dynamics.\n\n![Scheduled H-bridge reduced-order circuit driving a series resistor-inductor load](html/assets/circuit-h-bridge-rl.svg \"Scheduled H-bridge RL schematic with explicit high-side and low-side switches and dead-time scheduling.\")\n\n![BAB-CS H-bridge load-voltage and current-reversal results](html/assets/result-h-bridge-rl.svg \"Representative BAB-CS H-bridge result showing polarity reversal, dead time, and continuous inductor current.\")\n\n## DC-Link RLC Startup and Interruption\n\n`examples/power_stage/dc_link_rlc_reduced_order.json` connects a reduced-order\nDC source through a scheduled switch and series R-L path to a capacitor/load.\nA Shockley freewheel path and declared pre-link bleed resistor support bounded\ninterruption decay. The case is not a contactor, fault, or protection model.\n\n![Direct-current-link RLC reduced-order startup and interruption circuit](html/assets/circuit-dc-link-rlc.svg \"DC-link RLC schematic generated from the checked-in startup and interruption experiment.\")\n\n![BAB-CS DC-link voltage and inductor-current startup and interruption results](html/assets/result-dc-link-rlc.svg \"Representative BAB-CS DC-link startup and interruption result with accepted event boundaries.\")\n\n## Qualification\n\n`benchmarks/power_stage/manifest.json` defines refined trapezoidal authority,\nthree step refinements, and bounded candidate profiles. Tests require exact\nevent schedules, event-forced replay with at least eight subdivisions, finite\nstates and powers, residual and energy caps, deterministic CSV/JSON replay,\nH-bridge dead time and polarity reversal, diode conduction, and post-interrupt\nenergy decay.\n\nRun the comparison profiles with:\n\n```bash\nPYTHONPATH=src python tools/compare_methods.py \\\n  --manifest benchmarks/power_stage/manifest.json \\\n  --output artifacts/power-stage/numerical.json \\\n  --csv-output artifacts/power-stage/numerical.csv\n```\n\nThe evidence remains scoped to the exact reduced-order topology, parameters,\nsource tree, and declared refined authority.\n",
      "order": 3,
      "path": "POWER_STAGE_SANDBOX.md",
      "readingMinutes": 2,
      "sha256": "4d50bad285d68f2eb8b33dde04c481243be55de172c53aade69a327591ee8904",
      "summary": "The Power-Stage Sandbox extends BAB-CS event, authority, passivity, and determinism evidence without claiming production semiconductor or hardware fidelity. Every case uses only the currently implemented R, L, C, independent source…",
      "title": "BAB-CS Power-Stage Sandbox",
      "wordCount": 432
    },
    {
      "category": "Tests and Comparisons",
      "conceptIds": [
        "numerical-authority",
        "reduced-order-model",
        "deterministic-evidence",
        "fixed-step",
        "phase-error",
        "energy-drift",
        "shadow-mode",
        "python-wheel",
        "mna",
        "rc",
        "ulp",
        "html",
        "ngspice"
      ],
      "headings": [
        {
          "id": "bab-cs-teaching-and-reproducibility-lab",
          "level": 1,
          "text": "BAB-CS Teaching and Reproducibility Lab"
        }
      ],
      "kind": "Evidence",
      "markdown": "# BAB-CS Teaching and Reproducibility Lab\n\nThe dependency-light lab under `lab/` contains ten executable exercises:\n\n1. modified nodal analysis;\n2. measured fixed-step convergence;\n3. phase versus energy;\n4. shadow authority;\n5. deterministic wheel packaging;\n6. source versus installed-wheel equivalence;\n7. exact event alignment and multistep restart;\n8. empirical recursive-bound coverage;\n9. fallback and rejection forensics; and\n10. semantic mapping of 20 ngspice cases.\n\nThe complete novice tutorials are separate HTML-tree documents:\n\n1. [Modified nodal analysis and state ownership](tutorials/01_MNA_STATE_OWNERSHIP.md)\n2. [Convergence by measured refinement](tutorials/02_CONVERGENCE_BY_REFINEMENT.md)\n3. [Phase error versus energy error](tutorials/03_PHASE_VERSUS_ENERGY.md)\n4. [Shadow authority](tutorials/04_SHADOW_AUTHORITY.md)\n5. [Deterministic packaging](tutorials/05_DETERMINISTIC_PACKAGING.md)\n6. [Source versus installed-wheel equivalence](tutorials/06_SOURCE_WHEEL_EQUIVALENCE.md)\n7. [Exact event alignment](tutorials/07_EVENT_ALIGNMENT.md)\n8. [Empirical bound coverage](tutorials/08_EMPIRICAL_BOUND_COVERAGE.md)\n9. [Fallback and rejection forensics](tutorials/09_FALLBACK_AND_REJECTION_FORENSICS.md)\n10. [Semantic mapping to ngspice](tutorials/10_SEMANTIC_NGSPICE_MAPPING.md)\n\nRun the core numerical path with:\n\n```bash\nPYTHONPATH=src python lab/support/verify.py \\\n  --exercise 01-mna \\\n  --exercise 02-convergence \\\n  --exercise 03-phase-versus-energy \\\n  --exercise 04-shadow-authority\n```\n\nRun the full path from a clean source tree with:\n\n```bash\nPYTHONPATH=src python lab/support/verify.py --exercise all \\\n  --output artifacts/teaching-lab/verification.json\n```\n\nPackaging exercises reject a dirty tree unless `--development` is explicit.\nDevelopment output is labeled non-release evidence. Source/wheel verification\ncreates an isolated virtual environment, removes `PYTHONPATH`, asserts the\nimported module path is outside the repository, and compares source,\ninstalled-module, and installed-console traces and summaries byte-for-byte for\nRC, switched RC, and all three reduced-order power-stage cases. The recorded\nisolated-environment path is normalized for deterministic evidence. The same\nisolated wheel also runs a quick RC Method Observatory smoke and must reproduce\nthe source numerical report byte-for-byte.\nThe shadow-authority exercise separately requires an identical accepted time\ngrid and records the maximum state delta against a 16-ULP solver-roundoff gate;\ncandidate diagnostics do not grant accepted-state authority.\nThe event-alignment exercise proves exact scheduled breakpoints and post-event\nstartup. The bound-coverage exercise deliberately retains a zero measured\ncoverage result rather than turning it into a favorable claim. The forensics\nexercise separates rejected work, fallback, and accepted completion on a\nreduced-order H-bridge. The mapping exercise verifies the canonical state order\nand all 20 manifest-owned ngspice translations.\n\nThe review-controlled fixture changes only with explicit\n`--update-fixtures --exercise all`. The command prints old and new hashes;\nregenerating a fixture is not evidence that the changed result is acceptable.\n\nEach exercise README includes objectives, commands, interpretation questions,\nevidence, and a conservative claim boundary.\n",
      "order": 4,
      "path": "TEACHING_AND_REPRODUCIBILITY_LAB.md",
      "readingMinutes": 2,
      "sha256": "4e9434ea62bb9350a3babde1dd198b862eb3c326d831fe6afd4e29513dee4005",
      "summary": "The dependency-light lab under lab/ contains ten executable exercises:",
      "title": "BAB-CS Teaching and Reproducibility Lab",
      "wordCount": 405
    },
    {
      "category": "Tests and Comparisons",
      "conceptIds": [
        "babcs",
        "reduced-order-model",
        "deterministic-evidence",
        "phase-error",
        "rc",
        "rl",
        "rlc",
        "lc",
        "dc",
        "pwl",
        "sha256",
        "ngspice"
      ],
      "headings": [
        {
          "id": "bab-cs-ngspice-20-case-mapping-atlas",
          "level": 1,
          "text": "BAB-CS ngspice 20-Case Mapping Atlas"
        },
        {
          "id": "the-five-case-families",
          "level": 2,
          "text": "The Five Case Families"
        },
        {
          "id": "first-order-linear-cases",
          "level": 3,
          "text": "First-Order Linear Cases"
        },
        {
          "id": "resonant-and-rlc-cases",
          "level": 3,
          "text": "Resonant and RLC Cases"
        },
        {
          "id": "nonlinear-diode-cases",
          "level": 3,
          "text": "Nonlinear Diode Cases"
        },
        {
          "id": "scheduled-switching-cases",
          "level": 3,
          "text": "Scheduled Switching Cases"
        },
        {
          "id": "reduced-order-power-stage-cases",
          "level": 3,
          "text": "Reduced-Order Power-Stage Cases"
        },
        {
          "id": "mapping-feature-coverage",
          "level": 2,
          "text": "Mapping Feature Coverage"
        },
        {
          "id": "measured-reference-differences",
          "level": 2,
          "text": "Measured Reference Differences"
        },
        {
          "id": "run-and-preserve-the-suite",
          "level": 2,
          "text": "Run and Preserve the Suite"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Evidence",
      "markdown": "# BAB-CS ngspice 20-Case Mapping Atlas\n\nThis atlas documents the 20 cases owned by\n`benchmarks/external/manifest.json`. The manifest, not this prose table, is the\nauthoritative inventory used by the scheduled comparison workflow, the teaching\nlab, documentation metrics, and the suite runner.\n\nngspice is an independent implementation in the Simulation Program with\nIntegrated Circuit Emphasis (`SPICE`) family. Cross-implementation comparison\ncan reveal translation defects, state-order defects, event differences, and\nnonlinear-solver differences. It is not analytic truth and it is not a\nproduction-device certification tool.\n\n![Twenty-case ngspice mapping atlas](html/assets/ngspice-case-atlas.svg \"Twenty mapped cases grouped into five engineering categories.\")\n\n## The Five Case Families\n\n### First-Order Linear Cases\n\n1. **RC step response** checks constant voltage, resistance, capacitance, and a\n   zero initial capacitor voltage.\n2. **RC stored-energy discharge** checks a nonzero initial capacitor voltage\n   without an independent source.\n3. **Sinusoidally driven RC filter** checks sine-source amplitude and phase-lag\n   behavior.\n4. **Piecewise-linear current-driven RC network** checks a current source and a\n   piecewise-linear (`PWL`) schedule. Piecewise linear means straight-line\n   interpolation between declared time-value points.\n5. **RL current buildup** checks a resistor-inductor (`RL`) source transient.\n6. **RL stored-current decay** checks a nonzero initial inductor current.\n\n### Resonant and RLC Cases\n\n7. **Lossless LC oscillation** checks phase and energy behavior in an\n   inductor-capacitor (`LC`) tank.\n8. **LC mixed initial-condition oscillation** checks simultaneous initial\n   capacitor voltage and inductor current.\n9. **Underdamped parallel RLC decay** checks oscillatory stored-energy decay.\n10. **Overdamped parallel RLC decay** checks non-oscillatory decay.\n11. **Driven series RLC network** checks simultaneous capacitor-voltage and\n    inductor-current comparison under sinusoidal forcing.\n\n### Nonlinear Diode Cases\n\n12. **Diode clipper** checks nonlinear limiting with a sine source.\n13. **Capacitor-loaded diode rectifier** checks charging pulses and load\n    discharge.\n14. **Diode bias-transition clamp** checks recovery after a PWL bias reversal.\n\n### Scheduled Switching Cases\n\n15. **Scheduled switched RC network** checks pulse-controlled resistance and\n    exact event boundaries.\n16. **Scheduled switched RL network** checks inductor-current continuity and a\n    diode freewheel path.\n17. **Scheduled switched RLC network** checks event-driven transfer between\n    magnetic and electric stored energy.\n\n### Reduced-Order Power-Stage Cases\n\n18. **Simplified buck-like converter** checks a scheduled high-side switch,\n    freewheel diode, inductor, capacitor, and resistive load.\n19. **Scheduled H-bridge RL load** checks four switch schedules and bipolar load\n    current.\n20. **Direct-current-link RLC startup and interruption** checks connection,\n    interruption, freewheel behavior, and link-energy response.\n\nDirect current (`DC`) means current with a fixed polarity. The three cases in\nthis family are reduced-order numerical experiments. They are not transistor,\ncontactor, thermal, fault, protection, or hardware-safety models.\n\n## Mapping Feature Coverage\n\n![ngspice semantic feature coverage](html/assets/ngspice-feature-coverage.svg \"Counts of cases exercising each declared mapping feature.\")\n\nThe coverage graph counts how many cases exercise each mapping feature. A large\ncount does not prove correctness. It shows how broadly a feature is challenged\nby the current inventory.\n\nThe mapped device and source surface includes:\n\n- resistors, capacitors, inductors, Shockley diodes, and resistive switches;\n- independent voltage and current sources;\n- constant, sine, pulse, and PWL waveforms;\n- capacitor-voltage and inductor-current initial conditions;\n- diode thermal-voltage conversion through ngspice ideality; and\n- deterministic state-vector output in BAB-CS canonical order.\n\n## Measured Reference Differences\n\n![ngspice reference error overview](html/assets/ngspice-error-overview.svg \"Logarithmic maximum absolute differences for the 20-case ngspice 46 reference run.\")\n\nThe reference graph is generated from\n`benchmarks/external/reference-results.json`, which records the normalized\nmetrics from the reviewed ngspice 46 run. The horizontal axis is logarithmic so\nthat small and large differences remain visible together.\n\nThe H-bridge case contains the largest maximum pointwise difference. Its final\ncurrent difference is small, while a switched-event neighborhood creates a much\nlarger maximum. That is an investigation target: the result should lead to\nevent-by-event inspection, not a hidden average and not an unsupported claim\nthat either simulator is universally wrong.\n\n## Run and Preserve the Suite\n\n```bash\nPYTHONPATH=src python tools/run_external_suite.py \\\n  benchmarks/external/manifest.json \\\n  --output-root artifacts/external\n```\n\nThe command writes four artifacts per case plus `suite.json`: 81 files for the\n20-case run. Output refuses overwrite unless `--overwrite` is explicit.\n\nPreserve the report, netlist, raw data, log, manifest, exact source identity,\nand SHA-256 fingerprints together. A detached plot without its mapping and\nprovenance is weaker evidence.\n\n## Claim Boundary\n\nThe atlas proves that the repository owns 20 explicit mappings and that the\nreviewed live run executed all 20 with ngspice 46. It does not claim exact\nphysical trajectory error, universal simulator ranking, or production device\nfidelity.\n",
      "order": 5,
      "path": "NGSPICE_CASE_ATLAS.md",
      "readingMinutes": 4,
      "sha256": "c7321047b0b40a7b142ff6dbd287918096d9f9b7f90e9320819be9f8f11c75e2",
      "summary": "This atlas documents the 20 cases owned by benchmarks/external/manifest.json. The manifest, not this prose table, is the authoritative inventory used by the scheduled comparison workflow, the teaching lab, documentation metrics, and the…",
      "title": "BAB-CS ngspice 20-Case Mapping Atlas",
      "wordCount": 712
    },
    {
      "category": "Tests and Comparisons",
      "conceptIds": [
        "babcs",
        "candidate-method",
        "replay",
        "anchor",
        "recursive-bound",
        "residual",
        "jacobian",
        "deterministic-evidence",
        "fixed-accuracy",
        "empirical-coverage",
        "fail-closed",
        "python-wheel",
        "rss",
        "gnu-time",
        "mna",
        "rc",
        "rl",
        "adams-bashforth",
        "sha256",
        "ngspice"
      ],
      "headings": [
        {
          "id": "bab-cs-versus-ngspice-runtime-benchmark",
          "level": 1,
          "text": "BAB-CS versus ngspice Runtime Benchmark"
        },
        {
          "id": "equal-accuracy-development-update-august-28-2026",
          "level": 2,
          "text": "Equal-Accuracy Development Update — August 28, 2026"
        },
        {
          "id": "retained-fixed-config-publication-results",
          "level": 2,
          "text": "Retained Fixed-Config Publication Results"
        },
        {
          "id": "measurement-contract",
          "level": 2,
          "text": "Measurement Contract"
        },
        {
          "id": "claim-boundary",
          "level": 2,
          "text": "Claim Boundary"
        }
      ],
      "kind": "Evidence",
      "markdown": "# BAB-CS versus ngspice Runtime Benchmark\n\nThis report records a same-machine comparison between Bounded-Authority-Based Circuit Simulation (BAB-CS) and ngspice. The horizontal size coordinate is the model-declared Modified Nodal Analysis (MNA) count: BAB-CS dynamic states plus BAB-CS algebraic unknowns for the shared physical case. It keeps one case at the same horizontal position in both chart panels; it does not imply that ngspice assembles the same internal equation count. ngspice's own `Circuit Equations` value remains recorded separately. Resident set size (RSS) is the peak physical memory retained by a process.\n\n![BAB-CS speedup versus ngspice with accuracy beside it](../artifacts/runtime/speedup-accuracy-by-size.svg)\n\nAbove `1×` means BAB-CS was faster for the measured row. Lower trajectory error is better. Timing never overrides failed accuracy, convergence, or semantic mapping.\n\n## Equal-Accuracy Development Update — August 28, 2026\n\nThe retained publication table below is the earlier shared-timestep baseline. A\nnew bounded development run independently selected each tool's maximum timestep\nagainst the same scaled trajectory-error target of 1. This is called\n**fixed-accuracy comparison**: the circuit and stop time remain identical, but\neach simulator may use the coarsest tested maximum timestep that still satisfies\nthe common accuracy requirement.\n\nThe new `active_heun_deferred4_smooth` BAB-CS profile uses **Heun's method**, a\ntwo-stage predictor-corrector method, for smooth resistor-capacitor (`RC`),\nresistor-inductor (`RL`), and coupled RC circuits. It computes an implicit\ntrapezoidal reference at least every four accepted steps instead of every step.\nThe profile remains active and bounded: embedded error, recursive bounds,\nreference checkpoints, fallback, rejection, and periodic replay remain enabled.\n\n| Family | Size | Prior BAB-CS divisor | New divisor | BAB-CS runtime gain | New speedup vs ngspice |\n| --- | ---: | ---: | ---: | ---: | ---: |\n| `rc_bank` | 1 | 64 | 1 | 5.28× | 0.110× |\n| `rc_bank` | 4 | 64 | 1 | 5.13× | 0.079× |\n| `rc_bank` | 16 | 64 | 1 | 5.24× | 0.060× |\n| `rl_bank` | 1 | 32 | 1 | 2.96× | 0.130× |\n| `rl_bank` | 4 | 32 | 1 | 2.94× | 0.104× |\n| `rl_bank` | 16 | 32 | 1 | 2.73× | 0.073× |\n| `coupled_rc_ring` | 1 | 32 | 1 | 4.20× | 0.170× |\n| `coupled_rc_ring` | 4 | 128 | 1 | 9.63× | 0.601× |\n| `coupled_rc_ring` | 16 | 128 | 1 | 9.32× | 0.409× |\n\nA divisor of 1 means BAB-CS met the target at the baseline maximum timestep. All\nnine rows met the common target for both tools and proved that the source and\ninstalled-wheel trajectories were equivalent. The values use zero warm-ups and\none timed repeat, so they identify engineering direction rather than publication\nmedians. The retained reports are under\n`artifacts/runtime/fixed-accuracy-optimized-quick/`; the runtime-gain column\ncomes from the exploratory profile scan, while the speedup column comes from the\nretained optimized rerun.\n\nThe scheduled switched-RC profile retained Adams-Bashforth second-order (`AB2`),\na two-step explicit candidate method, and deferred ordinary references to every\nfour accepted steps. BAB-CS then qualified at divisor 16 with scaled error\n0.995. The row remains unavailable because ngspice exceeded the bounded\ncalibration budget before qualifying. The diode row also remains unavailable:\nits independently refined authorities differ by scaled error 6.155, above the\nallowed convergence cap of 0.25.\n\nThe next highest-gain work is not another backend change, and the internal bound\nmust not yet be tightened. A runtime-profile extension of the Bound Coverage\nAtlas found empirical external-authority coverage of 93.4% for the\nresistor-capacitor (`RC`) bank, 95.5% for the resistor-inductor (`RL`) bank,\n85.6% for the coupled RC ring, and 52.9% for the switched RC case. The diode\nauthority remains unavailable because its two refinements disagree by scaled\nerror 6.155 against a cap of 0.25.\n\nThe new decomposition shows that normalized circuit residuals are negligible:\ntheir maximum contribution is `8.88e-8`. Propagated prior uncertainty reaches\n91.72 and embedded Heun-versus-Euler deviation reaches 17.14. However, all 13\neligible full-reference transfers remain uncovered against external trajectory\nauthority because the recursive bound is internal and reference-relative: a\nreference solve can reset the internal recurrence without proving that the\nreference method has zero discretization error.\n\nThe first correction experiment added a separately named, default-off\ndual-resolution term. It compares one full trapezoidal reference step with two\nhalf steps and carries the discrepancy across partial and full authority\ntransfers. Same-source size-one evidence found only a 0.15-percentage-point RC\ncoverage gain, no RL gain, and a 7.47-percentage-point coupled-RC gain obtained\nonly after the uncertainty grew above 500,000 scaled units. Deterministic work\nincreased by approximately 8% to 10%, and reference solve count tripled.\n\nThe local estimator is therefore **not promoted**. The runtime profiles and\ndeferred bound cap remain unchanged. The next highest-gain experiment is an\noffline global dual-trajectory qualification that advances independent coarse\nand refined references over the complete output-time sequence and compares\ntheir accumulated drift with analytic or independently qualified authority. The\nbaseline atlas is under `artifacts/atlas/runtime-scaling-optimized/`; the failed\nlocal experiment is retained under `artifacts/atlas/runtime-dual-reference/`.\n\nThat global experiment is now also retained. Raw factor-2-versus-factor-4 drift\nraises total empirical coverage to 100.00% for RC, 100.00% for RL, and 93.77%\nfor the coupled RC ring. However, the added uncertainty is respectively 582,\n399, and 747 times the actual authority drift at the median eligible sample.\nThe global estimator itself covers only 95.24%, 94.83%, and 93.00% of refined\nreference error without an added safety factor. It is more stable than the local\nrecursive term but remains too vacuous for promotion.\n\nThe declared refinement-pair sweep is now complete. It evaluates factor pairs\n2/4, 4/8, 8/16, and 16/32 with safety factors 1 through 16 for RC, RL, and\ncoupled RC cases at sizes 1, 4, and 16. The raw factor-2/4 policy retains the\nhighest worst-case total coverage, 93.77%, but its worst median uncertainty is\n1,033.12 times actual authority drift. Factor 16/32 reduces that worst median to\n31.15 times but lowers worst-case total coverage to 83.40% and increases maximum\npair work to 67,584 unweighted solver events and iterations. No common policy is\nboth informative and reliably covering, so none is promoted.\n\nThis result also clarifies the circuit-scaling deficiency. Repeated RC and RL\nbanks are replication-throughput controls: increasing channel count expands the\nsystem but does not add new coupled dynamics. The atlas work counter records how\nmany solver events occur, not how expensive each larger matrix operation is. It\ncan therefore remain constant as circuit dimension grows and must not be read as\na runtime or floating-point-operation scaling measure. The coupled RC ring adds\ngenuine modes, but broader coupled nonlinear, switching, and oscillatory\nfamilies are still required.\n\nThe next highest-gain experiment is order-aware reference qualification. It\nwill use at least three refinement levels to estimate observed convergence order,\nrequire an asymptotic regime before extrapolation, and identify interpolation or\nsolve floors instead of masking them with a tuned family-specific safety factor.\nThe single-pair evidence is retained under\n`artifacts/atlas/runtime-global-dual-trajectory/`; the multi-pair evidence is\nretained under `artifacts/atlas/runtime-global-refinement-pair-sweep/`.\n\nThat order-aware experiment is now complete and retained under\n`artifacts/atlas/runtime-global-order-aware/`. Pointwise observed-order gating\nreduces median uncertainty inflation to approximately 1.7–2.3 times actual\nfinest-reference error, but only about 45–52% of the worst-case samples qualify.\nGrouping samples by BAB-CS anchor epoch raises the worst common qualified-sample\nfraction to 69–83% with median inflation of approximately 1.4–1.7 times, but\neffective reference-estimator coverage remains only 39–54%. A maximum-discrepancy\nepoch envelope raises reference coverage but also raises median inflation to\nroughly 3–10 times and tail inflation as high as about 164 times. All rejected\nepochs remain uncovered. No order-aware variant is promoted.\n\nThe signed statewise four-level experiment is now complete and retained under\n`artifacts/atlas/runtime-global-statewise-four-level/`. It preserves each\nstate's error direction, compares adjacent observed orders, checks leading-error\ncoefficient stability, and compares two adjacent extrapolated trajectories. A\nsample qualifies only when every state passes every gate.\n\n| Common four-level policy | Minimum sample qualification | Minimum state qualification | Minimum effective reference coverage | Worst median inflation | Worst p95 inflation |\n| --- | ---: | ---: | ---: | ---: | ---: |\n| 2/4/8/16 | 0.00% | 3.28% | 0.00% | 3.63x | 33.28x |\n| 4/8/16/32 | 0.22% | 1.70% | 0.22% | 3.94x | 97.39x |\n\nOnly 292 of 14,238 eligible sample-policy evaluations qualified. Signed\ndifference inconsistency caused 74,173 state rejections, while only 287 state\nrejections reached a direct numerical-difference floor. Nearly every adaptive\nBAB-CS sample required interpolation from at least one refined trajectory, but\nthe 18 evaluations at common native endpoints also failed sign or order gates.\nInterpolation therefore contributes to the problem but does not explain it\nalone. The stronger scaling failure is the joint-state requirement: as coupled\nstate count grows, one unstable state rejects the complete system sample. No\nstatewise four-level policy is promoted.\n\nThe epoch-aligned statewise experiment is now complete and retained under\n`artifacts/atlas/runtime-global-statewise-epoch/`. Each refinement integrates\nwith 2, 4, 8, 16, or 32 local substeps inside every BAB-CS diagnostic interval,\nso every comparison is native without collapsing the refinement factors onto an\nidentical output grid. Redundant periodic replay is disabled for these already\nimplicit offline authorities, while forced event re-anchors remain available.\n\n| Common four-level policy | Qualified epochs | Qualified state epochs | Qualified samples | Minimum effective reference coverage | Worst useful-case median inflation | Worst useful-case p95 inflation |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n| 2/4/8/16 | 13/483 | 85/3,630 | 193/7,119 | 0.00% | 1.00x | 16,532.33x |\n| 4/8/16/32 | 49/483 | 412/3,630 | 725/7,119 | 0.00% | 1.00x | 2.60x |\n\nThe finer policy qualifies 12 of 40 RL epochs and 3 of 42 RC epochs across each\nreplicated size, but its reference-error estimates remain slightly below the\nindependent authority error and therefore cover none of those qualified samples\nwithout an added safety multiplier. The size-one coupled RC ring reaches 1.69%\neffective reference coverage. Coupled sizes 4 and 16 qualify no complete epoch,\neven though 63 of 368 and 30 of 1,488 state epochs respectively qualify. The\ncommon fail-closed frontier is empty. Native integration therefore proves that\ninterpolation was not the root cause; joint-state asymptotic instability remains.\n\nThe mode-aligned experiment is now complete and retained under\n`artifacts/atlas/runtime-global-modal-epoch/`. It admits only homogeneous-unit,\nsmooth linear circuits with a symmetric differential Jacobian. A deterministic\nJacobi eigendecomposition must pass symmetry, residual, orthogonality, and sweep\nlimits. Repeated eigenvalues remain grouped, and reconstructed state errors use a\nconservative absolute basis transform.\n\n| Common four-level policy | Qualified joint epochs | Qualified modal-group epochs | Qualified samples | Minimum effective reference coverage | Worst reported median inflation | Worst reported p95 inflation |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n| 2/4/8/16 | 13/483 | 13/2,154 | 193/7,119 | 0.00% | 1.00x | 16,532.33x |\n| 4/8/16/32 | 50/483 | 209/2,154 | 740/7,119 | 0.00% | 1.00x | 9.41x |\n\nThe finer modal policy adds one qualified size-four coupled RC epoch, covering 15\nof 1,368 samples with 0.51% effective reference coverage and 0.88% effective\ntotal coverage. Size 16 improves from 30 qualified state epochs to 96 qualified\nmodal-group epochs but still qualifies no complete system epoch. RC and RL\nresults remain unchanged, confirming invariance for their repeated subspaces.\nThe common fail-closed frontier remains empty, so no modal policy is promoted.\n\nThe temporally aligned modal experiment is now complete and retained under\n`artifacts/atlas/runtime-global-temporal-modal-epoch/`. It permits a lag of at\nmost one diagnostic sample, only for scalar modal groups with one unique,\nmonotone, one-to-one zero-crossing match. Direction cosines use the common\nretained interval; observed order, coefficient agreement, extrapolant residual,\nerror estimates, and reconstructed-state bounds remain unshifted.\n\n| Common four-level policy | Qualified joint epochs | Qualified modal-group epochs | Qualified samples | Alignment attempts | Unique crossing matches | Alignments applied | Discarded endpoints |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n| 2/4/8/16 | 13/483 | 13/2,154 | 193/7,119 | 1,861 | 1 | 0 | 3 |\n| 4/8/16/32 | 50/483 | 209/2,154 | 740/7,119 | 1,844 | 3 | 0 | 6 |\n\nEvery qualification, coverage, and inflation result is identical to the\nunshifted modal study. Under the finer policy, 1,400 attempted groups have no\ncrossing evidence, 304 exhibit sign chatter, 128 repeated modal subspaces retain\nthe unshifted fallback, and 9 have no one-to-one crossing match. The three\nuniquely matched scalar groups still fail the aligned left-direction cosine\ngate. The common fail-closed frontier remains empty, so the temporal policy is\nnot promoted.\n\nThe five-level two-term modal experiment is now complete and retained under\n`artifacts/atlas/runtime-global-two-term-modal/`. Qualified Loop 5G groups keep\ntheir existing estimate. Rejected groups fit\n`Y_f = Y_inf + C f^-2 + D f^-q` with factors 2 through 16, while factor 32 is\nexcluded from fitting and used as the independent holdout. Secondary orders 3\nand 4 are common policies across all nine cases.\n\n| Common policy | Qualified joint epochs | Qualified modal-group epochs | Qualified samples | Loop 5G fallback groups | Fits attempted | Two-term fits qualified | Maximum training residual ratio | Maximum holdout residual ratio |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n| `p=2, q=3` | 50/483 | 209/2,154 | 740/7,119 | 209 | 1,945 | 0 | 4.93 | 1,573.78 |\n| `p=2, q=4` | 50/483 | 209/2,154 | 740/7,119 | 209 | 1,945 | 0 | 4.76 | 2,025.41 |\n\nThe deterministic condition numbers, 230.85 and 269.69, remain below the common\nlimit of 1,000. Conditioning is therefore not the failure. For both policies,\n1,656 groups fail the training-residual gate. The factor-32 holdout rejects 242\nadditional `q=3` groups and 232 `q=4` groups. No rejected Loop 5G group is\nrecovered, every coverage and inflation result remains unchanged, and the common\nfail-closed frontier remains empty. The two-term policies are not promoted.\n\nThe next highest-gain diagnostic is a finer-level asymptotic-entry ladder. It\nwill add native factors 64 and 128, test one-term modal policies ending at each\nnew level, and repeat the two-term fit with factor 128 reserved as the holdout.\nThis directly tests whether factor 32 remains pre-asymptotic, while publishing\nthe added integration work and every numerical-floor rejection instead of\nrelaxing a residual gate or tuning a family-specific multiplier.\n\n## Retained Fixed-Config Publication Results\n\nThe following table is the earlier publication-profile, shared-timestep\nbaseline. It remains useful as historical fixed-configuration evidence, but it\ndoes not represent the optimized fixed-accuracy profile described above.\n\n| Case | Family | Size | MNA unknowns | Status | BAB-CS median (s) | ngspice median (s) | Speedup × | BAB-CS scaled error | ngspice scaled error |\n| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |\n| rc_bank-n001 | rc_bank | 1 | 5 | success | 0.00944445 | 0.000628621 | 0.0665598 | 401.884 | 23.593 |\n| rc_bank-n002 | rc_bank | 2 | 8 | success | 0.0107041 | 0.000634121 | 0.0592412 | 401.884 | 23.593 |\n| rc_bank-n004 | rc_bank | 4 | 14 | success | 0.013238 | 0.000646564 | 0.0488415 | 401.884 | 23.593 |\n| rc_bank-n008 | rc_bank | 8 | 26 | success | 0.0196408 | 0.000673314 | 0.0342813 | 401.884 | 23.593 |\n| rc_bank-n016 | rc_bank | 16 | 50 | success | 0.0367185 | 0.000732295 | 0.0199435 | 401.884 | 23.593 |\n| rc_bank-n032 | rc_bank | 32 | 98 | success | 0.0912027 | 0.000832661 | 0.00912978 | 401.884 | 23.593 |\n| rc_bank-n064 | rc_bank | 64 | 194 | success | 0.291845 | 0.00104237 | 0.00357165 | 401.884 | 23.593 |\n| rl_bank-n001 | rl_bank | 1 | 4 | success | 0.00921964 | 0.000650392 | 0.0705442 | 379.119 | 23.4069 |\n| rl_bank-n002 | rl_bank | 2 | 6 | success | 0.0101999 | 0.000658237 | 0.0645337 | 379.119 | 23.4069 |\n| rl_bank-n004 | rl_bank | 4 | 10 | success | 0.0118644 | 0.000672633 | 0.0566933 | 379.119 | 23.4069 |\n| rl_bank-n008 | rl_bank | 8 | 18 | success | 0.0157166 | 0.000714491 | 0.0454608 | 379.119 | 23.4069 |\n| rl_bank-n016 | rl_bank | 16 | 34 | success | 0.0253709 | 0.000784782 | 0.0309324 | 379.119 | 23.4069 |\n| rl_bank-n032 | rl_bank | 32 | 66 | success | 0.0539536 | 0.000922087 | 0.0170904 | 379.119 | 23.4069 |\n| rl_bank-n064 | rl_bank | 64 | 130 | success | 0.17097 | 0.00120273 | 0.00703473 | 379.119 | 23.4069 |\n| diode_rc_bank-n001 | diode_rc_bank | 1 | 5 | success | 0.0325329 | 0.00100245 | 0.0308135 | 7819.57 | 6896.65 |\n| diode_rc_bank-n002 | diode_rc_bank | 2 | 8 | success | 0.0452995 | 0.0010301 | 0.0227398 | 7819.57 | 6896.65 |\n| diode_rc_bank-n004 | diode_rc_bank | 4 | 14 | success | 0.0735071 | 0.00108279 | 0.0147304 | 7819.57 | 6896.65 |\n| diode_rc_bank-n008 | diode_rc_bank | 8 | 26 | success | 0.165712 | 0.00119101 | 0.00718724 | 7819.57 | 6896.65 |\n| diode_rc_bank-n016 | diode_rc_bank | 16 | 50 | success | 0.529582 | 0.00139088 | 0.00262637 | 7819.57 | 6896.65 |\n| diode_rc_bank-n032 | diode_rc_bank | 32 | 98 | success | 2.31809 | 0.00179484 | 0.000774277 | 7819.57 | 6896.65 |\n| diode_rc_bank-n064 | diode_rc_bank | 64 | 194 | success | 12.7876 | 0.00261811 | 0.000204738 | 7819.57 | 6896.65 |\n| switched_rc_bank-n001 | switched_rc_bank | 1 | 6 | success | 0.0104565 | 0.000895806 | 0.0856697 | 9655.58 | 9899.94 |\n| switched_rc_bank-n002 | switched_rc_bank | 2 | 10 | success | 0.0132709 | 0.000915242 | 0.0689659 | 9653.94 | 9899.94 |\n| switched_rc_bank-n004 | switched_rc_bank | 4 | 18 | success | 0.0177245 | 0.000963402 | 0.0543542 | 9653.94 | 9899.94 |\n| switched_rc_bank-n008 | switched_rc_bank | 8 | 34 | success | 0.029396 | 0.00104904 | 0.0356865 | 9653.94 | 9899.94 |\n| switched_rc_bank-n016 | switched_rc_bank | 16 | 66 | success | 0.0645797 | 0.00120418 | 0.0186464 | 9653.94 | 9899.94 |\n| switched_rc_bank-n032 | switched_rc_bank | 32 | 130 | success | 0.193123 | 0.00152802 | 0.00791215 | 9653.94 | 9899.94 |\n| switched_rc_bank-n064 | switched_rc_bank | 64 | 258 | success | 0.780528 | 0.00225641 | 0.00289088 | 9653.94 | 9899.94 |\n| rc_step | — | — | 5 | success | 0.00117379 | 0.000241288 | 0.205563 | 868.923 | 37.9744 |\n| rc_discharge | — | — | 3 | success | 0.00846995 | 0.000619442 | 0.0731341 | 19.7138 | 5.9283 |\n| driven_rc | — | — | 5 | success | 0.0175035 | 0.000977578 | 0.0558504 | 6848.59 | 381.693 |\n| current_driven_rc | — | — | 3 | success | 0.0204109 | 0.00103566 | 0.0507406 | 2767.5 | 261.593 |\n| rl_step | — | — | 4 | success | 0.00117793 | 0.000251337 | 0.213372 | 787.822 | 37.4763 |\n| rl_decay | — | — | 2 | success | 0.0132628 | 0.000961558 | 0.0725002 | 19.8478 | 8.79759 |\n| lc_long | — | — | 4 | success | 0.356588 | 0.0100556 | 0.0281995 | 8934.88 | 9928.92 |\n| lc_offset | — | — | 4 | success | 0.140716 | 0.00507391 | 0.0360578 | 1270.58 | 10242.1 |\n| rlc_damped | — | — | 4 | success | 0.0379399 | 0.00117144 | 0.0308762 | 3726 | 8938.68 |\n| rlc_overdamped | — | — | 4 | success | 0.020308 | 0.000964434 | 0.0474903 | 6097.47 | 940.378 |\n| rlc_driven | — | — | 7 | success | 0.14203 | 0.00355237 | 0.0250114 | 473.21 | 255.55 |\n| diode_clip | — | — | 5 | success | 0.0751269 | 0.00224355 | 0.0298635 | 3134.89 | 224.54 |\n| diode_rectifier | — | — | 6 | success | 0.286595 | 0.0083782 | 0.0292336 | 54.0649 | 214.644 |\n| diode_bias_recovery | — | — | 5 | success | 0.120965 | 0.0043109 | 0.0356376 | 41.7189 | 299.271 |\n| switched_rc | — | — | 5 | success | 0.0142059 | 0.000831427 | 0.058527 | 9481.29 | 7109.62 |\n| switched_rl | — | — | 5 | success | 0.0820105 | 0.00265859 | 0.0324177 | 30.7663 | 3161.31 |\n| switched_rlc | — | — | 8 | success | 0.244519 | 0.00335301 | 0.0137127 | 11351.2 | 11476.4 |\n| buck_like_reduced_order | — | — | 7 | success | 0.0942436 | 0.00366604 | 0.0388996 | 261.528 | 3198.53 |\n| h_bridge_rl_reduced_order | — | — | 6 | success | 0.0778088 | 0.00405196 | 0.0520758 | 10032.1 | 10001.2 |\n| dc_link_rlc_reduced_order | — | — | 8 | success | 0.0726296 | 0.00251481 | 0.0346251 | 651.722 | 3166.67 |\n\n## Measurement Contract\n\n- Machine: `AMD Ryzen 9 7900X 12-Core Processor` on `7.1.3-2-cachyos`.\n- Profile: `publication` with 5 warmups, 15 repeats, and 3 rounds.\n- Accuracy grid: 201 shared samples with absolute tolerance `1e-08` and relative tolerance `0.0001`.\n- BAB-CS wheel SHA-256: `ca5d648e60dfd9923deadc85fb304b45dc9ecf87aecc982a369d3766542806f2`.\n- ngspice: `ngspice-46 : Circuit level simulation program`.\n- Runtime: analysis-only medians use BAB-CS `perf_counter_ns` timing around `Simulator.run` and ngspice `Total analysis time (seconds)` from `rusage all`.\n- Memory: both fresh child processes use GNU Time maximum RSS in kibibytes.\n\n## Claim Boundary\n\nRuntime evidence characterizes one recorded machine and software snapshot. It is not a universal speed or correctness claim, and ngspice is not treated as an exact physical oracle.\n",
      "order": 6,
      "path": "NGSPICE_RUNTIME_BENCHMARK.md",
      "readingMinutes": 15,
      "sha256": "426905a5cd1839658d561bb222e8002d7d686b2035a64a26f4a0966f4ee1560b",
      "summary": "This report records a same-machine comparison between Bounded-Authority-Based Circuit Simulation (BAB-CS) and ngspice. The horizontal size coordinate is the model-declared Modified Nodal Analysis (MNA) count: BAB-CS dynamic states plus…",
      "title": "BAB-CS versus ngspice Runtime Benchmark",
      "wordCount": 3099
    },
    {
      "category": "Tests and Comparisons",
      "conceptIds": [
        "replay",
        "anchor",
        "recursive-bound",
        "residual",
        "reduced-order-model",
        "deterministic-evidence",
        "fixed-step",
        "fixed-accuracy",
        "fixed-work",
        "phase-error",
        "empirical-coverage",
        "source-wheel-equivalence",
        "python-wheel",
        "mna",
        "rc",
        "rl",
        "rlc",
        "lc",
        "dc",
        "be",
        "klu",
        "scipy",
        "ulp",
        "json",
        "csv",
        "svg",
        "sha256",
        "ngspice"
      ],
      "headings": [
        {
          "id": "observatory-atlas-sandbox-and-lab-implementation-audit",
          "level": 1,
          "text": "Observatory, Atlas, Sandbox, and Lab Implementation Audit"
        },
        {
          "id": "audit-status",
          "level": 2,
          "text": "Audit Status"
        },
        {
          "id": "evidence-snapshot",
          "level": 2,
          "text": "Evidence Snapshot"
        },
        {
          "id": "requirement-to-evidence-matrix",
          "level": 2,
          "text": "Requirement-to-Evidence Matrix"
        },
        {
          "id": "deterministic-artifact-evidence",
          "level": 2,
          "text": "Deterministic Artifact Evidence"
        },
        {
          "id": "selection-and-rejection-review",
          "level": 2,
          "text": "Selection and Rejection Review"
        },
        {
          "id": "coverage-review",
          "level": 2,
          "text": "Coverage Review"
        },
        {
          "id": "qualification-and-promotion-boundary",
          "level": 2,
          "text": "Qualification and Promotion Boundary"
        },
        {
          "id": "2026-08-27-expansion-addendum",
          "level": 2,
          "text": "2026-08-27 Expansion Addendum"
        }
      ],
      "kind": "Evidence",
      "markdown": "# Observatory, Atlas, Sandbox, and Lab Implementation Audit\n\n## Audit Status\n\nThis audit records the implementation and development qualification state on\nAugust 27, 2026. It covers\n`OBSERVATORY_ATLAS_SANDBOX_LAB_IMPLEMENTATION_PLAN.md` and distinguishes\nimplemented functionality from release promotion.\n\nThe automated implementation is complete. The current worktree is dirty, so\nthe wheel and source/wheel results below are explicitly development evidence,\nnot release evidence. No exact commit has been selected, no human has approved\nthe exact source and wheel hashes, and no publication authority is implied.\n\n## Evidence Snapshot\n\n| Field | Value |\n| --- | --- |\n| Git `HEAD` | `c280b885ce54205805a9046a98430948498a73d9` |\n| Source-tree SHA-256 | `74ccc39a853f3410f898a6550268eb85136b58045dba5966907dedcfb1c41657` |\n| Source scope | 141 tracked or untracked non-ignored files, excluding generated evidence and evidence-only audit documents |\n| Dirty state | `true`; development evidence only |\n| Python | CPython 3.14.6 |\n| Platform | Linux 7.1.3-2-cachyos, x86-64, glibc 2.43 |\n| Optional backends | SciPy available; SuiteSparse KLU available |\n| Test surface | 276 test methods in 25 modules |\n| Complete suite | 276 passed, zero skipped, 64.203 seconds |\n\nThe complete suite ran with both `BABCS_LONG_TESTS=1` and\n`BABCS_VERY_LONG_TESTS=1`, so it included the 1,000-period LC qualification as\nwell as the available SciPy and KLU tests. `compileall` and strict JSON parsing\nalso passed.\n\n## Requirement-to-Evidence Matrix\n\n| Requirement | Implementation owner | Deterministic verification | Status |\n| --- | --- | --- | --- |\n| Shared versioned experiment records, stable row IDs, reason taxonomy, applicability, fixed-accuracy and fixed-work selection | `tools/experiment_records.py`, `benchmarks/schemas/` | `tests/test_experiment_records.py`, comparison compatibility tests | Implemented and passed |\n| RC, RL, RLC, LC, diode clip, and switched RC across all seven candidates | `benchmarks/observatory/manifest.json`, `tools/method_observatory.py` | 126 expected rows, 126 actual rows, 126 successful rows, no missing, duplicate, or unexpected rows | Implemented and passed |\n| Fixed-step, fixed-accuracy, and fixed-work reports without interpolation | Observatory JSON/CSV/SVG/Markdown writers | Every selected summary links to a measured `row_id`; `no_qualifying_row` remains explicit | Implemented and passed |\n| Actual authority error, recursive internal bound, anchor deviation, phase, energy, empirical coverage, fallback, and rejection causes | `tools/bound_coverage_atlas.py`, `benchmarks/atlas/manifest.json` | 87,874 accepted samples, 3,934 anchors, 3,040 cause records; exact diagnostic/work reconciliation | Implemented and passed |\n| Simplified buck-like converter | `examples/power_stage/buck_like_reduced_order.json` | Event, continuity, residual, energy, authority, determinism, refined-authority, and installed-wheel checks | Implemented and passed |\n| Scheduled H-bridge RL load | `examples/power_stage/h_bridge_rl_reduced_order.json` | Dead time, no leg overlap, polarity reversal, event/replay, residual, determinism, refined-authority, and installed-wheel checks | Implemented and passed |\n| DC-link RLC startup and interruption | `examples/power_stage/dc_link_rlc_reduced_order.json` | Startup/interruption events, diode conduction, post-interrupt energy decay, residual, determinism, refined-authority, and installed-wheel checks | Implemented and passed |\n| Exact reduced-order/non-production classification | Power-stage input metadata, `examples/power_stage/README.md`, `docs/POWER_STAGE_SANDBOX.md` | `tests/test_power_stage_examples.py` requires the exact classification text | Implemented and passed |\n| MNA exercise | `lab/01-mna/` | Dynamic/algebraic ownership and residual assertions | Implemented and passed |\n| Convergence exercise | `lab/02-convergence/` | Three measured refinements; observed orders 2.00117 and 2.00029 | Implemented and passed |\n| Phase-versus-energy exercise | `lab/03-phase-versus-energy/` | Separate phase and energy evidence for backward Euler and trapezoidal over ten LC periods | Implemented and passed |\n| Shadow-authority exercise | `lab/04-shadow-authority/` | Identical accepted time grid; maximum state delta `1.3877787807814457e-17` below recorded 16-ULP tolerance `3.552713678800501e-15` | Implemented and passed |\n| Deterministic packaging exercise | `lab/05-deterministic-packaging/` | Two byte-identical wheels, fixed timestamps, fixed permissions, canonical member order | Implemented and passed as development evidence |\n| Source-versus-wheel equivalence | `lab/06-source-wheel-equivalence/` | Isolated module and console runs match source byte-for-byte for RC, switched RC, and all three power-stage cases; installed-wheel Observatory smoke also matches | Implemented and passed as development evidence |\n| Fixture updates are review-controlled | `lab/support/verify.py`, `lab/fixtures/verification-baseline.json` | Updates require `--update-fixtures --exercise all`; ordinary runs do not modify the fixture | Implemented and passed |\n| Deterministic integration generation | Observatory, atlas, power-stage, and lab generators | Two independent output directories compared byte-for-byte for every deterministic artifact | Implemented and passed |\n| Documentation and claim boundaries | `README.md`, `docs/index.md`, comparison/error/roadmap/reproducibility/current-work documents, `CHANGELOG.md`, `RELEASE.md` | Documentation review plus exact classification and release-boundary tests | Implemented |\n\n## Deterministic Artifact Evidence\n\nTwo full runs in separate temporary directories produced byte-identical files.\nPrincipal report hashes are:\n\n| Artifact | SHA-256 |\n| --- | --- |\n| Method Observatory JSON | `90c5446ece34eec9e61d7a93c40105c83be4907734f5cce2c147103f5ddad5a0` |\n| Bound Coverage Atlas JSON | `f24ecff23786ab510bbe91207074742c601c5a53971b5bba3e3ea6aa3d48a0a1` |\n| Power-stage comparison JSON | `cfed4ea836e8252dc2f29e1c787767355ea6310942473c4bb03b3e84ef0c36c5` |\n| Full teaching-lab JSON | `0b6383a91ee51b6d075eedd0075f34e4b1b601ee61a3c3ea071ebf0e308320de` |\n| Review-controlled lab fixture | `ab021d66a32ae6397775eacb2f28bc536b9016fd031aaaaee0a9307198a76100` |\n| Development wheel, both builds | `ca5d648e60dfd9923deadc85fb304b45dc9ecf87aecc982a369d3766542806f2` |\n\nThe observatory CSV views, observatory SVG and Markdown, atlas sample CSV, all\nfour atlas SVGs, and power-stage CSV/SVG also matched byte-for-byte. Timing was\nnot included in deterministic correctness evidence.\n\n## Selection and Rejection Review\n\nThe fixed-accuracy view contains 126 target rows: 85 select a measured source\nrow and 41 report `no_qualifying_row`. The fixed-work view contains 168 budget\nrows: 65 select a measured source row and 103 report `no_qualifying_row`.\nThese are expected outcomes of the declared measured grids. They do not hide a\nfailed run, and no interpolation or extrapolation fills them.\n\nAll 3,040 Observatory rejected attempts are represented in the atlas cause\ntable with requested and suggested steps:\n\n- 2,972 `candidate_amplification_domain_exceeded` attempts, normalized as\n  `candidate_nonconvergence`; and\n- 68 `independent_re_anchor_failed` attempts, normalized as `replay_failure`.\n\nThe 57 power-stage rows all succeed after controlled retry. Their 3,761 rejected\nattempts are retained rather than discarded:\n\n- 3,715 candidate amplification-domain rejections;\n- 27 reference-solve failures;\n- 14 embedded-candidate-cap rejections;\n- 3 independent re-anchor failures; and\n- 2 predictor/reference-cap rejections.\n\nThese counts characterize the selected experiments. They are not generalized\nrobustness probabilities.\n\n## Coverage Review\n\nThe atlas marks 83,846 samples eligible for empirical recursive-bound coverage;\n3,793 are covered. Individual row fractions range from 0.0 to 1.0. This low and\ncase-dependent measured coverage is intentionally reported, not tuned away.\nIt confirms that the recursive internal bound is diagnostic evidence under the\nimplemented model, not a universal formal enclosure. Actual authority error,\nauthority-epoch drift, anchor deviation, phase, and energy remain separate.\n\n## Qualification and Promotion Boundary\n\nThe implementation, source tests, optional-backend tests, long-horizon tests,\ndeterministic reports, development wheel reproducibility, installed-wheel case\nequivalence, and installed-wheel observatory smoke all pass on the exact dirty\nsource-tree hash recorded above.\n\nThe following promotion requirements remain deliberately open:\n\n1. commit the reviewed source so the tree is clean and the exact commit is\n   selectable;\n2. rerun the complete qualification and deterministic artifact generation on\n   that clean exact commit;\n3. record the resulting exact source, wheel, manifest, report, workflow, and\n   environment hashes in release evidence; and\n4. obtain explicit human approval of the exact commit and artifacts.\n\nTherefore the facilities requested by the implementation plan are present and\nautomatically qualified in development, but `v1.1.0` is not release-qualified,\napproved, tagged, or published by this audit.\n\n## 2026-08-27 Expansion Addendum\n\nThis audit records the original six-exercise and four-mapping implementation\nbaseline. It is retained as historical evidence and is not rewritten to imply\nthat the larger surface existed during that earlier qualification run.\n\nThe current additive expansion is owned by\n`NGSPICE_AND_TEACHING_TUTORIAL_EXPANSION_PLAN.md`. That plan defines 20\nmanifest-owned ngspice mappings, ten executable teaching exercises, ten\ntutorial documents, and 13 generated tutorial/comparison SVG figures. Current\ncounts and current validation evidence must be read from that expansion record,\nthe authoritative manifests, and fresh test output rather than inferred from\nthe historical counts above.\n",
      "order": 7,
      "path": "OBSERVATORY_ATLAS_SANDBOX_LAB_IMPLEMENTATION_AUDIT.md",
      "readingMinutes": 6,
      "sha256": "043e28cc273207cfbc71ad00a4b75bdbba589e9882739308fe8e887c412c3433",
      "summary": "This audit records the implementation and development qualification state on August 27, 2026. It covers OBSERVATORY_ATLAS_SANDBOX_LAB_IMPLEMENTATION_PLAN.md and distinguishes implemented functionality from release promotion.",
      "title": "Observatory, Atlas, Sandbox, and Lab Implementation Audit",
      "wordCount": 1136
    },
    {
      "category": "Tests and Comparisons",
      "conceptIds": [
        "babcs",
        "replay",
        "anchor",
        "reduced-order-model",
        "deterministic-evidence",
        "fail-closed",
        "python-wheel",
        "rlc",
        "pwl",
        "rms",
        "json",
        "sha256",
        "ngspice"
      ],
      "headings": [
        {
          "id": "bounded-authority-based-circuit-simulation-external-comparison",
          "level": 1,
          "text": "Bounded-Authority-Based-Circuit-Simulation External Comparison"
        },
        {
          "id": "scope",
          "level": 2,
          "text": "Scope"
        },
        {
          "id": "prerequisite",
          "level": 2,
          "text": "Prerequisite"
        },
        {
          "id": "run",
          "level": 2,
          "text": "Run"
        },
        {
          "id": "translation-contract",
          "level": 2,
          "text": "Translation Contract"
        },
        {
          "id": "evidence-record",
          "level": 2,
          "text": "Evidence Record"
        },
        {
          "id": "interpretation",
          "level": 2,
          "text": "Interpretation"
        }
      ],
      "kind": "Evidence",
      "markdown": "# Bounded-Authority-Based-Circuit-Simulation External Comparison\n\n## Scope\n\n`tools/compare_external.py` compares one BAB-CS JSON case with `ngspice` when\nthe circuit can be translated without changing its modeled semantics. This is\ncross-implementation evidence, not an oracle and not proof of exact physical\ntrajectory error.\n\nThe adapter currently maps resistors, capacitors, inductors, independent\nvoltage/current sources, constant/sine/pulse/PWL waveforms, Shockley diodes with\nthermal voltage preserved through ngspice ideality, and time-controlled\nresistive switches. Unsupported element or parameter mappings fail closed.\n\n## Prerequisite\n\nInstall `ngspice` and verify it is available:\n\n```bash\nngspice --version\n```\n\nThe executable can be overridden with `--executable PATH`.\n\n## Run\n\n```bash\nPYTHONPATH=src python tools/run_external_suite.py \\\n  benchmarks/external/manifest.json \\\n  --output-root artifacts/external\n```\n\nThe manifest owns 20 cases across first-order linear, resonant and RLC,\nnonlinear diode, scheduled switching, and reduced-order power-stage families.\nSee the [20-case mapping atlas](NGSPICE_CASE_ATLAS.md) for every case, graph,\nengineering question, and claim boundary. Output paths refuse overwrite unless\n`--overwrite` is provided.\n\n## Translation Contract\n\nThe generated netlist uses the case's nominal step and stop time, preserves\ninitial capacitor voltage and inductor current, and evaluates the same dynamic\nstate coordinates used by BAB-CS. Capacitor voltages are exported before\ninductor currents to match BAB-CS canonical state ownership even when the input\nelements are listed in another order. Explicit `bab_state_N` vectors are\ncreated after `tran` so `wrdata` has a stable one-time-column-plus-state-columns\nshape.\n\nThe adapter validates finite, strictly increasing output times and the exact\ncolumn count. Missing executables, failed processes, malformed output,\nunsupported devices, or non-equivalent parameters terminate the comparison.\n\n## Evidence Record\n\nThe JSON report contains:\n\n- `ngspice` version and executed command.\n- Source commit, dirty state, deterministic source-tree SHA-256, and environment.\n- Input-case SHA-256.\n- Generated-netlist SHA-256.\n- Raw-output and external-log SHA-256 values.\n- State names and sample count.\n- Per-state final, maximum, RMS, and scaled differences.\n- Complete BAB-CS and simulation configuration.\n- BAB-CS diagnostic summary.\n- An explicit claim-boundary statement.\n\nThe suite writes those four files for every case plus `suite.json`: 81 files for\nthe complete 20-case set. Preserve the JSON, generated netlist, raw data, and\nlog together. Hash the files and associate them with the exact source commit\nbefore using them in a release review.\n\n## Interpretation\n\nDifferences may arise from integration method, event conventions, nonlinear\niteration, source interpolation, or device-model details. A small difference\nsupports implementation consistency for the mapped case. A large difference\nrequires investigation; it does not by itself identify which implementation is\nwrong.\n\nExternal comparison is intentionally separate from analytic truth and refined\nreplay. It must not replace analytic convergence tests, independent anchor\nchecks, runtime failure-gate tests, or installed-wheel qualification.\n",
      "order": 8,
      "path": "EXTERNAL_COMPARISON.md",
      "readingMinutes": 2,
      "sha256": "fb52762bd7f7611305337e027b916d93ceb9e2c2a9facaaedc7624d4b01e7591",
      "summary": "tools/compare_external.py compares one BAB-CS JSON case with ngspice when the circuit can be translated without changing its modeled semantics. This is cross-implementation evidence, not an oracle and not proof of exact physical…",
      "title": "Bounded-Authority-Based-Circuit-Simulation External Comparison",
      "wordCount": 415
    },
    {
      "category": "Tests and Comparisons",
      "conceptIds": [
        "babcs",
        "projection",
        "replay",
        "anchor",
        "residual",
        "jacobian",
        "passivity",
        "deterministic-evidence",
        "fixed-step",
        "fixed-accuracy",
        "fixed-work",
        "phase-error",
        "shadow-mode",
        "fail-closed",
        "python-wheel",
        "rc",
        "rl",
        "rlc",
        "lc",
        "pwl",
        "ab2",
        "adams-bashforth",
        "be",
        "bdf2",
        "json",
        "csv",
        "svg",
        "sha256",
        "ci",
        "yaml",
        "ngspice"
      ],
      "headings": [
        {
          "id": "bounded-authority-based-circuit-simulation-tests-and-comparisons-qualification-audit",
          "level": 1,
          "text": "Bounded-Authority-Based-Circuit-Simulation Tests and Comparisons Qualification Audit"
        },
        {
          "id": "status",
          "level": 2,
          "text": "Status"
        },
        {
          "id": "qualified-snapshot",
          "level": 2,
          "text": "Qualified Snapshot"
        },
        {
          "id": "validation-results",
          "level": 2,
          "text": "Validation Results"
        },
        {
          "id": "source-suite",
          "level": 3,
          "text": "Source Suite"
        },
        {
          "id": "deterministic-method-matrix",
          "level": 3,
          "text": "Deterministic Method Matrix"
        },
        {
          "id": "long-horizon-characterization",
          "level": 3,
          "text": "Long-Horizon Characterization"
        },
        {
          "id": "external-ngspice-evidence",
          "level": 3,
          "text": "External `ngspice` Evidence"
        },
        {
          "id": "installed-wheel",
          "level": 3,
          "text": "Installed Wheel"
        },
        {
          "id": "work-package-audit",
          "level": 2,
          "text": "Work-Package Audit"
        },
        {
          "id": "tc-001-shared-qualification-support-achieved",
          "level": 3,
          "text": "TC-001 — Shared Qualification Support: Achieved"
        },
        {
          "id": "tc-002-integrator-and-configuration-boundaries-achieved",
          "level": 3,
          "text": "TC-002 — Integrator and Configuration Boundaries: Achieved"
        },
        {
          "id": "tc-003-hard-failure-gates-achieved",
          "level": 3,
          "text": "TC-003 — Hard Failure Gates: Achieved"
        },
        {
          "id": "tc-004-bound-recurrence-verification-achieved",
          "level": 3,
          "text": "TC-004 — Bound Recurrence Verification: Achieved"
        },
        {
          "id": "tc-005-analytic-accuracy-and-convergence-achieved",
          "level": 3,
          "text": "TC-005 — Analytic Accuracy and Convergence: Achieved"
        },
        {
          "id": "tc-006-long-horizon-bounds-and-passivity-achieved",
          "level": 3,
          "text": "TC-006 — Long-Horizon Bounds and Passivity: Achieved"
        },
        {
          "id": "tc-007-event-and-nonlinear-qualification-achieved",
          "level": 3,
          "text": "TC-007 — Event and Nonlinear Qualification: Achieved"
        },
        {
          "id": "tc-008-comparison-runner-achieved",
          "level": 3,
          "text": "TC-008 — Comparison Runner: Achieved"
        },
        {
          "id": "tc-009-diagnostic-extension-achieved",
          "level": 3,
          "text": "TC-009 — Diagnostic Extension: Achieved"
        },
        {
          "id": "tc-010-optional-external-simulator-comparison-achieved",
          "level": 3,
          "text": "TC-010 — Optional External Simulator Comparison: Achieved"
        },
        {
          "id": "tc-011-ci-qualification-tiers-achieved",
          "level": 3,
          "text": "TC-011 — CI Qualification Tiers: Achieved"
        },
        {
          "id": "tc-012-documentation-and-evidence-audit-achieved",
          "level": 3,
          "text": "TC-012 — Documentation and Evidence Audit: Achieved"
        },
        {
          "id": "completion-gate-audit",
          "level": 2,
          "text": "Completion-Gate Audit"
        },
        {
          "id": "known-limitations",
          "level": 2,
          "text": "Known Limitations"
        }
      ],
      "kind": "Evidence",
      "markdown": "# Bounded-Authority-Based-Circuit-Simulation Tests and Comparisons Qualification Audit\n\nAudit date: August 24, 2026\n\n> **Historical-scope notice:** This audit qualifies the four-case external\n> mapping surface that existed on August 24, 2026. The current additive\n> 20-case ngspice inventory, ten-exercise lab, tutorial set, and generated SVG\n> evidence are owned by `NGSPICE_AND_TEACHING_TUTORIAL_EXPANSION_PLAN.md` and\n> fresh validation output. The historical counts below are retained to preserve\n> exact-snapshot evidence; they are not the current repository totals.\n\n## Status\n\n- **Local implementation:** achieved against the committed source snapshot identified below.\n- **Local deterministic qualification:** achieved.\n- **Installed-wheel qualification:** achieved.\n- **Live external comparison:** achieved locally with `ngspice-46` and remotely\n  with `ngspice-42` for the four declared mappings.\n- **Remote GitHub workflow evidence:** achieved for the exact implementation\n  commit through CI, scheduled comparisons, and release qualification.\n- **Release publication:** not performed by this qualification change; publishing\n  remains a separate human-approved action.\n\nThis is an additive qualification audit. It does not rewrite\n`docs/BAB_CSV1_COMPLETION_AUDIT.md` or imply that the tests and comparison\nprogram was part of the original v1 release evidence.\n\n## Qualified Snapshot\n\n- Implementation base commit: `46b8ad886bb25445208099b4627f45f6a9da4d5b`\n- Qualified implementation commit:\n  `3dafe404d5a7d134c26f3a0d7fc73d7e3777dd95`\n- Working tree at qualification: clean.\n- Deterministic source-tree SHA-256:\n  `55b3a7464a2f76b2ddad157096b7eb348e4e85aeec0eb0f37166f2ec490e4458`\n- Source files in hash: 61.\n- Hash scope: Git tracked and untracked non-ignored files, excluding generated\n  `artifacts/`, `build/`, and `dist/` content and this self-referential audit.\n- Comparison manifest SHA-256:\n  `7b805a88a1cd86e7569ff0d9fa0dbbd5f9db2b6f3c841808af12062b4866d406`\n- Environment: CPython 3.14.6 on\n  `Linux-7.1.3-2-cachyos-x86_64-with-glibc2.43`.\n\n`tools/compare_methods.py` and `tools/compare_external.py` record the source\ncommit, dirty state, source-tree hash, source-file count, scope statement, and\nenvironment in each JSON report.\n\n## Validation Results\n\n### Source Suite\n\nCommand:\n\n```bash\npython -m compileall -q -f src tests tools\nBABCS_LONG_TESTS=1 BABCS_VERY_LONG_TESTS=1 \\\n  PYTHONPATH=src python -m unittest discover -s tests -v\n```\n\nResult: 97 tests passed, zero skipped, in 78.596 seconds.\n\nTest log SHA-256:\n`ef4be34f7be96c5ff2328cebf24e6d6b945603bd331a0804568dac97ec31686c`\n\nThe default pull-request tier was run across the complete declared Python\nmatrix in remote CI.\n\n```bash\nfor version in 3.11 3.12 3.13 3.14; do\n  \"python${version}\" -m compileall -q -f src tests tools\n  PYTHONPATH=src \"python${version}\" -m unittest discover -s tests -v\ndone\n```\n\nEach CPython 3.11 through 3.14 job passed 97 tests with the scheduled and\nrelease-only long-horizon cases skipped, matching the intended pull-request\ntier. The exact run is recorded under TC-011.\n\n### Deterministic Method Matrix\n\nThe full manifest ran twice without timing. Numerical JSON, CSV, and SVG were\nbyte-identical. A third run with three timing repeats produced identical\nnumerical artifacts and a separate timing report.\n\n- Cases: 8.\n- Results: 100.\n- Methods: active, backward Euler, BDF2, raw AB2, shadow, trapezoidal.\n- Authorities: analytic and independent refined replay.\n- Convergence analyses: 35.\n- Fixed-accuracy analyses: 105.\n- Fixed-work analyses: 140.\n- Maximum characterized waveform error across the complete mixed-method matrix:\n  `0.12802541939866408`; this is characterization, not a universal threshold.\n- Maximum deterministic work units: 129596.\n- Timing samples: 100 results with three repeats each.\n- Median timing range: `1.770298695191741e-05` to\n  `1.0386381130083464` seconds; timing is not a correctness gate.\n\nThe performance range above is from the local timed run. Final remote artifact\nhashes at the qualified implementation commit are:\n\n- Numerical JSON:\n  `d5f63ea03cff855952b2158ab447a97163ed25f4aab06f93e5881421e86e8e4e`\n- Flat CSV:\n  `0de55953c57faa4ceb6f43570fc1cdd9efacf1aa4b9e0d031bdf30745b433195`\n- SVG plot:\n  `98742d51cbc017b2dd08d5ec57ad280ed9390b2fd96c4b279ae2e5450a0c843b`\n- Timing JSON for this run:\n  `f26b12458dbbfa83bbfc0dbab453eec8944ccbeec90d49c9e4b885db3e7991e8`\n- Timed-run log:\n  `4686cb36196522a712671ba92ddc0198bad224137d22fbd1cb1fd9a29b6d5963`\n\nThe timing hash is provenance for this run only and is not expected to be\nreproducible across machines or loads.\n\n### Long-Horizon Characterization\n\nThe no-skip suite includes the 10-, 100-, and 1,000-period LC gates. The full\ncomparison matrix separately records sampled amplitude error, final phase error,\nrelative period error, relative energy span, anchor deviation, and empirical\nanchor-error-to-pre-reset-bound ratios.\n\nFor active LC at the declared matrix points:\n\n- Relative amplitude error ranged from approximately `3.15e-11` to `5.06e-05`.\n- Final phase error ranged from approximately `2.24e-04` to `8.97e-04` radians.\n- Relative period error ranged from approximately `3.57e-06` to `1.43e-05`.\n- Relative energy span ranged from approximately `6.86e-04` to `2.86e-03`.\n- Empirical anchor-error/pre-reset-bound ratios were finite but exceeded one in\n  some cases. They remain characterization evidence and are not a formal proof\n  that the internal bound encloses exact trajectory error.\n\n### External `ngspice` Evidence\n\nThe table below records the final remote `ngspice-42` reports. All four reports\nidentify the qualified commit, report `dirty: false`, and identify the same\nsource-tree hash shown above.\n\n| Case | Samples | Maximum absolute difference | Report SHA-256 |\n| --- | ---: | ---: | --- |\n| `rc_step` | 24 | `0.005129168242569024` | `ca42d5e482c78de3fca6ea08606ee10fc955656d3c1c376913b05d1f2d29cb03` |\n| `rl_step` | 24 | `0.0005129168232507718` | `09892144ed19049e29c38d19f29dafe976b8160e9f79ac151d51e04f803bde9d` |\n| `diode_clip` | 264 | `0.0030983774729334713` | `8bc1b1e6ed3d47525cd4705003262504746696568270562c41757b6478d7932e` |\n| `switched_rc` | 101 | `0.07878138132636461` | `2ed0cf45ebfa6119d257610b25a4b078840ede4b107c7f5d262828d58a901fdf` |\n\nGenerated-netlist SHA-256 values:\n\n- `rc_step`: `a6d1f07519751a5c19afc49c7f241d09da7bb463181c09264be250ad10018260`\n- `rl_step`: `fcedf21e1dfd02529e44170b278aad867d3b840a3a9ef0bd603a864d896c9454`\n- `diode_clip`: `791b785413c8e3782becaa4641f75f5b0ad78bc3198850d716f7154b29bb7ac7`\n- `switched_rc`: `2d76c7d623bc6684af0317db3c099c085bb78a99927ddd5fcf2f199800512ef4`\n\nRaw-output SHA-256 values:\n\n- `rc_step`: `58f24ba7758753d34ba84bcd15e1ff0da164d13844aaedd9436366379a9df3af`\n- `rl_step`: `a1f8de03d35bd4f1f8acdf2820c9ec9fbfa3f8fd9ad2c25492b914c3ef2ddb4c`\n- `diode_clip`: `92403432105ea523745bd881f4f5da4dc727a2987cb71786b80fee41a5d71f32`\n- `switched_rc`: `1d461a433f332111b6e05bcbb8782c73791c1918cefc451ea6f5f21473c31c4e`\n\nExternal differences are cross-implementation evidence for the generated\nsemantic mapping. They do not establish exact physical truth or identify which\nimplementation is responsible for a discrepancy.\n\n### Installed Wheel\n\n- Wheel: `bab_cs-1.0.0-py3-none-any.whl`.\n- Wheel SHA-256:\n  `c4293b66d2dd27000da1e3b060690f460ad13fa2cc1285381221cbe981e2c791`.\n- Import path was verified inside the clean virtual environment rather than from\n  `src/`.\n- `pip check` reported no broken requirements.\n- Installed-wheel fast suite: 97 tests passed, with only the scheduled and\n  release long-horizon tests skipped by default.\n- Installed-wheel numerical JSON, CSV, and SVG matched the source-run artifacts\n  byte-for-byte.\n\n## Work-Package Audit\n\n### TC-001 — Shared Qualification Support: Achieved\n\n- `tests/support/circuits.py` owns reusable circuit constructors.\n- `tests/support/analytic.py` provides RC, RL, general parallel RLC, and driven\n  RC analytic solutions.\n- `tests/support/metrics.py` provides trace validation/interpolation, scaled\n  errors, convergence order, zero-crossing period estimation, and sinusoidal\n  offset/amplitude/phase fitting.\n- `tests/support/raw_ab2.py` provides test-only variable-step AB2.\n- `tests/test_support.py` checks initial and selected known analytic points,\n  incompatible dimensions, non-monotonic traces, phase fitting, and raw AB2\n  convergence.\n\n### TC-002 — Integrator and Configuration Boundaries: Achieved\n\n- `BABCSConfig` and `ImplicitSettings` reject invalid, non-positive, non-finite,\n  unsupported, and inconsistent boundaries.\n- `tests/test_integrator_boundaries.py` covers AB2 exact-rate cases, dimension\n  and step validation, exact ratio endpoints, outside-ratio startup, gain\n  monotonicity, and full-reference contraction fallback.\n\n### TC-003 — Hard Failure Gates: Achieved\n\n- Predictor, algebraic residual, full residual, energy, projection fallback,\n  implicit nonconvergence, independent replay, non-finite metric/model/state,\n  minimum-step, and rejection-budget paths have named regressions.\n- Rejected direct steps preserve immutable input state/history; simulator retry\n  tests verify bounded termination and event labeling.\n\n### TC-004 — Bound Recurrence Verification: Achieved\n\n- `tests/test_bound_model.py` independently reconstructs residual defect and\n  `B_next = q * B_current + delta` from emitted metrics.\n- Tests verify finite strict contraction, zero local gain under full implicit\n  authority, reset behavior, pre-reset bound retention, and replay work.\n- Empirical exact-error coverage is explicitly separated from recurrence\n  correctness.\n\n### TC-005 — Analytic Accuracy and Convergence: Achieved\n\n- Backward Euler demonstrates first-order convergence.\n- Trapezoidal, BDF2, and test-only raw AB2 demonstrate second-order convergence\n  on compatible smooth cases.\n- Active BAB-CS error decreases under refinement without claiming a universal\n  asymptotic order.\n- RC charge/discharge, RL rise/decay, underdamped/overdamped RLC, and driven RC\n  amplitude/phase are compared at common times against analytic authority.\n- Shadow mode matches its selected implicit authority.\n\n### TC-006 — Long-Horizon Bounds and Passivity: Achieved\n\n- `tests/test_long_horizon.py` covers 10-, 100-, and 1,000-period LC, timestep\n  and anchor sweeps, damped RLC decay, passive RC/RL monotonic energy, and active\n  versus raw AB2 phase behavior.\n- The manifest compares raw AB2, active BAB-CS, and implicit integration.\n- Phase, period, amplitude, and energy are separate fields; energy is not\n  presented as a phase bound.\n\n### TC-007 — Event and Nonlinear Qualification: Achieved\n\n- Zero-time pulse edges, finite rise/fall, closely spaced PWL points, repeated\n  switching, and rejection before an event are covered.\n- Tests verify each event time, history reset, and implicit startup after events.\n- Diode clipping, diode recovery, and switched RC are compared against refined\n  replay with residual and iteration evidence.\n- A diode case with intentionally constrained implicit iterations fails closed.\n\n### TC-008 — Comparison Runner: Achieved\n\n- `tools/compare_methods.py` validates `benchmarks/manifest.json`, supports all\n  six methods, records complete source/case/configuration/authority provenance,\n  and writes stable JSON, CSV, and SVG.\n- Fixed-timestep, fixed-accuracy, and deterministic fixed-work analyses are\n  emitted.\n- Existing outputs are never overwritten without `--overwrite`.\n- Two full runs and the numerical section of a timed run reproduced\n  byte-for-byte.\n\n### TC-009 — Diagnostic Extension: Achieved\n\n- Production diagnostics add residual ratio, local defect, pre-reset bound,\n  accepted-step statistics, rejection/reset categories, reference solve and\n  iteration counts, projection counts/iterations, Jacobian evaluations, and\n  replay work.\n- Fields are additive; existing meanings are retained.\n- `tests/test_bound_model.py` and `tests/test_cli.py` verify counters and output.\n\n### TC-010 — Optional External Simulator Comparison: Achieved\n\n- `tools/compare_external.py` is opt-in and not a package dependency or\n  pull-request requirement.\n- Netlist tests cover component values, initial conditions, state vectors,\n  switch control, and unsupported diode semantics.\n- Reports preserve tool version, command, source hash, configuration, case,\n  netlist, raw-output, and log hashes.\n- Four live `ngspice-46` mappings completed successfully.\n\n### TC-011 — CI Qualification Tiers: Achieved\n\n- `.github/workflows/ci.yml` covers Python 3.11 through 3.14, the fast suite,\n  deterministic examples/comparison smoke, wheel build, and installed-wheel\n  smoke.\n- `.github/workflows/comparisons.yml` is scheduled/manual and covers the long\n  suite, complete matrix, repeated timing, live `ngspice`, hashes, and uploaded\n  JSON/CSV/log/plot artifacts.\n- `.github/workflows/release-qualification.yml` covers the no-skip source suite,\n  wheel build/hash, installed-wheel tests, complete comparison matrix, source\n  commit, environment, and report hashes.\n- All workflow files parse as valid YAML, and their commands were reproduced\n  locally, including the complete Python 3.11 through 3.14 default matrix.\n- `CI` push run `32729607872` passed at the qualified implementation commit,\n  including CPython 3.11 through 3.14 and the wheel job.\n- `Scheduled Comparisons` dispatch run `32729633142` passed at the same commit,\n  including the no-skip long-horizon suite, complete deterministic method\n  matrix, and all four live `ngspice` mappings.\n- `Release Qualification` dispatch run `32729636093` passed at the same commit,\n  including the no-skip source suite, candidate-wheel build, installed-wheel\n  verification, provenance capture, and artifact upload.\n- The release-qualification wheel SHA-256 is\n  `c4293b66d2dd27000da1e3b060690f460ad13fa2cc1285381221cbe981e2c791`.\n- The scheduled numerical CSV and SVG matched the installed-wheel CSV and SVG\n  byte-for-byte, with SHA-256 values\n  `0de55953c57faa4ceb6f43570fc1cdd9efacf1aa4b9e0d031bdf30745b433195`\n  and `98742d51cbc017b2dd08d5ec57ad280ed9390b2fd96c4b279ae2e5450a0c843b`.\n- The remote reports record source-tree SHA-256\n  `55b3a7464a2f76b2ddad157096b7eb348e4e85aeec0eb0f37166f2ec490e4458`\n  and manifest SHA-256\n  `7b805a88a1cd86e7569ff0d9fa0dbbd5f9db2b6f3c841808af12062b4866d406`.\n- All four external reports record `dirty: false`; generated evidence no longer\n  contaminates source-cleanliness provenance.\n\n### TC-012 — Documentation and Evidence Audit: Achieved\n\n- `README.md` documents local qualification commands and CI tiers.\n- `docs/COMPARISON_PROTOCOL.md` documents authority, controls, metrics,\n  determinism, thresholds, performance boundaries, and CI tiers.\n- `docs/EXTERNAL_COMPARISON.md` documents mapping, provenance, failure behavior,\n  and claim limits.\n- This file records the requirement-to-evidence audit without modifying the\n  historical completion audit.\n\n## Completion-Gate Audit\n\n- Existing BAB-CSv1 regression requirements: pass within the 97-test no-skip\n  suite.\n- Isolated hard failure gates: pass.\n- Independent recursive-bound recomputation: pass.\n- Analytic convergence for authority methods and raw AB2: pass.\n- Active accuracy, contraction, fallback, anchor, and sweep evidence: pass.\n- Long-horizon phase separated from energy: pass.\n- Complete authority and configuration provenance: pass.\n- Byte-identical deterministic numerical artifacts: pass.\n- Installed candidate wheel comparison: pass.\n- Requirement-to-evidence audit: present.\n- Exact-candidate remote CI, scheduled, and release workflows: pass at\n  `3dafe404d5a7d134c26f3a0d7fc73d7e3777dd95`.\n- Human review before release publication: retained as a separate gate; no new\n  release was published by this qualification run.\n\nThe implementation and comparison program are qualified locally and remotely.\nThe audit itself is excluded from the deterministic source-tree hash, so this\nevidence-only update does not alter the qualified implementation snapshot.\nPublishing or replacing a GitHub release still requires an explicit human\ndecision after reviewing the candidate commit, thresholds, and artifacts.\n\n## Known Limitations\n\n- Active BAB-CS performs an implicit reference solve on every eligible AB step\n  and is not expected to outperform pure implicit integration in v1.\n- Dense algebra limits circuit scale.\n- Higher-index and singular topologies fail closed rather than being\n  regularized.\n- External comparison covers only explicitly equivalent mappings.\n- Empirical bound coverage is not a formal exact-trajectory enclosure proof.\n- Wall time is characterization only.\n- Arbitrary analog threshold root finding and production AB-only operation\n  remain deferred.\n",
      "order": 9,
      "path": "TESTS_AND_COMPARISONS_AUDIT.md",
      "readingMinutes": 9,
      "sha256": "49a9e10ec9df135843e70d9d7b0dd00d8bc9248c6a0df6a82f8efee568672739",
      "summary": "Audit date: August 24, 2026",
      "title": "Bounded-Authority-Based-Circuit-Simulation Tests and Comparisons Qualification Audit",
      "wordCount": 1863
    },
    {
      "category": "Tests and Comparisons",
      "conceptIds": [
        "babcs",
        "projection",
        "replay",
        "anchor",
        "residual",
        "jacobian",
        "newton-iteration",
        "stiffness",
        "passivity",
        "deterministic-evidence",
        "phase-error",
        "fail-closed",
        "factorization",
        "python-wheel",
        "mna",
        "rc",
        "rlc",
        "lc",
        "ab2",
        "adams-bashforth",
        "ab3",
        "be",
        "bdf2",
        "rk23",
        "csc",
        "klu",
        "superlu",
        "scipy",
        "colamd",
        "lru",
        "rms",
        "wrms",
        "ulp",
        "sha256",
        "api",
        "zip",
        "amd",
        "ngspice"
      ],
      "headings": [
        {
          "id": "bounded-authority-based-circuit-simulation-performance-optimization-audit",
          "level": 1,
          "text": "Bounded-Authority-Based-Circuit-Simulation Performance Optimization Audit"
        },
        {
          "id": "status",
          "level": 2,
          "text": "Status"
        },
        {
          "id": "changes",
          "level": 2,
          "text": "Changes"
        },
        {
          "id": "replay-correctness",
          "level": 3,
          "text": "Replay correctness"
        },
        {
          "id": "repeated-jacobian-work",
          "level": 3,
          "text": "Repeated Jacobian work"
        },
        {
          "id": "nonlinear-and-implicit-solves",
          "level": 3,
          "text": "Nonlinear and implicit solves"
        },
        {
          "id": "linear-algebra-kernels",
          "level": 3,
          "text": "Linear algebra kernels"
        },
        {
          "id": "reproducible-packaging",
          "level": 3,
          "text": "Reproducible packaging"
        },
        {
          "id": "exact-baseline-comparison",
          "level": 2,
          "text": "Exact Baseline Comparison"
        },
        {
          "id": "follow-on-replay-and-sensitivity-gain",
          "level": 2,
          "text": "Follow-On Replay and Sensitivity Gain"
        },
        {
          "id": "scaling-and-factorization-gain",
          "level": 2,
          "text": "Scaling and Factorization Gain"
        },
        {
          "id": "optional-sparse-factorization-and-compiled-stamping-gain",
          "level": 2,
          "text": "Optional Sparse Factorization and Compiled Stamping Gain"
        },
        {
          "id": "continued-sparse-and-replay-gains",
          "level": 2,
          "text": "Continued Sparse and Replay Gains"
        },
        {
          "id": "fill-gated-superlu-ordering",
          "level": 3,
          "text": "Fill-gated SuperLU ordering"
        },
        {
          "id": "residual-and-sampled-input-assembly",
          "level": 3,
          "text": "Residual and sampled-input assembly"
        },
        {
          "id": "higher-order-replay-initialization",
          "level": 3,
          "text": "Higher-order replay initialization"
        },
        {
          "id": "norm-work-elimination",
          "level": 3,
          "text": "Norm-work elimination"
        },
        {
          "id": "native-sparse-differential-jacobian-norm",
          "level": 3,
          "text": "Native sparse differential-Jacobian norm"
        },
        {
          "id": "coupled-algebraic-newton-prediction",
          "level": 3,
          "text": "Coupled algebraic Newton prediction"
        },
        {
          "id": "explicit-projection-and-reference-reuse",
          "level": 3,
          "text": "Explicit projection and reference reuse"
        },
        {
          "id": "quartic-replay-algebraic-initialization",
          "level": 3,
          "text": "Quartic replay algebraic initialization"
        },
        {
          "id": "guarded-nonlinear-chord-prediction",
          "level": 3,
          "text": "Guarded nonlinear chord prediction"
        },
        {
          "id": "post-chord-kernel-reductions",
          "level": 3,
          "text": "Post-chord kernel reductions"
        },
        {
          "id": "accepted-inputs-and-specialized-residual-assembly",
          "level": 3,
          "text": "Accepted inputs and specialized residual assembly"
        },
        {
          "id": "final-solution-materialization-and-numeric-conversion",
          "level": 3,
          "text": "Final solution materialization and numeric conversion"
        },
        {
          "id": "contractively-bounded-schur-implicit-prediction",
          "level": 3,
          "text": "Contractively bounded Schur implicit prediction"
        },
        {
          "id": "ulp-aware-two-step-evidence-age",
          "level": 3,
          "text": "ULP-aware two-step evidence age"
        },
        {
          "id": "compiled-simulation-breakpoint-schedules",
          "level": 3,
          "text": "Compiled simulation breakpoint schedules"
        },
        {
          "id": "demand-gated-sparse-kernel-compile-reuse",
          "level": 3,
          "text": "Demand-gated sparse-kernel compile reuse"
        },
        {
          "id": "hot-topology-sparse-kernel-adoption",
          "level": 3,
          "text": "Hot-topology sparse-kernel adoption"
        },
        {
          "id": "duplicate-built-in-switch-control-sampling",
          "level": 3,
          "text": "Duplicate built-in switch-control sampling"
        },
        {
          "id": "bounded-suitesparse-klu-symbolicnumeric-reuse",
          "level": 3,
          "text": "Bounded SuiteSparse KLU symbolic/numeric reuse"
        },
        {
          "id": "klu-hot-path-safety-and-boundary-reduction",
          "level": 3,
          "text": "KLU hot-path safety and boundary reduction"
        },
        {
          "id": "fused-private-sparse-assembly-and-klu-factorsolve",
          "level": 3,
          "text": "Fused private sparse assembly and KLU factor/solve"
        },
        {
          "id": "jacobian-only-native-sensitivity-assembly",
          "level": 3,
          "text": "Jacobian-only native sensitivity assembly"
        },
        {
          "id": "independent-mixed-sensitivity-gather-ownership",
          "level": 3,
          "text": "Independent mixed-sensitivity gather ownership"
        },
        {
          "id": "deferred-reference-jacobian-materialization",
          "level": 3,
          "text": "Deferred-reference Jacobian materialization"
        },
        {
          "id": "independent-evidence-controlled-replay-refinement",
          "level": 3,
          "text": "Independent evidence-controlled replay refinement"
        },
        {
          "id": "qualified-switched-bdf2-replay-refinement",
          "level": 3,
          "text": "Qualified switched BDF2 replay refinement"
        },
        {
          "id": "current-cumulative-scaling",
          "level": 3,
          "text": "Current cumulative scaling"
        },
        {
          "id": "repeated-topology-circuit-construction",
          "level": 3,
          "text": "Repeated-topology circuit construction"
        },
        {
          "id": "local-validation",
          "level": 2,
          "text": "Local Validation"
        },
        {
          "id": "remaining-high-value-work",
          "level": 2,
          "text": "Remaining High-Value Work"
        }
      ],
      "kind": "Evidence",
      "markdown": "# Bounded-Authority-Based-Circuit-Simulation Performance Optimization Audit\n\n## Status\n\nThis document records a locally validated candidate optimization pass relative\nto commit `8dad1f1bb41acf343c36dae8daeb932c137fb268` on August 24, 2026. The\ncandidate is not a release qualification or publication claim until it is\ncommitted and the repository workflows pass that exact commit.\n\nThe pass deliberately preserves the qualified default architecture: active and\nshadow modes still compute an implicit reference on every eligible AB step, and\nperiodic independent replay remains enabled. Replay refinement is now\ntopology-aware, but no reference solve or anchor interval was removed, made\noptional, or evidence-skipping.\n\n## Changes\n\n### Replay correctness\n\n- Independent BDF2 replay now carries the previous differential state and\n  previous accepted substep across the full replay window.\n- The first replay substep still starts with backward Euler, as required when\n  BDF2 history does not yet exist.\n- A regression verifies that replayed BDF2 matches explicitly history-fed BDF2\n  and no longer collapses to a backward-Euler sequence.\n- The replay refinement count remains four for phase-sensitive C+L topologies\n  and backward-Euler replay, while other built-in topologies use two substeps by\n  default. The fixed-refinement behavior remains available by configuration.\n- After replay startup, uniform replay windows use an AB3 extrapolation after\n  two matching substeps. Variable or nonmatching substeps retain the\n  variable-step AB2 initial guess. Neither predictor changes the reference\n  method, residual equation, convergence gate, or backward-Euler startup.\n\n### Repeated Jacobian work\n\n- `BABCSHistory` caches the differential-Jacobian norm associated with its\n  stored previous evaluation.\n- Regular active/shadow steps calculate one new norm instead of recalculating\n  both adjacent-state norms. Startup, event reset, fallback, and independent\n  re-anchor paths invalidate the cache rather than reusing uncertain data.\n- Standard `Circuit` instances derive the differential Jacobian from exact MNA\n  sensitivities at the accepted algebraic solution. This removes perturbed\n  circuit evaluations from implicit Newton and bound estimation. Subclasses\n  preserve the finite-difference fallback or their own override behavior.\n\n### Nonlinear and implicit solves\n\n- Algebraic Newton line-search trials assemble residuals without allocating or\n  stamping an unused dense Jacobian.\n- An accepted algebraic trial that already satisfies the configured tolerance\n  returns immediately instead of performing a redundant full assembly.\n- The implicit integrator returns the evaluation that produced its converged\n  residual instead of solving the identical circuit state once more.\n- A full-reference correction reuses the existing implicit reference\n  evaluation instead of projecting the same differential state again.\n\n### Linear algebra kernels\n\n- Scalar linear systems bypass generic augmented-matrix elimination while\n  preserving the same scale-relative pivot rejection rule.\n- Dense-system scaling is calculated while the augmented matrix is built,\n  removing a separate matrix-norm traversal from every solve.\n- Scalar infinity norms and finite-difference Jacobians use direct paths rather\n  than allocating general dense structures.\n- Infinity norms now propagate `NaN` deterministically instead of depending on\n  value ordering inside `max`.\n\n### Reproducible packaging\n\n- The wheel backend now fixes ZIP timestamps and file modes instead of\n  inheriting the wall-clock build time.\n- A regression builds the wheel twice in independent directories and requires\n  byte-identical archives with canonical metadata.\n\nThese changes do not relax a residual, contraction, passivity, stiffness,\nevent, timestep, or re-anchor gate.\n\n## Exact Baseline Comparison\n\nThe baseline and candidate were run from separate worktrees on CPython 3.14.6\nand an AMD Ryzen 9 7900X. Each round used five warmups followed by 25 timed\nexecutions of the nonlinear `diode_clip` case to `1.0e-3` seconds with a\n`4.0e-6` nominal step, active mode, a 50-step anchor interval, and four anchor\nsubsteps.\n\n| Measurement | Baseline | Candidate | Reduction |\n| --- | ---: | ---: | ---: |\n| Round 1 median | 0.144777326 s | 0.096212455 s | 33.545% |\n| Round 2 median | 0.141734707 s | 0.097759334 s | 31.027% |\n| Mean of medians | 0.143256017 s | 0.096985895 s | 32.299% |\n| Differential Jacobian evaluations | 498 | 254 | 48.996% |\n| Per-step reference circuit evaluations | 1,056 | 806 | 23.674% |\n| Replay circuit evaluations | 4,248 | 3,248 | 23.540% |\n\nAgainst the already optimized pre-kernel candidate, the linear-algebra changes\nreduced the same benchmark's mean of medians by a further 8.349% without\nchanging any operation count. The final 100-result numerical matrix is exactly\nequal to the pre-kernel candidate matrix, including diagnostics, work counters,\nand derived analyses.\n\nThe full 100-result method matrix produced identical per-result accuracy,\nbound, oscillator, authority, configuration, and selected-step values. Its\nconvergence analysis was also identical. Work-derived analyses changed because\nthe measured deterministic work changed:\n\n| Full-matrix work counter | Baseline | Candidate | Reduction |\n| --- | ---: | ---: | ---: |\n| Differential Jacobian evaluations | 35,680 | 18,682 | 47.640% |\n| Per-step reference circuit evaluations | 136,151 | 106,922 | 21.468% |\n| Replay circuit evaluations | 333,810 | 263,598 | 21.034% |\n| Explicit projections | 35,680 | 33,095 | 7.245% |\n| Deterministic work units | 1,020,516 | 918,043 | 10.041% |\n\n## Follow-On Replay and Sensitivity Gain\n\nA controlled follow-on comparison used five warmups and 25 timed runs of the\nnonlinear `diode_clip` case to `1.0e-3` seconds with a `2.0e-6` nominal step and\na 50-step anchor interval. The pre-loop path used fixed four-substep replay,\nfinite-difference differential Jacobians, and Euler replay initialization. The\nretained path used topology-aware two-substep replay, exact MNA sensitivities,\nand AB2 replay initialization.\n\n| Method | Pre-loop median | Retained median | Reduction |\n| --- | ---: | ---: | ---: |\n| Active bounded AB2 | 0.194835465 s | 0.115822253 s | 40.554% |\n| Fast bounded RK23 | 0.188275857 s | 0.112518345 s | 40.238% |\n\nFor active bounded AB2, replay steps fell from 2,001 to 1,000 and replay circuit\nevaluations fell from 6,499 to 1,998. Its maximum waveform error against the\nsame refined authority remained `9.176019653e-4`. For fast bounded RK23, replay\nsteps fell from 2,000 to 1,000, replay circuit evaluations fell from 6,496 to\n1,998, and maximum waveform error changed only from `7.728687513e-5` to\n`7.730052969e-5`.\n\nThe AB2 replay initial guess is workload-dependent: a separate smooth RC\nmeasurement reduced median runtime by roughly 30-32%, while the diode runtime\nwas neutral. The optimization remains because it materially reduces linear\nreference work without weakening convergence tests.\n\n## Scaling and Factorization Gain\n\nThe next optimization loop targeted repeated dense factorization after exact\nMNA sensitivities exposed multi-state scaling cost. The retained design:\n\n- solves all sensitivity columns through one multi-right-hand-side\n  factorization;\n- caches linear differential Jacobians by component values and selected switch\n  topology;\n- caches algebraic and implicit residual factorizations by topology, method,\n  and step shape;\n- assembles residual-only systems after a linear algebraic factor is available;\n- bounds each cache to 128 entries so long-running adaptive simulations cannot\n  accumulate unbounded topology or step-shape state;\n- bypasses all caches for diode circuits and preserves finite-difference\n  behavior for `Circuit` subclasses.\n\nA controlled comparison used five warmups and 15 timed runs per case. The\npre-loop path used one dense factorization per sensitivity column and no\nlinear-topology caches. The optimized path includes all retained scaling\nchanges. Endpoints were bit-identical in every case.\n\n| Workload | Dynamic states | Pre-loop median | Optimized median | Reduction |\n| --- | ---: | ---: | ---: | ---: |\n| Nonlinear diode clip | 1 | 0.121379363 s | 0.120120340 s | 1.037% |\n| RC charge | 1 | 0.055779174 s | 0.041220080 s | 26.101% |\n| Parallel RLC | 2 | 0.117980812 s | 0.076879102 s | 34.838% |\n| Four independent LC tanks | 8 | 0.100803271 s | 0.028100581 s | 72.123% |\n| Eight independent LC tanks | 16 | 0.202783340 s | 0.025254669 s | 87.546% |\n\nIsolated characterization showed multi-right-hand-side sensitivities reducing\nthe 8-state and 16-state cases by 33.1% and 52.7%; linear Jacobian caching by\n34.1% and 49.0%; algebraic factor caching by 19.8% and 24.3%; and implicit\nfactor caching by 19.4% and 26.0%. These percentages are incremental within\ntheir individual controlled comparisons and must not be added together.\n\n## Optional Sparse Factorization and Compiled Stamping Gain\n\nThe next retained loops added an explicit optional SciPy SuperLU backend and\nthen removed dense assembly from its hot path without changing the\ndependency-free `dense` default. `Circuit` now compiles its algebraic CSC\nstructure, terminal locations, device Jacobian locations, constraint locations,\nand differential-sensitivity right-hand sides once. Eligible sparse evaluations\nupdate only the numeric values. The SciPy adapter reuses a validated CSC\ntemplate and copies the numeric data before factorization.\n\n`auto` uses sparse reusable factorizations from 16 unknowns, one-shot sparse\nsolves from 32 unknowns, and the 16-unknown multi-right-hand-side crossover only\nwhen at least eight columns can amortize the backend overhead. Systems above 35%\nstructural density remain dense. Explicit `scipy` selection is available for\ncontrolled characterization and fails clearly when the optional dependency is\nunavailable.\n\nAn interleaved local comparison used three warmups and 11 timed executions per\nbackend for independent LC tanks over `2.0e-4` seconds with a `2.0e-6` nominal\nstep. The sparse timings are incremental against the already optimized dense\npath, not against the original project baseline. Endpoints were bit-identical.\n\n| Dynamic states | Dense median | Auto median | Reduction |\n| ---: | ---: | ---: | ---: |\n| 8 | 0.029026481 s | 0.029071947 s | -0.157% |\n| 16 | 0.053386233 s | 0.042590269 s | 20.222% |\n| 32 | 0.118676441 s | 0.067108034 s | 43.453% |\n| 64 | 0.344328509 s | 0.124991749 s | 63.700% |\n\nA second interleaved comparison used five warmups and 15 timed executions per\nbackend for independent driven diode channels over `1.0e-4` seconds with a\n`2.0e-6` nominal step. Auto intentionally remained dense below the fresh-factor\ncrossover; larger nonlinear systems used direct compiled CSC stamping for\nNewton and sensitivity solves. Endpoints were bit-identical across every timed\nexecution and backend.\n\n| Diode channels | Algebraic unknowns | Dense median | Auto median | Reduction |\n| ---: | ---: | ---: | ---: | ---: |\n| 2 | 8 | 0.017495564 s | 0.017812335 s | -1.811% |\n| 4 | 16 | 0.038361584 s | 0.038581474 s | -0.573% |\n| 8 | 32 | 0.119441513 s | 0.051047508 s | 57.262% |\n| 16 | 64 | 0.500826076 s | 0.073091419 s | 85.406% |\n| 32 | 128 | 2.707985152 s | 0.122329999 s | 95.483% |\n\nThe small negative rows are retained as crossover evidence, not described as\nspeedups. The auto policy keeps the underlying dense numerical path there.\n\nAn isolated comparison against the preceding sparse-factor candidate, which\nstill assembled densely and converted each matrix, measured direct-CSC\nreductions of 35.974%, 54.299%, and 69.144% at 32, 64, and 128 algebraic\nunknowns respectively. Those percentages are incremental implementation gains,\nnot additional factors to add to the dense-versus-auto table.\n\nThe follow-on implicit loop now solves the exact coupled algebraic/dynamic block\nsystem directly instead of explicitly materializing the dense differential\nJacobian and its Schur complement for nonlinear Newton updates. The compiled\nblock has the form\n\n```text\n[ A   -B ] [delta_u] = [        0]\n[-hD   aI ] [delta_x]   [-residual]\n```\n\nwhere `A` is the algebraic Jacobian, `A du/dx = B`, `D du/dx` is the dynamic\nJacobian, and `aI - hD A^-1 B` is exactly the prior implicit residual Jacobian.\nStructural-equivalence tests compare the block update with the explicitly\nformed Schur update. Against the immediately preceding direct-CSC candidate,\nthe block solve reduced the 32-, 64-, and 128-unknown medians by a further\n2.342%, 6.518%, and 23.284%, with bit-identical simulation endpoints in the\nmeasured workload.\n\nThe final backend loop reuses one mutable CSC value workspace per structural\npattern and thread instead of allocating and validating a new SciPy matrix for\nevery factorization. The per-thread cache is bounded to 128 structures, and\nregressions verify that previously returned SuperLU factor objects remain\nindependent after the workspace is reused. An isolated 128-unknown\nfactorization microbenchmark reduced setup from approximately 55 microseconds\nto 20 microseconds. End-to-end medians fell a further 10.918%, 9.826%, and\n2.860% at 32, 64, and 128 unknowns respectively.\n\nThe final assembly loop splits the sparse full-Jacobian path from the dense and\nresidual-only paths, then fuses voltage lookup, residual stamping, and compiled\nCSC value updates inside each device loop. This removes nested helper dispatch\nwithout vectorizing, changing component mutability, or altering arithmetic\nordering. Against the workspace-reuse candidate, medians fell a further 3.963%,\n4.195%, and 6.534% at 32, 64, and 128 unknowns respectively. Existing dense\nversus sparse structural-equivalence tests continued to compare every residual\nand Jacobian entry exactly.\n\n## Continued Sparse and Replay Gains\n\nThe next measured loops retained several independent reductions. Each\npercentage below is incremental against the immediately preceding candidate;\nthe values must not be added together.\n\n### Fill-gated SuperLU ordering\n\nRepeated sparse structures start with `COLAMD`. On the fourth factorization,\nthe implementation probes `NATURAL` ordering with the same numeric values and\nretains it only when the existing singularity gate passes and `L.nnz + U.nnz`\nis no greater than the `COLAMD` fill. A failed cached `NATURAL` factorization\npermanently falls back to `COLAMD` for that bounded thread-local workspace.\n\nThree balanced rounds with five warmups and 15 paired runs measured reductions\nof 1.128%, 2.084%, and 1.997% at 32, 64, and 128 unknowns respectively. The\nminimum round reductions were 0.929%, 1.778%, and 1.706%. Endpoints remained\nexactly equal.\n\n### Residual and sampled-input assembly\n\nLarge sparse residual-only evaluations now stamp directly into the residual\nwithout constructing Jacobian values. Arithmetic order remains\nreciprocal-then-multiply so the sparse and original paths remain exactly equal.\nThree balanced rounds measured mean reductions of 2.195%, 1.891%, and 2.275%\nat 32, 64, and 128 unknowns.\n\nFor sparse systems with at least 64 algebraic unknowns, one evaluation samples\neach current-source waveform, switch control, and constraint waveform once and\nreuses those values through Newton and power accounting. Mutable waveform\nobjects are still dereferenced on every new evaluation. Mean reductions were\n2.263% at 64 unknowns and 2.836% at 128 unknowns; the 32-unknown production path\nis intentionally unchanged.\n\nConstraint target positions are also precompiled while their mutable source\nobjects and state values remain live. Isolated target-construction reductions\nranged from 22.86% to 36.66%. End-to-end results were positive at 32 and 128\nunknowns but noisy at 64 unknowns, so this is retained as an isolated kernel\ngain rather than claimed as a uniform simulation speedup.\n\n### Higher-order replay initialization\n\nAfter two matching uniform replay substeps, the Newton initial guess is\n\n```text\nx[n] + h * (23 f[n] - 16 f[n-1] + 5 f[n-2]) / 12.\n```\n\nThe first replay step remains unpredicted and variable replay spacing falls\nback to the existing variable-step AB2 formula. The implicit method, residual,\nconvergence test, and backward-Euler restart are unchanged.\n\nThree balanced rounds measured reductions of 16.394%, 17.628%, and 19.076% at\n32, 64, and 128 unknowns, with minimum round reductions of 15.883%, 17.456%,\nand 18.762%. Replay Newton iterations fell from 46, 52, and 62 to one, and\nreplay circuit evaluations fell from 146, 152, and 162 to 101.\n\nThe changed predictor intentionally changes tolerance-limited replay endpoints.\nAgainst a refined replay with a `1.25e-7` step, the prior AB2 endpoint had a\nmaximum error of `6.934961321869437e-08`; the AB3 endpoint error was\n`1.4848380275322981e-08`. This supports retaining the change as both a\nperformance and accuracy improvement rather than treating endpoint equality\nwith the lower-order initial guess as the criterion.\n\n### Norm-work elimination\n\nAn accepted algebraic solution caches its infinity norm only for the exact\naccepted tuple object; an equal copied sequence is recomputed. The validated\ndynamic-state infinity norm is stored in `CircuitEvaluation` during the\nmandatory finite-state scan and reused by the implicit residual gate. These\nchanges measured mean reductions of 1.622-2.365% and 1.587-2.022%\nrespectively. In the 128-unknown profile, total infinity-norm calls fell from\n1,903 before these changes to 1,251.\n\n### Native sparse differential-Jacobian norm\n\nEligible large nonlinear built-in circuits now solve all precompiled\ndifferential-sensitivity right-hand sides as one native NumPy array and compute\nthe induced infinity norm without materializing a Python dense Jacobian. The\nresult is conservatively rounded upward by a dimension-scaled floating-point\nenvelope. Dense, small, and subclass paths continue to materialize the existing\nJacobian so extension behavior is unchanged.\n\nThree balanced rounds measured mean reductions of 2.960% at 64 unknowns and\n7.508% at 128 unknowns, with minimum round reductions of 2.575% and 7.019%.\nThe 32-unknown case remains on the original path. Simulation endpoints were\nexactly equal; bound metrics differed only by the deliberate conservative\nupward rounding.\n\n### Coupled algebraic Newton prediction\n\nThe sparse coupled implicit block already solves for both the algebraic update\nand the dynamic update. The integrator now retains the algebraic component and\nuses its damped value as the algebraic initial guess for the corresponding\ndynamic line-search trial. The normal algebraic residual and Newton tolerance\nremain authoritative.\n\nThree balanced rounds measured mean reductions of 8.178%, 7.257%, and 6.187%\nat 32, 64, and 128 unknowns, with minimum round reductions of 8.005%, 7.070%,\nand 5.818%. Reference algebraic iterations fell from 100 to 50. Endpoints and\nall non-work metrics were exactly equal in the measured workload.\n\n### Explicit projection and reference reuse\n\nFor eligible large sparse explicit candidates, the mandatory current-state\ndifferential-sensitivity factorization now performs one modified-Newton\nalgebraic projection and carries its conservative Jacobian norm into the\nbounded controller. Dense, small, implicit-candidate, and extension paths are\nunchanged. This removed all 49 candidate algebraic iterations in the measured\n64- and 128-unknown workloads. Three balanced rounds measured 2.108% at 64\nunknowns and 0.601% at 128 unknowns; 32 unknowns intentionally remained on the\noriginal path.\n\nThe scheduled implicit reference also reuses the candidate's already accepted\ncircuit evaluation when its time and complete differential state exactly match\nthe implicit initial guess. This removes a duplicate projection without\nchanging the implicit residual. Mean reductions were 12.717%, 13.128%, and\n12.493% at 32, 64, and 128 unknowns, with minimum round reductions of 12.642%,\n12.889%, and 12.030%. Reference circuit evaluations fell from 100 to 51 and\nreference algebraic iterations fell from 50 to one. Final dynamic states were\nidentical; the largest intermediate dynamic delta was `1.68e-14`, and maximum\nalgebraic and full residual evidence was unchanged.\n\n### Quartic replay algebraic initialization\n\nAfter four matching uniform replay substeps, eligible large sparse systems\nextrapolate accepted algebraic solutions as\n\n```text\n5 u[n] - 10 u[n-1] + 10 u[n-2] - 5 u[n-3] + u[n-4].\n```\n\nThis is only an initial guess. A failed algebraic prediction retries from the\ncurrent accepted algebraic solution, and the same Newton tolerance decides\nwhether the guess is sufficient. Variable, event-reset, small, dense, and\nextension paths do not use it.\n\nThree balanced rounds measured mean reductions of 2.996% at 64 unknowns and\n2.279% at 128 unknowns, with minimum round reductions of 2.706% and 2.172%.\nReplay algebraic iterations fell from 100 to 78. Against an eight-times-refined\ntrapezoidal authority with tighter Newton tolerances, the predicted replay\nendpoint error was approximately 0.14% lower than the prior endpoint error.\n\n### Guarded nonlinear chord prediction\n\nEligible built-in diode circuits with at least 64 algebraic unknowns retain the\nmost recently validated sparse algebraic factorization as a chord predictor.\nThe predictor never bypasses the current residual, line search, Newton\ntolerance, or singularity gates. A failed factor solve or an update that does\nnot strictly reduce the current residual clears the cached factorization and\nimmediately retries through the original fresh-Jacobian Newton path. The cache\ncontains at most one factorization per `Circuit`.\n\nThree balanced rounds measured mean reductions of 24.020% at 64 unknowns and\n20.109% at 128 unknowns, with minimum round reductions of 23.791% and 19.783%.\nAlgebraic iteration counts were unchanged. Maximum final-state deltas were\n`5.676015213396113e-15` and `7.320533068622126e-15`; the maximum algebraic\nunknown delta was below `6.58e-14`, and maximum residual evidence was unchanged.\nAgainst an eight-times-refined trapezoidal authority with tighter Newton\ntolerances, the endpoint-error ratios were approximately `1.00000042` and\n`1.00000048`.\n\n### Post-chord kernel reductions\n\nInfinity norms of at least 64 values now use two C-level iterator passes: one\nto preserve deterministic `NaN` propagation and one to compute the maximum\nmagnitude. Shorter vectors retain the original scalar loop. Isolated balanced\nmeasurements reduced the 64- and 128-unknown workloads by 1.078% and 1.474%,\nwith minimum round reductions of 0.934% and 1.136%; the 32-unknown production\npath is unchanged and all measured traces were exactly equal.\n\nLarge sparse nonlinear evaluations now retain diode currents only when they\nwere assembled for the exact unknown-vector object accepted by Newton. Power\naccounting consumes those currents without evaluating the diode law again.\nDense, subclass, stale-object, and unavailable-cache paths recompute normally.\nThree balanced rounds measured reductions of 1.585%, 2.348%, and 2.613% at 32,\n64, and 128 unknowns, with minimum round reductions of 1.182%, 2.101%, and\n2.441%. Dynamic traces and every recorded source/dissipated-power value were\nexactly equal.\n\nFinally, dynamic and algebraic sizes are stored as compiled-topology facts, and\nthe sparse-Jacobian eligibility decision is cached by backend. Changing the\nbackend invalidates the decision and is covered by regression. Three balanced\nrounds measured reductions of 1.881%, 1.621%, and 1.326% at 32, 64, and 128\nunknowns, with minimum round reductions of 1.486%, 0.926%, and 1.129%. Traces\nwere exactly equal.\n\nThe exact base `Circuit` sparse kernels now inline the diode limiting law. The\nresidual-only path computes current without constructing the unused\nconductance, while the full sparse-Jacobian path preserves the original current\nand conductance operation order. Subclasses continue through the overridable\ndevice method. Against a preserved pre-kernel package, three balanced rounds\nmeasured reductions of 1.049%, 2.862%, and 2.583% at 32, 64, and 128 unknowns,\nwith minimum round reductions of 1.029%, 2.069%, and 2.063%. Dynamic traces and\nall recorded source/dissipated-power values were exactly equal.\n\n### Accepted inputs and specialized residual assembly\n\nAccepted evaluations now retain the already sampled algebraic inputs that\nproduced them. Native differential sensitivity and coupled sparse implicit work\nreuse those inputs only when the evaluation records the exact owning `Circuit`;\nforeign, unavailable, dense, and extension paths resample normally. Three\nbalanced rounds measured mean reductions of 1.458% at 64 unknowns and 1.155%\nat 128 unknowns, with minimum round reductions of 1.132% and 0.812%. The\n32-unknown result was within timing noise and its production path is unchanged.\nEvery measured state, source-power, dissipated-power, and residual value was\nexactly equal.\n\nFor exact built-in `Circuit` instances on the eligible large sparse path,\ntopology construction now compiles a residual-only scalar kernel with fixed\nvalidated indices and the original device-group stamping order. The generated\nkernel contains no user-provided source text, reads mutable component parameters\nand sampled inputs live, and preserves the scalar fallback for subclasses and\nineligible paths. A NumPy residual-buffer prototype was rejected after it made\nthe isolated kernel approximately 61% slower.\n\nAgainst the immediately preceding scalar fallback, the specialized kernel\nreduced end-to-end simulation time by 5.987% at 64 unknowns and 6.514% at 128\nunknowns, with minimum round reductions of 5.096% and 6.226%. Kernel build\noverhead was approximately 1.09 ms and 2.25 ms respectively. Timed from circuit\nconstruction through a 50-step simulation, the eager design still reduced total\nlatency by 3.250% and 1.729%, with minimum round reductions of 3.136% and\n1.533%. State and metric traces were exactly equal in every comparison.\n\nThe same validated-index design now covers full residual-plus-CSC assembly,\nbut only after 256 eligible calls on the exact built-in circuit. Eager\ncompilation was rejected because construction-through-short-simulation latency\nregressed by 2.7% to 3.3%. The demand gate leaves the measured 50-step workload\non the existing fallback at 115 to 116 full assemblies, while a 1,000-step\nworkload demonstrates repeated use before paying compilation cost. On those\nlong workloads, three balanced rounds measured end-to-end reductions of 1.943%\nat 64 unknowns and 1.888% at 128 unknowns, with minimum round reductions of\n1.072% and 1.516%. The generated assembly kernel itself reduced direct call\ntime by approximately 37% to 39%. Residuals, CSC numeric data, states, and\nrecorded metrics were exactly equal, including after resistor, diode, and\nswitch parameter mutation.\n\nEvaluation now enters a private algebraic-solve core only after time and\ndynamic-state validation has already succeeded, so the public `evaluate`\nboundary no longer triggers the same state scan again inside\n`solve_algebraic`. Public direct solves retain their original validation. For\nnoncached algebraic guesses, finiteness checking and infinity-norm calculation\nare combined into one scalar pass; the exact last accepted tuple still reuses\nits cached norm. Against the exact preceding wheel, three balanced rounds\nmeasured reductions of 1.954%, 1.929%, and 1.987% at 32, 64, and 128 unknowns,\nwith minimum round reductions of 1.294%, 1.574%, and 1.836%. State and metric\ntraces were exactly equal, and a public non-finite initial guess continues to\nfail closed.\n\nThe topology-constant differential-sensitivity right-hand-side matrix is now\nconverted to a read-only NumPy array only on its first eligible native sparse\nuse and then reused by identity. Capacitor branch indices are likewise retained\nas compiled topology data instead of rebuilt as a NumPy array for every norm.\nThe 32-unknown path remains below the native-sensitivity gate. Direct repeated\nmulti-right-hand-side solves were 68% faster at 64 unknowns and 77% faster at\n128 unknowns. Against the exact preceding wheel, three balanced end-to-end\nrounds measured reductions of 2.697% at 64 unknowns and 6.870% at 128 unknowns,\nwith minimum round reductions of 1.913% and 6.510%. State and metric traces\nwere exactly equal. In the warmed 128-unknown profile, aggregate\n`numpy.asarray` time fell from 0.046 to 0.014 seconds.\n\n### Final solution materialization and numeric conversion\n\nAlgebraic solution construction now consumes the validated unknown sequence\nonce. The node-voltage dictionary is updated from a shared iterator in compiled\nnode order, and the branch-current dictionary consumes the remaining values in\ncompiled branch order. This preserves the public mapping order and tuple/dict\ntypes while removing two redundant indexed dictionary comprehensions. Isolated\nconstruction time fell by approximately 30%, 40%, 48%, and 52% at 32, 64, 128,\nand 256 algebraic unknowns. Against the exact preceding wheel, three balanced\nend-to-end rounds measured mean reductions of 0.961%, 1.521%, and 1.897% at 32,\n64, and 128 unknowns, with exactly equal state and metric traces.\n\nEquivalent tuple/list conversions of already validated numerical sequences now\nuse the C-level `map(float, ...)` path. Conversion order and exception behavior\nremain unchanged. Against the immediately preceding retained candidate, this\nwas timing-neutral at 32 unknowns and reduced mean end-to-end time by 1.932% at\n64 unknowns and 1.269% at 128 unknowns. State and metric traces were exactly\nequal.\n\n### Contractively bounded Schur implicit prediction\n\nThe native differential-sensitivity path now retains both the algebraic\nsensitivity matrix and the exact reduced differential Jacobian used by the\nbound calculation. An eligible nonlinear implicit solve may use that prior\nevidence to form the reduced Schur system\n`(a I - h J) delta_x = -residual`, then recover the algebraic update from the\nretained sensitivities. The differential-Jacobian infinity-norm computation and\nits outward rounding remain in their original order; a mixed capacitor/inductor\nprobe produced an exactly equal old and new bound.\n\nThe Schur result is only a contractive predictor. It is attempted at most once\nper implicit solve, must reduce the residual below 90% of its prior value under\nthe normal line search, and reserves one iteration for the exact coupled sparse\nNewton block. Future sensitivity evidence, changed switch topology, nonfinite\nupdates, singular reduced systems, and evidence outside the bounded age window\nare rejected. A failed contraction restores the base algebraic guess and\nrecomputes the base residual before the exact path proceeds. Periodic\nindependent replay remains unchanged.\n\nDirect mixed C+L sparse-update comparisons measured reductions from 35% to 73%\nover the exact coupled block across the tested dimensions. Against the exact\npreceding candidate, nonlinear capacitor/diode simulations measured mean\nend-to-end reductions of 2.957% at 64 algebraic unknowns and 3.692% at 128,\nwith maximum state delta `1.0408340855860843e-17`. Mixed capacitor/inductor\nsimulations measured 1.084% at 64 algebraic/32 dynamic unknowns and 0.545% at\n128 algebraic/64 dynamic unknowns, with maximum state delta\n`4.336808689942018e-19`.\n\n### ULP-aware two-step evidence age\n\nThe sensitivity-age guard now evaluates the same mathematical two-step window\nwith a scale-aware tolerance of eight ULPs. This admits accumulated timestamps\nsuch as `2.0000000000000053` steps without widening the intended age policy.\nFuture evidence, genuinely older evidence, changed switch topology, failed\ncontraction, and exact coupled fallback behavior remain unchanged.\n\nAgainst the immediately preceding fixed-ratio guard, three balanced rounds\nmeasured mean reductions of 3.751% at 64 algebraic unknowns and 2.197% at 128\nalgebraic unknowns on mixed C+L workloads, with minimum round reductions of\n3.558% and 1.959%. Maximum dynamic-state deltas were\n`1.734723475976807e-18` and `3.469446951953614e-18`; maximum metric deltas were\n`1.681e-10` and `1.531e-10`. Smooth and pulsed controls were timing-neutral\nwithin local noise, while the 64-unknown switched case measured a 0.827% mean\nreduction with exact state and a `6.441069899665308e-12` maximum metric delta.\n\nAn attempted three-step extension was rejected after correcting the benchmark\nbaseline. The earlier apparent mixed-workload gain compared three steps with a\nstricter ratio test rather than with the implemented ULP-aware two-step guard.\nAgainst the true current guard, the mixed workloads exposed no additional\neligible three-step evidence, while pulsed cases could pay extra predictor cost.\nThe production policy therefore remains mathematically two steps.\n\n### Compiled simulation breakpoint schedules\n\nFor the exact built-in `Circuit` type, `Simulator.run` now compiles the active\nbreakpoint providers once per run and deduplicates pure built-in waveform\nschedules by timing signature. Pulse levels, sine amplitudes, and piecewise-\nlinear values do not affect their event times, so equivalent schedules share one\nprovider. Public `Circuit.breakpoints` behavior is unchanged, custom waveforms\nremain individually observable, circuit subclasses keep their virtual\n`breakpoints` dispatch, and every new simulation run recompiles current element\nassignments.\n\nAgainst the exact ULP-aware baseline, three balanced rounds measured mean\nreductions of 11.638% and 16.243% for 16- and 32-channel pulsed diode networks,\nwith minimum round reductions of 11.322% and 15.635%. Sixteen- and 32-channel\nswitched networks measured mean reductions of 18.306% and 22.102%, with minimum\nround reductions of 17.763% and 21.093%. State traces, reported metrics,\nrejection counts, and deterministic candidate-work counts were exactly equal.\nAn isolated runtime-path check reduced repeated-schedule query time by 98.177%\nand also improved unique built-in and custom schedules by 1.285% and 7.961%,\nrespectively, because the per-run provider list removes repeated element lookup.\n\n### Demand-gated sparse-kernel compile reuse\n\nGenerated sparse assembly source depends on topology but reads resistance,\ndiode, switch, state, and sampled-input values from the live circuit. The\ndemand-gated sparse kernel therefore now uses a bounded 128-entry source cache\nacross identical topologies. The startup residual kernel remains per-circuit:\na broader cache was rejected because its source hashing regressed workloads\nthat never reached the heavy sparse-assembly gate.\n\nAgainst the breakpoint-optimized baseline, repeated 16- and 32-channel switched\ntopologies measured incremental mean reductions of 3.973% and 5.938%, with\nminimum round reductions of 3.223% and 5.476%. State and metric traces and all\ndeterministic work counts were exactly equal. Smooth, mixed, and short pulsed\nworkloads do not invoke this cache; their measured timing variation is therefore\ntreated as ambient benchmark noise rather than a causal code-path effect.\n\n### Hot-topology sparse-kernel adoption\n\nThe source cache above removed repeated Python compilation, but each newly\nconstructed circuit still repeated the 256-call fallback warmup before asking\nfor the already compiled function. The retained design now records a compiled\nkernel under an exact structural key containing the CSC pattern, device stamps,\nconstraint stamps, and inductor-state mapping. The registry is a lock-protected\n128-entry LRU. The first circuit for a topology still has to satisfy the original\ndemand gate; later exact built-in `Circuit` instances with the same topology\nadopt the proven kernel on their first eligible sparse assembly.\n\nThe kernel continues to read resistance, diode, switch, dynamic-state, and\nsampled-input values from the receiving circuit. Parameter mutation therefore\nremains live. Circuit subclasses, distinct structures, and cold topologies keep\nthe original fallback and demand-gate behavior. Focused tests cover exact\nfallback equivalence, parameter mutation, distinct-topology misses, first-call\nhot adoption, and LRU eviction.\n\nAgainst the source-cache baseline, five balanced rounds of 25 paired runs\nmeasured mean reductions of 3.829% and 4.069% for repeated 16- and 32-channel\nswitched topologies. Minimum round reductions were 3.636% and 3.602%. State and\nmetric traces and deterministic work counts were exactly equal.\n\n### Duplicate built-in switch-control sampling\n\nThe hot switch profile then showed repeated `Pulse.value` evaluation for 32\nnumerically identical built-in control waveforms. For exact built-in circuits\nwith at least 32 switches, construction now compares signed-zero-aware value\nkeys for immutable built-in controls. Only a plan that actually finds duplicate\nvalues installs a specialized sampler. Unique built-ins, custom waveforms,\nsmaller circuits, and subclasses execute the original sampling method unchanged.\nCustom providers remain observable once per switch. Direct control reassignment\nrefreshes the plan through a weak callback, so no circuit-to-switch reference\ncycle is introduced and changed control topology remains visible to the chord\nguard.\n\nAgainst the hot-topology baseline, five balanced rounds of 25 paired runs on the\n32-channel switched workload measured a 1.683% mean reduction with a 1.433%\nminimum round reduction. A 32-channel unique-control matrix was neutral at\n+0.266% mean with a -0.055% minimum round result. All state and metric traces\nwere exactly equal. An earlier per-evaluation identity-checking plan was rejected\nbecause its invalidation and mapping overhead erased the waveform-call savings.\n\nAcross both retained changes, the same five-round comparison against the exact\npre-loop baseline measured cumulative reductions of 4.114% at 16 channels and\n5.985% at 32 channels, with minimum round reductions of 3.646% and 5.832%.\nEvery state trace, reported metric, rejection count, and deterministic\ncandidate-work count was exactly equal.\n\n### Bounded SuiteSparse KLU symbolic/numeric reuse\n\nThe next profile identified repeated SuperLU symbolic and numeric factorization\ninside large batched differential-sensitivity solves. BAB-CS now has an optional\n`ctypes` adapter for a compatible system SuiteSparse KLU 2 library. KLU symbolic\nanalysis and numeric storage live in a bounded 128-entry per-thread LRU. Exact\nstructure identity avoids repeated tuple hashing in hot circuits, exact\nstructural equality still permits reuse across separately constructed circuits,\nand weak factor references allow eviction without invalidating the public\nreusable-factorization contract. A stale or cross-thread factorization restores\nits immutable matrix values into an appropriate workspace before solving.\n\nThe KLU workspace disables row scaling so its exposed U diagonal remains on the\noriginal matrix scale. Every factor and refactor must pass the existing absolute\nminimum-pivot gate, singular and nonfinite results fail closed, and automatic\nKLU failure retries with SciPy. Each multi-right-hand-side solve uses a distinct\nowned Fortran buffer. An earlier prototype accidentally allowed `ctypes` to\noverwrite a transposed view of the read-only cached right-hand sides; the retained\nimplementation forces a copy and has a direct mutation regression test.\n\nAutomatic adoption is deliberately narrow. Generic `auto` factorization keeps\nthe existing dense/SciPy selection. KLU is selected automatically only for\nnative sensitivity systems with at least 128 algebraic unknowns and 32 right-\nhand sides, where repeated structure and batching amortize the adapter cost.\n`linear_backend=\"klu\"` remains available for explicit research use, while a\nmissing NumPy installation or compatible shared library fails clearly.\n\nThree balanced rounds with four warmups and 15 paired runs per round compared\nthe retained implementation against commit `259a836`. Mean end-to-end reductions\nwere 2.048% for the 32-channel sine case, 4.166% for mixed capacitor/inductor\nchannels, 4.293% for pulsed channels, and 3.140% for switched channels. Minimum\nround reductions were 1.484%, 3.674%, 4.191%, and 2.780%, respectively. Every\nstate trace, reported metric, rejection count, and deterministic candidate-work\ncount was exactly equal. Final factor-plus-batched-solve kernels were about 22%\nfaster for the mixed case and 13% faster for the switched case on the local\nSuiteSparse KLU 2.3.6 installation.\n\n### KLU hot-path safety and boundary reduction\n\nThe first follow-up hypothesis was native sparse numerical-value ownership. A\ndirect 128-unknown, 32-right-hand-side profile rejected that priority ordering:\nlist-to-tuple conversion cost about 0.28 microseconds and copying the immutable\ntuple into KLU's NumPy value buffer cost about 3.43 microseconds, while the\nPython U-pivot scan cost about 37 microseconds and sparse infinity-norm\nconstruction cost about 20 microseconds. The retained work therefore attacks\nthe measured safety and boundary costs before changing public matrix ownership.\n\nThe KLU workspace now calculates the absolute pivot threshold from its owned\nnumeric values with a vectorized sparse row reduction, rejects nonfinite values\nbefore native factorization, and validates the unscaled U diagonal with a\nvectorized finite/minimum scan. This preserves the same absolute singularity\ncontract. The workspace also retains stable `ctypes` pointers for its structural\nand numeric arrays and solves directly into the independent C-order `(nrhs, n)`\nresult. That same memory is column-major `(n, nrhs)` to KLU, so no intermediate\ntranspose-copy is needed and later solves cannot mutate earlier results. The\ndirect layout reduced the isolated solve from about 7.93 to 6.89 microseconds for\ncapacitor channels and from 13.10 to 10.93 microseconds for mixed channels, with\nbit-identical solutions. Against the exact pre-layout wheel, mean end-to-end\nreductions were 1.530%, 1.460%, 0.497%, and 1.012% for sine, mixed, pulsed, and\nswitched workloads. The pulsed minimum round was -0.469%, so this isolated\nincrement remains small relative to timing noise even though the cumulative\ncomparison below is stable.\n\nNative sensitivity post-processing now gathers inductor voltage columns in\nbatches instead of issuing one NumPy operation per inductor. Read-only\ncapacitance and inductance arrays are reused while live element-value mutation\nstill refreshes them. Native NumPy right-hand-side matrices are validated from\ntheir two-dimensional shape rather than by iterating over every row; generic\nPython sequences retain the original per-row validation.\n\nAgainst the exact pushed KLU baseline `f21b383`, three balanced rounds with four\nwarmups and 15 paired runs per round measured mean reductions of 4.131% for\n32-channel sine, 6.814% for mixed capacitor/inductor channels, 6.020% for pulsed\nchannels, and 6.282% for switched channels. Minimum round reductions were\n3.768%, 6.466%, 4.958%, and 5.668%, respectively. State traces, metrics,\nrejection counts, and deterministic candidate-work counts were exactly equal.\nThe isolated native sensitivity kernel fell from about 91.7 to 56.8\nmicroseconds for capacitor-only channels and from about 117.1 to 83.3\nmicroseconds for mixed channels in the final local profile; these microsecond\nfigures remain sensitive to host noise and are not portable guarantees.\n\n### Fused private sparse assembly and KLU factor/solve\n\nThe next boundary probe measured the complete generated-kernel-to-sensitivity\npath rather than the tuple copy in isolation. At 128 algebraic unknowns and 32\nright-hand sides, returning the generated scalar value list directly and\nperforming factorization plus the first batched solve in one KLU workspace call\nreduced the microkernel from about 42.4 to 41.4 microseconds while still\nconstructing the reusable factorization required by projection correction.\nDirect NumPy and `array('d')` stamping were rejected because scalar writes made\nthe generated arithmetic slower.\n\nThe retained implementation keeps the public `SparseMatrix` and stale-factor\ncontracts unchanged. Only the exact built-in native-sensitivity path may request\nraw generated values. KLU copies those values into its owned numeric buffer,\nsolves the batched sensitivity system, and returns both independent solutions\nand an immutable reusable factorization handle. Automatic KLU failure still\nreconstructs the sparse matrix and falls back to SciPy.\n\nAcross 11 isolated rounds, native sensitivity improved by 3.433% on average for\ncapacitor-only channels and 3.336% for mixed channels; minimum round reductions\nwere 0.943% and 1.834%. In the balanced whole-run comparison, the isolated\nincrement was near timing noise for smooth sine and mixed cases, while pulsed\nand switched cases measured 2.241% and 0.978% mean reductions with 1.652% and\n0.955% minimum reductions. Every state, metric, rejection, and deterministic\nwork trace was exactly equal.\n\n### Jacobian-only native sensitivity assembly\n\nThe next profile showed that native sensitivity consumed only algebraic\nJacobian values, but the private generated sparse kernel still allocated and\nstamped a complete residual, calculated diode currents, and replaced the\naccepted diode-current cache. A separate generated Jacobian-only kernel now\nstamps the same live resistor, switch, diode, and constraint derivatives without\nconstructing unused residual evidence. Public residual-plus-Jacobian assembly,\nsubclass dispatch, limiting rules, topology, and SciPy fallback remain\nunchanged. The smaller compiler activates eagerly only at the existing\nqualified KLU crossover of at least 128 algebraic unknowns and 32 right-hand\nsides; below that crossover the previous demand and fallback paths remain\nauthoritative.\n\nAgainst exact commit `351a8e0`, 11 isolated paired rounds reduced 32-channel\nnative sensitivity by 14.404% on average for capacitor-only channels and\n11.506% for mixed channels. Minimum round reductions were 13.225% and 10.787%.\nThe generated Jacobian values were exactly equal before and after live resistor\nand diode parameter mutation, and the kernel does not alter residual or\naccepted-current caches.\n\nThree balanced 32-channel rounds measured mean whole-run reductions of 3.742%\nfor sine, 4.182% for mixed C+L, 7.960% for pulsed, and 0.882% for switched\nworkloads. Minimum round reductions were 1.165%, 2.885%, 6.608%, and 0.471%.\nTwo balanced 64-channel rounds measured mean reductions of 3.723%, 4.286%,\n6.850%, and 6.171%, with minimum reductions of 2.685%, 4.163%, 6.823%, and\n5.480%. State, metric, rejection, and deterministic work traces were exactly\nequal in every retained comparison.\n\n### Independent mixed-sensitivity gather ownership\n\nThe Jacobian-only profile exposed one remaining large Python-visible copy in\nmixed capacitor/inductor systems. NumPy advanced indexing already returns an\nindependent writable sensitivity gather, but the inductor voltage path copied\nthat gather a second time before subtracting negative-node columns. Removing\nthe redundant copy preserves source-array isolation and all public result\nownership while leaving capacitor-only paths unchanged.\n\nAgainst the exact Jacobian-only candidate, 11 isolated rounds reduced the\n32-channel mixed native-sensitivity call by 3.519% on average with a 2.564%\nminimum round reduction. Three balanced 32-channel mixed runs measured a 1.133%\nmean end-to-end reduction with a 0.539% minimum round reduction. Two balanced\n64-channel mixed runs measured a 0.832% mean reduction with a 0.076% minimum.\nState, metric, rejection, and deterministic work traces were exactly equal.\n\n### Deferred-reference Jacobian materialization\n\nThe next ownership profile separated native sensitivity evidence from dense\ndynamic-Jacobian storage. Deferred-reference candidate steps need the batched\nalgebraic sensitivities and conservative infinity norm, but they do not consume\nthe dense dynamic Jacobian unless a later stiffness or bound checkpoint forces\nimplicit authority. At 64 or more dynamic states, unscheduled reference steps\nnow omit that quadratic allocation and scaling. Scheduled references keep the\nprevious eager path, and a forced reference materializes the matrix from the\nsame owned sensitivities before attempting the guarded sparse chord update.\n\nThe crossover is deliberately evidence-gated at 64 dynamic states. At 32\nchannels the whole-run effect remained timing noise. Against exact commit\n`a0d67b5`, three balanced 64-channel rounds at a reference interval of eight\nreduced mixed, pulsed, and switched workloads by 1.137%, 1.363%, and 1.613% on\naverage. Minimum round reductions were 0.552%, 0.675%, and 0.992%. Exact state,\nmetric, accepted/rejected work, and fallback traces were preserved. A\n128-channel follow-up remained positive for mixed and pulsed workloads, while\nswitched timing was inconclusive; the retained 64-state crossover therefore\nrests on the all-positive 64-channel evidence rather than a monotonic-scaling\nclaim.\n\nInstrumentation also ruled out broader cache policy as the next gain. Each\nprofiled 32- and 64-channel run incurred one KLU workspace miss followed only by\nidentity hits, zero evictions, one generated Jacobian-kernel compilation, and\none numeric refactor per new sensitivity. Existing symbolic reuse is therefore\nalready complete for these workloads. The remaining factorization opportunity\nis fewer justified numeric refreshes or a different backend interface, not a\nlarger cache.\n\n### Independent evidence-controlled replay refinement\n\nDirect timing showed that periodic independent replay consumed about 27.1% of\nthe 32-channel sine run, 42.6% of the mixed C+L run, 16.5% of the pulsed run,\nand 22.8% of the switched run at a 16-step anchor interval. Replay still covers\nthe complete accepted interval; the opportunity was subdivision count, not\nanchor omission.\n\nMixed C+L trapezoidal replay now starts at `minimum_anchor_substeps` and computes\nan ordered local quadrature defect from three independent replay derivatives.\nIf the scaled defect exceeds `anchor_embedded_error_cap`, the complete replay\nrestarts from the trusted anchor at a cubically predicted finer subdivision.\nThe original `anchor_substeps` count remains the ceiling and therefore the\nfail-closed baseline. Nonfinite evidence rejects the step. Pure-C/L\ntrapezoidal policies, Backward Euler, ineligible BDF2 topologies, and disabled\nadaptivity retain their previous execution without estimator overhead; exact\nevent boundaries still reset history.\n\nFor the 32-channel mixed workload, replay work fell from 322 to 162 steps at a\n16-step anchor profile and from 201 to 101 steps at a 50-step anchor. The\ncorresponding median total times fell from about 87.33 to 72.89 milliseconds\nand from 71.53 to 62.24 milliseconds. A three-round balanced comparison against\ncommit `4511c46` measured a 13.450% mean end-to-end reduction with a 12.850%\nminimum round reduction for the mixed workload. Pure sine, pulsed, and switched\ncases retained their previous work and remained within local timing noise.\n\nThe adaptive mixed endpoint differed from the former four-substep authority by\n`1.776e-8` in maximum absolute state and `6.712e-10` in maximum reported metric\nfor the balanced case. In a separate authority calibration, the adaptive\nendpoint was 0.863 weighted RMS from an eight-substep replay, versus 0.091 for\nthe fixed four-substep replay; its maximum embedded replay evidence was 0.486\nagainst the default cap of 1.25. These are bounded calibration results, not a\nclaim that two substeps are universally equivalent to eight.\n\n### Qualified switched BDF2 replay refinement\n\nBDF2 replay cannot use only its multistep defect because each independent\nwindow begins without history and therefore takes one Backward Euler startup\nstep. The retained estimator measures both terms. For startup step `h`, the\nstate defect is `0.5 h (f_1 - f_0)`. For a variable BDF2 step `h` following a\nstep `k`, the defect is\n`h^2 (h + k) / (3 (k + 2h))` multiplied by\n`(f_{n+1} - f_n) / h - (f_n - f_{n-1}) / k`. Both are scaled by the same\nabsolute and relative state tolerances. The complete replay restarts from the\ntrusted anchor when the maximum evidence exceeds `anchor_embedded_error_cap`.\nBecause startup is second order, subdivision prediction uses a square-root\nlaw; the configured fixed count remains the ceiling.\n\nBroad application did not pass the retention gate. A BDF2-only defect that\nignored startup appeared faster on source-pulsed cases but under-reported the\nfirst-step error. Adding the required startup evidence made the pulsed workload\n0.296% slower on average. Smooth sine replay was 14.630% slower before the\ntopology gate, and mixed C+L replay retried to the fixed ceiling. The retained\npath is therefore limited to capacitive circuits with a built-in `Pulse` or\npiecewise-linear switch control; custom controls, smooth controls, source-only\npulses, inductive circuits, and disabled adaptivity retain fixed replay.\n\nAgainst exact commit `9a804a3`, three balanced rounds with four warmups and 15\npaired samples per round produced the following switched-capacitive results:\n\n| Channels | Mean reduction | Minimum round reduction | Maximum WRMS versus fixed eight |\n| ---: | ---: | ---: | ---: |\n| 1 | 10.307% | 9.127% | 0.263 |\n| 16 | 9.094% | 8.853% | 0.264 |\n| 32 | 11.229% | 10.923% | 0.266 |\n| 64 | 11.116% | 10.388% | 0.384 |\n\nReplay steps fell from 390 to 263 in every case. Replay circuit evaluations\nfell from 393 to 269 through 32 channels and to 271 at 64 channels. Candidate\nand scheduled-reference work, rejection counts, accepted time grids, and event\nboundaries were unchanged. Maximum adaptive-versus-fixed-four state deltas were\n`2.799e-9`, `3.219e-9`, `3.667e-9`, and `1.255e-8` from one through 64\nchannels. Fixed four remained closer to fixed eight, so the result is a bounded\nperformance trade rather than a claim of increased reference accuracy.\n\n**Current semantic correction:** the table and replay counts above remain\nhistorical evidence for exact commit `9a804a3`. The current source forces\nindependent replay at event boundaries before multistep history reset, so event\nresets can no longer suppress authority work. The historical timing and replay\ncounts shall not be promoted as current release evidence without a fresh frozen-\nsource benchmark.\n\n### Current cumulative scaling\n\nA fresh cumulative comparison used five warmups and 15 paired runs in each of\nthree balanced rounds. It includes all retained loops above and compares the\ncurrent forced-dense and `auto` paths rather than reusing the earlier dense\nbaseline.\n\n| Algebraic unknowns | Dense mean median | Auto mean median | Mean reduction | Minimum round reduction |\n| ---: | ---: | ---: | ---: | ---: |\n| 32 | 0.095483697 s | 0.036160544 s | 62.129% | 61.958% |\n| 64 | 0.382285888 s | 0.030522380 s | 92.016% | 91.958% |\n| 128 | 1.973011725 s | 0.046981886 s | 97.619% | 97.605% |\n\nThe 32-unknown traces were exactly equal. Maximum dense-versus-auto dynamic\ntrace deltas were `2.1104364783530727e-11` at 64 unknowns and\n`1.96882926628561e-11` at 128 unknowns; both complete paths pass the same\nresidual, nonlinear, bound, comparison, and long-horizon qualifications.\n\nThe BDF2 replay regression is an intentional correctness change outside the\ndefault trapezoidal reference configuration. Configurations that explicitly use\n`reference_method=\"bdf2\"` should therefore expect corrected anchor trajectories\nrather than baseline equality.\n\n### Repeated-topology circuit construction\n\nParameter sweeps, Monte Carlo studies, and comparison matrices repeatedly build\nthe same structural circuit with different numerical values. Profiling exact\ncommit `dd8145e` showed that these runs still rebuilt the algebraic CSC pattern,\nJacobian stamps, constraint stamps, differential-sensitivity right-hand sides,\nimplicit block layout, and generated residual source for every instance. The\nretained design now uses bounded 128-entry structural caches whose keys contain\nonly ordered terminal indices, branch positions, and dynamic-state placement.\nCached values are frozen sparse templates, immutable stamps, read-only tuple\nright-hand sides, and compiled functions. Resistance, capacitance, inductance,\nsource, diode, switch, initial-state, and waveform values remain owned by and\nread live from each circuit.\n\nThe CSC builder now buckets rows by column instead of repeatedly scanning the\ncomplete position set. The implicit coupled block reuses its immutable layout,\nbut rebuilds each circuit's `1/C` and signed `1/L` multipliers independently.\nGenerated residual code is cached by structural stamps before source generation,\nso a cache hit does not reconstruct or hash a large source string. Exact built-in\nelements use direct dataclass construction during normalized copying; subclasses\nretain the general `dataclasses.replace` path and therefore keep their runtime\ntype and extension semantics.\n\nFive balanced construction rounds and three balanced build-plus-one-evaluation\nrounds compared the combined retained path with exact commit `dd8145e`:\n\n| Workload | Construction mean | Construction minimum | Build + evaluation mean | Build + evaluation minimum |\n| --- | ---: | ---: | ---: | ---: |\n| 16 capacitor/diode channels | 72.491% | 71.965% | 64.058% | 63.728% |\n| 32 capacitor/diode channels | 73.529% | 73.265% | 67.010% | 66.067% |\n| 64 capacitor/diode channels | 75.787% | 75.619% | 69.352% | 68.968% |\n| 64 mixed capacitor/inductor channels | 75.356% | 75.210% | 69.445% | 69.338% |\n| 128 capacitor/diode channels | 78.326% | 78.228% | 72.768% | 72.565% |\n\nThe topology-cache portion alone reduced construction by 50.993% to 52.508%\nagainst the same baseline. The exact-built-in normalization kernel reduced its\nisolated copy loop by 65.719%. A final order-preserving pass fused exact-type\nclassification, parameter validation, constraint collection, and first-seen node\nindexing while retaining independent subclass `isinstance` behavior and duplicate-\nname error precedence. A simulation-only comparison deliberately started timing\nafter construction: all state, metric, rejection, and deterministic work traces\nwere exactly equal, while mean timing varied from a 0.543% regression to a 0.509%\ngain. The retained claim is therefore constructor and ensemble latency, not faster\nsimulation arithmetic.\n\n## Local Validation\n\n- Focused replay, Jacobian, nonlinear, comparison, accuracy, failure-gate, and\n  long-horizon regression groups passed before the full run.\n- Full current-source qualification on August 25, 2026 with SciPy 1.18.0 and\n  SuiteSparse KLU 2.3.6, `BABCS_LONG_TESTS=1`, and\n  `BABCS_VERY_LONG_TESTS=1`: 229 tests passed in 56.596 seconds, with zero skips.\n- Two independent `bab_cs-1.1.0-py3-none-any.whl` builds were byte-identical.\n- Local candidate wheel SHA-256:\n  `761462fd7c451d33a111162e8a55a225920e0646ac72544a542db592ee3dde82`.\n- Clean dependency-free installed-wheel qualification: 229 tests passed in\n  53.080 seconds with 57 expected optional-backend skips; `pip check` reported\n  no broken requirements.\n- The same clean installed wheel with SciPy 1.18.1, NumPy 2.5.2, and SuiteSparse\n  KLU 2.3.6: all 229 tests passed in 53.433 seconds with zero skips;\n  `pip check` reported no broken requirements.\n- Earlier source/installed comparison hashes were invalidated by the constructor\n  source and test changes. They remain historical evidence and must be regenerated\n  from the eventual exact release commit before qualification.\n- Fresh `ngspice-46` cross-implementation runs completed for `rc_step`,\n  `rl_step`, `diode_clip`, and `switched_rc`.\n\nThe external comparison remains cross-implementation evidence for the\ngenerated semantic mapping, not proof that BAB-CS is generally more accurate\nor faster than ngspice.\n\n## Remaining High-Value Work\n\n1. **Normalize-and-classify fusion:** the retained classifier removed most\n   repeated `isinstance` work, reducing a 20-instance 128-channel profile from\n   0.061 to 0.042 seconds. Normalized copying and classification remain separate\n   passes. A future fusion may retain the first validation failure while still\n   giving duplicate-name errors their existing precedence, but must preserve\n   input-object isolation and subclass constructors.\n2. **Compact structural-key formation:** cache hits still create terminal-index\n   tuples and several small derived tuples per circuit. Any reduction must keep\n   first-seen node ordering, branch ordering, exact element-family separation,\n   and collision-free topology identity.\n3. **Cache diagnostics and policy evidence:** deterministic work reports should\n   expose structural, residual, implicit-layout, KLU, and SciPy cache hits,\n   misses, evictions, refactors, and fallbacks before cache policy becomes user-\n   configurable.\n4. **Backend-interface numeric refresh:** KLU symbolic reuse is already complete\n   in measured runs. Further solver work should target an interface that can\n   refresh numeric factors without unsafe caller-buffer borrowing or redundant\n   public-result copies.\n5. **Projection residency only after renewed profiling:** current projection\n   conversion cost is small relative to solves. Any retained change must remain\n   lazy, preserve independent results, and demonstrate an end-to-end gain.\n6. **Authority-refresh semantics before scheduling:** a future dynamic anchor\n   policy must distinguish event-driven history reset from independently\n   recomputed authority, honor exact event boundaries, and enforce a hard maximum\n   elapsed authority age. The current probe found no safe performance gain, so\n   this is a correctness prerequisite rather than the next optimization.\n\nReusable KLU scratch/result residency is no longer an active target. Borrowing\nthe result would violate independent ownership, while a safe scratch-plus-copy\nprototype regressed isolated solves by about 3.3% to 12.4%. NumPy weighted-RMS\nand 128-device diode batches were also rejected because their isolated vector\ngains did not survive balanced whole-run tests. Reactive-value invalidation,\ngenerated residual-plus-norm fusion, and broad projection ownership were already\nbelow their retention thresholds.\nAn exact-state probe rejected shared accepted-evaluation Jacobian caching: the\nstiffness evaluations do not use the same differential states as the preceding\nblock linearizations. Direct profiling also rejected standalone sparse tuple\nownership; the retained fused path removes only private assembly boundaries and\nreturns the required reusable handle. Direct cache instrumentation then found\none initial KLU workspace miss, identity hits thereafter, and no evictions in\nthe qualified workloads, so broader cache policy is not the next performance\ngain. Cross-anchor refinement retention reduced replay work but slowed both\nmeasured workloads and was not uniformly closer to eight-substep authority. A\nstandalone Backward Euler derivative-defect prototype was ordered under\nrefinement but repeatedly selected the maximum subdivision under the default\ncap, increasing RC replay work. Cross-anchor retention and general Backward\nEuler adaptation were rejected; the same startup term is retained only inside\nthe qualified switched BDF2 estimator. Dynamic anchor scheduling was then\nrejected as the next replay optimization. Over 256 uninterrupted accepted\nsteps, fixed replay intervals of 16, 32, 64, and 128 each performed 1,024 replay\nsteps; fewer anchors simply reintegrated longer complete windows. In the\nswitched BDF2 workload, intervals above the event spacing appeared 31--34%\nfaster, but periodic independent replay fell to zero because event handling\nreset the step counter and adopted the event state as the next anchor. The\nremaining state delta was small, but no independent authority justified it.\nAdaptive subdivision does not justify older or omitted authority, and an event\nhistory reset must not be treated as an authority refresh.\n\nThe cross-anchor retention prototype reduced one-channel retries from 31 to 17\nand replay steps from 3,248 to 3,056, but increased mean elapsed time by 7.382%.\nAt 32 channels it reduced retries from eight to four and replay steps from 752\nto 672, but increased mean elapsed time by 16.226%. Its weighted-RMS distance\nto fixed eight-substep authority improved from 688.55 to 595.99 in the first\ncase and worsened from 359.92 to 367.67 in the second. Lower retry counts were\ntherefore neither a timing win nor uniform authority improvement.\n\nThe Backward Euler prototype used the ordered local defect\n`0.5 h (f_n - f_{n-1})` with square-root refinement scaling. On the default RC\nqualification, its early anchors repeatedly retried at the configured maximum\nfour substeps, and total replay work exceeded the existing fixed-four path.\nLarger evidence caps could reduce work, but changing the default authority cap\nto rescue one estimator would weaken the established policy. The prototype is\nnot retained as a general Backward Euler policy; its startup defect remains\nnecessary inside BDF2 replay.\n\nA weak reactive-value invalidation prototype was also rejected. It reduced the\nisolated cached-scale check from about 0.97 to 0.11 microseconds for 32 capacitor\nchannels and from 1.57 to 0.11 microseconds for 32 mixed channels. End-to-end\nmeans improved by only 0.096% to 0.513%, while sine and pulse minimum rounds\nregressed by 0.095% and 0.070%. Exact state and metric traces were preserved, but\nthe gain did not justify adding mutation callbacks to every capacitor and\ninductor. The simpler live tuple check remains authoritative.\n\nA NumPy diode-family batch was rejected at the current automatic crossover. For\n16 and 32 diodes, scalar arithmetic took about 2.14 and 4.05 microseconds while\nthe vector form took about 7.62 and 7.74 microseconds. Vector stamping crossed\nover only around 64 devices and became materially faster at 128, but NumPy\ntranscendental and division ordering introduced small nonzero conductance deltas.\nThe generated scalar kernel therefore remains authoritative for current\n32-channel KLU adoption. Any future batch must use a larger evidence-gated\ncrossover and prove that its numerical deltas do not alter accepted trajectories.\n\nAn exact-index evaluation-accounting prototype was also rejected. It reduced\nthe isolated accounting kernel by 15.6% to 18.9%, but end-to-end measurements\nregressed by 0.958% at 32 unknowns and 0.383% at 64 unknowns, while the\n128-unknown gain was only 0.260%. The qualified dictionary-backed public result\nconstruction and accounting path is retained.\n\nAn exact generated residual-plus-norm prototype was rejected as well. Its\nunrolled, single-pass, deterministic `NaN`-propagating norm reduced isolated\n64-value residual calls by 6.2%, but was neutral at 128 values and regressed by\n1.0% at 256 values. Three balanced end-to-end rounds reduced mean runtime by\nonly 0.214% at 64 algebraic unknowns and regressed by 0.130% at 128 unknowns,\nwith a worst round regression of 0.547%. State and metric traces were exactly\nequal. The extra generated code and paired private APIs therefore do not meet\nthe retention threshold; evidence is preserved in\n`/tmp/babcs-residual-norm-gain.jsonl`.\n\nA deferred dense differential-Jacobian prototype was also rejected. It retained\nthe gathered sensitivity blocks after computing the norm and materialized the\ndense matrix only when a later chord update reached it. Exact 32-channel traces\nwere preserved, but sine regressed by 1.411% on average with a 3.378% worst\nround. Mixed and pulsed means improved by only 0.419% and 1.099%, and each had a\nnegative round of 0.472% and 0.653%. Switched runs improved by 0.607% with a\n0.487% minimum, which did not justify a switch-only ownership mode and its\nadditional cached-state semantics. Evidence is preserved under\n`/tmp/babcs-lazy-jacobian-benchmark/`.\n\nA direct NumPy KLU right-hand-side clone was rejected too. Replacing the\nexplicit C-order allocation and assignment with `source.copy(order=\"C\")`\nreduced the isolated clone by 28.56% at 32 by 128 values and 12.04% at 64 by\n256 values. That local saving did not survive the native solve: 32-channel\ncapacitor-only and mixed sensitivity means improved by only 0.641% and 0.548%,\nwith negative rounds of 0.753% and 2.005%. Exact end-to-end traces were also\nneutral or worse: sine and mixed means changed by only 0.020% and 0.076%, while\nthe switched workload regressed by 0.684% on average and 1.965% in its worst\nround. The explicit owned buffer remains authoritative. Evidence is preserved\nunder `/tmp/babcs-klu-copy-benchmark/`.\n\nA cached COLAMD pre-permutation prototype was also rejected. It recovered the\nfirst SuperLU factorization's column ordering, rebuilt the fixed CSC column\nlayout once, performed later numeric factorizations with `NATURAL` ordering,\nand scattered single- and multi-right-hand-side solutions back to original\ncoordinates. Direct repeated factor-plus-solve workloads improved by 8.324%,\n17.385%, and 24.711% at 64, 144, and 256 unknowns. Whole nonlinear simulations,\nhowever, improved by only about 0.3% at 128 unknowns and 0.5% to 1.5% on average\nat 256 to 512 unknowns, with negative rounds at every larger size. State deltas\nremained at floating-point roundoff and reported metrics were unchanged, but\nthe mapping and copy complexity did not meet the end-to-end retention gate.\nExplicit symbolic/numeric reuse therefore remains a backend-interface\nopportunity rather than an in-tree pre-permutation workaround. Evidence is\npreserved under `/tmp/babcs-perm-benchmark/`.\n",
      "order": 10,
      "path": "PERFORMANCE_OPTIMIZATION_AUDIT.md",
      "readingMinutes": 46,
      "sha256": "23f01075a152c7ec17d662a7c5b86f43f6317fb2b19dbeead50099960b7d75a7",
      "summary": "This document records a locally validated candidate optimization pass relative to commit 8dad1f1bb41acf343c36dae8daeb932c137fb268 on August 24, 2026. The candidate is not a release qualification or publication claim until it is…",
      "title": "Bounded-Authority-Based-Circuit-Simulation Performance Optimization Audit",
      "wordCount": 9934
    },
    {
      "category": "Tests and Comparisons",
      "conceptIds": [
        "candidate-method",
        "python-wheel",
        "ci",
        "api"
      ],
      "headings": [
        {
          "id": "qualification-summary-evidence",
          "level": 1,
          "text": "Qualification Summary Evidence"
        },
        {
          "id": "canonical-owners",
          "level": 2,
          "text": "Canonical Owners"
        }
      ],
      "kind": "Evidence",
      "markdown": "# Qualification Summary Evidence\n\n`qualification-summary.json` is generated by the release-qualification workflow\nand is a required, checksummed manifest artifact. It replaces manually copied\nsurface counts with values derived from canonical repository owners.\n\nGenerate a development summary with a prepared evidence directory:\n\n```bash\nPYTHONPATH=src python tools/release_evidence.py write-qualification-summary \\\n  --repository-root . \\\n  --evidence-dir artifacts/release \\\n  --benchmark-manifest benchmarks/manifest.json \\\n  --ci-workflow .github/workflows/ci.yml \\\n  --latest-public-release v1.0.0 \\\n  --output artifacts/release/qualification-summary.json\n```\n\nThe release workflow does not use `--allow-dirty`. A tracked dirty tree fails\nclosed.\n\n## Canonical Owners\n\n| Summary field | Canonical owner |\n| --- | --- |\n| Source commit and dirty state | Git `HEAD`, tracked index, and tracked worktree |\n| Project, package, licence, requirement, wheel | `src/babcs/_project.py` |\n| Test methods and modules | Python syntax in `tests/test_*.py` |\n| Bounded candidate methods | `src/babcs/candidates.py` |\n| Benchmark cases and configurations | `benchmarks/manifest.json` |\n| CI Python versions | `.github/workflows/ci.yml` |\n| Workflow run identity | release evidence environment files |\n| Latest public release | GitHub Releases API at qualification time |\n\nThe release manifest validates that the summary names the same source commit,\ncandidate tag, creation time, workflow identity, package version, and wheel, and\nthat it does not claim a dirty source tree is clean. The artifact does not\nrepresent human release approval.\n",
      "order": 11,
      "path": "QUALIFICATION_SUMMARY.md",
      "readingMinutes": 1,
      "sha256": "38b4a76a592c44c036bbee5c4f8d4c971cb2c31483edaa9aa93ae659ec668d00",
      "summary": "qualification-summary.json is generated by the release-qualification workflow and is a required, checksummed manifest artifact. It replaces manually copied surface counts with values derived from canonical repository owners.",
      "title": "Qualification Summary Evidence",
      "wordCount": 199
    }
  ],
  "featuredDocuments": [
    "ARCHITECTURE.md",
    "METHOD_OBSERVATORY.md",
    "BOUND_COVERAGE_ATLAS.md",
    "EXTERNAL_COMPARISON.md",
    "POWER_STAGE_SANDBOX.md",
    "TEACHING_AND_REPRODUCIBILITY_LAB.md"
  ],
  "project": "Bounded-Authority-Based-Circuit-Simulation",
  "schemaVersion": 3,
  "shortName": "BAB-CS",
  "siteMetrics": {
    "comparison": {
      "assignments": 51,
      "caseIds": [
        "rc_step",
        "rl_step",
        "rlc_damped",
        "rlc_overdamped",
        "driven_rc",
        "lc_long",
        "diode_clip",
        "switched_rc"
      ],
      "cases": 8,
      "matrixRows": 154,
      "methodIds": [
        "active",
        "backward_euler",
        "bdf2",
        "bounded_ab2_fast",
        "bounded_backward_euler",
        "bounded_bdf2",
        "bounded_explicit_euler",
        "bounded_heun",
        "bounded_heun_fast",
        "bounded_rk23",
        "bounded_rk23_fast",
        "bounded_trapezoidal",
        "raw_ab2",
        "shadow",
        "trapezoidal"
      ],
      "methods": 15
    },
    "external": {
      "caseIds": [
        "rc_step",
        "rc_discharge",
        "driven_rc",
        "current_driven_rc",
        "rl_step",
        "rl_decay",
        "lc_long",
        "lc_offset",
        "rlc_damped",
        "rlc_overdamped",
        "rlc_driven",
        "diode_clip",
        "diode_rectifier",
        "diode_bias_recovery",
        "switched_rc",
        "switched_rl",
        "switched_rlc",
        "buck_like_reduced_order",
        "h_bridge_rl_reduced_order",
        "dc_link_rlc_reduced_order"
      ],
      "cases": 20,
      "categories": {
        "first_order_linear": 6,
        "nonlinear_diode": 3,
        "reduced_order_power_stage": 3,
        "resonant_and_rlc": 5,
        "scheduled_switching": 3
      },
      "mappedFeatures": 14,
      "referenceTool": {
        "name": "ngspice",
        "version": "ngspice-46 : Circuit level simulation program"
      }
    },
    "observatory": {
      "assignments": 42,
      "caseIds": [
        "rc_step",
        "rl_step",
        "rlc_damped",
        "lc_long",
        "diode_clip",
        "switched_rc"
      ],
      "cases": 6,
      "matrixRows": 126,
      "methodIds": [
        "candidate_ab2",
        "candidate_backward_euler",
        "candidate_bdf2",
        "candidate_explicit_euler",
        "candidate_heun",
        "candidate_rk23",
        "candidate_trapezoidal"
      ],
      "methods": 7
    },
    "powerStage": {
      "assignments": 19,
      "caseIds": [
        "buck_like_reduced_order",
        "h_bridge_rl_reduced_order",
        "dc_link_rlc_reduced_order"
      ],
      "cases": 3,
      "matrixRows": 57,
      "methodIds": [
        "candidate_ab2",
        "candidate_backward_euler",
        "candidate_bdf2",
        "candidate_explicit_euler",
        "candidate_heun",
        "candidate_rk23",
        "candidate_trapezoidal"
      ],
      "methods": 7
    },
    "sourceSha256": "04253a23d2a4b675628ac99a245a0bf300b7d7422e6f5e8bc3f6d336f354f143",
    "teachingLab": {
      "exerciseIds": [
        "01-mna",
        "02-convergence",
        "03-phase-versus-energy",
        "04-shadow-authority",
        "05-deterministic-packaging",
        "06-source-wheel-equivalence",
        "07-event-alignment",
        "08-bound-coverage",
        "09-fallback-forensics",
        "10-ngspice-mapping"
      ],
      "exercises": 10
    },
    "tests": {
      "methods": 358,
      "modules": 27
    }
  },
  "sourceSha256": "4ae8b5141f7364311583ab53125c4b41ad5d3082bc4ed884a5dabdeecbde67a4"
};
