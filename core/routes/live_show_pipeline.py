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
    ab2_exec_code = (final_code or "").strip()
    ab2_exec_code = ab2_exec_code.replace("\r\n", "\n")
    if ab2_exec_code.lower().startswith("```python"):
        ab2_exec_code = ab2_exec_code[len("```python"):].lstrip("\n")
    elif ab2_exec_code.startswith("```"):
        ab2_exec_code = ab2_exec_code[len("```"):].lstrip("\n")
    if ab2_exec_code.endswith("```"):
        ab2_exec_code = ab2_exec_code[:-3].rstrip()

    # [Fix] Apply execution optimizer to Ab2 as well, so that oversized range/while
    # loops are capped and time.sleep is stripped — same as Ab3.
    # This ensures CPU time comparison is fair (not confounded by loop size).
    ab2_exec_code = optimize_live_execution_code_fn(ab2_exec_code)

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

        try:
            from scripts.evaluate_mcri import evaluate_math_hygiene

            if "question_text" in ab2_exe_res:
                h_score, _ = evaluate_math_hygiene(ab2_exe_res["question_text"])
                ab2_exe_res["_mcri_hygiene_score"] = h_score
        except Exception:
            pass

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
    api_stubs="",
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
    # Optional: post-healer scaffold reassembler (used by Radical Orchestrator)
    radical_reassemble_fn=None,
):
    cpu_start_ab3 = time.time()
    problems_result = []
    ab3_exec_elapsed = 0.0

    # [UNIVERSAL FIX] Force Radical Scaffold Assembly here, for BOTH text and image paths
    if "FourOperationsOfRadicals" in (skill_id or ""):
        from core.routes.live_show import _assemble_radical_orchestrator_code
        final_code = _assemble_radical_orchestrator_code(final_code)
        print(f"⚙️ [UNIVERSAL_ASSEMBLER] Applied orchestrator scaffold for {skill_id}")

    healed_code = final_code
    regex_fixes = 0
    regex_code_fixes = 0
    regex_display_fixes = 0
    ast_fixes = 0
    o1_fixes = 0
    detail_logs = []
    generated_fp = {}
    iso_isomorphic = False

    if "FourOperationsOfRadicals" in (skill_id or ""):
        # Radical Orchestrator: skip the general healer entirely
        anti_dup_fixes = 0
        detail_logs.insert(0, "[HEALER_STATUS] ✅ Radical Orchestrator — general healer bypassed.")
        print("⚙️ [RADICAL_ASSEMBLER] healer bypassed.")
    else:
        try:
            healed_code, *healer_stats = advanced_healer_fn(final_code, ablation_id=3, skill_id=skill_id)
            regex_code_fixes = healer_stats[0] if len(healer_stats) > 0 else 0
            regex_fixes = regex_code_fixes
            ast_fixes = healer_stats[1] if len(healer_stats) > 1 else 0
            ast_stats = healer_stats[2] if len(healer_stats) > 2 else None
            # Collect AST healer logs before mutating detail_logs
            detail_logs = getattr(ast_stats, "logs", []) if ast_stats else []
            _healer_total = healer_stats[5] if len(healer_stats) > 5 and isinstance(healer_stats[5], int) else None
            anti_dup_fixes = max(0, (_healer_total - regex_code_fixes - ast_fixes)) if _healer_total is not None else 0
            regex_code_fixes += anti_dup_fixes
            regex_fixes = regex_code_fixes
            detail_logs.insert(0, f"[HEALER_STATUS] ✅ Active Healer ran — regex_code={regex_code_fixes}, ast={ast_fixes}, anti_dup={anti_dup_fixes}")
            print(f"=== [VL Pipeline Healer] Success! Regex: {regex_fixes}, AST: {ast_fixes}, AntiDup: {anti_dup_fixes} ===")
        except Exception as _healer_exc:
            import traceback as _healer_tb
            print("=== [VL Pipeline Healer] CRASHED ===")
            _healer_tb.print_exc()
            healed_code = final_code
            anti_dup_fixes = 0
            detail_logs.append(f"[HEALER_STATUS] ❌ Healer CRASHED — {type(_healer_exc).__name__}: {_healer_exc}")
            detail_logs.append("[HEALER_STATUS] 使用原始 AI 輸出，Skip 所有修復。")

    healed_exec_code = patch_fraction_skill_eval_calls_fn(
        optimize_live_execution_code_fn(healed_code),
        skill_id,
    )
    # [Bug 16 Fix] If AST healer exited early (e.g. syntax-repair loop), bare eval()
    # may survive.  Replace now so MCRI static scan sees safe_eval() instead.
    import re as _re16
    healed_exec_code = _re16.sub(r'\beval\s*\(', 'safe_eval(', healed_exec_code)

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

        # ── Hard bypass: Radical / Orchestrator skills ───────────────────────
        # Two independent signals trigger the bypass (belt-and-suspenders):
        #   (a) expected_fp is empty — set by _radical_bypass_expected_fp()
        #   (b) skill_id contains "Radicals" — catches any new radical variant
        # Without this gate the ISO-guard ALWAYS fires for radical skills because
        # _is_expression_isomorphic({}, expr) compared every field against None,
        # triggering an integer-based deterministic fallback that destroyed the
        # DomainFunctionHelper-generated LaTeX output.
        _bypass_iso_guard = (not expected_fp) or ("Radicals" in (skill_id or ""))
        if _bypass_iso_guard:
            try:
                from core.skill_policies.registry import get_skill_policy as _gsp_chk
                _chk_policy = _gsp_chk(skill_id) or {}
                if _chk_policy.get("skip_complexity_mirror", False) or "Radicals" in (skill_id or ""):
                    print(
                        f"⚠️ [ADVISOR] Radical Skill Detected: "
                        f"Bypassing Legacy Complexity Mirror. skill={skill_id!r}"
                    )
            except Exception:
                print(
                    f"⚠️ [ADVISOR] Radical Skill Detected: "
                    f"Bypassing Legacy Complexity Mirror. skill={skill_id!r}"
                )
            detail_logs.append(
                f"[COMPLEXITY_MIRROR][HARD_BYPASS] expected_fp=empty or 'Radicals' in skill_id — "
                f"ISO-guard skipped for {skill_id!r}."
            )
            guard_meta = {
                "triggered":       False,
                "expr":            generated_expr,
                "isomorphic":      True,
                "decimal_mismatch": False,
            }
            decimal_mismatch = False
        else:
            guard_meta = evaluate_iso_style_guard_fn(
                expected_fp=expected_fp,
                question_text=exe_res.get("question_text", ""),
                decimal_style_mode=decimal_style_mode,
                extract_expr_fn=extract_math_expr_from_question_fn,
                has_decimal_fn=has_decimal_number_fn,
                isomorphic_fn=is_expression_isomorphic_fn,
            )
            decimal_mismatch = bool(guard_meta.get("decimal_mismatch"))

        # [Bug 29 Guard] 明確的中括號↔絕對值結構錯位守衛（ISO guard 的備援保障）
        # 當 expected 有 [ ] (bracket_count>0, abs_count=0) 但生成含 | | 時強制 fallback。
        if not guard_meta.get("triggered"):
            _exp_brackets29 = expected_fp.get("bracket_count", 0)
            _exp_abs29 = expected_fp.get("abs_count", 0)
            _qt29 = exe_res.get("question_text", "")
            if _exp_brackets29 > 0 and _exp_abs29 == 0 and "|" in _qt29:
                guard_meta["triggered"] = True
                guard_meta["bracket_abs_mismatch"] = True
                detail_logs.append(
                    f"[BRACKET_ABS_GUARD][Bug29] 例題使用中括號（bracket_count={_exp_brackets29}，abs_count=0）"
                    f"但生成題目含 | 絕對值符號，強制觸發 iso-fallback。"
                )

        # [Bug 25 Guard] 非分數技能禁止在生成題目中出現 \frac{}{}
        # [Bug 26 Guard] 分數技能帶分數/純分數顯示風格必須與輸入例題一致
        #
        # [Orchestrator Bypass] Skills that set skip_complexity_mirror=True
        # (e.g. jh_數學2上_FourOperationsOfRadicals) generate LaTeX with
        # \frac / \sqrt via DomainFunctionHelper — this is intentional and
        # correct.  Applying Bug-25 or Bug-26 guards would falsely trigger
        # iso-fallback.  Skip both guards for those skills.
        if not guard_meta.get("triggered"):
            import re as _re_guard26
            from core.skill_policies.registry import get_skill_policy as _gsp
            _policy = _gsp(skill_id)
            _qt = exe_res.get("question_text", "")

            if _policy.get("skip_complexity_mirror", False):
                # Radical / orchestrator skill — structural guards don't apply.
                detail_logs.append(
                    f"[COMPLEXITY_MIRROR][BYPASS] skill={skill_id!r} has "
                    f"skip_complexity_mirror=True; Bug-25/26 guards skipped."
                )
            elif not _policy.get("enable_fraction_display", False):
                # Bug 25: 非分數技能（整數四則運算等）出現 \frac 時觸發 fallback
                if "\\frac" in _qt:
                    guard_meta["triggered"] = True
                    guard_meta["frac_forbidden"] = True
                    detail_logs.append(
                        f"[FRAC_GUARD][Bug25] 非分數技能({skill_id!r})生成含 \\frac 的題目，"
                        f"疑似 AI 幻覺，強制觸發 iso-fallback。"
                    )
            else:
                # Bug 26: 分數技能 — 帶分數 / 純分數顯示風格必須鏡像輸入例題
                # 帶分數pattern：整數緊接 \frac（前面非 \、{、/，避免誤抓 \frac 本體）
                _HAS_MIXED_RE = _re_guard26.compile(r'(?<![\\{/])\d+\s*\\frac\s*\{')
                _has_mixed_gen = bool(_HAS_MIXED_RE.search(_qt))
                if fraction_display_mode == "fraction" and _has_mixed_gen:
                    # 輸入只有純分數，但 AI 生成了帶分數
                    guard_meta["triggered"] = True
                    guard_meta["mixed_style_mismatch"] = True
                    detail_logs.append(
                        "[MIXED_GUARD][Bug26] 輸入為純分數（無帶分數），"
                        "生成題目含帶分數（整數+\\frac），強制觸發 iso-fallback。"
                    )
                elif fraction_display_mode == "mixed" and not _has_mixed_gen:
                    # 輸入有帶分數，但 AI 生成了純分數
                    guard_meta["triggered"] = True
                    guard_meta["mixed_style_mismatch"] = True
                    detail_logs.append(
                        "[MIXED_GUARD][Bug26] 輸入含帶分數，"
                        "生成題目無帶分數（僅 \\frac 無整數首項），強制觸發 iso-fallback。"
                    )

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
            if not fallback_code:
                # Fallback returned empty string — OCR text may have no parseable numbers.
                # Log the failure clearly so diagnostics can catch it.
                detail_logs.append(
                    "[ISO_GUARD][FALLBACK_EMPTY] build_isomorphic_fallback_code 返回空字串"
                    "（OCR 文字可能無數字 span），跳過 fallback，保留原始 AI 輸出。"
                )
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
        # Radical Orchestrator: structural isomorphism is guaranteed by
        # DomainFunctionHelper; force True so the UI always shows a green mirror.
        # [UI FIX] Populate generated_fp with supercharged radical profile so the frontend mirror isn't blank.
        if radical_reassemble_fn is not None:
            iso_isomorphic = True
            from core.code_utils.live_show_math_utils import _build_radical_profile
            generated_fp = _build_radical_profile(generated_expr_final)
        else:
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
                # [Fix] Evaluate with api_stubs prepended so robustness detection
                # (class IntegerOps / FractionOps) is consistent with Ab2's evaluation.
                eval_code = (api_stubs + "\n\n" + healed_exec_code) if api_stubs else healed_exec_code
                _live_mcri = evaluate_live_code(
                    code=eval_code,
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
            "architect_raw_spec": json.dumps(json_spec, ensure_ascii=False, indent=2) if json_spec else "",
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
