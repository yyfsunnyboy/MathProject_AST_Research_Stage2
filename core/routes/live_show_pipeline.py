# -*- coding: utf-8 -*-
"""Live Show pipeline helpers.

先以低風險方式抽出 Ab2 協調流程，讓 route 專注編排。
"""

import os
import time
import uuid
import json


def run_ab2_interception(
    *,
    scaler,
    final_code,
    api_stubs,
    skill_id,
    expected_fp,
    decimal_style_mode,
    ocr_text,
    fraction_display_mode,
    ai_inference_time_sec,
    live_file_display_mode,
    optimize_live_execution_code_fn,
    patch_fraction_skill_eval_calls_fn,
    evaluate_iso_style_guard_fn,
    build_isomorphic_fallback_code_fn,
    extract_math_expr_from_question_fn,
    has_decimal_number_fn,
    is_expression_isomorphic_fn,
    sanitize_result_question_fn,
    format_result_question_display_fn,
    recompute_result_answer_fn,
    recompute_correct_answer_from_question_fn,
    maybe_add_o1_fix_fn,
):
    ab2_exec_code = optimize_live_execution_code_fn(final_code)
    ab2_exec_code = patch_fraction_skill_eval_calls_fn(ab2_exec_code, skill_id)

    ab2_result = {}
    ab2_save_dir = "generated_scripts"
    if not os.path.exists(ab2_save_dir):
        os.makedirs(ab2_save_dir, exist_ok=True)
    ab2_filename = f"live_show_{int(time.time())}_{uuid.uuid4().hex[:6]}_ab2.py"
    ab2_file_path = os.path.join(ab2_save_dir, ab2_filename)
    ab2_final_exec_code = ab2_exec_code

    ab2_cpu_start = time.time()
    try:
        ab2_exe_res = scaler._execute_code(ab2_exec_code, level=1)
        ab2_exec_elapsed = time.time() - ab2_cpu_start
        ab2_guard = evaluate_iso_style_guard_fn(
            expected_fp=expected_fp,
            question_text=ab2_exe_res.get("question_text", ""),
            decimal_style_mode=decimal_style_mode,
            extract_expr_fn=extract_math_expr_from_question_fn,
            has_decimal_fn=has_decimal_number_fn,
            isomorphic_fn=is_expression_isomorphic_fn,
        )
        if ab2_guard.get("triggered"):
            fallback_code_ab2 = build_isomorphic_fallback_code_fn(ocr_text, skill_id=skill_id)
            if fallback_code_ab2:
                ab2_final_exec_code = patch_fraction_skill_eval_calls_fn(
                    optimize_live_execution_code_fn(fallback_code_ab2),
                    skill_id,
                )
                ab2_exe_res = scaler._execute_code(ab2_final_exec_code, level=1)
                ab2_exe_res["_ab2_iso_fallback"] = True
                if ab2_guard.get("decimal_mismatch"):
                    ab2_exe_res.setdefault("healer_logs", [])
                    ab2_exe_res["healer_logs"].append(
                        "[STYLE_GUARD] source contains decimal; switched to decimal-preserving fallback."
                    )

        if "question_text" in ab2_exe_res:
            sanitize_result_question_fn(
                ab2_exe_res,
                after_fallback=False,
            )
            format_result_question_display_fn(
                ab2_exe_res,
                skill_id,
                display_mode=fraction_display_mode,
                source_text=ocr_text,
            )

        if "question_text" in ab2_exe_res:
            recompute_result_answer_fn(
                ab2_exe_res,
                skill_id,
                recompute_answer_fn=recompute_correct_answer_from_question_fn,
            )

        try:
            from scripts.evaluate_mcri import evaluate_math_hygiene

            if "question_text" in ab2_exe_res:
                h_score, _ = evaluate_math_hygiene(ab2_exe_res["question_text"])
                ab2_exe_res["_mcri_hygiene_score"] = h_score
        except Exception:
            pass

        if ab2_exe_res.get("_o1_healed"):
            maybe_add_o1_fix_fn(
                ab2_exe_res,
                message="[O(1)_HEALER] Intelligently scaled variables to force perfect division (Native).",
            )

        ab2_result = ab2_exe_res
    except Exception as e:
        ab2_exec_elapsed = time.time() - ab2_cpu_start
        ab2_result = {"error": f"執行錯誤: {e}"}

    with open(ab2_file_path, "w", encoding="utf-8") as _fb:
        _fb.write(ab2_final_exec_code)

    try:
        live_file_display_mode[os.path.abspath(ab2_file_path)] = {
            "mode": fraction_display_mode,
            "skill_id": skill_id,
            "ocr_text": ocr_text,
        }
    except Exception:
        pass

    ab2_result["file_path"] = ab2_file_path
    ab2_result["ai_inference_time_sec"] = ai_inference_time_sec
    ab2_result["cpu_execution_time_sec"] = ab2_exec_elapsed

    final_code_with_stubs = api_stubs + "\n\n" + final_code
    ab2_result["raw_code"] = final_code_with_stubs
    ab2_result["final_code"] = final_code_with_stubs

    return {
        "ab2_result": ab2_result,
        "ab2_exec_elapsed": ab2_exec_elapsed,
        "ab2_file_path": ab2_file_path,
        "ab2_final_exec_code": ab2_final_exec_code,
        "final_code_with_stubs": final_code_with_stubs,
    }


