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
import re
from PIL import Image  # 新增：用於處理影像對象
import io             # 新增：用於 Base64 轉換
import requests       # 確保網路模組為檔案域全域可用
from config import Config # 新增：供 Qwen3-VL 讀取模型參數
from core.healers.live_show_healer import (
    sanitize_question_text_display as _sanitize_question_text_display,
    build_readable_healer_logs as _build_readable_healer_logs,
    force_fraction_answer_text as _force_fraction_answer_text,
    infer_fraction_display_mode as _infer_fraction_display_mode_impl,
    has_decimal_number as _has_decimal_number_impl,
    format_fraction_mixed_display as _format_fraction_mixed_display_impl,
    init_healer_trace as _init_healer_trace_impl,
    recompute_regex_totals as _recompute_regex_totals_impl,
    apply_sanitize_report_to_trace as _apply_sanitize_report_to_trace_impl,
    apply_display_report_to_trace as _apply_display_report_to_trace_impl,
    add_o1_fix as _add_o1_fix_impl,
    sanitize_result_question as _sanitize_result_question_impl,
    format_result_question_display as _format_result_question_display_impl,
    recompute_result_answer as _recompute_result_answer_impl,
    maybe_add_o1_fix as _maybe_add_o1_fix_impl,
)
from core.code_utils.live_show_math_utils import (
    _normalize_math_text,
    _scan_number_spans,
    _count_binary_ops,
    _extract_enclosed_segments,
    _extract_abs_segments,
    _segment_stats,
    _build_structural_profile,
    _extract_operator_fingerprint,
    _build_isomorphic_constraints,
    _select_liveshow_structure_template,
    _extract_math_expr_from_question,
    _to_eval_expression_template,
    _recompute_correct_answer_from_question,
    _is_expression_isomorphic,
    _profile_diff_summary,
)
from core.healers.live_show_iso_guard import (
    evaluate_iso_style_guard as _evaluate_iso_style_guard_impl,
    append_iso_style_guard_logs as _append_iso_style_guard_logs_impl,
    append_fallback_switch_log as _append_fallback_switch_log_impl,
)
from core.skill_policies import get_skill_policy, normalize_skill_id
from core.routes.live_show_pipeline import run_ab2_interception, run_ab3_full_healer, assemble_visual_output
# (舊有 Pix2Text 套件已移除，OCR 全權交由 Qwen3-VL 處理)

# 從 __init__.py 匯入已註冊的 Blueprint
from . import live_show_bp

# 全局初始化 MathEngine (延遲載入以避免循環引用)
_engine_instance = None
_LIVE_FILE_DISPLAY_MODE = {}


def get_engine():
    global _engine_instance
    if _engine_instance is None:
        from core.engine.engine import MathEngine
        _engine_instance = MathEngine()
    return _engine_instance


def _infer_fraction_display_mode(source_text, skill_id):
    return _infer_fraction_display_mode_impl(
        source_text,
        skill_id,
        extract_expr_fn=_extract_math_expr_from_question,
    )


def _has_decimal_number(text):
    return _has_decimal_number_impl(text, extract_expr_fn=_extract_math_expr_from_question)


def _format_fraction_mixed_display(question_text, skill_id, display_mode="auto", source_text=None, return_report=False):
    return _format_fraction_mixed_display_impl(
        question_text,
        skill_id,
        display_mode=display_mode,
        source_text=source_text,
        return_report=return_report,
        infer_mode_fn=_infer_fraction_display_mode,
    )


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
    code = re.sub(r"\btraceback\.print_exc\s*\(\s*\)", "pass", code)
    return code


def _patch_fraction_skill_eval_calls(code_text, skill_id):
        """
        僅針對分數技能做執行相容補丁：
        - 不改動整數技能既有函式
        - 將 IntegerOps.safe_eval(...) 轉為 safe_eval(...)
            交由執行環境中的通用 safe_eval（支援 Fraction）處理
        """
        policy = get_skill_policy(skill_id)
        if not bool(policy.get("apply_fraction_eval_patch", False)):
                return code_text

        code = code_text or ""
        code = code.replace("IntegerOps.safe_eval(", "safe_eval(")

        # 關閉「倒算法強制整除」：分數技能不需要把除法硬湊成整數
        code = code.replace(
            "if type(ans_init).__name__ == \"Fraction\" and ans_init.denominator != 1:",
            "if False and type(ans_init).__name__ == \"Fraction\" and ans_init.denominator != 1:"
        )
        code = code.replace(
            "if isinstance(ans_init, Fraction) and ans_init.denominator != 1:",
            "if False and isinstance(ans_init, Fraction) and ans_init.denominator != 1:"
        )
        code = code.replace(
            "if ans_init.denominator != 1:",
            "if False and ans_init.denominator != 1:"
        )

        # 分數技能數值降階（僅此技能）
        # 分母：避免 1 與過大分母
        code = code.replace("IntegerOps.random_nonzero(1, 99)", "IntegerOps.random_nonzero(-10, 10)")
        code = code.replace("IntegerOps.random_nonzero(1, 100)", "IntegerOps.random_nonzero(-10, 10)")
        code = code.replace("random.randint(1, 99)", "random.randint(-10, 10)")
        code = code.replace("random.randint(1, 100)", "random.randint(-10, 10)")

        # 分子：降到七年級友善區間
        code = code.replace("IntegerOps.random_nonzero(-99, 99)", "IntegerOps.random_nonzero(-50, 50)")
        code = code.replace("random.randint(-99, 99)", "random.randint(-50, 50)")

        # 常見寬鬆結果上限，收斂到目前規範
        code = code.replace("abs(ans.numerator) > 60 or ans.denominator > 24", "abs(ans.numerator) > 120 or ans.denominator > 30")
        code = code.replace("abs(ans.numerator) > 80 or ans.denominator > 30", "abs(ans.numerator) > 120 or ans.denominator > 30")

        # 常見分母保護（避免出現 ±1 讓題面退化為整數）
        code = code.replace("while den == 0:", "while den == 0 or abs(den) == 1:")

        return code


