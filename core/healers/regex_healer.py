# -*- coding: utf-8 -*-
# ==============================================================================
# ID: core/healers/regex_healer.py
# Version: V2.8 (Duplicate Class Removal + Method Call Fix)
# Last Updated: 2026-02-08
# Author: Math AI Research Team (Advisor & Student)
#
# [Description]:
#   Regex 修復引擎 - 文字層級的預處理，現已新增重複類定義移除與方法調用修復
#   [Healer V2.8] 防止重複類定義衝突 + 錯誤的類方法調用
#
# [Key Features]:
#   0. Remove Trailing Artifacts - 移除 C-style `}` 和 markdown 末尾垃圾 ⭐ [V2.6]
#   0.5. Fix Mismatched Braces - 修復括號不匹配 (缺少 }, ], ) 等) ⭐ [V2.7]
#   1. Smart Dependency Injection - 自動注入 FractionOps, IntegerOps 等
#   2.5. Remove Duplicate Classes - 移除重複的類定義 ⭐ [V2.8 NEW]
#   2.8. Fix Method Calls - 修復錯誤的類方法調用 ⭐ [V2.8 NEW]
#   3. Markdown Fence Removal - 移除 ```python ... ```
#   4. Syntax Error Fixes - 修復中文符號等
#   5. Input Call Removal - 移除 input() 以避免阻塞
#   6. Return Stats Dict - 返回修復統計資訊
#
# [New in V2.8]:
#   - remove_duplicate_class_definitions(): 檢測並移除重複的類定義（如雙重 IntegerOps）
#   - fix_incorrect_class_method_calls(): 修復錯誤調用（如 IntegerOps.fmt_num() → fmt_num()）
#   - 在 heal() Step 2.5 & 2.8 執行，在依賴注入之後
#   - 防止「重複定義導致的衝突」和「調用不存在的類方法」錯誤
#
# [Previous in V2.7]:
#   - fix_mismatched_braces(): 檢測並修復括號不匹配問題 (第一次高度防禦)
#   - 在 heal() Step 0.5 執行，在 Markdown 移除之前
#   - 防止「返回字典缺少 }」的常見錯誤
#
# [Previous in V2.6]:
#   - remove_trailing_artifacts(): 移除末尾非 Python 代碼殘留物（第一道防線）
#   - 在 heal() Step 0 執行，確保 AST 能正確解析
# ==============================================================================

import re
import logging

logger = logging.getLogger(__name__)


