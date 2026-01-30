# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱 (Module Name): core/healers/regex_healer.py
功能說明 (Description): Regex 修復引擎，處理 LaTeX、Markdown、f-string 格式問題
執行語法 (Usage): from core.healers import RegexHealer
版本資訊 (Version): V2.0 (Refactored from code_generator.py::refine_ai_code)
更新日期 (Date): 2026-01-30
維護團隊 (Maintainer): Math AI Project Team

[修復規則列表 F.1-F.12]:
  F.1:  移除 Markdown 代碼塊標記 (```python / ```)
  F.2:  修復 f-string 缺失的 f 前綴
  F.3:  移除多餘空行
  F.4:  修復 LaTeX 指數格式 (x^2 -> x^{2})
  F.5:  移除註釋掉的 import 語句
  F.6:  移除禁用函數 (eval/exec)
  F.7:  移除重複的 import
  F.8:  修復 Markdown 殘留 (**bold**, *italic*)
  F.9:  修復 LaTeX 括號格式
  F.10: 移除冗餘的 utils 函數定義
  F.11: 修復多項式格式化函數
  F.12: 移除 clean_latex_output 調用
=============================================================================
"""

import re
import logging

logger = logging.getLogger(__name__)

class RegexHealer:
    """
    Regex 修復引擎 - 執行 F.1-F.12 格式修復規則
    
    ⚠️ 注意：此類別直接從 code_generator.py::refine_ai_code() 重構而來
    保持所有 regex pattern 不變以確保向後相容
    """
    
    def __init__(self):
        """初始化 Healer"""
        self.fix_count = 0
        
    def heal(self, code_str: str) -> tuple:
        """
        執行完整 Regex 修復流程
        
        Args:
            code_str: 原始代碼字串
            
        Returns:
            tuple: (修復後代碼, 修復次數)
        """
        # ⚠️ 為了節省重構時間，暫時返回原代碼
        # TODO: 將 refine_ai_code() 的完整邏輯搬移到這裡
        
        # 臨時實現：調用舊函數（保證功能正常）
        from core.code_generator import refine_ai_code
        refined_code = refine_ai_code(code_str)
        
        # 簡單計算修復次數（通過比較差異）
        fix_count = 0
        if refined_code != code_str:
            fix_count = len(code_str.split('\n')) - len(refined_code.split('\n'))
            fix_count = max(1, abs(fix_count))  # 至少修復 1 次
        
        logger.info(f"Regex Healer 完成，修復 {fix_count} 處")
        return refined_code, fix_count
    
    # TODO: 將以下方法從 refine_ai_code() 拆分出來
    # def _remove_markdown_blocks(self, code: str) -> tuple: pass
    # def _fix_fstring_prefix(self, code: str) -> tuple: pass
    # def _remove_redundant_blank_lines(self, code: str) -> tuple: pass
    # def _fix_latex_exponents(self, code: str) -> tuple: pass
    # ... F.1-F.12 的各個方法
