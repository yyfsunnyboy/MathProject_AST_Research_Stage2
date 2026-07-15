from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree


OFFICIAL_BASE = Path(r"G:\我的雲端硬碟\科展 AI\AST_exp_result_official")
OUTPUT_DIR = Path("artifacts/fail_to_fail_forensics")

MANUAL_COLUMNS = [
    "root_cause",
    "failure_layer",
    "eligibility",
    "why_fail_to_fail",
    "recommended_action",
]

OBJECTIVE_COLUMNS = [
    "raw_failure_stage",
    "healed_failure_stage",
    "raw_error_type",
    "healed_error_type",
    "healer_triggered",
    "rules_triggered",
    "code_changed",
    "rollback",
]

FORENSIC_INPUT_COLUMNS = [
    "case_id",
    "dataset",
    "task_id",
    "sample_idx",
    "model",
    "raw_pass",
    "healed_pass",
    "raw_error",
    "healed_error",
    "raw_path",
    "healed_path",
    "normalized_diff_path",
    "pairing_status",
    *OBJECTIVE_COLUMNS,
]

OUTPUT_COLUMNS = [
    "case_id",
    "dataset",
    "task_id",
    "sample_idx",
    "model",
    "raw_pass",
    "raw_error",
    "healed_pass",
    "healed_error",
    "raw_path",
    "raw_eval_ready_path",
    "healed_path",
    "healed_eval_ready_path",
    "generation_log",
    "trace",
    "healer_triggered",
    "rules_triggered",
    "rollback",
    "sha256",
    "code_changed",
    "ast_changed",
    "normalized_diff_path",
    "ast_diff_path",
    "pairing_status",
    "missing_artifacts",
    *MANUAL_COLUMNS,
]


CELL_CONFIGS = [
    {
        "cell": "Gemini x HumanEval",
        "dataset": "humaneval",
        "model_label": "gemini",
        "root": "outputs_nothink_gemini_humaneval_164",
        "excel": r"results\results\gemini_humaneval\exp1_pass_at_1_humaneval.xlsx",
        "generation_log": "generation_log_humaneval.csv",
    },
    {
        "cell": "Gemini x MBPP",
        "dataset": "mbpp",
        "model_label": "gemini",
        "root": "outputs_nothink_gemini_mbpp",
        "excel": r"results\results\gemini_mbpp\exp1_pass_at_1_mbpp.xlsx",
        "generation_log": "generation_log_mbpp.csv",
    },
    {
        "cell": "Qwen8B x HumanEval",
        "dataset": "humaneval",
        "model_label": "qwen8b",
        "root": "qwen8b_nothink_humaneval_164",
        "excel": r"results\results\qwen8b_humaneval\exp1_pass_at_1_humaneval.xlsx",
        "generation_log": "generation_log_humaneval.csv",
    },
    {
        "cell": "Qwen8B x MBPP",
        "dataset": "mbpp",
        "model_label": "qwen8b",
        "root": "qwen8b_nothink_mbpp_378",
        "excel": r"results\results\qwen8b_mbpp\exp1_pass_at_1_mbpp.xlsx",
        "generation_log": "generation_log_mbpp.csv",
    },
]


ALIASES = {
    "task_id": ("task_id", "task", "problem_id"),
    "model": ("model", "model_name"),
    "strategy": ("strategy", "ablation", "variant"),
    "sample_idx": ("sample_idx", "sample", "sample_id", "idx"),
    "passed": ("passed", "pass", "success"),
    "error_type": ("error_type", "error", "status"),
    "error_msg": ("error_msg", "error_message", "message"),
    "eval_ready_path": ("eval_ready_path", "path", "file_path"),
    "eval_ready_sha256": ("eval_ready_sha256", "sha256"),
    "source_path": ("source_path", "raw_path"),
    "healer_trace": ("healer_trace", "trace"),
}


@dataclass(frozen=True)
class PairKey:
    dataset: str
    model: str
    task_id: str
    sample_idx: int


