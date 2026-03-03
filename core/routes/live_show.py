# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱 (Module Name): core/routes/live_show.py
功能說明 (Description): 科展 Live Show 專用路由。
  GET  /live_show              — 渲染前端 HTML 頁面
  POST /api/generate_live      — Ab1 / Ab3 平行生成（JSON 回傳）
  GET  /api/stream_thought_ab1 — Ab1 思考過程即時串流 (Server-Sent Events)
=============================================================================
"""

from flask import request, jsonify, render_template, Response, stream_with_context, current_app
import time
import json
import os
import base64
import uuid
from PIL import Image  # 新增：用於處理影像對象
import io             # 新增：用於 Base64 轉換
import requests       # 確保網路模組為檔案域全域可用
from config import Config # 新增：供 Qwen3-VL 讀取模型參數
# (舊有 Pix2Text 套件已移除，OCR 全權交由 Qwen3-VL 處理)

# 從 __init__.py 匯入已註冊的 Blueprint
from . import live_show_bp

# 全局初始化 MathEngine (延遲載入以避免循環引用)
_engine_instance = None
def get_engine():
    global _engine_instance
    if _engine_instance is None:
        from core.engine.engine import MathEngine
        _engine_instance = MathEngine()
    return _engine_instance


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
    # 新增：也抓取大括號 {} 區塊併入統計（或可獨立統計，但通常視為高等級括號）
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
        f"1) 運算子順序必須完全一致：{seq_text}",
        f"2) 二元運算子總數必須一致：{fp['operator_count']}",
        f"2.1) 數字總數必須一致：{fp['number_count']}",
        f"2.2) 加減乘除統計必須一致：+={fp['counts']['plus']}, -={fp['counts']['minus']}, ×={fp['counts']['times']}, ÷={fp['counts']['divide']}",
    ]

    if fp["has_square_brackets"]:
        lines.append("3) 必須保留中括號結構 []，不得改成一般括號或移除。")
        lines.append(f"3.1) 中括號區塊數量必須一致：{fp['bracket_count']}")
        for idx, st in enumerate(fp["bracket_stats"], start=1):
            lines.append(
                f"3.{idx+1}) 第{idx}個中括號內：數字={st['numbers']}，運算子={st['ops']}（+{st['plus']}/-{st['minus']}/×{st['times']}/÷{st['divide']}）"
            )
    else:
        lines.append("3) 禁止新增中括號 []。")

    if fp["has_abs"]:
        lines.append("4) 必須保留絕對值符號 | |，不可省略。")
        lines.append(f"4.1) 絕對值區塊數量必須一致：{fp['abs_count']}")
        for idx, st in enumerate(fp["abs_stats"], start=1):
            lines.append(
                f"4.{idx+1}) 第{idx}個絕對值內：數字={st['numbers']}，運算子={st['ops']}（+{st['plus']}/-{st['minus']}/×{st['times']}/÷{st['divide']}）"
            )
    else:
        lines.append("4) 禁止新增絕對值符號 | | 或 abs()。")

    if fp["has_parenthesized_negative"]:
        lines.append("5) 負數必須以括號形式表達（例如 (-7)）。")
    else:
        lines.append("5) 不可為了湊格式而新增多餘的負數括號。")

    if forbidden_ops:
        lines.append(f"6) 禁止新增未出現的運算子：{', '.join(forbidden_ops)}")

    if json_spec and isinstance(json_spec, dict):
        structure = json_spec.get("structure") or ""
        if structure:
            lines.append(f"7) 參考結構：{structure}")

    block = "\n".join(lines)
    return block, fp


def _select_liveshow_structure_template(fp):
    if fp.get("has_abs"):
        template_id = "T3_ABS_MIXED"
        template_text = (
            "題型骨架 T3（含絕對值）：| A op1 B | op2 C op3 D\n"
            "- 絕對值符號必須保留\n"
            "- 內外層運算子順序不可改\n"
            "- 負數格式必須使用 IntegerOps.fmt_num()"
        )
        return template_id, template_text

    if fp.get("has_square_brackets"):
        template_id = "T2_BRACKETED_NESTED"
        template_text = (
            "題型骨架 T2（雙中括號巢狀）：[ ... ] op [ ... ]\n"
            "- 左右兩側都必須保留中括號\n"
            "- 中括號內可含小括號與多步運算\n"
            "- 最外層只允許原題出現的運算子"
        )
        return template_id, template_text

    template_id = "T1_LINEAR_MIXED"
    template_text = (
        "題型骨架 T1（線性混合）：A op1 B op2 C ...\n"
        "- 不新增絕對值、不新增中括號\n"
        "- 僅保留原題已有的小括號樣式\n"
        "- 運算子序列與數量必須同構"
    )
    return template_id, template_text


def _extract_math_expr_from_question(question_text):
    if not question_text:
        return ""
    import re
    m = re.search(r'\$(.*?)\$', str(question_text))
    if m:
        return m.group(1).strip()
    return str(question_text).strip()

def _to_eval_expression_template(expr):
    import re
    # 預保護修補：暫時隱藏 f-string 佔位符 {v1}, {v2}... 避免被誤轉
    temp = re.sub(r'\{v(\d+)\}', r'__V\1__', expr or "")
    
    norm = _normalize_math_text(temp)
    compact = "".join(norm.split())

    # 1. 移除不影響數學結構但干擾演算的排版 LaTeX 指令
    compact = compact.replace('\\left', '').replace('\\right', '').replace('\\text', '')
    # 2. 將所有類括號統一轉為圓括號 (此時大括號只剩數學大括號)
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
    # 3. 還原 f-string 佔位符
    final_expr = re.sub(r'__V(\d+)__', r'{v\1}', final_expr)
    return final_expr


def _recompute_correct_answer_from_question(question_text):
    import re
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
        fval = float(val)
    except Exception:
        return None

    if abs(fval - round(fval)) < 1e-6:
        return str(int(round(fval)))
    return str(fval)


def _collapse_double_numeric_parentheses(expr_text):
    import re
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


def _enforce_negative_parentheses(expr_text):
    """
    將顯示算式中的「單元負數常數」統一為括號格式：
    -3 -> (-3)
    但已經是 (-3) 的不重複包裝。
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


def _sanitize_question_text_display(question_text, return_report=False):
    import re
    if not question_text:
        return (question_text, {"double_paren_fixes": 0}) if return_report else question_text

    text = str(question_text)
    m = re.search(r'\$(.*?)\$', text)
    total_fixes = 0
    total_neg_wraps = 0
    if m:
        inner = m.group(1)
        fixed_inner, fix_count = _collapse_double_numeric_parentheses(inner)
        total_fixes += fix_count
        fixed_inner_2, wrap_count = _enforce_negative_parentheses(fixed_inner)
        total_neg_wraps += wrap_count
        sanitized = text[:m.start(1)] + fixed_inner_2 + text[m.end(1):]
    else:
        sanitized, fix_count = _collapse_double_numeric_parentheses(text)
        total_fixes += fix_count
        sanitized, wrap_count = _enforce_negative_parentheses(sanitized)
        total_neg_wraps += wrap_count

    if return_report:
        return sanitized, {
            "double_paren_fixes": total_fixes,
            "negative_wrap_fixes": total_neg_wraps,
        }
    return sanitized


def _optimize_live_execution_code(code_text):
    """
    Live Show 執行優化：
    - 壓低超大重試迴圈上限，避免 CPU latency 被 3000+ 次重試拖高
    - 去除 time.sleep 人為延遲
    """
    import re

    code = code_text or ""

    def _shrink_for_range(m):
        var_name = m.group(1)
        n = int(m.group(2))
        capped = 120 if n > 120 else n
        return f"for {var_name} in range({capped})"

    code = re.sub(
        r"for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+range\((\d{3,6})\)",
        _shrink_for_range,
        code,
    )

    def _cap_while_limit(m):
        prefix = m.group(1)
        n = int(m.group(2))
        capped = 120 if n > 120 else n
        return f"{prefix}{capped}"

    code = re.sub(
        r"(while\s+[A-Za-z_][A-Za-z0-9_]*\s*<\s*)(\d{3,6})",
        _cap_while_limit,
        code,
    )

    code = re.sub(r"\btime\.sleep\s*\([^\)]*\)", "pass", code)
    return code


