"""Bounded measured repair with hard gates and reversible adoption."""
from __future__ import annotations

import copy
import heapq
import shutil
import time
from pathlib import Path
from typing import Any

from .build import build_spec, BuildError
from .geometry import segment_hits
from .geometry import length_mm
from .io import load_json, write_json_atomic
from .layout import semantic_signature, apply_constraints, profile_for
from .manifest import utc_now
from .qa import inspect_spec, QAError
from .knowledge import knowledge_root


def score(qa: dict[str, Any]) -> tuple[int, int, int]:
    defects = qa.get('defects', [])
    # Aesthetic gains cannot compensate for changed hard conditions or content.
    hard = sum(d['type'] in {'constraint-conflict', 'space-infeasible', 'text-risk',
                            'check-unavailable', 'layout-not-converged', 'pdf-pages'} for d in defects)
    return hard, len(defects), len(qa.get('warnings', []))


def route_around(edge: dict[str, Any], geometry: dict[str, Any], edge_index: int) -> dict[str, Any] | None:
    """Orthogonal visibility grid using measured rectangles and endpoint ports."""
    nodes = geometry['nodes']
    if edge.get('to') not in nodes or edge['from'] == edge.get('to'):
        return None
    if any(edge.get(k) and edge[k] not in {'north', 'south', 'east', 'west'} for k in ('from_anchor', 'to_anchor')):
        return None  # center/corner/scientific connection semantics require manual routing
    source, target = nodes[edge['from']], nodes[edge['to']]
    eid = edge.get('id', f'edge-{edge_index}')
    boxes = list(nodes.values()) + [b for k, b in geometry.get('labels', {}).items()
                                   if k != f'edge-label:{eid}']
    margin = 2.0
    def ports(box):
        return {'east': (box['right'] + margin + .5, box['y']),
                'west': (box['left'] - margin - .5, box['y']),
                'north': (box['x'], box['top'] + margin + .5),
                'south': (box['x'], box['bottom'] - margin - .5)}
    starts, ends = ports(source), ports(target)
    # Respect explicitly selected scientific connection ports.
    if edge.get('from_anchor') in starts:
        starts = {edge['from_anchor']: starts[edge['from_anchor']]}
    if edge.get('to_anchor') in ends:
        ends = {edge['to_anchor']: ends[edge['to_anchor']]}
    xs = sorted({round(v, 5) for b in boxes for v in (b['left'] - margin - .5, b['right'] + margin + .5)}
                | {round(p[0], 5) for p in [*starts.values(), *ends.values()]})
    ys = sorted({round(v, 5) for b in boxes for v in (b['bottom'] - margin - .5, b['top'] + margin + .5)}
                | {round(p[1], 5) for p in [*starts.values(), *ends.values()]})
    vertices = {(x, y) for x in xs for y in ys
                if not any(b['left'] - margin < x < b['right'] + margin and
                           b['bottom'] - margin < y < b['top'] + margin for b in boxes)}
    adjacency = {p: [] for p in vertices}
    for x in xs:
        points = sorted((p for p in vertices if p[0] == x), key=lambda p: p[1])
        for a, b in zip(points, points[1:]):
            if not any(segment_hits(a, b, box, margin) for box in boxes):
                adjacency[a].append((b, 'v')); adjacency[b].append((a, 'v'))
    for y in ys:
        points = sorted((p for p in vertices if p[1] == y), key=lambda p: p[0])
        for a, b in zip(points, points[1:]):
            if not any(segment_hits(a, b, box, margin) for box in boxes):
                adjacency[a].append((b, 'h')); adjacency[b].append((a, 'h'))
    goals = {(round(p[0], 5), round(p[1], 5)): name for name, p in ends.items()}
    queue = []; best = {}; serial = 0
    for name, point in starts.items():
        p = (round(point[0], 5), round(point[1], 5))
        if p not in vertices:
            continue
        initial = abs(p[0] - source['x']) + abs(p[1] - source['y'])
        heapq.heappush(queue, (initial, serial, p, '', [p], name)); serial += 1
    while queue:
        cost, _, point, direction, path, anchor = heapq.heappop(queue)
        state = point, direction
        if cost >= best.get(state, float('inf')):
            continue
        best[state] = cost
        if point in goals:
            compact = [path[0]]
            for a, b, c in zip(path, path[1:], path[2:]):
                if (b[0] - a[0]) * (c[1] - b[1]) != (b[1] - a[1]) * (c[0] - b[0]):
                    compact.append(b)
            if path[-1] != compact[-1]:
                compact.append(path[-1])
            if len(compact) > 12:
                return None
            result = copy.deepcopy(edge)
            result.update(route='polyline', from_anchor=anchor, to_anchor=goals[point],
                          routing={'points': [{'x': round(x / 10, 6), 'y': round(y / 10, 6)} for x, y in compact]})
            full = [(source['x'], source['y'])] + compact + [(target['x'], target['y'])]
            middle = (len(full) - 2) // 2
            a, b = full[middle:middle + 2]
            if abs(a[0] - b[0]) < abs(a[1] - b[1]):
                side = 'left' if (a[0] + b[0]) / 2 < (source['x'] + target['x']) / 2 else 'right'
            else:
                side = 'above' if (a[1] + b[1]) / 2 > (source['y'] + target['y']) / 2 else 'below'
            result.update(label_side=side, label_position=.5, label_sloped=False)
            return result
        for neighbor, axis in adjacency.get(point, []):
            length = abs(neighbor[0] - point[0]) + abs(neighbor[1] - point[1])
            heapq.heappush(queue, (cost + length + (4 if direction and axis != direction else 0), serial,
                                  neighbor, axis, path + [neighbor], anchor)); serial += 1
    return None


