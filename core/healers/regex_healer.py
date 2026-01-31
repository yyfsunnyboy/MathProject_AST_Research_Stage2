# -*- coding: utf-8 -*-
# ==============================================================================
# ID: core/healers/regex_healer.py
# Version: V2.1 (Refactored from code_generator.py)
# Last Updated: 2026-01-30
# Author: Math AI Research Team (Advisor & Student)
#
# [Description]:
#   Regex 修復引擎 - 處理文字層級的問題
#   [Active Healer V9.2.1] 針對 14B 模型「不聽話」特性的強力矯正
#
# [Functionality]:
#   1. 幻覺函數殺除 (clean_expression, format_num 等)
#   2. 返回格式修復 (dict key 標準化)
#   3. 危險 import 移除 (os, sys, subprocess)
#   4. 註釋和 Markdown 清理
#   5. 縮排和格式修正
#
# [Logic Flow]:
#   1. Input Code -> Regex Pattern Matching
#   2. Replace/Remove -> Fixed Code
#   3. Track Fix Count -> Metrics
#
# [Helper Functions]:
#   - clean_redundant_imports: 保留所有 import（不刪除）
#   - remove_forbidden_functions_unified: 移除禁止的函數定義
# ==============================================================================

import re
import logging

logger = logging.getLogger(__name__)

# 預編譯的正則表達式 Patterns (性能優化)
COMPILED_PATTERNS = {
    'clean_expression': re.compile(r'clean_expression\('),
}

