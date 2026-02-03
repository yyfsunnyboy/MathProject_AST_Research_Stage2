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

logger = logging.getLogger(__name__)

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
    
    def __init__(self):
        """初始化 AST Healer"""
        self.fixes = 0

    def visit_BinOp(self, node):
        """修復二元運算符"""
        self.generic_visit(node)
        # 1. 修復次方符號：將 XOR (^) 轉為 Pow (**)
        if isinstance(node.op, ast.BitXor):
            self.fixes += 1
            node.op = ast.Pow()
            return node
        return node

    def visit_Call(self, node):
        """修復函數調用"""
        self.generic_visit(node)
        
        # 0. [V10.0] 檢測並處理幻覺函數
        hallucinated_funcs = [
            'build_polynomial_text', 'format_polynomial', 'poly_to_latex',
            'build_expression', 'format_expression', 'latex_polynomial',
            'polynomial_text', 'expr_to_latex', 'build_latex'
        ]
        
        if isinstance(node.func, ast.Name) and node.func.id in hallucinated_funcs:
            self.fixes += 1
            logger.info(f"🔴 偵測到幻覺函數: {node.func.id}() -> build_polynomial_text()")
            node.func.id = 'build_polynomial_text'
            return node
        
        # 1. 攔截 eval/exec/safe_eval
        target_funcs = ['eval', 'exec', 'safe_eval']
        if isinstance(node.func, ast.Name) and node.func.id in target_funcs:
            self.fixes += 1
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
        """移除非法 import"""
        self.fixes += 1
        return None
    
    def visit_ImportFrom(self, node):
        """移除非法 from ... import"""
        self.fixes += 1
        return None
    
    def visit_FunctionDef(self, node):
        """修復函數定義"""
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
        
        return node
    
    def visit_While(self, node):
        """
        [Circuit Breaker] 將 while True 轉換為 for _ in range(1000)
        """
        self.generic_visit(node)
        
        is_infinite = False
        
        # 檢查是否為 while True
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            is_infinite = True
        elif hasattr(ast, 'NameConstant') and isinstance(node.test, ast.NameConstant) and node.test.value is True:
            is_infinite = True
            
        if is_infinite:
            self.fixes += 1
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
        # 預檢查：如果不包含需要修復的關鍵字，直接跳過
        keywords_need_ast = ['eval', 'exec', 'while True', '^', 'import ', '    def ']
        if not any(kw in code_str for kw in keywords_need_ast):
            return code_str, 0
        
        try:
            tree = ast.parse(code_str)
            new_tree = self.visit(tree)
            ast.fix_missing_locations(new_tree)
            
            new_code = ast.unparse(new_tree)
            
            # 📌 【方案 A】驗證 ast.unparse() 的輸出是否有效
            # 這是關鍵的防線：即使 unparse 成功執行，輸出代碼也可能有語法錯誤
            try:
                ast.parse(new_code)
                logger.info(f"✅ AST Healer 成功：輸出代碼驗證通過，修復 {self.fixes} 項")
                return new_code, self.fixes
            except SyntaxError as syntax_err:
                logger.warning(f"⚠️  AST unparse 產生無效代碼：{syntax_err}")
                logger.warning(f"🔄 回退使用 Regex Healer 的結果（安全降級）")
                return code_str, 0
                
        except Exception as e:
            logger.error(f"❌ AST Healing Failed: {e}")
            return code_str, 0
    
    # TODO: 將以下方法從 fix_code_via_ast() 拆分出來
    # def _replace_eval_to_safe_eval(self, tree): pass
    # def _fix_infinite_recursion(self, tree): pass
    # def _inject_missing_imports(self, tree): pass