def repair(spec: dict[str, Any], qa: dict[str, Any], geometry: dict[str, Any],
           resolved: dict[str, Any], *, relayout: bool = False, round_index: int = 0) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    result = copy.deepcopy(spec)
    result['diagram'] = copy.deepcopy(resolved)
    diagram = result['diagram']; diagram.setdefault('layout', {})['measure'] = True
    priorities = {'node-overlap': 0, 'text-overflow': 0, 'edge-node-crossing': 1, 'label-overlap': 2,
                  'edge-label-crossing': 3, 'label-node-overlap': 4}
    defects = sorted(qa.get('defects', []), key=lambda d: priorities.get(d['type'], 9)); actions = []
    nodes = {n['id']: n for n in diagram['nodes']}
    pins = {c['nodes'][0] for c in diagram['layout'].get('constraints', []) if c['type'] == 'pin'}
    original_layout = spec['diagram'].get('layout', {})
    can_move = relayout or (original_layout.get('type') != 'manual' and spec['recipe'] != 'scientific-schematic')
    for defect in defects:
        kind, objects = defect['type'], defect['objects']
        if kind == 'text-overflow' and objects[0] in nodes:
            node = nodes[objects[0]]
            if spec['recipe'] == 'scientific-schematic' and node.get('role') == 'component' and not relayout:
                continue  # component dimensions can encode physical proportions
            node['text_width'] = f"{length_mm(node.get('text_width'), 32) + defect['evidence']['overflow_pt'] * 25.4 / 72.27 + 1:.3f}mm"
            actions.append({'prescription': 'expand-node-text', 'objects': objects, 'cause': defect['id']})
            break
        if kind == 'label-overlap' and all(o.startswith('group-label:') for o in objects):
            a, b = [o.split(':', 1)[1] for o in objects]
            groups = {g['id']: g for g in diagram.get('groups', [])}
            target = a if b in groups[a]['members'] else b
            height = max(geometry['labels'][o]['height'] for o in objects)
            groups[target]['title_gap'] = f"{length_mm(groups[target].get('title_gap')) + height + 1:.3f}mm"
            actions.append({'prescription': 'separate-group-title', 'objects': [target], 'cause': defect['id']})
            break
        if kind == 'node-overlap' and can_move:
            a, b = objects
            if b in pins:
                a, b = b, a
            if b in pins:
                continue
            for nid, node in nodes.items():
                box = geometry['nodes'][nid]
                node['position'] = {'type': 'absolute', 'x': box['x'] / 10, 'y': box['y'] / 10}
            box_a, box_b = geometry['nodes'][a], geometry['nodes'][b]
            nodes[b]['position']['y'] = (box_a['bottom'] - 6 - box_b['height'] / 2) / 10
            actions.append({'prescription': 'separate-node', 'objects': [b], 'cause': defect['id']})
            break  # remeasure before touching another node or its connected paths
        if kind in {'label-node-overlap', 'label-overlap'}:
            label = next((o for o in objects if o.startswith('edge-label:')), None)
            if label:
                for index, edge in enumerate(diagram.get('edges', [])):
                    if label == 'edge-label:' + edge.get('id', f'edge-{index}'):
                        edge['label_position'] = (.35, .65, .5)[round_index % 3]
                        sides = ('above', 'below', 'right', 'left')
                        old = edge.get('label_side', 'above')
                        nbox = geometry['nodes'].get(objects[-1]); lbox = geometry['labels'].get(label)
                        if nbox and lbox:
                            dx, dy = lbox['x'] - nbox['x'], lbox['y'] - nbox['y']
                            edge['label_side'] = ('left' if dx < 0 else 'right') if abs(dx) > abs(dy) else ('below' if dy < 0 else 'above')
                        else:
                            edge['label_side'] = sides[(sides.index(old) + 1) % 4] if old in sides else 'above'
                        actions.append({'prescription': 'move-edge-label', 'objects': [label], 'cause': defect['id']})
        if kind in {'edge-node-crossing', 'edge-label-crossing'}:
            for index, edge in enumerate(diagram.get('edges', [])):
                if edge.get('id', f'edge-{index}') != objects[0]:
                    continue
                routed = route_around(edge, geometry, index)
                if routed:
                    diagram['edges'][index] = routed
                    actions.append({'prescription': 'visibility-route', 'objects': [objects[0]], 'cause': defect['id']})
                    break
            if actions:
                break  # new route/label bounds must be measured before the next repair
    if actions:
        dimensions = {n: (b['width'], b['height']) for n, b in geometry['nodes'].items()}
        if all(n.get('position', {}).get('type') == 'absolute' for n in nodes.values()):
            apply_constraints(result, dimensions)
    return result, actions