def _is_expression_isomorphic(expected_fp, generated_expr):
    if not generated_expr:
        return False
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


def _build_isomorphic_fallback_code(ocr_text):
    norm = _normalize_math_text(ocr_text)
    compact = "".join(norm.split())

    spans = _scan_number_spans(compact)

    if not spans:
        return ""

    eval_parts = []
    math_parts = []
    cursor = 0
    idx = 1
    var_specs = []
    for start, end, unary_minus in spans:
        left = compact[cursor:start]
        # 轉義大括號，避免干擾後續生成的 f-string 佔位符
        left_escaped = left.replace("{", "{{").replace("}", "}}")
        
        token = compact[start:end]
        eval_parts.append(left_escaped)
        math_parts.append(left_escaped)

        var_name = f"v{idx}"
        eval_parts.append("{" + var_name + "}")
        wrapped = (start - 1 >= 0 and end < len(compact) and compact[start - 1] == '(' and compact[end] == ')')
        source_negative = token.startswith('-')

        if wrapped:
            math_parts.append("{" + var_name + "}")
        else:
            math_parts.append("{fmt(" + var_name + ")}")

        var_specs.append((var_name, source_negative))

        cursor = end
        idx += 1

    tail = compact[cursor:]
    tail_escaped = tail.replace("{", "{{").replace("}", "}}")
    eval_parts.append(tail_escaped)
    math_parts.append(tail_escaped)

    eval_template = "".join(eval_parts)
    math_template = "".join(math_parts)
    math_template = math_template.replace("\\", "\\\\").replace("*", "\\\\times").replace("/", "\\\\div")
    eval_template = _to_eval_expression_template(eval_template)
    eval_template = eval_template.replace("\\", "\\\\")

    assign_lines = ["        vars_dict = {}"]
    for i, (var_name, source_negative) in enumerate(var_specs):
        if i == 0:
            vmin, vmax = 1, 200
        elif i == 1:
            vmin, vmax = 1, 10
        elif i == 2:
            vmin, vmax = 1, 20
        else:
            vmin, vmax = 1, 15
            
        if source_negative:
            assign_lines.append(f"        vars_dict['{var_name}'] = IntegerOps.random_nonzero(-{vmax}, -{vmin})")
        else:
            assign_lines.append(f"        vars_dict['{var_name}'] = IntegerOps.random_nonzero({vmin}, {vmax})")

    assign_block = "\n".join(assign_lines)

    code = f'''import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    last_ans = None
    last_math_str = None
    
    for attempt in range(25):
{assign_block}
        _o1_healed = False

        # 智慧型倒算法 (Intelligent Reverse Calculation) 的結構同構攔截與縮放
        try:
            eval_str_init = "{eval_template}"
            
            # 使用 Fraction 強制保留精確分母
            for k, v in vars_dict.items():
                key1 = chr(123) + k + chr(125)
                key2 = chr(123) + "fmt(" + k + ")" + chr(125)
                frac_str = "Fraction(" + str(v) + ", 1)"
                eval_str_init = eval_str_init.replace(key1, frac_str)
                eval_str_init = eval_str_init.replace(key2, frac_str)
                
            ans_init = safe_eval(eval_str_init)
            
            # 若第一波計算產生分數，代表存在除法截斷。
            # 直接將結構中的「第一個變數」乘上分母，強制使得整組式中存在能夠被整除的公倍數，實現完美的 O(1) 倒算法！
            if type(ans_init).__name__ == "Fraction" and ans_init.denominator != 1:
                # [保護機制] 如果隨機出的分母過大（例如幾百萬），乘回 v1 會導致出現天文數字。
                # 國中範圍的分母通常在 1000 以內。超過 1000 直接拒絕，讓外層迴圈重新隨機洗牌。
                if ans_init.denominator > 1000:
                    continue
                    
                # 取得第一個生成的變數名 (例如 v1) 並將它乘上剛剛算出來的分母
                first_var = "{var_specs[0][0]}" if {len(var_specs)} > 0 else None
                if first_var:
                    vars_dict[first_var] = vars_dict[first_var] * ans_init.denominator
                    _o1_healed = True
                    
            # 變數縮放完成後，重新組裝字串與算式
            eval_str = "{eval_template}"
            math_str = "{math_template}"
            
            for k, v in vars_dict.items():
                key1 = chr(123) + k + chr(125)
                key2 = chr(123) + "fmt(" + k + ")" + chr(125)
                
                # 最終答案計算也用 Fraction 以確保絕對精確
                frac_str = "Fraction(" + str(v) + ", 1)"
                eval_str = eval_str.replace(key1, frac_str)
                eval_str = eval_str.replace(key2, frac_str)
                
                math_str = math_str.replace(key1, str(v))
                math_str = math_str.replace(key2, IntegerOps.fmt_num(v))
                
            ans = safe_eval(eval_str)
            
            last_ans = ans
            last_math_str = math_str
            
            if type(ans).__name__ == "Fraction":
                if ans.denominator == 1:
                    return {{
                        'question_text': "計算 $" + math_str + "$ 的值。",
                        'correct_answer': str(ans.numerator),
                        'mode': 1,
                        '_o1_healed': _o1_healed
                    }}
            elif abs(ans - round(ans)) < 1e-6:
                return {{
                    'question_text': "計算 $" + math_str + "$ 的值。",
                    'correct_answer': str(int(round(ans))),
                    'mode': 1,
                    '_o1_healed': _o1_healed
                }}
            
        except Exception:
            import traceback
            traceback.print_exc()
            continue
            
    # 如果極端情況 25 次都找不到，退避到最後一次結果
    if last_ans is not None:
        if type(last_ans).__name__ == "Fraction":
            if last_ans.denominator == 1:
                final_ans = str(last_ans.numerator)
            else:
                final_ans = f"{{last_ans.numerator}}/{{last_ans.denominator}}"
        else:
            final_ans = f"{{last_ans:.2f}}"
        return {{
            'question_text': "計算 $" + last_math_str + "$ 的值。",
            'correct_answer': final_ans,
            'mode': 1,
            '_o1_healed': False
        }}

        
    return {{'question_text': 'Error', 'correct_answer': '0', 'mode': 1}}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {{'correct': True, 'result': '正確'}}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6:
            return {{'correct': True, 'result': '正確'}}
    except Exception:
        pass
    return {{'correct': False, 'result': '錯誤'}}
'''
    return code


def apply_strict_mirroring(scaffold, ocr_text):
    """
    更強力的過濾器：只要沒出現符號，就刪除整行包含關鍵字的指令
    """
    # 定義符號與必須刪除的關鍵字
    guards = {
        "|": ["絕對值", "Absolute Value", "abs("],
        "[": ["中括號", "bracket", "Level 2"],
        "^": ["次方", "指數", "Level 3", "高難度"]
    }

    lines = scaffold.split('\n')
    cleaned_lines = []

    for line in lines:
        should_remove = False
        for symbol, keywords in guards.items():
            # 如果圖片裡沒這個符號，且這行含有相關關鍵字
            if symbol not in ocr_text:
                if any(kw in line for kw in keywords):
                    should_remove = True
                    break
        
        if not should_remove:
            cleaned_lines.append(line)

    # 重新組裝並加上強制同構命令
    final_output = '\n'.join(cleaned_lines)
    
    # 針對你的個案：如果沒看到絕對值，直接把【任務】那一行強制改掉
    if "|" not in ocr_text:
        final_output = final_output.replace(
            "題目結構必須為：括號內混合運算 + 絕對值 + (Level 3: 高難度多層混和)",
            "題目結構必須與【參考例題】完全相同，嚴禁增加額外運算（如絕對值）。"
        )
    
    return final_output


