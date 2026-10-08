from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from funfig.build import build_spec
from funfig.geometry import geometry_defects
from funfig.io import load_json, write_json_atomic
from funfig.layout import plan_layout, semantic_signature, constraint_defects
from funfig.optimize import optimize_spec, route_around, repair
from funfig.paths import PROJECT_ROOT
from funfig.qa import inspect_spec, analyze_pdf
from funfig.schema import validate_spec
from funfig.templates import assess_template, get_template
from funfig.render import render_spec
from funfig.expert import build_expert


def base_spec() -> dict:
    return {'schema_version': '1.1', 'id': 'smart-test', 'recipe': 'flowchart', 'kind': 'tikz',
            'profile': {'id': 'journal-single-column'}, 'theme': {'id': 'journal-muted'},
            'outputs': {'basename': 'figure'}, 'diagram': {'layout': {'type': 'auto', 'direction': 'down'},
            'nodes': [{'id': 'a', 'label': 'Input', 'role': 'process'},
                      {'id': 'b', 'label': 'Validate', 'role': 'process'},
                      {'id': 'c', 'label': 'Result', 'role': 'process'}],
            'edges': [{'id': 'ab', 'from': 'a', 'to': 'b'}, {'id': 'bc', 'from': 'b', 'to': 'c'}]}}


