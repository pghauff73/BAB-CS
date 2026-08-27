from __future__ import annotations

import hashlib
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path

import build_backend
from babcs import __version__
from babcs import _project


class BuildBackendTests(unittest.TestCase):
    def test_project_metadata_has_one_consistent_version(self) -> None:
        project_data = tomllib.loads(Path("pyproject.toml").read_text())
        project = project_data["project"]
        self.assertEqual(project["name"], _project.DISTRIBUTION_NAME)
        self.assertEqual(project["version"], _project.VERSION)
        self.assertEqual(project["description"], _project.SUMMARY)
        self.assertEqual(project["requires-python"], _project.REQUIRES_PYTHON)
        self.assertEqual(project["license"], _project.LICENSE_EXPRESSION)
        self.assertEqual(project["license-files"], [_project.LICENSE_FILE])
        self.assertEqual(
            project["optional-dependencies"]["sparse"],
            [_project.SPARSE_REQUIREMENT],
        )
        self.assertEqual(
            project["scripts"]["babcs"],
            _project.CONSOLE_SCRIPT.split(" = ", 1)[1],
        )
        self.assertEqual(__version__, _project.VERSION)

    def test_wheel_build_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first_directory, tempfile.TemporaryDirectory() as second_directory:
            first_path = Path(first_directory) / build_backend.build_wheel(first_directory)
            second_path = Path(second_directory) / build_backend.build_wheel(second_directory)

            first_bytes = first_path.read_bytes()
            second_bytes = second_path.read_bytes()
            self.assertEqual(hashlib.sha256(first_bytes).digest(), hashlib.sha256(second_bytes).digest())

            with zipfile.ZipFile(first_path) as archive:
                self.assertTrue(archive.infolist())
                self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist()))
                self.assertTrue(all(info.external_attr >> 16 == 0o100644 for info in archive.infolist()))
                dist_info = _project.dist_info_directory()
                metadata = archive.read(f"{dist_info}/METADATA").decode()
                wheel = archive.read(f"{dist_info}/WHEEL").decode()
                entry_points = archive.read(f"{dist_info}/entry_points.txt").decode()
                self.assertEqual(first_path.name, _project.wheel_filename())
                self.assertIn(f"Name: {_project.DISTRIBUTION_NAME}\n", metadata)
                self.assertIn(f"Version: {_project.VERSION}\n", metadata)
                self.assertIn(f"Summary: {_project.SUMMARY}\n", metadata)
                self.assertIn(f"Requires-Python: {_project.REQUIRES_PYTHON}\n", metadata)
                self.assertIn("Metadata-Version: 2.4\n", metadata)
                self.assertIn(
                    f"License-Expression: {_project.LICENSE_EXPRESSION}\n",
                    metadata,
                )
                self.assertIn(f"License-File: {_project.LICENSE_FILE}\n", metadata)
                self.assertIn("Provides-Extra: sparse", metadata)
                self.assertIn(
                    f'Requires-Dist: {_project.SPARSE_REQUIREMENT}; extra == "sparse"',
                    metadata,
                )
                self.assertIn(f"Tag: {_project.WHEEL_TAG}\n", wheel)
                self.assertEqual(
                    entry_points,
                    f"[console_scripts]\n{_project.CONSOLE_SCRIPT}\n",
                )
                self.assertEqual(
                    archive.read(
                        f"{dist_info}/licenses/{_project.LICENSE_FILE}"
                    ),
                    Path(_project.LICENSE_FILE).read_bytes(),
                )


if __name__ == "__main__":
    unittest.main()