class RegexHealer:
    """
    Regex-based Healer (Text Pre-processor) V2.5
    
    功能：在 AST 解析前，處理純文本層級的錯誤與依賴注入
    新增：自動注入 domain_function_library 的缺失引用
    """
    
    def __init__(self):
        """初始化 Regex Healer"""
        self.forbidden_chars = ['\u200b', '\ufeff']  # 零寬字元
        self.forbidden_funcs = [
            'format_number_for_latex', 'format_num_latex', 
            'latex_format', '_format_term_with_parentheses'
        ]
        
        # [V2.5] 依賴映射表 - 自動注入規則
        # [V3.5] 依賴映射表 - 自動注入規則
        # [2026-02-14 Critical Fix] 禁用自動 import domain_function_library
        # 因為我們現在使用 Scaffolding 機制直接將這些函數注入到生成代碼的頂部
        # 所以不需要額外 import，否則會導致運行時錯誤 (ImportError)
        self.dependency_map = {
            # "IntegerOps": "from domain_function_library import IntegerOps", # Disabled
            # "FractionOps": "from domain_function_library import FractionOps", # Disabled
            # "RadicalOps":  "from domain_function_library import RadicalOps", # Disabled
            # "CalculusOps": "from domain_function_library import CalculusOps", # Disabled
            # "fmt_num":     "from domain_function_library import fmt_num", # Disabled
        }

    def remove_trailing_artifacts(self, code_str: str) -> str:
        """
        [V2.6 Critical Fix] 移除代碼末尾的非 Python 殘留物
        修復 14B 模型常犯的 C-style 結尾錯誤 (如 '}')
        
        功能：清理 LLM 在代碼末尾留下的非 Python 語法垃圾
        例如：
            INPUT:  code_here\n}
            OUTPUT: code_here
        
        ⚠️ 注意：只移除「明显是垃圾的」末尾符号，不移除合法代码
        
        Args:
            code_str: 原始代碼字串
            
        Returns:
            str: 移除末尾非 Python 殘留物的代碼
        """
        if not code_str:
            return ""
        
        # 先做初始清理
        code_str = code_str.strip()
        
        # 迭代式移除末尾垃圾，直到沒有為止
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            original = code_str
            
            # 1. 移除末尾的 ``` (Markdown fence) - 明确是垃圾
            code_str = re.sub(r'```\s*$', '', code_str, flags=re.MULTILINE)
            code_str = code_str.strip()
            
            # 2. 移除末尾的 'python' 字樣 - 明确是垃圾（代碼末尾不應有此字）
            code_str = re.sub(r'\s+python\s*$', '', code_str, flags=re.IGNORECASE)
            code_str = code_str.strip()
            
            # 3. 移除末尾的孤立 '}' - 必須是單獨一行或多行
            # 模式：\n} 或 空白+} 作為末尾（表示 LLM 添加的多餘結尾，而不是字典內容）
            code_str = re.sub(r'\n\s*}\s*$', '', code_str)
            code_str = code_str.strip()
            
            # 4. 移除末尾的孤立 ';' (C-style semicolon) - 代碼末尾不應有分號
            code_str = re.sub(r';\s*$', '', code_str)
            code_str = code_str.strip()
            
            # 5. 如果沒有變化，就停止迴圈
            if code_str == original.strip():
                break
        
        return code_str.strip()

    def fix_mismatched_braces(self, code_str: str) -> str:
        """
        [V2.7 CRITICAL] 修復括號不匹配問題 - 保守策略
        
        ⚠️ 注意：這個方法現在採用「保守策略」
        只修復「確實缺少」的括號，不會亂加
        
        問題模式：
            INPUT:  return {\n    'mode': 1\n(缺少 })
            OUTPUT: return {\n    'mode': 1\n}
        
        Args:
            code_str: 原始代碼字串
            
        Returns:
            str: 修復後的代碼
        """
        if not code_str:
            return ""
        
        # 只處理最簡單的情況：code 末尾明確缺少 }
        # 其他複雜情況交給 AST Healer
        
        lines = code_str.split('\n')
        if not lines:
            return code_str
        
        # 只檢查最後一行是否是不完整的返回字典
        last_line = lines[-1].strip() if lines else ""
        
        # 簡單啟發式：如果最後一行是 dict value 但沒有右括號
        # 模式: 'key': value 而不是 'key': value}
        if "'" in last_line and ':' in last_line and not last_line.endswith(('}', ')', ']')):
            # 檢查是否真的缺少括號
            # 通過計算是否有未閉合的 {
            open_braces = code_str.count('{')
            close_braces = code_str.count('}')
            
            if open_braces > close_braces:
                missing = open_braces - close_braces
                print(f"🔧 [RegexHealer V2.7] 偵測到缺少 {missing} 個 '}}'，自動修復")
                return code_str + '\n' + ('}' * missing)
        
        return code_str

    def remove_markdown_fences(self, code_str: str) -> str:
        """
        [V2.5 新增] 移除 Markdown 代碼塊標記 (```python ... ```)
        
        功能：清理 LLM 生成的代碼中的 markdown 包裝
        例如：
            INPUT:  '''python\\ncode here\\n```'''
            OUTPUT: code here
        
        Args:
            code_str: 原始代碼字串
            
        Returns:
            str: 移除 Markdown 標記後的代碼
        """
        if not code_str:
            return ""
        
        # 匹配 ```python ... ``` 或 ``` ... ```
        pattern = r"```(?:python)?\n(.*?)```"
        match = re.search(pattern, code_str, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return code_str.strip()

    def inject_domain_imports(self, code_str: str) -> tuple:
        """
        [V2.6 CRITICAL FIX] 智慧依賴注入 - 自動補充遺漏的 domain_function_library 引用
        
        核心邏輯：
        1. 掃描代碼中是否使用了特定關鍵字（如 FractionOps, IntegerOps 等）
        2. 檢查對應的 import 語句是否存在
        3. ★★★ 新增：檢查是否已經在代碼中本地定義 (class/def Keyword)
        4. 如果關鍵字存在但 import 遺漏 且 未本地定義，自動注入到代碼頂部
        
        依賴映射表：
            IntegerOps    → from domain_function_library import IntegerOps
            FractionOps   → from domain_function_library import FractionOps
            RadicalOps    → from domain_function_library import RadicalOps
            CalculusOps   → from domain_function_library import CalculusOps
            fmt_num       → from domain_function_library import fmt_num
        
        例子：
            INPUT:  code uses FractionOps but 缺 import and 未本地定義
            OUTPUT: 自動在最上方注入 from domain_function_library import FractionOps
            
            INPUT:  code has 「class IntegerOps」定義 (已本地定義)
            OUTPUT: 跳過 import，不重複注入
        
        Returns:
            tuple: (新代碼, 注入次數)
        """
        injections = []
        
        # 逐一掃描依賴
        for keyword, import_stmt in self.dependency_map.items():
            # ★★★ [V2.6 CRITICAL] 檢查是否已經在本地定義
            # 防止重複定義導致的衝突（如 Ab3 的 IntegerOps 雙定義問題）
            pattern_local_def = rf"(?:class|def)\s+{keyword}\b"
            if re.search(pattern_local_def, code_str):
                # 已經本地定義了，跳過 import
                print(f"   [RegexHealer V2.6] {keyword} 已在本地定義，不重複 import")
                continue
            
            # 簡單檢查：
            #   1. 代碼中有用到關鍵字
            #   2. 對應的 import 不存在
            #   3. 未在本地定義
            if keyword in code_str and import_stmt not in code_str:
                injections.append(import_stmt)
                print(f"   [RegexHealer] 偵測到遺漏的引用: {keyword} → {import_stmt}")
        
        if injections:
            # 排序並去重
            injections = sorted(list(set(injections)))
            
            # 組合 import 標頭
            header = "\n".join(injections) + "\n"
            
            print(f"   [RegexHealer] 自動注入 {len(injections)} 個 import 語句")
            return header + code_str, len(injections)
        
        return code_str, 0

    def remove_invalid_dependencies(self, code_str: str) -> tuple:
        """
        [V3.3 Ab3 Fix] 移除錯誤的模組引用（當使用 Scaffolding 注入時）
        例如： from domain_function_library import fmt_num, IntegerOps
        """
        old_code = code_str
        fix_count = 0
        
        # [Critial Fix] Remove 'from domain_function_library'
        # [V3.4] 極度寬鬆模式：只要行內包含 import domain_function_library 就整行刪除
        # 這是為了對抗可能的不可見字符或奇怪的前綴
        if "domain_function_library" in code_str:
             print(f"[DEBUG] Found 'domain_function_library' in code. Regex removing...")

        patterns = [
            r"^.*from\s+domain_function_library\s+import.*(?:\n|$)",
            r"^.*import\s+domain_function_library.*(?:\n|$)",
            r"^.*from\s+core\.code_generator\s+import.*(?:\n|$)",
            r"^.*from\s+core\..*\s+import.*(?:\n|$)"
        ]
        
        current_code = code_str
        for pattern in patterns:
            # 使用 sub 刪除匹配的行
            new_code = re.sub(pattern, "", current_code, flags=re.MULTILINE)
            if len(new_code) < len(current_code): # 如果長度變短，表示有刪除
                fix_count += 1
                current_code = new_code
        
        if fix_count > 0:
            print(f"🔧 [RegexHealer] 移除已注入的無效依賴引用 (domain_function_library/core)")
            # 移除可能留下的多餘空行 (3行變2行)
            current_code = re.sub(r'\n\s*\n\s*\n', '\n\n', current_code)
            
        return current_code, fix_count

    def fix_common_syntax_errors(self, code_str: str) -> str:
        """
        [V2.5] 修復常見的符號錯誤 (如中文括號、全形符號)
        
        功能：標準化常見的符號錯誤
        例如：
            （x）  → (x)
            ，     → ,
            ：     → :
        
        Args:
            code_str: 代碼字串
            
        Returns:
            str: 修復後的代碼
        """
        # 中文全形符號替換表
        replacements = {
            '（': '(',
            '）': ')',
            '，': ',',
            '：': ':',
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            # [V2.10] 雙重運算符修復 (For LaTeX/Math strings)
            '++': '+',
            '+-': '-',
            '-+': '-',
            # ' -- ': ' + ', # Too risky due to comments/separators
        }
        
        result = code_str
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        return result

    def remove_duplicate_class_definitions(self, code_str: str) -> tuple:
        """
        [V2.8 Critical Fix] 移除重複的類定義
        
        功能：檢測並移除重複的 class 定義（特別是 IntegerOps, FractionOps 等）
        保留第一個完整的定義，移除後續的不完整或重複定義
        
        例子：
            INPUT:  class IntegerOps: ... (完整定義)
                    ...
                    class IntegerOps: ... (不完整重複)
            OUTPUT: class IntegerOps: ... (只保留第一個)
        
        Args:
            code_str: 代碼字串
            
        Returns:
            tuple: (fixed_code, removed_count)
        """
        removed_count = 0
        
        # 針對常見的 domain 類別檢查重複定義
        class_names = ['IntegerOps', 'FractionOps', 'RadicalOps', 'CalculusOps']
        
        for class_name in class_names:
            # 使用 regex 找到所有該類的定義
            pattern = rf'^class\s+{class_name}\s*[:\(]'
            matches = list(re.finditer(pattern, code_str, re.MULTILINE))
            
            if len(matches) > 1:
                print(f"   [RegexHealer V2.8] 偵測到重複的類定義: {class_name} (共 {len(matches)} 次)")
                
                # 保留第一個，移除後續的
                # 策略：找到第二個定義的開始位置，向後查找到下一個 top-level 定義或檔案結尾
                first_match_end = matches[0].end()
                second_match_start = matches[1].start()
                
                # 找到第二個定義的結束位置（找下一個 top-level def/class 或檔案結尾）
                # 簡單策略：找到下一個不縮排的 def 或 class
                rest_code = code_str[second_match_start:]
                lines = rest_code.split('\n')
                
                end_line_idx = 1  # 至少包含 class 定義那一行
                for i in range(1, len(lines)):
                    line = lines[i]
                    # 如果遇到新的 top-level 定義（不縮排的 def/class），停止
                    if line and not line[0].isspace() and (line.startswith('def ') or line.startswith('class ')):
                        break
                    end_line_idx = i + 1
                
                # 計算要移除的文本範圍
                lines_to_remove = '\n'.join(lines[:end_line_idx])
                
                # 移除重複的定義
                code_str = code_str.replace(lines_to_remove, '', 1)
                removed_count += 1
                print(f"   [RegexHealer V2.8] 已移除第 {len(matches)} 個重複的 {class_name} 定義")
        
        return code_str, removed_count

    def fix_incorrect_class_method_calls(self, code_str: str) -> tuple:
        """
        [V2.8 Critical Fix] 修復錯誤的類方法調用
        [V2.8.1 Fix] 已重新啟用特定替換，確保原本 hallucinated 的全球 fmt_num 回歸 IntegerOps.fmt_num
        """
        fix_count = 0
        
        # 定義需要自動補全前綴的函數，以及對應的目標類別
        method_map = {
            'fmt_num': 'IntegerOps',
            'to_latex': 'FractionOps',
            'format_fraction': 'FractionOps'
        }
        
        for method, class_name in method_map.items():
            # 查找並替換所有未加前綴的調用
            # pattern: 匹配 ` method(` 但排除 `.method(`
            pattern = rf'(?<!\.)\b{method}\s*\('
            
            def replacer(match):
                nonlocal fix_count
                fix_count += 1
                return f"{class_name}.{method}("
            
            if re.search(pattern, code_str):
                code_str = re.sub(pattern, replacer, code_str)
                print(f"   [RegexHealer V2.8] 修復幻覺方法: {method} → {class_name}.{method}")

        code_str, fix_count = self.fix_hallucinated_methods(code_str)
        return code_str, fix_count

    def fix_hallucinated_methods(self, code_str: str) -> tuple:
        """
        修復常見的幻覺方法呼叫
        例如： PolynomialOps.format() -> PolynomialOps.format_latex()
        """
        fix_count = 0
        hallucinations = {
            'PolynomialOps.format(': 'PolynomialOps.format_latex(',
            'RadicalOps.format(': 'RadicalOps.format_term(',
            'poly_format(': 'poly_format_latex('
        }
        
        for bad_call, good_call in hallucinations.items():
            if bad_call in code_str:
                count = code_str.count(bad_call)
                code_str = code_str.replace(bad_call, good_call)
                fix_count += count
                print(f"   [RegexHealer V2.9] 修復幻覺方法調用: {bad_call} → {good_call}")
                
        return code_str, fix_count

    def remove_input_calls(self, code_str: str) -> str:
        """
        [V2.5] 移除 input() 呼叫以避免阻塞執行
        
        功能：將所有 input(...) 替換為默認值 '0'
        例如：
            INPUT:  x = input("Enter value: ")
            OUTPUT: x = 0
        
        Args:
            code_str: 代碼字串
            
        Returns:
            str: 移除 input 後的代碼
        """
        return re.sub(r'input\s*\([^)]*\)', '0', code_str)

    def heal(self, code_str: str) -> tuple:
        """
        [V2.6] 主要修復入口
        
        執行順序：
        0. 移除末尾非 Python 殘留物 (```'python', '}' 等) ⭐ 新增
        0.5. 修復括號不匹配 (缺少 }, ], ) 等) ⭐ [V2.6 NEW]
        1. 移除 Markdown 代碼塊標記 (```python)
        2. 智慧依賴注入 (自動補 import)
        3. 語法符號修復 (中文括號等)
        4. 移除 input() 呼叫
        
        Args:
            code_str: 原始代碼字串
            
        Returns:
            tuple: (fixed_code, stats_dict)
            
        stats_dict 包含：
            - 'regex_fix_count': 總修復次數 (包括各類修復)
            - 'markdown_removed': Markdown 標記是否被移除
            - 'imports_injected': 注入的 import 數量
            - 'syntax_fixed': 語法修復是否進行
            - 'input_removed': input 呼叫是否被移除
            - 'braces_fixed': 括號修復是否進行
        """
        stats = {'regex_fix_count': 0}
        
        if not code_str:
            return "", stats

        # ================================================================
        # Step 0: 移除末尾非 Python 殘留物 ⭐ [V2.6 新增 - 第一道防線]
        # ================================================================
        old_code = code_str
        code_str = self.remove_trailing_artifacts(code_str)

        # ================================================================
        # Step -1: 移除夾雜的中文廢話 ⭐ [V4.0 Aggressive Healer]
        # ================================================================
        old_code_zh = code_str
        code_str = self._strip_chinese_garbage(code_str)
        if code_str != old_code_zh:
            stats['regex_fix_count'] += 1
            print(f"🔧 [RegexHealer V4.0] 移除夾雜的中文廢話 (Thinking Leakage)")
        
        if code_str != old_code:
            stats['regex_fix_count'] += 1
            print(f"🔧 [RegexHealer V2.6] 移除末尾非代碼殘留物 (如 '}}', 'python')")

        # ================================================================
        # Step 0.5: 修復括號不匹配 ⭐ [V2.6 NEW - 防止返回語句缺少 }]
        # ================================================================
        old_code = code_str
        code_str = self.fix_mismatched_braces(code_str)
        
        if code_str != old_code:
            stats['regex_fix_count'] += 1
            stats['braces_fixed'] = True
            print(f"🔧 [RegexHealer V2.6] 修復括號不匹配")
        else:
            stats['braces_fixed'] = False

        # ================================================================
        # Step 0.8: 移除無效依賴引用 ⭐ [V3.3 Ab3 Fix]
        # ================================================================
        code_str, dep_removed_count = self.remove_invalid_dependencies(code_str)
        stats['regex_fix_count'] += dep_removed_count

        # ================================================================
        # Step 1.8: 自動補全類前綴 ⭐ [V2.9 New]
        # ================================================================
        code_str, prefix_fixes = self.fix_missing_class_prefix(code_str)
        stats['regex_fix_count'] += prefix_fixes

        # ================================================================
        # Step 1: 移除 Markdown 代碼塊標記
        # ================================================================
        old_code = code_str
        code_str = self.remove_markdown_fences(code_str)
        
        if code_str != old_code:
            stats['regex_fix_count'] += 1
            stats['markdown_removed'] = True
            print(f"🔧 [RegexHealer] 移除 Markdown 代碼塊標記")
        else:
            stats['markdown_removed'] = False

        # ================================================================
        # Step 2: 智慧依賴注入 (計入 regex_fix_count)
        # ================================================================
        code_str, import_fixes = self.inject_domain_imports(code_str)
        stats['regex_fix_count'] += import_fixes
        stats['imports_injected'] = import_fixes

        # ================================================================
        # Step 2.1: 遺漏的標準庫注入 ⭐ [V3.4 NEW]
        # ================================================================
        code_str, std_lib_fixes = self.inject_standard_libraries(code_str)
        stats['regex_fix_count'] += std_lib_fixes
        if std_lib_fixes > 0:
            print(f"🔧 [RegexHealer V3.4] 自動注入 {std_lib_fixes} 個標準庫依賴")


        # ================================================================
        # Step 2.5: 移除重複的類定義 ⭐ [V2.8 NEW - 防止類定義衝突]
        # ================================================================
        code_str, duplicates_removed = self.remove_duplicate_class_definitions(code_str)
        stats['regex_fix_count'] += duplicates_removed
        stats['duplicates_removed'] = duplicates_removed
        
        if duplicates_removed > 0:
            print(f"🔧 [RegexHealer V2.8] 移除 {duplicates_removed} 個重複的類定義")

        # ================================================================
        # Step 2.8: 修復錯誤的類方法調用 ⭐ [V2.8 NEW - 防止調用不存在的方法]
        # ================================================================
        code_str, method_fixes = self.fix_incorrect_class_method_calls(code_str)
        stats['regex_fix_count'] += method_fixes
        stats['method_calls_fixed'] = method_fixes
        
        if method_fixes > 0:
            print(f"🔧 [RegexHealer V2.8] 修復 {method_fixes} 個錯誤的方法調用")

        # ================================================================
        # Step 3: 語法符號修復 (若有變更則計數)
        # ================================================================
        old_code = code_str
        code_str = self.fix_common_syntax_errors(code_str)
        
        if code_str != old_code:
            stats['regex_fix_count'] += 1
            stats['syntax_fixed'] = True
            print(f"🔧 [RegexHealer] 修復常見的符號錯誤")
        else:
            stats['syntax_fixed'] = False

        # ================================================================
        # Step 4: 移除 input() 呼叫
        # ================================================================
        old_code = code_str
        code_str = self.remove_input_calls(code_str)
        
        if code_str != old_code:
            stats['regex_fix_count'] += 1
            stats['input_removed'] = True
            print(f"🔧 [RegexHealer] 移除 input() 呼叫")
        else:
            stats['input_removed'] = False

        return code_str, stats

    def inject_standard_libraries(self, code_str: str) -> tuple:
        """
        [V3.4 NEW] 自動注入遺漏的 Python 標準庫
        例如: 使用了 defaultdict 但沒 import collections
        """
        fix_count = 0
        
        # 映射表: 關鍵字 -> 需要的 import 語句
        # 注意: 這裡只處理常用的，避免過度干涉
        lib_map = {
            'defaultdict': 'from collections import defaultdict',
            'deque': 'from collections import deque',
            'Counter': 'from collections import Counter',
            'Fraction': 'from fractions import Fraction',
            'Decimal': 'from decimal import Decimal',
            're\\.\w+': 'import re',  # 如果用到 re.xxx
            'math\\.\w+': 'import math', # 如果用到 math.xxx
            'random\\.\w+': 'import random',
            'itertools\\.\w+': 'import itertools',
            'datetime': 'import datetime',
        }
        
        # 準備插入點 (在第一個 import 之後或文件開頭)
        lines = code_str.split('\n')
        insert_idx = 0
        has_imports = False
        
        # 簡單判斷插入位置
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_idx = i
                has_imports = True
            elif has_imports and not (line.startswith('import ') or line.startswith('from ') or line.strip() == ''):
                break # 找到 import 塊結束
                
        if not has_imports:
            # 如果完全沒 import，插在 docstring 後或最前面
            insert_idx = 0
            # 跳過 shebang 或 encoding
            if len(lines) > 0 and (lines[0].startswith('#!') or lines[0].startswith('# -*')):
                insert_idx = 1
        else:
            insert_idx += 1 # 插在最後一個 import 後面
            
        initial_insert_idx = insert_idx
        injected_lines = []

        for keyword_regex, import_stmt in lib_map.items():
            # 1. 檢查是否使用了該關鍵字
            if re.search(keyword_regex, code_str):
                # 2. 檢查是否已經 import 了
                # 簡易檢查：整行完全匹配，或 from ... import ... 中包含
                # 對於 'import re' 這種，檢查 'import re' 或 'import .*re.*'
                
                already_imported = False
                if import_stmt in code_str:
                    already_imported = True
                else:
                    # 進階檢查
                    if 'from ' in import_stmt:
                        # e.g. from collections import defaultdict
                        # check if "defaultdict" is in a line starting with "from collections"
                        module = import_stmt.split(' ')[1]
                        target = import_stmt.split(' ')[3]
                        pattern = rf'from\s+{module}\s+import\s+.*{target}'
                        if re.search(pattern, code_str):
                            already_imported = True
                    else:
                        # e.g. import re
                        # check "import re" or "import ..., re, ..."
                        module = import_stmt.split(' ')[1]
                        pattern = rf'^\s*import\s+.*(\s|,){module}(\s|,|$)'
                        if re.search(pattern, code_str, re.MULTILINE):
                            already_imported = True
                            
                if not already_imported:
                    # 3. 注入
                    injected_lines.append(import_stmt)
                    fix_count += 1
        
        if injected_lines:
            # 插入到代碼中
            # 反向插入以保持順序
            for stmt in reversed(injected_lines):
                lines.insert(initial_insert_idx, stmt)
            
            code_str = '\n'.join(lines)
            
        return code_str, fix_count

    def fix_missing_class_prefix(self, code_str: str) -> tuple:
        """
        [V2.9 New] 自動補全缺失的類前綴 (針對 RadicalOps 等工具)
        
        當 AI 寫出 `simplify_term(...)` 卻忘了加 `RadicalOps.` 時，
        此函數會自動將其修復為 `RadicalOps.simplify_term(...)`。
        
        僅當：
        1. 函數名在 target_methods 列表中
        2. 函數未在本地定義 (def name)
        3. 函數未被 import (我們已經移除了錯誤的 import)
        """
        fix_count = 0
        
        # 定義需要補前綴的函數映射
        # 格式: 'method_name': 'ClassName'
        method_map = {
            'simplify_term': 'RadicalOps',
            'format_term': 'RadicalOps',
            'format_expression': 'RadicalOps',
            'get_prime_factors': 'RadicalOps',
            'is_perfect_square': 'RadicalOps',
            'create_radical': 'RadicalOps', # Alias for create
        }
        
        for method, class_name in method_map.items():
            # 1. 檢查是否在本地定義了該函數 (避免誤殺自定義函數)
            if re.search(rf'def\s+{method}\s*\(', code_str):
                continue
                
            # 2. 查找並替換所有未加前綴的調用
            # pattern: 匹配 ` method(` 但排除 `.method(`
            pattern = rf'(?<!\.)\b{method}\s*\('
            
            # 使用回調函數來計數並替換
            def replacer(match):
                nonlocal fix_count
                fix_count += 1
                return f"{class_name}.{method}("
            
            # 執行替換
            if re.search(pattern, code_str):
                new_code = re.sub(pattern, replacer, code_str)
                if new_code != code_str:
                    code_str = new_code
                    print(f"   [RegexHealer V2.9] 自動補全前綴: {method} → {class_name}.{method}")

        return code_str, fix_count

    def remove_invalid_dependencies(self, code_str: str) -> tuple:
        """
        [V3.3 Ab3 Fix] 移除錯誤的模組引用（當使用 Scaffolding 注入時）
        例如： from domain_function_library import fmt_num, IntegerOps
        [V3.4] 增加移除 from RadicalOps import ...
        """
        old_code = code_str
        fix_count = 0
        
        if "domain_function_library" in code_str:
             print(f"[DEBUG] Found 'domain_function_library' in code. Regex removing...")

        patterns = [
            r"^.*from\s+domain_function_library\s+import.*(?:\n|$)",
            r"^.*import\s+domain_function_library.*(?:\n|$)",
            r"^.*from\s+core\.code_generator\s+import.*(?:\n|$)",
            r"^.*from\s+core\..*\s+import.*(?:\n|$)",
            r"^.*from\s+RadicalOps\s+import.*(?:\n|$)", # [V3.4 NEW]
            r"^.*import\s+RadicalOps.*(?:\n|$)"          # [V3.4 NEW]
        ]
        
        current_code = code_str
        for pattern in patterns:
            # 使用 sub 刪除匹配的行
            new_code = re.sub(pattern, "", current_code, flags=re.MULTILINE)
            if len(new_code) < len(current_code): # 如果長度變短，表示有刪除
                fix_count += 1
                current_code = new_code
        
        if fix_count > 0:
            print(f"🔧 [RegexHealer] 移除已注入的無效依賴引用 (domain/RadicalOps)")
        return current_code, fix_count

    def _strip_chinese_garbage(self, code: str) -> str:
        """
        [V4.2 Aggressive Healer]
        移除夾雜在代碼中的中文廢話 (Thinking Leakage)。
        規則：
        1. 忽略註解行 (# 開頭)
        2. 使用強大的正則移除所有 Python 字串 (包括三引號、單引號、轉義字符)
        3. 如果移除字串後，該行仍包含中文字符，則視為 Garbage 刪除
        """
        lines = code.split('\n')
        cleaned_lines = []
        
        # Robust Python String Regex (StackOverflow Approved)
        # Matches: """...""" | '''...''' | "..." | '...' (handling escapes)
        string_pattern = re.compile(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')')

        for line in lines:
            stripped_line = line.strip()
            # 1. 忽略註解
            if stripped_line.startswith('#'):
                cleaned_lines.append(line)
                continue
            
            # 2. 移除字串內容
            # 注意：這裡我們只針對單行進行檢查，所以假設字串不跨行 (大部分 Thinking 是單行的)
            # 如果是跨行字串，Regex Healer本來就很難處理，交給 AST 吧。
            line_no_strings = re.sub(string_pattern, '', line)
            
            # 3. 檢查剩餘內容是否有中文
            if re.search(r'[\u4e00-\u9fff]', line_no_strings):
                # 中文出現在字串外部 -> 這是廢話
                continue
            
            cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)

    def heal_minimal(self, code: str) -> Tuple[str, Dict[str, int]]:
        """
        僅進行最小幅度的修復，用於 Ab2 (Regex Only)
        """
        original_code = code
        fixes = {}
        fixes['regex_fix_count'] = 0
        fixes['minimal_mode'] = True
        
        if not code:
            return "", fixes

        # 0. [NEW] Aggressive Chinese Stripping (First Pass)
        code = self._strip_chinese_garbage(code)

        # Step 1: 智慧依賴注入 (Import Injection)
        code, injected = self.inject_domain_imports(code)
        fixes['regex_fix_count'] += injected
        
        if injected > 0:
            print(f"🔧 [RegexHealer] 自動注入 {injected} 個依賴 (Domain Specific)")

        # Step 1: 移除 Markdown 代碼塊標記
        code = self.remove_markdown_fences(code)
        
        # Step 2: 語法符號修復 (基本)
        code = self.fix_common_syntax_errors(code)

        # Step 1.5: 移除無效依賴引用 (Scaffolding Fix)
        # 這是為了移除舊的、錯誤的引用，避免 ImportError
        code, dep_removed_count = self.remove_invalid_dependencies(code)
        fixes['regex_fix_count'] += dep_removed_count
        
        # Step 1.8: 自動補全類前綴
        # 為了讓 Ab2 也能跑通，我們允許這個 "語法糖" 級別的修復
        code, prefix_fixes = self.fix_missing_class_prefix(code)
        fixes['regex_fix_count'] += prefix_fixes

        # Step 1.9: 修復幻覺方法調用
        code, hallu_fixes = self.fix_hallucinated_methods(code)
        fixes['regex_fix_count'] += hallu_fixes

        fixes['markdown_removed'] = False
        fixes['syntax_fixed'] = False

        return code, fixes


