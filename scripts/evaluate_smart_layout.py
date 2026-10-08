#!/usr/bin/env python3
"""Reproducible failure/change suite; machine results do not claim image review."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import time

from funfig.build import build_spec
from funfig.io import load_json, write_json_atomic
from funfig.manifest import sha256_file
from funfig.optimize import optimize_spec
from funfig.qa import inspect_spec
from funfig.layout import semantic_signature
from funfig.paths import PROJECT_ROOT


def case_spec(kind: str) -> dict:
    base = {'schema_version': '1.1', 'id': 'smart-' + kind, 'kind': 'tikz', 'recipe': 'flowchart',
            'theme': {'id': 'journal-muted'}, 'profile': {'id': 'journal-single-column'},
            'outputs': {'basename': 'figure'},
            'diagram': {'layout': {'type': 'auto', 'direction': 'down'}, 'nodes': [], 'edges': []}}
    diagram = base['diagram']
    count = 4 if kind not in {'feedback', 'long-chain', 'nested'} else 5
    labels = [f'Step {i + 1}' for i in range(count)]
    if kind == 'long-chain':
        labels = ['Collect and harmonize observations from several independent sources',
                  'Assess methodological quality and completeness of the available information',
                  'Estimate the mechanism with explicitly controlled confounding factors',
                  'Evaluate uncertainty through repeated validation across contexts',
                  'Report the supported conclusion and the limits of its generalization']
        diagram['layout']['direction'] = 'right'
    if kind == 'cjk-chain':
        labels = ['收集来自不同研究场景的原始资料', '核验数据质量并保留不确定性说明',
                  '在明确研究边界的条件下估计作用机制', '报告结论、证据与仍待检验的问题']
    if kind == 'math':
        labels = [r'$x_i \in \mathbb{R}$', r'$y = \alpha + \beta x$', r'$\sigma^2 > 0$', r'$p < 0.05$']
    for i, label in enumerate(labels):
        node = {'id': f'n{i}', 'label': label, 'role': 'process'}
        if kind == 'math': node['label_format'] = 'tex'
        diagram['nodes'].append(node)
    diagram['edges'] = [{'id': f'e{i}', 'from': f'n{i}', 'to': f'n{i+1}'} for i in range(count - 1)]
    if kind == 'large-grid':
        diagram['layout'] = {'type': 'grid', 'auto_fit': True, 'row_gap': '15mm', 'column_gap': '20mm'}
        for i, n in enumerate(diagram['nodes']):
            n.update(text_width='15mm', min_height='25mm', position={'type': 'grid', 'row': i, 'column': 0})
    elif kind == 'decision':
        base = load_json(PROJECT_ROOT / 'examples/templates/flowcharts/decision-branch/template.funfig.json')
        base['outputs'] = {'basename': 'figure'}
        base['diagram']['layout'] = {'type': 'auto', 'direction': 'down'}
        for n in base['diagram']['nodes']: n.pop('position', None)
    elif kind == 'nested':
        base['recipe'] = 'framework-diagram'
        for n in diagram['nodes']: n['role'] = 'module'
        diagram['groups'] = [{'id': 'inner', 'members': ['n0', 'n1'], 'label': 'Evidence'},
                             {'id': 'outer', 'members': ['inner', 'n2'], 'label': 'Study framework'},
                             {'id': 'result', 'members': ['n3', 'n4'], 'label': 'Evaluation'}]
    elif kind == 'feedback':
        diagram['edges'] += [{'id': 'f1', 'from': 'n4', 'to': 'n0', 'label': 'revise'},
                             {'id': 'f2', 'from': 'n3', 'to': 'n1', 'label': 'verify', 'label_side': 'left'}]
    elif kind == 'obstacle':
        diagram['nodes'] = [{'id': n, 'label': label, 'role': 'process', 'position': {'type': 'absolute', 'x': x, 'y': 0}}
                            for n, label, x in [('a', 'Input', 0), ('obstacle', 'Other module', 3), ('b', 'Output', 6)]]
        diagram['edges'] = [{'id': 'blocked', 'from': 'a', 'to': 'b', 'label': 'signal'}]
        diagram['layout'] = {'type': 'manual', 'measure': True, 'constraints': [
            {'type': 'pin', 'nodes': [n['id']], 'x': n['position']['x'], 'y': 0} for n in diagram['nodes']]}
    elif kind == 'pins':
        diagram['nodes'] = diagram['nodes'][:2]; diagram['edges'] = diagram['edges'][:1]
        diagram['layout']['constraints'] = [{'type': 'pin', 'nodes': ['n0'], 'x': 0, 'y': 0},
                                           {'type': 'pin', 'nodes': ['n1'], 'x': 0, 'y': 0},
                                           {'type': 'order-y', 'nodes': ['n0', 'n1']}]
    elif kind == 'impossible':
        diagram['nodes'] = diagram['nodes'][:1]; diagram['edges'] = []
        diagram['nodes'][0]['min_width'] = '120mm'
    elif kind == 'edit':
        diagram['nodes'][1]['label'] = 'A substantially longer replacement label requiring several extra lines'
    return base


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    cases = load_json(PROJECT_ROOT / 'tests/fixtures/smart-layout-cases.json')['cases']; results = []
    for case in cases:
        directory = args.out / case['id']; directory.mkdir(exist_ok=True)
        path = directory / 'figure.funfig.json'; spec = case_spec(case['kind']); signature = semantic_signature(spec)
        if case['kind'] == 'edit':
            short = copy.deepcopy(spec); short['diagram']['nodes'][1]['label'] = 'Short'
            write_json_atomic(path, short); build_spec(short, path)
        write_json_atomic(path, spec); started = time.monotonic()
        build_spec(spec, path); first = inspect_spec(spec, path)
        report = optimize_spec(spec, path)
        current = load_json(path)
        build_spec(current, path); final = inspect_spec(current, path)
        assert semantic_signature(current) == signature
        row = {**case, 'first_machine_pass': first['machine_checks_passed'], 'final_machine_pass': final['machine_checks_passed'],
               'first_defects': first['defects'], 'final_defects': final['defects'], 'adopted': report['adopted'],
               'evaluations': len(report['evaluations']), 'elapsed_seconds': round(time.monotonic()-started, 3),
               'hashes': load_json(directory / '.funfig/manifest.json')['hashes'],
               'visual_review': 'pending', 'preview': str(directory / '.funfig/preview.png')}
        results.append(row)
        print(case['id'], row['first_machine_pass'], '->', row['final_machine_pass'], flush=True)
    summary = {'version': '1.0', 'cases': results, 'first_machine_passes': sum(r['first_machine_pass'] for r in results),
               'final_machine_passes': sum(r['final_machine_pass'] for r in results), 'count': len(results),
               'visual_review': 'pending; review current hash-bound images independently'}
    write_json_atomic(args.out / 'results.json', summary)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
