# -*- coding: utf-8 -*-
# ==============================================================================
# ID: core/healers/ast_healer.py
# Version: V2.1 (Refactored from code_generator.py)
# Last Updated: 2026-01-30
# Author: Math AI Research Team (Advisor & Student)
#
# [Description]:
#   AST 修復引擎 - 處理語法樹層級的問題
#   [V45.0 AST Logic Surgeon] 深入語法樹層級，修復 Regex 無法觸及的邏輯錯誤
#
# [Core Technology]:
#   使用 ast.NodeTransformer 遍歷和修改抽象語法樹 (AST)
#
# [Functionality]:
#   1. 修復幻覺函數 (build_polynomial_text, format_polynomial 等)
#   2. 替換危險函數 (eval/exec -> safe_eval)
#   3. 修復無窮迴圈 (while True -> for loop)
#   4. 清理非法 import
#   5. 修復 fmt_num 參數問題
#
# [Logic Flow]:
#   1. parse -> AST Tree
#   2. transform -> visit nodes -> modify/replace nodes
#   3. unparse -> Fixed Code
# ==============================================================================

import ast
import re
import logging
import sys

logger = logging.getLogger(__name__)


class _ScopeBindingVisitor(ast.NodeVisitor):
    """Collect bindings in one lexical scope without entering child scopes."""

    def __init__(self):
        self.names = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.names.add(node.id)

    def visit_arg(self, node):
        self.names.add(node.arg)

    def visit_Import(self, node):
        for item in node.names:
            self.names.add(item.asname or item.name.split('.')[0])

    def visit_ImportFrom(self, node):
        for item in node.names:
            if item.name != '*':
                self.names.add(item.asname or item.name)

    def visit_FunctionDef(self, node):
        self.names.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.names.add(node.name)

    def visit_Lambda(self, node):
        return None


class _SameScopeImportUseVisitor(ast.NodeVisitor):
    """Find a load that resolves to an import binding, ignoring shadowed scopes."""

    def __init__(self, binding, require_attribute):
        self.binding = binding
        self.require_attribute = require_attribute
        self.used = False

    @staticmethod
    def _local_bindings(node):
        visitor = _ScopeBindingVisitor()
        for argument in (
            list(node.args.posonlyargs)
            + list(node.args.args)
            + list(node.args.kwonlyargs)
        ):
            visitor.visit(argument)
        if node.args.vararg:
            visitor.visit(node.args.vararg)
        if node.args.kwarg:
            visitor.visit(node.args.kwarg)
        for statement in node.body:
            visitor.visit(statement)
        return visitor.names

    def visit_Name(self, node):
        if (
            not self.require_attribute
            and isinstance(node.ctx, ast.Load)
            and node.id == self.binding
        ):
            self.used = True

    def visit_Attribute(self, node):
        if (
            self.require_attribute
            and isinstance(node.value, ast.Name)
            and isinstance(node.value.ctx, ast.Load)
            and node.value.id == self.binding
        ):
            self.used = True
        if not self.used:
            self.generic_visit(node)

    def _visit_function(self, node):
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in list(node.args.defaults) + [
            item for item in node.args.kw_defaults if item is not None
        ]:
            self.visit(default)
        if self.used or self.binding in self._local_bindings(node):
            return
        for statement in node.body:
            self.visit(statement)
            if self.used:
                return

    visit_FunctionDef = _visit_function
    visit_AsyncFunctionDef = _visit_function

    def visit_ClassDef(self, node):
        bindings = _ScopeBindingVisitor()
        for statement in node.body:
            bindings.visit(statement)
        if self.binding in bindings.names:
            return
        for statement in node.body:
            self.visit(statement)
            if self.used:
                return

    def visit_Lambda(self, node):
        bindings = {item.arg for item in node.args.args}
        if self.binding not in bindings:
            self.visit(node.body)

