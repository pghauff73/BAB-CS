from __future__ import annotations

import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

import build_backend


class BuildBackendTests(unittest.TestCase):
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
                metadata = archive.read("bab_cs-1.0.0.dist-info/METADATA").decode()
                self.assertIn("Provides-Extra: sparse", metadata)
                self.assertIn('Requires-Dist: scipy>=1.11; extra == "sparse"', metadata)


if __name__ == "__main__":
    unittest.main()
