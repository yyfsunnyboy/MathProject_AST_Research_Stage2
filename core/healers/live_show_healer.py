# -*- coding: utf-8 -*-
"""Live Show 專用的顯示層 Healer 工具。"""

import re
from core.skill_policies import get_skill_policy


def _normalize_plain_operator_tokens(text):
    if not text:
        return text, 0

    out = str(text)
    total = 0

    out, n = re.subn(r'\\times\b', '×', out)
    total += n
    out, n = re.subn(r'\\div\b', '÷', out)
    total += n

    out, n = re.subn(r'(?<!\\)(?<![A-Za-z])times(?![A-Za-z])', '×', out, flags=re.IGNORECASE)
    total += n
    out, n = re.subn(r'(?<!\\)(?<![A-Za-z])div(?![A-Za-z])', '÷', out, flags=re.IGNORECASE)
    total += n

    return out, total


def collapse_double_numeric_parentheses(expr_text):
    if not expr_text:
        return expr_text, 0

    out = str(expr_text)
    total_replacements = 0
    for _ in range(8):
        new_out, count = re.subn(r'\(\s*\(\s*(-?\d+)\s*\)\s*\)', r'(\1)', out)
        total_replacements += count
        if new_out == out:
            break
        out = new_out
    return out, total_replacements


def enforce_negative_parentheses(expr_text):
    """
    將顯示算式中的「單元負數常數（或負混合分數）」統一為括號格式：
    -3            -> (-3)
    -4\\frac{1}{5} -> (-4\\frac{1}{5})   [FIX: 負混合分數整體包裝]
    但已經是 (-3) 或 (-4\\frac{1}{5}) 的不重複包裝。

    Bug 修正：原版只掃描數字部分，導致 -4\\frac{1}{5} 被誤包成
    (-4)\\frac{1}{5}，負號僅覆蓋整數部分而非整個混合分數。
    修正：掃到數字後若緊接 \\frac，繼續掃過兩個 {...} 大括號群，
    使 already_wrapped 判斷能正確偵測外層括號。
    """
    if not expr_text:
        return expr_text, 0

    compact = "".join(str(expr_text).split())
    out = []
    changes = 0
    i = 0

    while i < len(compact):
        ch = compact[i]
        if ch == '-':
            prev = compact[i - 1] if i > 0 else ''
            unary = (i == 0 or prev in '+-*/([|')
            if unary:
                j = i + 1
                if j < len(compact) and compact[j].isdigit():
                    while j < len(compact) and compact[j].isdigit():
                        j += 1

                    # [FIX] 若數字後緊接 \frac{a}{b}，將整個混合分數併入 token
                    # 例：-4\frac{1}{5} → token="-4\frac{1}{5}"
                    # 這樣 already_wrapped 才能正確偵測到外層 (...)
                    if compact[j:j + 5] == '\\frac':
                        j += 5  # skip '\frac'
                        for _ in range(2):  # 掃過兩組 {分子}{分母}
                            if j < len(compact) and compact[j] == '{':
                                depth = 1
                                j += 1
                                while j < len(compact) and depth > 0:
                                    if compact[j] == '{':
                                        depth += 1
                                    elif compact[j] == '}':
                                        depth -= 1
                                    j += 1

                    already_wrapped = (prev == '(' and j < len(compact) and compact[j] == ')')
                    token = compact[i:j]
                    if already_wrapped:
                        out.append(token)
                    else:
                        out.append(f"({token})")
                        changes += 1
                    i = j
                    continue

        out.append(ch)
        i += 1

    return "".join(out), changes


