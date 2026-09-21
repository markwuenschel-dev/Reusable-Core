"""INTEG-005 and INTEG-011.

INTEG-005 analysis_code_version() hashed raw bytes while baseline.py normalises
          line endings, so the published provenance value depended on the
          checkout's line endings and the committed value was unreproducible on
          a CRLF working tree.
INTEG-011 n_valid subtracted a de-duplicated set of failing record ids, so two
          records sharing an id collapsed to one subtraction, and dataset-level
          failures (recorded under '*') were excluded from the subtraction
          entirely.
"""

import unittest

from verification_v1.integrity import validate_dataset_records
from verification_v1.v12_report import analysis_code_version

try:  # pragma: no cover - import shim matching the other v12 test modules
    from v12_helpers import make_record
except ImportError:
    from tests.v12_helpers import make_record


class AnalysisCodeVersionTest(unittest.TestCase):
    def test_line_endings_do_not_change_the_provenance_value(self) -> None:
        import pathlib
        import tempfile

        from verification_v1.v12_report import ANALYSIS_CODE_PATHS, repo_root

        source = repo_root()

        def _materialise(root: pathlib.Path, newline: bytes) -> str:
            for relative in ANALYSIS_CODE_PATHS:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                raw = (source / relative).read_bytes()
                lf = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
                target.write_bytes(lf.replace(b"\n", newline))
            return analysis_code_version(root)

        with tempfile.TemporaryDirectory() as lf_dir, tempfile.TemporaryDirectory() as crlf_dir:
            lf_value = _materialise(pathlib.Path(lf_dir), b"\n")
            crlf_value = _materialise(pathlib.Path(crlf_dir), b"\r\n")
        self.assertEqual(
            lf_value, crlf_value, "provenance must not depend on checkout line endings"
        )


class ValidCountTest(unittest.TestCase):
    @staticmethod
    def _blocking(record):
        """A wrong schema_version is a blocking MISSING_IDENTITY failure."""
        import dataclasses

        return dataclasses.replace(record, schema_version="not-a-real-schema/0")

    def test_duplicate_failing_ids_do_not_collapse(self) -> None:
        """Two distinct failing records sharing an id must both leave n_valid.
        The old subtraction de-duplicated the ids and gave one of them back."""
        import dataclasses

        bad = self._blocking(make_record(name="dup"))
        other = self._blocking(make_record(name="dup2"))
        other = dataclasses.replace(other, record_id=bad.record_id)
        result = validate_dataset_records((bad, other))
        self.assertFalse(result["ok"])
        self.assertEqual(0, result["n_valid"])

    def test_valid_records_are_counted_not_subtracted(self) -> None:
        good = make_record(name="good-a")
        other = make_record(name="good-b")
        bad = self._blocking(make_record(name="bad"))
        result = validate_dataset_records((good, other, bad))
        self.assertEqual(2, result["n_valid"])
        self.assertEqual(3, result["n_records"])

    def test_dataset_level_failures_are_surfaced(self) -> None:
        good = make_record(name="only")
        result = validate_dataset_records((good,))
        self.assertIn("n_dataset_level_failures", result)
        self.assertEqual(0, result["n_dataset_level_failures"])


if __name__ == "__main__":
    unittest.main()