def run_ab3_full_healer(
    *,
    scaler,
    final_code,
    skill_id,
    expected_fp,
    decimal_style_mode,
    ocr_text,
    fraction_display_mode,
    live_file_display_mode,
    optimize_live_execution_code_fn,
    patch_fraction_skill_eval_calls_fn,
    advanced_healer_fn,
    sanitize_result_question_fn,
    evaluate_iso_style_guard_fn,
    append_iso_style_guard_logs_fn,
    append_fallback_switch_log_fn,
    profile_diff_summary_fn,
    build_isomorphic_fallback_code_fn,
    extract_math_expr_from_question_fn,
    has_decimal_number_fn,
    is_expression_isomorphic_fn,
    build_structural_profile_fn,
    recompute_result_answer_fn,
    recompute_correct_answer_from_question_fn,
    format_result_question_display_fn,
    maybe_add_o1_fix_fn,
):
    cpu_start_ab3 = time.time()
    problems_result = []
    ab3_exec_elapsed = 0.0

    healed_code = final_code
    regex_fixes = 0
    regex_code_fixes = 0
    regex_display_fixes = 0
    ast_fixes = 0
    o1_fixes = 0
    detail_logs = []
    generated_fp = {}
    iso_isomorphic = False

    try:
        healed_code, *healer_stats = advanced_healer_fn(final_code, ablation_id=3, skill_id=skill_id)
        regex_code_fixes = healer_stats[0] if len(healer_stats) > 0 else 0
        regex_fixes = regex_code_fixes
        ast_fixes = healer_stats[1] if len(healer_stats) > 1 else 0
        ast_stats = healer_stats[2] if len(healer_stats) > 2 else None
        detail_logs = getattr(ast_stats, "logs", []) if ast_stats else []
        print(f"=== [VL Pipeline Healer] Success! Regex: {regex_fixes}, AST: {ast_fixes} ===")
    except Exception:
        import traceback
        print("=== [VL Pipeline Healer] CRASHED ===")
        traceback.print_exc()
        healed_code = final_code

    healed_exec_code = patch_fraction_skill_eval_calls_fn(
        optimize_live_execution_code_fn(healed_code),
        skill_id,
    )

    try:
        exe_res = scaler._execute_code(healed_exec_code, level=1)
        if "question_text" in exe_res:
            trace_seed = {
                "regex_code_fixes": regex_code_fixes,
                "regex_display_fixes": regex_display_fixes,
                "ast_fixes": ast_fixes,
                "o1_fixes": o1_fixes,
            }
            sanitize_report, trace_shadow = sanitize_result_question_fn(
                exe_res,
                detail_logs=detail_logs,
                after_fallback=False,
                trace_seed=trace_seed,
            )
            regex_display_fixes = int(trace_shadow.get("regex_display_fixes", 0) or 0)
            regex_fixes = int(trace_shadow.get("regex_fixes", 0) or 0)
            sanitize_meta = sanitize_report if isinstance(sanitize_report, dict) else {}
            double_paren_cnt = int(sanitize_meta.get("double_paren_fixes", 0) or 0)
            negative_wrap_cnt = int(sanitize_meta.get("negative_wrap_fixes", 0) or 0)
            if double_paren_cnt > 0:
                detail_logs.append(f"[DISPLAY_SANITIZE] collapsed {double_paren_cnt} nested numeric parenthesis pattern(s).")
            if negative_wrap_cnt > 0:
                detail_logs.append(f"[DISPLAY_SANITIZE] wrapped {negative_wrap_cnt} bare negative literal(s) with parentheses.")

        generated_expr = extract_math_expr_from_question_fn(exe_res.get("question_text", ""))
        guard_meta = evaluate_iso_style_guard_fn(
            expected_fp=expected_fp,
            question_text=exe_res.get("question_text", ""),
            decimal_style_mode=decimal_style_mode,
            extract_expr_fn=extract_math_expr_from_question_fn,
            has_decimal_fn=has_decimal_number_fn,
            isomorphic_fn=is_expression_isomorphic_fn,
        )
        decimal_mismatch = bool(guard_meta.get("decimal_mismatch"))
        if guard_meta.get("triggered"):
            append_iso_style_guard_logs_fn(
                detail_logs,
                expected_fp,
                generated_expr,
                decimal_mismatch,
                is_expression_isomorphic_fn,
                profile_diff_summary_fn,
            )

            fallback_code = build_isomorphic_fallback_code_fn(ocr_text, skill_id=skill_id)
            if fallback_code:
                healed_code = fallback_code
                healed_exec_code = optimize_live_execution_code_fn(healed_code)
                healed_exec_code = patch_fraction_skill_eval_calls_fn(healed_exec_code, skill_id)
                exe_res = scaler._execute_code(healed_exec_code, level=1)
                if "question_text" in exe_res:
                    trace_seed_2 = {
                        "regex_code_fixes": regex_code_fixes,
                        "regex_display_fixes": regex_display_fixes,
                        "ast_fixes": ast_fixes,
                        "o1_fixes": o1_fixes,
                    }
                    sanitize_report2, trace_shadow_2 = sanitize_result_question_fn(
                        exe_res,
                        detail_logs=detail_logs,
                        after_fallback=True,
                        trace_seed=trace_seed_2,
                    )
                    regex_display_fixes = int(trace_shadow_2.get("regex_display_fixes", 0) or 0)
                    regex_fixes = int(trace_shadow_2.get("regex_fixes", 0) or 0)
                    sanitize_meta_2 = sanitize_report2 if isinstance(sanitize_report2, dict) else {}
                    double_paren_cnt_2 = int(sanitize_meta_2.get("double_paren_fixes", 0) or 0)
                    negative_wrap_cnt_2 = int(sanitize_meta_2.get("negative_wrap_fixes", 0) or 0)
                    if double_paren_cnt_2 > 0:
                        detail_logs.append(f"[DISPLAY_SANITIZE] collapsed {double_paren_cnt_2} nested numeric parenthesis pattern(s) after fallback.")
                    if negative_wrap_cnt_2 > 0:
                        detail_logs.append(f"[DISPLAY_SANITIZE] wrapped {negative_wrap_cnt_2} bare negative literal(s) after fallback.")
                append_fallback_switch_log_fn(detail_logs, decimal_mismatch)

                generated_expr_2 = extract_math_expr_from_question_fn(exe_res.get("question_text", ""))
                if not is_expression_isomorphic_fn(expected_fp, generated_expr_2):
                    for d in profile_diff_summary_fn(expected_fp, generated_expr_2):
                        detail_logs.append(f"[ISO_GUARD][FALLBACK_FAIL] {d}")
                    raise ValueError("ISO_GUARD fallback failed: generated structure still not isomorphic")

        generated_expr_final = extract_math_expr_from_question_fn(exe_res.get("question_text", ""))
        generated_fp = build_structural_profile_fn(generated_expr_final)
        iso_isomorphic = is_expression_isomorphic_fn(expected_fp, generated_expr_final)
        recompute_result_answer_fn(
            exe_res,
            skill_id,
            recompute_answer_fn=recompute_correct_answer_from_question_fn,
            detail_logs=detail_logs,
            append_change_logs=True,
        )

        if "question_text" in exe_res:
            trace_seed_3 = {
                "regex_code_fixes": regex_code_fixes,
                "regex_display_fixes": regex_display_fixes,
                "ast_fixes": ast_fixes,
                "o1_fixes": o1_fixes,
            }
            _, trace_shadow_3 = format_result_question_display_fn(
                exe_res,
                skill_id,
                display_mode=fraction_display_mode,
                source_text=ocr_text,
                detail_logs=detail_logs,
                trace_seed=trace_seed_3,
            )
            regex_display_fixes = int(trace_shadow_3.get("regex_display_fixes", 0) or 0)
            regex_fixes = int(trace_shadow_3.get("regex_fixes", 0) or 0)

        if exe_res.get("_o1_healed"):
            trace_o1 = maybe_add_o1_fix_fn(
                exe_res,
                detail_logs=detail_logs,
                trace_seed={
                    "o1_fixes": o1_fixes,
                    "regex_code_fixes": regex_code_fixes,
                    "regex_display_fixes": regex_display_fixes,
                    "ast_fixes": ast_fixes,
                },
            )
            if isinstance(trace_o1, dict):
                o1_fixes = int(trace_o1.get("o1_fixes", o1_fixes) or o1_fixes)

        ab3_exec_elapsed = time.time() - cpu_start_ab3

        try:
            from scripts.evaluate_mcri import evaluate_live_code

            if "question_text" in exe_res:
                _live_mcri = evaluate_live_code(
                    code=healed_exec_code,
                    exec_result=exe_res,
                    healer_trace={"regex_fixes": regex_fixes, "ast_fixes": ast_fixes},
                    ablation_mode=False,
                )
                exe_res["_live_mcri"] = _live_mcri
                exe_res["_mcri_hygiene_score"] = _live_mcri["breakdown"].get("l4_3_hygiene", 15.0)
        except Exception:
            pass

        problems_result.append(exe_res)
    except Exception as e:
        ab3_exec_elapsed = time.time() - cpu_start_ab3
        problems_result.append({"error": f"執行錯誤: {e}"})

    save_dir = "generated_scripts"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)
    unique_filename = f"live_show_{int(time.time())}_{uuid.uuid4().hex[:6]}.py"
    file_path = os.path.join(save_dir, unique_filename)
    with open(file_path, "w", encoding="utf-8") as _fb:
        _fb.write(healed_exec_code)

    try:
        live_file_display_mode[os.path.abspath(file_path)] = {
            "mode": fraction_display_mode,
            "skill_id": skill_id,
            "ocr_text": ocr_text,
        }
    except Exception:
        pass

    return {
        "problems_result": problems_result,
        "cpu_execution_time_sec": ab3_exec_elapsed,
        "healed_code": healed_code,
        "healed_exec_code": healed_exec_code,
        "file_path": file_path,
        "regex_fixes": regex_fixes,
        "regex_code_fixes": regex_code_fixes,
        "regex_display_fixes": regex_display_fixes,
        "ast_fixes": ast_fixes,
        "o1_fixes": o1_fixes,
        "detail_logs": detail_logs,
        "generated_fp": generated_fp,
        "iso_isomorphic": iso_isomorphic,
    }


