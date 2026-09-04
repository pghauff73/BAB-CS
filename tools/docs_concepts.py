from __future__ import annotations

import re
from typing import Any


CONCEPT_GLOSSARY: tuple[dict[str, Any], ...] = (
    {
        "id": "ourd",
        "term": "OURD Coding Agent",
        "aliases": ["OURD", "OURD Coding Agent"],
        "definition": "The governed local advisory coding agent used to review evidence and propose changes without receiving final approval authority.",
    },
    {
        "id": "babcs",
        "term": "BAB-CS",
        "aliases": ["BAB-CS", "BAB-CSv1", "Bounded-Authority-Based-Circuit-Simulation"],
        "definition": "A circuit-simulation architecture where numerical methods may propose states, but independent checks control which state is accepted.",
    },
    {
        "id": "candidate-method",
        "term": "Candidate method",
        "aliases": ["candidate method", "candidate methods", "candidate integrator", "candidate integrators"],
        "definition": "The numerical formula that proposes the next capacitor voltages and inductor currents without approving its own result.",
    },
    {
        "id": "numerical-authority",
        "term": "Numerical authority",
        "aliases": ["numerical authority", "reference authority", "accepted-state authority"],
        "definition": "The independent calculations and rules that decide whether a proposed timestep is accepted, corrected, recomputed, or rejected.",
    },
    {
        "id": "projection",
        "term": "Projection",
        "aliases": ["projection", "projections"],
        "definition": "A circuit-equation solve that restores node-voltage and branch-current consistency for a proposed dynamic state.",
    },
    {
        "id": "replay",
        "term": "Replay",
        "aliases": ["replay", "replays"],
        "definition": "An independent recomputation of a recent interval from a trusted state, usually with a different implicit method and smaller internal steps.",
    },
    {
        "id": "anchor",
        "term": "Anchor",
        "aliases": ["anchor", "anchors"],
        "definition": "A retained accepted state used as the starting point for an independent replay check.",
    },
    {
        "id": "recursive-bound",
        "term": "Recursive internal bound",
        "aliases": ["recursive internal bound", "recursive internal bounds", "recursive bound", "recursive bounds"],
        "definition": "A running estimate of how previously modeled numerical error and the newest local defect may combine.",
    },
    {
        "id": "residual",
        "term": "Residual",
        "aliases": ["residual", "residuals"],
        "definition": "The mismatch left when the circuit equations are evaluated at a computed solution.",
    },
    {
        "id": "jacobian",
        "term": "Jacobian",
        "aliases": ["Jacobian", "Jacobians"],
        "definition": "A matrix of local sensitivities showing how each equation changes when each unknown changes.",
    },
    {
        "id": "newton-iteration",
        "term": "Newton iteration",
        "aliases": ["Newton iteration", "Newton iterations", "Newton solve", "Newton solves", "Newton method", "Newton methods"],
        "definition": "A repeated linearization process used to solve nonlinear equations such as diode circuit equations.",
    },
    {
        "id": "nonlinear-convergence",
        "term": "Nonlinear convergence",
        "aliases": ["nonlinear convergence", "converged nonlinear"],
        "definition": "The condition reached when an iterative nonlinear solve satisfies its declared equation-mismatch and update tolerances.",
    },
    {
        "id": "stiffness",
        "term": "Stiffness",
        "aliases": ["stiffness", "stiff"],
        "definition": "The presence of fast and slow behavior together, which can force some numerical methods to use very small timesteps for stability.",
    },
    {
        "id": "passivity",
        "term": "Passivity",
        "aliases": ["passivity", "passive"],
        "definition": "The physical rule that a passive declared model may not create net energy from nothing.",
    },
    {
        "id": "reduced-order-model",
        "term": "Reduced-order model",
        "aliases": ["reduced-order model", "reduced-order models", "reduced-order numerical experiment", "reduced-order numerical experiments", "reduced-order"],
        "definition": "A deliberately simplified model that retains only the behavior needed for the stated engineering question.",
    },
    {
        "id": "deterministic-evidence",
        "term": "Deterministic evidence",
        "aliases": ["deterministic evidence", "deterministic report", "deterministic output", "deterministic"],
        "definition": "Evidence designed to repeat for the same declared source, configuration, and environment rather than depending on incidental execution order.",
    },
    {
        "id": "fixed-step",
        "term": "Fixed-step comparison",
        "aliases": ["fixed-step", "fixed timestep", "fixed-timestep"],
        "definition": "A comparison in which methods use the same declared nominal advance in simulated time.",
    },
    {
        "id": "fixed-accuracy",
        "term": "Fixed-accuracy comparison",
        "aliases": ["fixed-accuracy"],
        "definition": "A comparison that selects results against the same declared error target.",
    },
    {
        "id": "fixed-work",
        "term": "Fixed-work comparison",
        "aliases": ["fixed-work"],
        "definition": "A comparison under the same deterministic operation budget rather than the same wall-clock time.",
    },
    {
        "id": "phase-error",
        "term": "Phase error",
        "aliases": ["phase error", "phase errors", "phase drift", "phase"],
        "definition": "The timing shift of an oscillation relative to the chosen authority or expected waveform.",
    },
    {
        "id": "energy-drift",
        "term": "Energy drift",
        "aliases": ["energy drift", "energy error", "energy errors"],
        "definition": "Numerical gain or loss of stored capacitor and inductor energy that is not caused by the declared model.",
    },
    {
        "id": "empirical-coverage",
        "term": "Empirical coverage",
        "aliases": ["empirical coverage", "coverage ratio"],
        "definition": "The measured fraction of eligible samples for which an internal bound covered independently observed authority error.",
    },
    {
        "id": "shadow-mode",
        "term": "Shadow mode",
        "aliases": ["shadow mode", "shadow authority"],
        "definition": "An observe-only mode where a candidate runs and records evidence while a trusted reference still owns the accepted state.",
    },
    {
        "id": "fail-closed",
        "term": "Fail closed",
        "aliases": ["fail closed", "fail-closed"],
        "definition": "Refuse to produce an accepted result when required evidence, convergence, or support is missing.",
    },
    {
        "id": "factorization",
        "term": "Matrix factorization",
        "aliases": ["factorization", "factorisation", "refactor"],
        "definition": "Rewriting a matrix into parts that make one or more equation solves more efficient.",
    },
    {
        "id": "source-wheel-equivalence",
        "term": "Source-versus-wheel equivalence",
        "aliases": ["source-versus-wheel equivalence", "source and installed", "source-versus-installed"],
        "definition": "A check that the source checkout and an isolated installation of the built Python package produce the same declared evidence.",
    },
    {
        "id": "python-wheel",
        "term": "Python wheel",
        "aliases": ["Python wheel", "Python wheels", "wheel", "wheels"],
        "definition": "An installable Python package file containing code and package metadata.",
    },
    {
        "id": "rss",
        "term": "RSS",
        "aliases": ["RSS", "resident set size"],
        "definition": "Resident set size: the physical memory occupied by a process at a measured time; maximum RSS records its observed peak.",
    },
    {
        "id": "gnu-time",
        "term": "GNU Time",
        "aliases": ["GNU", "GNU Time"],
        "definition": "The GNU Project's command-line utility for measuring process runtime and resource use, including maximum resident memory.",
    },
    {
        "id": "mna",
        "term": "MNA",
        "aliases": ["MNA", "modified nodal analysis"],
        "definition": "Modified nodal analysis: a standard way to turn a circuit into equations for node voltages and selected branch currents.",
    },
    {
        "id": "dae",
        "term": "DAE",
        "aliases": ["DAE", "DAEs", "differential-algebraic equation", "differential-algebraic equations"],
        "definition": "Differential-algebraic equation: a model combining time-evolution equations with constraints that must hold immediately.",
    },
    {
        "id": "ode",
        "term": "ODE",
        "aliases": ["ODE", "ODEs", "ordinary differential equation", "ordinary differential equations"],
        "definition": "Ordinary differential equation: an equation describing how a state changes with time without a separate algebraic constraint system.",
    },
    {
        "id": "spice",
        "term": "SPICE",
        "aliases": ["SPICE", "SPICE2"],
        "definition": "Simulation Program with Integrated Circuit Emphasis: a widely used family of circuit-simulation methods and tools.",
    },
    {
        "id": "rc",
        "term": "RC",
        "aliases": ["RC"],
        "definition": "Resistor-capacitor: a circuit containing resistance and electrical energy storage in a capacitor.",
    },
    {
        "id": "rl",
        "term": "RL",
        "aliases": ["RL", "R-L"],
        "definition": "Resistor-inductor: a circuit containing resistance and magnetic energy storage in an inductor.",
    },
    {
        "id": "rlc",
        "term": "RLC",
        "aliases": ["RLC"],
        "definition": "Resistor-inductor-capacitor: a circuit containing resistance and both magnetic and electrical energy storage.",
    },
    {
        "id": "lc",
        "term": "LC",
        "aliases": ["LC", "C+L"],
        "definition": "Inductor-capacitor: a circuit in which energy moves between magnetic and electrical storage.",
    },
    {
        "id": "dc",
        "term": "DC",
        "aliases": ["DC", "direct current"],
        "definition": "Direct current: electrical voltage or current whose intended direction does not alternate periodically.",
    },
    {
        "id": "pwl",
        "term": "PWL",
        "aliases": ["PWL", "piecewise linear"],
        "definition": "Piecewise linear: a waveform made from straight-line segments joined at declared breakpoints.",
    },
    {
        "id": "kcl",
        "term": "KCL",
        "aliases": ["KCL", "Kirchhoff current law", "Kirchhoff's current law"],
        "definition": "Kirchhoff current law: current entering and leaving a circuit node must balance.",
    },
    {
        "id": "ab2",
        "term": "AB2",
        "aliases": ["AB2", "Adams-Bashforth order two", "Adams–Bashforth order two"],
        "definition": "Adams-Bashforth order two: an explicit two-step method that predicts a new state from current and previous derivative information.",
    },
    {
        "id": "adams-bashforth",
        "term": "AB",
        "aliases": ["AB", "Adams-Bashforth", "Adams–Bashforth"],
        "definition": "Adams-Bashforth: a family of explicit multistep methods that predict a new state from stored derivative history.",
    },
    {
        "id": "ab3",
        "term": "AB3",
        "aliases": ["AB3"],
        "definition": "Adams-Bashforth order three: an explicit three-step proposal method using three derivative-history points.",
    },
    {
        "id": "be",
        "term": "BE",
        "aliases": ["BE", "backward Euler"],
        "definition": "Backward Euler: a first-order implicit method that solves an equation containing the new state.",
    },
    {
        "id": "bdf2",
        "term": "BDF2",
        "aliases": ["BDF2", "backward differentiation formula order two"],
        "definition": "Backward differentiation formula order two: a second-order implicit method that uses the current and previous accepted states.",
    },
    {
        "id": "rk23",
        "term": "RK23",
        "aliases": ["RK23", "Bogacki-Shampine", "Bogacki–Shampine"],
        "definition": "A Runge-Kutta method with related second- and third-order results that can estimate local error.",
    },
    {
        "id": "csc",
        "term": "CSC",
        "aliases": ["CSC", "compressed sparse column"],
        "definition": "Compressed sparse column: a matrix format that stores nonzero values by column instead of storing every zero.",
    },
    {
        "id": "klu",
        "term": "KLU",
        "aliases": ["KLU", "SuiteSparse KLU"],
        "definition": "A sparse linear solver designed for circuit-like matrices with repeated structure.",
    },
    {
        "id": "superlu",
        "term": "SuperLU",
        "aliases": ["SuperLU"],
        "definition": "A software library for factoring and solving sparse linear equation systems.",
    },
    {
        "id": "scipy",
        "term": "SciPy",
        "aliases": ["SciPy"],
        "definition": "A Python scientific-computing library that provides numerical algorithms and sparse matrix tools.",
    },
    {
        "id": "colamd",
        "term": "COLAMD",
        "aliases": ["COLAMD"],
        "definition": "Column approximate minimum degree: a matrix-ordering strategy intended to reduce extra nonzero work during sparse factorization.",
    },
    {
        "id": "lru",
        "term": "LRU",
        "aliases": ["LRU", "least-recently-used"],
        "definition": "Least recently used: a bounded cache policy that evicts the entry unused for the longest time.",
    },
    {
        "id": "rms",
        "term": "RMS",
        "aliases": ["RMS", "root-mean-square"],
        "definition": "Root mean square: a way to combine several values by averaging their squares and then taking a square root.",
    },
    {
        "id": "wrms",
        "term": "WRMS",
        "aliases": ["WRMS", "weighted RMS", "weighted root-mean-square"],
        "definition": "Weighted root mean square: an RMS measure after each component is scaled by its allowed tolerance.",
    },
    {
        "id": "ulp",
        "term": "ULP",
        "aliases": ["ULP", "unit in the last place"],
        "definition": "Unit in the last place: the gap between adjacent floating-point numbers near a value.",
    },
    {
        "id": "json",
        "term": "JSON",
        "aliases": ["JSON", "JavaScript Object Notation"],
        "definition": "JavaScript Object Notation: a text format for structured data made from objects, arrays, numbers, strings, and booleans.",
    },
    {
        "id": "csv",
        "term": "CSV",
        "aliases": ["CSV", "comma-separated values", "comma-separated-value"],
        "definition": "Comma-separated values: a plain-text table format where each row is a line and columns are separated by commas.",
    },
    {
        "id": "svg",
        "term": "SVG",
        "aliases": ["SVG", "Scalable Vector Graphics"],
        "definition": "Scalable Vector Graphics: a text-based vector image format that stays sharp when resized.",
    },
    {
        "id": "sha256",
        "term": "SHA-256",
        "aliases": ["SHA-256", "SHA256", "SHA"],
        "definition": "Secure Hash Algorithm: a cryptographic fingerprint family; BAB-CS evidence uses the 256-bit SHA-256 form to identify exact digital content.",
    },
    {
        "id": "ci",
        "term": "CI",
        "aliases": ["CI", "continuous integration"],
        "definition": "Continuous integration: automated building and testing triggered by repository events.",
    },
    {
        "id": "cli",
        "term": "CLI",
        "aliases": ["CLI", "command-line interface"],
        "definition": "Command-line interface: a text-based way to run a program by typing commands and options.",
    },
    {
        "id": "api",
        "term": "API",
        "aliases": ["API", "APIs", "application programming interface", "application programming interfaces"],
        "definition": "Application programming interface: a defined way for software components to call and exchange data with one another.",
    },
    {
        "id": "url",
        "term": "URL",
        "aliases": ["URL", "URLs"],
        "definition": "Uniform Resource Locator: the address of a resource such as a web page or downloadable artifact.",
    },
    {
        "id": "utc",
        "term": "UTC",
        "aliases": ["UTC"],
        "definition": "Coordinated Universal Time: the global time standard commonly used for unambiguous timestamps.",
    },
    {
        "id": "yaml",
        "term": "YAML",
        "aliases": ["YAML"],
        "definition": "A human-readable structured-data format commonly used for configuration files and automation workflows.",
    },
    {
        "id": "html",
        "term": "HTML",
        "aliases": ["HTML", "HyperText Markup Language"],
        "definition": "HyperText Markup Language: the standard markup used to structure web pages.",
    },
    {
        "id": "zip",
        "term": "ZIP",
        "aliases": ["ZIP"],
        "definition": "A compressed archive format that packages multiple files into one container.",
    },
    {
        "id": "pythonpath",
        "term": "PYTHONPATH",
        "aliases": ["PYTHONPATH"],
        "definition": "An environment variable that tells Python which additional directories to search when importing modules.",
    },
    {
        "id": "long-test-flags",
        "term": "BABCS_LONG_TESTS and BABCS_VERY_LONG_TESTS",
        "aliases": ["BABCS_LONG_TESTS", "BABCS_VERY_LONG_TESTS"],
        "definition": "Environment-variable switches that enable longer BAB-CS qualification tiers which are intentionally omitted from the default fast suite.",
    },
    {
        "id": "doi",
        "term": "DOI",
        "aliases": ["DOI"],
        "definition": "Digital Object Identifier: a persistent identifier used to locate a published research work.",
    },
    {
        "id": "spdx",
        "term": "SPDX",
        "aliases": ["SPDX"],
        "definition": "Software Package Data Exchange: a standard vocabulary for identifying software licenses and supply-chain information.",
    },
    {
        "id": "mpl2",
        "term": "MPL-2.0",
        "aliases": ["MPL-2.0", "MPL 2.0", "MPL", "Mozilla Public License 2.0"],
        "definition": "Mozilla Public License 2.0: a file-level open-source license used by this project.",
    },
    {
        "id": "hil",
        "term": "HIL",
        "aliases": ["HIL", "hardware-in-the-loop"],
        "definition": "Hardware-in-the-loop: testing real controller hardware against a simulated plant.",
    },
    {
        "id": "itp",
        "term": "ITP",
        "aliases": ["ITP"],
        "definition": "Interpolate, Truncate, and Project: a bracketed root-finding method that combines interpolation speed with guaranteed interval reduction.",
    },
    {
        "id": "os",
        "term": "OS",
        "aliases": ["OS", "operating system"],
        "definition": "Operating system: the base software that manages the computer, files, processes, and hardware used for a qualification run.",
    },
    {
        "id": "git-head",
        "term": "Git HEAD",
        "aliases": ["Git HEAD", "HEAD"],
        "definition": "Git HEAD: the Git reference identifying the currently checked-out commit.",
    },
    {
        "id": "http-methods",
        "term": "POST and PUT",
        "aliases": ["POST", "PUT"],
        "definition": "HTTP request methods: POST commonly creates or triggers work, while PUT commonly replaces or updates a named resource.",
    },
    {
        "id": "wheel-metadata-files",
        "term": "WHEEL and METADATA",
        "aliases": ["WHEEL", "METADATA"],
        "definition": "Standard files inside a Python wheel that describe the wheel format, package identity, dependencies, and other installation metadata.",
    },
    {
        "id": "natural-ordering",
        "term": "NATURAL ordering",
        "aliases": ["NATURAL", "natural ordering"],
        "definition": "A sparse-solver ordering that keeps the matrix columns in their original declared order instead of applying a fill-reducing permutation.",
    },
    {
        "id": "identifier",
        "term": "ID",
        "aliases": ["ID", "identifier"],
        "definition": "Identifier: a name or number used to distinguish one requirement, case, run, record, or artifact from another.",
    },
    {
        "id": "ieee",
        "term": "IEEE",
        "aliases": ["IEEE"],
        "definition": "Institute of Electrical and Electronics Engineers: a professional organization and publisher of engineering standards and research.",
    },
    {
        "id": "acm",
        "term": "ACM",
        "aliases": ["ACM"],
        "definition": "Association for Computing Machinery: a professional computing organization and research publisher.",
    },
    {
        "id": "siam",
        "term": "SIAM",
        "aliases": ["SIAM"],
        "definition": "Society for Industrial and Applied Mathematics: a professional organization and publisher focused on applied mathematics.",
    },
    {
        "id": "ucb",
        "term": "UCB",
        "aliases": ["UCB"],
        "definition": "University of California, Berkeley: the institution identified by the UCB report prefix in historical circuit-simulation references.",
    },
    {
        "id": "amd",
        "term": "AMD",
        "aliases": ["AMD"],
        "definition": "Advanced Micro Devices: the processor manufacturer named in the local performance-test environment.",
    },
    {
        "id": "bit-journal",
        "term": "BIT Numerical Mathematics",
        "aliases": ["BIT", "BIT Numerical Mathematics"],
        "definition": "A peer-reviewed journal that publishes research in numerical analysis and scientific computing.",
    },
    {
        "id": "ngspice",
        "term": "ngspice",
        "aliases": ["ngspice"],
        "definition": "An open-source SPICE-family circuit simulator used here for mapped cross-implementation comparison evidence.",
    },
    {
        "id": "ltspice",
        "term": "LTspice",
        "aliases": ["LTspice"],
        "definition": "A circuit-simulation and schematic-capture environment commonly used with Analog Devices models and example circuits.",
    },
    {
        "id": "plecs",
        "term": "PLECS",
        "aliases": ["PLECS"],
        "definition": "A power-electronics system simulation environment covering converters, controls, switching, thermal behavior, and deployment workflows.",
    },
    {
        "id": "simscape-electrical",
        "term": "Simscape Electrical",
        "aliases": ["Simscape Electrical"],
        "definition": "A MathWorks environment for electrical systems that can interact with mechanical, thermal, control, motor, and grid models.",
    },
    {
        "id": "xyce",
        "term": "Xyce",
        "aliases": ["Xyce"],
        "definition": "A SPICE-compatible high-performance circuit simulator designed for very large serial and parallel problems.",
    },
)