def sanitize_question_text_display(question_text, return_report=False):
    if not question_text:
        return (question_text, {"double_paren_fixes": 0, "negative_wrap_fixes": 0, "operator_token_fixes": 0}) if return_report else question_text

    text = str(question_text)
    m = re.search(r'\$(.*?)\$', text)
    total_fixes = 0
    total_neg_wraps = 0
    op_token_count = 0
    if m:
        inner = m.group(1)
        fixed_inner, fix_count = collapse_double_numeric_parentheses(inner)
        total_fixes += fix_count
        fixed_inner_2, wrap_count = enforce_negative_parentheses(fixed_inner)
        total_neg_wraps += wrap_count
        sanitized = text[:m.start(1)] + fixed_inner_2 + text[m.end(1):]
    else:
        sanitized, fix_count = collapse_double_numeric_parentheses(text)
        total_fixes += fix_count
        sanitized, wrap_count = enforce_negative_parentheses(sanitized)
        total_neg_wraps += wrap_count
        sanitized, op_token_count = _normalize_plain_operator_tokens(sanitized)

    if return_report:
        return sanitized, {
            "double_paren_fixes": total_fixes,
            "negative_wrap_fixes": total_neg_wraps,
            "operator_token_fixes": int(op_token_count if 'op_token_count' in locals() else 0),
        }
    return sanitized


def infer_fraction_display_mode(source_text, skill_id, extract_expr_fn=None):
    policy = get_skill_policy(skill_id)
    if not bool(policy.get("enable_fraction_display", False)):
        return "none"
    if not source_text:
        return "fraction"

    text = str(source_text)
    expr = extract_expr_fn(text) if callable(extract_expr_fn) else ""
    expr_text = "" if expr is None else str(expr)
    target = expr_text or text

    mixed_patterns = [
        r'(?<!\\frac\{)[+-]?\d+\s*\\frac\s*\{\s*\d+\s*\}\s*\{\s*[1-9]\d*\s*\}',
        r'(?<!\d)[+-]?\d+\s+\d+\s*/\s*[1-9]\d*(?!\d)',
    ]
    if any(re.search(p, target) for p in mixed_patterns):
        return "mixed"
    return "fraction"


def has_decimal_number(text, extract_expr_fn=None):
    if not text:
        return False
    base_text = str(text)
    target = extract_expr_fn(base_text) if callable(extract_expr_fn) else ""
    target = str(target) if target is not None else ""
    target = target or base_text
    return re.search(r'(?<!\d)-?\d+\.\d+(?!\d)', target) is not None