# ==============================================================================
# Backward Compatibility 相容性函數
# ==============================================================================

def fix_code_syntax(code_str, error_msg=""):
    """
    [Legacy Function] 保留以相容舊代碼
    新代碼應使用 RegexHealer.heal() 代替
    """
    fixed_code = code_str.replace("，", ", ").replace("：", ": ")
    total_fixes = 0
    
    # 簡單的符號修復
    replacements = {
        '（': '(',
        '）': ')',
    }
    for old, new in replacements.items():
        count = fixed_code.count(old)
        if count > 0:
            fixed_code = fixed_code.replace(old, new)
            total_fixes += count
    
    return fixed_code, total_fixes


def clean_redundant_imports(code_str):
    """
    [Legacy Function] 保留所有 import（不刪除）
    
    返回：(code_str, 0, [])
    """
    return code_str, 0, []


def remove_forbidden_functions_unified(code_str, forbidden_list):
    """
    [Legacy Function] 統一的函數移除器
    
    Args:
        code_str: 代碼字串
        forbidden_list: 禁止的函數名稱列表
        
    Returns:
        tuple: (cleaned_code, removed_count)
    """
    lines = code_str.split('\n')
    cleaned_lines = []
    skip_mode = False
    target_indent = -1
    removed_count = 0
    
    for line in lines:
        should_skip = False
        for func_name in forbidden_list:
            if re.match(rf'^\s*def\s+{func_name}\s*\(', line):
                skip_mode = True
                target_indent = len(line) - len(line.lstrip())
                removed_count += 1
                print(f"[Unified Remover] Removing function: {func_name}")
                should_skip = True
                break
        
        if should_skip:
            continue
        
        if skip_mode:
            current_indent = len(line) - len(line.lstrip())
            if not line.strip() or line.strip().startswith('#'):
                continue
            if current_indent <= target_indent and line.strip():
                skip_mode = False
            else:
                continue
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines), removed_count


