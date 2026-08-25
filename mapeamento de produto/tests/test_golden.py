from __future__ import annotations

import json
from pathlib import Path
import unittest

from mapping.pipeline import compare_golden, run_products


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
GOLDEN_DIR = ROOT / "tests" / "golden"
INPUT = DATA_DIR / "normalized" / "consolidacao.parquet"


class GoldenMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not INPUT.exists():
            raise RuntimeError("Run bootstrap before the golden tests")

    def test_a12038(self) -> None:
        expected = json.loads((GOLDEN_DIR / "a12038.json").read_text(encoding="utf-8"))
        run = run_products(INPUT, DATA_DIR, GOLDEN_DIR, ["A12038"], publish_static=False)
        actual = run["results"]["A12038"]
        self.assertEqual(compare_golden(actual, expected), [])
        self.assertEqual(actual["summary"]["quantity_total"], 62630)
        self.assertEqual(actual["contract"]["market_top1"], "Refrigeração comercial e cadeia do frio")
        self.assertEqual(actual["contract"]["application_top1_quantity"], 30436)
        self.assertEqual(actual["contract"]["equipment_top1_quantity"], 30436)

    def test_vent_fs4_400_et(self) -> None:
        expected = json.loads((GOLDEN_DIR / "vent_fs4_400_et.json").read_text(encoding="utf-8"))
        run = run_products(INPUT, DATA_DIR, GOLDEN_DIR, ["VENT. FS/4-400 ET"], publish_static=False)
        actual = run["results"]["VENT_FS4_400_ET"]
        self.assertEqual(compare_golden(actual, expected), [])
        self.assertEqual(actual["summary"]["quantity_total"], 14875)
        self.assertEqual(actual["summary"]["eligible_quantity"], 11740)
        self.assertEqual(actual["summary"]["final_quantity"], 11456)
        self.assertEqual(actual["summary"]["eligible_clients"], 176)
        self.assertEqual(actual["contract"]["equipment_top1_quantity"], 9530)


if __name__ == "__main__":
    unittest.main()
