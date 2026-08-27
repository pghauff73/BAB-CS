# Security Policy

## Supported Versions

Bounded-Authority-Based-Circuit-Simulation is research software. Security fixes
are applied to the current public release and the active development line when a
fix can be made without weakening numerical validation or release provenance.

| Version | Status |
| --- | --- |
| `1.1.x` | Active development; not yet release-approved |
| `1.0.x` | Current public release |
| `< 1.0` | Not supported |

## Reporting a Vulnerability

Do not open a public issue containing exploit details, private data, credentials,
or a proof of concept that could harm users.

Use GitHub's private vulnerability-reporting form:

`https://github.com/pghauff73/Bounded-Authority-Based-Circuit-Simulation/security/advisories/new`

Include:

- the affected release tag, wheel hash, or full source commit;
- the affected command, input, backend, and platform;
- reproduction steps and expected impact;
- whether the issue affects integrity, availability, code execution, artifact
  provenance, or numerical-result trust;
- any proposed mitigation or embargo constraints.

The maintainer will acknowledge a complete report when practical, validate the
issue against an exact source identity, and coordinate disclosure after a fix or
documented mitigation exists. Security reports do not bypass the normal
exact-hash release approval process.

## Numerical Integrity Reports

A numerical discrepancy without a security impact belongs in the structured
Numerical Evidence issue form. Reports involving crafted inputs that can cause
code execution, dependency compromise, artifact substitution, or silent
integrity loss belong in private vulnerability reporting.
