# -*- coding: utf-8 -*-
"""Live Show 路由共用的數學結構/抽取工具（純函式）。"""

import re


def _normalize_math_text(text):
    if not text:
        return ""
    normalized = str(text)
    replacements = {
        "×": "*", "✕": "*", "\u00d7": "*", "\\times": "*",
        "÷": "/", "\u00f7": "/", "\\div": "/",
        "（": "(", "）": ")", "［": "[", "］": "]",
        "【": "[", "】": "]", "｛": "{", "｝": "}",
        "－": "-", "﹣": "-", "−": "-", "＋": "+", "｜": "|",
    }
    for src, dst in replacements.items():
        normalized = normalized.replace(src, dst)

    frac_pattern = r"\\frac\s*\{\s*([+-]?\d+)\s*\}\s*\{\s*([+-]?\d+)\s*\}"
    normalized = re.sub(frac_pattern, r"(\1/\2)", normalized)

    def _mixed_to_improper(match):
        sign_token = match.group('sign') or ''
        whole = int(match.group('whole'))
        num = int(match.group('num'))
        den = int(match.group('den'))
        if den == 0:
            return match.group(0)
        improper_num = whole * den + num
        return f"{sign_token}({improper_num}/{den})"

    mixed_pattern = r"(?<!\d)(?P<sign>[+-]?)\s*(?P<whole>\d+)\s+(?P<num>\d+)\s*/\s*(?P<den>\d+)(?!\d)"
    normalized = re.sub(mixed_pattern, _mixed_to_improper, normalized)

    mixed_compact_pattern = r"(?<![\d\)])(?P<sign>[+-]?)\s*(?P<whole>\d+)\s*\(\s*(?P<num>\d+)\s*/\s*(?P<den>\d+)\s*\)"
    normalized = re.sub(mixed_compact_pattern, _mixed_to_improper, normalized)
    return normalized


def _scan_number_spans(compact_expr):
    spans = []
    i = 0
    while i < len(compact_expr):
        ch = compact_expr[i]
        if ch.isdigit():
            j = i
            while j < len(compact_expr) and compact_expr[j].isdigit():
                j += 1
            if j < len(compact_expr) and compact_expr[j] == '.':
                k = j + 1
                while k < len(compact_expr) and compact_expr[k].isdigit():
                    k += 1
                if k > j + 1:
                    j = k
            spans.append((i, j, False))
            i = j
            continue

        if ch == '-' and i + 1 < len(compact_expr) and compact_expr[i + 1].isdigit():
            prev = compact_expr[i - 1] if i > 0 else ''
            unary = (i == 0 or prev in '([{|+*/')
            if unary:
                j = i + 1
                while j < len(compact_expr) and compact_expr[j].isdigit():
                    j += 1
                if j < len(compact_expr) and compact_expr[j] == '.':
                    k = j + 1
                    while k < len(compact_expr) and compact_expr[k].isdigit():
                        k += 1
                    if k > j + 1:
                        j = k
                spans.append((i, j, True))
                i = j
                continue
        i += 1
    return spans


def _count_binary_ops(compact_expr):
    sequence = []
    prev = ""
    for idx, ch in enumerate(compact_expr):
        if ch not in "+-*/":
            prev = ch
            continue

        is_unary_minus = ch == "-" and (idx == 0 or prev in "([{|+-*/")
        if is_unary_minus:
            prev = ch
            continue

        if ch == "+":
            sequence.append("plus")
        elif ch == "-":
            sequence.append("minus")
        elif ch == "*":
            sequence.append("times")
        elif ch == "/":
            sequence.append("divide")
        prev = ch
    counts = {
        "plus": sequence.count("plus"),
        "minus": sequence.count("minus"),
        "times": sequence.count("times"),
        "divide": sequence.count("divide"),
    }
    return sequence, counts


def _extract_enclosed_segments(compact_expr, left_ch, right_ch):
    segments = []
    stack = []
    for i, ch in enumerate(compact_expr):
        if ch == left_ch:
            stack.append(i)
        elif ch == right_ch and stack:
            start = stack.pop()
            if len(stack) == 0:
                segments.append(compact_expr[start + 1:i])
    return segments