def format_fraction_mixed_display(
    question_text,
    skill_id,
    display_mode="auto",
    source_text=None,
    return_report=False,
    infer_mode_fn=None,
):
    policy = get_skill_policy(skill_id)
    if not bool(policy.get("enable_fraction_display", False)):
        if return_report:
            return question_text, {"regex_fix_count": 0}
        return question_text
    if not question_text:
        if return_report:
            return question_text, {"regex_fix_count": 0}
        return question_text

    mode = display_mode or "auto"
    if mode == "auto":
        basis = source_text if source_text else question_text
        if callable(infer_mode_fn):
            mode = infer_mode_fn(basis, skill_id)
        else:
            mode = infer_fraction_display_mode(basis, skill_id)
    use_mixed = (mode == "mixed")

    def _fraction_latex(num_text, den_text):
        try:
            import math
            num = int(num_text)
            den = int(den_text)
            if den == 0:
                return f"{num_text}/{den_text}"
            if den < 0:
                den = -den
                num = -num

            raw_num = num
            raw_den = den

            g = math.gcd(abs(num), abs(den))
            if g > 1:
                num //= g
                den //= g
            sign = "-" if num < 0 else ""
            anum = abs(num)
            whole = anum // den
            rem = anum % den
            if rem == 0:
                return f"{sign}\\frac{{{abs(raw_num)}}}{{{raw_den}}}"
            if not use_mixed:
                return f"{sign}\\frac{{{anum}}}{{{den}}}"
            if whole == 0:
                return f"{sign}\\frac{{{rem}}}{{{den}}}"
            return f"{sign}{whole}\\frac{{{rem}}}{{{den}}}"
        except Exception:
            return f"{num_text}/{den_text}"

    text = str(question_text)
    m = re.search(r'\$(.*?)\$', text)
    if not m:
        normalized_text, op_token_count = _normalize_plain_operator_tokens(text)
        report = {
            "regex_fix_count": int(op_token_count),
            "fix_breakdown": {"plain_operator_token_to_symbol": int(op_token_count)} if op_token_count > 0 else {},
        }
        if return_report:
            return normalized_text, report
        return normalized_text

    inner = m.group(1)

    def _replace_latex_frac(mt):
        return _fraction_latex(mt.group(1), mt.group(2))

    def _replace_plain_frac(mt):
        return _fraction_latex(mt.group(1), mt.group(2))

    def _replace_paren_num_frac(mt):
        return _fraction_latex(mt.group(1), mt.group(2))

    def _replace_num_paren_den_frac(mt):
        return _fraction_latex(mt.group(1), mt.group(2))

    def _replace_paren_paren_frac(mt):
        return _fraction_latex(mt.group(1), mt.group(2))

    regex_fix_count = 0
    breakdown = {}

    def _inc(name, n):
        nonlocal regex_fix_count
        n = int(n or 0)
        if n <= 0:
            return
        regex_fix_count += n
        breakdown[name] = int(breakdown.get(name, 0)) + n

    inner2, n = re.subn(r'\\frac\s*\{\s*([+-]?\d+)\s*\}\s*\{\s*([1-9]\d*)\s*\}', _replace_latex_frac, inner)
    _inc("normalize_latex_fraction", n)
    inner2, n = re.subn(r'\(\s*([+-]?\d+)\s*\)\s*/\s*\(\s*([+-]?\d+)\s*\)(?!\s*/)', _replace_paren_paren_frac, inner2)
    _inc("paren_over_paren_to_fraction", n)
    inner2, n = re.subn(r'\(\s*([+-]?\d+)\s*\)\s*/\s*([1-9]\d*)(?!\s*/)', _replace_paren_num_frac, inner2)
    _inc("paren_num_over_num_to_fraction", n)
    inner2, n = re.subn(r'(?<![\d\\}/])([+-]?\d+)\s*/\s*\(\s*([+-]?\d+)\s*\)(?!\s*/)', _replace_num_paren_den_frac, inner2)
    _inc("num_over_paren_den_to_fraction", n)
    inner2, n = re.subn(
        r'(?<![\d\\}/])([+-]?\d+)\s*/\s*([1-9]\d*)(?!\s*/)(?![\d\{])',
        _replace_plain_frac,
        inner2
    )
    _inc("slash_fraction_to_latex", n)

    inner2, n = re.subn(
        r'(?<![\d\\}])([+-]?\d+)\s*/\s*([1-9]\d*)(?![\d\{])',
        _replace_plain_frac,
        inner2
    )
    _inc("slash_fraction_to_latex_fallback", n)

    for _ in range(3):
        _before = inner2
        inner2 = inner2.replace("+-", "-").replace("-+", "-").replace("++", "+").replace("--", "+")
        if inner2 != _before:
            _inc("normalize_sign_sequence", 1)

    for _ in range(6):
        new_inner = inner2
        new_inner, n = re.subn(r'-\(\s*-\s*([^()]+?)\s*\)', r'+\1', new_inner)
        _inc("double_negative_parenthesis", n)
        new_inner, n = re.subn(r'\+\(\s*-\s*([^()]+?)\s*\)', r'-\1', new_inner)
        _inc("plus_negative_parenthesis", n)
        new_inner, n = re.subn(r'-\(\s*\+\s*([^()]+?)\s*\)', r'-\1', new_inner)
        _inc("minus_plus_parenthesis", n)
        new_inner, n = re.subn(r'\+\(\s*\+\s*([^()]+?)\s*\)', r'+\1', new_inner)
        _inc("plus_plus_parenthesis", n)

        new_inner, n = re.subn(
            r'\(\s*([+-]?(?:\\frac\{\d+\}\{\d+\}|\d+\\frac\{\d+\}\{\d+\}|\d+))\s*\)',
            r'\1',
            new_inner
        )
        _inc("remove_redundant_atomic_parenthesis", n)
        new_inner = new_inner.replace("+-", "-").replace("-+", "-").replace("++", "+").replace("--", "+")
        if new_inner == inner2:
            break
        inner2 = new_inner

    inner2, n = re.subn(r'\\{2,}div\b', lambda _m: '\\div', inner2)
    _inc("normalize_div_backslashes", n)
    inner2, n = re.subn(r'\\{2,}times\b', lambda _m: '\\times', inner2)
    _inc("normalize_times_backslashes", n)

    inner2, n = re.subn(r'(?<!\\)(?<![A-Za-z])div(?![A-Za-z])', r'\\div', inner2, flags=re.IGNORECASE)
    _inc("fix_plain_div_token", n)
    inner2, n = re.subn(r'(?<!\\)(?<![A-Za-z])times(?![A-Za-z])', r'\\times', inner2, flags=re.IGNORECASE)
    _inc("fix_plain_times_token", n)

    inner2, n = re.subn(r'(?<!\\)div(?=\s*[\[\(\{])', r'\\div', inner2)
    _inc("fix_plain_div_token", n)
    inner2, n = re.subn(r'(?<=\d)\s*div\s*(?=[\-\+\[\(\{\\])', r'\\div', inner2)
    _inc("fix_plain_div_token", n)
    inner2, n = re.subn(r'(?<!\\)times(?=\s*[\[\(\{])', r'\\times', inner2)
    _inc("fix_plain_times_token", n)

    inner2, n = re.subn(r'(\\left\[)\s*\+\s*', r'\1', inner2)
    _inc("remove_leading_plus_in_left_bracket", n)
    inner2, n = re.subn(r'(\\left\()\s*\+\s*', r'\1', inner2)
    _inc("remove_leading_plus_in_left_paren", n)
    inner2, n = re.subn(r'(\\left\{)\s*\+\s*', r'\1', inner2)
    _inc("remove_leading_plus_in_left_brace", n)
    inner2, n = re.subn(r'([\[\(\{])\s*\+\s*', r'\1', inner2)
    _inc("remove_leading_plus_after_open_bracket", n)

    inner2, n = re.subn(r'^\s*\+\s*', '', inner2)
    _inc("remove_leading_plus_at_start", n)

    out = text[:m.start(1)] + inner2 + text[m.end(1):]
    if return_report:
        return out, {"regex_fix_count": int(regex_fix_count), "fix_breakdown": breakdown}
    return out


