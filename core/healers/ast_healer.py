# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱 (Module Name): core/healers/ast_healer.py
功能說明 (Description): AST 修復引擎，處理語法樹層級的問題
執行語法 (Usage): from core.healers import ASTHealer
版本資訊 (Version): V2.0 (Refactored from code_generator.py::fix_code_via_ast)
更新日期 (Date): 2026-01-30
維護團隊 (Maintainer): Math AI Project Team
=============================================================================
"""

import ast
import logging

logger = logging.getLogger(__name__)

class ASTHealer:
    """
    AST 修復引擎 - 處理語法樹層級的問題
    
    功能：
    1. 替換危險函數 (eval -> safe_eval)
    2. 修復遞迴死鎖
    3. 注入缺失的依賴
    
    ⚠️ 注意：此類別直接從 code_generator.py::fix_code_via_ast() 重構而來
    """
    
    def __init__(self):
        """初始化 AST Healer"""
        self.forbidden_funcs = ['eval', 'exec']
    
    def heal(self, code_str: str) -> tuple:
        """
        執行 AST 修復
        
        Args:
            code_str: 原始代碼字串
            
        Returns:
            tuple: (修復後代碼, 修復次數)
        """
        # ⚠️ 為了節省重構時間，暫時返回原代碼
        # TODO: 將 fix_code_via_ast() 的完整邏輯搬移到這裡
        
        # 臨時實現：調用舊函數（保證功能正常）
        from core.code_generator import fix_code_via_ast
        fixed_code = fix_code_via_ast(code_str)
        
        # 簡單計算修復次數
        fix_count = 0
        if fixed_code != code_str:
            # 計算替換次數（eval -> safe_eval）
            fix_count = code_str.count('eval(') - fixed_code.count('eval(')
            fix_count = max(0, fix_count)
        
        logger.info(f"AST Healer 完成，修復 {fix_count} 處")
        return fixed_code, fix_count
    
    # TODO: 將以下方法從 fix_code_via_ast() 拆分出來
    # def _replace_eval_to_safe_eval(self, tree): pass
    # def _fix_infinite_recursion(self, tree): pass
    # def _inject_missing_imports(self, tree): pass
