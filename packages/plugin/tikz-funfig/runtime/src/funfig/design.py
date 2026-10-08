"""Validate the optional, agent-authored design contract without new dependencies."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from .io import load_json
from .manifest import sha256_file
from .paths import SCHEMA_PATH
from .schema import load_and_validate


def _check(value: Any, rule: dict[str, Any], root: dict[str, Any], path: str) -> list[str]:
    # This intentionally supports only the vocabulary used by our design schema,
    # not arbitrary JSON Schema. Fail closed if the contract adds another keyword.
    supported = {
        "$schema", "$id", "title", "description", "$defs", "$ref", "type",
        "const", "enum", "required", "properties", "additionalProperties",
        "items", "minItems", "uniqueItems", "minLength", "pattern",
        "minimum", "maximum", "exclusiveMinimum", "contains", "if", "then", "allOf",
    }
    if set(rule) - supported:
        raise ValueError(f"unsupported design schema keywords: {sorted(set(rule) - supported)}")
    errors: list[str] = []
    if "$ref" in rule:
        ref = rule["$ref"]
        if not ref.startswith("#/$defs/"):
            raise ValueError(f"unsupported design schema reference: {ref}")
        errors.extend(_check(value, root["$defs"][ref.removeprefix("#/$defs/")], root, path))
    checks = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": type(value) in (int, float) and math.isfinite(value),
        "integer": type(value) is int,
    }
    if "type" in rule and not checks.get(rule["type"], False):
        return errors + [f"{path} must be {rule['type']}"]
    if "const" in rule and value != rule["const"]:
        errors.append(f"{path} must be {rule['const']!r}")
    if "enum" in rule and value not in rule["enum"]:
        errors.append(f"{path} must be one of {rule['enum']}")
    if isinstance(value, dict):
        properties = rule.get("properties", {})
        for name in rule.get("required", []):
            if name not in value:
                errors.append(f"{path}.{name} is required")
        for name, item in value.items():
            if name in properties:
                errors.extend(_check(item, properties[name], root, f"{path}.{name}"))
            elif rule.get("additionalProperties") is False:
                errors.append(f"{path}.{name} is not supported")
    if isinstance(value, list):
        if len(value) < rule.get("minItems", 0):
            errors.append(f"{path} needs at least {rule['minItems']} item(s)")
        if rule.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in value}) != len(value):
            errors.append(f"{path} must contain unique items")
        for index, item in enumerate(value):
            errors.extend(_check(item, rule.get("items", {}), root, f"{path}[{index}]"))
        if "contains" in rule and not any(not _check(item, rule["contains"], root, path) for item in value):
            errors.append(f"{path} must include {rule['contains']}")
    if isinstance(value, str):
        if len(value) < rule.get("minLength", 0) or ("pattern" in rule and not re.search(rule["pattern"], value)):
            errors.append(f"{path} is empty or has an invalid format")
    if type(value) in (int, float) and "exclusiveMinimum" in rule and value <= rule["exclusiveMinimum"]:
        errors.append(f"{path} must be greater than {rule['exclusiveMinimum']}")
    if type(value) in (int, float) and "minimum" in rule and value < rule["minimum"]:
        errors.append(f"{path} must be at least {rule['minimum']}")
    if type(value) in (int, float) and "maximum" in rule and value > rule["maximum"]:
        errors.append(f"{path} must be at most {rule['maximum']}")
    for item in rule.get("allOf", []):
        errors.extend(_check(value, item, root, path))
    if "if" in rule and not _check(value, rule["if"], root, path):
        errors.extend(_check(value, rule.get("then", {}), root, path))
    return errors


def validate_design(path: Path, *, delivery: bool = False) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"design file does not exist: {path}")
    design = load_json(path)
    schema = load_json(SCHEMA_PATH.with_name("figure-design.schema.json"))
    errors = _check(design, schema, schema, "design")
    if errors:
        raise ValueError("invalid figure design:\n- " + "\n- ".join(errors))
    directory = path.resolve().parent
    basename = design["delivery"]["basename"]
    formats = design["delivery"]["formats"]
    structured = design["render_mode"] == "structured"
    spec_path = directory / "figure.funfig.json"
    if structured and spec_path.is_file():
        spec, result = load_and_validate(spec_path)
        errors.extend(result.errors)
        if spec.get("id") != design["id"]:
            errors.append("design id differs from FigureSpec id")
        outputs = spec.get("outputs") or {}
        if outputs.get("basename", "figure") != basename:
            errors.append("design basename differs from FigureSpec outputs.basename")
        if set(outputs.get("formats", ["pdf"])) != set(formats):
            errors.append("design formats differ from FigureSpec outputs.formats")
    if delivery:
        if path.name != "figure.design.json":
            errors.append("delivery design filename must be figure.design.json")
        if design["content"]["unresolved"]:
            errors.append("unresolved content questions prevent final delivery")
        manifest_name = "manifest.json" if structured else "expert-manifest.json"
        required = [f"{basename}.tex", *[f"{basename}.{fmt}" for fmt in formats], f".funfig/{manifest_name}"]
        if structured:
            required.append("figure.funfig.json")
        for name in required:
            if not (directory / name).is_file():
                errors.append(f"missing delivery artifact: {name}")
        manifest_path = directory / ".funfig" / manifest_name
        if manifest_path.is_file():
            manifest = load_json(manifest_path)
            expected_modes = {"structured", "legacy-structured"} if structured else {"raw-expert"}
            if manifest.get("mode") not in expected_modes or manifest.get("status") != "built":
                errors.append("delivery manifest does not record a successful build in the selected mode")
            qa = manifest.get("qa") or {}
            if qa.get("status") != "passed" or qa.get("visual_review") != "passed" or not qa.get("machine_checks_passed"):
                errors.append("delivery requires passing machine checks and an actual recorded visual review")
            size = qa.get('size_check') or {}
            for key in ('target_width_mm', 'minimum_text_pt'):
                if size.get(key) is not None and abs(float(size[key]) - float(design['appearance'][key])) > .05:
                    errors.append(f'delivery {key} differs from the design; apply output profile and rebuild')
            artifacts = {"tex": f"{basename}.tex", "pdf": f"{basename}.pdf"}
            if structured:
                artifacts["spec"] = "figure.funfig.json"
                if "svg" in formats:
                    artifacts["svg"] = f"{basename}.svg"
            for kind, name in artifacts.items():
                artifact = directory / name
                if artifact.is_file() and (manifest.get("hashes") or {}).get(f"{kind}_sha256") != sha256_file(artifact):
                    errors.append(f"stale or missing build hash for {name}; rebuild and review the current figure")
    if errors:
        raise ValueError("invalid figure design/delivery:\n- " + "\n- ".join(errors))
    return design