class RegexHealer:
    """
    Regex 修復引擎 - 處理文字層級的問題
    [Active Healer V9.2.1] 針對 14B 模型「不聽話」特性的強力矯正
    
    功能：
    1. 幻覺函數殺除 (clean_expression, format_num 等)
    2. 返回格式修復 (dict key 標準化)
    3. 未定義變數修復 (反向推導問題)
    4. 垃圾字元清理 (孤立反引號、特殊符號)
    5. Tuple Return 修復 (return q, a -> return dict)
    6. 語義錯誤修復 (ensure_xxx 參數類型檢查)
    7. Float/Fraction 一致性修復
    8. LaTeX 格式修復 (移除中文題幹中的 $)
    9. Eval 消除器 (safe_eval -> 直接計算)
    """
    
    def __init__(self):
        """初始化 Regex Healer"""
        self.forbidden_chars = ['\u200b', '\ufeff']  # 零寬字元
        self.forbidden_funcs = [
            'format_number_for_latex', 'format_num_latex', 
            'latex_format', '_format_term_with_parentheses'
        ]
    
    def heal(self, code_str: str) -> tuple:
        """
        執行 Regex 修復
        
        Args:
            code_str: 原始代碼字串
            
        Returns:
            tuple: (修復後代碼, 修復次數)
        """
        fixes = 0
        refined_code = code_str

        # -----------------------------------------------------------
        # 0. [Complexity Checker] 檢測過於簡單的代碼（可能抄襲範例）
        # -----------------------------------------------------------
        complexity_warnings = []
        
        num_random_ints = len(re.findall(r'random\.randint\(', code_str))
        num_fractions = len(re.findall(r'Fraction\(', code_str))
        total_operands = num_random_ints + num_fractions
        
        if total_operands < 3:
            complexity_warnings.append(f"⚠️  運算數過少: 僅發現 {total_operands} 個變數生成")
        
        has_multiply = '*' in code_str or '\\times' in code_str
        has_divide = '/' in code_str or '\\div' in code_str
        
        if not (has_multiply or has_divide):
            complexity_warnings.append("⚠️  缺少乘除運算: 僅發現加減運算")
        
        if num_fractions == 0:
            complexity_warnings.append("⚠️  未使用分數: 可能全為整數")
        
        code_lines = [line for line in code_str.split('\n') if line.strip() and not line.strip().startswith('#')]
        if len(code_lines) < 10:
            complexity_warnings.append(f"⚠️  代碼過短: 僅 {len(code_lines)} 行有效代碼")
        
        if complexity_warnings:
            print("=" * 60)
            print("🔴 [Complexity Checker] 偵測到可能未完整實現 MASTER_SPEC:")
            for warning in complexity_warnings:
                print(f"   {warning}")
            print("   建議檢查: MASTER_SPEC 的 complexity_requirements 和 implementation_checklist")
            print("=" * 60)

        # -----------------------------------------------------------
        # 0.5 [Undefined Variable Healer] 修復反向推導中的未定義變數
        # -----------------------------------------------------------
        undefined_vars = []
        for var_name in ['final_result', 'target_value', 'answer_value', 'result_value', 'tangent_x0', 'tangent_y0']:
            usage_pattern = rf'\b{var_name}\b\s*[/\-+*%]|[/\-+*%=]\s*\b{var_name}\b|while.*\b{var_name}\b'
            definition_pattern = rf'\b{var_name}\s*='
            
            if re.search(usage_pattern, refined_code):
                usage_match = re.search(usage_pattern, refined_code)
                usage_pos = usage_match.start()
                
                pre_code = refined_code[:usage_pos]
                if not re.search(definition_pattern, pre_code):
                    undefined_vars.append(var_name)
        
        if undefined_vars:
            print(f"🔧 [Healer] 偵測到未定義變數使用順序問題: {', '.join(undefined_vars)}")
            
            gen_pattern = r'(def generate\(.*?\):\n\s+import random\n)'
            gen_match = re.search(gen_pattern, refined_code)
            
            if gen_match:
                injection_lines = []
                for var_name in undefined_vars:
                    if var_name in ['tangent_x0', 'x0']:
                        injection_lines.append(f"    {var_name} = random.choice([-2, -1, 0, 1, 2])")
                    elif var_name in ['tangent_y0', 'y0']:
                        injection_lines.append(f"    {var_name} = 0  # Will be calculated later")
                    else:
                        injection_lines.append(f"    {var_name} = random.randint(-50, 50)")
                        injection_lines.append(f"    if {var_name} == 0: {var_name} = 1  # 確保非零")
                
                if injection_lines:
                    injection_code = '\n'.join(injection_lines) + '\n'
                    insert_pos = gen_match.end()
                    refined_code = refined_code[:insert_pos] + f"    # [Auto-Healer] 預先定義未定義變數\n" + injection_code + refined_code[insert_pos:]
                    
                    fixes += len(undefined_vars)
                    print(f"   ✅ 已在 generate() 開頭注入 {len(undefined_vars)} 個變數的初始定義")
            else:
                print(f"   ⚠️  無法找到 generate() 函數定義，無法注入變數")

        # -----------------------------------------------------------
        # 0.9 [Loop Breaker] 無窮迴圈破壞者 (CRITICAL SAFETY)
        # -----------------------------------------------------------
        # 在 AST 解析前，強制將危險的 while 迴圈加上計數器限制
        # 這樣即使 AST Healer 失敗，至少迴圈會有個極限
        dangerous_loops = ['while True:', 'while 1:', 'while (True):', 'while (1):']
        if any(loop in refined_code for loop in dangerous_loops):
            print(f"🔧 [Loop Breaker] 偵測到危險的無限迴圈，正在轉換為有限迴圈...")
            original_code = refined_code
            
            # Pattern 1: while True: -> for _safety_counter in range(1000):
            refined_code = re.sub(
                r'(\s*)while\s+(True|1|\(True\)|\(1\))\s*:',
                r'\1for _safety_counter in range(1000):  # Safety: converted from while True',
                refined_code
            )
            
            if refined_code != original_code:
                fixes += 1
                print(f"   ✅ 已強制替換無限迴圈為有限迴圈（最多 1000 次）")
                print(f"   ⚠️  警告：這是緊急保護措施，請檢查生成邏輯是否正確")


        # -----------------------------------------------------------
        # 0.95 [Advanced Loop Pattern Fixer] 修復 while len(...) < target 模式
        # -----------------------------------------------------------
        # 簡化版：只替換 while len(...) 為 for loop with safety counter
        
        pattern = r'(\s*)while\s+len\(\s*(\w+)\s*\)\s*<\s*(\w+)\s*:'
        matches = list(re.finditer(pattern, refined_code))
        
        if matches:
            print(f"🔧 [Advanced Loop Fixer] 偵測到危險的 while len(...) 模式，正在重構...")
            
            for match in reversed(matches):  # 從後往前處理
                indent = match.group(1)
                var_name = match.group(2)
                target_var = match.group(3)
                
                # 簡單替換：while len(xxx) < target: → for _attempt in range(100):
                # 並在 for 內部添加 break 條件
                original_while = match.group(0)
                
                # 新的 for loop 頭部
                new_for_loop = f"{indent}for _attempt in range(100):  # Safety: converted from while len({var_name}) < {target_var}"
                
                # 替換
                refined_code = refined_code[:match.start()] + new_for_loop + refined_code[match.end():]
                
                # 在 for loop 後面插入 break 條件（下一行）
                # 找到下一行的位置
                next_line_start = match.end()
                next_newline = refined_code.find('\n', next_line_start)
                if next_newline != -1:
                    # 插入 break 條件
                    break_line = f"\n{indent}    if len({var_name}) >= {target_var}: break"
                    refined_code = refined_code[:next_newline] + break_line + refined_code[next_newline:]
                
                fixes += 1
            
            print(f"   ✅ 已修復 {len(matches)} 處危險的 while len(...) 模式")
            print(f"   提示：建議使用 shuffle + slice 模式替代 while len(...)") 




        # -----------------------------------------------------------
        # 1. [Garbage Cleaner] 移除 AI 生成的孤立字元和垃圾語法
        # -----------------------------------------------------------
        garbage_patterns = [
            (r'^\s*`\d*\s*$', ''),
            (r'(\n\s*)`(\d*)\s*\n', r'\1\n'),
            (r'^\s*```\s*$', ''),
            (r'^\s*\.\.\.$', ''),
        ]
        
        for pattern, replacement in garbage_patterns:
            original = refined_code
            refined_code = re.sub(pattern, replacement, refined_code, flags=re.MULTILINE)
            if refined_code != original:
                count = original.count('\n') - refined_code.count('\n') + 1
                print(f"🔧 [Healer] 移除孤立字元: {pattern[:30]}... ({count} 處)")
                fixes += count

        # -----------------------------------------------------------
        # 2. [Hallucination Killer] 殺死自創函式，強制導回標準工具
        # -----------------------------------------------------------
        if "clean_expression" in refined_code:
            refined_code, n = COMPILED_PATTERNS['clean_expression'].subn('clean_latex_output(', refined_code)
            if n > 0:
                print(f"🔧 [Healer] 矯正幻覺函式: clean_expression -> clean_latex_output ({n} 處)")
                fixes += n

        if "def clean_expression" in refined_code:
            refined_code, n = re.subn(r'(def clean_expression.*?:)', r'# \1 (Removed by Healer)', refined_code)
            fixes += n

        # -----------------------------------------------------------
        # 3. [Tuple Return Fixer] 修復錯誤的 tuple 返回格式
        # -----------------------------------------------------------
        tuple_return_patterns = [
            r'return\s+(\w+),\s*(\w+)\s*$',
            r'return\s+([qa]|question|answer|result),\s*([qa]|question|answer|result)\s*$'
        ]
        
        for pattern in tuple_return_patterns:
            match = re.search(pattern, refined_code, re.MULTILINE)
            if match:
                var1 = match.group(1)
                var2 = match.group(2)
                
                print(f"🔧 [Healer] 偵測到 tuple 返回格式: return {var1}, {var2}")
                print(f"   正在轉換為標準 dict 格式...")
                
                new_return = f"return {{'question_text': {var1}, 'correct_answer': {var2}, 'answer': {var2}, 'mode': 1}}"
                refined_code = re.sub(pattern, new_return, refined_code, flags=re.MULTILINE)
                fixes += 1
                print(f"   ✅ 已修復: {new_return}")
                break

        # -----------------------------------------------------------
        # 4. [Overly Strict Constraint Remover] 移除過度嚴格的複雜度約束
        # -----------------------------------------------------------
        overly_strict_patterns = [
            r'if\s+(?:isinstance\([^)]+,\s*Fraction\)\s*and\s*)?(?:\()?abs\([^)]+\.numerator\)\s*>\s*\d+\s+or\s+abs\([^)]+\.denominator\)\s*>\s*\d+(?:\))?\s*:\s*\n\s+raise\s+ValueError\(["\']Final result exceeds complexity constraints["\'][^\n]*\)',
            r'if\s+isinstance\([^)]+,\s*Fraction\)\s*:\s*\n\s+if\s+abs\([^)]+\.numerator\)\s*>\s*\d+\s+or\s+abs\([^)]+\.denominator\)\s*>\s*\d+\s*:\s*\n\s+raise\s+ValueError\(["\'][^"\']*complexity[^"\']*["\'][^\n]*\)',
        ]
        
        for pattern in overly_strict_patterns:
            matches = re.findall(pattern, refined_code, re.MULTILINE | re.DOTALL)
            if matches:
                print(f"🔧 [Healer] 偵測到過度嚴格的複雜度約束 ({len(matches)} 處)")
                print(f"   這會導致 Dynamic Sampling 失敗，正在移除...")
                
                refined_code = re.sub(pattern, '', refined_code, flags=re.MULTILINE | re.DOTALL)
                fixes += len(matches)
                print(f"   ✅ 已移除 {len(matches)} 個不合理的運行時約束")

        # -----------------------------------------------------------
        # 5. [Return Format Fixer] 強制修復回傳字典格式
        # -----------------------------------------------------------
        has_wrong_key = re.search(r"['\"]question['\"]\s*:", refined_code)
        
        if has_wrong_key:
            print(f"🔧 [Healer] 偵測到錯誤的 Return Key，正在重組...")
            
            refined_code, n1 = re.subn(r"(['\"])question\1\s*:", r"'question_text':", refined_code)
            
            if "'correct_answer'" not in refined_code and '"correct_answer"' not in refined_code:
                return_pattern = r"return\s*\{([^}]+)\}"
                match = re.search(return_pattern, refined_code)
                
                if match:
                    dict_content = match.group(1)
                    
                    if re.search(r"['\"]answer['\"]", dict_content) and not re.search(r"['\"]correct_answer['\"]", dict_content):
                        ans_match = re.search(r"['\"]answer['\"]\s*:\s*f['\"]([^'\"]+)['\"]", dict_content)
                        if ans_match:
                            ans_value = f"f'{ans_match.group(1)}'"
                        else:
                            ans_match = re.search(r"['\"]answer['\"]\s*:\s*['\"]([^'\"]+)['\"]", dict_content)
                            if ans_match:
                                ans_value = f"'{ans_match.group(1)}'"
                            else:
                                ans_match = re.search(r"['\"]answer['\"]\s*:\s*([a-zA-Z_]\w*)", dict_content)
                                if ans_match:
                                    ans_value = ans_match.group(1)
                                else:
                                    ans_value = "a"
                        
                        new_dict_content = f"'question_text': q, 'correct_answer': {ans_value}, 'answer': {ans_value}, 'mode': 1"
                        new_return = f"return {{{new_dict_content}}}"
                        
                        refined_code = re.sub(return_pattern, new_return, refined_code)
                        fixes += 1
                        print(f"🔧 [Healer] 重建 return 語句：{new_return[:80]}...")

        # -----------------------------------------------------------
        # 6. [Semantic Error Fixer] 修復函數調用的參數類型不匹配
        # -----------------------------------------------------------
        semantic_error_patterns = [
            (r'while\s+.*?ensure_\w+\s*\(\s*operators\s*\)', 'operators passed to operand-checking function'),
            (r'while\s+.*?\<\s*\d+\s*:\s*\n\s+for\s+\w+\s+in\s+range', 'unsafe loop structure'),
        ]
        
        for pattern_str, error_desc in semantic_error_patterns:
            pattern = re.compile(pattern_str, re.MULTILINE | re.DOTALL)
            matches = list(pattern.finditer(refined_code))
            
            if matches:
                print(f"🔧 [Healer V47.6] 偵測到 {len(matches)} 個語義錯誤: {error_desc}")
                
                for match in reversed(matches):
                    start_pos = match.start()
                    
                    before_match = refined_code[:start_pos]
                    match_indent = len(before_match.split('\n')[-1])
                    
                    remaining = refined_code[match.end():]
                    lines = remaining.split('\n')
                    
                    end_line_offset = 0
                    for line_idx, line in enumerate(lines):
                        if not line.strip():
                            end_line_offset = len('\n'.join(lines[:line_idx+1])) + 1
                            continue
                        
                        current_indent = len(line) - len(line.lstrip())
                        
                        if current_indent <= match_indent:
                            end_line_offset = len('\n'.join(lines[:line_idx]))
                            break
                        
                        end_line_offset = len('\n'.join(lines[:line_idx+1])) + 1
                    else:
                        end_line_offset = len(remaining)
                    
                    end_pos = match.end() + end_line_offset
                    refined_code = refined_code[:start_pos] + refined_code[end_pos:]
                    fixes += 1
                    print(f"   ✅ 已移除語義錯誤的 while 迴圈: {error_desc}")

        # -----------------------------------------------------------
        # 7. [Float/Fraction Consistency] 確保數值類型一致性
        # -----------------------------------------------------------
        float_returns = re.findall(r'return\s+float\s*\((.*?)\)', refined_code)
        
        if float_returns:
            print(f"🔧 [Healer V47.7] 修復 {len(float_returns)} 個 float 返回，轉換為 Fraction")
            refined_code = re.sub(r'return\s+float\s*\((.*?)\)', r'return Fraction(\1)', refined_code)
            fixes += len(float_returns)
        
        float_assignments = re.findall(r'(\w+operand\w*)\s*=\s*float\s*\((.*?)\)', refined_code)
        
        if float_assignments:
            print(f"🔧 [Healer V47.7] 修復 {len(float_assignments)} 個 operand float 轉換")
            refined_code = re.sub(r'(\w+operand\w*)\s*=\s*float\s*\((.*?)\)', r'\1 = Fraction(\2)', refined_code)
            fixes += len(float_assignments)

        # -----------------------------------------------------------
        # 8. [Eval Eliminator] 智能替換 safe_eval 為直接計算
        # -----------------------------------------------------------
        if 'safe_eval(' in refined_code:
            eval_count = 0
            
            def replace_safe_eval(match):
                nonlocal eval_count
                full_expr = match.group(0)
                content = match.group(1)
                
                var_pattern = r'\{(\w+)\}'
                vars_found = re.findall(var_pattern, content)
                
                if len(vars_found) == 3:
                    var1, op_var, var2 = vars_found
                    eval_count += 1
                    return f"({var1} {op_var} {var2})"
                
                print(f"⚠️  [Healer] 無法解析 safe_eval 表達式: {full_expr[:60]}...")
                return full_expr
            
            refined_code = re.sub(r'safe_eval\(([^)]+)\)', replace_safe_eval, refined_code)
            
            if eval_count > 0:
                print(f"🔧 [Healer] 移除 safe_eval 調用，替換為直接計算 ({eval_count} 處)")
                fixes += eval_count

        # -----------------------------------------------------------
        # 9. [Op Latex Fixer] 修復 op_latex(...) -> op_latex[...]
        # -----------------------------------------------------------
        if 'op_latex(' in refined_code:
            refined_code, n = re.subn(r'op_latex\(([^\)]+)\)', r'op_latex[\1]', refined_code)
            if n > 0:
                print(f"🔧 [Healer] 修復 op_latex 調用方式: op_latex(...) -> op_latex[...] ({n} 處)")
                fixes += n

        # -----------------------------------------------------------
        # 10. [Forbidden Function Remover] 移除自創的格式化函式
        # -----------------------------------------------------------
        for func_name in self.forbidden_funcs:
            if f'def {func_name}' in refined_code:
                lines = refined_code.split('\n')
                cleaned_lines = []
                skip_mode = False
                target_indent = -1
                
                for line in lines:
                    if f'def {func_name}' in line:
                        skip_mode = True
                        target_indent = len(line) - len(line.lstrip())
                        fixes += 1
                        continue
                    
                    if skip_mode:
                        current_indent = len(line) - len(line.lstrip())
                        if not line.strip(): 
                            continue
                        if current_indent > target_indent:
                            continue
                        else:
                            skip_mode = False
                    
                    cleaned_lines.append(line)
                
                refined_code = '\n'.join(cleaned_lines)
                
        for old_func in self.forbidden_funcs:
            refined_code, n = re.subn(f'{old_func}\\(', 'fmt_num(', refined_code)
            fixes += n

        # -----------------------------------------------------------
        # 11. [LaTeX Operator Fixer] LaTeX 運算符修復
        # -----------------------------------------------------------
        refined_code, n1 = re.subn(r'(?<=f")([^{"]*?)\\\*([^{"]*?)(?=")', r'\1\\times\2', refined_code)
        refined_code, n2 = re.subn(r'(?<=f")([^{"]*?)\\\/([^{"]*?)(?=")', r'\1\\div\2', refined_code)
        fixes += (n1 + n2)

        # -----------------------------------------------------------
        # 12. [F-string fmt_num Fixer] f-string fmt_num 包裹修復
        # -----------------------------------------------------------
        pattern = r'(f["\'])([^"\']*?)\bfmt_num\(([^)]+)\)([^"\']*?)(["\'])'
        def fix_fmt_num(match):
            prefix, before, var, after, quote = match.groups()
            if before.strip().endswith('{') and after.strip().startswith('}'):
                return match.group(0)
            return f'{prefix}{before}{{fmt_num({var})}}{after}{quote}'
        
        refined_code, n = re.subn(pattern, fix_fmt_num, refined_code)
        fixes += n

        # -----------------------------------------------------------
        # 13. [Safe Choice Replacer] random.choice -> safe_choice
        # -----------------------------------------------------------
        refined_code, n = re.subn(r'\brandom\.choice\s*\(', 'safe_choice(', refined_code)
        fixes += n

        # -----------------------------------------------------------
        # 14. [LaTeX Dollar Sign Fixer] 修復中文字被錯誤包在 LaTeX $ 內的問題
        # [DISABLED 2026-02-01] 此修復與 Domain Helper 策略衝突
        # Domain Helper 函數（如 _poly_to_latex）需要手動包裝 $，不應被移除
        # -----------------------------------------------------------
        # if 'question_text' in refined_code or 'q =' in refined_code:
        #     if re.search(r'f[\'"][^\'"]*( 計算|的值|求|解|判斷)', refined_code):
        #         print(f"🔧 [Healer] 偵測到題幹可能有 LaTeX 格式問題，正在移除內嵌 $ 符號...")
        #         
        #         def remove_dollar_in_question(match):
        #             var_name = match.group(1)
        #             quote = match.group(2)
        #             content = match.group(3)
        #             
        #             fixed_content = content.replace('$', '')
        #             
        #             return f"{var_name} = f{quote}{fixed_content}{quote}"
        #         
        #         original_code = refined_code
        #         refined_code = re.sub(
        #             r"(question_text|q)\s*=\s*f(['\"])(.+?)\2",
        #             remove_dollar_in_question,
        #             refined_code
        #         )
        #         
        #         if refined_code != original_code:
        #             fixes += 1
        #             print(f"🔧 [Healer] 已移除題幣中 的 $ 符號，clean_latex_output() 會重新包裝")

        # -----------------------------------------------------------
        # 14.5. [Domain Helper LaTeX Fixer] 修復 Domain Helper 函數的 LaTeX 包裝問題
        # -----------------------------------------------------------
        # 檢測模式：使用了 _poly_to_latex 或 _deriv_symbol_latex，但沒有正確包裝 $
        if '_deriv_symbol_latex' in refined_code or '_poly_to_latex' in refined_code:
            # Pattern 1: 修復缺少 $ 包裝的 derivative_symbols
            # 例如：q = f'...求 {derivative_symbols_latex}。'
            # 應改為：q = f'...求 ${derivative_symbols_latex}$。'
            pattern1 = r"(q\s*=\s*f['\"][^'\"]*求\s+)(\{[^}]+symbols[^}]*\})(。['\"])"
            if re.search(pattern1, refined_code):
                print(f"🔧 [Healer] 偵測到導數符號缺少 $ 包裝，正在修復...")
                refined_code = re.sub(
                    pattern1,
                    r"\1$\2$\3",
                    refined_code
                )
                fixes += 1
            
            # Pattern 2: 移除對 Domain Helper 輸出的 clean_latex_output 呼叫
            # 檢測：q = clean_latex_output(q) 且 q 包含 _poly_to_latex 或 _deriv_symbol_latex
            lines = refined_code.split('\n')
            new_lines = []
            skip_next_clean = False
            
            for i, line in enumerate(lines):
                # 檢查前一行是否使用了 Domain Helper
                if i > 0:
                    prev_line = lines[i - 1]
                    if ('_poly_to_latex' in prev_line or '_deriv_symbol_latex' in prev_line) and 'q = f' in prev_line:
                        skip_next_clean = True
                
                # 如果當前行是 clean_latex_output(q)，且應該跳過
                if skip_next_clean and re.match(r'\s*q\s*=\s*clean_latex_output\(q\)', line):
                    print(f"🔧 [Healer] 移除對 Domain Helper 輸出的 clean_latex_output() 呼叫")
                    new_lines.append(re.sub(r'q\s*=\s*clean_latex_output\(q\)', '# Removed: clean_latex_output(q) - Domain Helper output already formatted', line))
                    fixes += 1
                    skip_next_clean = False
                else:
                    new_lines.append(line)
                    if skip_next_clean and not line.strip().startswith('#'):
                        skip_next_clean = False
            
            refined_code = '\n'.join(new_lines)


        # -----------------------------------------------------------
        # 15. [Internal Function Return Fixer] 檢測內部函數缺少返回值
        # -----------------------------------------------------------
        if 'def ' in refined_code and 'for _safety_loop_var in range' in refined_code:
            inner_func_pattern = r'(    def \w+\([^)]*\):.*?)(    \w+|def generate)'
            matches = list(re.finditer(inner_func_pattern, refined_code, re.DOTALL))
            
            for match in matches:
                func_body = match.group(1)
                func_name_match = re.search(r'def (\w+)\(', func_body)
                if not func_name_match:
                    continue
                    
                func_name = func_name_match.group(1)
                
                if 'for _safety_loop_var in range' in func_body:
                    lines = func_body.strip().split('\n')
                    last_non_empty_line = ''
                    indent_count = 0
                    for line in reversed(lines):
                        stripped = line.strip()
                        if stripped and not stripped.startswith('#'):
                            indent = len(line) - len(line.lstrip())
                            if indent == 4:
                                last_non_empty_line = stripped
                                indent_count = indent
                                break
                    
                    if last_non_empty_line and not last_non_empty_line.startswith('return'):
                        print(f"🔧 [Healer] 偵測到內部函數 '{func_name}' 可能缺少默認返回值，正在添加...")
                        
                        func_indent = '    '
                        default_return = f"{func_indent}return (0, 0)  # [Auto-Fixed] 默認返回值（避免 None unpacking）\n"
                        
                        func_start = refined_code.find(func_body)
                        if func_start != -1:
                            func_end = func_start + len(func_body)
                            refined_code = refined_code[:func_end] + default_return + refined_code[func_end:]
                            fixes += 1

        return refined_code, fixes