@live_show_bp.route('/live_show')
def live_show():
    """渲染 Live Show 的前端展示頁面"""
    return render_template('live_show.html')


@live_show_bp.route('/api/generate_live', methods=['POST'])
def generate_live():
    """
    API: 根據 ablation_mode 生產題目與 debug_meta 資訊
    前端會在同時間對此打兩支平行連線 (Ab1 與 Ab3)
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No JSON payload provided."}), 400
        
    input_text = data.get("prompt") or data.get("input_text", "")
    ablation_mode = data.get("ablation_mode", False)
    count = data.get("count", 1)
    model_id = data.get("model_id", "qwen3-8b")
    skill_id = data.get("skill_id")
    
    start_time = time.time()
    try:
        image_data = data.get("image_data")
        json_spec = data.get("json_spec", {})
        
        if skill_id == "Unknown":
            return jsonify({
                "success": False,
                "error": "Cannot generate code for Unknown skill. Please try another image or clearer prompt.",
                "debug_meta": {
                    "latency_ms": int((time.time() - start_time) * 1000),
                    "healer_fix_count": 0,
                    "MCRI_score": 0,
                    "architect_model": "None"
                }
            }), 400
        
        if image_data and not ablation_mode:
            print(">>> 👁️ 觸發 Monolithic Multimodal Brain (Qwen3-VL 代碼生成)")
            import re
            image_data = re.sub(r'^data:image/.+;base64,', '', image_data)
                
            from core.engine.scaler import AdaptiveScaler
            scaler = AdaptiveScaler()
            
            # 1. 取得技能知識與模板
            skill_path = scaler._get_skill_path(skill_id)
            skill_md_path = os.path.join(skill_path, "SKILL.md")
            with open(skill_md_path, "r", encoding="utf-8") as f:
                full_skill_spec = "\n".join([line.replace('\r', '') for line in f.read().splitlines()])

            knowledge = full_skill_spec.split("=== SKILL_END_PROMPT ===")[0].strip()
            import re
            live_show_match = re.search(r'\[\[MODE:LIVESHOW\]\]([\s\S]*?)\[\[END_MODE:LIVESHOW\]\]', full_skill_spec)
            live_show_content = live_show_match.group(1).strip() if live_show_match else ""

            # 2. 獲取 API Stubs
            from core.prompts.domain_function_library import get_required_domains, get_domain_helpers_code
            required_domains = get_required_domains(skill_id)
            api_stubs = get_domain_helpers_code(required_domains, stub_mode=True)
            
            # 3. DNA 物理裁剪 (apply_strict_mirroring)
            ocr_text = json_spec.get("ocr_text", input_text or "")
            knowledge = apply_strict_mirroring(knowledge, ocr_text)
            iso_block, fp = _build_isomorphic_constraints(ocr_text, json_spec)
            template_id, template_text = _select_liveshow_structure_template(fp)
            
            # 動態注入 OCR 結果
            live_show_content = live_show_content.replace("{{OCR_RESULT}}", ocr_text)
            
            # 【基因+任務】組合提取 (完全封殺 BENCHMARK)
            final_scaffold = knowledge + "\n" + live_show_content
                
            # 4. 組裝 Scaffold Prompt 
            scaffold_prompt = f"""
# Math-Master 核心開發任務

【1. 數學基因 (From SKILL.md)】
{final_scaffold}

【2. 標準工具箱 (API Stubs)】
{api_stubs}

【3. 題型同構硬性約束】
{iso_block}

