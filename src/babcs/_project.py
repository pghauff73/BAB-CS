from __future__ import annotations

PROJECT_NAME = "Bounded-Authority-Based-Circuit-Simulation"
DISTRIBUTION_NAME = "bab-cs"
PACKAGE_NAME = "babcs"
VERSION = "1.1.0"
SUMMARY = "Bounded-authority-based circuit simulation reference implementation"
REQUIRES_PYTHON = ">=3.11"
SPARSE_REQUIREMENT = "scipy>=1.11"
LICENSE_EXPRESSION = "MPL-2.0"
LICENSE_FILE = "LICENSE"
WHEEL_TAG = "py3-none-any"
CONSOLE_SCRIPT = "babcs = babcs.cli:main"


def distribution_stem() -> str:
    return DISTRIBUTION_NAME.replace("-", "_")


def wheel_filename() -> str:
    return f"{distribution_stem()}-{VERSION}-{WHEEL_TAG}.whl"


def dist_info_directory() -> str:
    return f"{distribution_stem()}-{VERSION}.dist-info"
