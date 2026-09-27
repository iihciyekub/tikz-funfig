from __future__ import annotations

import importlib.util
import math
import unittest

from funfig.paths import PROJECT_ROOT


SCRIPT = PROJECT_ROOT / "packages/skill/scripts/fit_polar_geometry.py"
SPEC = importlib.util.spec_from_file_location("fit_polar_geometry", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FitPolarGeometryTests(unittest.TestCase):
    def test_regular_ring_recovers_center_radius_and_order(self) -> None:
        points = []
        for index in range(16):
            angle = math.radians(90 - index * 22.5)
            points.append([10 + 5 * math.cos(angle), 20 + 5 * math.sin(angle)])
        result = MODULE.analyze({"points": points})
        self.assertAlmostEqual(result["center"][0], 10.0, places=7)
        self.assertAlmostEqual(result["center"][1], 20.0, places=7)
        self.assertAlmostEqual(result["radius"], 5.0, places=7)
        self.assertEqual(result["node_count"], 16)
        self.assertEqual(result["suggested_structure_model"]["symmetry"]["group"], "C16")
        self.assertLess(result["symmetry"]["normalized_symmetry_error"], 1e-10)


if __name__ == "__main__":
    unittest.main()
