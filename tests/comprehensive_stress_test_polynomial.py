"""Polynomial live_show regression stress test.

This regression is intentionally textbook-shaped:
1. Every textbook example is flattened into a single case.
2. Each case runs through /api/generate_live.
3. Each generated file is looped through /api/run_generated_code several times.
4. We fail the case if any loop produces empty question/answer, non-LaTeX question,
   or an execution error.
"""

from __future__ import annotations

import html
import os
import re
import sys
import time
from typing import Any

import requests


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.polynomial_domain_functions import PolynomialFunctionHelper

BASE_URL = os.environ.get("MATHPROJECT_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
GENERATE_URL = f"{BASE_URL}/api/generate_live"
RUN_URL = f"{BASE_URL}/api/run_generated_code"
TIMEOUT = int(os.environ.get("POLY_STRESS_TIMEOUT", "300"))
LOOPS = int(os.environ.get("POLY_STRESS_LOOPS", "5"))
LIMIT = int(os.environ.get("POLY_STRESS_LIMIT", "0"))

SKILL_ID = "jh_數學2上_FourArithmeticOperationsOfPolynomial"

TEST_CASES: list[dict[str, str]] = [
    {"family": "poly_add_sub_flat", "text": "計算 $(4x+5+2x^{2})+(1+2x+x^{2})$。"},
    {"family": "poly_add_sub_flat", "text": "計算 $(5x+3x^{2}+1)+(x^{2}+7x+5)$。"},
    {"family": "poly_add_sub_flat", "text": "計算 $(3x-5+5x^{2})+(6+2x^{2}-3x)$。"},
    {"family": "poly_add_sub_flat", "text": "計算 $(2x^{2}-5)+(-x^{2}+2x+1)$。"},
    {"family": "poly_add_sub_flat", "text": "計算 $(5x-x^{2})+(2x^{2}-3)$。"},
    {"family": "poly_add_sub_flat", "text": "計算 $(4x-x^{3}+8)+(-2x^{3}+3x^{2})$。"},
    {"family": "poly_add_sub_flat", "text": "計算 $(x^{2}+5x+1)-(2-3x^{2})$。"},
    {"family": "poly_add_sub_flat", "text": "計算 $(-x+1+2x^{2})-(5x^{2}+4x-3)$。"},
    {"family": "poly_add_sub_flat", "text": "計算 $(7-x^{2})-(2x-4x^{3}+6)$。"},
    {"family": "poly_add_sub_nested", "text": "計算 $(-3x^{2}-7+x)-[(1-2x^{2})-(2x+6)]$。"},
    {"family": "poly_add_sub_unknown", "text": "若 $A+(-4x^{2}+1+5x)=x^{3}+5-2x$，則多項式 $A=$？"},
    {"family": "poly_add_sub_flat", "text": "計算 $(3x^{2}+6x-9)-(-3x^{2}+4x)+(-2x+3)$。"},
    {"family": "poly_add_sub_unknown", "text": "若 $B-(6x^{3}-2+x^{2})=5x^{2}+11-3x$，則多項式 $B=$？"},
    {"family": "poly_mul_monomial", "text": "計算 $(-7x)\\times 5x$。"},
    {"family": "poly_mul_monomial", "text": "計算 $(-5x)^{2}$。"},
    {"family": "poly_mul_monomial", "text": "計算 $\\frac{1}{2}x\\times\\left(-\\frac{4}{5}\\right)x^{2}$。"},
    {"family": "poly_mul_monomial", "text": "計算 $3x(x+2)$。"},
    {"family": "poly_mul_monomial", "text": "計算 $(4x-3)(-2x)$。"},
    {"family": "poly_mul_monomial", "text": "計算 $-2x(5x+2)$。"},
    {"family": "poly_mul_monomial", "text": "計算 $(-2x+3)(-3x)$。"},
    {"family": "poly_mul_poly", "text": "計算 $(x^{2}-x+1)(x+2)$。"},
    {"family": "poly_mul_poly", "text": "計算 $(x+2)(-2x+1)$。"},
    {"family": "poly_mul_poly", "text": "計算 $(x-1)(x^{2}+x+1)$。"},
    {"family": "poly_mul_poly", "text": "計算 $(5x^{2}-4)(-2x+3)$。"},
    {"family": "poly_mul_poly", "text": "計算 $(3x^{2}+2)(-4x-1)$。"},
    {"family": "poly_mul_special_identity", "text": "利用乘法公式計算 $(3x+4)^{2}$。"},
    {"family": "poly_mul_special_identity", "text": "利用乘法公式計算 $(2x-5)^{2}$。"},
    {"family": "poly_mul_special_identity", "text": "利用乘法公式計算 $(4x+7)(4x-7)$。"},
    {"family": "poly_mul_special_identity", "text": "利用乘法公式計算 $(4x+3)^{2}$。"},
    {"family": "poly_mul_special_identity", "text": "利用乘法公式計算 $(5-2x)^{2}$。"},
    {"family": "poly_mul_special_identity", "text": "利用乘法公式計算 $(2y+9)(2y-9)$。"},
    {"family": "poly_div_monomial_eval", "text": "計算 $(15x^{2})\\div(3x)$。"},
    {"family": "poly_div_monomial_eval", "text": "計算 $(-4x^{3})\\div(2x)$。"},
    {"family": "poly_div_monomial_eval", "text": "計算 $(14x^{2})\\div(-4x^{2})$。"},
    {"family": "poly_div_monomial_qr", "text": "求 $(4x^{2}+8x-2)$ 除以 $4x$ 的商式與餘式。"},
    {"family": "poly_div_monomial_qr", "text": "求 $(5x^{2}+10x)$ 除以 $5x$ 的商式與餘式。"},
    {"family": "poly_div_monomial_qr", "text": "求 $(-6x^{2}+4x-5)$ 除以 $2x$ 的商式與餘式。"},
    {"family": "poly_div_poly_qr", "text": "求 $(2x^{2}-x-6)$ 除以 $(x-2)$ 的商式與餘式。"},
    {"family": "poly_div_poly_qr", "text": "求 $(3x^{2}+5)$ 除以 $(x-4)$ 的商式與餘式。"},
    {"family": "poly_div_poly_qr", "text": "求 $(2x^{2}-x-6)$ 除以 $(2x+3)$ 的商式與餘式。"},
    {"family": "poly_div_poly_qr", "text": "求 $(3x^{2}-1)$ 除以 $(x-1)$ 的商式與餘式。"},
    {"family": "poly_div_poly_qr", "text": "求 $(3x^{2}-8x+2)$ 除以 $(3x^{2}-9x+1)$ 的商式與餘式。"},
    {"family": "poly_div_poly_qr", "text": "求 $(2x^{2}+4x-5)$ 除以 $(3x^{2}-4x)$ 的商式與餘式。"},
    {"family": "poly_div_poly_qr", "text": "求 $(4x^{2}-2x+1)$ 除以 $(3x^{2}+2x+1)$ 的商式與餘式。"},
    {"family": "poly_div_poly_qr", "text": "求 $(9x^{2}+14x)$ 除以 $(5+x^{2}-4x)$ 的商式與餘式。"},
    {"family": "poly_div_reverse", "text": "如果一個多項式 A 除以 $x+2$ 的商式為 $3x^{2}+1$，餘式為 $4$，試求此多項式 A。"},
    {"family": "poly_div_reverse", "text": "如果一個多項式 B 除以 $3x^{2}-1$ 的商式為 $2x+5$，餘式為 $x+2$，試求此多項式 B。"},
    {"family": "poly_div_reverse", "text": "已知 $2x^{2}+7x+1$ 除以另一個多項式 A 後，得到商式為 $2x+1$，餘式為 $-2$，試求此多項式 A。"},
    {"family": "poly_div_reverse", "text": "已知 $8x^{2}+2x-15$ 除以另一個多項式 B 後，得到商式為 $4x+7$，餘式為 $6$，試求此多項式 B。"},
    {"family": "poly_mixed_simplify", "text": "計算 $(x+2)^{2}+(2x+1)$。"},
    {"family": "poly_mixed_simplify", "text": "計算 $5(2x+1)^{2}-3(x+1)(x+3)$。"},
    {"family": "poly_mixed_simplify", "text": "計算 $1-5(x-2)^{2}+2(x-1)$。"},
    {"family": "poly_mixed_simplify", "text": "計算 $(x+1)(x+2)-(x+3)(x+4)$。"},
    {"family": "poly_geom_region_composite", "text": "右圖中，大長方形的長為 $2x+5$、寬為 $x+4$，小長方形的長為 $2x+1$、寬為 $x-1$。試以 x 的多項式表示橘色部分的周長與面積。"},
    {"family": "poly_geom_formula_direct", "text": "右圖是大象造型的梯形溜滑梯，若溜滑梯的上底為 $x-3$、下底為 $3x+5$、面積為 $2x^{2}+5x+2$，試以 x 的多項式表示此溜滑梯的高。"},
]

_LOCAL_CLIENT = None
_PFH = PolynomialFunctionHelper()


def _get_local_client():
    global _LOCAL_CLIENT
    if _LOCAL_CLIENT is None:
        from app import app

        _LOCAL_CLIENT = app.test_client()
    return _LOCAL_CLIENT


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.post(url, json=payload, timeout=(2, TIMEOUT))
        response.raise_for_status()
        return response.json()
    except Exception:
        client = _get_local_client()
        if url.endswith("/api/generate_live"):
            resp = client.post("/api/generate_live", json=payload)
        elif url.endswith("/api/run_generated_code"):
            resp = client.post("/api/run_generated_code", json=payload)
        else:
            raise
        body = resp.get_json()
        if resp.status_code >= 400:
            raise RuntimeError(body.get("error", f"http {resp.status_code}"))
        return body


def call_generate(text: str) -> dict[str, Any]:
    payload = {
        "prompt": text,
        "skill_id": SKILL_ID,
        "ablation_mode": False,
        "count": 1,
        "json_spec": {"ocr_text": text},
    }
    body = _post_json(GENERATE_URL, payload)
    if not body.get("success"):
        raise RuntimeError(body.get("error", "generate success=false"))
    return body


def call_next(file_path: str, source_text: str) -> dict[str, Any]:
    payload = {
        "file_path": file_path,
        "skill_id": SKILL_ID,
        "ocr_text": source_text,
        "json_spec": {"ocr_text": source_text},
    }
    body = _post_json(RUN_URL, payload)
    if not body.get("success"):
        raise RuntimeError(body.get("error", "run_generated_code success=false"))
    return body


def validate_result(body: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    q = str(body.get("problem") or body.get("question_text") or "").strip()
    a = str(body.get("answer") or body.get("correct_answer") or "").strip()
    if not q:
        errors.append("empty question")
    if "$" not in q or q.count("$") < 2:
        errors.append("question not latex-wrapped")
    if "x^2" in q or "y^2" in q:
        errors.append("plain exponent in question")
    if q == "Error" or "Traceback" in q:
        errors.append("question is error")
    if not a:
        errors.append("empty answer")
    if a == "Error":
        errors.append("answer is error")
    return errors


def classify_question_style(question_text: str) -> list[str]:
    issues: list[str] = []
    q = str(question_text or "")
    if "+-" in q or "-+" in q:
        issues.append("awkward sign sequence")
    if "--" in q:
        issues.append("double minus sequence")
    return issues


def evaluate_track(source_text: str, body: dict[str, Any]) -> tuple[list[str], str, str, dict[str, Any], dict[str, Any]]:
    issues = validate_result(body)
    q = str(body.get("problem") or body.get("question_text") or "").strip()
    issues.extend(classify_question_style(q))
    if not q:
        return issues, "", "", {}, {}
    try:
        matched, reason, src_sig, gen_sig = _PFH.same_family_and_structure(source_text, q)
    except Exception as exc:
        issues.append(f"structure check crashed: {exc}")
        return issues, "", "", {}, {}
    if not matched:
        issues.append(reason)
    return issues, src_sig.get("family", ""), gen_sig.get("family", ""), src_sig, gen_sig


def status_cell(ok: bool, issues: list[str]) -> str:
    if ok:
        return "PASS"
    return "FAIL: " + " ; ".join(issues[:6])


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    rows: list[str] = []
    failed = 0
    drift_cases: list[dict[str, Any]] = []

    cases = TEST_CASES[:LIMIT] if LIMIT > 0 else TEST_CASES

    print(f"[START] Polynomial textbook regression: {len(cases)} cases, {LOOPS} loops each")
    print(f"[START] generate={GENERATE_URL}")
    print(f"[START] run={RUN_URL}")

    for idx, case in enumerate(cases, start=1):
        t0 = time.perf_counter()
        status = "PASS"
        gen_issues: list[str] = []
        loop_issues: list[str] = []
        generated: dict[str, Any] = {}
        first_next: dict[str, Any] = {}
        src_family = case["family"]
        gen_family = ""
        loop_family = ""
        src_sig: dict[str, Any] = {}
        gen_sig: dict[str, Any] = {}
        loop_sig: dict[str, Any] = {}
        try:
            generated = call_generate(case["text"])
            gen_issues, _src_family, gen_family, src_sig, gen_sig = evaluate_track(case["text"], generated)
            if generated.get("architect_model") != "PolynomialFunctionHelper":
                gen_issues.append(f"unexpected architect_model={generated.get('architect_model')}")
            if _src_family:
                src_family = _src_family

            file_path = str(generated.get("file_path") or "")
            if not file_path or not os.path.exists(file_path):
                loop_issues.append("missing generated file_path")
            else:
                for loop in range(1, LOOPS + 1):
                    nxt = call_next(file_path, case["text"])
                    if not first_next:
                        first_next = nxt
                    loop_errors, _loop_src_family, loop_family, loop_src_sig, loop_sig = evaluate_track(case["text"], nxt)
                    if _loop_src_family:
                        src_family = _loop_src_family
                    if loop_errors:
                        loop_issues.append(f"loop {loop}: " + "; ".join(loop_errors))
                        if not src_sig:
                            src_sig = loop_src_sig
                        break

            detail = gen_issues + loop_issues
            if detail:
                failed += 1
                status = "FAIL: " + " | ".join(detail)
                drift_cases.append(
                    {
                        "idx": idx,
                        "input": case["text"],
                        "generated": generated.get("problem", ""),
                        "next": first_next.get("problem", ""),
                        "issues": detail,
                    }
                )
            elapsed = time.perf_counter() - t0
            print(f"[{idx:02d}/{len(cases)}] {case['family']} {elapsed:.2f}s {status}")
        except Exception as exc:
            failed += 1
            status = f"CRASH: {exc}"
            print(f"[{idx:02d}/{len(cases)}] {case['family']} {status}")

        rows.append(
            "<tr>"
            f"<td>{idx}</td>"
            f"<td>{html.escape(case['text'])}</td>"
            f"<td>{html.escape(str(generated.get('problem') or ''))}</td>"
            f"<td>{html.escape(status_cell(not gen_issues, gen_issues))}</td>"
            f"<td>{html.escape(str(first_next.get('problem') or ''))}</td>"
            f"<td>{html.escape(status_cell(not loop_issues, loop_issues))}</td>"
            f"<td>{html.escape(str(generated.get('answer') or ''))}</td>"
            f"<td>{html.escape(src_family)}</td>"
            f"<td>{html.escape(gen_family or '—')}</td>"
            f"<td>{html.escape(loop_family or '—')}</td>"
            f"<td><code>{html.escape(str(src_sig.get('signature', '')))}</code></td>"
            f"<td><code>{html.escape(str(gen_sig.get('signature', '')))}</code></td>"
            f"<td><code>{html.escape(str(loop_sig.get('signature', '')))}</code></td>"
            f"<td>{html.escape(status)}</td>"
            "</tr>"
        )

    passed = len(cases) - failed
    print("=" * 80)
    print(f"[SUMMARY] total={len(cases)} pass={passed} fail={failed}")
    print("=" * 80)
    if drift_cases:
        print("[DRIFT] first 10 failing cases")
        for row in drift_cases[:10]:
            print(f"- #{row['idx']} {row['issues']}")

    report_path = os.path.join(os.path.dirname(__file__), "stress_test_report_polynomial.html")
    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write(
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<title>Polynomial Stress Report</title>"
            "<script>MathJax = { tex: { inlineMath: [['$', '$']] } };</script>"
            "<script src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js'></script>"
            "<style>body{font-family:Arial,sans-serif;margin:20px;}table{border-collapse:collapse;width:100%;}"
            "th,td{border:1px solid #ddd;padding:10px;vertical-align:top;text-align:left;}th{background:#f2f2f2;}tr:nth-child(even){background:#fafafa;}code{font-size:11px;}</style>"
            "</head><body>"
            f"<h2>多項式四則運算 live_show 壓力測試</h2><p>Total: {len(cases)} | Pass: {passed} | Fail: {failed}</p>"
            f"<p>Skill: {html.escape(SKILL_ID)} | Loops: {LOOPS}</p>"
            "<table><tr><th>#</th><th>課本題目</th><th>首題生成</th><th>首題狀態</th><th>下一題</th><th>下一題狀態</th><th>答案</th><th>Expected Family</th><th>Generated Family</th><th>Next Family</th><th>Expected Signature</th><th>Generated Signature</th><th>Next Signature</th><th>整體狀態</th></tr>"
            + "".join(rows)
            + "</table></body></html>"
        )
    print(f"[HTML] report saved to {report_path}")


if __name__ == "__main__":
    main()
