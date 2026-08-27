# Licence Decision Record

## Selected Terms

The repository owner selected the Mozilla Public License 2.0 on August 27,
2026. The live authority is commit
`2eab2dc2306a7ccd9e034b2f1343d1afd559dd22`, whose message is
`Change license to Mozilla Public License 2.0`.

The selected SPDX expression is:

```text
MPL-2.0
```

The public project name is
`Bounded-Authority-Based-Circuit-Simulation`. The compatible Python
distribution, import package, and command remain `bab-cs`, `babcs`, and
`babcs`.

## Canonical Text Correction

The first owner-selected `LICENSE` file was materially different from
Mozilla's published MPL 2.0 text and therefore could not be represented safely
as the SPDX expression `MPL-2.0`. The implementation replaces it with Mozilla's
unmodified canonical text, records `MPL-2.0` in `pyproject.toml`,
`CITATION.cff`, and wheel core metadata, and includes `LICENSE` under the
wheel's `.dist-info/licenses/` directory.

This correction implements the owner's selected licence; it does not choose a
different licence or add custom terms.

## Distribution Consequences

- Source and distribution archives identify `MPL-2.0` using the standard SPDX
  expression.
- The wheel uses Core Metadata 2.4 `License-Expression` and `License-File`
  fields and carries the exact `LICENSE` bytes.
- Contributors must preserve the licence text and applicable notices.
- Commercial use is not separately prohibited; all use and distribution remain
  subject to MPL 2.0.

This record documents repository authority and implementation provenance; it is
not legal advice.

## Remaining Release Gate

Licence selection is complete. Because the canonical-text and packaging changes
alter the source and wheel bytes, `v1.1.0` still requires fresh exact-commit
qualification, evidence review, tagging, tag-triggered qualification, explicit
publication approval, and public-download verification.