def _extract_abs_segments(compact_expr):
    segments = []
    opens = []
    for i, ch in enumerate(compact_expr):
        if ch == '|':
            if opens:
                start = opens.pop()
                segments.append(compact_expr[start + 1:i])
            else:
                opens.append(i)
    return segments


def _segment_stats(segment_expr):
    seq, counts = _count_binary_ops(segment_expr)
    number_spans = _scan_number_spans(segment_expr)
    return {
        "numbers": len(number_spans),
        "ops": len(seq),
        "plus": counts["plus"],
        "minus": counts["minus"],
        "times": counts["times"],
        "divide": counts["divide"],
    }


def _build_structural_profile(text):
    norm = _normalize_math_text(text)
    compact = "".join(norm.split())
    sequence, counts = _count_binary_ops(compact)
    number_spans = _scan_number_spans(compact)

    bracket_segments = _extract_enclosed_segments(compact, '[', ']')
    brace_segments = _extract_enclosed_segments(compact, '{', '}')
    all_bracket_segments = bracket_segments + brace_segments

    abs_segments = _extract_abs_segments(compact)

    bracket_stats = [_segment_stats(seg) for seg in all_bracket_segments]
    abs_stats = [_segment_stats(seg) for seg in abs_segments]

    return {
        "normalized": compact,
        "operator_sequence": sequence,
        "operator_count": len(sequence),
        "counts": counts,
        "number_count": len(number_spans),
        "bracket_count": len(all_bracket_segments),
        "abs_count": len(abs_segments),
        "bracket_stats": bracket_stats,
        "abs_stats": abs_stats,
        "has_abs": len(abs_segments) > 0,
        "has_square_brackets": len(all_bracket_segments) > 0,
        "has_parentheses": "(" in compact and ")" in compact,
        "has_parenthesized_negative": "(-" in compact,
        "has_braces": len(brace_segments) > 0,
    }


def _extract_operator_fingerprint(text):
    return _build_structural_profile(text)


def _build_isomorphic_constraints(source_text, json_spec=None):
    fp = _build_structural_profile(source_text)
    seq_text = " -> ".join(fp["operator_sequence"]) if fp["operator_sequence"] else "none"
    forbidden_ops = [
        op for op in ("plus", "minus", "times", "divide")
        if fp["counts"].get(op, 0) == 0
    ]

    lines = [
        "【同構零容忍檢查清單】",
        f"1) 數字總數量必須嚴格一致：恰好 {fp['number_count']} 個參與計算的數字 (算式中出現幾個數字，你就只能宣告幾個變數)",
        f"2) 二元運算子總數必須嚴格一致：恰好 {fp['operator_count']} 個運算子",
        f"3) 運算子順序必須完全一致：{seq_text}",
        f"4) 運算子統計必須嚴格一致：+={fp['counts']['plus']}, -={fp['counts']['minus']}, ×={fp['counts']['times']}, ÷={fp['counts']['divide']}",
        "【重大警告】禁止擅自修改結構！如果生成的數字數量或運算子種類與上方統計不符，你的程式碼將被判定為嚴重失敗！"
    ]

    if fp["has_square_brackets"]:
        lines.append("\n5) 必須保留中括號結構 []，不得改成一般括號或移除。")
        lines.append(f"5.1) 中括號區塊數量必須一致：{fp['bracket_count']}")
        for idx, st in enumerate(fp["bracket_stats"], start=1):
            lines.append(
                f"5.{idx+1}) 第{idx}個中括號內：數字={st['numbers']}，運算子={st['ops']}（+{st['plus']}/-{st['minus']}/×{st['times']}/÷{st['divide']}）"
            )
    else:
        lines.append("\n5) 禁止新增中括號 []。")

    if fp["has_abs"]:
        lines.append("6) 必須保留絕對值符號 | |，不可省略。")
        lines.append(f"6.1) 絕對值區塊數量必須一致：{fp['abs_count']}")
        for idx, st in enumerate(fp["abs_stats"], start=1):
            lines.append(
                f"6.{idx+1}) 第{idx}個絕對值內：數字={st['numbers']}，運算子={st['ops']}（+{st['plus']}/-{st['minus']}/×{st['times']}/÷{st['divide']}）"
            )
    else:
        lines.append("6) 禁止新增絕對值符號 | | 或 abs()。")

    if fp["has_parenthesized_negative"]:
        lines.append("7) 負數必須以括號形式表達（例如 (-7)）。")
    else:
        lines.append("7) 不可為了湊格式而新增多餘的負數括號。")

    if forbidden_ops:
        lines.append(f"8) 禁止新增未出現的運算子：{', '.join(forbidden_ops)}")

    if json_spec and isinstance(json_spec, dict):
        structure = json_spec.get("structure") or ""
        if structure:
            lines.append(f"9) 參考結構：{structure}")

    block = "\n".join(lines)
    return block, fp


