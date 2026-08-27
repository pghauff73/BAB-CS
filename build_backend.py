from __future__ import annotations

import base64
import csv
import hashlib
import importlib.util
import io
import zipfile
from functools import lru_cache
from pathlib import Path
from types import ModuleType


@lru_cache(maxsize=1)
def _project() -> ModuleType:
    path = Path(__file__).parent / "src" / "babcs" / "_project.py"
    specification = importlib.util.spec_from_file_location("_babcs_project", path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load project metadata from {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _metadata() -> bytes:
    project = _project()
    return (
        "Metadata-Version: 2.4\n"
        f"Name: {project.DISTRIBUTION_NAME}\n"
        f"Version: {project.VERSION}\n"
        f"Summary: {project.SUMMARY}\n"
        f"Requires-Python: {project.REQUIRES_PYTHON}\n"
        f"License-Expression: {project.LICENSE_EXPRESSION}\n"
        f"License-File: {project.LICENSE_FILE}\n"
        "Provides-Extra: sparse\n"
        f'Requires-Dist: {project.SPARSE_REQUIREMENT}; extra == "sparse"\n'
        "\n"
    ).encode()


def _wheel_name() -> str:
    return _project().wheel_filename()


def build_wheel(wheel_directory: str, config_settings=None, metadata_directory=None) -> str:
    root = Path(__file__).parent
    project = _project()
    target = Path(wheel_directory) / _wheel_name()
    records: list[tuple[str, str, str]] = []

    def write_bytes(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
        info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 3
        info.external_attr = 0o100644 << 16
        archive.writestr(info, data)

    def add_bytes(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
        write_bytes(archive, name, data)
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        records.append((name, f"sha256={digest}", str(len(data))))

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((root / "src" / "babcs").glob("*.py")):
            add_bytes(archive, f"babcs/{path.name}", path.read_bytes())
        dist_info = project.dist_info_directory()
        add_bytes(archive, f"{dist_info}/METADATA", _metadata())
        add_bytes(
            archive,
            f"{dist_info}/WHEEL",
            (
                "Wheel-Version: 1.0\n"
                f"Generator: {project.DISTRIBUTION_NAME}\n"
                "Root-Is-Purelib: true\n"
                f"Tag: {project.WHEEL_TAG}\n"
            ).encode(),
        )
        add_bytes(
            archive,
            f"{dist_info}/entry_points.txt",
            f"[console_scripts]\n{project.CONSOLE_SCRIPT}\n".encode(),
        )
        add_bytes(
            archive,
            f"{dist_info}/licenses/{project.LICENSE_FILE}",
            (root / project.LICENSE_FILE).read_bytes(),
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerows(records)
        writer.writerow((f"{dist_info}/RECORD", "", ""))
        write_bytes(archive, f"{dist_info}/RECORD", buffer.getvalue().encode())
    return target.name


def prepare_metadata_for_build_wheel(metadata_directory: str, config_settings=None) -> str:
    dist_info = Path(metadata_directory) / _project().dist_info_directory()
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_bytes(_metadata())
    return dist_info.name


def build_sdist(sdist_directory: str, config_settings=None) -> str:
    raise RuntimeError("sdist generation is not supported")