def normalize_header(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def resolve_columns(headers: Iterable[Any], aliases: dict[str, tuple[str, ...]] = ALIASES) -> dict[str, str]:
    normalized = {normalize_header(header): str(header) for header in headers if header is not None}
    resolved: dict[str, str] = {}
    for logical, candidates in aliases.items():
        for candidate in candidates:
            if candidate in normalized:
                resolved[logical] = normalized[candidate]
                break
    return resolved


def normalize_task_id(task_id: Any) -> str:
    text = str(task_id or "").strip().replace("\\", "/")
    text = re.sub(r"__s\d+\.py$", "", text)
    text = re.sub(r"\.py$", "", text)
    text = text.replace("HumanEval_", "HumanEval/").replace("Mbpp_", "Mbpp/")
    text = re.sub(r"/+", "/", text)
    if text.lower().startswith("humaneval/"):
        return "HumanEval/" + text.split("/", 1)[1]
    if text.lower().startswith("mbpp/"):
        return "Mbpp/" + text.split("/", 1)[1]
    return text


def task_file_stem(task_id: Any, sample_idx: Any) -> str:
    return normalize_task_id(task_id).replace("/", "_") + f"__s{normalize_sample_idx(sample_idx)}.py"


def normalize_sample_idx(value: Any) -> int:
    if value in (None, ""):
        return 0
    if isinstance(value, float):
        return int(value)
    match = re.search(r"\d+", str(value))
    if not match:
        return 0
    return int(match.group(0))


def normalize_model(value: Any) -> str:
    text = str(value or "").strip().lower().replace("/", "_").replace(":", "-")
    text = re.sub(r"[^a-z0-9._-]+", "_", text)
    text = text.replace("google_gemini", "google_gemini")
    text = text.replace("qwen3-8b", "qwen3-8b")
    return text


def parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "pass", "passed"}:
        return True
    if text in {"false", "0", "no", "n", "fail", "failed"}:
        return False
    return None


def read_table(path: Path) -> tuple[list[dict[str, Any]], list[str], str]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            return list(reader), list(reader.fieldnames or []), "csv"
    if suffix == ".xlsx":
        return read_xlsx_first_sheet(path)
    raise ValueError(f"Unsupported table type: {path}")


def read_xlsx_first_sheet(path: Path) -> tuple[list[dict[str, Any]], list[str], str]:
    with zipfile.ZipFile(path) as archive:
        shared = _read_shared_strings(archive)
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        first_sheet = workbook.find(".//x:sheets/x:sheet", ns)
        if first_sheet is None:
            return [], [], "xlsx"
        rel_id = first_sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        rels = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = None
        for rel in rels:
            if rel.attrib.get("Id") == rel_id:
                target = rel.attrib["Target"]
                break
        if target is None:
            return [], [], "xlsx"
        sheet_path = target.lstrip("/")
        if not sheet_path.startswith("xl/"):
            sheet_path = "xl/" + sheet_path
        rows = _read_sheet_rows(archive, sheet_path, shared)
    if not rows:
        return [], [], "xlsx"
    headers = [str(value) if value is not None else "" for value in rows[0]]
    records = []
    for row in rows[1:]:
        padded = row + [None] * (len(headers) - len(row))
        records.append(dict(zip(headers, padded)))
    return records, headers, "xlsx"


def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    strings = []
    for item in root.findall("x:si", ns):
        strings.append("".join(node.text or "" for node in item.findall(".//x:t", ns)))
    return strings


def _read_sheet_rows(archive: zipfile.ZipFile, sheet_path: str, shared: list[str]) -> list[list[Any]]:
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    root = ElementTree.fromstring(archive.read(sheet_path))
    rows: list[list[Any]] = []
    for row in root.findall(".//x:sheetData/x:row", ns):
        values: list[Any] = []
        for cell in row.findall("x:c", ns):
            ref = cell.attrib.get("r", "")
            col_idx = _column_index(ref)
            while len(values) < col_idx:
                values.append(None)
            values.append(_cell_value(cell, shared))
        rows.append(values)
    return rows


def _column_index(ref: str) -> int:
    letters = re.sub(r"[^A-Z]", "", ref.upper())
    value = 0
    for letter in letters:
        value = value * 26 + ord(letter) - ord("A") + 1
    return max(value - 1, 0)


def _cell_value(cell: ElementTree.Element, shared: list[str]) -> Any:
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    cell_type = cell.attrib.get("t")
    value = cell.find("x:v", ns)
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//x:t", ns))
    if value is None:
        return None
    text = value.text or ""
    if cell_type == "s":
        return shared[int(text)]
    if cell_type == "b":
        return text == "1"
    try:
        number = float(text)
    except ValueError:
        return text
    return int(number) if number.is_integer() else number


