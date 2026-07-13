"""
Frozen Math task schema and output contract (Phase 3.5).

Defines immutable MathTask / MathOutputContract models, strict parsing,
and deterministic serialization. Does not execute code, call models, or
implement mathematical equivalence checking.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

MATH_ENTRY_POINT = "solve"

INPUT_CONTRACT_KIND_NO_ARGUMENTS = "no_arguments"

ALLOWED_ANSWER_TYPES: frozenset[str] = frozenset(
    {
        "number",
        "rational",
        "symbolic_expression",
        "coordinate_pair",
        "multi_field_answer",
    }
)

ALLOWED_REPRESENTATION_POLICIES: frozenset[str] = frozenset(
    {"semantic_only", "exact_answer_type"}
)

ALLOWED_SYMBOLIC_REPRESENTATION_SUBTYPES: frozenset[str] = frozenset(
    {"radical", "generic"}
)

ALLOWED_CURRICULUM_LEVELS: frozenset[str] = frozenset(
    {"grade_7", "grade_8", "grade_9", "senior_high", "cross_grade"}
)

ALLOWED_EVIDENCE_ROLES: frozenset[str] = frozenset(
    {
        "development",
        "validation",
        "deployment_representative",
        "cross_grade_challenge",
        "holdout",
    }
)

EVIDENCE_ROLE_DEPLOYMENT_REPRESENTATIVE = "deployment_representative"
EVIDENCE_ROLE_CROSS_GRADE_CHALLENGE = "cross_grade_challenge"
EVIDENCE_ROLE_HOLDOUT = "holdout"
CURRICULUM_LEVEL_CROSS_GRADE = "cross_grade"

_MATH_TASK_REQUIRED_KEYS: frozenset[str] = frozenset(
    {
        "task_id",
        "source",
        "source_year",
        "source_exam",
        "source_question_number",
        "domain",
        "subdomain",
        "curriculum_level",
        "evidence_role",
        "problem_text",
        "entry_point",
        "input_contract",
        "output_contract",
        "reference_semantic",
        "reference_display",
        "metadata",
    }
)

_MATH_TASK_OPTIONAL_KEYS: frozenset[str] = frozenset(
    {"choices", "units", "subquestions", "visual_spec"}
)

_MATH_TASK_ALLOWED_TOP_LEVEL_KEYS: frozenset[str] = (
    _MATH_TASK_REQUIRED_KEYS | _MATH_TASK_OPTIONAL_KEYS
)

_OUTPUT_CONTRACT_REQUIRED_KEYS: frozenset[str] = frozenset(
    {
        "answer_type",
        "representation_subtype",
        "python_return_type",
        "representation_policy",
        "validator_type",
        "allowed_tolerance",
        "symbolic_variables",
        "answer_fields",
    }
)


class MathTaskSchemaError(ValueError):
    """Raised when a Math task record violates the frozen schema."""


@dataclass(frozen=True)
class MathOutputContract:
    answer_type: str
    representation_subtype: Optional[str]
    python_return_type: str
    representation_policy: str
    validator_type: str
    allowed_tolerance: Optional[float]
    symbolic_variables: Tuple[str, ...]
    answer_fields: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.answer_type not in ALLOWED_ANSWER_TYPES:
            raise MathTaskSchemaError(
                f"output_contract.answer_type must be one of "
                f"{sorted(ALLOWED_ANSWER_TYPES)}, got {self.answer_type!r}"
            )
        if self.representation_policy not in ALLOWED_REPRESENTATION_POLICIES:
            raise MathTaskSchemaError(
                f"output_contract.representation_policy must be one of "
                f"{sorted(ALLOWED_REPRESENTATION_POLICIES)}, "
                f"got {self.representation_policy!r}"
            )
        if not isinstance(self.validator_type, str) or not self.validator_type.strip():
            raise MathTaskSchemaError(
                "output_contract.validator_type must be a non-empty string"
            )
        if self.allowed_tolerance is not None:
            if not isinstance(self.allowed_tolerance, (int, float)) or isinstance(
                self.allowed_tolerance, bool
            ):
                raise MathTaskSchemaError(
                    "output_contract.allowed_tolerance must be null or a number"
                )
            if float(self.allowed_tolerance) < 0:
                raise MathTaskSchemaError(
                    "output_contract.allowed_tolerance must be null or non-negative"
                )
        if not isinstance(self.symbolic_variables, tuple):
            raise MathTaskSchemaError(
                "output_contract.symbolic_variables must be a tuple[str, ...]"
            )
        if len(self.symbolic_variables) != len(set(self.symbolic_variables)):
            raise MathTaskSchemaError(
                "output_contract.symbolic_variables must not contain duplicates"
            )
        for name in self.symbolic_variables:
            if not isinstance(name, str) or not name.strip():
                raise MathTaskSchemaError(
                    "output_contract.symbolic_variables entries must be non-empty strings"
                )
        if not isinstance(self.answer_fields, tuple):
            raise MathTaskSchemaError(
                "output_contract.answer_fields must be a tuple[str, ...]"
            )
        if len(self.answer_fields) != len(set(self.answer_fields)):
            raise MathTaskSchemaError(
                "output_contract.answer_fields must not contain duplicates"
            )
        for name in self.answer_fields:
            if not isinstance(name, str) or not name.strip():
                raise MathTaskSchemaError(
                    "output_contract.answer_fields entries must be non-empty strings"
                )

        if self.representation_subtype is not None:
            if not isinstance(self.representation_subtype, str) or not (
                self.representation_subtype.strip()
            ):
                raise MathTaskSchemaError(
                    "output_contract.representation_subtype must be null or a non-empty string"
                )

        self._validate_answer_type_constraints()

    def _validate_answer_type_constraints(self) -> None:
        return_type = self.python_return_type
        if not isinstance(return_type, str) or not return_type.strip():
            raise MathTaskSchemaError(
                "output_contract.python_return_type must be a non-empty string"
            )

        if self.answer_type == "number":
            if return_type not in ("int", "float"):
                raise MathTaskSchemaError(
                    "output_contract for answer_type='number' requires "
                    "python_return_type 'int' or 'float'"
                )
            if self.answer_fields:
                raise MathTaskSchemaError(
                    "output_contract.answer_fields must be empty for answer_type='number'"
                )
            return

        if self.answer_type == "rational":
            if return_type != "Fraction":
                raise MathTaskSchemaError(
                    "output_contract for answer_type='rational' requires "
                    "python_return_type 'Fraction'"
                )
            if self.answer_fields:
                raise MathTaskSchemaError(
                    "output_contract.answer_fields must be empty for answer_type='rational'"
                )
            return

        if self.answer_type == "symbolic_expression":
            if return_type != "str":
                raise MathTaskSchemaError(
                    "output_contract for answer_type='symbolic_expression' requires "
                    "python_return_type 'str'"
                )
            if self.representation_subtype is not None and (
                self.representation_subtype not in ALLOWED_SYMBOLIC_REPRESENTATION_SUBTYPES
            ):
                raise MathTaskSchemaError(
                    "output_contract.representation_subtype for "
                    "answer_type='symbolic_expression' must be one of "
                    f"{sorted(ALLOWED_SYMBOLIC_REPRESENTATION_SUBTYPES)}"
                )
            if self.answer_fields:
                raise MathTaskSchemaError(
                    "output_contract.answer_fields must be empty for "
                    "answer_type='symbolic_expression'"
                )
            return

        if self.answer_type == "coordinate_pair":
            if return_type != "tuple":
                raise MathTaskSchemaError(
                    "output_contract for answer_type='coordinate_pair' requires "
                    "python_return_type 'tuple'"
                )
            if self.answer_fields:
                raise MathTaskSchemaError(
                    "output_contract.answer_fields must be empty for "
                    "answer_type='coordinate_pair'"
                )
            return

        if self.answer_type == "multi_field_answer":
            if return_type != "dict":
                raise MathTaskSchemaError(
                    "output_contract for answer_type='multi_field_answer' requires "
                    "python_return_type 'dict'"
                )
            if not self.answer_fields:
                raise MathTaskSchemaError(
                    "output_contract.answer_fields must be non-empty for "
                    "answer_type='multi_field_answer'"
                )


@dataclass(frozen=True)
class MathTask:
    task_id: str
    source: str
    source_year: int
    source_exam: str
    source_question_number: Union[int, str]
    domain: str
    subdomain: str
    curriculum_level: str
    evidence_role: str
    problem_text: str
    entry_point: str
    input_contract: Dict[str, Any]
    output_contract: MathOutputContract
    reference_semantic: Any
    reference_display: Optional[str]
    metadata: Dict[str, Any]
    choices: Optional[Tuple[str, ...]] = None
    units: Optional[str] = None
    subquestions: Optional[Tuple[Dict[str, Any], ...]] = None
    visual_spec: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise MathTaskSchemaError("task_id must be a non-empty string")
        for field_name in (
            "source",
            "source_exam",
            "domain",
            "subdomain",
            "problem_text",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise MathTaskSchemaError(f"{field_name} must be a non-empty string")
        if isinstance(self.source_year, bool) or not isinstance(self.source_year, int):
            raise MathTaskSchemaError("source_year must be an integer")
        if not isinstance(self.source_question_number, (int, str)) or isinstance(
            self.source_question_number, bool
        ):
            raise MathTaskSchemaError(
                "source_question_number must be an integer or string"
            )
        if self.entry_point != MATH_ENTRY_POINT:
            raise MathTaskSchemaError(
                f"entry_point must be {MATH_ENTRY_POINT!r}, got {self.entry_point!r}"
            )
        if not isinstance(self.input_contract, dict):
            raise MathTaskSchemaError("input_contract must be an object")
        if self.input_contract != {"kind": INPUT_CONTRACT_KIND_NO_ARGUMENTS}:
            raise MathTaskSchemaError(
                "input_contract must be exactly {'kind': 'no_arguments'}"
            )
        if not isinstance(self.metadata, dict):
            raise MathTaskSchemaError("metadata must be an object")
        if self.reference_display is not None and not isinstance(
            self.reference_display, str
        ):
            raise MathTaskSchemaError("reference_display must be null or a string")
        if self.choices is not None:
            if not isinstance(self.choices, tuple) or not all(
                isinstance(item, str) for item in self.choices
            ):
                raise MathTaskSchemaError("choices must be null or a tuple[str, ...]")
        if self.units is not None and not isinstance(self.units, str):
            raise MathTaskSchemaError("units must be null or a string")
        if self.subquestions is not None:
            if not isinstance(self.subquestions, tuple) or not all(
                isinstance(item, dict) for item in self.subquestions
            ):
                raise MathTaskSchemaError(
                    "subquestions must be null or a tuple[dict[str, Any], ...]"
                )
        if self.visual_spec is not None and not isinstance(self.visual_spec, dict):
            raise MathTaskSchemaError("visual_spec must be null or an object")

        if not isinstance(self.curriculum_level, str) or not self.curriculum_level.strip():
            raise MathTaskSchemaError("curriculum_level must be a non-empty string")
        if self.curriculum_level not in ALLOWED_CURRICULUM_LEVELS:
            raise MathTaskSchemaError(
                f"curriculum_level must be one of {sorted(ALLOWED_CURRICULUM_LEVELS)}, "
                f"got {self.curriculum_level!r}"
            )

        if not isinstance(self.evidence_role, str) or not self.evidence_role.strip():
            raise MathTaskSchemaError("evidence_role must be a non-empty string")
        if self.evidence_role not in ALLOWED_EVIDENCE_ROLES:
            raise MathTaskSchemaError(
                f"evidence_role must be one of {sorted(ALLOWED_EVIDENCE_ROLES)}, "
                f"got {self.evidence_role!r}"
            )

        self._validate_evidence_scope()

    def _validate_evidence_scope(self) -> None:
        if self.metadata.get("synthetic_fixture") is True and (
            self.evidence_role == EVIDENCE_ROLE_HOLDOUT
        ):
            raise MathTaskSchemaError(
                "metadata.synthetic_fixture=true disallows evidence_role='holdout'"
            )
        if (
            self.evidence_role == EVIDENCE_ROLE_DEPLOYMENT_REPRESENTATIVE
            and self.curriculum_level == CURRICULUM_LEVEL_CROSS_GRADE
        ):
            raise MathTaskSchemaError(
                "evidence_role='deployment_representative' disallows "
                "curriculum_level='cross_grade'"
            )


def _string_tuple(
    value: Any,
    *,
    field_name: str,
    context: str,
) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        items = list(value)
    elif isinstance(value, list):
        items = value
    else:
        raise MathTaskSchemaError(
            f"{context}{field_name} must be a list or tuple of strings"
        )
    normalized: List[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            raise MathTaskSchemaError(
                f"{context}{field_name}[{index}] must be a non-empty string"
            )
        normalized.append(item)
    return tuple(normalized)


def _parse_output_contract(
    data: Any,
    *,
    context: str,
) -> MathOutputContract:
    if not isinstance(data, dict):
        raise MathTaskSchemaError(f"{context}output_contract must be an object")

    unknown = set(data) - _OUTPUT_CONTRACT_REQUIRED_KEYS
    if unknown:
        raise MathTaskSchemaError(
            f"{context}output_contract contains unknown fields: {sorted(unknown)}"
        )
    missing = _OUTPUT_CONTRACT_REQUIRED_KEYS - set(data)
    if missing:
        raise MathTaskSchemaError(
            f"{context}output_contract missing required fields: {sorted(missing)}"
        )

    representation_subtype = data["representation_subtype"]
    if representation_subtype is not None and not isinstance(
        representation_subtype, str
    ):
        raise MathTaskSchemaError(
            f"{context}output_contract.representation_subtype must be null or a string"
        )

    allowed_tolerance = data["allowed_tolerance"]
    if allowed_tolerance is not None:
        if isinstance(allowed_tolerance, bool) or not isinstance(
            allowed_tolerance, (int, float)
        ):
            raise MathTaskSchemaError(
                f"{context}output_contract.allowed_tolerance must be null or a number"
            )
        allowed_tolerance = float(allowed_tolerance)

    return MathOutputContract(
        answer_type=data["answer_type"],
        representation_subtype=representation_subtype,
        python_return_type=data["python_return_type"],
        representation_policy=data["representation_policy"],
        validator_type=data["validator_type"],
        allowed_tolerance=allowed_tolerance,
        symbolic_variables=_string_tuple(
            data["symbolic_variables"],
            field_name="symbolic_variables",
            context=context,
        ),
        answer_fields=_string_tuple(
            data["answer_fields"],
            field_name="answer_fields",
            context=context,
        ),
    )


def parse_math_task(data: Mapping[str, Any]) -> MathTask:
    """Parse one Math task record; fails closed on unknown top-level fields."""
    if not isinstance(data, Mapping):
        raise MathTaskSchemaError("math task record must be a mapping")

    unknown = set(data) - _MATH_TASK_ALLOWED_TOP_LEVEL_KEYS
    if unknown:
        raise MathTaskSchemaError(
            f"unknown top-level fields: {sorted(unknown)}"
        )

    missing = _MATH_TASK_REQUIRED_KEYS - set(data)
    if missing:
        raise MathTaskSchemaError(
            f"missing required fields: {sorted(missing)}"
        )

    task_id = data.get("task_id")
    context = f"task_id={task_id!r}: " if isinstance(task_id, str) and task_id else ""

    if "output_contract" not in data:
        raise MathTaskSchemaError(f"{context}missing required field 'output_contract'")

    output_contract = _parse_output_contract(
        data["output_contract"],
        context=context,
    )

    choices_raw = data.get("choices")
    choices: Optional[Tuple[str, ...]]
    if choices_raw is None:
        choices = None
    else:
        choices = _string_tuple(choices_raw, field_name="choices", context=context)

    subquestions_raw = data.get("subquestions")
    subquestions: Optional[Tuple[Dict[str, Any], ...]]
    if subquestions_raw is None:
        subquestions = None
    else:
        if isinstance(subquestions_raw, tuple):
            items = list(subquestions_raw)
        elif isinstance(subquestions_raw, list):
            items = subquestions_raw
        else:
            raise MathTaskSchemaError(f"{context}subquestions must be a list or tuple")
        if not all(isinstance(item, dict) for item in items):
            raise MathTaskSchemaError(
                f"{context}subquestions entries must be objects"
            )
        subquestions = tuple(items)

    visual_spec = data.get("visual_spec")
    if visual_spec is not None and not isinstance(visual_spec, dict):
        raise MathTaskSchemaError(f"{context}visual_spec must be null or an object")

    units = data.get("units")
    if units is not None and not isinstance(units, str):
        raise MathTaskSchemaError(f"{context}units must be null or a string")

    metadata = data["metadata"]
    if not isinstance(metadata, dict):
        raise MathTaskSchemaError(f"{context}metadata must be an object")

    input_contract = data["input_contract"]
    if not isinstance(input_contract, dict):
        raise MathTaskSchemaError(f"{context}input_contract must be an object")

    return MathTask(
        task_id=data["task_id"],
        source=data["source"],
        source_year=data["source_year"],
        source_exam=data["source_exam"],
        source_question_number=data["source_question_number"],
        domain=data["domain"],
        subdomain=data["subdomain"],
        curriculum_level=data["curriculum_level"],
        evidence_role=data["evidence_role"],
        problem_text=data["problem_text"],
        entry_point=data["entry_point"],
        input_contract=dict(input_contract),
        output_contract=output_contract,
        reference_semantic=data["reference_semantic"],
        reference_display=data["reference_display"],
        metadata=dict(metadata),
        choices=choices,
        units=units,
        subquestions=subquestions,
        visual_spec=visual_spec,
    )


def _output_contract_to_dict(contract: MathOutputContract) -> Dict[str, Any]:
    return {
        "answer_type": contract.answer_type,
        "representation_subtype": contract.representation_subtype,
        "python_return_type": contract.python_return_type,
        "representation_policy": contract.representation_policy,
        "validator_type": contract.validator_type,
        "allowed_tolerance": contract.allowed_tolerance,
        "symbolic_variables": list(contract.symbolic_variables),
        "answer_fields": list(contract.answer_fields),
    }


def math_task_to_dict(task: MathTask) -> Dict[str, Any]:
    """Serialize a MathTask to a deterministic JSON-compatible dict."""
    payload: Dict[str, Any] = {
        "task_id": task.task_id,
        "source": task.source,
        "source_year": task.source_year,
        "source_exam": task.source_exam,
        "source_question_number": task.source_question_number,
        "domain": task.domain,
        "subdomain": task.subdomain,
        "curriculum_level": task.curriculum_level,
        "evidence_role": task.evidence_role,
        "problem_text": task.problem_text,
        "entry_point": task.entry_point,
        "input_contract": {"kind": INPUT_CONTRACT_KIND_NO_ARGUMENTS},
        "output_contract": _output_contract_to_dict(task.output_contract),
        "reference_semantic": task.reference_semantic,
        "reference_display": task.reference_display,
        "metadata": dict(task.metadata),
    }
    if task.choices is not None:
        payload["choices"] = list(task.choices)
    if task.units is not None:
        payload["units"] = task.units
    if task.subquestions is not None:
        payload["subquestions"] = [dict(item) for item in task.subquestions]
    if task.visual_spec is not None:
        payload["visual_spec"] = dict(task.visual_spec)
    return payload


def load_math_tasks_jsonl(path: Union[str, pathlib.Path]) -> List[MathTask]:
    """Load Math tasks from a read-only JSONL file."""
    jsonl_path = pathlib.Path(path)
    if not jsonl_path.is_file():
        raise MathTaskSchemaError(f"math task file not found: {jsonl_path}")

    tasks: List[MathTask] = []
    seen_task_ids: set[str] = set()

    for line_no, line in enumerate(
        jsonl_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise MathTaskSchemaError(
                f"{jsonl_path}: line {line_no}: invalid JSON: {exc}"
            ) from exc
        if not isinstance(obj, dict):
            raise MathTaskSchemaError(
                f"{jsonl_path}: line {line_no}: expected a JSON object"
            )
        try:
            task = parse_math_task(obj)
        except MathTaskSchemaError as exc:
            task_id = obj.get("task_id")
            if isinstance(task_id, str) and task_id.strip():
                raise MathTaskSchemaError(
                    f"{jsonl_path}: line {line_no}: task_id={task_id!r}: {exc}"
                ) from exc
            raise MathTaskSchemaError(
                f"{jsonl_path}: line {line_no}: {exc}"
            ) from exc

        if task.task_id in seen_task_ids:
            raise MathTaskSchemaError(
                f"{jsonl_path}: line {line_no}: duplicate task_id {task.task_id!r}"
            )
        seen_task_ids.add(task.task_id)
        tasks.append(task)

    return tasks