class SmartLayoutTests(unittest.TestCase):
    def test_new_golden_has_deterministic_render_and_design(self):
        source = PROJECT_ROOT / 'examples/golden/smart-layout'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'figure.funfig.json'; spec = load_json(source / path.name)
            write_json_atomic(path, spec); tex, _ = render_spec(spec, path)
            self.assertEqual(tex.read_text(), (source / 'smart-layout.tex').read_text())

    def test_invalid_constraints_and_polyline_are_rejected(self):
        for record in ({'type': 'pin', 'nodes': ['a'], 'x': True, 'y': 0},
                       {'type': 'align-x', 'nodes': ['missing', 'a']},
                       {'type': 'order-y', 'nodes': ['a', 'b'], 'gap': '-2mm'},
                       {'type': 'equal-height', 'nodes': ['a', 'a']}):
            spec = base_spec(); spec['diagram']['layout']['constraints'] = [record]
            self.assertFalse(validate_spec(spec).ok)
        spec = base_spec(); spec['diagram']['edges'][0].update(route='polyline', routing={'points': [{'x': float('inf'), 'y': 0}]})
        self.assertFalse(validate_spec(spec).ok)

    def test_pins_win_over_impossible_order_and_report_conflict(self):
        spec = base_spec(); spec['diagram']['layout']['constraints'] = [
            {'type': 'pin', 'nodes': ['a'], 'x': 0, 'y': 0},
            {'type': 'pin', 'nodes': ['b'], 'x': 0, 'y': 0}, {'type': 'order-y', 'nodes': ['a', 'b']}]
        planned, report = plan_layout(spec)
        self.assertEqual(planned['diagram']['nodes'][0]['position'], {'type': 'absolute', 'x': 0, 'y': 0})
        self.assertTrue(any(d['type'] == 'constraint-conflict' for d in report['conflicts']))

    def test_semantics_exclude_style_but_include_topology_labels_and_groups(self):
        spec = base_spec(); signature = semantic_signature(spec)
        changed = copy.deepcopy(spec); changed['theme']['id'] = 'journal-monochrome'
        self.assertEqual(signature, semantic_signature(changed))
        for field, value in (('to', 'c'), ('label', 'changed meaning'), ('arrows', 'backward')):
            changed = copy.deepcopy(spec); changed['diagram']['edges'][0][field] = value
            self.assertNotEqual(signature, semantic_signature(changed))
        scientific = base_spec(); scientific['recipe'] = 'scientific-schematic'
        for i, node in enumerate(scientific['diagram']['nodes']):
            node.update(role='component', text_width='15mm', position={'type': 'absolute', 'x': i * 3, 'y': 0})
        scientific['diagram']['layout'] = {'type': 'manual', 'measure': True}
        proposed, actions = repair(scientific, {'defects': [{'id': 'overflow', 'type': 'text-overflow', 'objects': ['a'],
                                                           'evidence': {'overflow_pt': 10}}]}, {'nodes': {}}, scientific['diagram'])
        self.assertFalse(actions)
        self.assertEqual(proposed, scientific)

    def test_input_order_does_not_reverse_a_dag(self):
        spec = base_spec(); spec['diagram']['nodes'].reverse()
        planned, _ = plan_layout(spec)
        nodes = {n['id']: n['position'] for n in planned['diagram']['nodes']}
        self.assertGreater(nodes['a']['y'], nodes['b']['y'])
        self.assertGreater(nodes['b']['y'], nodes['c']['y'])

    def test_actual_measurement_and_explicit_sizes_control_spacing(self):
        spec = base_spec(); geometry = {'nodes': {n['id']: {'width': 22, 'height': 35} for n in spec['diagram']['nodes']}}
        planned, report = plan_layout(spec, geometry)
        nodes = planned['diagram']['nodes']
        self.assertGreaterEqual((nodes[0]['position']['y'] - nodes[1]['position']['y']) * 10, 41)
        self.assertEqual(report['measurement'], 'tex-anchors')

    def test_template_fit_rejects_incompatible_count_width_and_density(self):
        spec = base_spec(); spec['diagram']['nodes'][0]['label'] = 'very long label ' * 15
        fit = assess_template(get_template('merge-split'), spec)
        self.assertFalse(fit['eligible'])
        self.assertGreaterEqual(len(fit['reasons']), 3)

    def test_missing_text_checker_cannot_pass(self):
        with patch('funfig.qa._pdf_info', return_value={'pages': 1, 'width_mm': 80, 'height_mm': 40}), patch('funfig.qa._pdf_text_metrics', return_value=None):
            result = analyze_pdf(Path('unused.pdf'), target_width_mm=88)
        self.assertIn('check-unavailable', [d['type'] for d in result['defects']])

    @unittest.skipUnless(shutil.which('latexmk') and shutil.which('pdftotext'), 'TeX/Poppler required')
    def test_measured_build_cache_invalidation_equal_size_and_freshness(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'figure.funfig.json'; spec = base_spec()
            spec['diagram']['nodes'][1]['min_height'] = '25mm'
            spec['diagram']['layout']['constraints'] = [{'type': 'align-x', 'nodes': ['a', 'b', 'c']},
                                                        {'type': 'equal-height', 'nodes': ['a', 'b']}]
            write_json_atomic(path, spec); build_spec(spec, path)
            geom = load_json(path.parent / '.funfig/geometry.json')
            manifest = load_json(path.parent / '.funfig/manifest.json')
            self.assertFalse(constraint_defects(manifest['layout']['resolved_diagram'], geom['nodes']))
            self.assertFalse(geometry_defects(manifest['layout']['resolved_diagram'], geom))
            build_spec(spec, path)
            self.assertTrue(load_json(path.parent / '.funfig/manifest.json')['layout']['cache_hit'])
            spec['diagram']['nodes'][0]['label'] = 'A much longer replacement that wraps to multiple lines'
            write_json_atomic(path, spec)
            self.assertIn('check-unavailable', [d['type'] for d in inspect_spec(spec, path)['defects']])
            build_spec(spec, path)
            self.assertFalse(load_json(path.parent / '.funfig/manifest.json')['layout']['cache_hit'])

    @unittest.skipUnless(shutil.which('latexmk') and shutil.which('pdftotext'), 'TeX/Poppler required')
    def test_route_repair_preserves_pins_and_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = base_spec(); spec['diagram']['layout'] = {'type': 'manual', 'measure': True, 'constraints': []}
            for i, n in enumerate(spec['diagram']['nodes']):
                n['position'] = {'type': 'absolute', 'x': i * 3, 'y': 0}
                spec['diagram']['layout']['constraints'].append({'type': 'pin', 'nodes': [n['id']], 'x': i * 3, 'y': 0})
            spec['diagram']['edges'] = [{'id': 'ac', 'from': 'a', 'to': 'c', 'label': 'signal'}]
            path = Path(tmp) / 'figure.funfig.json'; write_json_atomic(path, spec)
            report = optimize_spec(spec, path)
            self.assertTrue(report['adopted'])
            self.assertEqual(report['final_score'], [0, 0, 0])
            updated = load_json(path)
            self.assertEqual(semantic_signature(spec), semantic_signature(updated))
            for a, b in zip(spec['diagram']['nodes'], updated['diagram']['nodes']):
                self.assertEqual(a['position'], b['position'])
            self.assertEqual(updated['diagram']['edges'][0]['route'], 'polyline')
            self.assertEqual(load_json(path.parent / '.funfig/manifest.json')['qa']['visual_review'], 'pending')

    @unittest.skipUnless(shutil.which('latexmk') and shutil.which('pdftotext'), 'TeX/Poppler required')
    def test_infeasible_conditions_do_not_overwrite_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = base_spec(); spec['diagram']['nodes'][0]['min_width'] = '150mm'
            path = Path(tmp) / 'figure.funfig.json'; write_json_atomic(path, spec)
            original = path.read_bytes(); report = optimize_spec(spec, path, max_candidates=2, repair_limit=1)
            self.assertFalse(report['adopted'])
            self.assertEqual(path.read_bytes(), original)
            self.assertTrue(any(d['type'] == 'space-infeasible' for r in report['evaluations'] for d in r.get('defects', [])))

    @unittest.skipUnless(shutil.which('latexmk') and shutil.which('pdftotext'), 'TeX/Poppler required')
    def test_final_failure_restores_exact_previous_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'figure.funfig.json'; spec = base_spec()
            write_json_atomic(path, spec); build_spec(spec, path); inspect_spec(spec, path)
            names = [path.name, 'figure.tex', 'figure.pdf', '.funfig/manifest.json', '.funfig/geometry.json', '.funfig/preview.png']
            before = {name: (path.parent / name).read_bytes() for name in names}
            real_inspect = inspect_spec; calls = 0
            def injected(spec, path):
                nonlocal calls
                calls += 1
                qa = real_inspect(spec, path)
                if calls == 2:
                    qa['defects'].append({'id': 'injected', 'type': 'check-unavailable', 'objects': ['pdf'], 'severity': 'error'})
                return qa
            with patch('funfig.optimize.inspect_spec', side_effect=injected):
                result = optimize_spec(spec, path, max_candidates=1, repair_limit=0)
            self.assertFalse(result['adopted'])
            self.assertIn('rollback', result)
            for name, content in before.items():
                self.assertEqual((path.parent / name).read_bytes(), content)

    @unittest.skipUnless(shutil.which('latexmk') and shutil.which('pdftotext'), 'TeX/Poppler required')
    def test_expert_uses_same_readability_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            tex = Path(tmp) / 'figure.tex'
            tex.write_text(r'\documentclass[tikz,border=2pt]{standalone}' + '\n' +
                           r'\begin{document}\begin{tikzpicture}\node[font=\tiny]{Very small text};\end{tikzpicture}\end{document}')
            _, manifest = build_expert(tex, cards=['diagram-layout-repair'], target_width_mm=88)
            qa = load_json(manifest)['qa']
            self.assertFalse(qa['machine_checks_passed'])
            self.assertIn('text-risk', [d['type'] for d in qa['defects']])

    @unittest.skipUnless(shutil.which('latexmk') and shutil.which('pdftotext'), 'TeX/Poppler required')
    def test_unbreakable_node_text_is_diagnosed_and_repaired(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = base_spec(); spec['diagram']['nodes'][1].update(label='electroencephalographically', text_width='15mm')
            path = Path(tmp) / 'figure.funfig.json'; write_json_atomic(path, spec)
            build_spec(spec, path); qa = inspect_spec(spec, path)
            self.assertIn('text-overflow', [d['type'] for d in qa['defects']])
            result = optimize_spec(spec, path, max_candidates=1)
            self.assertEqual(result.get('final_score'), [0, 0, 0])
            self.assertEqual(load_json(path)['diagram']['nodes'][1]['label'], spec['diagram']['nodes'][1]['label'])


if __name__ == '__main__':
    unittest.main()