def _select_liveshow_structure_template(fp):
    if fp.get("has_abs"):
        template_id = "T3_ABS_MIXED"
        template_text = (
            f"題型骨架 T3（含絕對值，目標需恰好 {fp.get('number_count', 0)} 個數字）：| A op1 B | op2 C op3 D\n"
            "- 絕對值符號必須保留\n"
            "- 內外層運算子順序不可改\n"
            "- 負數格式必須使用 IntegerOps.fmt_num()\n"
            "【最高禁令】算式結構與數字個數必須100%同構，嚴禁增減任何變數或常數！"
        )
        return template_id, template_text

    if fp.get("has_square_brackets"):
        template_id = "T2_BRACKETED_NESTED"
        template_text = (
            f"題型骨架 T2（雙中括號，目標需恰好 {fp.get('number_count', 0)} 個數字）：[ ... ] op [ ... ]\n"
            "- 左右兩側都必須保留中括號\n"
            "- 中括號內可含小括號與多步運算\n"
            "- 最外層只允許原題出現的運算子\n"
            "【最高禁令】算式結構與數字個數必須100%同構，嚴禁增減任何變數或常數！"
        )
        return template_id, template_text

    template_id = "T1_LINEAR_MIXED"
    template_text = (
        f"題型骨架 T1（線性混合，目標需恰好 {fp.get('number_count', 0)} 個數字）：A op1 B op2 C ...\n"
        "- 不新增絕對值、不新增中括號\n"
        "- 僅保留原題已有的小括號樣式\n"
        "- 運算子序列與數量必須同構\n"
        "【最高禁令】算式結構與數字個數必須100%同構，嚴禁增減任何變數或常數！"
    )
    return template_id, template_text


def _extract_math_expr_from_question(question_text):
    if not question_text:
        return ""

    def _clean_candidate(expr):
        if expr is None:
            return ""
        out = str(expr).strip()
        out = out.strip('$').strip()
        out = re.sub(r'[。．\.?？]+$', '', out).strip()
        out = re.sub(r'^(?:計算|請計算|求)\s*', '', out).strip()
        out = re.sub(r'\s*(?:的值|等於多少|是多少)\s*$', '', out).strip()
        if '=' in out:
            out = out.split('=', 1)[0].strip()
        if out and out[0] in '+*/':
            out = out[1:].strip()
        return out

    text = str(question_text).strip()
    m = re.search(r'\$(.*?)\$', text)
    if m:
        return _clean_candidate(m.group(1))

    m2 = re.search(r'計算\s*(.+?)\s*(?:的值|等於多少|是多少)\s*[。\.?？]?$', text)
    if m2:
        return _clean_candidate(m2.group(1))

    return _clean_candidate(text)


def _to_eval_expression_template(expr):
    temp = re.sub(r'\{v(\d+)\}', r'__V\1__', expr or "")

    norm = _normalize_math_text(temp)
    compact = "".join(norm.split())

    compact = compact.replace('\\left', '').replace('\\right', '').replace('\\text', '')
    compact = compact.replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")

    out = []
    abs_open = False
    for ch in compact:
        if ch == '|':
            if not abs_open:
                out.append('abs(')
                abs_open = True
            else:
                out.append(')')
                abs_open = False
        else:
            out.append(ch)

    if abs_open:
        out.append(')')

    final_expr = "".join(out)
    final_expr = final_expr.strip().strip('$').strip()
    final_expr = re.sub(r'[。．\.?？]+$', '', final_expr).strip()
    if '=' in final_expr:
        final_expr = final_expr.split('=', 1)[0].strip()
    if final_expr and final_expr[0] in '+*/':
        final_expr = final_expr[1:].strip()

    atom = r'(?:__V\d+__|-?\d+)'
    frac_pat = rf'(?<![\w\)])({atom})/({atom})(?![\w\(])'
    for _ in range(8):
        final_expr, n = re.subn(frac_pat, r'(\1/\2)', final_expr)
        if n == 0:
            break

    final_expr = re.sub(r'__V(\d+)__', r'{v\1}', final_expr)
    return final_expr