def healer_rule_explain(rule_key):
    mapping = {
        "normalize_latex_fraction": "標準化既有 LaTeX 分數格式",
        "paren_over_paren_to_fraction": "將 (a)/(b) 轉為教材分數格式",
        "paren_num_over_num_to_fraction": "將 (a)/b 轉為教材分數格式",
        "num_over_paren_den_to_fraction": "將 a/(b) 轉為教材分數格式",
        "slash_fraction_to_latex": "將 a/b 斜線分數轉為 \\frac{a}{b}",
        "slash_fraction_to_latex_fallback": "補抓遺漏斜線分數並轉為 LaTeX",
        "normalize_sign_sequence": "清理連續符號（+-、-- 等）",
        "double_negative_parenthesis": "清理雙重負號括號（-(-x)）",
        "plus_negative_parenthesis": "清理 +(-x) 為 -x",
        "minus_plus_parenthesis": "清理 -(+x) 為 -x",
        "plus_plus_parenthesis": "清理 +(+x) 為 +x",
        "remove_redundant_atomic_parenthesis": "移除原子分數/整數外層冗餘括號",
        "fix_plain_div_token": "修正裸字串 div 為 LaTeX \\div",
        "fix_plain_times_token": "修正裸字串 times 為 LaTeX \\times",
        "normalize_div_backslashes": "將重複反斜線 \\\\div 正規化為 \\div",
        "normalize_times_backslashes": "將重複反斜線 \\\\times 正規化為 \\times",
        "remove_leading_plus_in_left_bracket": "移除 \\left[ 後多餘正號",
        "remove_leading_plus_in_left_paren": "移除 \\left( 後多餘正號",
        "remove_leading_plus_in_left_brace": "移除 \\left{ 後多餘正號",
        "remove_leading_plus_after_open_bracket": "移除開括號後多餘正號",
        "remove_leading_plus_at_start": "移除式首多餘正號",
    }
    return mapping.get(rule_key, f"規則 {rule_key}")