class ASTHealer(ast.NodeTransformer):
    """
    AST 修復引擎 - 處理語法樹層級的問題
    [V45.0 AST Logic Surgeon] 深入語法樹層級，修復 Regex 無法觸及的邏輯錯誤
    
    功能：
    1. 修復幻覺函數 (build_polynomial_text, format_polynomial 等)
    2. 替換危險函數 (eval/exec -> safe_eval)
    3. 修復無窮迴圈 (while True -> for loop)
    4. 清理非法 import
    5. 修復 fmt_num 參數問題
    """

    BLOCKED_IMPORT_ROOTS = {
        'builtins', 'ctypes', 'ensurepip', 'ftplib', 'http', 'importlib',
        'marshal', 'multiprocessing', 'os', 'pathlib', 'pickle', 'resource',
        'shelve', 'shutil', 'signal', 'smtplib', 'socket', 'sqlite3',
        'subprocess', 'sys', 'tempfile', 'urllib', 'webbrowser', 'winreg',
    }
    DOMAIN_MODES = frozenset({'benchmark', 'math_generator'})
    
    def __init__(self, ai_client=None, require_entry_point: bool = True,
                 entry_point: str = "generate", domain_mode: str = "benchmark"):
        """
        初始化 AST Healer
        
        Args:
            ai_client: (Optional) 用於執行 Semantic Healing 的 AI 客戶端
            require_entry_point: 是否在缺失進入點函式時注入備用函式（數學出題預設 True）
            entry_point: 進入點函式名稱（數學出題預設 generate）
            domain_mode: benchmark preserves Python semantics; math_generator
                enables legacy math-generator rewrites.
        """
        if domain_mode not in self.DOMAIN_MODES:
            raise ValueError(
                f"unsupported AST healer domain_mode={domain_mode!r}; "
                f"expected one of {sorted(self.DOMAIN_MODES)}"
            )
        self.fixes = 0
        self.ai_client = ai_client
        self.logs = []
        self.require_entry_point = require_entry_point
        self.entry_point = entry_point
        self.domain_mode = domain_mode
        self._preserved_import_aliases = set()

    @staticmethod
    def _statement_binds_name(statement, name):
        visitor = _ScopeBindingVisitor()
        visitor.visit(statement)
        return name in visitor.names

    @staticmethod
    def _statement_uses_import(statement, binding, require_attribute):
        visitor = _SameScopeImportUseVisitor(binding, require_attribute)
        visitor.visit(statement)
        return visitor.used

    def _binding_used_after(self, statements, import_index, binding, require_attribute):
        for statement in statements[import_index + 1:]:
            # Ambiguous evaluation order or a definite rebinding fails closed.
            if self._statement_binds_name(statement, binding):
                return False
            if self._statement_uses_import(statement, binding, require_attribute):
                return True
        return False

    def _is_preservable_stdlib(self, module):
        if not module:
            return False
        root = module.split('.')[0]
        stdlib_modules = getattr(sys, 'stdlib_module_names', frozenset())
        return root in stdlib_modules and root not in self.BLOCKED_IMPORT_ROOTS

    def _prepare_import_preservation(self, tree):
        self._preserved_import_aliases = set()
        scope_types = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        for scope in (node for node in ast.walk(tree) if isinstance(node, scope_types)):
            statements = scope.body
            for index, statement in enumerate(statements):
                if isinstance(statement, ast.Import):
                    for item in statement.names:
                        if not self._is_preservable_stdlib(item.name):
                            continue
                        binding = item.asname or item.name.split('.')[0]
                        if self._binding_used_after(
                            statements, index, binding, require_attribute=True
                        ):
                            self._preserved_import_aliases.add(id(item))
                elif (
                    isinstance(statement, ast.ImportFrom)
                    and statement.level == 0
                    and self._is_preservable_stdlib(statement.module)
                ):
                    for item in statement.names:
                        if item.name == '*':
                            continue
                        binding = item.asname or item.name
                        if self._binding_used_after(
                            statements, index, binding, require_attribute=False
                        ):
                            self._preserved_import_aliases.add(id(item))

    def visit_BinOp(self, node):
        """修復二元運算符"""
        self.generic_visit(node)
        # This legacy rewrite is only valid inside the explicit math generator.
        if self.domain_mode == 'math_generator' and isinstance(node.op, ast.BitXor):
            self.fixes += 1
            self.logs.append("AST Healer: Replaced BitXor (^) with Pow (**)")
            node.op = ast.Pow()
            return node
        return node

    def visit_Call(self, node):
        """修復函數調用"""
        self.generic_visit(node)

        # 00. [V50.3] 攔截 input() -> 直接閹割，避免卡死
        # 將 input(...) 替換為常數字串 "0" (避免後續 int() 轉換失敗)
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            
        if func_name == 'input':
            self.fixes += 1
            self.logs.append("AST Healer: Removed dangerous input() call")
            logger.warning("💉 AST Healer: 偵測到 input()，正在切除... (Replaced with '0')")
            return ast.Constant(value="0")
        
        # 0. [V10.0] 檢測並處理幻覺函數
        hallucinated_funcs = [
            'build_polynomial_text', 'format_polynomial', 'poly_to_latex',
            'build_expression', 'latex_polynomial',
            'polynomial_text', 'expr_to_latex', 'build_latex'
        ]
        
        if isinstance(node.func, ast.Name) and node.func.id in hallucinated_funcs:
            self.fixes += 1
            self.logs.append(f"AST Healer: Replaced hallucinated function {node.func.id}() with build_polynomial_text()")
            logger.info(f"🔴 偵測到幻覺函數: {node.func.id}() -> build_polynomial_text()")
            node.func.id = 'build_polynomial_text'
            return node
        
        # 1. 攔截 eval/exec（safe_eval 是合法替換目標，不列入）
        target_funcs = ['eval', 'exec']
        if isinstance(node.func, ast.Name) and node.func.id in target_funcs:
            self.fixes += 1
            self.logs.append(f"AST Healer: Replaced dangerous function {node.func.id}() with safe_eval()")
            node.func.id = 'safe_eval'
            
            # 強制清洗參數（只保留第一個）
            if len(node.args) > 1:
                logger.info(f"🧹 清除 safe_eval 的多餘參數")
                node.args = [node.args[0]]
            return node
        
        # 2. 處理 fmt_num [V47.11 增強版]
        if isinstance(node.func, ast.Name) and node.func.id == 'fmt_num':
            # [新增] 檢查參數類型
            # fmt_num 期望：int/float/Fraction（標量數值）
            # fmt_num 不能接受：list/array/coeffs（集合）
            if node.args and isinstance(node.args[0], (ast.List, ast.Tuple)):
                # 這是在調用 fmt_num(list) 或 fmt_num(tuple)，是錯的
                # 不進行修復，保留原代碼讓後續的 F.9 處理
                return node
            
            # 移除幻想參數
            if node.keywords:
                original_len = len(node.keywords)
                node.keywords = [k for k in node.keywords if k.arg in ['signed', 'op']]
                if len(node.keywords) != original_len:
                    self.fixes += 1
            
            # 補救空參數（只有在參數確實為空時）
            if not node.args:
                self.fixes += 1
                self.logs.append("AST Healer: Injected random integers for empty fmt_num() call")
                node.args = [
                    ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id='random', ctx=ast.Load()),
                            attr='randint',
                            ctx=ast.Load()
                        ),
                        args=[
                            ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=10)),
                            ast.Constant(value=10)
                        ],
                        keywords=[]
                    )
                ]
            return node
        
        # 3. 格式化函式重定向 [V47.11 CRITICAL FIX]
        # [已禁用] 原因：這個修復會把 _format_poly_string(coeffs) 改成 fmt_num(coeffs)
        # 導致 fmt_num 收到無法處理的 list 參數，而且後續 F.9 修復會進一步把它改成不存在的函數名
        #
        # 新策略：
        # 1. 保護所有已知的多項式格式化函數（不進行改名）
        # 2. 只有在確認是「幻覺函數」（被調用但未定義）時才改名
        # 3. 改名時也要考慮參數類型（fmt_num 不接受 list）
        
        if isinstance(node.func, ast.Name):
            protected = {
                'fmt_num', 'to_latex', 'clean_latex_output', 'check', 'safe_eval',
                'gcd', 'lcm', 'is_prime', 'get_factors',
                'clamp_fraction', 'safe_pow', 'factorial_bounded', 'nCr', 'nPr',
                'rational_gauss_solve', 'normalize_angle',
                'fmt_set', 'fmt_interval', 'fmt_vec',
                # [V47.11] 保護所有已知的多項式相關函數
                '_format_poly_string', '_format_derivative_symbol', '_differentiate_coeffs',
                'build_polynomial_text', 'format_polynomial', 'polynomial_to_latex',
                'polynomial_to_string', 'fmt_polynomial', 'poly_to_latex'
            }
            
            # 不再進行自動重定向 - 讓 LLM 生成的函數名保持原樣
            # AST 層級應該只修復結構性錯誤，不應該進行函數名稱轉換
            pass
        return node
    
    def visit_Import(self, node):
        """移除非法 import，但保留安全的數學相關模組"""
        safe_modules = {'math', 'random', 'fractions', 'decimal', 're'}
        new_names = [
            alias for alias in node.names
            if alias.name.split('.')[0] in safe_modules
            or id(alias) in self._preserved_import_aliases
        ]
        
        if len(new_names) < len(node.names):
            self.fixes += 1
            removed = [alias.name for alias in node.names if alias not in new_names]
            self.logs.append(f"AST Healer: Removed dangerous import(s): {', '.join(removed)}")
            
        if not new_names:
            return None
            
        node.names = new_names
        return node
    
    def visit_ImportFrom(self, node):
        """移除非法 from ... import，但保留安全的數學相關模組"""
        safe_modules = {
            'math', 'random', 'fractions', 'decimal', 're', 'typing',
            # 'core' is trusted: core.domain_functions provides
            # DomainFunctionHelper for the Radical Orchestrator scaffold.
            # Stripping this import would silently break radical code execution.
            'core',
        }
        if (
            node.level == 0
            and node.module
            and node.module.split('.')[0] in safe_modules
            and all(item.name != '*' for item in node.names)
        ):
            return node

        preserved_names = [
            item for item in node.names if id(item) in self._preserved_import_aliases
        ]
        if preserved_names:
            if len(preserved_names) < len(node.names):
                self.fixes += 1
                removed = [item.name for item in node.names if item not in preserved_names]
                self.logs.append(
                    f"AST Healer: Removed unreferenced import(s) from {node.module}: "
                    f"{', '.join(removed)}"
                )
            node.names = preserved_names
            return node
            
        self.fixes += 1
        self.logs.append(f"AST Healer: Removed dangerous from...import: {ast.unparse(node)}")
        return None
    
    def visit_FunctionDef(self, node):
        """修復函數定義"""
        # [V50.3 Shadow Killer Relaxed] 
        # 修正：不再無條件刪除與標準庫重名的函數，除非它們是空的或只有 pass
        shadowed_funcs = {
            'fmt_num', 'to_latex', 'clean_latex_output', 'check', 'safe_eval',
            'gcd', 'lcm', 'is_prime', 'get_factors', 'safe_choice',
            'clamp_fraction', 'safe_pow', 'factorial_bounded', 'nCr', 'nPr',
            'rational_gauss_solve', 'normalize_angle',
            'fmt_set', 'fmt_interval', 'fmt_vec',
            'build_polynomial_text', 'format_polynomial', 'polynomial_to_latex'
        }
        
        if node.name in shadowed_funcs:
            # 檢查是否為空實作 (Empty or Pass only)
            is_trivial = False
            if len(node.body) == 0:
                is_trivial = True
            elif len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                is_trivial = True
            elif len(node.body) == 1 and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                 # Only a docstring
                is_trivial = True
                
            if is_trivial:
                self.fixes += 1
                self.logs.append(f"AST Healer: Shadow Killer removed duplicate function definition '{node.name}'")
                logger.info(f"🔪 Shadow Killer: 刪除空的重複定義 '{node.name}' (使用 Injected Utils)")
                return None
            else:
                logger.info(f"🛡️ Shadow Killer: 保留自定義實作 '{node.name}' (非空函數)")


        # [NEW] 強制刪除清單 (Forbidden local duplicates)
        forbidden_helper_funcs = {
            'format_poly', 'format_polynomial_latex', 'format_term', 'poly_to_latex', 'build_poly', 'build_polynomial', 'format_polynomial'
        }
        
        if node.name in forbidden_helper_funcs:
            self.fixes += 1
            self.logs.append(f"AST Healer: Shadow Killer forcefully removed forbidden helper function '{node.name}'")
            logger.info(f"🔪 Shadow Killer: 強制刪除違規本地函數 '{node.name}' (應使用全域資源)")
            return None

        self.generic_visit(node)
        
        # 1. 移除明顯的虛函數 [V47.13 CONSERVATIVE FIX]
        # [改進策略] 不使用白名單，改為只刪除明顯無用的虛函數：
        # - 空函數（只有 pass 或 docstring）
        # - 明顯的 CamelCase 虛函數（如 FormatPolynomial, DisplayLatex）
        # - 不刪除任何以 _ 開頭的輔助函數（信任 LLM 生成的工具函數）
        
        # 保護 generate 和所有 _ 開頭的函數
        if node.name == 'generate' or node.name.startswith('_'):
            pass  # 不刪除
        else:
            # 只刪除明顯的 CamelCase 虛函數（首字母大寫 + 包含格式化關鍵字）
            # 例如：FormatPolynomial, DisplayLatex, BuildQuestion 等
            if re.match(r'^[A-Z][a-zA-Z]*(?:Format|Latex|Display|Build|Create|Make)', node.name):
                # 額外檢查：如果函數體只有 pass 或 docstring，才刪除
                is_empty = True
                for stmt in node.body:
                    if isinstance(stmt, ast.Pass):
                        continue
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                        continue  # docstring
                    is_empty = False
                    break
                
                if is_empty:
                    self.fixes += 1
                    self.logs.append(f"AST Healer: Removed useless empty function '{node.name}'")
                    return None 
        
        # 2. 檢測內部輔助函數是否缺少默認返回值
        if node.name != 'generate' and node.body:
            has_loop = any(isinstance(stmt, (ast.For, ast.While)) for stmt in node.body)
            
            if has_loop:
                last_stmt = node.body[-1]
                if not isinstance(last_stmt, ast.Return):
                    logger.info(f"🔧 內部函數 '{node.name}' 缺少默認返回值")
                    default_return = ast.Return(
                        value=ast.Tuple(
                            elts=[ast.Constant(value=0), ast.Constant(value=0)],
                            ctx=ast.Load()
                        )
                    )
                    node.body.append(default_return)
                    self.fixes += 1
                    self.logs.append(f"AST Healer: Injected default return statement for function '{node.name}'")
        
        return node
    
    def visit_While(self, node):
        """
        Apply the legacy circuit breaker only in explicit math-generator mode.

        Benchmark evaluation owns timeout enforcement. Rewriting a Python loop
        changes its semantics and is therefore refused in benchmark mode.
        """
        self.generic_visit(node)

        if self.domain_mode != 'math_generator':
            return node
        
        is_infinite = False
        
        # 檢查是否為 while True
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            is_infinite = True
        elif hasattr(ast, 'NameConstant') and isinstance(node.test, ast.NameConstant) and node.test.value is True:
            is_infinite = True
            
        if is_infinite:
            self.fixes += 1
            self.logs.append("AST Healer: Circuit Breaker triggered: Replaced while True with for loop")
            logger.info(f"🛑 熔斷機制啟動: while True -> for loop (1000 runs)")
            
            return ast.For(
                target=ast.Name(id='_safety_loop_var', ctx=ast.Store()),
                iter=ast.Call(
                    func=ast.Name(id='range', ctx=ast.Load()),
                    args=[ast.Constant(value=1000)],
                    keywords=[]
                ),
                body=node.body,
                orelse=node.orelse,
                type_comment=None
            )
            
        return node

    def visit_Assign(self, node):
        """修復賦值語句"""
        self.generic_visit(node)
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
            target_tuple = node.targets[0]
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'fmt_num':
                self.fixes += 1
                self.logs.append("AST Healer: Fixed tuple assignment for fmt_num()")
                val_var = target_tuple.elts[0]
                latex_var = target_tuple.elts[1]
                if node.value.args:
                    num_source = node.value.args[0]
                else:
                    num_source = ast.Call(
                        func=ast.Attribute(value=ast.Name(id='random', ctx=ast.Load()), attr='randint', ctx=ast.Load()),
                        args=[ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=10)), ast.Constant(value=10)],
                        keywords=[]
                    )
                assign_val = ast.Assign(targets=[val_var], value=num_source)
                assign_latex = ast.Assign(
                    targets=[latex_var],
                    value=ast.Call(
                        func=ast.Name(id='fmt_num', ctx=ast.Load()),
                        args=[val_var],
                        keywords=node.value.keywords
                    )
                )
                return [assign_val, assign_latex]
        
        return node
    
    def heal(self, code_str: str) -> tuple:
        """
        執行 AST 修復
        
        Args:
            code_str: 原始代碼字串
            
        Returns:
            tuple: (修復後代碼, 修復次數)
        """
        # [V51.0] Iterative Syntax Repair (Syntax De-Noising)
        # 嘗試刪除導致語法錯誤的行（如 Thinking Leakage, 亂碼符號）
        for attempt in range(5):
            try:
                tree = ast.parse(code_str)
                break # Syntax Valid!
            except SyntaxError as e:
                lines = code_str.split('\n')
                if 1 <= e.lineno <= len(lines):
                    removed = lines.pop(e.lineno - 1)
                    self.fixes += 1
                    self.logs.append(f"AST Healer: Syntax Repair: Removed line {e.lineno} causing SyntaxError")
                    logger.warning(f"🔪 AST Syntax Repair: 刪除語法錯誤行 {e.lineno}: {removed.strip()}")
                    code_str = '\n'.join(lines)
                else:
                    logger.error(f"❌ AST Syntax Repair Failed: Line {e.lineno} out of range")
                    break
            except Exception as e:
                logger.error(f"❌ AST Input Error: {e}")
                break

        try:
            tree = ast.parse(code_str) # Re-parse final version
            self._prepare_import_preservation(tree)
            new_tree = self.visit(tree)
            ast.fix_missing_locations(new_tree)
            
            # [V52.0 Core Safety Net] 保證進入點函式存在（僅數學出題等 require_entry_point 模式）
            has_entry = any(isinstance(node, ast.FunctionDef) and node.name == self.entry_point
                            for node in new_tree.body)
            if self.require_entry_point and not has_entry:
                self.fixes += 1
                self.logs.append(
                    f"AST Healer: Critical Hallucination - Injected missing {self.entry_point}() fallback.")
                logger.error(
                    f"🛑 偵測到致命性幻覺：完全缺失 {self.entry_point}() 函式。"
                    f"正在啟動【最後防線】注入備用函式...")

                # ── Context-aware fallback ───────────────────────────────────
                # If the code already references DomainFunctionHelper (radical
                # orchestrator scaffold), the injected generate() tries to use
                # it so a valid radical problem is still produced.
                # For all other skills the inner except clause returns the safe
                # placeholder dict that keeps MCRI from crashing.
                #
                # NOTE: this function is appended AFTER self.visit() already ran,
                # so visit_ImportFrom will NOT strip the import inside the try block.
                _fallback_src = (
                    f"def {self.entry_point}(level=1, **kwargs):\n"
                    f"    # Injected by AST Healer — assembly failure signal\n"
                    "    return {\n"
                    f"        'question_text':  'Fallback due to missing {self.entry_point}() wrapper',\n"
                    "        'correct_answer': '\\\\text{Failed}',\n"
                    "    }\n"
                )
                try:
                    _fb_tree = ast.parse(_fallback_src)
                    fallback_func = _fb_tree.body[0]
                except Exception:
                    # Ultra-safe last resort: plain dict return via AST nodes
                    fallback_func = ast.FunctionDef(
                        name=self.entry_point,
                        args=ast.arguments(
                            posonlyargs=[], args=[], kwonlyargs=[],
                            kw_defaults=[], defaults=[],
                        ),
                        body=[
                            ast.Return(
                                value=ast.Dict(
                                    keys=[
                                        ast.Constant(value="question_text"),
                                        ast.Constant(value="correct_answer"),
                                    ],
                                    values=[
                                        ast.Constant(
                                            value=f"Fallback due to missing {self.entry_point}() wrapper"),
                                        ast.Constant(value="\\text{Failed}"),
                                    ],
                                )
                            )
                        ],
                        decorator_list=[],
                        returns=None,
                        type_comment=None,
                    )
                new_tree.body.append(fallback_func)
                ast.fix_missing_locations(new_tree)

            new_code = ast.unparse(new_tree)
            
            # 📌 【方案 A】驗證 ast.unparse() 的輸出是否有效
            try:
                ast.parse(new_code)
                return new_code, self.fixes
            except SyntaxError as syntax_err:
                logger.warning(f"⚠️  AST unparse 產生無效代碼：{syntax_err}")
                return code_str, self.fixes # Return modified code (at least we removed garbage lines)
                
        except Exception as e:
            logger.error(f"❌ AST Healing Failed: {e}")
            if self.fixes > 0:
                return code_str, self.fixes # Return partial fixes (garbage removed)
            return code_str, 0
    
    # TODO: 將以下方法從 fix_code_via_ast() 拆分出來
    # def _replace_eval_to_safe_eval(self, tree): pass
    # def _fix_infinite_recursion(self, tree): pass
    # def _inject_missing_imports(self, tree): pass

    # ==============================================================================
    # [V50.0 Semantic Self-Correction] Hybrid Healing Extension
    # ==============================================================================

    def semantic_heal(self, code_str: str, error_msg: str, model_name: str = 'qwen2.5-coder:14b') -> tuple:
        """
        [Dynamic] 使用 LLM 進行語意層級的自我修復 (Self-Correction)
        當靜態 AST 分析無法解決問題時（如變數未定義、邏輯錯誤），啟用此功能。
        
        Args:
            code_str: 執行失敗的代碼
            error_msg: 錯誤堆疊訊息 (Traceback)
            model_name: 使用的模型名稱
            
        Returns:
            tuple: (修復後的代碼, 是否成功修復)
        """
        if not self.ai_client:
            logger.warning("⚠️  Semantic Heal Skipped: No AI Client provided.")
            return code_str, False

        # [Safety Check] 防止使用超大 Context 的模型 (如 Gemini 3.0 Preview, 65k tokens) 進行修復
        # 因為那會導致極度漫長的等待，甚至看起來像死循環。
        if hasattr(self.ai_client, 'max_tokens') and self.ai_client.max_tokens > 20000:
            logger.warning(f"⏩ 跳過 Semantic Heal: Client max_tokens ({self.ai_client.max_tokens}) 過大，避免卡死。")
            return code_str, False

        logger.info(f"🧠 啟動 Semantic Healer (Self-Correction)...")
        logger.debug(f"Error Context: {error_msg.splitlines()[-1]}")

        # 1. 建構 Prompt
        prompt = f"""
You are an expert Python debugger. The following code failed to execute.
Please fix the logic error based on the error message provided.

[BROKEN CODE]:
{code_str}

[ERROR MESSAGE]:
{error_msg}

[INSTRUCTIONS]:
1. Identify the variable or logic error causing the crash (e.g. NameError, TypeError).
2. Fix the code to ensure it runs correctly and returns valid output.
3. OUTPUT ONLY THE FULL FIXED PYTHON CODE.
4. DO NOT wrap with markdown code blocks. DO NOT add explanations. JUST THE CODE.
"""
        # messages = [
        #     {"role": "system", "content": "You are a Python coding assistant. Output only raw code."},
        #     {"role": "user", "content": prompt}
        # ]

        try:
            # 2. 呼叫 LLM
            # [FIX] 使用 generate_content (適配 GoogleAIClient/LocalAIClient)
            # 原來的 chat_completion 不存在於 wrapper 中
            
            # [Refactored] 使用 shared retry logic (2 retries for healing is enough)
            from core.ai_wrapper import call_ai_with_retry
            
            if hasattr(self.ai_client, 'generate_content'):
                response = call_ai_with_retry(
                    client=self.ai_client,
                    prompt=prompt,
                    max_retries=2,
                    retry_delay=2,
                    verbose=True
                )
                
                # Wrapper 返回的是 MockResponse 對象，需取 .text
                if hasattr(response, 'text'):
                    fixed_code_raw = response.text
                else:
                    fixed_code_raw = str(response) # Fallback
            else:
                 logger.error("❌ AI Client 不支援 generate_content")
                 return code_str, False

            # 3. 清理輸出的 Markdown
            fixed_code = fixed_code_raw.replace("```python", "").replace("```", "").strip()
            
            if not fixed_code:
                logger.error("❌ Semantic Healer returned empty code.")
                return code_str, False

            # 4. 簡單驗證語法 (Syntax Check)
            try:
                ast.parse(fixed_code)
            except SyntaxError:
                logger.warning("❌ Semantic Healer generated invalid syntax.")
                return code_str, False

            # 5. 更新計數器並返回
            if fixed_code != code_str:
                self.fixes += 1
                self.logs.append(f"Semantic Healer: Successfully self-corrected runtime error")
                logger.info(f"✅ Semantic Healer 應用修正 (Fixes count: {self.fixes})")
                return fixed_code, True
            else:
                logger.info("○ Semantic Healer 建議不變更代碼")
                return code_str, False

        except Exception as e:
            logger.error(f"❌ Semantic Healing Error: {e}")
            return code_str, False