def row_key(row: dict[str, Any], columns: dict[str, str], dataset: str) -> PairKey:
    return PairKey(
        dataset=dataset,
        model=normalize_model(row.get(columns["model"])),
        task_id=normalize_task_id(row.get(columns["task_id"])),
        sample_idx=normalize_sample_idx(row.get(columns["sample_idx"])),
    )


def index_rows(rows: list[dict[str, Any]], columns: dict[str, str], dataset: str) -> dict[tuple[PairKey, str], list[dict[str, Any]]]:
    index: dict[tuple[PairKey, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not all(name in columns for name in ("task_id", "model", "strategy", "sample_idx")):
            continue
        strategy = str(row.get(columns["strategy"]) or "").strip()
        index[(row_key(row, columns, dataset), strategy)].append(row)
    return index


def select_fail_to_fail(index: dict[tuple[PairKey, str], list[dict[str, Any]]], columns: dict[str, str]) -> list[tuple[PairKey, list[dict[str, Any]], list[dict[str, Any]]]]:
    keys = sorted({key for key, strategy in index if strategy in {"Ab2g", "Ab3"}}, key=lambda k: (k.dataset, k.model, k.task_id, k.sample_idx))
    selected = []
    for key in keys:
        raw_rows = index.get((key, "Ab2g"), [])
        healed_rows = index.get((key, "Ab3"), [])
        if len(raw_rows) == 1 and len(healed_rows) == 1:
            raw_pass = parse_bool(raw_rows[0].get(columns["passed"]))
            healed_pass = parse_bool(healed_rows[0].get(columns["passed"]))
            if raw_pass is False and healed_pass is False:
                selected.append((key, raw_rows, healed_rows))
        elif raw_rows or healed_rows:
            raw_failed = any(parse_bool(row.get(columns["passed"])) is False for row in raw_rows)
            healed_failed = any(parse_bool(row.get(columns["passed"])) is False for row in healed_rows)
            if raw_failed and healed_failed:
                selected.append((key, raw_rows, healed_rows))
    return selected


def build_artifact_index(root: Path, strategy: str | None = None) -> dict[tuple[str, str, str, int], list[Path]]:
    index: dict[tuple[str, str, str, int], list[Path]] = defaultdict(list)
    pattern = re.compile(r"^(HumanEval|Mbpp)_(\d+)__s(\d+)\.py$", re.IGNORECASE)
    for path in root.rglob("*.py") if root.exists() else []:
        match = pattern.match(path.name)
        if not match:
            continue
        if strategy is not None and path.parent.name != strategy:
            continue
        dataset = "humaneval" if match.group(1).lower() == "humaneval" else "mbpp"
        task_id = f"{'HumanEval' if dataset == 'humaneval' else 'Mbpp'}/{match.group(2)}"
        model = normalize_model(path.parent.parent.name if len(path.parts) >= 3 else "")
        index[(dataset, model, task_id, int(match.group(3)))].append(path)
    return index


def find_artifact(index: dict[tuple[str, str, str, int], list[Path]], key: PairKey) -> tuple[str, Path | None]:
    hits = index.get((key.dataset, key.model, key.task_id, key.sample_idx), [])
    if len(hits) == 1:
        return "complete", hits[0]
    if len(hits) > 1:
        return "ambiguous", None
    return "missing", None


def find_expected_artifact(root: Path, section: str, strategy: str, key: PairKey) -> tuple[str, Path | None]:
    path = root / section / key.dataset / key.model / strategy / task_file_stem(key.task_id, key.sample_idx)
    return ("complete", path) if path.exists() else ("missing", path)


def path_from_row(row: dict[str, Any] | None, columns: dict[str, str], base_dir: Path) -> Path | None:
    if not row or "eval_ready_path" not in columns:
        return None
    value = row.get(columns["eval_ready_path"])
    if not value:
        return None
    path = Path(str(value))
    candidates = [path]
    if not path.is_absolute():
        candidates.append(base_dir / path)
        parts = path.parts
        if len(parts) > 1:
            candidates.append(base_dir / Path(*parts[1:]))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return base_dir / path if not path.is_absolute() else path


def sha256_path(path: Path | None) -> str:
    if not path or not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: Path | None) -> str | None:
    if not path or not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def normalize_code(code: str | None) -> str | None:
    if code is None:
        return None
    return "\n".join(line.rstrip() for line in code.replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip() + "\n"


def ast_signature(code: str | None) -> tuple[str, str | None]:
    if code is None:
        return "", "missing"
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return "", f"SyntaxError: {exc.msg}"
    return ast.dump(tree, annotate_fields=True, include_attributes=False), None


def write_diff(path: Path, before: str | None, after: str | None, title: str) -> str:
    import difflib

    if before is None or after is None:
        return ""
    lines = list(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"{title}.raw",
            tofile=f"{title}.healed",
        )
    )
    if not lines:
        return ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")
    return str(path)


def parse_trace(trace: str) -> tuple[bool, str, str]:
    if not trace:
        return False, "", ""
    try:
        parsed = json.loads(trace)
    except json.JSONDecodeError:
        return True, "unparsed_trace", ""
    rules = []
    rollback = ""
    for entry in parsed if isinstance(parsed, list) else []:
        layer = str(entry.get("layer", ""))
        changed = bool(entry.get("changed"))
        n_fixes = int(entry.get("n_fixes") or 0)
        if changed or n_fixes:
            rules.append(layer)
        if "rollback" in layer.lower():
            rollback = "true"
    return bool(rules), ";".join(rules), rollback


def split_official_error(error: Any) -> tuple[str, str]:
    """Split joined official ``error_type: error_msg`` into type and message."""
    text = str(error or "").strip()
    if not text:
        return "", ""
    if ": " in text:
        error_type, message = text.split(": ", 1)
        return error_type.strip(), message.strip()
    return text, ""


def classify_failure_stage(error: Any) -> str:
    """Derive an objective failure stage from the official joined error string.

    Mapping is mechanical only (no root-cause / eligibility / semantic judgment):
    - worker_error -> worker
    - fail with base/plus flags -> base | plus | base+plus
    - other nonempty error_type -> other
    """
    error_type, message = split_official_error(error)
    if not error_type:
        return ""
    if error_type == "worker_error":
        return "worker"
    if error_type == "fail":
        base_fail = "base=fail" in message
        base_pass = "base=pass" in message
        plus_fail = "plus=fail" in message
        plus_pass = "plus=pass" in message
        if base_fail and plus_fail:
            return "base+plus"
        if base_pass and plus_fail:
            return "plus"
        if base_fail and plus_pass:
            return "base"
        return "eval"
    return "other"


def objective_fields(record: dict[str, Any]) -> dict[str, str]:
    """Fill only objective forensic fields from an extracted pairing record."""
    rollback = str(record.get("rollback") or "").strip().lower()
    if rollback not in {"true", "false"}:
        rollback = "true" if rollback in {"1", "yes", "y"} else "false"
    return {
        "raw_failure_stage": classify_failure_stage(record.get("raw_error")),
        "healed_failure_stage": classify_failure_stage(record.get("healed_error")),
        "raw_error_type": split_official_error(record.get("raw_error"))[0],
        "healed_error_type": split_official_error(record.get("healed_error"))[0],
        "healer_triggered": str(record.get("healer_triggered") or "").strip().lower(),
        "rules_triggered": str(record.get("rules_triggered") or ""),
        "code_changed": str(record.get("code_changed") or "").strip().lower(),
        "rollback": rollback,
    }


def load_pairing_manifest(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def select_qwen8b_complete_cases(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = [
        record
        for record in records
        if str(record.get("case_id", "")).startswith("qwen8b_")
        and str(record.get("pairing_status", "")).strip().lower() == "complete"
        and str(record.get("model", "")).strip().lower() in {"qwen3-8b", "qwen8b"}
    ]
    return sorted(selected, key=lambda row: (row.get("dataset", ""), row.get("task_id", ""), row.get("sample_idx", 0)))


def build_qwen8b_forensic_input_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in select_qwen8b_complete_cases(records):
        row = {
            "case_id": record.get("case_id", ""),
            "dataset": record.get("dataset", ""),
            "task_id": record.get("task_id", ""),
            "sample_idx": record.get("sample_idx", ""),
            "model": record.get("model", ""),
            "raw_pass": record.get("raw_pass", ""),
            "healed_pass": record.get("healed_pass", ""),
            "raw_error": record.get("raw_error", ""),
            "healed_error": record.get("healed_error", ""),
            "raw_path": record.get("raw_path", ""),
            "healed_path": record.get("healed_path", ""),
            "normalized_diff_path": record.get("normalized_diff_path", ""),
            "pairing_status": record.get("pairing_status", ""),
        }
        row.update(objective_fields(record))
        rows.append(row)
    return rows


def write_qwen8b_forensic_input(
    manifest_path: Path = OUTPUT_DIR / "pairing_manifest.jsonl",
    output_path: Path = OUTPUT_DIR / "qwen8b_forensic_input.csv",
) -> dict[str, Any]:
    records = load_pairing_manifest(manifest_path)
    rows = build_qwen8b_forensic_input_rows(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output_path, rows, FORENSIC_INPUT_COLUMNS)
    humaneval = sum(1 for row in rows if row.get("dataset") == "humaneval")
    mbpp = sum(1 for row in rows if row.get("dataset") == "mbpp")
    return {
        "output_path": str(output_path),
        "total": len(rows),
        "humaneval": humaneval,
        "mbpp": mbpp,
    }


def build_generation_log_index(path: Path, dataset: str) -> tuple[dict[tuple[PairKey, str], list[dict[str, Any]]], list[str]]:
    if not path.exists():
        return {}, []
    rows, headers, _ = read_table(path)
    columns = resolve_columns(headers)
    if not all(name in columns for name in ("task_id", "model", "strategy", "sample_idx")):
        return {}, headers
    return index_rows(rows, columns, dataset), headers


def extract_cell(config: dict[str, str], base_dir: Path, output_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    root = base_dir / config["root"]
    excel_path = base_dir / config["excel"]
    rows, headers, source_type = read_table(excel_path)
    columns = resolve_columns(headers)
    required = {"task_id", "model", "strategy", "sample_idx", "passed"}
    missing_columns = sorted(required - set(columns))
    if missing_columns:
        raise ValueError(f"{excel_path} missing required columns after header detection: {missing_columns}")

    row_index = index_rows(rows, columns, config["dataset"])
    selected = select_fail_to_fail(row_index, columns)
    gen_index, gen_headers = build_generation_log_index(root / config["generation_log"], config["dataset"])
    records = []
    unpaired = []
    for key, raw_rows, healed_rows in selected:
        raw_row = raw_rows[0] if len(raw_rows) == 1 else None
        healed_row = healed_rows[0] if len(healed_rows) == 1 else None
        raw_art_status, raw_path = find_expected_artifact(root, "raw_outputs", "Ab2g", key)
        healed_art_status, healed_path = find_expected_artifact(root, "healed_outputs", "Ab3", key)
        raw_eval_status, raw_eval_path = find_expected_artifact(root, "eval_ready_outputs", "Ab2g", key)
        healed_eval_status, healed_eval_path = find_expected_artifact(root, "eval_ready_outputs", "Ab3", key)
        raw_eval_from_excel = path_from_row(raw_row, columns, base_dir)
        healed_eval_from_excel = path_from_row(healed_row, columns, base_dir)
        if raw_eval_path is None:
            raw_eval_path = raw_eval_from_excel if raw_eval_from_excel and raw_eval_from_excel.exists() else raw_eval_from_excel
            raw_eval_status = "complete" if raw_eval_path and raw_eval_path.exists() else raw_eval_status
        if healed_eval_path is None:
            healed_eval_path = healed_eval_from_excel if healed_eval_from_excel and healed_eval_from_excel.exists() else healed_eval_from_excel
            healed_eval_status = "complete" if healed_eval_path and healed_eval_path.exists() else healed_eval_status

        gen_rows = gen_index.get((key, "Ab2g"), [])
        gen_status = "complete" if len(gen_rows) == 1 else "missing" if not gen_rows else "ambiguous"
        gen_row = gen_rows[0] if len(gen_rows) == 1 else {}
        trace = str(gen_row.get("healer_trace", ""))
        healer_triggered, rules_triggered, rollback = parse_trace(trace)

        artifact_statuses = {
            "raw_output": raw_art_status,
            "raw_eval_ready": raw_eval_status,
            "healed_output": healed_art_status,
            "healed_eval_ready": healed_eval_status,
            "generation_log": gen_status,
            "excel_raw_row": "complete" if len(raw_rows) == 1 else "ambiguous",
            "excel_healed_row": "complete" if len(healed_rows) == 1 else "ambiguous",
        }
        missing = [name for name, status in artifact_statuses.items() if status != "complete"]
        if any(status == "ambiguous" for status in artifact_statuses.values()):
            pairing_status = "ambiguous"
        elif missing:
            pairing_status = "missing"
        else:
            pairing_status = "complete"

        raw_code = normalize_code(read_text(raw_path))
        healed_code = normalize_code(read_text(healed_path))
        raw_ast, raw_ast_error = ast_signature(raw_code)
        healed_ast, healed_ast_error = ast_signature(healed_code)
        code_changed = "" if raw_code is None or healed_code is None else str(raw_code != healed_code).lower()
        ast_changed = "" if raw_ast_error or healed_ast_error else str(raw_ast != healed_ast).lower()

        safe_case = f"{config['model_label']}_{config['dataset']}_{key.task_id.replace('/', '_')}__s{key.sample_idx}"
        norm_diff_path = write_diff(output_dir / "diffs" / f"{safe_case}.normalized.diff", raw_code, healed_code, safe_case)
        ast_diff_path = write_diff(output_dir / "diffs" / f"{safe_case}.ast.diff", raw_ast, healed_ast, safe_case)

        sha_payload = {
            "raw_output": sha256_path(raw_path),
            "raw_eval_ready": sha256_path(raw_eval_path),
            "healed_output": sha256_path(healed_path),
            "healed_eval_ready": sha256_path(healed_eval_path),
        }
        if raw_ast_error:
            missing.append(f"raw_ast_parse:{raw_ast_error}")
        if healed_ast_error:
            missing.append(f"healed_ast_parse:{healed_ast_error}")

        record = {
            "case_id": safe_case,
            "dataset": key.dataset,
            "task_id": key.task_id,
            "sample_idx": key.sample_idx,
            "model": raw_row.get(columns["model"]) if raw_row else key.model,
            "raw_pass": raw_row.get(columns["passed"]) if raw_row else "",
            "raw_error": _join_error(raw_row, columns),
            "healed_pass": healed_row.get(columns["passed"]) if healed_row else "",
            "healed_error": _join_error(healed_row, columns),
            "raw_path": str(raw_path or ""),
            "raw_eval_ready_path": str(raw_eval_path or ""),
            "healed_path": str(healed_path or ""),
            "healed_eval_ready_path": str(healed_eval_path or ""),
            "generation_log": str(root / config["generation_log"]) if gen_status == "complete" else "",
            "trace": trace,
            "healer_triggered": str(healer_triggered).lower(),
            "rules_triggered": rules_triggered,
            "rollback": rollback,
            "sha256": json.dumps(sha_payload, ensure_ascii=False, sort_keys=True),
            "code_changed": code_changed,
            "ast_changed": ast_changed,
            "normalized_diff_path": norm_diff_path,
            "ast_diff_path": ast_diff_path,
            "pairing_status": pairing_status,
            "missing_artifacts": ";".join(dict.fromkeys(missing)),
        }
        for column in MANUAL_COLUMNS:
            record[column] = ""
        records.append(record)
        if pairing_status != "complete":
            unpaired.append(record)

    schema = {
        "cell": config["cell"],
        "excel": str(excel_path),
        "excel_source_type": source_type,
        "excel_headers": headers,
        "excel_resolved_columns": columns,
        "generation_log": str(root / config["generation_log"]),
        "generation_log_headers": gen_headers,
        "root": str(root),
    }
    return records, schema, unpaired


def _join_error(row: dict[str, Any] | None, columns: dict[str, str]) -> str:
    if not row:
        return ""
    parts = []
    for logical in ("error_type", "error_msg"):
        column = columns.get(logical)
        value = row.get(column) if column else ""
        if value not in (None, ""):
            parts.append(str(value))
    return ": ".join(parts)


def write_outputs(records: list[dict[str, Any]], schemas: list[dict[str, Any]], unpaired: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_jsonl = output_dir / "pairing_manifest.jsonl"
    with manifest_jsonl.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    write_csv(output_dir / "pairing_manifest.csv", records, OUTPUT_COLUMNS)
    write_csv(output_dir / "unpaired_or_ambiguous_cases.csv", unpaired, OUTPUT_COLUMNS)
    census = build_census(records)
    write_csv(output_dir / "cell_census.csv", census, ["dataset", "model", "total", "complete", "missing", "ambiguous"])
    (output_dir / "schema_inventory.json").write_text(json.dumps(schemas, ensure_ascii=False, indent=2), encoding="utf-8")
    write_readme(output_dir / "README.md", records, census)
    return {"records": len(records), "census": census, "unpaired": len(unpaired)}


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_census(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for record in records:
        grouped[(record["dataset"], str(record["model"]))][record["pairing_status"]] += 1
        grouped[(record["dataset"], str(record["model"]))]["total"] += 1
    census = []
    for (dataset, model), counts in sorted(grouped.items()):
        census.append(
            {
                "dataset": dataset,
                "model": model,
                "total": counts["total"],
                "complete": counts["complete"],
                "missing": counts["missing"],
                "ambiguous": counts["ambiguous"],
            }
        )
    return census


def write_readme(path: Path, records: list[dict[str, Any]], census: list[dict[str, Any]]) -> None:
    lines = [
        "# Fail-to-Fail Forensics",
        "",
        "Extractor output for Ab2g fail -> Ab3 fail paired cases.",
        "",
        "Included strategies: raw Ab2g and healed/original Ab3 rows where both pass values are false.",
        "Pairing key: dataset + normalized model + normalized task_id + sample_idx.",
        "Missing or duplicate artifacts are marked as missing or ambiguous; the extractor does not infer replacements.",
        "",
        "## Census",
        "",
        "| dataset | model | total | complete | missing | ambiguous |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in census:
        lines.append(f"| {row['dataset']} | {row['model']} | {row['total']} | {row['complete']} | {row['missing']} | {row['ambiguous']} |")
    lines.extend(
        [
            "",
            "## Files",
            "",
            "- `pairing_manifest.jsonl` and `pairing_manifest.csv`: case-level manifest.",
            "- `cell_census.csv`: counts by dataset/model cell and pairing status.",
            "- `unpaired_or_ambiguous_cases.csv`: cases needing artifact follow-up.",
            "- `schema_inventory.json`: observed source headers and resolved logical columns.",
            "- `diffs/`: normalized text and AST-signature unified diffs when available.",
            "",
            f"Total cases: {len(records)}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(base_dir: Path = OFFICIAL_BASE, output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    all_records: list[dict[str, Any]] = []
    schemas = []
    unpaired: list[dict[str, Any]] = []
    for config in CELL_CONFIGS:
        print(f"extracting {config['cell']}...", flush=True)
        records, schema, cell_unpaired = extract_cell(config, base_dir, output_dir)
        print(f"  cases={len(records)} unpaired={len(cell_unpaired)}", flush=True)
        all_records.extend(records)
        schemas.append(schema)
        unpaired.extend(cell_unpaired)
    return write_outputs(all_records, schemas, unpaired, output_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract Ab2g fail -> Ab3 fail paired forensics cases.")
    parser.add_argument("--base-dir", type=Path, default=OFFICIAL_BASE)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument(
        "--build-qwen8b-forensic-input",
        action="store_true",
        help="Build objective-only Qwen8B forensic input CSV from pairing_manifest.jsonl without re-extracting.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="pairing_manifest.jsonl path for --build-qwen8b-forensic-input (default: <output-dir>/pairing_manifest.jsonl).",
    )
    parser.add_argument(
        "--forensic-input",
        type=Path,
        default=None,
        help="Output CSV path for --build-qwen8b-forensic-input (default: <output-dir>/qwen8b_forensic_input.csv).",
    )
    args = parser.parse_args(argv)
    if args.build_qwen8b_forensic_input:
        manifest = args.manifest or (args.output_dir / "pairing_manifest.jsonl")
        forensic_input = args.forensic_input or (args.output_dir / "qwen8b_forensic_input.csv")
        summary = write_qwen8b_forensic_input(manifest, forensic_input)
    else:
        summary = run(args.base_dir, args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