def _patch_fraction_eval_calls_heuristic(code_text):
    """
    run_generated_code 防護：若程式碼中明顯是 Fraction 計算，
    但仍使用 IntegerOps.safe_eval，則轉為 safe_eval。
    """
    code = code_text or ""
    if "IntegerOps.safe_eval(" in code and ("Fraction(" in code or "from fractions import Fraction" in code):
        code = code.replace("IntegerOps.safe_eval(", "safe_eval(")
    return code


def _build_isomorphic_fallback_code(ocr_text, skill_id=None):
    expr_text = _extract_math_expr_from_question(ocr_text) or ocr_text
    expr_marked = str(expr_text)
    expr_marked = expr_marked.replace("\\div", "§DIV§").replace("÷", "§DIV§")
    expr_marked = expr_marked.replace("\\times", "§TIMES§").replace("×", "§TIMES§")

    norm = _normalize_math_text(expr_marked)
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

        source_is_decimal = ('.' in token)
        var_specs.append((var_name, source_negative, source_is_decimal))

        cursor = end
        idx += 1

    tail = compact[cursor:]
    tail_escaped = tail.replace("{", "{{").replace("}", "}}")
    eval_parts.append(tail_escaped)
    math_parts.append(tail_escaped)

    eval_template = "".join(eval_parts)
    math_template = "".join(math_parts)

    eval_template = eval_template.replace("§DIV§", "/").replace("§TIMES§", "*")

    math_template = math_template.replace("§DIV§", "\\\\div").replace("§TIMES§", "\\\\times")
    policy = get_skill_policy(skill_id)
    is_fraction_skill = bool(policy.get("fallback_fraction_style", False))
    math_template = math_template.replace("\\", "\\\\").replace("*", "\\\\times")
    if not is_fraction_skill:
        math_template = math_template.replace("/", "\\\\div")
    eval_template = _to_eval_expression_template(eval_template)
    eval_template = eval_template.replace("\\", "\\\\")

    assign_lines = ["        vars_dict = {}"]
    source_has_decimal = _has_decimal_number(ocr_text)

    for i, (var_name, source_negative, source_is_decimal) in enumerate(var_specs):
        prev_char = compact[spans[i][0] - 1] if spans[i][0] > 0 else ''
        is_denominator_position = (prev_char == '/')

        if is_fraction_skill:
            if is_denominator_position:
                assign_lines.append(f"        vars_dict['{var_name}'] = IntegerOps.random_nonzero(-10, 10)")
                assign_lines.append(f"        while abs(vars_dict['{var_name}']) <= 1:")
                assign_lines.append(f"            vars_dict['{var_name}'] = IntegerOps.random_nonzero(-10, 10)")
            else:
                # 若來源題型含小數，對應小數位置維持小數型態
                if source_has_decimal and source_is_decimal:
                    assign_lines.append(f"        vars_dict['{var_name}'] = IntegerOps.random_nonzero(-50, 50) / 10.0")
                    assign_lines.append(f"        while abs(vars_dict['{var_name}'] - int(vars_dict['{var_name}'])) < 1e-9:")
                    assign_lines.append(f"            vars_dict['{var_name}'] = IntegerOps.random_nonzero(-50, 50) / 10.0")
                else:
                    # 分子符號不跟原題綁死：改為對稱隨機，避免固定「第一個負、第二個正」的死板模式
                    assign_lines.append(f"        vars_dict['{var_name}'] = IntegerOps.random_nonzero(-50, 50)")
        else:
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
                if isinstance(v, float):
                    frac_str = "Fraction('" + format(v, '.1f') + "')"
                else:
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
                if isinstance(v, float):
                    frac_str = "Fraction('" + format(v, '.1f') + "')"
                else:
                    frac_str = "Fraction(" + str(v) + ", 1)"
                eval_str = eval_str.replace(key1, frac_str)
                eval_str = eval_str.replace(key2, frac_str)

                if isinstance(v, float):
                    disp_v = format(v, '.1f')
                else:
                    disp_v = str(v)
                math_str = math_str.replace(key1, disp_v)
                math_str = math_str.replace(key2, disp_v if isinstance(v, float) else IntegerOps.fmt_num(v))
                
            ans = safe_eval(eval_str)
            
            last_ans = ans
            last_math_str = math_str
            
            if type(ans).__name__ == "Fraction":
                if abs(ans.numerator) > 120 or ans.denominator > 30:
                    continue
                if ans.denominator == 1:
                    final_ans = str(ans.numerator)
                else:
                    final_ans = f"{{ans.numerator}}/{{ans.denominator}}"
                return {{
                    'question_text': "計算 $" + math_str + "$ 的值。",
                    'correct_answer': final_ans,
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

    # 分數技能：禁用 fallback 內建的 O(1) 整除強制邏輯，避免題目退化為整數四則
    if is_fraction_skill:
        code = code.replace(
            "if type(ans_init).__name__ == \"Fraction\" and ans_init.denominator != 1:",
            "if False and type(ans_init).__name__ == \"Fraction\" and ans_init.denominator != 1:"
        )

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

    # [Bug 23 Fix] 追蹤「絕對值段落」狀態：遇到 "3) 絕對值層級" 等段落標題後，
    # 後續的縮排內容行（數量一致、分布一致等）也要一併刪除，直到遇到非縮排行（新段落）。
    _skip_abs_block = False

    for line in lines:
        should_remove = False
        for symbol, keywords in guards.items():
            # 如果圖片裡沒這個符號，且這行含有相關關鍵字
            if symbol not in ocr_text:
                if any(kw in line for kw in keywords):
                    should_remove = True
                    if symbol == "|":
                        _skip_abs_block = True  # 開始跳過絕對值段落的縮排內容
                    break

        # 若正在跳過絕對值子段落，且此行是縮排的子項目（以空白/- 開頭且包含「數量一致」等）
        if not should_remove and _skip_abs_block and "|" not in ocr_text:
            stripped = line.strip()
            if stripped.startswith('-') or stripped.startswith('•') or (line.startswith('  ') and stripped):
                # 這是縮排的子項目，屬於上方已刪除的絕對值段
                should_remove = True
            else:
                # 遇到非縮排行（新段落或空行），停止跳過
                if stripped and not stripped.startswith('-'):
                    _skip_abs_block = False

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


def _looks_like_fraction_expression(text: str) -> bool:
    content = str(text or "")
    return (
        "\\frac" in content
        or bool(re.search(r"\b\d+\s*/\s*\d+\b", content))
        or bool(re.search(r"\b\d+\s+\d+\s*/\s*\d+\b", content))
    )


def _looks_like_radical_expression(text: str) -> bool:
    content = str(text or "")
    lowered = content.lower()
    return ("\\sqrt" in content) or ("√" in content) or ("radical" in lowered) or ("根號" in content)


def _apply_skill_safety_guard(skill_name: str, ocr_text: str, available_skills):
    if skill_name == "jh_數學2上_FourOperationsOfRadicals":
        if _looks_like_fraction_expression(ocr_text) and not _looks_like_radical_expression(ocr_text):
            corrected = normalize_skill_id("Fractions", available_skills)
            if corrected != "Unknown":
                return corrected, "fraction_without_radical_symbol"
    return skill_name, None


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
        json_spec = data.get("json_spec") or {}
        if not isinstance(json_spec, dict):
            json_spec = {}

        # ── Canonical OCR text ─────────────────────────────────────────────
        # Both image-paste and text-box paths go through /api/classify first.
        # Classify stores the final ocr_text (after LaTeX normalisation) into
        # json_spec["ocr_text"].  Using it here keeps both paths on the exact
        # same execution track; we fall back to input_text only when json_spec
        # is absent (e.g. direct API calls or old clients).
        canonical_ocr_text = json_spec.get("ocr_text") or input_text

        route_mode = "text_engine_ab1" if ablation_mode else "text_engine_ab3"
        if input_text and image_data:
            image_data = None
            print(">>> 🛡️ [PATH] image_data ignored due to text-priority guard")
        
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
            route_mode = "image_monolithic_ab3"
            print(f">>> 🧭 [PATH] /api/generate_live route_mode={route_mode}")
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
            # Use canonical_ocr_text (from classify) so image and text paths are identical.
            ocr_text = canonical_ocr_text
            fraction_display_mode = _infer_fraction_display_mode(ocr_text, skill_id)
            decimal_style_mode = _has_decimal_number(ocr_text)
            knowledge = apply_strict_mirroring(knowledge, ocr_text)
            # Re-use pre-computed structural profile from classify when available.
            if json_spec.get("operator_fingerprint"):
                iso_block = json_spec.get("isomorphic_constraints", "")
                fp = json_spec["operator_fingerprint"]
                template_id = json_spec.get("structure_template_id", "")
                template_text = json_spec.get("structure_template_text", "")
                if not iso_block:
                    iso_block, fp = _build_isomorphic_constraints(ocr_text, json_spec)
                    template_id, template_text = _select_liveshow_structure_template(fp)
            else:
                iso_block, fp = _build_isomorphic_constraints(ocr_text, json_spec)
                template_id, template_text = _select_liveshow_structure_template(fp)
            
            # 動態注入 OCR 結果
            live_show_content = live_show_content.replace("{{OCR_RESULT}}", ocr_text)
            
            # 【基因+任務】組合提取 (完全封殺 BENCHMARK)
            final_scaffold = knowledge + "\n" + live_show_content
                
            # 4. 組裝 Scaffold Prompt
            # [Bug 26] 根據 fraction_display_mode 動態注入帶分數/純分數限制
            if fraction_display_mode == "fraction":
                _fraction_mode_constraint = (
                    "\n【帶分數禁令（Bug26）】"
                    "輸入例題只含純分數（\frac{a}{b}，無帶分數 n\frac{r}{b}）。"
                    "禁止生成帶分數格式。所有 FractionOps.to_latex() 必須傳入 mixed=False。"
                    "禁止生成分子大於分母的帶分數表示（如 2\\frac{1}{3}、-1\\frac{2}{5}）。"
                )
            elif fraction_display_mode == "mixed":
                _fraction_mode_constraint = (
                    "\n【帶分數必要（Bug26）】"
                    "輸入例題含帶分數（n\frac{r}{b} 格式，n≥1）。"
                    "所有 FractionOps.to_latex() 必須傳入 mixed=True，"
                    "假分數必須轉換成帶分數格式（如 \frac{7}{3} → 2\\frac{1}{3}）。"
                )
            else:
                _fraction_mode_constraint = ""

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
{template_text}{_fraction_mode_constraint}
"""
            # 5. 準備 Qwen3-VL 呼叫
            vl_config = Config.CODER_PRESETS.get('qwen3-vl-8b', {})
            model_name = 'qwen3-vl:8b-instruct-q4_k_m'  # 鎖定模型名稱
            
            # [Bug 29] Dynamically inject bracket/abs constraint into system prompt
            # so the AI cannot ignore it via the 「無視所有模板」 override.
            _fp_brackets = fp.get("bracket_count", 0)
            _fp_abs = fp.get("abs_count", 0)
            if _fp_brackets > 0 and _fp_abs == 0:
                _sys_grouping_note = (
                    "【中括號守則（最高優先）】圖片中的分組符號是中括號 [ ]。"
                    "生成的 math_str 字串中必須原樣保留 [ ]，"
                    "嚴禁以 | | 或 abs() 替代。違者判定生成失敗。"
                )
            elif _fp_abs > 0 and _fp_brackets == 0:
                _sys_grouping_note = (
                    "【絕對值守則（最高優先）】圖片中含絕對值符號 | |。"
                    "生成的 math_str 字串中必須原樣保留 | |，嚴禁替換成 [ ]。"
                )
            else:
                _sys_grouping_note = ""
            system_prompt = (
                f"你現在是頂級 Python 工程師。你現在直接觀察圖片，你的唯一任務是 100% 鏡像模仿圖片中的算式結構。"
                f"嚴禁加入任何圖片中沒有的數學符號（如：絕對值、括號）。必須使用 IntegerOps.fmt_num 與 \\div、\\times。\n"
                f"{_sys_grouping_note}\n\n"
                f"【最高指令】『無視所有模板，以你看到的圖片內容為唯一真理。產出最簡約的 generate 函式。』\n\n"
                f"請根據圖片與提供的【SCAFFOLD PROMPT】，直接輸出 Python 代碼，不需要解釋。\n\n"
                f"【SCAFFOLD PROMPT】\n{scaffold_prompt}"
            )
            
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
            expected_fp = _build_structural_profile(ocr_text)
            # --- Ab2 Interception (Scaffold Prompt, No Healer) ---
            ab2_pack = run_ab2_interception(
                scaler=scaler,
                final_code=final_code,
                api_stubs=api_stubs,
                skill_id=skill_id,
                expected_fp=expected_fp,
                decimal_style_mode=decimal_style_mode,
                ocr_text=ocr_text,
                fraction_display_mode=fraction_display_mode,
                ai_inference_time_sec=ai_inference_time_sec,
                live_file_display_mode=_LIVE_FILE_DISPLAY_MODE,
                optimize_live_execution_code_fn=_optimize_live_execution_code,
                patch_fraction_skill_eval_calls_fn=_patch_fraction_skill_eval_calls,
                evaluate_iso_style_guard_fn=_evaluate_iso_style_guard_impl,
                build_isomorphic_fallback_code_fn=_build_isomorphic_fallback_code,
                extract_math_expr_from_question_fn=_extract_math_expr_from_question,
                has_decimal_number_fn=_has_decimal_number,
                is_expression_isomorphic_fn=_is_expression_isomorphic,
                sanitize_result_question_fn=_sanitize_result_question_impl,
                format_result_question_display_fn=_format_result_question_display_impl,
                recompute_result_answer_fn=_recompute_result_answer_impl,
                recompute_correct_answer_from_question_fn=_recompute_correct_answer_from_question,
                maybe_add_o1_fix_fn=_maybe_add_o1_fix_impl,
            )
            ab2_result = ab2_pack["ab2_result"]
            from core.code_generator import _advanced_healer
            ab3_pack = run_ab3_full_healer(
                scaler=scaler,
                final_code=final_code,
                skill_id=skill_id,
                expected_fp=expected_fp,
                decimal_style_mode=decimal_style_mode,
                ocr_text=ocr_text,
                fraction_display_mode=fraction_display_mode,
                live_file_display_mode=_LIVE_FILE_DISPLAY_MODE,
                api_stubs=api_stubs,
                optimize_live_execution_code_fn=_optimize_live_execution_code,
                patch_fraction_skill_eval_calls_fn=_patch_fraction_skill_eval_calls,
                advanced_healer_fn=_advanced_healer,
                sanitize_result_question_fn=_sanitize_result_question_impl,
                evaluate_iso_style_guard_fn=_evaluate_iso_style_guard_impl,
                append_iso_style_guard_logs_fn=_append_iso_style_guard_logs_impl,
                append_fallback_switch_log_fn=_append_fallback_switch_log_impl,
                profile_diff_summary_fn=_profile_diff_summary,
                build_isomorphic_fallback_code_fn=_build_isomorphic_fallback_code,
                extract_math_expr_from_question_fn=_extract_math_expr_from_question,
                has_decimal_number_fn=_has_decimal_number,
                is_expression_isomorphic_fn=_is_expression_isomorphic,
                build_structural_profile_fn=_build_structural_profile,
                recompute_result_answer_fn=_recompute_result_answer_impl,
                recompute_correct_answer_from_question_fn=_recompute_correct_answer_from_question,
                format_result_question_display_fn=_format_result_question_display_impl,
                maybe_add_o1_fix_fn=_maybe_add_o1_fix_impl,
            )

            problems_result = ab3_pack["problems_result"]
            cpu_execution_time_sec = ab3_pack["cpu_execution_time_sec"]
            healed_code = ab3_pack["healed_code"]
            file_path = ab3_pack["file_path"]
            regex_fixes = ab3_pack["regex_fixes"]
            regex_code_fixes = ab3_pack["regex_code_fixes"]
            regex_display_fixes = ab3_pack["regex_display_fixes"]
            ast_fixes = ab3_pack["ast_fixes"]
            o1_fixes = ab3_pack["o1_fixes"]
            detail_logs = ab3_pack["detail_logs"]
            generated_fp = ab3_pack["generated_fp"]
            iso_isomorphic = ab3_pack["iso_isomorphic"]
            
            output = assemble_visual_output(
                problems_result=problems_result,
                ai_inference_time_sec=ai_inference_time_sec,
                cpu_execution_time_sec=cpu_execution_time_sec,
                raw_out=raw_out,
                api_stubs=api_stubs,
                healed_code=healed_code,
                file_path=file_path,
                system_prompt=system_prompt,
                json_spec=json_spec,
                regex_fixes=regex_fixes,
                regex_code_fixes=regex_code_fixes,
                regex_display_fixes=regex_display_fixes,
                ast_fixes=ast_fixes,
                o1_fixes=o1_fixes,
                detail_logs=detail_logs,
                expected_fp=expected_fp,
                generated_fp=generated_fp,
                iso_isomorphic=iso_isomorphic,
                fraction_display_mode=fraction_display_mode,
                ab2_result=ab2_result,
            )
        else:
            print(f">>> 🧭 [PATH] /api/generate_live route_mode={route_mode}")
            engine = get_engine()
            # Use canonical_ocr_text so image-paste and text-box reach the same point.
            enriched_input = canonical_ocr_text
            if not ablation_mode:
                # Re-use isomorphic constraints computed during classify when available.
                iso_block = json_spec.get("isomorphic_constraints", "") if isinstance(json_spec, dict) else ""
                if not iso_block:
                    iso_block, _ = _build_isomorphic_constraints(canonical_ocr_text, json_spec if isinstance(json_spec, dict) else None)
                enriched_input = f"{canonical_ocr_text}\n\n【題型同構硬性約束】\n{iso_block}"

            output = engine.generate_practice_set(
                input_text=enriched_input,
                count=count,
                ablation_mode=ablation_mode,
                model_id=model_id,
                skill_name=skill_id
            )
            
        output["api_time"] = time.time() - start_time
        output["route_mode"] = route_mode

        # ── Flatten debug_meta fields for the frontend ────────────────────
        dm = output.get("debug_meta", {})
        perf = dm.get("performance", {})
        healer_trace = dm.get("healer_trace", {})
        mcri_report  = dm.get("mcri_report", {})

        # Ab2 metrics (from the nested ab2_result if available)
        ab2_res = output.get("ab2_result")
        if not isinstance(ab2_res, dict):
            ab2_res = {}
        ab2_dm = ab2_res.get("debug_meta", {})
        ab2_perf = ab2_dm.get("performance", {})
        
        output["ab2_ai_inference_time_sec"] = ab2_perf.get("ai_inference_time_sec", 0)
        output["ab2_cpu_execution_time_sec"] = ab2_perf.get("cpu_execution_time_sec", 0)

        # Ab3 metrics (standard fields)
        output["ai_inference_time_sec"]  = perf.get("ai_inference_time_sec", 0)
        output["cpu_execution_time_sec"] = perf.get("cpu_execution_time_sec", 0)
        output["thinking"] = dm.get("thinking", "")
        output["fixes"]    = (
            (healer_trace.get("regex_fixes", 0) or 0)
            + (healer_trace.get("ast_fixes", 0) or 0)
            + (healer_trace.get("o1_fixes", 0) or 0)
        )
        
        # Merge basic trace counts with detailed logs
        base_logs = [
            "HEALER_FIX_LOGS",
            f"regex_fixes: {healer_trace.get('regex_fixes', 0)}",
            f"regex_code_fixes: {healer_trace.get('regex_code_fixes', 0)}",
            f"regex_display_fixes: {healer_trace.get('regex_display_fixes', 0)}",
            f"ast_fixes: {healer_trace.get('ast_fixes', 0)}",
            f"o1_fixes: {healer_trace.get('o1_fixes', 0)}",
            f"robustness: {mcri_report.get('robustness_grade', 'N/A')}",
        ]
        detail_logs = dm.get("healer_logs", [])
        readable_logs = _build_readable_healer_logs(healer_trace, detail_logs)
        output["healer_logs"] = base_logs + readable_logs + detail_logs

        # ── Map problems[0] fields for the frontend ───────────────────────
        problems = output.get("problems", [])
        
        # 確保不論成功與否，前端終端機都能拿到 raw_code 與 final_code 進行診斷
        output["raw_text"] = dm.get("raw_text", dm.get("raw_code", ""))
        output["raw_code"] = dm.get("raw_code", "")
        output["final_code"] = dm.get("final_code", "")
        output["file_path"] = dm.get("file_path", "")
        output["bare_prompt"] = dm.get("bare_prompt", "")
        output["scaffold_prompt"] = dm.get("scaffold_prompt", "")
        output["architect_raw_spec"] = dm.get("architect_raw_spec", dm.get("gemini_raw_spec", ""))
        output["gemini_raw_spec"] = output["architect_raw_spec"]
        output["architect_model"] = dm.get("architect_model", "Qwen3-VL 8B (Local)")
        output["iso_profile_expected"] = dm.get("iso_profile_expected", {})
        output["iso_profile_generated"] = dm.get("iso_profile_generated", {})
        output["iso_isomorphic"] = dm.get("iso_isomorphic", None)

        # Keep Ab2/Ab3 diagnostics anchored to the same pre-healer raw text.
        if isinstance(ab2_res, dict):
            ab2_res["raw_text"] = output["raw_text"]
            ab2_res["raw_code"] = output["raw_code"]
            output["ab2_result"] = ab2_res

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
                "raw_text":               output.get("raw_text", raw_ab2.get("raw_code", "")),
                "raw_code":               output.get("raw_code", raw_ab2.get("raw_code", "")),
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

        # [Bug 26 companion — ab2 ≡ ab3 when fixes=0]
        # 當 ab3 healer 修復數 = 0 時，ab2 與 ab3 使用相同程式碼，共享同一運行結果。
        # 背景：ab2 與 ab3 分別獨立執行同一份程式碼，但因亂數種子不同會產生不同問題，
        # 導致前端顯示不一致。當修復數=0 時將 ab3 的題目/答案複製至 ab2_result。
        if (
            output.get("fixes", 0) == 0
            and isinstance(output.get("ab2_result"), dict)
            and "error" not in output
            and "problem" in output
        ):
            output["ab2_result"]["problem"] = output["problem"]
            output["ab2_result"]["answer"] = output["answer"]
            output["ab2_result"]["_same_as_ab3"] = True

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

    text_data = (data.get("text_data") or "").strip()
    image_data = data.get("image_data")
    route_mode = "none"
    if text_data and image_data:
        # 後端防呆：若文字與圖片同時存在，優先採用文字路徑，避免舊版前端殘留 canvas 造成誤判
        route_mode = "text_priority_conflict"
        image_data = None
    elif image_data:
        route_mode = "image"
        import re
        image_data = re.sub(r'^data:image/.+;base64,', '', image_data)
    elif text_data:
        route_mode = "text"

    ocr_text = ""
    process_logs = []

    try:
        process_logs.append("> 🧬 Initiating Vision DNA Sequencing [Qwen3-VL Mode]...")
        process_logs.append(f"> 🧭 Route Mode: {route_mode}")
        print(f">>> 🧭 [PATH] /api/classify route_mode={route_mode}")
        
        skill_name = "Unknown"
        confidence = 0
        json_spec = {}
        api_error = None

        if image_data or text_data:
            if image_data:
                process_logs.append("> 🖼️ Detected Image Payload. Passing to Visual Logic Core...")
            else:
                process_logs.append("> 📝 Detected Text Payload. Passing to Visual Logic Core for Semantic Parsing...")
            
            # 使用 Qwen3-VL 進行「視覺/語義單次推理」架構
            print(">>> 📥 傳送資料至 Qwen3-VL 進行聯合分析 (提取 + 分類)...")
            
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
你現在是邏輯辨識核心。請觀察圖片，精確提取數學 LaTeX 算式（需忽略 \\tt 與噪音），並完成技能分類。
【!! 你只能輸出一個 JSON 物件，嚴禁包含任何其他文字、分析過程或 markdown block !!】

【最高指令：技能 ID 選擇】
你『必須』且『只能』從以下清單中選擇一個最符合的作為 skill_id：
{skills_list_str}

輸出格式要求（skill_id 必須是上面清單中的確切字串）：
{{
  "ocr_text": "12 \\div (-4) \\times (-3)",
  "skill_id": "jh_數學1上_FourArithmeticOperationsOfIntegers",
  "confidence": 95
}}
[嚴格要求] 嚴禁輸出多餘欄位；只輸出 ocr_text、skill_id、confidence。嚴禁在 JSON 內加入 // 注解或任何額外文字。
"""
                msg_content = [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            else:
                prompt_text = f"""
你現在是邏輯辨識核心。請閱讀以下使用者提供的數學算式或指令，精確完成技能分類。
【!! 你只能輸出一個 JSON 物件，嚴禁包含任何其他文字、分析過程或 markdown block !!】

【使用者輸入文字】
{text_data.strip()}

【最高指令：技能 ID 選擇】
你『必須』且『只能』從以下清單中選擇一個最符合的作為 skill_id：
{skills_list_str}

輸出格式要求（skill_id 必須是上面清單中的確切字串）：
{{
  "ocr_text": "{text_data.strip()}",
  "skill_id": "對應的資料夾名稱",
  "confidence": 95
}}
[嚴格要求] 嚴禁輸出多餘欄位；只輸出 ocr_text、skill_id、confidence。嚴禁在 JSON 內加入 // 注解或任何額外文字。
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
                    "num_ctx": 8192,  # 升至 8192：圖片 token 消耗大，避免截斷 <think> 閉合標籤
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
                print(f">>> 📝 Qwen3-VL raw_out (前300字): {repr(raw_out[:300])}")
                process_logs.append(f"> 🔍 VL raw (前150字): {repr(raw_out[:150])}")

                import re
                import json

                # 1. 清除 <think>...</think> 區塊
                # 同時處理兩種情況：
                #   a) 正常閉合：<think>...</think>
                #   b) 未閉合（num_ctx 截斷導致 </think> 消失）：<think>...[EOF]
                raw_out_clean = re.sub(r'<think>.*?</think>', '', raw_out, flags=re.DOTALL)
                # 若仍有 <think> 開頭但沒閉合，截掉從 <think> 開始的所有內容
                raw_out_clean = re.sub(r'<think>.*', '', raw_out_clean, flags=re.DOTALL)
                raw_out_clean = raw_out_clean.strip()
                # 若剝除思考區塊後為空（模型只輸出 think），退回原始文字並嘗試找 JSON
                if not raw_out_clean:
                    raw_out_clean = raw_out

                # 2. 清除 ```json ... ``` 包裝（模型可能照搬 markdown 格式）
                raw_out_clean = re.sub(r'```(?:json)?\s*', '', raw_out_clean).strip()
                raw_out_clean = raw_out_clean.replace('```', '').strip()

                # 3. JSON 提取：掃描每個 { 位置，找第一個含 ocr_text/skill_id 的合法 JSON
                # [Bug 21 Fix] 原本的 greedy re.search(r'\{.*\}', ..., re.DOTALL) 會從第一個 {
                # 一路貪婪匹配到最後一個 }。若模型在 </think> 後仍輸出說明文字（如
                # "{some note}. Answer: {...}"），說明文字的 { 會讓 regex 擴展過頭 →
                # 拼出非法 JSON → JSONDecodeError → OCR 失敗。
                # 改用 json.JSONDecoder().raw_decode() 逐一嘗試每個 { 起點，
                # 找到第一個能成功解析且含 ocr_text / skill_id 的合法 JSON 即停止。
                _json_decoder = json.JSONDecoder()
                parsed_res = None
                for _scan_m in re.finditer(r'\{', raw_out_clean):
                    _snip = raw_out_clean[_scan_m.start():]
                    # [Bug 17 Fix] escape invalid JSON backslashes (e.g. bare \div → \\div)
                    # [Bug 22 Fix] add (?<!\\) lookbehind: if the model already outputs \\div
                    # (properly escaped), the old regex incorrectly re-escapes the second \
                    # (followed by 'd' not in exclusion list) → \\\div (3 backslashes) → invalid JSON.
                    # Lookbehind ensures we only touch lone \ (not \\ pairs).
                    _snip_fixed = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', _snip)
                    # remove // line-end comments (model sometimes copies prompt examples)
                    _snip_fixed = re.sub(r'\s*//[^\n"]*', '', _snip_fixed)
                    try:
                        _obj, _ = _json_decoder.raw_decode(_snip_fixed)
                        if isinstance(_obj, dict) and ('ocr_text' in _obj or 'skill_id' in _obj):
                            parsed_res = _obj
                            break
                    except (json.JSONDecodeError, ValueError):
                        continue

                if parsed_res is not None:
                    try:
                        ocr_text = parsed_res.get("ocr_text", text_data.strip() if text_data else "")
                        raw_skill_id = parsed_res.get("skill_id", "Unknown")
                        confidence = parsed_res.get("confidence", 95)
                        json_spec = {}

                        # [Bug 20 Fix] json.loads() interprets \t→tab, \r→CR, \f→FF, \b→BS, \n→LF.
                        # LaTeX commands that start with these bytes get mangled after parsing:
                        #   \times → (tab)imes,  \frac → (FF)rac,  \right → (CR)ight,
                        #   \begin → (BS)egin,   \neq  → (LF)eq
                        # Unmangle them back to proper LaTeX after json.loads().
                        _LATEX_JSON_UNMANGLE = [
                            ('\times',       r'\times'),
                            ('\to',          r'\to'),
                            ('\top',         r'\top'),
                            ('\text',        r'\text'),
                            ('\theta',       r'\theta'),
                            ('\frac',        r'\frac'),
                            ('\forall',      r'\forall'),
                            ('\right',       r'\right'),
                            ('\rightarrow',  r'\rightarrow'),
                            ('\begin',       r'\begin'),
                            ('\beta',        r'\beta'),
                            ('\neq',         r'\neq'),
                            ('\neg',         r'\neg'),
                            ('\nabla',       r'\nabla'),
                            ('\nleq',        r'\nleq'),
                            ('\ngeq',        r'\ngeq'),
                        ]
                        for _mangled, _fixed in _LATEX_JSON_UNMANGLE:
                            ocr_text = ocr_text.replace(_mangled, _fixed)

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
                        # Canonical OCR text — stored here so generate_live can use exactly the
                        # same text regardless of whether the original input was an image or a
                        # text-box entry, keeping both paths on the same execution track.
                        json_spec["ocr_text"] = ocr_text
                        process_logs.append(
                            f"> 🧪 Complexity Profile: nums={op_fp.get('number_count', 0)}, ops={op_fp.get('operator_count', 0)}, []={op_fp.get('bracket_count', 0)}, ||={op_fp.get('abs_count', 0)}"
                        )

                        raw_skill_id = raw_skill_id.strip()
                        skill_name = normalize_skill_id(raw_skill_id, available_skills)
                        if skill_name == "Unknown":
                            print(f">>> ❌ 找不到對應的 Skill ID: {raw_skill_id}")
                        elif skill_name != raw_skill_id:
                            print(f">>> ⚠️ 觸發 Policy Normalization 修正 Skill ID: {raw_skill_id} -> {skill_name}")
                                    
                        
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

                        guarded_skill, guard_reason = _apply_skill_safety_guard(skill_name, ocr_text, available_skills)
                        if guarded_skill != skill_name:
                            process_logs.append(
                                f"> 🛡️ Classification Safety Guard: [{skill_name}] -> [{guarded_skill}] ({guard_reason})"
                            )
                            print(
                                f">>> 🛡️ Classification Safety Guard 修正: {skill_name} -> {guarded_skill} ({guard_reason})"
                            )
                            skill_name = guarded_skill
                            confidence = min(int(confidence or 0), 95)
                                
                        print(f">>> ✅ Qwen3-VL 最終決策完成! Skill: {skill_name}, Confidence: {confidence}, OCR: {ocr_text}")
                        
                    except Exception as e:
                        print(f">>> ❌ JSON 後處理失敗: {e}")
                        print(f">>> ❌ 清理後文字(前500字): {repr(raw_out_clean[:500])}")
                        skill_name = "Unknown"
                        ocr_text = text_data.strip() if text_data else "(Text Extraction Failed due to JSON Error)"
                else:
                    print(f">>> ❌ 所有 {{ 位置均無法解析出有效 JSON。清理後文字(前500字): {repr(raw_out_clean[:500])}")
                    process_logs.append(f"> ❌ JSON scan failed. clean(前150字): {repr(raw_out_clean[:150])}")
                    # [Last-resort fallback] 直接用 regex 抽 ocr_text 值（容許 LaTeX 反斜線）
                    _fb = re.search(r'"ocr_text"\s*:\s*"((?:[^"\\]|\\.)*)"', raw_out)
                    if _fb:
                        ocr_text = re.sub(r'\\(?!["\\bfnrtu/])', r'\\', _fb.group(1))
                        try:
                            ocr_text = ocr_text.encode('raw_unicode_escape').decode('unicode_escape')
                        except Exception:
                            pass
                        print(f">>> ⚠️ Last-resort OCR fallback: {ocr_text}")
                        process_logs.append(f"> ⚠️ OCR last-resort fallback: {ocr_text}")
                        skill_name = "Unknown"  # skill 仍 unknown，但 ocr_text 保留
                    else:
                        skill_name = "Unknown"
                        ocr_text = text_data.strip() if text_data else "(Text Extraction Failed due to JSON Error)"
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response is not None else "N/A"
                response_text = ""
                if e.response is not None:
                    response_text = (e.response.text or "").strip()
                if len(response_text) > 400:
                    response_text = response_text[:400] + "..."
                api_error = f"Qwen3-VL API HTTP {status_code}: {response_text or str(e)}"
                print(f">>> ❌ Qwen3-VL HTTP 錯誤: {api_error}")
                process_logs.append(f"> ❌ Ollama Upstream Error: HTTP {status_code}")
                ocr_text = "ERROR: Failed to reach Qwen3-VL API."
            except requests.exceptions.RequestException as e:
                print(f">>> ❌ Qwen3-VL 執行失敗: {e}")
                api_error = f"Qwen3-VL API Request failed: {e}"
                process_logs.append("> ❌ Ollama Upstream Error: Request failed")
                ocr_text = "ERROR: Failed to reach Qwen3-VL API."

            if api_error:
                return jsonify({
                    "success": False,
                    "error": api_error,
                    "process_logs": process_logs,
                }), 502

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
                    # [Bug 23 Fix] live_show_content（[[MODE:LIVESHOW]] 區塊）也需要過濾。
                    # 未過濾時模型仍看到「3) 絕對值層級」「D4: 以 abs() 實作」等規則，
                    # 導致生成題目含絕對值，即使輸入例題沒有絕對值。
                    live_show_content = apply_strict_mirroring(live_show_content, ocr_text)

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
            "route_mode": route_mode,
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
    skill_id = data.get("skill_id")
    fraction_display_mode = data.get("fraction_display_mode", "auto")
    source_ocr_text = data.get("ocr_text", "")

    # ── Phase 4-C: 取得 json_spec（下一題結構化 profile）────────────────
    json_spec = data.get("json_spec")
    if not isinstance(json_spec, dict):
        json_spec = {}
    # 若 json_spec 帶有 ocr_text，以其為 source_ocr_text 的優先來源
    if not source_ocr_text and json_spec.get("ocr_text"):
        source_ocr_text = json_spec["ocr_text"]
    # ────────────────────────────────────────────────────────────────────

    if file_path:
        try:
            _meta = _LIVE_FILE_DISPLAY_MODE.get(os.path.abspath(file_path), {})
            if (not skill_id) and _meta.get("skill_id"):
                skill_id = _meta.get("skill_id")
            if (fraction_display_mode == "auto") and _meta.get("mode"):
                fraction_display_mode = _meta.get("mode")
            if (not source_ocr_text) and _meta.get("ocr_text"):
                source_ocr_text = _meta.get("ocr_text")
        except Exception:
            pass

    ablation_mode = data.get("ablation_mode", False)
    healer_trace = data.get("healer_trace") if isinstance(data.get("healer_trace"), dict) else {}
    fixes_from_payload = data.get("fixes", 0) or 0
    healer_trace = _init_healer_trace_impl(healer_trace, fixes_from_payload=fixes_from_payload)
    
    start_time = time.time()
    try:
        engine = get_engine()
        
        # 下一題執行防護：重用 live_show 的執行補丁，避免 file_path 舊碼造成第二題 Error
        exec_code = _optimize_live_execution_code(code)
        exec_code = _patch_fraction_skill_eval_calls(exec_code, skill_id)
        exec_code = _patch_fraction_eval_calls_heuristic(exec_code)

        # 執行程式碼
        res = engine.scaler._execute_code(exec_code, level=level)
        if "question_text" in res:
            sanitized_q, sanitize_report = _sanitize_question_text_display(
                res.get("question_text", ""),
                return_report=True
            )
            _apply_sanitize_report_to_trace_impl(healer_trace, [], sanitize_report, after_fallback=False)

            final_q, display_report = _format_fraction_mixed_display(
                sanitized_q,
                skill_id,
                display_mode=fraction_display_mode,
                source_text=source_ocr_text,
                return_report=True
            )
            _apply_display_report_to_trace_impl(healer_trace, [], display_report)
            _recompute_regex_totals_impl(healer_trace)
            res["question_text"] = final_q
            fixed_ans = _recompute_correct_answer_from_question(res.get("question_text", ""))
            if fixed_ans is not None:
                res["correct_answer"] = fixed_ans
            res["correct_answer"] = _force_fraction_answer_text(res.get("correct_answer", ""), skill_id)
        
        # ── V6.7 MCRI 真實評分（下一題路徑）──────────────────────
        live_mcri_result = None
        if "question_text" in res:
            try:
                from scripts.evaluate_mcri import evaluate_live_code
                live_mcri_result = evaluate_live_code(
                    code=exec_code,
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
            "fraction_display_mode": _infer_fraction_display_mode(source_ocr_text or res.get("question_text", ""), skill_id),
            "mcri": mcri_payload,
            "json_spec": json_spec or {},   # Phase 4-C: 傳回 structural profile，供前端連鎖下一題使用
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
