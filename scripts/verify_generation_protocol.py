"""Verify generation_protocol_v1 and optionally record two synthetic probes.

This script never loads benchmark datasets and never retries an HTTP request.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Sequence

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.ollama_generation_runner import (  # noqa: E402
    OllamaGenerationError,
    _post_chat,
    load_generation_protocol,
    protocol_settings,
)

DEFAULT_PROTOCOL = REPO_ROOT / "configs/public_benchmark_generation_protocol_v1.json"
DEFAULT_BASE_URL = "http://127.0.0.1:11434"
SYNTHETIC_PROMPT = "Return exactly PROTOCOL_OK and no other text."
_THINK_TAG = re.compile(r"</?think>", re.IGNORECASE)


class ProtocolVerificationError(RuntimeError):
    pass


def _http_json(
    url: str, timeout_seconds: float, *, method: str = "GET", payload: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"} if body is not None else {},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except (OSError, TimeoutError, urllib.error.URLError) as exc:
        raise ProtocolVerificationError(f"{method} {url} failed: {exc}") from exc
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProtocolVerificationError(f"{method} {url} returned invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise ProtocolVerificationError(f"{method} {url} did not return an object")
    return parsed


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def inspect_environment(
    protocol: Dict[str, Any], base_url: str, timeout_seconds: float
) -> Dict[str, Any]:
    version = _http_json(base_url.rstrip("/") + "/api/version", timeout_seconds)
    if version.get("version") != protocol["ollama"]["version"]:
        raise ProtocolVerificationError("Ollama version differs from frozen protocol")
    tags = _http_json(base_url.rstrip("/") + "/api/tags", timeout_seconds)
    installed = {
        (entry.get("name") or entry.get("model")): entry
        for entry in tags.get("models", [])
        if isinstance(entry, dict)
    }

    result: Dict[str, Any] = {"ollama_version": version["version"], "models": {}}
    for role, expected in protocol["models"].items():
        entry = installed.get(expected["tag"])
        if entry is None:
            raise ProtocolVerificationError(f"required model {expected['tag']!r} is absent")
        details = entry.get("details") if isinstance(entry.get("details"), dict) else {}
        checks = {
            "digest": entry.get("digest"),
            "size_bytes": entry.get("size"),
            "modified_at": entry.get("modified_at"),
            "quantization": details.get("quantization_level"),
            "parameter_size": details.get("parameter_size"),
        }
        for field, actual in checks.items():
            if actual != expected[field]:
                raise ProtocolVerificationError(
                    f"{expected['tag']} {field} differs: {actual!r} != {expected[field]!r}"
                )
        show = _http_json(
            base_url.rstrip("/") + "/api/show",
            timeout_seconds,
            method="POST",
            payload={"model": expected["tag"]},
        )
        template = show.get("template")
        if not isinstance(template, str):
            raise ProtocolVerificationError(f"{expected['tag']} has no inspectable template")
        if _sha256_text(template) != expected["template_sha256"]:
            raise ProtocolVerificationError(f"{expected['tag']} template differs from protocol")
        if "/nothink" in template.lower():
            raise ProtocolVerificationError("/nothink string is forbidden by protocol")
        result["models"][role] = {
            "tag": expected["tag"],
            **checks,
            "template": template,
            "template_sha256": expected["template_sha256"],
            "template_contains_nothink": False,
        }
    return result


def run_probe(
    protocol: Dict[str, Any], role: str, base_url: str, timeout_seconds: float
) -> Dict[str, Any]:
    settings = protocol_settings(protocol, model_role=role, seed=protocol["seeds"][0])
    response = _post_chat(SYNTHETIC_PROMPT, base_url, timeout_seconds, settings)
    transport = response.pop("_ollama_response_metadata", None)
    if not isinstance(transport, dict):
        raise ProtocolVerificationError("probe transport metadata was not preserved")
    request_payload = transport.get("request_payload")
    raw_body = transport.get("raw_body")
    if not isinstance(request_payload, dict) or request_payload.get("think") is not False:
        raise ProtocolVerificationError("probe request did not record think=false")
    if not isinstance(raw_body, str) or not raw_body:
        raise ProtocolVerificationError("probe raw response body was not preserved")

    message = response.get("message") if isinstance(response.get("message"), dict) else {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ProtocolVerificationError("probe response content is empty")
    if message.get("thinking") not in (None, "") or response.get("thinking") not in (None, ""):
        raise ProtocolVerificationError("probe response contains thinking content")
    if _THINK_TAG.search(content):
        raise ProtocolVerificationError("probe response contains a think tag")

    required_metadata = {
        "model",
        "created_at",
        "done",
        "done_reason",
        "total_duration",
        "load_duration",
        "prompt_eval_count",
        "prompt_eval_duration",
        "eval_count",
        "eval_duration",
    }
    missing = sorted(required_metadata - response.keys())
    if missing:
        raise ProtocolVerificationError(f"probe response metadata missing: {missing}")
    return {
        "model_role": role,
        "model_tag": settings.model,
        "request": request_payload,
        "response": response,
        "raw_response_body": raw_body,
        "http_status": transport.get("http_status"),
        "api_endpoint": transport.get("api_endpoint"),
        "no_thinking_verified": True,
        "response_contains_think_tag": False,
        "metadata_complete": True,
    }


def verify_protocol(
    protocol_path: pathlib.Path,
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout_seconds: float = 180.0,
    probe_manifest_path: Optional[pathlib.Path] = None,
) -> Dict[str, Any]:
    protocol = load_generation_protocol(protocol_path)
    environment = inspect_environment(protocol, base_url, timeout_seconds)
    result: Dict[str, Any] = {
        "protocol_version": protocol["protocol_version"],
        "protocol_sha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        "environment": environment,
        "protocol_valid": True,
    }
    if probe_manifest_path is not None:
        probes = [
            run_probe(protocol, "primary_development_model", base_url, timeout_seconds),
            run_probe(protocol, "frozen_transfer_model", base_url, timeout_seconds),
        ]
        manifest = {
            "manifest_version": "synthetic_probe_manifest_v1",
            "protocol_version": protocol["protocol_version"],
            "protocol_sha256": result["protocol_sha256"],
            "synthetic_prompt": SYNTHETIC_PROMPT,
            "synthetic_prompt_sha256": _sha256_text(SYNTHETIC_PROMPT),
            "public_benchmark_task_content_used": False,
            "probe_count": 2,
            "probes": probes,
        }
        probe_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        probe_manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        result["probe_manifest"] = str(probe_manifest_path)
        result["no_thinking_verified_models"] = [probe["model_tag"] for probe in probes]
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=pathlib.Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    parser.add_argument("--probe-manifest", type=pathlib.Path)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = verify_protocol(
            args.protocol,
            base_url=args.base_url,
            timeout_seconds=args.timeout_seconds,
            probe_manifest_path=args.probe_manifest,
        )
    except (ProtocolVerificationError, OllamaGenerationError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
