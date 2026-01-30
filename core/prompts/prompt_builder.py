# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱 (Module Name): core/prompts/prompt_builder.py
功能說明 (Description): Prompt 構建器，負責生成 LLM 的輸入 Prompt
執行語法 (Usage): from core.prompts import PromptBuilder
版本資訊 (Version): V2.0 (Refactored from code_generator.py)
更新日期 (Date): 2026-01-30
維護團隊 (Maintainer): Math AI Project Team
=============================================================================
"""

import logging

logger = logging.getLogger(__name__)

class PromptBuilder:
    """
    Prompt 構建器
    負責根據 Skill ID 和 Ablation Level 構建完整的 Prompt
    """
    
    @staticmethod
    def build(skill_id: str, **kwargs) -> str:
        """
        構建完整 Prompt
        
        Args:
            skill_id: 技能 ID
            **kwargs: 其他參數（ablation_id, prompt_level 等）
            
        Returns:
            str: 完整的 Prompt 字串
        """
        # ⚠️ 臨時實現：調用舊邏輯
        # TODO: 將 Prompt 構建邏輯從 auto_generate_skill_code() 中提取出來
        
        from core.code_generator import get_dynamic_skeleton
        skeleton = get_dynamic_skeleton(skill_id)
        
        logger.info(f"Prompt 構建完成（Skill: {skill_id}）")
        return skeleton
    
    # TODO: 實現以下方法
    # def _build_bare_prompt(self, skill_id): pass
    # def _build_engineered_prompt(self, skill_id): pass
    # def _build_full_prompt(self, skill_id): pass