def fix_code_syntax(code_str, error_msg=""):
    """
    [V45.6 Syntax Emergency Room + Orthopedic Surgeon]
    1. Regex 修復語法錯誤 (Latex, Break, Op-var)。
    2. [NEW] Auto-Indenter: 自動矯正 IndentationError。
    """
    fixed_code = code_str.replace("，", ", ").replace("：", ": ")
    fixed_code = re.sub(r'###.*?\n', '', fixed_code) 
    
    total_fixes = 0
    def apply_fix(pattern, replacement, code):
        new_code, count = re.subn(pattern, replacement, code, flags=re.MULTILINE)
        return new_code, count

    # 1. Latex Fixes
    fixed_code, c = apply_fix(r'(?<!\\)\\ ', r'\\\\ ', fixed_code); total_fixes += c
    fixed_code, c = apply_fix(r'(?<!\\)\\u(?![0-9a-fA-F]{4})', r'\\\\u', fixed_code); total_fixes += c

    # 2. Tuple Unpacking Fix
    unpacking_pattern = r'^(\s*(?!break|continue|return|pass|raise|yield)[a-zA-Z_]\w*)\s+([a-zA-Z_]\w*)\s*=(?!=)'
    fixed_code, c = re.subn(unpacking_pattern, r'\1, \2 =', fixed_code, flags=re.MULTILINE)
    total_fixes += c

    # 3. Break Hallucination Fix
    break_pattern = r'^[ \t]*break[ \t]*,[ \t]*([a-zA-Z_]\w*)[ \t]*=[ \t]*(.+)$'
    fixed_code, c = re.subn(break_pattern, r'\1 = \2; break', fixed_code, flags=re.MULTILINE)
    if c > 0: 
        logger.info(f"🚑 [Syntax Healer] 修復了 {c} 處 break 賦值幻覺 (使用分號策略)")
    total_fixes += c

    # 4. Variable as Operator Fix
    op_vars = r'(?:op\d+|current_op|Op_\w+)'
    
    pattern_inner = rf'\(([\w\.]+)\s+({op_vars})\s+([\w\.]+)\)'
    for _ in range(3): 
        fixed_code, c = re.subn(pattern_inner, r'safe_eval(f"{ \1 } { \2 } { \3 }")', fixed_code)
        total_fixes += c

    pattern_assign = rf'=\s*(.+?)\s+({op_vars})\s+([\w\.]+)\s*$'
    def assign_replacer(match):
        left = match.group(1)
        op = match.group(2)
        right = match.group(3)
        return f'= safe_eval(f"""{{ {left} }} {{ {op} }} {{ {right} }}""")'

    fixed_code, c = re.subn(pattern_assign, assign_replacer, fixed_code, flags=re.MULTILINE)
    if c > 0: 
        logger.info(f"🚑 [Syntax Healer] 修復了 {c} 處運算符變數語法")
    total_fixes += c
    
    # 5. F-string Braces
    def fix_latex_braces(match):
        content = match.group(1)
        if not (re.search(r'\\[a-zA-Z]+', content) and not re.search(r'^\\n', content)):
            return f'f"{content}"'
        pattern = r'(\{[a-zA-Z_][a-zA-Z0-9_]*(\(.*\))?\})|(\{)|(\})'
        def token_sub(m):
            if m.group(1): return m.group(1) 
            if m.group(3): return "{{"        
            if m.group(4): return "}}"        
            return m.group(0)
        new_content = re.sub(pattern, token_sub, content)
        return f'f"{new_content}"'

    fixed_code, c = re.subn(r'f"(.*?)"', fix_latex_braces, fixed_code); total_fixes += c

    # 6. Auto-Indenter
    lines = fixed_code.split('\n')
    indented_lines = []
    prev_line_ends_colon = False
    prev_indent = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            indented_lines.append(line)
            continue
            
        current_indent = len(line) - len(line.lstrip())
        
        if prev_line_ends_colon:
            if current_indent <= prev_indent:
                new_indent = prev_indent + 4
                fixed_line = " " * new_indent + line.lstrip()
                indented_lines.append(fixed_line)
                prev_indent = new_indent 
            else:
                indented_lines.append(line)
                prev_indent = current_indent
        else:
            indented_lines.append(line)
            prev_indent = current_indent
            
        code_part = stripped.split('#')[0].rstrip()
        if code_part.endswith(':'):
            prev_line_ends_colon = True
        else:
            prev_line_ends_colon = False
            
    fixed_code = '\n'.join(indented_lines)

    return fixed_code, total_fixes