def build_readable_healer_logs(healer_trace, detail_logs):
    def _to_zh(line):
        s = str(line or "").strip()

        if s.startswith("AST Healer:"):
            body = s.replace("AST Healer:", "", 1).strip()
            body = body.replace("Replaced dangerous function", "已替換危險函式")
            body = body.replace("with", "為")
            return f"- AST 修補：{body}"

        if s.startswith("[ISO_GUARD]"):
            content = s.replace("[ISO_GUARD]", "", 1).strip()
            content = content.replace("primary output profile mismatch.", "主輸出結構與目標不一致。")
            content = content.replace("operator_sequence:", "運算子序列差異：")
            content = content.replace("number_count:", "數字數量差異：")
            content = content.replace("op_counts:", "四則運算統計差異：")
            content = content.replace("bracket_count:", "中括號區塊數差異：")
            content = content.replace("bracket_stats mismatch", "中括號內部統計不一致")
            content = content.replace("LLM output drift detected; switched to deterministic isomorphic fallback.", "偵測到模型輸出漂移，已切換到同構 deterministic fallback。")
            return f"- ISO 檢查：{content}"

        if s.startswith("[DISPLAY_SANITIZE]"):
            content = s.replace("[DISPLAY_SANITIZE]", "", 1).strip()
            content = content.replace("collapsed", "已折疊")
            content = content.replace("nested numeric parenthesis pattern(s)", "重複數字括號樣式")
            content = content.replace("wrapped", "已補上")
            content = content.replace("bare negative literal(s) with parentheses", "裸負數括號")
            content = content.replace("after fallback", "（fallback 後）")
            return f"- 題面清理：{content}"

        return ""

    lines = []
    regex_total = int(healer_trace.get("regex_fixes", 0) or 0)
    regex_code = int(healer_trace.get("regex_code_fixes", 0) or 0)
    regex_display = int(healer_trace.get("regex_display_fixes", 0) or 0)
    ast_total = int(healer_trace.get("ast_fixes", 0) or 0)
    o1_total = int(healer_trace.get("o1_fixes", 0) or 0)

    lines.append("HEALER_FIX_SUMMARY")
    lines.append(f"- Regex 總修補: {regex_total}（Code={regex_code}, Display={regex_display}）")
    lines.append(f"- AST 結構修補: {ast_total}")
    lines.append(f"- O(1) 倒算法修補: {o1_total}")

    for raw in detail_logs or []:
        m = re.search(r'^\[DISPLAY_REGEX_HEALER\]\s+([a-z_]+):\s+\+(\d+)$', str(raw).strip())
        if m:
            key = m.group(1)
            cnt = int(m.group(2))
            lines.append(f"- {key}: +{cnt}（{healer_rule_explain(key)}）")

    for raw in detail_logs or []:
        m = re.search(r'^\[DISPLAY_SANITIZE_HEALER\]\s+([a-z_]+):\s+\+(\d+)$', str(raw).strip())
        if m:
            key = m.group(1)
            cnt = int(m.group(2))
            lines.append(f"- {key}: +{cnt}（{sanitize_rule_explain(key)}）")

    for raw in detail_logs or []:
        zh = _to_zh(raw)
        if zh:
            lines.append(zh)

    return lines


def sanitize_rule_explain(rule_key):
    mapping = {
        "double_paren_fixes": "折疊重複數字括號，例如 (((-3))) -> (-3)",
        "negative_wrap_fixes": "將裸負數統一包成括號，例如 -3 -> (-3)",
        "operator_token_fixes": "將裸運算子字串（times/div 或 \\times/\\div）轉為可讀符號（×/÷）",
    }
    return mapping.get(rule_key, f"規則 {rule_key}")


def init_healer_trace(trace=None, fixes_from_payload=0):
    base = trace if isinstance(trace, dict) else {}
    out = dict(base)
    out.setdefault("regex_fixes", int(fixes_from_payload or 0))
    out.setdefault("ast_fixes", 0)
    out.setdefault("regex_code_fixes", int(out.get("regex_fixes", 0) or 0))
    out.setdefault("regex_display_fixes", 0)
    out.setdefault("o1_fixes", int(out.get("o1_fixes", 0) or 0))
    return recompute_regex_totals(out)


def recompute_regex_totals(trace):
    if not isinstance(trace, dict):
        trace = {}
    regex_code = int(trace.get("regex_code_fixes", trace.get("regex_fixes", 0)) or 0)
    regex_display = int(trace.get("regex_display_fixes", 0) or 0)
    trace["regex_code_fixes"] = regex_code
    trace["regex_display_fixes"] = regex_display
    trace["regex_fixes"] = regex_code + regex_display
    trace["ast_fixes"] = int(trace.get("ast_fixes", 0) or 0)
    trace["o1_fixes"] = int(trace.get("o1_fixes", 0) or 0)
    return trace


