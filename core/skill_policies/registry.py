# -*- coding: utf-8 -*-
"""Live Show skill policy registry.

目標：讓技能策略以「每個 family 一個 policy 檔」方式擴充，
新技能僅需新增 policy 檔並填入 skill_ids 即可接上。
"""

from __future__ import annotations

import importlib
import pkgutil
import difflib
from typing import Dict, List

_DEFAULT_POLICY: Dict[str, object] = {
    "policy_id": "default",
    "family": "generic",
    "skill_ids": [],
    "apply_fraction_eval_patch": False,
    "enable_fraction_display": False,
    "force_fraction_answer": False,
    "fallback_fraction_style": False,
    "aliases": [],
}

_POLICY_TABLE: Dict[str, Dict[str, object]] = {}
_ALIAS_TABLE: Dict[str, str] = {}


def _normalize_policy(raw: Dict[str, object]) -> Dict[str, object]:
    out = dict(_DEFAULT_POLICY)
    out.update(raw or {})
    out["skill_ids"] = list(out.get("skill_ids") or [])
    out["aliases"] = list(out.get("aliases") or [])
    return out


def _load_policies() -> Dict[str, Dict[str, object]]:
    table: Dict[str, Dict[str, object]] = {}
    package_name = __name__.rsplit(".", 1)[0]
    package = importlib.import_module(package_name)

    for module_info in pkgutil.iter_modules(package.__path__):
        mod_name = module_info.name
        if mod_name.startswith("_") or mod_name in {"registry"}:
            continue

        module = importlib.import_module(f"{package_name}.{mod_name}")
        raw_policies = getattr(module, "POLICIES", [])
        for raw in raw_policies:
            policy = _normalize_policy(raw)
            for skill_id in policy.get("skill_ids", []):
                if skill_id:
                    table[str(skill_id)] = policy

    return table


def _build_alias_table(policy_table: Dict[str, Dict[str, object]]) -> Dict[str, str]:
    aliases: Dict[str, str] = {}
    for skill_id, policy in policy_table.items():
        if not skill_id:
            continue
        canonical = str(skill_id)
        aliases[canonical.lower()] = canonical
        for alias in policy.get("aliases", []) or []:
            alias_key = str(alias or "").strip().lower()
            if alias_key:
                aliases[alias_key] = canonical
    return aliases


def refresh_registry() -> None:
    global _POLICY_TABLE, _ALIAS_TABLE
    _POLICY_TABLE = _load_policies()
    _ALIAS_TABLE = _build_alias_table(_POLICY_TABLE)


def get_skill_policy(skill_id: str | None) -> Dict[str, object]:
    if not _POLICY_TABLE:
        refresh_registry()
    if not skill_id:
        return dict(_DEFAULT_POLICY)
    return dict(_POLICY_TABLE.get(str(skill_id), _DEFAULT_POLICY))


def normalize_skill_id(raw_skill_id: str | None, available_skills: List[str] | None = None) -> str:
    if not _POLICY_TABLE:
        refresh_registry()

    raw = str(raw_skill_id or "").strip()
    if not raw:
        return "Unknown"

    available = list(available_skills or [])
    available_set = set(available)
    raw_lower = raw.lower()

    if raw in available_set:
        return raw

    canonical = _ALIAS_TABLE.get(raw_lower)
    if canonical:
        if not available or canonical in available_set:
            return canonical

    candidates = available if available else list_registered_skill_ids()
    if not candidates:
        return canonical or "Unknown"

    substring_match = next((cand for cand in candidates if raw_lower in cand.lower()), None)
    if substring_match:
        return substring_match

    fuzzy = difflib.get_close_matches(raw, candidates, n=1, cutoff=0.3)
    if fuzzy:
        return fuzzy[0]

    return canonical or "Unknown"


def get_policy_bool(skill_id: str | None, key: str, default: bool = False) -> bool:
    policy = get_skill_policy(skill_id)
    val = policy.get(key, default)
    return bool(val)


def list_registered_skill_ids() -> List[str]:
    if not _POLICY_TABLE:
        refresh_registry()
    return sorted(_POLICY_TABLE.keys())
