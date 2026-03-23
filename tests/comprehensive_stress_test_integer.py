"""Phase-1 integer arithmetic stress test.

Scope:
- pure integer arithmetic
- absolute value / brackets
- distributive-factor style calculations
- arithmetic word problems mapped to net change or scoring

Excluded from phase 1:
- number-line geometry
- image-driven puzzles
- ghost-leg / diagram-heavy questions
"""

from __future__ import annotations

import html
import os
import sys
from typing import Any


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.integer_domain_functions import IntegerFunctionHelper
from tests.integer_phase1_cases import PHASE1_CASES


LOOPS = int(os.environ.get("INTEGER_STRESS_LOOPS", "5"))
LIMIT = int(os.environ.get("INTEGER_STRESS_LIMIT", "0"))
SKILL_ID = "jh_數學1上_FourArithmeticOperationsOfIntegers"


def _status(ok: bool, issues: list[str]) -> str:
    return "PASS" if ok else "FAIL: " + " ; ".join(issues[:6])


def _validate_result(body: dict[str, Any]) -> list[str]:
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
    return issues


def _run_case(helper: IntegerFunctionHelper, question: str) -> dict[str, Any]:
    config = helper.build_config(question)
    first = helper.generate_from_config(config)
    first_issues = _validate_result(first)

    next_out: dict[str, Any] = {}
    next_issues: list[str] = []
    for loop in range(LOOPS):
        nxt = helper.generate_from_config(config)
        if not next_out:
            next_out = nxt
        errs = _validate_result(nxt)
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
    helper = IntegerFunctionHelper()
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
    report_path = os.path.join(os.path.dirname(__file__), "stress_test_report_integer.html")
    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write(
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<title>Integer Phase-1 Stress Report</title>"
            "<script>MathJax = { tex: { inlineMath: [['$', '$']] } };</script>"
            "<script src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js'></script>"
            "<style>body{font-family:Arial,sans-serif;margin:20px;}table{border-collapse:collapse;width:100%;}"
            "th,td{border:1px solid #ddd;padding:10px;vertical-align:top;text-align:left;}th{background:#f2f2f2;}tr:nth-child(even){background:#fafafa;}</style>"
            "</head><body>"
            f"<h2>整數四則運算 Phase 1 壓力測試</h2><p>Total: {len(cases)} | Pass: {passed} | Fail: {failed}</p>"
            f"<p>Skill: {html.escape(SKILL_ID)} | Loops: {LOOPS}</p>"
            "<table><tr><th>#</th><th>課本題目</th><th>首題生成</th><th>首題狀態</th><th>下一題</th><th>下一題狀態</th><th>答案</th><th>Family</th><th>整體狀態</th></tr>"
            + "".join(rows)
            + "</table></body></html>"
        )
    print(f"[HTML] report saved to {report_path}")


if __name__ == "__main__":
    main()
