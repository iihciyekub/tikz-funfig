#!/usr/bin/env python3
"""Optional development comparison, never a portable runtime dependency."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess
import time

from funfig.build import build_spec
from funfig.io import load_json, write_json_atomic
from funfig.layout import semantic_signature
from funfig.qa import inspect_spec

ELK_SCRIPT = r"""
const fs = require('fs');
const ELK = require(process.argv[1]);
const graph = JSON.parse(fs.readFileSync(0, 'utf8'));
new ELK().layout(graph).then(result => process.stdout.write(JSON.stringify(result)));
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('spec', type=Path); parser.add_argument('--elk-module', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True); parser.add_argument('--direction', choices=['DOWN', 'RIGHT'], default='DOWN')
    args = parser.parse_args(); spec = load_json(args.spec)
    manifest = load_json(args.spec.parent / '.funfig/manifest.json')
    geometry = load_json(args.spec.parent / '.funfig/geometry.json')
    resolved = manifest['layout']['resolved_diagram']
    if resolved.get('groups') or resolved.get('layout', {}).get('constraints') or any(e.get('to_edge') for e in resolved['edges']):
        raise ValueError('this comparison adapter is flat node-to-node only; compound graphs/pins/edge targets require a separate validated adapter')
    graph = {'id': 'root', 'layoutOptions': {'elk.algorithm': 'layered', 'elk.direction': args.direction,
                'elk.edgeRouting': 'ORTHOGONAL', 'elk.spacing.nodeNode': '6', 'elk.layered.spacing.nodeNodeBetweenLayers': '9',
                'elk.randomSeed': '1'}, 'children': [], 'edges': []}
    for node in resolved['nodes']:
        box = geometry['nodes'][node['id']]
        graph['children'].append({'id': node['id'], 'width': box['width'], 'height': box['height']})
    for i, edge in enumerate(resolved['edges']):
        item = {'id': edge.get('id', f'edge-{i}'), 'sources': [edge['from']], 'targets': [edge['to']]}
        label = geometry.get('labels', {}).get('edge-label:' + item['id'])
        if label:
            item['labels'] = [{'id': 'label-' + item['id'], 'text': edge['label'], 'width': label['width'], 'height': label['height']}]
        graph['edges'].append(item)
    started = time.monotonic()
    process = subprocess.run(['node', '-e', ELK_SCRIPT, str(args.elk_module.resolve())], input=json.dumps(graph), text=True, capture_output=True, check=True)
    output = json.loads(process.stdout); candidate = copy.deepcopy(spec); candidate['diagram'] = copy.deepcopy(resolved)
    candidate['diagram']['layout'] = {'type': 'manual', 'measure': True}
    positions = {n['id']: n for n in output['children']}
    for node in candidate['diagram']['nodes']:
        n = positions[node['id']]
        node['position'] = {'type': 'absolute', 'x': (n['x'] + n['width']/2)/10, 'y': -(n['y'] + n['height']/2)/10}
    routes = {e['id']: e for e in output['edges']}
    for i, edge in enumerate(candidate['diagram']['edges']):
        section = routes[edge.get('id', f'edge-{i}')]['sections'][0]
        points = section.get('bendPoints', [])
        if points:
            edge.update(route='polyline', routing={'points': [{'x': p['x']/10, 'y': -p['y']/10} for p in points]})
        else:
            edge.update(route='straight'); edge.pop('routing', None)
        # ELK section endpoints are boundary ports, not intermediate waypoints.
        # A duplicated terminal boundary point creates a degenerate TikZ segment
        # and can flip arrowheads despite an unchanged graph signature.
        for key, endpoint, nid in (('from_anchor', section['startPoint'], edge['from']),
                                   ('to_anchor', section['endPoint'], edge['to'])):
            node = positions[nid]
            candidates = {'west': abs(endpoint['x']-node['x']), 'east': abs(endpoint['x']-node['x']-node['width']),
                          'north': abs(endpoint['y']-node['y']), 'south': abs(endpoint['y']-node['y']-node['height'])}
            edge[key] = min(candidates, key=candidates.get)
    assert semantic_signature(candidate) == semantic_signature(spec)
    args.out.mkdir(parents=True, exist_ok=True); path = args.out / 'figure.funfig.json'; write_json_atomic(path, candidate)
    build_spec(candidate, path); qa = inspect_spec(candidate, path)
    report = {'engine': 'elkjs', 'version': load_json(args.elk_module.parent.parent / 'package.json')['version'],
              'direction': args.direction, 'elapsed_seconds': round(time.monotonic()-started, 3),
              'semantic_signature': semantic_signature(candidate), 'machine_checks_passed': qa['machine_checks_passed'],
              'defects': qa['defects'], 'width_mm': qa['pdf']['width_mm'], 'visual_review': 'pending',
              'limitations': ['flat adapter only', 'ELK label placement is not yet mapped exactly to TikZ path labels',
                              'user pins, compound groups, and edge targets need independently verified mapping']}
    write_json_atomic(args.out / 'comparison.json', report); print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