def _alias_pattern(alias: str) -> re.Pattern[str]:
    case_sensitive = bool(
        re.fullmatch(r"[A-Z][A-Z0-9+_.-]*(?: [A-Z0-9+_.-]+)*", alias)
    )
    return re.compile(
        rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])",
        0 if case_sensitive else re.IGNORECASE,
    )


def _markdown_prose(markdown: str) -> str:
    prose = re.sub(r"```.*?```", " ", markdown, flags=re.DOTALL)
    prose = re.sub(r"`[^`]*`", " ", prose)
    prose = re.sub(r"^#\s+.*$", " ", prose, count=1, flags=re.MULTILINE)
    prose = re.sub(r"\[\[[^]]+]]\([^)]+\)", " ", prose)
    prose = re.sub(r"\[([^]]*)]\([^)]+\)", r"\1", prose)
    return prose


def concept_ids_for_markdown(markdown: str) -> list[str]:
    prose = _markdown_prose(markdown)
    matches: list[str] = []
    for concept in CONCEPT_GLOSSARY:
        if any(_alias_pattern(str(alias)).search(prose) for alias in concept["aliases"]):
            matches.append(str(concept["id"]))
    return matches


_ACRONYM_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])[A-Z][A-Z0-9+_.-]{1,}(?![A-Za-z0-9_])"
)
_NON_CONCEPT_ACRONYMS = {
    "ERL",
    "M520",
    "README",
    "REFERENCES",
}
_NON_CONCEPT_PATTERNS = (
    re.compile(r"(?:BAB|RQ|TC|IP)-\d+"),
    re.compile(r"BF\d+"),
    re.compile(r"CSD-\d+-\d+"),
    re.compile(r"TCS\.\d+\.\d+"),
    re.compile(r"[A-Z]\.-[A-Z]"),
)


def unexplained_prose_acronyms(markdown: str) -> list[str]:
    prose = _markdown_prose(markdown)
    aliases = sorted(
        (
            str(alias)
            for concept in CONCEPT_GLOSSARY
            for alias in concept["aliases"]
        ),
        key=len,
        reverse=True,
    )
    for alias in aliases:
        prose = _alias_pattern(alias).sub(" ", prose)
    known = {
        str(alias).upper()
        for concept in CONCEPT_GLOSSARY
        for alias in concept["aliases"]
        if _ACRONYM_PATTERN.fullmatch(str(alias))
    }
    unexplained: set[str] = set()
    for match in _ACRONYM_PATTERN.finditer(prose):
        token = match.group().rstrip(".")
        if len(token) < 2 or token in known or token in _NON_CONCEPT_ACRONYMS:
            continue
        if "_" in token or any(pattern.fullmatch(token) for pattern in _NON_CONCEPT_PATTERNS):
            continue
        unexplained.add(token)
    return sorted(unexplained)
