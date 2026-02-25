# -*- coding: utf-8 -*-
# ==============================================================================
# ID: core/prompts/assembler.py
# Description: 動態數學 Prompt 組裝器
# ==============================================================================
from core.prompts.domain_library import DomainLibrary

def assemble_prompt(target_question_dna: str, domain_tag: str) -> str:
    """
    動態組裝 Prompt 的核心引擎。
    將目標例題、領域限定邏輯與通用鐵律結合成一段給予 LLM 的嚴謹指令。
    """
    domain_config = DomainLibrary.get_domain_config(domain_tag)
    base_rules = DomainLibrary.BASE_RULES

    role = domain_config['role']
    tools = domain_config['tools']
    logic = domain_config['logic']
    
    # 動態分析複雜度
    complexity_hint = ""
    if any(op in target_question_dna for op in ['/', '÷']):
        complexity_hint += "\n[特別提醒]: 此題包含除法，請務必使用「商 * 除數 = 被除數」的邏輯來生成，避免出現小數。"
    
    if len(target_question_dna) > 20: # 假設字串很長代表很複雜
        complexity_hint += "\n[特別提醒]: 此題結構較深，請務必使用變數 `term1`, `term2` 等分段計算，不准寫成一行長算式。"

    prompt = f"""
----------------------------------------
【角色設定】
你是一位嚴謹的 {role}。

【任務目標】
你需要進行「邏輯逆向工程」，精準模仿下方提供的【目標例題 DNA】，寫出能夠隨機動態生成該類題型的 Python 函式 `generate(level=1, **kwargs)`。

【目標例題 DNA】
{target_question_dna}

{complexity_hint}

【🧠 逆向工程與領域邏輯導引】
必須嚴格遵守以下邏輯：
{logic}

【🔧 強制限定工具手冊】
你【必須且唯一】依賴以下工具進行計算與渲染：
{tools}

{base_rules}

----------------------------------------
"""
    return prompt.strip()