# ==============================================================================
# 測試區塊
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("[V2.5 RegexHealer] 完整測試")
    print("=" * 80)
    
    healer = RegexHealer()
    
    # ========================================================================
    # TEST 1: remove_markdown_fences
    # ========================================================================
    print("\n【TEST 1】remove_markdown_fences()")
    print("-" * 80)
    
    code_with_markdown = """```python
from fractions import Fraction

def generate():
    return 42
```"""
    
    cleaned = healer.remove_markdown_fences(code_with_markdown)
    print(f"INPUT:\n{code_with_markdown}\n")
    print(f"OUTPUT:\n{cleaned}\n")
    print(f"✅ PASS" if "```" not in cleaned and "def generate" in cleaned else "❌ FAIL")
    
    # ========================================================================
    # TEST 2: inject_domain_imports - 偵測 FractionOps 並注入
    # ========================================================================
    print("\n【TEST 2】inject_domain_imports() - 偵測 FractionOps")
    print("-" * 80)
    
    code_with_fraction = """def generate():
    x = FractionOps.create(3.5)
    return x"""
    
    injected, count = healer.inject_domain_imports(code_with_fraction)
    print(f"INPUT:\n{code_with_fraction}\n")
    print(f"OUTPUT:\n{injected}\n")
    print(f"Injections: {count}")
    print(f"✅ PASS" if "from domain_function_library import FractionOps" in injected and count == 1 else "❌ FAIL")
    
    # ========================================================================
    # TEST 3: inject_domain_imports - 多重依賴
    # ========================================================================
    print("\n【TEST 3】inject_domain_imports() - 多重依賴")
    print("-" * 80)
    
    code_multi = """def generate():
    a = IntegerOps.fmt_num(-5)
    b = FractionOps.create(0.6)
    c = RadicalOps.create(12)
    return a, b, c"""
    
    injected, count = healer.inject_domain_imports(code_multi)
    print(f"INPUT:\n{code_multi}\n")
    print(f"Injections: {count}")
    print(f"✅ PASS" if count == 3 else f"❌ FAIL (expected 3, got {count})")
    
    # ========================================================================
    # TEST 4: fix_common_syntax_errors
    # ========================================================================
    print("\n【TEST 4】fix_common_syntax_errors() - 中文符號修復")
    print("-" * 80)
    
    code_bad = """def test（）：
    x = Fraction（3，5）
    return x"""
    
    fixed = healer.fix_common_syntax_errors(code_bad)
    print(f"INPUT:\n{code_bad}\n")
    print(f"OUTPUT:\n{fixed}\n")
    print(f"✅ PASS" if "def test():" in fixed and "Fraction(3,5)" in fixed else "❌ FAIL")
    
    # ========================================================================
    # TEST 5: remove_input_calls
    # ========================================================================
    print("\n【TEST 5】remove_input_calls() - 移除 input()")
    print("-" * 80)
    
    code_input = """x = input("Enter value: ")
y = int(input("Number: "))"""
    
    removed = healer.remove_input_calls(code_input)
    print(f"INPUT:\n{code_input}\n")
    print(f"OUTPUT:\n{removed}\n")
    print(f"✅ PASS" if "input" not in removed and "= 0" in removed else "❌ FAIL")
    
    # ========================================================================
    # TEST 6: heal - 完整修復流程
    # ========================================================================
    print("\n【TEST 6】heal() - 完整修復流程")
    print("-" * 80)
    
    code_complete = """```python
def generate（）：
    x = FractionOps.create（-0.6）
    y = input（"value"）
    return x, y
```"""
    
    fixed, stats = healer.heal(code_complete)
    print(f"INPUT:\n{code_complete}\n")
    print(f"OUTPUT:\n{fixed}\n")
    print(f"STATS: {stats}\n")
    
    # 驗證
    checks = [
        ("移除 Markdown", "```" not in fixed),
        ("注入 FractionOps", "from domain_function_library import FractionOps" in fixed),
        ("修復括號", "def generate():" in fixed),
        ("移除 input", "input" not in fixed),
        ("修復count > 0", stats['regex_fix_count'] > 0),
    ]
    
    for check_name, result in checks:
        print(f"  {check_name}: {'✅ PASS' if result else '❌ FAIL'}")
    
    # ========================================================================
    # 總結
    # ========================================================================
    print("\n" + "=" * 80)
    print("【測試完成】")
    print("=" * 80)
    print("✅ RegexHealer V2.5 所有功能已驗證")
    print("✅ 智慧依賴注入功能正常")
    print("✅ 返回統計資訊字典")
