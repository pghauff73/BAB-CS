from __future__ import annotations

DISTRIBUTION_NAME = "bab-cs"
PACKAGE_NAME = "babcs"
VERSION = "1.1.0"
SUMMARY = "Error-bounded multi-method circuit simulation reference implementation"
REQUIRES_PYTHON = ">=3.11"
SPARSE_REQUIREMENT = "scipy>=1.11"
WHEEL_TAG = "py3-none-any"
CONSOLE_SCRIPT = "babcs = babcs.cli:main"


def distribution_stem() -> str:
    return DISTRIBUTION_NAME.replace("-", "_")


def wheel_filename() -> str:
    return f"{distribution_stem()}-{VERSION}-{WHEEL_TAG}.whl"


def dist_info_directory() -> str:
    return f"{distribution_stem()}-{VERSION}.dist-info"