# ==============================================================================
# Helper Functions
# ==============================================================================

def clean_redundant_imports(code_str):
    """
    [V47.6 CRITICAL FIX] 不刪除任何 import！
    
    原因：
    1. LLM 新生成的 import 是必需的（如 from random import randint）
    2. PERFECT_UTILS 後續會注入全域 import，不需要提前刪除
    3. AST Healer 會處理真正的重複問題
    
    修復策略：保留所有 import，讓後續管線處理重複檢測
    
    Args:
        code_str (str): 待處理的代碼字符串
    
    Returns:
        tuple: (code_str, 0, []) - 不做任何修改
    """
    # 不做任何修改，直接回傳原始代碼
    return code_str, 0, []


def remove_forbidden_functions_unified(code_str, forbidden_list):
    """
    [Performance Fix V9.2.1] 統一的函數移除器
    
    合併原本在 refine_ai_code(), 工具函式重定義偵測器, 通用語法修復 三處的邏輯
    避免重複掃描，提升 15-20% 執行速度
    
    Args:
        code_str (str): 待處理的代碼字符串
        forbidden_list (list): 禁止的函數名稱列表
    
    Returns:
        tuple: (cleaned_code, removed_count)
    
    Examples:
        >>> code = "def bad_func():\\n    pass\\ndef good_func():\\n    pass"
        >>> cleaned, count = remove_forbidden_functions_unified(code, ['bad_func'])
        >>> 'bad_func' not in cleaned
        True
    """
    lines = code_str.split('\n')
    cleaned_lines = []
    skip_mode = False
    target_indent = -1
    removed_count = 0
    
    for line in lines:
        # 檢查是否進入禁止函數定義
        should_skip = False
        for func_name in forbidden_list:
            # 嚴格匹配定義行（避免誤判函數調用）
            if re.match(rf'^\s*def\s+{func_name}\s*\(', line):
                skip_mode = True
                target_indent = len(line) - len(line.lstrip())
                removed_count += 1
                should_skip = True
                print(f"[Unified Remover] Removing function: {func_name}")
                break
        
        if should_skip:
            continue
        
        if skip_mode:
            current_indent = len(line) - len(line.lstrip())
            # 空行或註釋：跳過
            if not line.strip() or line.strip().startswith('#'):
                continue
            # 縮排回到定義層級或更外層：結束跳過模式
            if current_indent <= target_indent and line.strip():
                skip_mode = False
            else:
                continue  # 仍在函數體內，跳過
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines), removed_count