def _recompute_correct_answer_from_question(question_text):
    from fractions import Fraction

    expr = _extract_math_expr_from_question(question_text)
    if not expr:
        return None

    eval_expr = _to_eval_expression_template(expr)
    if not re.fullmatch(r"[0-9+\-*/().aabs]+", eval_expr):
        return None

    try:
        val = eval(eval_expr, {"__builtins__": {}}, {"abs": abs})
    except Exception:
        return None

    try:
        fval = Fraction(val).limit_denominator()
    except Exception:
        try:
            fval = Fraction(str(val)).limit_denominator()
        except Exception:
            return None

    if fval.denominator == 1:
        return str(fval.numerator)
    return f"{fval.numerator}/{fval.denominator}"


def _is_expression_isomorphic(expected_fp, generated_expr):
    if not generated_expr:
        return False
    # Empty fingerprint = bypass mode (radical orchestrator, OCR-less path, etc.)
    # All fields default to None; comparing None against real values always returns
    # False — treating an empty dict as "no constraints" is the correct semantic.
    if not expected_fp:
        return True
    got_fp = _build_structural_profile(generated_expr)
    if got_fp.get("operator_sequence") != expected_fp.get("operator_sequence"):
        return False
    if got_fp.get("number_count") != expected_fp.get("number_count"):
        return False
    if got_fp.get("counts") != expected_fp.get("counts"):
        return False
    if got_fp.get("has_abs") != expected_fp.get("has_abs"):
        return False
    if got_fp.get("has_square_brackets") != expected_fp.get("has_square_brackets"):
        return False
    if got_fp.get("abs_count") != expected_fp.get("abs_count"):
        return False
    if got_fp.get("bracket_count") != expected_fp.get("bracket_count"):
        return False
    if got_fp.get("bracket_stats") != expected_fp.get("bracket_stats"):
        return False
    if got_fp.get("abs_stats") != expected_fp.get("abs_stats"):
        return False
    return True


def _profile_diff_summary(expected_fp, generated_expr):
    got_fp = _build_structural_profile(generated_expr or "")
    diffs = []

    if got_fp.get("operator_sequence") != expected_fp.get("operator_sequence"):
        diffs.append(f"operator_sequence: expected={expected_fp.get('operator_sequence')} got={got_fp.get('operator_sequence')}")
    if got_fp.get("number_count") != expected_fp.get("number_count"):
        diffs.append(f"number_count: expected={expected_fp.get('number_count')} got={got_fp.get('number_count')}")
    if got_fp.get("counts") != expected_fp.get("counts"):
        diffs.append(f"op_counts: expected={expected_fp.get('counts')} got={got_fp.get('counts')}")
    if got_fp.get("bracket_count") != expected_fp.get("bracket_count"):
        diffs.append(f"bracket_count: expected={expected_fp.get('bracket_count')} got={got_fp.get('bracket_count')}")
    if got_fp.get("abs_count") != expected_fp.get("abs_count"):
        diffs.append(f"abs_count: expected={expected_fp.get('abs_count')} got={got_fp.get('abs_count')}")
    if got_fp.get("bracket_stats") != expected_fp.get("bracket_stats"):
        diffs.append("bracket_stats mismatch")
    if got_fp.get("abs_stats") != expected_fp.get("abs_stats"):
        diffs.append("abs_stats mismatch")

    return diffs


# ===========================================================================
# Radical Math DNA — specialised profiler for jh_數學2上_FourOperationsOfRadicals
# ===========================================================================

def _has_square_factor(n: int) -> bool:
    """Return True if integer n contains a perfect-square factor > 1.

    A radicand is *simplifiable* when it is not in its simplest radical form,
    e.g. 12 = 4×3 → √12 = 2√3.  Prime radicands (2, 3, 5, 7, …) are already
    in simplest form and return False.
    """
    if not isinstance(n, int) or n < 4:
        return False
    i = 2
    while i * i <= n:
        if n % (i * i) == 0:
            return True
        i += 1
    return False


