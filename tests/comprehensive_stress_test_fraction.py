"""Phase-1 fraction arithmetic stress test.

Scope:
- simplify / equivalent fraction / preserve-value
- compare fractions and mixed numbers
- add/sub/mul/div with fractions, mixed numbers, and decimals
- reciprocal
- listed textbook word problems without image dependency
"""

from __future__ import annotations

import html
import math
import os
import re
import sys
from typing import Any


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.fraction_domain_functions import FractionFunctionHelper
from tests.fraction_phase1_cases import PHASE1_CASES


LOOPS = int(os.environ.get("FRACTION_STRESS_LOOPS", "5"))
LIMIT = int(os.environ.get("FRACTION_STRESS_LIMIT", "0"))
SKILL_ID = "jh_數學1上_FourArithmeticOperationsOfNumbers"


def _status(ok: bool, issues: list[str]) -> str:
    return "PASS" if ok else "FAIL: " + " ; ".join(issues[:6])


def _validate_result(body: dict[str, Any], *, strict_quality: bool) -> list[str]:
    issues: list[str] = []
    q = str(body.get("question_text") or body.get("problem") or "").strip()
    a = str(body.get("correct_answer") or body.get("answer") or "").strip()
    if not q:
        issues.append("empty question")
    if not a:
        issues.append("empty answer")
    if q == "Error":
        issues.append("question is error")
    if a == "Error":
        issues.append("answer is error")
    if re.search(r"\d+/\d+|\d+\s+\d+/\d+|[*/]", q) and "$" not in q:
        issues.append("question missing latex math wrapper")
    if strict_quality:
        issues.extend(_validate_render_quality(q))
    return issues


def _number_tokens(text: str) -> list[str]:
    return re.findall(
        r"-?\d+\s*\\frac\{\d+\}\{\d+\}|-?\\frac\{\d+\}\{\d+\}|-?\d+\s+\d+/\d+|-?\d+/\d+|-?\d+\.\d+|-?\d+",
        str(text or ""),
    )


def _validate_variation(source: str, candidate: str) -> list[str]:
    issues: list[str] = []
    src_tokens = _number_tokens(source)
    cand_tokens = _number_tokens(candidate)
    if src_tokens and len(src_tokens) != len(cand_tokens):
        issues.append(f"numeric token count changed: {len(src_tokens)}->{len(cand_tokens)}")
    elif src_tokens:
        unchanged = [idx for idx, (a, b) in enumerate(zip(src_tokens, cand_tokens), start=1) if a == b]
        if unchanged:
            issues.append(f"unchanged numeric token positions: {unchanged[:8]}")
    return issues


def _validate_render_quality(text: str) -> list[str]:
    issues: list[str] = []
    for num, den in re.findall(r"\\frac\{(\d+)\}\{(\d+)\}", str(text or "")):
        if math.gcd(int(num), int(den)) != 1:
            issues.append(f"unreduced fraction: {num}/{den}")
            break
    for num, den in re.findall(r"-?\d+\\frac\{(\d+)\}\{(\d+)\}", str(text or "")):
        if math.gcd(int(num), int(den)) != 1:
            issues.append(f"unreduced mixed fraction: {num}/{den}")
            break
    return issues


def _run_case(helper: FractionFunctionHelper, question: str) -> dict[str, Any]:
    config = helper.build_config(question)
    first = helper.generate_from_config(config)
    first_issues = _validate_result(first, strict_quality=False)

    next_out: dict[str, Any] = {}
    next_issues: list[str] = []
    for loop in range(LOOPS):
        runtime_cfg = helper.build_runtime_config(config, level=loop + 2)
        nxt = helper.generate_from_config(runtime_cfg)
        if not next_out:
            next_out = nxt
        errs = _validate_result(nxt, strict_quality=True) + _validate_variation(
            str(first.get("question_text") or config.get("source_text") or question),
            str(runtime_cfg.get("source_text") or ""),
        )
        if errs:
            next_issues.append(f"loop {loop + 1}: " + "; ".join(errs))
            break

    return {
        "family": config.get("family", ""),
        "first": first,
        "next": next_out,
        "first_issues": first_issues,
        "next_issues": next_issues,
        "status": _status(not (first_issues or next_issues), first_issues + next_issues),
    }


def main() -> None:
    helper = FractionFunctionHelper()
    cases = PHASE1_CASES[:LIMIT] if LIMIT > 0 else PHASE1_CASES

    rows: list[str] = []
    failed = 0

    for idx, question in enumerate(cases, start=1):
        try:
            result = _run_case(helper, question)
        except Exception as exc:
            result = {
                "family": "crash",
                "first": {},
                "next": {},
                "first_issues": [str(exc)],
                "next_issues": [],
                "status": f"CRASH: {exc}",
            }
            failed += 1
        else:
            if result["first_issues"] or result["next_issues"]:
                failed += 1

        rows.append(
            "<tr>"
            f"<td>{idx}</td>"
            f"<td>{html.escape(question)}</td>"
            f"<td>{html.escape(str(result['first'].get('question_text') or ''))}</td>"
            f"<td>{html.escape(_status(not result['first_issues'], result['first_issues']))}</td>"
            f"<td>{html.escape(str(result['next'].get('question_text') or ''))}</td>"
            f"<td>{html.escape(_status(not result['next_issues'], result['next_issues']))}</td>"
            f"<td>{html.escape(str(result['first'].get('correct_answer') or ''))}</td>"
            f"<td>{html.escape(str(result['family']))}</td>"
            f"<td>{html.escape(result['status'])}</td>"
            "</tr>"
        )

    passed = len(cases) - failed
    report_path = os.path.join(os.path.dirname(__file__), "stress_test_report_fraction.html")
    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write(
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<title>Fraction Phase-1 Stress Report</title>"
            "<script>MathJax = { tex: { inlineMath: [['$', '$']] } };</script>"
            "<script src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js'></script>"
            "<style>body{font-family:Arial,sans-serif;margin:20px;}table{border-collapse:collapse;width:100%;}"
            "th,td{border:1px solid #ddd;padding:10px;vertical-align:top;text-align:left;}th{background:#f2f2f2;}tr:nth-child(even){background:#fafafa;}</style>"
            "</head><body>"
            f"<h2>Fraction Phase-1 Stress Report</h2><p>Total: {len(cases)} | Pass: {passed} | Fail: {failed}</p>"
            f"<p>Skill: {html.escape(SKILL_ID)} | Loops: {LOOPS}</p>"
            "<table><tr><th>#</th><th>Source</th><th>First Question</th><th>First Status</th><th>Next Question</th><th>Next Status</th><th>Answer</th><th>Family</th><th>Overall</th></tr>"
            + "".join(rows)
            + "</table></body></html>"
        )
    print(f"[HTML] report saved to {report_path}")


if __name__ == "__main__":
    main()
