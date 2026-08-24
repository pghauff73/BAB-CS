from __future__ import annotations

import base64
import csv
import hashlib
import io
import zipfile
from pathlib import Path


def _metadata() -> bytes:
    return (
        "Metadata-Version: 2.1\n"
        "Name: bab-cs\n"
        "Version: 1.0.0\n"
        "Summary: Bounded Adams-Bashforth circuit simulation reference implementation\n"
        "Requires-Python: >=3.11\n"
        "\n"
    ).encode()


def _wheel_name() -> str:
    return "bab_cs-1.0.0-py3-none-any.whl"


def build_wheel(wheel_directory: str, config_settings=None, metadata_directory=None) -> str:
    root = Path(__file__).parent
    target = Path(wheel_directory) / _wheel_name()
    records: list[tuple[str, str, str]] = []

    def add_bytes(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
        archive.writestr(name, data)
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        records.append((name, f"sha256={digest}", str(len(data))))

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((root / "src" / "babcs").glob("*.py")):
            add_bytes(archive, f"babcs/{path.name}", path.read_bytes())
        dist_info = "bab_cs-1.0.0.dist-info"
        add_bytes(archive, f"{dist_info}/METADATA", _metadata())
        add_bytes(
            archive,
            f"{dist_info}/WHEEL",
            b"Wheel-Version: 1.0\nGenerator: bab-cs\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        )
        add_bytes(
            archive,
            f"{dist_info}/entry_points.txt",
            b"[console_scripts]\nbabcs = babcs.cli:main\n",
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerows(records)
        writer.writerow((f"{dist_info}/RECORD", "", ""))
        archive.writestr(f"{dist_info}/RECORD", buffer.getvalue().encode())
    return target.name


def prepare_metadata_for_build_wheel(metadata_directory: str, config_settings=None) -> str:
    dist_info = Path(metadata_directory) / "bab_cs-1.0.0.dist-info"
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_bytes(_metadata())
    return dist_info.name


def build_sdist(sdist_directory: str, config_settings=None) -> str:
    raise RuntimeError("sdist generation is not supported")