def optimize_spec(spec: dict[str, Any], spec_path: Path, *, relayout: bool = False,
                  max_candidates: int = 3, repair_limit: int = 3) -> dict[str, Any]:
    if spec.get('schema_version') != '1.1' or not spec.get('diagram'):
        raise ValueError('measured optimization requires a structured 1.1 diagram; plots/Expert use shared inspection and visual repair')
    if not 1 <= max_candidates <= 3 or not 0 <= repair_limit <= 3:
        raise ValueError('candidate and repair budgets must be within 1–3 and 0–3')
    prescriptions = load_json(knowledge_root() / 'layout-prescriptions.json')
    started = time.monotonic(); original_text = spec_path.read_text(encoding='utf-8')
    signature = semantic_signature(spec); figure_dir = spec_path.parent
    session = figure_dir / '.funfig' / 'optimization' / (utc_now().replace(':', '').replace('.', '-') + '-' + str(time.time_ns()))
    session.mkdir(parents=True, exist_ok=False)
    backup = session / 'previous'
    backup.mkdir()
    basename = (spec.get('outputs') or {}).get('basename', 'figure')
    original_artifacts = [spec_path.name, *[basename + '.' + ext for ext in ('tex', 'pdf', 'svg')],
                          '.funfig/manifest.json', '.funfig/geometry.json', '.funfig/preview.png']
    for name in original_artifacts:
        source = figure_dir / name
        if source.is_file():
            target = backup / name; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    original = copy.deepcopy(spec); original['diagram'].setdefault('layout', {})['measure'] = True
    original['diagram']['layout']['target_width_mm'] = profile_for(spec)['target_width_mm']
    proposals = [('current', original)]
    layout = spec['diagram'].get('layout', {})
    movable = relayout or (layout.get('type') != 'manual' and spec['recipe'] != 'scientific-schematic')
    complex_graph = len(spec['diagram']['nodes']) > 4 or bool(spec['diagram'].get('groups'))
    if movable:
        directions = ['down', 'right'] if layout.get('direction', 'right') == 'right' else ['right', 'down']
        for direction in directions[:2 if complex_graph else 1]:
            candidate = copy.deepcopy(spec)
            candidate['diagram']['layout'].update(type='auto', direction=direction, measure=True)
            candidate['diagram']['layout']['target_width_mm'] = profile_for(spec)['target_width_mm']
            for node in candidate['diagram']['nodes']:
                node.pop('position', None)
            proposals.append((direction, candidate))
    entries = []; best = None; baseline = None
    for candidate_index, (name, proposal) in enumerate(proposals[:max_candidates]):
        candidate_dir = session / name
        # Preserve relative datasets/includes while excluding generated state.
        shutil.copytree(figure_dir, candidate_dir, ignore=shutil.ignore_patterns('.funfig', '.git', '*.pdf', '*.svg', '*.aux', '*.log'))
        path = candidate_dir / spec_path.name
        candidate_best = None
        for round_index in range(repair_limit + 1):
            if semantic_signature(proposal) != signature:
                raise ValueError('optimizer attempted a semantic change')
            write_json_atomic(path, proposal)
            try:
                build_spec(proposal, path); qa = inspect_spec(proposal, path)
            except (BuildError, QAError, ValueError) as error:
                entries.append({'candidate': name, 'round': round_index, 'error': str(error), 'accepted': False})
                break
            manifest = load_json(candidate_dir / '.funfig/manifest.json')
            geometry = load_json(candidate_dir / '.funfig/geometry.json')
            rank = score(qa)
            entry = {'candidate': name, 'round': round_index, 'score': list(rank),
                     'defects': qa['defects'], 'hashes': manifest['hashes'], 'semantic_signature': signature,
                     'preview': str((candidate_dir / '.funfig/preview.png').relative_to(figure_dir)),
                     'accepted': candidate_best is None or rank < candidate_best[0]}
            entries.append(entry)
            if baseline is None:
                baseline = rank
            if candidate_best is None or rank < candidate_best[0]:
                candidate_best = rank, copy.deepcopy(proposal)
                # Keep the exact best preview/source; later failed rounds are retained separately.
                archive = candidate_dir / '.funfig' / f'round-{round_index}'
                archive.mkdir()
                for source in (path, candidate_dir / manifest['artifacts']['tex'], candidate_dir / manifest['artifacts']['pdf'], candidate_dir / '.funfig/preview.png'):
                    shutil.copy2(source, archive / source.name)
            elif rank > candidate_best[0]:
                entry['rollback'] = 'candidate worsened; restore best proposal'
                proposal = copy.deepcopy(candidate_best[1])
                break
            if not any(rank) or round_index == repair_limit:
                break
            next_proposal, actions = repair(proposal, qa, geometry, manifest['layout']['resolved_diagram'],
                                            relayout=relayout, round_index=round_index)
            entry['actions'] = actions
            if not actions or next_proposal == proposal:
                break
            proposal = next_proposal
        if candidate_best and (best is None or candidate_best[0] < best[0]):
            best = (*candidate_best, name)
        if best and not any(best[0]) and (not complex_graph or candidate_index >= 1):
            break  # simple successful figures do not pay for unused alternatives
    report = {'version': '1.0', 'semantic_signature': signature, 'baseline_score': list(baseline) if baseline else None,
              'evaluations': entries, 'visual_review': 'pending', 'adopted': False}
    if best and (best[0] < baseline or (best[0] == baseline and not any(best[0]))):
        (session / 'previous.funfig.json').write_text(original_text, encoding='utf-8')
        try:
            write_json_atomic(spec_path, best[1])
            build_spec(best[1], spec_path); final = inspect_spec(best[1], spec_path)
            if score(final) > best[0]:
                raise ValueError('final rebuild worsened candidate checks')
            report.update(adopted=True, selected=best[2], final_score=list(score(final)),
                          final_hashes=load_json(figure_dir / '.funfig/manifest.json')['hashes'])
        except (BuildError, QAError, ValueError) as error:
            for name in original_artifacts:
                saved, target = backup / name, figure_dir / name
                if saved.is_file():
                    shutil.copy2(saved, target)
                elif target.is_file():
                    target.unlink()
            report['rollback'] = str(error)
    report['elapsed_seconds'] = round(time.monotonic() - started, 3)
    report['prescriptions'] = 'knowledge/layout-prescriptions.json'
    report['prescription_version'] = prescriptions['version']
    known_actions = {p['id'] for p in prescriptions['prescriptions']}
    if any(a['prescription'] not in known_actions for e in entries for a in e.get('actions', [])):
        raise ValueError('repair action is missing from the verified prescription registry')
    write_json_atomic(session / 'report.json', report)
    report['report'] = str(session / 'report.json')
    return report
