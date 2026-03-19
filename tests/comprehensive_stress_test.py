# -*- coding: utf-8 -*-
"""
綜合壓力測試：模擬會場實戰 (純淨解析版)
1. 自動拆解 14 大題為純 LaTeX 小題（排除題號與說明）。
2. 在 Terminal 即時顯示當前測試的算式內容。
3. 驗證產出是否符合國中教科書格式。
"""

import copy
import html
import os
import re
import sys
import time
import requests
from typing import Any, Dict, List, Tuple

# 確保可引用專案根目錄下的本地模組
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# 課本 14 大題原始資料
FULL_MINUS = "\uFF0D"   # 全形 －
FULL_PLUS = "\uFF0B"    # 全形 ＋
RAW_STRINGS = [
    f"計算下列各式的值。⑴ $({FULL_MINUS}2 )\\times3 \\sqrt{{5}}$ ⑵ $4 \\sqrt{{2}}\\times \\frac{{1}}{{6}}$ ⑶ $\\frac{{2}}{{3}}\\times \\frac{{\\sqrt{{3}}}}{{3}}$",
    f"計算下列各式的值。⑴ $\\frac{{3}}{{5}}\\times5 \\sqrt{{2}}$ ⑵ $\\frac{{\\sqrt{{5}}}}{{12}}\\times({FULL_MINUS}16 )$ ⑶ $\\frac{{3\\sqrt{{7}}}}{{4}}\\times \\frac{{1}}{{9}}$",
    f"計算下列各式的值。⑴ $\\sqrt{{2}}\\times \\sqrt{{3}}$ ⑵ $({FULL_MINUS}\\frac{{2}}{{3}} \\sqrt{{5}} \\quad )\\times4 \\sqrt{{7}}$ ⑶ $7 \\sqrt{{2}}\\times5 \\sqrt{{2}}$",
    f"計算下列各式的值。⑴ $\\sqrt{{35}}\\div \\sqrt{{5}}$ ⑵ $({FULL_MINUS}12 \\sqrt{{6}} )\\div( 8 \\sqrt{{3}} )$ ⑶ $\\frac{{1}}{{\\sqrt{{3}}}}\\div \\frac{{\\sqrt{{6}}}}{{\\sqrt{{2}}}}$",
    "將下列根式化為最簡根式。⑴ $\\sqrt{5^3}$ ⑵ $\\sqrt{18}$ ⑶ $\\sqrt{8}\\times \\sqrt{45}$",
    "將下列根式化為最簡根式。⑴ $\\frac{2}{\\sqrt{10}}$ ⑵ $\\frac{5}{\\sqrt{12}}$",
    "將下列根式化為最簡根式。⑴ $\\sqrt{0.8}$ ⑵ $\\sqrt{\\frac{5}{27}}$",
    "圈圈看，下列哪些是 $\\sqrt{6}$ 的同類方根？ $\\sqrt{12}$ $\\sqrt{24}$ $\\sqrt{16}$ $\\sqrt{\\frac{2}{3}}$ $\\frac{2}{\\sqrt{3}}$ $\\sqrt{0.06}$",
    f"化簡下列各式。⑴ $2 \\sqrt{{3}}{FULL_PLUS}3 \\sqrt{{3}}$ ⑵ $4 \\sqrt{{6}}{FULL_MINUS}3 \\sqrt{{6}}$ ⑶ $5 \\sqrt{{10}}{FULL_MINUS}3 \\sqrt{{5}}{FULL_MINUS}2 \\sqrt{{10}}{FULL_PLUS}4 \\sqrt{{5}}$",
    f"化簡下列各式。⑴ $3 \\sqrt{{2}}{FULL_PLUS} \\sqrt{{8}}$ ⑵ $\\sqrt{{1\\frac{{9}}{{16}}}}{FULL_PLUS} \\sqrt{{4\\frac{{25}}{{36}}}}$ ⑶ $\\frac{{1}}{{\\sqrt{{3}}}}{FULL_MINUS}\\frac{{2}}{{3}} \\sqrt{{3}}$ ⑷ $3 \\sqrt{{3}}{FULL_PLUS}2 \\sqrt{{5}}{FULL_MINUS}( \\sqrt{{12}}{FULL_MINUS} \\sqrt{{45}} )$",
    f"化簡下列各式。⑴ $\\sqrt{{\\frac{{1}}{{2}}}}\\times \\sqrt{{\\frac{{1}}{{5}}}}\\div \\sqrt{{\\frac{{1}}{{6}}}}$ ⑵ $({FULL_MINUS}4 \\sqrt{{15}} )\\times({FULL_MINUS} \\sqrt{{\\frac{{1}}{{3}}}} ){FULL_MINUS}4 \\sqrt{{5}}$",
    f"化簡下列各式。⑴ $2 \\sqrt{{3}}\\times( \\sqrt{{12}}{FULL_MINUS} \\sqrt{{2}} )$ ⑵ $({FULL_MINUS}3 \\sqrt{{2}}{FULL_PLUS} \\sqrt{{15}} )\\div \\sqrt{{3}}$ ⑶ $( \\sqrt{{3}}{FULL_PLUS} \\sqrt{{2}} )( \\sqrt{{6}}{FULL_MINUS}1 )$",
    f"利用乘法公式化簡下列各式。⑴ $( \\sqrt{{3}}{FULL_MINUS}2 \\sqrt{{2}} )( \\sqrt{{3}}{FULL_PLUS}2 \\sqrt{{2}} )$ ⑵ $( \\sqrt{{3}}{FULL_PLUS}2 \\sqrt{{2}} \\quad )^2$",
    f"將下列各式的分母有理化。⑴ $\\frac{{1}}{{ \\sqrt{{3}}{FULL_MINUS} \\sqrt{{2}}}}$ ⑵ $\\frac{{\\sqrt{{2}}}}{{3 \\sqrt{{2}}{FULL_PLUS}4}}$",
]