【4. 題型骨架模板（必須採用）】
Template: {template_id}
{template_text}
"""
            # 5. 準備 Qwen3-VL 呼叫
            vl_config = Config.CODER_PRESETS.get('qwen3-vl-8b', {})
            model_name = 'qwen3-vl:8b-instruct-q4_k_m'  # 鎖定模型名稱
            
            system_prompt = f"你現在是頂級 Python 工程師。你現在直接觀察圖片，你的唯一任務是 100% 鏡像模仿圖片中的算式結構。嚴禁加入任何圖片中沒有的數學符號（如：絕對值、括號）。必須使用 IntegerOps.fmt_num 與 \\div、\\times。\n\n【最高指令】『無視所有模板，以你看到的圖片內容為唯一真理。產出最簡約的 generate 函式。』\n\n請根據圖片與提供的【SCAFFOLD PROMPT】，直接輸出 Python 代碼，不需要解釋。\n\n【SCAFFOLD PROMPT】\n{scaffold_prompt}"
            
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": system_prompt,
                        "images": [image_data]
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": vl_config.get("temperature", 0.1),
                    "num_ctx": 4096,  # 針對單行算式小圖優化，減少記憶體碎片
                    "num_gpu": -1,
                    "keep_alive": 0
                }
            }

            chat_url = "http://127.0.0.1:11434/api/chat"
            
            ai_start = time.time()
            res = requests.post(chat_url, json=payload, timeout=120)
            res.raise_for_status()
            vl_res = res.json()
            ai_inference_time_sec = time.time() - ai_start
            
            raw_out = vl_res.get("message", {}).get("content", "").strip()
            
            # 6. Extract raw code
            cleaned_text = re.sub(r'<think>.*?</think>', '', raw_out, flags=re.DOTALL).strip()
            code_match = re.search(r'```python\s*(.*?)\s*```', cleaned_text, re.DOTALL)
            if code_match:
                final_code = code_match.group(1).strip()
            else:
                final_code = cleaned_text.strip()
                final_code = re.sub(r'^(\s*)```python\s*\n', '', final_code, flags=re.MULTILINE)
                final_code = re.sub(r'^(\s*)```\s*\n', '', final_code, flags=re.MULTILINE)
                final_code = re.sub(r'\n(\s*)```\s*$', '', final_code, flags=re.MULTILINE)
                
            # 7. Execute Code to get output dict identical to `scaler.py` format
            cpu_start = time.time()
            expected_fp = _build_structural_profile(ocr_text)
            generated_fp = {}
            iso_isomorphic = False
            ab2_exec_code = _optimize_live_execution_code(final_code)
            
            # --- [NEW] Ab2 Interception (Scaffold Prompt, No Healer) ---
            ab2_result = {}
            ab2_save_dir = "generated_scripts"
            if not os.path.exists(ab2_save_dir):
                os.makedirs(ab2_save_dir, exist_ok=True)
            ab2_filename = f"live_show_{int(time.time())}_{uuid.uuid4().hex[:6]}_ab2.py"
            ab2_file_path = os.path.join(ab2_save_dir, ab2_filename)
            with open(ab2_file_path, "w", encoding="utf-8") as _fb:
                _fb.write(final_code)
                
            ab2_cpu_start = time.time()
            try:
                ab2_exe_res = scaler._execute_code(ab2_exec_code, level=1)
                ab2_exec_elapsed = time.time() - ab2_cpu_start
                if "question_text" in ab2_exe_res:
                    sanitized_q, sanitize_report = _sanitize_question_text_display(
                        ab2_exe_res.get("question_text", ""),
                        return_report=True
                    )
                    ab2_exe_res["question_text"] = sanitized_q
                    ab2_exe_res["_display_sanitize_report"] = sanitize_report
                if "question_text" in ab2_exe_res:
                    old_ans = ab2_exe_res.get("correct_answer", "")
                    fixed_ans = _recompute_correct_answer_from_question(ab2_exe_res.get("question_text", ""))
                    if fixed_ans is not None:
                        ab2_exe_res["correct_answer"] = fixed_ans
                        ab2_exe_res["_answer_recomputed"] = True
                        if str(old_ans) != str(fixed_ans):
                            ab2_exe_res["_answer_recomputed_from"] = str(old_ans)
                            ab2_exe_res["_answer_recomputed_to"] = str(fixed_ans)
                try:
                    from scripts.evaluate_mcri import evaluate_math_hygiene
                    if "question_text" in ab2_exe_res:
                        h_score, _ = evaluate_math_hygiene(ab2_exe_res["question_text"])
                        ab2_exe_res["_mcri_hygiene_score"] = h_score
                except:
                    pass
                if ab2_exe_res.get("_o1_healed"):
                    ab2_exe_res.setdefault("healer_trace", {"regex_fixes": 0, "ast_fixes": 0})
                    ab2_exe_res["healer_trace"]["ast_fixes"] += 1
                    ab2_exe_res.setdefault("healer_logs", [])
                    ab2_exe_res["healer_logs"].append("[O(1)_HEALER] Intelligently scaled variables to force perfect division (Native).")
                ab2_result = ab2_exe_res
            except Exception as e:
                ab2_exec_elapsed = time.time() - ab2_cpu_start
                ab2_result = {"error": f"執行錯誤: {e}"}
            
            ab2_result["file_path"] = ab2_file_path
            ab2_result["ai_inference_time_sec"] = ai_inference_time_sec
            ab2_result["cpu_execution_time_sec"] = ab2_exec_elapsed
            
            # [NEW] Prepend api_stubs to BOTH final executed code AND the raw code shown on UI
            final_code_with_stubs = api_stubs + "\n\n" + final_code
            ab2_result["raw_code"] = final_code_with_stubs
            ab2_result["final_code"] = final_code_with_stubs # no healer applied
            
            # --- Resume Ab3 (Full Healer) ---
            # Ab3 CPU time = Healer + Execution (must always be ≥ Ab2)
            cpu_start_ab3 = time.time()
            problems_result = []
            ab3_exec_elapsed = 0.0
            
            # [FIX] 真正執行 Healer，讓 Ab3 擁有自癒能力
            from core.code_generator import _advanced_healer
            healed_code = final_code
            regex_fixes = 0
            ast_fixes = 0
            try:
                healed_code, *healer_stats = _advanced_healer(final_code, ablation_id=3, skill_id=skill_id)
                # 提取修復次數
                regex_fixes = healer_stats[0] if len(healer_stats) > 0 else 0
                ast_fixes = healer_stats[1] if len(healer_stats) > 1 else 0
                ast_stats = healer_stats[2] if len(healer_stats) > 2 else None
                detail_logs = getattr(ast_stats, "logs", []) if ast_stats else []
                print(f"=== [VL Pipeline Healer] Success! Regex: {regex_fixes}, AST: {ast_fixes} ===")
            except Exception as e:
                import traceback
                print(f"=== [VL Pipeline Healer] CRASHED ===")
                traceback.print_exc()
                healed_code = final_code
            
            try:
                healed_exec_code = _optimize_live_execution_code(healed_code)
                exe_res = scaler._execute_code(healed_exec_code, level=1)
                if "question_text" in exe_res:
                    sanitized_q, sanitize_report = _sanitize_question_text_display(
                        exe_res.get("question_text", ""),
                        return_report=True
                    )
                    exe_res["question_text"] = sanitized_q
                    if sanitize_report.get("double_paren_fixes", 0) > 0:
                        detail_logs = detail_logs if 'detail_logs' in locals() else []
                        detail_logs.append(f"[DISPLAY_SANITIZE] collapsed {sanitize_report['double_paren_fixes']} nested numeric parenthesis pattern(s).")
                    if sanitize_report.get("negative_wrap_fixes", 0) > 0:
                        detail_logs = detail_logs if 'detail_logs' in locals() else []
                        detail_logs.append(f"[DISPLAY_SANITIZE] wrapped {sanitize_report['negative_wrap_fixes']} bare negative literal(s) with parentheses.")

                generated_expr = _extract_math_expr_from_question(exe_res.get("question_text", ""))
                if not _is_expression_isomorphic(expected_fp, generated_expr):
                    detail_logs = detail_logs if 'detail_logs' in locals() else []
                    detail_logs.append("[ISO_GUARD] primary output profile mismatch.")
                    for d in _profile_diff_summary(expected_fp, generated_expr):
                        detail_logs.append(f"[ISO_GUARD] {d}")

                    fallback_code = _build_isomorphic_fallback_code(ocr_text)
                    if fallback_code:
                        healed_code = fallback_code
                        healed_exec_code = _optimize_live_execution_code(healed_code)
                        exe_res = scaler._execute_code(healed_exec_code, level=1)
                        if "question_text" in exe_res:
                            sanitized_q2, sanitize_report2 = _sanitize_question_text_display(
                                exe_res.get("question_text", ""),
                                return_report=True
                            )
                            exe_res["question_text"] = sanitized_q2
                            if sanitize_report2.get("double_paren_fixes", 0) > 0:
                                detail_logs.append(f"[DISPLAY_SANITIZE] collapsed {sanitize_report2['double_paren_fixes']} nested numeric parenthesis pattern(s) after fallback.")
                            if sanitize_report2.get("negative_wrap_fixes", 0) > 0:
                                detail_logs.append(f"[DISPLAY_SANITIZE] wrapped {sanitize_report2['negative_wrap_fixes']} bare negative literal(s) after fallback.")
                        detail_logs.append("[ISO_GUARD] LLM output drift detected; switched to deterministic isomorphic fallback.")
                        generated_expr_2 = _extract_math_expr_from_question(exe_res.get("question_text", ""))
                        if not _is_expression_isomorphic(expected_fp, generated_expr_2):
                            for d in _profile_diff_summary(expected_fp, generated_expr_2):
                                detail_logs.append(f"[ISO_GUARD][FALLBACK_FAIL] {d}")
                            raise ValueError("ISO_GUARD fallback failed: generated structure still not isomorphic")

                generated_expr_final = _extract_math_expr_from_question(exe_res.get("question_text", ""))
                generated_fp = _build_structural_profile(generated_expr_final)
                iso_isomorphic = _is_expression_isomorphic(expected_fp, generated_expr_final)
                old_ans = exe_res.get("correct_answer", "")
                fixed_ans = _recompute_correct_answer_from_question(exe_res.get("question_text", ""))
                if fixed_ans is not None:
                    exe_res["correct_answer"] = fixed_ans
                    detail_logs = detail_logs if 'detail_logs' in locals() else []
                    detail_logs.append("[ANS_GUARD] correct_answer recomputed from displayed expression.")
                    if str(old_ans) != str(fixed_ans):
                        detail_logs.append(f"[ANS_GUARD] correct_answer changed: {old_ans} -> {fixed_ans}")
                        
                if exe_res.get("_o1_healed"):
                    ast_fixes += 1
                    detail_logs = detail_logs if 'detail_logs' in locals() else []
                    detail_logs.append("[O(1)_HEALER] Intelligently scaled variables to force perfect division.")
                    
                ab3_exec_elapsed = time.time() - cpu_start_ab3

                # 使用 V6.7 evaluate_live_code 計分
                try:
                    from scripts.evaluate_mcri import evaluate_live_code
                    if "question_text" in exe_res:
                        _live_mcri = evaluate_live_code(
                            code=healed_exec_code,
                            exec_result=exe_res,
                            healer_trace={"regex_fixes": regex_fixes, "ast_fixes": ast_fixes},
                            ablation_mode=False
                        )
                        exe_res["_live_mcri"] = _live_mcri
                        exe_res["_mcri_hygiene_score"] = _live_mcri["breakdown"].get("l4_3_hygiene", 15.0)
                except:
                    pass
                problems_result.append(exe_res)
            except Exception as e:
                ab3_exec_elapsed = time.time() - cpu_start_ab3
                problems_result.append({"error": f"執行錯誤: {e}"})
                
            cpu_execution_time_sec = ab3_exec_elapsed
            
            # 8. 儲存原始碼以供「下一題」功能調用 (儲存 Healed 版本)
            save_dir = "generated_scripts"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
            unique_filename = f"live_show_{int(time.time())}_{uuid.uuid4().hex[:6]}.py"
            file_path = os.path.join(save_dir, unique_filename)
            with open(file_path, "w", encoding="utf-8") as _fb:
                _fb.write(healed_code)
            
            output = {
                "problems": problems_result,
                "debug_meta": {
                    "performance": {
                        "ai_inference_time_sec": ai_inference_time_sec,
                        "cpu_execution_time_sec": cpu_execution_time_sec
                    },
                    "raw_code": raw_out,
                    "final_code": api_stubs + "\n\n" + healed_code,
                    "file_path": file_path,
                    "bare_prompt": "",
                    "scaffold_prompt": system_prompt,
                    "gemini_raw_spec": json.dumps(json_spec, ensure_ascii=False, indent=2) if json_spec else "",
                    "architect_model": "Qwen3-VL",
                    "healer_trace": {"regex_fixes": regex_fixes, "ast_fixes": ast_fixes},
                    "healer_logs": detail_logs if 'detail_logs' in locals() else [],
                    "iso_profile_expected": expected_fp,
                    "iso_profile_generated": generated_fp,
                    "iso_isomorphic": iso_isomorphic,
                    "mcri_report": {"robustness_grade": "MODERATE", "robustness_reason": "Visual Generation with Full Healer"}
                },
                "ab2_result": ab2_result
            }
        else:
            engine = get_engine()
            enriched_input = input_text
            if not ablation_mode:
                iso_block = ""
                if isinstance(json_spec, dict):
                    iso_block = json_spec.get("isomorphic_constraints", "")
                if not iso_block:
                    iso_block, _ = _build_isomorphic_constraints(input_text, json_spec if isinstance(json_spec, dict) else None)
                enriched_input = f"{input_text}\n\n【題型同構硬性約束】\n{iso_block}"

            output = engine.generate_practice_set(
                input_text=enriched_input,
                count=count,
                ablation_mode=ablation_mode,
                model_id=model_id,
                skill_name=skill_id
            )
            
        output["api_time"] = time.time() - start_time

        # ── Flatten debug_meta fields for the frontend ────────────────────
        dm = output.get("debug_meta", {})
        perf = dm.get("performance", {})
        healer_trace = dm.get("healer_trace", {})
        mcri_report  = dm.get("mcri_report", {})

        # Ab2 metrics (from the nested ab2_result if available)
        ab2_res = output.get("ab2_result", {})
        ab2_dm = ab2_res.get("debug_meta", {})
        ab2_perf = ab2_dm.get("performance", {})
        
        output["ab2_ai_inference_time_sec"] = ab2_perf.get("ai_inference_time_sec", 0)
        output["ab2_cpu_execution_time_sec"] = ab2_perf.get("cpu_execution_time_sec", 0)

        # Ab3 metrics (standard fields)
        output["ai_inference_time_sec"]  = perf.get("ai_inference_time_sec", 0)
        output["cpu_execution_time_sec"] = perf.get("cpu_execution_time_sec", 0)
        output["thinking"] = dm.get("thinking", "")
        output["fixes"]    = (healer_trace.get("regex_fixes", 0) or 0) + (healer_trace.get("ast_fixes", 0) or 0)
        
        # Merge basic trace counts with detailed logs
        base_logs = [
            f"regex_fixes: {healer_trace.get('regex_fixes', 0)}",
            f"ast_fixes: {healer_trace.get('ast_fixes', 0)}",
            f"robustness: {mcri_report.get('robustness_grade', 'N/A')}",
        ]
        detail_logs = dm.get("healer_logs", [])
        output["healer_logs"] = base_logs + detail_logs

        # ── Map problems[0] fields for the frontend ───────────────────────
        problems = output.get("problems", [])
        
        # 確保不論成功與否，前端終端機都能拿到 raw_code 與 final_code 進行診斷
        output["raw_text"] = dm.get("raw_text", dm.get("raw_code", ""))
        output["raw_code"] = dm.get("raw_code", "")
        output["final_code"] = dm.get("final_code", "")
        output["file_path"] = dm.get("file_path", "")
        output["bare_prompt"] = dm.get("bare_prompt", "")
        output["scaffold_prompt"] = dm.get("scaffold_prompt", "")
        output["gemini_raw_spec"] = dm.get("gemini_raw_spec", "")
        output["architect_model"] = dm.get("architect_model", "Gemini 3 Flash")
        output["iso_profile_expected"] = dm.get("iso_profile_expected", {})
        output["iso_profile_generated"] = dm.get("iso_profile_generated", {})
        output["iso_isomorphic"] = dm.get("iso_isomorphic", None)

        if problems:
            first = problems[0]
            if not isinstance(first, dict):
                output["error"] = f"Invalid problem format: {type(first)}"
            elif "error" in first:
                output["error"] = first["error"]
            elif "question_text" not in first:
                output["error"] = "Missing question_text in problem output."
            else:
                q_text = first.get("question_text", "")
                output["problem"] = q_text
                output["answer"]  = first.get("correct_answer", "")

                if not output.get("iso_profile_expected") and isinstance(json_spec, dict):
                    output["iso_profile_expected"] = (
                        json_spec.get("structural_profile")
                        or json_spec.get("operator_fingerprint")
                        or {}
                    )

                if output.get("iso_profile_expected") and q_text:
                    _expr = _extract_math_expr_from_question(q_text)
                    _gen_profile = _build_structural_profile(_expr)
                    output["iso_profile_generated"] = _gen_profile
                    output["iso_isomorphic"] = _is_expression_isomorphic(output["iso_profile_expected"], _expr)

                # ── V6.7 MCRI 真實評分 ──────────────────────────────────────
                _live_mcri = first.get("_live_mcri")
                if _live_mcri:
                    output["mcri"] = {
                        "syntax_score":    _live_mcri["syntax_score"],
                        "logic_score":     _live_mcri["logic_score"],
                        "render_score":    _live_mcri["render_score"],
                        "stability_score": _live_mcri["stability_score"],
                        "total_score":     _live_mcri["total_score"],
                        "breakdown":       _live_mcri.get("breakdown", {}),
                    }
                else:
                    _final_code_str = dm.get("final_code", "")
                    _healer_trace = dm.get("healer_trace", {})
                    try:
                        from scripts.evaluate_mcri import evaluate_live_code
                        _live_mcri = evaluate_live_code(
                            code=_final_code_str,
                            exec_result=first,
                            healer_trace=_healer_trace,
                            ablation_mode=ablation_mode
                        )
                        output["mcri"] = {
                            "syntax_score":    _live_mcri["syntax_score"],
                            "logic_score":     _live_mcri["logic_score"],
                            "render_score":    _live_mcri["render_score"],
                            "stability_score": _live_mcri["stability_score"],
                            "total_score":     _live_mcri["total_score"],
                            "breakdown":       _live_mcri.get("breakdown", {}),
                        }
                    except Exception as _mcri_err:
                        import traceback as _tb
                        output["_mcri_error"] = f"{type(_mcri_err).__name__}: {_mcri_err}\n{_tb.format_exc()[:500]}"
                        robust_grade = mcri_report.get('robustness_grade', 'NEUTRAL')
                        robust_map = {"ROBUST": 90, "MODERATE": 65, "NEUTRAL": 50, "UNKNOWN": 50, "RISKY": 30, "SYNTAX_ERROR": 0}
                        arch_score = robust_map.get(robust_grade, 50)
                        output["mcri"] = {
                            "syntax_score": arch_score, "logic_score": arch_score,
                            "render_score": arch_score, "stability_score": arch_score,
                            "total_score":  arch_score,
                        }

        # ── Normalize ab2_result to match frontend renderResult expectations ──
        raw_ab2 = output.get("ab2_result")
        if raw_ab2 and isinstance(raw_ab2, dict) and "error" not in raw_ab2:
            _ab2_live_mcri = raw_ab2.get("_live_mcri")
            if not _ab2_live_mcri:
                try:
                    from scripts.evaluate_mcri import evaluate_live_code
                    _ab2_live_mcri = evaluate_live_code(
                        code=raw_ab2.get("raw_code", ""),
                        exec_result=raw_ab2,
                        healer_trace={}, # No healer for Ab2
                        ablation_mode=False # Ab2 is scaffold, so it benefits from the 80 base stability
                    )
                except Exception:
                    ab2_hygiene = raw_ab2.get("_mcri_hygiene_score", 0) or 0
                    ab2_norm_hygiene = (ab2_hygiene / 15.0) * 100
                    _ab2_live_mcri = {
                        "syntax_score":    min(100, max(0, ab2_norm_hygiene)),
                        "logic_score":     50,  
                        "render_score":    min(100, max(0, ab2_norm_hygiene)),
                        "stability_score": 60,
                        "total_score":     round((ab2_norm_hygiene * 0.4 + 50 * 0.4 + 60 * 0.2), 1),
                        "breakdown":       {}
                    }

            output["ab2_result"] = {
                "problem":                raw_ab2.get("question_text", "(Ab2 — scaffold prompt result)"),
                "answer":                 raw_ab2.get("correct_answer", ""),
                "raw_code":               raw_ab2.get("raw_code", ""),
                "final_code":             raw_ab2.get("raw_code", ""),   # No Healer for Ab2
                "file_path":              raw_ab2.get("file_path", ""),
                "ai_inference_time_sec":  raw_ab2.get("ai_inference_time_sec", 0),
                "cpu_execution_time_sec": raw_ab2.get("cpu_execution_time_sec", 0),
                "fixes":                  0,   # No Healer
                "healer_logs":            [],
                "mcri": {
                    "syntax_score":    _ab2_live_mcri["syntax_score"],
                    "logic_score":     _ab2_live_mcri["logic_score"],
                    "render_score":    _ab2_live_mcri["render_score"],
                    "stability_score": _ab2_live_mcri["stability_score"],
                    "total_score":     _ab2_live_mcri["total_score"],
                    "breakdown":       _ab2_live_mcri.get("breakdown", {}),
                }
            }

        return jsonify(output)
    except Exception as e:
        import traceback
        return jsonify({
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc(),
            "api_time": time.time() - start_time
        }), 500


@live_show_bp.route('/api/stream_thought_ab1')
def stream_thought_ab1():
    """
    SSE Endpoint: 以 stream=True 呼叫 Ollama，即時抓取 Ab1 模式下的
    <thought> 標籤內容，並以 Server-Sent Events 推送至瀏覽器。

    Query params:
        prompt  — 使用者輸入的數學敘述
    """
    prompt_text = request.args.get('prompt', '').strip()
    model_id_query = request.args.get('model_id', 'qwen3-8b').strip()
    
    if not prompt_text:
        return Response('data: {"type":"error","text":"No prompt provided."}\n\n',
                        content_type='text/event-stream')

    # 建構 Ab1 zero-shot prompt（與 scaler.py 保持一致）
    ab1_prompt = f"請寫一個 generate(level=1) 函式，參考：\n{prompt_text}\n直接輸出代碼。"

    def generate_sse():
        try:
            from config import Config
            from core.ai_wrapper import LocalAIClient

            model_config = (
                Config.CODER_PRESETS.get(model_id_query) or
                Config.CODER_PRESETS.get('qwen3-8b') or
                next(iter(Config.CODER_PRESETS.values()), None)
            )
            if not model_config:
                yield 'data: {"type":"error","text":"No model configured."}\n\n'
                return

            client = LocalAIClient(
                model_name=model_config.get('model', 'qwen3:8b'),
                temperature=model_config.get('temperature', 0.7),
                **{k: v for k, v in model_config.items()
                   if k not in ('model', 'temperature', 'provider')}
            )

            for chunk in client.generate_content_stream(ab1_prompt):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                if chunk["type"] in ("done", "error"):
                    return

        except Exception as exc:
            err_payload = json.dumps({"type": "error", "text": str(exc)}, ensure_ascii=False)
            yield f"data: {err_payload}\n\n"

    return Response(
        stream_with_context(generate_sse()),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )

@live_show_bp.route('/api/classify', methods=['POST'])
def classify_input():
    """
    API: 接收 Base64 圖片或純文字，進行 OCR (若有圖) 並使用 Classifier 分類技能。
    回傳 skill_id, confidence_scores 與 process_logs。
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided."}), 400

    image_data = data.get("image_data")
    if image_data:
        import re
        image_data = re.sub(r'^data:image/.+;base64,', '', image_data)
        
    text_data = data.get("text_data")
    ocr_text = ""
    process_logs = []

    try:
        process_logs.append("> 🧬 Initiating Vision DNA Sequencing [Qwen3-VL Mode]...")
        
        skill_name = "Unknown"
        confidence = 0
        json_spec = {}

        if image_data or text_data:
            if image_data:
                process_logs.append("> 🖼️ Detected Image Payload. Passing to Visual Logic Core...")
            else:
                process_logs.append("> 📝 Detected Text Payload. Passing to Visual Logic Core for Semantic Parsing...")
            
            # 使用 Qwen3-VL 進行「視覺/語義單次推理」架構
            print(">>> 📥 傳送資列至 Qwen3-VL 進行聯合分析 (提取 + 分類 + JSON Spec)...")
            
            # 動態取得所有 Agent Skills 資料夾名稱
            # 修正：確保指向 core/agent_skills 而不依賴 current_app 執行環境限制
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            skills_dir = os.path.join(base_dir, "agent_skills")
            available_skills = []
            if os.path.exists(skills_dir):
                for d in os.listdir(skills_dir):
                    if os.path.isdir(os.path.join(skills_dir, d)):
                        available_skills.append(d)
            skills_list_str = ", ".join(available_skills) if available_skills else "Arithmetic, Algebra"

            msg_content = []
            if image_data:
                prompt_text = f"""
你現在是邏輯辨識核心。請觀察圖片，精確提取數學 LaTeX 算式（需忽略 \\tt 與噪音），產出精確的 JSON Spec。
【!! 你只能輸出一個 JSON 物件，嚴禁包含任何其他文字、分析過程或 markdown block !!】

【最高指令：技能 ID 選擇】
你『必須』且『只能』從以下清單中選擇一個最符合的作為 skill_id：
{skills_list_str}

輸出格式要求（skill_id 必須是上面清單中的確切字串）：
{{
  "ocr_text": "12 \\div (-4) \\times (-3)", // 絕對禁止在這裡放入任何解題步驟、文字解說或 markdown，只能有 LaTeX 算式！
  "skill_id": "jh_數學1上_FourArithmeticOperationsOfIntegers",
  "confidence": 95,
  "spec": {{
    "structure": "A \\div B \\times C",
    "operator_sequence": ["divide", "times"],
    "constraints": "A 為正整數，B, C 為負整數",
    "steps": [
      "必須使用 IntegerOps.fmt_num 代入所需數字",
      "嚴禁使用 abs() 或 | 符號"
    ]
  }}
}}
[嚴格禁止] 嚴禁使用『混合練習』或『隨機運算』等模糊描述。你必須從 SKILL.md 目錄或已知概念的【程式要求】中提取對應的 Domain API (如 IntegerOps) 調用規範，並將其寫入 JSON 的 spec.steps 中。此外，針對當前題型，嚴禁出現哪些算子（如：若圖片沒絕對值，則必須寫下「嚴禁使用 abs() 或 | 符號」）也必須寫在 steps 中。
"""
                msg_content = [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            else:
                prompt_text = f"""
你現在是邏輯辨識核心。請閱讀以下使用者提供的數學算式或指令，精確產出結構化的 JSON Spec。
【!! 你只能輸出一個 JSON 物件，嚴禁包含任何其他文字、分析過程或 markdown block !!】

【使用者輸入文字】
{text_data.strip()}

【最高指令：技能 ID 選擇】
你『必須』且『只能』從以下清單中選擇一個最符合的作為 skill_id：
{skills_list_str}

輸出格式要求（skill_id 必須是上面清單中的確切字串）：
{{
  "ocr_text": "{text_data.strip()}", // 絕對禁止在這裡放入任何解題步驟、文字解說或 markdown，只能有 LaTeX 算式！
  "skill_id": "對應的資料夾名稱",
  "confidence": 95,
  "spec": {{
    "structure": "例如 A \\div B \\times C",
    "operator_sequence": ["divide", "times"],
    "constraints": "精確寫出約束條件",
    "steps": [
      "使用對應的 Domain API",
      "嚴格限制的算式或符號"
    ]
  }}
}}
[嚴格禁止] 嚴禁使用『混合練習』或『隨機運算』等模糊描述。你必須從 SKILL.md 目錄或已知概念的【程式要求】中提取對應的 Domain API 調用規範，並將其寫入 JSON 的 spec.steps 中。此外，針對當前題型，嚴禁出現哪些算子（例如沒出現絕對值，就必須明確列為禁用）也必須寫在 steps 中。
"""
                msg_content = prompt_text

            # 從 Config 中動態取用參數 (目前強制校準為 qwen3-vl:8b 測試連線)
            vl_config = Config.CODER_PRESETS.get('qwen3-vl-8b', {})
            model_name = 'qwen3-vl:8b-instruct-q4_k_m'  # 鎖定模型名稱
            
            # 準備 Ollama Chat API Payload (Compatible with both image and pure Text messages)
            msg_dict = {"role": "user", "content": prompt_text}
            if image_data:
                # [Fix] Ollama Chat API requires raw base64, not the data URI scheme.
                b64_str = image_data
                if "base64," in b64_str:
                    b64_str = b64_str.split("base64,")[1]
                msg_dict["images"] = [b64_str]
                
            payload = {
                "model": model_name,
                "messages": [msg_dict],
                "stream": False,
                "options": {
                    "temperature": vl_config.get("temperature", 0.1),
                    "num_ctx": 4096,  # 針對單行算式小圖優化，加快速回應
                    "num_gpu": -1,
                    "repeat_penalty": 1.05
                }
            }

            chat_url = "http://127.0.0.1:11434/api/chat"
            
            print(f">>> 🎯 準備連線 Ollama 模型: {model_name} (URL: {chat_url})")
            try:
                response = requests.post(chat_url, json=payload, timeout=120)
                response.raise_for_status()
                result = response.json()
                
                # 從 Chat API 結構中取出回覆
                raw_out = result.get("message", {}).get("content", "").strip()
                
                import re
                import json
                import difflib

                # 1. 更強力的 JSON 提取 (包含 <think> 標籤也能用貪婪搜索強行拉出)
                # 解決 LaTeX 大括號干擾：嘗試抓出整個 JSON 字串
                json_match = re.search(r'(\{.*\})', raw_out, re.DOTALL)

                if json_match:
                    clean_json_str = json_match.group(0)
                    try:
                        parsed_res = json.loads(clean_json_str)
                        ocr_text = parsed_res.get("ocr_text", text_data.strip() if text_data else "")
                        raw_skill_id = parsed_res.get("skill_id", "Unknown")
                        confidence = parsed_res.get("confidence", 95)
                        json_spec = parsed_res.get("spec", parsed_res.get("json_spec", {}))
                        
                        # [核心修復] 如果 spec 裡面沒東西，從外層補齊
                        if not json_spec and "structure" in parsed_res:
                            json_spec = {
                                "structure": parsed_res.get("structure"),
                                "operator_sequence": parsed_res.get("operator_sequence"),
                                "constraints": parsed_res.get("constraints")
                            }
                        
                        # [新修復] 將 OCR 提取出來的 * 和 / 替換為 LaTeX 格式
                        ocr_text = ocr_text.replace("*", "\\times").replace("/", "\\div")

                        iso_constraints, op_fp = _build_isomorphic_constraints(ocr_text, json_spec)
                        template_id, template_text = _select_liveshow_structure_template(op_fp)
                        if not isinstance(json_spec, dict):
                            json_spec = {}
                        json_spec["isomorphic_constraints"] = iso_constraints
                        json_spec["operator_fingerprint"] = op_fp
                        json_spec["structural_profile"] = op_fp
                        json_spec["structure_template_id"] = template_id
                        json_spec["structure_template_text"] = template_text
                        process_logs.append(
                            f"> 🧪 Complexity Profile: nums={op_fp.get('number_count', 0)}, ops={op_fp.get('operator_count', 0)}, []={op_fp.get('bracket_count', 0)}, ||={op_fp.get('abs_count', 0)}"
                        )

                        # 1. 字典硬覆寫 (Hard Mapping)
                        HARD_MAPPING = {
                            "Arithmetic": "jh_數學1上_FourArithmeticOperationsOfIntegers",
                            "IntegerArithmetic": "jh_數學1上_FourArithmeticOperationsOfIntegers",
                            "FourArithmeticOperationsOfIntegers": "jh_數學1上_FourArithmeticOperationsOfIntegers",
                            "jh_數學1上_四則運算": "jh_數學1上_FourArithmeticOperationsOfIntegers",
                            "Algebra": "jh_數學2上_FourArithmeticOperationsOfPolynomial",
                            "Polynomial": "jh_數學2上_FourArithmeticOperationsOfPolynomial",
                            "jh_數學2上_多項式的四則運算": "jh_數學2上_FourArithmeticOperationsOfPolynomial",
                            "Radicals": "jh_數學2上_FourOperationsOfRadicals",
                            "jh_數學2上_根號運算": "jh_數學2上_FourOperationsOfRadicals",
                        }
                        
                        raw_skill_id = raw_skill_id.strip()
                        if raw_skill_id in HARD_MAPPING:
                            print(f">>> ⚠️ 觸發 Hard Mapping 修正: {raw_skill_id} -> {HARD_MAPPING[raw_skill_id]}")
                            raw_skill_id = HARD_MAPPING[raw_skill_id]

                        # 2. Substring & Fuzzy Matching 模糊比對邏輯
                        if raw_skill_id in available_skills:
                            skill_name = raw_skill_id
                        else:
                            # 2a. 先嘗試 Case-Insensitive 的「包含」檢查 (Substring Match)
                            substring_match = next((avail for avail in available_skills if raw_skill_id.lower() in avail.lower()), None)
                            if substring_match:
                                skill_name = substring_match
                                print(f">>> ⚠️ 觸發 Substring 修正 Skill ID: {raw_skill_id} -> {skill_name}")
                            else:
                                # 2b. 再退化為 difflib 相似度檢查
                                matches = difflib.get_close_matches(raw_skill_id, available_skills, n=1, cutoff=0.3)
                                if matches:
                                    skill_name = matches[0]
                                    print(f">>> ⚠️ 觸發 Fuzzy 修正 Skill ID: {raw_skill_id} -> {skill_name}")
                                else:
                                    skill_name = "Unknown"
                                    print(f">>> ❌ 找不到對應的 Skill ID: {raw_skill_id}")
                                    
                        
                        print(f"DEBUG: Available skills are {available_skills}")
                        # 3. 動態路徑實體檢查 (強制 100% 信心度)
                        if skill_name != "Unknown":
                            target_path = os.path.join(skills_dir, skill_name)
                            if os.path.exists(target_path):
                                confidence = 100
                                process_logs.append(f"> 🧬 DNA Mapping Success: [{raw_skill_id}] -> [{skill_name}]")
                                print(f">>> 🎯 動態路徑確認存在: {target_path} (信心度設為 100)")
                            else:
                                confidence = 0
                                skill_name = "Unknown"
                                print(f">>> ❌ 嚴重錯誤: 已匹配 ID {skill_name} 但實體路徑不存在！")
                                
                        print(f">>> ✅ Qwen3-VL 最終決策完成! Skill: {skill_name}, Confidence: {confidence}, OCR: {ocr_text}")
                        
                    except json.JSONDecodeError as e:
                        print(f">>> ❌ JSON 解析失敗: {e}。原始輸出: {raw_out}")
                        skill_name = "Unknown"
                        # [容錯] 儘量保留 ocr_text 給後端使用，而非直接丟失
                        ocr_text = text_data.strip() if text_data else "(Text Extraction Failed due to JSON Error)"
                else:
                    print(">>> ❌ 找不到 JSON 結構")
                    skill_name = "Unknown"
                    ocr_text = text_data.strip() if text_data else "(Text Extraction Failed due to JSON Error)"
            except requests.exceptions.RequestException as e:
                print(f">>> ❌ Qwen3-VL 執行失敗: {e}")
                ocr_text = "ERROR: Failed to reach Qwen3-VL API."

            display_text = ocr_text[:30] + "..." if len(ocr_text) > 30 else ocr_text
            if skill_name == "Unknown":
                process_logs.append(f"> 📄 VL Extraction & Alignment Complete: [{display_text}] -> Unknown")
                process_logs.append("> ⚠️ DNA Match Failed: Falling back to Unknown.")
            else:
                process_logs.append(f"> 📄 VL Extraction & Alignment Complete: [{display_text}]")
        
        else:
            return jsonify({"success": False, "error": "Require image_data or text_data."}), 400

        bare_prompt = ""
        scaffold_prompt = ""

        if skill_name != "Unknown":
            process_logs.append(f"> ✅ DNA Sequence Aligned: {skill_name}")
            confidence = 98
            
            # 確保 engine 已經初始化，因為 Qwen3-VL (image_data) 沒有呼叫 classifier
            import core.routes.live_show as live_show_module
            if 'engine' not in locals():
                engine = get_engine()

            # [NEW] Generate Prompt Previews
            try:
                skill_path = engine.scaler._get_skill_path(skill_name)
                
                ab1_prompt_path = os.path.join(skill_path, "experiments", "ab1_bare_prompt.md")
                if os.path.exists(ab1_prompt_path):
                    with open(ab1_prompt_path, "r", encoding="utf-8") as f:
                        ab1_template = f.read()
                    import re
                    bare_prompt = re.sub(
                        r"【參考例題】.*?【程式要求】", 
                        lambda m: f"【參考例題】\n{ocr_text}\n\n【程式要求】", 
                        ab1_template, 
                        flags=re.DOTALL
                    )
                else:
                    bare_prompt = f"請寫一個 generate(level=1) 函式，參考：\n{ocr_text}\n直接輸出代碼。"

                skill_md_path = os.path.join(skill_path, "SKILL.md")
                if os.path.exists(skill_md_path):
                    with open(skill_md_path, "r", encoding="utf-8") as f:
                        skill_spec = f.read()
                    # 使用明確的切斷錨點，確保不同技能都能精準抓取精華區塊
                    skill_spec_distilled = skill_spec.split("=== SKILL_END_PROMPT ===")[0].strip()

                    import re
                    live_show_match = re.search(r'\[\[MODE:LIVESHOW\]\]([\s\S]*?)\[\[END_MODE:LIVESHOW\]\]', skill_spec)
                    live_show_content = live_show_match.group(1).strip() if live_show_match else ""

                    # 預處理 input_text 確保有 LaTeX 基本結構 (Using a simplified version of scaler's sanitize)
                    input_text_safe = re.sub(r'(\w)\^(\d+)', r'\1^{\2}', ocr_text)
                    if "$" not in input_text_safe:
                        input_text_safe = re.sub(r'(\(.*\).*)', r'$\1$', input_text_safe)

                    # 動態注入 OCR 結果
                    live_show_content = live_show_content.replace('{{OCR_RESULT}}', input_text_safe)
                    
                    # 應用物理裁切，確保不必要的規則（如絕對值）在沒有出現對應符號時被移除
                    skill_spec_distilled = apply_strict_mirroring(skill_spec_distilled, ocr_text)

                    scaffold_prompt = f"""{skill_spec_distilled}\n=== SKILL_END_PROMPT ===\n\n{live_show_content}"""
                else:
                    scaffold_prompt = "[SKILL.md 未找到]"

                iso_constraints, op_fp = _build_isomorphic_constraints(ocr_text, json_spec if isinstance(json_spec, dict) else None)
                template_id, template_text = _select_liveshow_structure_template(op_fp)
                if isinstance(json_spec, dict):
                    json_spec["isomorphic_constraints"] = iso_constraints
                    json_spec["operator_fingerprint"] = op_fp
                    json_spec["structural_profile"] = op_fp
                    json_spec["structure_template_id"] = template_id
                    json_spec["structure_template_text"] = template_text
                scaffold_prompt += (
                    f"\n\n【題型同構硬性約束】\n{iso_constraints}"
                    f"\n\n【題型骨架模板（必須採用）】\nTemplate: {template_id}\n{template_text}"
                )
                    
            except Exception as e:
                scaffold_prompt = f"Error loading SKILL.md: {e}"
                
        else:
            process_logs.append("> ⚠️ DNA Match Failed: Falling back to Unknown.")
            confidence = 30
            # [強制防禦] 就算辨識出錯退回 Unknown，也幫前端準備乾淨的防禦性 scaffold_prompt 以免出問題
            fallback_knowledge = "題目結構必須與【參考例題】完全相同，嚴禁增加額外運算（如絕對值）。"
            fallback_knowledge_safe = apply_strict_mirroring(fallback_knowledge, ocr_text)
            scaffold_prompt = fallback_knowledge_safe

        return jsonify({
            "success": True,
            "ocr_text": ocr_text,
            "skill_id": skill_name,
            "confidence_scores": confidence,
            "process_logs": process_logs,
            "bare_prompt": bare_prompt,
            "scaffold_prompt": scaffold_prompt,
            "json_spec": json_spec,
            "structural_profile": json_spec.get("structural_profile", {}) if isinstance(json_spec, dict) else {}
        })

    except Exception as e:
        print(f">>> ❌ OCR 階段崩潰: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@live_show_bp.route('/api/run_generated_code', methods=['POST'])
def run_generated_code():
    """
    API: 接受已生成的 Python 程式碼並執行，用於「下一題」即時功能，避免重新呼叫 LLM
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided."}), 400
        
    code = data.get("code")
    file_path = data.get("file_path")
    
    if file_path and os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
            
    if not code:
        return jsonify({"success": False, "error": "No code or valid file_path provided."}), 400
    level = data.get("level", 1)
    ablation_mode = data.get("ablation_mode", False)
    healer_trace = data.get("healer_trace") if isinstance(data.get("healer_trace"), dict) else {}
    if not healer_trace:
        fixes_from_payload = data.get("fixes", 0) or 0
        healer_trace = {"regex_fixes": int(fixes_from_payload), "ast_fixes": 0}
    
    start_time = time.time()
    try:
        engine = get_engine()
        
        # 執行程式碼
        res = engine.scaler._execute_code(code, level=level)
        if "question_text" in res:
            res["question_text"] = _sanitize_question_text_display(res.get("question_text", ""))
        
        # ── V6.7 MCRI 真實評分（下一題路徑）──────────────────────
        live_mcri_result = None
        if "question_text" in res:
            try:
                from scripts.evaluate_mcri import evaluate_live_code
                live_mcri_result = evaluate_live_code(
                    code=code,
                    exec_result=res,
                    healer_trace=healer_trace,
                    ablation_mode=ablation_mode
                )
            except Exception:
                live_mcri_result = None

        if live_mcri_result:
            mcri_payload = {
                "syntax_score":    live_mcri_result["syntax_score"],
                "logic_score":     live_mcri_result["logic_score"],
                "render_score":    live_mcri_result["render_score"],
                "stability_score": live_mcri_result["stability_score"],
                "total_score":     live_mcri_result["total_score"],
                "breakdown":       live_mcri_result.get("breakdown", {}),
            }
        else:
            mcri_payload = {
                "syntax_score": 50, "logic_score": 50,
                "render_score": 50, "stability_score": 50, "total_score": 50
            }

        output = {
            "success": True,
            "problem": res.get("question_text", ""),
            "answer": res.get("correct_answer", ""),
            "api_time": time.time() - start_time,
            "fixes": (healer_trace.get("regex_fixes", 0) or 0) + (healer_trace.get("ast_fixes", 0) or 0),
            "mcri": mcri_payload
        }
        return jsonify(output)
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc(),
            "api_time": time.time() - start_time
        }), 500