def apply_sanitize_report_to_trace(trace, detail_logs, sanitize_report, after_fallback=False):
    if not isinstance(trace, dict):
        trace = init_healer_trace({})
    if not isinstance(sanitize_report, dict):
        return 0

    double_cnt = int(sanitize_report.get("double_paren_fixes", 0) or 0)
    negative_cnt = int(sanitize_report.get("negative_wrap_fixes", 0) or 0)
    op_token_cnt = int(sanitize_report.get("operator_token_fixes", 0) or 0)
    total = double_cnt + negative_cnt + op_token_cnt
    if total <= 0:
        return 0

    trace["regex_display_fixes"] = int(trace.get("regex_display_fixes", 0) or 0) + total
    recompute_regex_totals(trace)

    if isinstance(detail_logs, list):
        suffix = " after fallback" if after_fallback else ""
        detail_logs.append(f"[DISPLAY_SANITIZE_HEALER] regex sanitize fixes{suffix}: +{total}")
        if double_cnt > 0:
            detail_logs.append(f"[DISPLAY_SANITIZE_HEALER] double_paren_fixes: +{double_cnt}")
        if negative_cnt > 0:
            detail_logs.append(f"[DISPLAY_SANITIZE_HEALER] negative_wrap_fixes: +{negative_cnt}")
        if op_token_cnt > 0:
            detail_logs.append(f"[DISPLAY_SANITIZE_HEALER] operator_token_fixes: +{op_token_cnt}")

    return total


def apply_display_report_to_trace(trace, detail_logs, display_report):
    if not isinstance(trace, dict):
        trace = init_healer_trace({})
    if not isinstance(display_report, dict):
        return 0

    total = int(display_report.get("regex_fix_count", 0) or 0)
    if total <= 0:
        return 0

    trace["regex_display_fixes"] = int(trace.get("regex_display_fixes", 0) or 0) + total
    recompute_regex_totals(trace)

    if isinstance(detail_logs, list):
        detail_logs.append(f"[DISPLAY_REGEX_HEALER] regex display fixes: +{total}")
        breakdown = display_report.get("fix_breakdown", {}) or {}
        if isinstance(breakdown, dict):
            for key, val in sorted(breakdown.items()):
                cnt = int(val or 0)
                if cnt > 0:
                    detail_logs.append(f"[DISPLAY_REGEX_HEALER] {key}: +{cnt}")
    return total


def add_o1_fix(trace, detail_logs, message="[O(1)_HEALER] Intelligently scaled variables to force perfect division."):
    if not isinstance(trace, dict):
        trace = init_healer_trace({})
    trace["o1_fixes"] = int(trace.get("o1_fixes", 0) or 0) + 1
    if isinstance(detail_logs, list) and message:
        detail_logs.append(str(message))
    return int(trace["o1_fixes"])


def sanitize_result_question(exe_res, detail_logs=None, after_fallback=False, trace_seed=None):
    if not isinstance(exe_res, dict):
        return None, init_healer_trace(trace_seed, fixes_from_payload=0)
    if "question_text" not in exe_res:
        return None, init_healer_trace(trace_seed if isinstance(trace_seed, dict) else exe_res.get("healer_trace"), fixes_from_payload=0)

    sanitized_q, sanitize_report = sanitize_question_text_display(
        exe_res.get("question_text", ""),
        return_report=True,
    )
    exe_res["question_text"] = sanitized_q
    exe_res["_display_sanitize_report"] = sanitize_report

    trace = init_healer_trace(
        trace_seed if isinstance(trace_seed, dict) else exe_res.get("healer_trace"),
        fixes_from_payload=0,
    )
    logs = detail_logs if isinstance(detail_logs, list) else exe_res.setdefault("healer_logs", [])
    apply_sanitize_report_to_trace(trace, logs, sanitize_report, after_fallback=after_fallback)
    exe_res["healer_trace"] = trace
    return sanitize_report, trace