BASE_URL = os.environ.get("MATHPROJECT_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
CLASSIFY_URL = f"{BASE_URL}/api/classify"
GENERATE_URL = f"{BASE_URL}/api/generate_live"
# 僅在 classify 失敗且需對照舊行為時作為後備（預設不走此路）
FALLBACK_SKILL_ID = "jh_數學2上_FourOperationsOfRadicals"
CLASSIFY_TIMEOUT = int(os.environ.get("STRESS_CLASSIFY_TIMEOUT", "180"))
GENERATE_TIMEOUT = int(os.environ.get("STRESS_GENERATE_TIMEOUT", "300"))


def clean_latex(inner: str) -> str:
    """清理算式：處理全形字元並移除所有空格。"""
    s = inner.replace(FULL_MINUS, "-").replace(FULL_PLUS, "+")
    # 把 \x0crac 救回 \frac（Python 字串裡 \f 曾被誤判為 Form Feed）
    s = s.replace("\x0c", "\\f")
    return s.replace(" ", "").strip()


def collect_pure_math_cases() -> List[Tuple[int, int, str, str]]:
    """
    從 RAW_STRINGS 提取純淨的 $...$ 片段。
    回傳 (大題編號, 小題編號, 清洗後算式, 該大題完整課本原文)。
    完整原文會一併送進 /api/classify，貼近前端「整段題幹 + 辨識」再交 generate 的流程。
    """
    test_cases = []
    for big_idx, raw_text in enumerate(RAW_STRINGS, start=1):
        matches = re.findall(r"\$(.*?)\$", raw_text)
        for sub_idx, fragment in enumerate(matches, start=1):
            cleaned = clean_latex(fragment)
            if cleaned:
                test_cases.append((big_idx, sub_idx, cleaned, raw_text))
    return test_cases


def build_classify_text_data(parent_raw_line: str, math_expr: str) -> str:
    """
    回應診斷：拔除干擾的中文前綴，只給 AI 最純淨的算式，
    迫使它的注意力 100% 集中在 LaTeX 骨架上！
    """
    safe_expr = math_expr.replace("\x0c", "\\f")
    # 🌟 直接回傳純算式，不加任何「計算下列各式...」的廢話！
    return f"${safe_expr}$"


def run_classify(text_data: str) -> Tuple[bool, Dict[str, Any], str]:
    """
    POST /api/classify。成功時回 (True, body, "")；失敗時回 (False, {{}}, 錯誤訊息)。
    """
    try:
        r = requests.post(
            CLASSIFY_URL,
            json={"text_data": text_data},
            timeout=CLASSIFY_TIMEOUT,
        )
        body = r.json() if r.content else {}
        if r.status_code != 200:
            err = body.get("error") if isinstance(body, dict) else str(body)
            return False, {}, f"HTTP {r.status_code}: {err or r.text[:200]}"
        if not isinstance(body, dict) or not body.get("success"):
            err = body.get("error", "classify success=false") if isinstance(body, dict) else "invalid JSON"
            return False, {}, str(err)
        return True, body, ""
    except Exception as e:
        return False, {}, str(e)


def normalize_classify_result(
    c_body: Dict[str, Any], math_expr: str
) -> Tuple[str, str, Dict[str, Any], List[str]]:
    """
    清理 classify 回傳，避免 Unknown skill / 非純算式 ocr_text 讓 generate 直接 400。
    回傳: (skill_id, ocr_text, json_spec, notes)
    """
    notes: List[str] = []
    raw_skill = (c_body.get("skill_id") or "").strip()
    ocr_text = (c_body.get("ocr_text") or "").strip()
    json_spec = c_body.get("json_spec")
    if not isinstance(json_spec, dict):
        json_spec = {}
    json_spec = copy.deepcopy(json_spec)

    if not ocr_text:
        ocr_text = math_expr
        notes.append("ocr_text fallback to math_expr")

    # 測試場景：Unknown skill 直接讓 generate_live 拒絕，故在壓測腳本做後備
    skill_id = raw_skill if raw_skill and raw_skill != "Unknown" else FALLBACK_SKILL_ID
    if raw_skill == "Unknown":
        notes.append(f"skill fallback to {FALLBACK_SKILL_ID}")

    json_spec["ocr_text"] = ocr_text
    return skill_id, ocr_text, json_spec, notes


def run_assertions(problem_text: str) -> List[str]:
    """執行排版品質檢驗"""
    errors = []
    if not problem_text or len(problem_text.strip()) < 2:
        return ["❌ 產出為空"]

    # 🌟 教授的最後一道防護網：沒有 $ 符號絕對不是合法的數學題！
    if problem_text.count("$") == 0:
        errors.append("❌ 嚴重瑕疵：遺失數學模式符號 $")

    # 1. 嚴禁中括號 (除非是 LaTeX 指令)
    clean_text = problem_text.replace(r"\left[", "").replace(r"\right]", "")
    if "[" in clean_text or "]" in clean_text:
        errors.append("❌ 偵測到非法中括號 [ ]")

    # 2. 嚴禁雙括號
    if "((" in problem_text or "))" in problem_text:
        errors.append("❌ 偵測到冗餘雙括號 (( ))")

    # 3. 乘號後負數保護
    if re.search(r"\\times\s*-", problem_text):
        errors.append("❌ 偵測到 \\times 接裸露負號")

    # LaTeX 致命錯誤攔截
    if problem_text.count("{") != problem_text.count("}"):
        errors.append("❌ LaTeX 大括號 { } 不成對 (渲染必死)")
    if problem_text.count("$") % 2 != 0:
        errors.append("❌ 數學模式 $ 不成對 (渲染必死)")

    return errors


def main() -> None:
    test_items = collect_pure_math_cases()
    total = len(test_items)
    print(f"[START] 壓力測試啟動：共 {len(RAW_STRINGS)} 大題，解析出 {total} 個純淨算式。")
    print(f"[START] 流程：POST {CLASSIFY_URL}（含大題原文+小題）→ POST {GENERATE_URL}（沿用 json_spec）")
    print("=" * 80)

    passed, failed, crashed = 0, 0, 0
    fail_details = []
    html_rows = []

    for idx, (big, sub, math_expr, parent_raw) in enumerate(test_items, start=1):
        print(f"\n[TEST] [{idx}/{total}] 正在處理題目 ({big}-{sub}): {math_expr}")

        text_for_classify = build_classify_text_data(parent_raw, math_expr)
        c0 = time.perf_counter()
        ok_c, c_body, c_err = run_classify(text_for_classify)
        classify_elapsed = time.perf_counter() - c0

        if not ok_c:
            print(f"  [FAIL] [CLASSIFY] {c_err}")
            failed += 1
            fail_details.append(
                {"idx": idx, "input": math_expr, "output": "", "errors": [f"classify: {c_err}"]}
            )
            html_rows.append(f"""
                <tr>
                    <td>{idx}</td>
                    <td>${html.escape(math_expr)}$</td>
                    <td><span style="color:red"><b>[classify 失敗]</b></span></td>
                    <td></td>
                    <td>❌ {html.escape(c_err)}</td>
                    <td>—</td>
                </tr>
            """)
            continue

        skill_id, ocr_text, json_spec, normalize_notes = normalize_classify_result(c_body, math_expr)

        _ocr_preview = (
            f"{ocr_text[:80]!r}..."
            if len(ocr_text) > 80
            else repr(ocr_text)
        )
        print(
            f"  [CLASSIFY] ({classify_elapsed:.2f}s) skill_id={skill_id} | ocr_text={_ocr_preview}"
        )
        if normalize_notes:
            print(f"  [CLASSIFY-NORMALIZE] {', '.join(normalize_notes)}")

        payload = {
            "input_text": ocr_text,
            "prompt": ocr_text,
            "ablation_mode": False,
            "model_id": "qwen3-vl-8b",
            "model": "qwen3-vl-8b",
            "skill_id": skill_id,
            "json_spec": json_spec,
        }

        try:
            start_t = time.perf_counter()
            r = requests.post(GENERATE_URL, json=payload, timeout=GENERATE_TIMEOUT)
            elapsed = time.perf_counter() - start_t

            if r.status_code == 200:
                data = r.json()
                generated_q = data.get("problem", "")
                ans = data.get("answer", "")

                backend_error = data.get("error", "")
                if not backend_error and not generated_q:
                    backend_error = "模型輸出格式嚴重損毀，導致沙盒拒絕執行或正則清空。"

                issues = run_assertions(generated_q)

                if not generated_q:
                    issues.append(f"❌ 致命崩潰: {backend_error}")

                status_icon = "✅" if not issues else "❌"
                html_rows.append(f"""
                <tr>
                    <td>{idx}</td>
                    <td>${html.escape(math_expr)}$<br><small>classify ocr: {html.escape(ocr_text[:120])}{'…' if len(ocr_text) > 120 else ''}</small><br><small>skill: {html.escape(skill_id)}</small></td>
                    <td>{html.escape(generated_q) if generated_q else '<span style="color:red"><b>[無產出]</b></span>'}</td>
                    <td>{html.escape(str(ans))}</td>
                    <td>{status_icon} {html.escape(', '.join(issues))}</td>
                    <td>cls {classify_elapsed:.2f}s / gen {elapsed:.2f}s</td>
                </tr>
                """)

                if not issues:
                    print(
                        f"  [PASS] (classify {classify_elapsed:.2f}s, generate {elapsed:.2f}s) -> 生成結果: {generated_q}"
                    )
                    passed += 1
                else:
                    print(f"  [FAIL] {', '.join(issues)}")
                    print(f"     原始輸入: {math_expr}")
                    print(f"     生成輸出: {generated_q}")
                    failed += 1
                    fail_details.append({"idx": idx, "input": math_expr, "output": generated_q, "errors": issues})
            else:
                msg = f"generate_live HTTP {r.status_code}: {(r.text or '')[:300]}"
                print(f"  [CRASH] {msg}")
                crashed += 1
                html_rows.append(f"""
                <tr>
                    <td>{idx}</td>
                    <td>${html.escape(math_expr)}$<br><small>classify ocr: {html.escape(ocr_text[:120])}{'…' if len(ocr_text) > 120 else ''}</small><br><small>skill: {html.escape(skill_id)}</small></td>
                    <td><span style="color:red"><b>[HTTP 錯誤]</b></span></td>
                    <td></td>
                    <td>❌ {html.escape(msg)}</td>
                    <td>cls {classify_elapsed:.2f}s</td>
                </tr>
                """)
                fail_details.append({"idx": idx, "input": math_expr, "output": "", "errors": [msg]})
        except Exception as e:
            print(f"  [CRASH] 連線錯誤: {str(e)}")
            crashed += 1
            html_rows.append(f"""
                <tr>
                    <td>{idx}</td>
                    <td>${html.escape(math_expr)}$<br><small>classify ocr: {html.escape(ocr_text[:120])}{'…' if len(ocr_text) > 120 else ''}</small><br><small>skill: {html.escape(skill_id)}</small></td>
                    <td><span style="color:red"><b>[連線例外]</b></span></td>
                    <td></td>
                    <td>❌ {html.escape(str(e))}</td>
                    <td>cls {classify_elapsed:.2f}s</td>
                </tr>
                """)
            fail_details.append({"idx": idx, "input": math_expr, "output": "", "errors": [str(e)]})

    print("\n" + "=" * 80)
    print("[REPORT] 最終測試報表")
    print("-" * 80)
    print(f"  總測試數: {total}")
    print(f"  成功 (PASS): {passed}")
    print(f"  瑕疵 (FAIL): {failed}")
    print(f"  崩潰 (CRASH): {crashed}")
    if total:
        print(f"  成功率: {passed / total * 100:.1f}%")
    print("=" * 80)

    if fail_details:
        print("\n[DIAG] 瑕疵題目診斷清單：")
        for f in fail_details:
            print(f"- [#{f['idx']}] 輸入: {f['input']} | 輸出: {f['output']} | 原因: {f['errors']}")

    html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MathProject 壓力測試渲染報表 (Ab3)</title>
    <script>
        MathJax = {{
            tex: {{ inlineMath: [['$', '$']] }}
        }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; vertical-align: top; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background: #fafafa; }}
    </style>
</head>
<body>
    <h2>根式四則運算 (Qwen3-VL-8B + Active Healer) 壓力測試渲染結果</h2>
    <p>流程：每題先 <code>/api/classify</code>（text_data = 大題原文 + 小題算式），再以回傳的 <code>json_spec</code> + <code>ocr_text</code> 呼叫 <code>/api/generate_live</code>。</p>
    <p>總測試數: {total} | 成功: {passed} | 失敗: {failed} | 崩潰: {crashed}</p>
    <table>
        <tr><th>編號</th><th>課本小題 / classify 結果</th><th>AI 生成題幹 (LaTeX渲染測試)</th><th>生成答案</th><th>狀態</th><th>耗時 (classify / generate)</th></tr>
        {''.join(html_rows)}
    </table>
</body>
</html>
"""
    report_path = os.path.join(os.path.dirname(__file__), "stress_test_report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"\n[HTML] 已產生視覺化報表：{report_path} (請用瀏覽器開啟以檢查 LaTeX 渲染)")


if __name__ == "__main__":
    main()