def _frac_denominators(text: str) -> list:
    """Return a list of denominator strings from all \\frac{}{} / \\dfrac{}{} in *text*.

    Uses brace-depth tracking so nested LaTeX constructs are handled correctly.
    """
    # Normalise \dfrac → \frac so a single pass suffices.
    normalised = text.replace(r'\dfrac{', r'\frac{')
    denoms: list = []
    i = 0
    while i < len(normalised):
        pos = normalised.find(r'\frac{', i)
        if pos == -1:
            break
        j = pos + 6  # step past '\frac{'
        # Walk over the numerator brace
        depth = 1
        while j < len(normalised) and depth > 0:
            if normalised[j] == '{':
                depth += 1
            elif normalised[j] == '}':
                depth -= 1
            j += 1
        # Skip optional whitespace between } and {
        while j < len(normalised) and normalised[j] in ' \t\n':
            j += 1
        if j >= len(normalised) or normalised[j] != '{':
            i = pos + 1
            continue
        j += 1  # step past opening '{' of denominator
        denom_start = j
        depth = 1
        while j < len(normalised) and depth > 0:
            if normalised[j] == '{':
                depth += 1
            elif normalised[j] == '}':
                depth -= 1
            j += 1
        denoms.append(normalised[denom_start: j - 1])
        i = pos + 1
    return denoms


def _build_radical_profile(latex_text: str) -> dict:
    """Extract the *Radical Math DNA* fingerprint from a LaTeX question string.

    Returns a dict with:
        rad_count          — total number of \\sqrt{N} tokens (integer radicands)
        simplifiable_count — how many of those radicands contain a square factor
        rationalize_count  — number of \\frac / \\dfrac whose denominator holds a \\sqrt
        radicands          — the list of integer radicands found (preserves duplicates)

    Example
    -------
    ``$2\\sqrt{3} + \\sqrt{12}$``
        → {'rad_count': 2, 'simplifiable_count': 1,
           'rationalize_count': 0, 'radicands': [3, 12]}

    ``$\\dfrac{5}{\\sqrt{3}}$``
        → {'rad_count': 1, 'simplifiable_count': 0,
           'rationalize_count': 1, 'radicands': [3]}
    """
    text = str(latex_text or '')

    # Only integer radicands are relevant for junior-high radical problems.
    sqrt_matches = re.findall(r'\\sqrt\{(\d+)\}', text)
    radicands = [int(m) for m in sqrt_matches]

    rad_count          = len(radicands)
    simplifiable_count = sum(1 for r in radicands if _has_square_factor(r))

    denoms             = _frac_denominators(text)
    rationalize_count  = sum(1 for d in denoms if r'\\sqrt' in d or '\\sqrt' in d)

    return {
        'rad_count':          rad_count,
        'simplifiable_count': simplifiable_count,
        'rationalize_count':  rationalize_count,
        'radicands':          radicands,
    }


def _is_radical_isomorphic(target_rp: dict, generated_text: str) -> bool:
    """Return True when *generated_text* matches the *target_rp* radical profile.

    Strict fields: rad_count, simplifiable_count.
    rationalize_count is intentionally advisory (not checked here) to avoid
    over-constraining patterns whose denominator style can vary.
    """
    if not generated_text:
        return False
    gen_rp = _build_radical_profile(generated_text)
    if gen_rp['rad_count'] != target_rp.get('rad_count', -1):
        return False
    if gen_rp['simplifiable_count'] != target_rp.get('simplifiable_count', -1):
        return False
    return True


def _radical_profile_diff(target_rp: dict, generated_text: str) -> list:
    """Return human-readable diff strings for every mismatched radical profile field."""
    gen_rp = _build_radical_profile(generated_text or '')
    diffs = []
    for field in ('rad_count', 'simplifiable_count', 'rationalize_count'):
        exp = target_rp.get(field)
        got = gen_rp.get(field)
        if exp is not None and exp != got:
            diffs.append(f"{field}: expected={exp} got={got}")
    return diffs
