# Tutorial 5: Deterministic Packaging

Deterministic packaging means that two builds from the same declared source
state produce exactly the same installable package bytes. The Python package
format used here is a wheel: a ZIP-based archive containing modules and package
metadata.

![Deterministic packaging flow](html/assets/tutorial-05-deterministic-packaging.svg "Two independent wheel builds from one frozen source are compared byte-for-byte.")

## What You Will Learn

Reproducible numerical evidence can be weakened if the distributed package is
not reproducible. A package might accidentally include a stale file, omit a
module, reorder archive members, preserve local timestamps, or change file
permissions.

The exercise checks:

- fixed archive timestamps;
- fixed file permissions;
- deterministic member order;
- the declared wheel filename; and
- byte-identical Secure Hash Algorithm 256-bit (`SHA-256`) fingerprints.

SHA-256 is a cryptographic fingerprint. If two package files have the same
SHA-256 value, they are treated as the same exact byte sequence for this
evidence workflow.

## Run the Exercise

From a clean source tree:

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 05-deterministic-packaging
```

For an explicitly non-release experiment in a dirty tree:

```bash
PYTHONPATH=src python lab/support/verify.py \
  --exercise 05-deterministic-packaging \
  --development
```

Development mode records that the result is not release evidence.

## Expected Results

If timestamps, permissions, member ordering, package metadata, and included
files are deterministic, two independent builds from the same source should
have identical bytes and therefore identical SHA-256 fingerprints. Because the
working tree is dirty and development mode is explicit, the expected release
evidence flag is `false` even if the wheel bytes match.

## Observed Data

The development-mode command was run on August 27, 2026 because the repository
contained uncommitted work.

| Measurement | Observed value |
| --- | --- |
| Wheel filename | `bab_cs-1.1.0-py3-none-any.whl` |
| Archive members | `19` |
| Fixed timestamps | `true` |
| Fixed permissions | `true` |
| Member order matches the build-backend contract | `true` |
| First wheel SHA-256 | `ca5d648e60dfd9923deadc85fb304b45dc9ecf87aecc982a369d3766542806f2` |
| Second wheel SHA-256 | `ca5d648e60dfd9923deadc85fb304b45dc9ecf87aecc982a369d3766542806f2` |
| Wheel hashes match | `true` |
| Release evidence | `false` |

The two complete 64-character fingerprints are identical, so the two measured
wheel files were byte-for-byte identical. The `release evidence` field remains
false because development mode permits a dirty source tree. Deterministic bytes
do not override the clean-source and human-approval release gates.

## Expected Versus Actual Results

The two wheel fingerprints matched exactly, and every archive-control check
returned `true`. The result therefore met the deterministic-build expectation.
The release flag also matched the expected `false` value.

A common but incorrect expectation is that reproducible bytes automatically
make a package releasable. The actual result demonstrates why that is false:
byte identity answers a packaging question, while release qualification also
requires a clean exact source commit, complete evidence, and human approval.

## Understand the Build Contract

The verifier builds the wheel twice into different directories. It compares the
complete byte sequences and then inspects the archives. Sorting members alone
is not enough: timestamps, permissions, generated metadata, and version fields
must also be controlled.

The reviewed build backend defines the authoritative member order. A test that
merely compares extracted source text would miss archive-level differences.

## Theory and Practical Outcomes

The theoretical outcome follows from hashing: identical byte sequences produce
the same SHA-256 fingerprint. The practical outcome depends on controlling
every source of archive variation rather than only the Python module text.

Deterministic packaging supports regulated review, long-lived research
artifacts, exact rollback, and independent reproduction. A reviewer can tie a
published wheel fingerprint to the exact source and evidence that were
approved.

## Conclusion

The development wheel is reproducible under the measured build environment.
This supports repeatable installation and rollback, but the result deliberately
remains development evidence rather than release evidence.

## Claim Boundary

Matching wheel hashes prove byte identity for the two measured builds. They do
not prove numerical correctness, security, release approval, or reproducibility
on every operating system and Python version.