def assemble_visual_output(
    *,
    problems_result,
    ai_inference_time_sec,
    cpu_execution_time_sec,
    raw_out,
    api_stubs,
    healed_code,
    file_path,
    system_prompt,
    json_spec,
    regex_fixes,
    regex_code_fixes,
    regex_display_fixes,
    ast_fixes,
    o1_fixes,
    detail_logs,
    expected_fp,
    generated_fp,
    iso_isomorphic,
    fraction_display_mode,
    ab2_result,
):
    return {
        "problems": problems_result,
        "debug_meta": {
            "performance": {
                "ai_inference_time_sec": ai_inference_time_sec,
                "cpu_execution_time_sec": cpu_execution_time_sec,
            },
            "raw_code": raw_out,
            "final_code": api_stubs + "\n\n" + healed_code,
            "file_path": file_path,
            "bare_prompt": "",
            "scaffold_prompt": system_prompt,
            "gemini_raw_spec": json.dumps(json_spec, ensure_ascii=False, indent=2) if json_spec else "",
            "architect_model": "Qwen3-VL",
            "healer_trace": {
                "regex_fixes": regex_fixes,
                "regex_code_fixes": regex_code_fixes,
                "regex_display_fixes": regex_display_fixes,
                "ast_fixes": ast_fixes,
                "o1_fixes": o1_fixes,
            },
            "healer_logs": detail_logs if isinstance(detail_logs, list) else [],
            "iso_profile_expected": expected_fp,
            "iso_profile_generated": generated_fp,
            "iso_isomorphic": iso_isomorphic,
            "fraction_display_mode": fraction_display_mode,
            "mcri_report": {
                "robustness_grade": "MODERATE",
                "robustness_reason": "Visual Generation with Full Healer",
            },
        },
        "ab2_result": ab2_result,
    }