def format_result_question_display(
    exe_res,
    skill_id,
    display_mode="auto",
    source_text=None,
    detail_logs=None,
    trace_seed=None,
):
    if not isinstance(exe_res, dict):
        return None, init_healer_trace(trace_seed, fixes_from_payload=0)
    if "question_text" not in exe_res:
        return None, init_healer_trace(trace_seed if isinstance(trace_seed, dict) else exe_res.get("healer_trace"), fixes_from_payload=0)

    final_q, display_report = format_fraction_mixed_display(
        exe_res.get("question_text", ""),
        skill_id,
        display_mode=display_mode,
        source_text=source_text,
        return_report=True,
    )
    exe_res["question_text"] = final_q

    trace = init_healer_trace(
        trace_seed if isinstance(trace_seed, dict) else exe_res.get("healer_trace"),
        fixes_from_payload=0,
    )
    logs = detail_logs if isinstance(detail_logs, list) else exe_res.setdefault("healer_logs", [])
    apply_display_report_to_trace(trace, logs, display_report)
    exe_res["healer_trace"] = trace
    return display_report, trace


def recompute_result_answer(exe_res, skill_id, recompute_answer_fn=None, detail_logs=None, append_change_logs=False):
    if not isinstance(exe_res, dict):
        return None
    if "question_text" not in exe_res:
        exe_res["correct_answer"] = force_fraction_answer_text(exe_res.get("correct_answer", ""), skill_id)
        return exe_res.get("correct_answer")

    old_ans = exe_res.get("correct_answer", "")
    fixed_ans = recompute_answer_fn(exe_res.get("question_text", "")) if callable(recompute_answer_fn) else None
    if fixed_ans is not None:
        # [Bug 24 Guard] 整數技能（force_fraction_answer=False）時，若 recompute 結果為分數
        # （表示顯示字串與計算字串拓撲不一致），則拒絕覆蓋，保留腳本原來的整數答案。
        policy = get_skill_policy(skill_id)
        _is_fraction_result = "/" in str(fixed_ans) and not str(fixed_ans).startswith("-/")
        _force_frac = bool(policy.get("force_fraction_answer", False))
        if _is_fraction_result and not _force_frac:
            if append_change_logs and isinstance(detail_logs, list):
                detail_logs.append(
                    f"[ANS_GUARD][Bug24] 整數技能 recompute 得到分數 {fixed_ans!r}，"
                    f"疑似 eval_str/math_str 拓撲不一致，保留原答案 {old_ans!r}。"
                )
        else:
            exe_res["correct_answer"] = fixed_ans
            exe_res["_answer_recomputed"] = True
            if str(old_ans) != str(fixed_ans):
                exe_res["_answer_recomputed_from"] = str(old_ans)
                exe_res["_answer_recomputed_to"] = str(fixed_ans)

            if append_change_logs and isinstance(detail_logs, list):
                detail_logs.append("[ANS_GUARD] correct_answer recomputed from internal expression.")
                if str(old_ans) != str(fixed_ans):
                    detail_logs.append(f"[ANS_GUARD] correct_answer changed: {old_ans} -> {fixed_ans}")

    exe_res["correct_answer"] = force_fraction_answer_text(exe_res.get("correct_answer", ""), skill_id)
    return exe_res.get("correct_answer")


def maybe_add_o1_fix(exe_res, detail_logs=None, message="[O(1)_HEALER] Intelligently scaled variables to force perfect division.", trace_seed=None):
    if not isinstance(exe_res, dict) or not exe_res.get("_o1_healed"):
        return None

    trace = init_healer_trace(
        trace_seed if isinstance(trace_seed, dict) else exe_res.get("healer_trace"),
        fixes_from_payload=0,
    )
    logs = detail_logs if isinstance(detail_logs, list) else exe_res.setdefault("healer_logs", [])
    add_o1_fix(trace, logs, message=message)
    exe_res["healer_trace"] = trace
    return trace


def force_fraction_answer_text(answer_text, skill_id):
    policy = get_skill_policy(skill_id)
    if not bool(policy.get("force_fraction_answer", False)):
        return answer_text
    if answer_text is None:
        return answer_text
    s = str(answer_text).strip()
    if not s:
        return s
    if "/" in s:
        return s
    if re.fullmatch(r"[+-]?\d+", s):
        return f"{s}/1"
    return s
