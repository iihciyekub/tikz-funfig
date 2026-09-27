from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from funfig.generative import GenerativeError, build_generative_design, compare_topology_hypotheses, render_generative_design
from funfig.generative_geometry import GeometryError, delaunay_triangles, safe_expression, split_box_edge_occlusion, voronoi_cells
from funfig.io import load_json, write_json_atomic
from funfig.paths import PROJECT_ROOT


GOLDEN = PROJECT_ROOT / "examples/golden/flowchart-decision/figure.design.json"


def _generative_design() -> dict:
    design = copy.deepcopy(load_json(GOLDEN))
    design["id"] = "generative-circular-network"
    design["family"] = "schematic"
    design["render_mode"] = "expert"
    design["knowledge_sources"] = ["pgfmanual-3.1.11a-p0160-0161"]
    design["routing"] = {
        "features": ["cyclic-symmetry", "dense-chords"],
        "recipe_candidate": "scientific-schematic",
        "unsupported_features": ["dense-rule-based-graph"],
        "decision": "expert",
        "reason": "The figure is generated from cyclic graph rules rather than independent schematic objects.",
        "expert_patterns": ["repeated-components"],
        "knowledge_queries": ["polar coordinates repeated graph"],
    }
    design["structure_model"] = {
        "coordinate_system": "polar",
        "symmetry": {"group": "C8", "order": 8, "phase_deg": 90, "tolerance": 0.01},
        "generators": [
            {"id": "outer", "type": "ring_nodes", "parameters": {"count": 8, "radius": 3.0, "node_radius": 0.22, "phase_deg": 90}},
            {"id": "boundary", "type": "boundary_circle", "parameters": {"nodes": "outer"}},
            {"id": "chords", "type": "complete_edges", "parameters": {"nodes": "outer"}},
            {"id": "center", "type": "center_node", "parameters": {"radius": 0.12}},
            {"id": "spokes", "type": "center_spokes", "parameters": {"nodes": "outer", "center": "center"}},
        ],
        "constraints": ["outer nodes are equally spaced", "center is at the origin"],
    }
    design["visual_density"] = {"target": "light", "edge_opacity": 0.36}
    design["search_space"] = [
        {"path": "visual_density.edge_opacity", "values": [0.28, 0.36, 0.44]},
    ]
    return design


class GenerativeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.design_path = self.root / "figure.design.json"
        write_json_atomic(self.design_path, _generative_design())

    def test_complete_circular_graph_is_rendered_deterministically(self) -> None:
        first, metadata = render_generative_design(self.design_path)
        text_a = first.read_text(encoding="utf-8")
        second, metadata_b = render_generative_design(self.design_path)
        text_b = second.read_text(encoding="utf-8")
        self.assertEqual(text_a, text_b)
        self.assertEqual(metadata, metadata_b)
        self.assertEqual(metadata["node_count"], 9)
        self.assertEqual(metadata["edge_count"], 36)
        self.assertIn("genedge/.style", text_a)
        self.assertIn("minimum size=0.440000cm", text_a)
        self.assertLess(metadata["resolved_density"]["edge_line_width_pt"], 0.5)

    def test_structure_model_requires_expert_mode(self) -> None:
        design = _generative_design()
        design["render_mode"] = "structured"
        design["routing"]["decision"] = "structured"
        write_json_atomic(self.design_path, design)
        with self.assertRaises(ValueError):
            render_generative_design(self.design_path)

    def test_unknown_generator_is_rejected(self) -> None:
        design = _generative_design()
        design["structure_model"]["generators"][0]["type"] = "magic_graph"
        # The schema rejects unsupported generator families before runtime rendering.
        write_json_atomic(self.design_path, design)
        with self.assertRaises(ValueError):
            render_generative_design(self.design_path)

    def test_invalid_generator_reference_is_rejected(self) -> None:
        design = _generative_design()
        design["structure_model"]["generators"][1]["parameters"] = {"nodes": "missing"}
        write_json_atomic(self.design_path, design)
        with self.assertRaises(GenerativeError):
            render_generative_design(self.design_path)

    def test_skew_lattice_generates_nodes_edges_and_cells(self) -> None:
        design = _generative_design()
        design["id"] = "generative-skew-lattice"
        design["structure_model"] = {
            "coordinate_system": "cartesian",
            "symmetry": {"group": "translation", "order": 1, "phase_deg": 0, "tolerance": 0.0},
            "generators": [
                {"id": "mesh", "type": "lattice_nodes", "parameters": {"rows": 3, "cols": 4, "origin": [0, 0], "basis_u": [1, 0], "basis_v": [0.5, 0.8660254], "node_radius": 0.08}},
                {"id": "mesh_edges", "type": "lattice_edges", "parameters": {"nodes": "mesh", "neighbor_steps": [[0, 1], [1, 0], [1, -1]]}},
                {"id": "mesh_cells", "type": "lattice_cells", "parameters": {"nodes": "mesh", "cell_mode": "triangles", "fill_opacity": 0.025}},
            ],
            "constraints": ["shared lattice basis", "nearest-neighbour edges only"],
        }
        write_json_atomic(self.design_path, design)
        tex, metadata = render_generative_design(self.design_path)
        self.assertEqual(metadata["node_count"], 12)
        self.assertEqual(metadata["edge_count"], 23)
        self.assertEqual(metadata["polygon_count"], 12)
        self.assertIn("gencell/.style", tex.read_text(encoding="utf-8"))

    def test_complete_bipartite_graph_uses_line_node_groups(self) -> None:
        design = _generative_design()
        design["id"] = "generative-bipartite"
        design["structure_model"] = {
            "coordinate_system": "cartesian",
            "symmetry": {"group": "bilateral", "order": 2, "phase_deg": 0, "tolerance": 0.0},
            "generators": [
                {"id": "left", "type": "line_nodes", "parameters": {"count": 3, "start": [-2, 1], "end": [-2, -1], "node_radius": 0.14}},
                {"id": "right", "type": "line_nodes", "parameters": {"count": 4, "start": [2, 1.2], "end": [2, -1.2], "node_radius": 0.14}},
                {"id": "links", "type": "complete_bipartite_edges", "parameters": {"left": "left", "right": "right"}},
            ],
            "constraints": ["every left node connects to every right node"],
        }
        write_json_atomic(self.design_path, design)
        _, metadata = render_generative_design(self.design_path)
        self.assertEqual(metadata["node_count"], 7)
        self.assertEqual(metadata["edge_count"], 12)

    def test_parametric_fractal_and_projected_solids_generate_curves(self) -> None:
        cases = [
            (
                "parametric",
                "cartesian",
                [{"id": "rose", "type": "parametric_curve", "parameters": {"family": "rose", "samples": 181, "amplitude": 3.0, "petals": 5}}],
                1,
            ),
            (
                "fractal",
                "cartesian",
                [{"id": "koch", "type": "koch_snowflake", "parameters": {"depth": 2, "radius": 3.0}}],
                1,
            ),
            (
                "box",
                "3d",
                [{"id": "box", "type": "projected_box", "parameters": {"size": [3, 2, 2]}}],
                12,
            ),
            (
                "prism",
                "3d",
                [{"id": "prism", "type": "projected_prism", "parameters": {"sides": 6, "radius": 2.4, "height": 3.2}}],
                18,
            ),
        ]
        for case_id, coordinate_system, generators, expected_curves in cases:
            with self.subTest(case=case_id):
                design = _generative_design()
                design["id"] = f"generative-{case_id}"
                design["structure_model"] = {
                    "coordinate_system": coordinate_system,
                    "symmetry": {"group": "generated", "order": 1, "phase_deg": 0, "tolerance": 0.0},
                    "generators": generators,
                    "constraints": ["deterministic geometry"],
                }
                write_json_atomic(self.design_path, design)
                tex, metadata = render_generative_design(self.design_path)
                self.assertEqual(metadata["curve_count"], expected_curves)
                self.assertIn("gencurve/.style", tex.read_text(encoding="utf-8"))

    def test_new_golden_geometry_is_deterministic(self) -> None:
        expected = {
            "hidden-box": (0, 0, 0, 12, 3),
            "box-occlusion": (0, 0, 0, 18, 0),
            "hexagonal-prism": (0, 0, 0, 18, 5),
            "point-dual": (5, 8, 5, 0, 0),
            "expression-curve": (0, 0, 0, 1, 0),
            "dragon-lsystem": (0, 0, 0, 1, 0),
            "truchet-tiling": (0, 0, 0, 96, 0),
        }
        for name, counts in expected.items():
            with self.subTest(name=name):
                golden = PROJECT_ROOT / f"examples/golden/generative-{name}/figure.design.json"
                first, metadata = render_generative_design(golden, output=self.root / "first.tex")
                first_text = first.read_text(encoding="utf-8")
                second, metadata2 = render_generative_design(golden, output=self.root / "second.tex")
                self.assertEqual(first_text, second.read_text(encoding="utf-8"))
                self.assertEqual(metadata, metadata2)
                self.assertEqual(tuple(metadata[key] for key in ("node_count", "edge_count", "polygon_count", "curve_count", "hidden_curve_count")), counts)
                if name == "hidden-box":
                    self.assertEqual(first_text.count(r"\draw[genhidden]"), 3)
                if name == "hexagonal-prism":
                    self.assertEqual(first_text.count(r"\draw[genhidden]"), 5)

    def test_expression_rejects_python_and_undefined_samples(self) -> None:
        for expression in ("__import__('os').system('echo bad')", "t.__class__", "[t][0]", "2**100"):
            with self.subTest(expression=expression):
                try:
                    compiled = safe_expression(expression)
                    compiled(1.0)
                except GeometryError:
                    pass
                else:
                    self.fail("unsafe or unbounded expression was accepted")
        design = load_json(PROJECT_ROOT / "examples/golden/generative-expression-curve/figure.design.json")
        design["structure_model"]["generators"][0]["parameters"]["x"] = "1/(t-1)"
        design["structure_model"]["generators"][0]["parameters"].update({"t_min": 0, "t_max": 2, "samples": 17})
        write_json_atomic(self.design_path, design)
        with self.assertRaises(GenerativeError):
            render_generative_design(self.design_path)

    def test_dual_geometry_boundary_and_degeneracy(self) -> None:
        points = [(0, 0), (1, 0), (1, 1), (0, 1)]
        triangles = delaunay_triangles(points)
        self.assertEqual(len(triangles), 2)
        self.assertEqual(len({tuple(sorted(edge)) for tri in triangles for edge in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0]))}), 5)
        cells = voronoi_cells([(0, 0), (2, 0)], (-1, -1, 3, 1))
        self.assertTrue(all(abs(x) <= 1.0000001 for x, _ in cells[0] if x > 0))
        with self.assertRaises(GeometryError):
            delaunay_triangles([(0, 0), (1, 0), (2, 0)])

    def test_projected_box_camera_must_match_projection(self) -> None:
        design = load_json(PROJECT_ROOT / "examples/golden/generative-hidden-box/figure.design.json")
        box = design["structure_model"]["generators"][0]["parameters"]
        box["camera_direction"] = [1, 0, 0]
        write_json_atomic(self.design_path, design)
        with self.assertRaisesRegex(GenerativeError, "perpendicular"):
            render_generative_design(self.design_path)
        box["camera_direction"] = [1, 1, 0.72]
        write_json_atomic(self.design_path, design)
        _, metadata = render_generative_design(self.design_path)
        self.assertEqual(metadata["hidden_curve_count"], 3)

    def test_projected_prism_validates_sides_camera_and_visibility(self) -> None:
        design = load_json(PROJECT_ROOT / "examples/golden/generative-hexagonal-prism/figure.design.json")
        params = design["structure_model"]["generators"][0]["parameters"]
        params["sides"] = 2
        write_json_atomic(self.design_path, design)
        with self.assertRaises(GenerativeError):
            render_generative_design(self.design_path)

        params["sides"] = 6
        params["camera_direction"] = [1, 0, 0]
        write_json_atomic(self.design_path, design)
        with self.assertRaisesRegex(GenerativeError, "perpendicular"):
            render_generative_design(self.design_path)

        params.pop("camera_direction")
        params["visibility"] = "visible_only"
        write_json_atomic(self.design_path, design)
        _, metadata = render_generative_design(self.design_path)
        self.assertEqual(metadata["curve_count"], 13)
        self.assertEqual(metadata["hidden_curve_count"], 0)

    def test_box_edge_is_split_at_inter_object_occlusion(self) -> None:
        pieces = split_box_edge_occlusion((0, 0.5, 0.5), (2, 0.5, 0.5),
                                           [((0.5, 0, 2), (1, 1, 1))], (0, 0, 1))
        self.assertEqual([covered for _, _, covered in pieces], [False, True, False])
        self.assertAlmostEqual(pieces[1][0][0], 0.5)
        self.assertAlmostEqual(pieces[1][1][0], 1.5)
        design = load_json(PROJECT_ROOT / "examples/golden/generative-box-occlusion/figure.design.json")
        design["structure_model"]["generators"][1]["parameters"]["project_x"] = [1, 0]
        write_json_atomic(self.design_path, design)
        with self.assertRaisesRegex(GenerativeError, "shared projection"):
            render_generative_design(self.design_path)

    def test_missing_reference_image_is_reported_cleanly(self) -> None:
        design = load_json(PROJECT_ROOT / "examples/golden/generative-cyclic-topology/figure.design.json")
        write_json_atomic(self.design_path, design)
        with self.assertRaisesRegex(GenerativeError, "cannot read reference image"):
            compare_topology_hypotheses(self.design_path, self.root / "missing.png", limit=3)

    def test_l_system_rejects_excessive_expansion(self) -> None:
        design = load_json(PROJECT_ROOT / "examples/golden/generative-dragon-lsystem/figure.design.json")
        design["structure_model"]["generators"][0]["parameters"].update({"axiom": "F", "rules": {"F": "FFFFFFFFFF"}, "depth": 5})
        write_json_atomic(self.design_path, design)
        with self.assertRaises(GenerativeError):
            render_generative_design(self.design_path)

    def test_truchet_rejects_collapsed_affine_grid(self) -> None:
        design = load_json(PROJECT_ROOT / "examples/golden/generative-truchet-tiling/figure.design.json")
        design["structure_model"]["generators"][0]["parameters"]["basis_v"] = [1.6, 0]
        write_json_atomic(self.design_path, design)
        with self.assertRaisesRegex(GenerativeError, "independent"):
            render_generative_design(self.design_path)

    @unittest.skipUnless(shutil.which("latexmk") and shutil.which("pdftoppm"), "TeX and Poppler required")
    def test_reference_image_ranks_rendered_topologies(self) -> None:
        design = load_json(PROJECT_ROOT / "examples/golden/generative-cyclic-topology/figure.design.json")
        write_json_atomic(self.design_path, design)
        pdf, _, _ = build_generative_design(self.design_path)
        reference = self.root / "reference"
        subprocess.run(["pdftoppm", "-f", "1", "-singlefile", "-png", "-scale-to", "512", str(pdf), str(reference)], check=True)
        preview, report = compare_topology_hypotheses(self.design_path, reference.with_suffix(".png"), limit=3)
        self.assertTrue(preview.is_file())
        candidates = load_json(report)["candidates"]
        self.assertEqual(candidates[0]["topology"], "complete")
        self.assertLess(candidates[0]["score"], candidates[1]["score"])


if __name__ == "__main__":
    unittest.main()
