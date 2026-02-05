# -*- coding: utf-8 -*-
# ==============================================================================
# ID: core/prompts/prompt_builder.py
# Version: V2.3 (Added BARE_PROMPT_TEMPLATE for realistic user simulation)
# Last Updated: 2026-01-30
# Author: Math AI Research Team (Advisor & Student)
#
# [Description]:
#   Prompt 構建引擎 - 負責生成不同 Ablation 模式的 Prompt
#   [Research Edition] 用於消融研究實驗
#
# [Ablation Modes]:
#   1. BARE_PROMPT_TEMPLATE: 模擬一般用戶的 Prompt（Ab1 對照組）
#   2. UNIVERSAL_GEN_CODE_PROMPT: 完整規格書（Ab2/Ab3 實驗組）
#
# [Core Technology]:
#   - Template-based prompt generation
#   - Dynamic prompt assembly based on mode
#
# [Logic Flow]:
#   1. Input: (master_spec, mode, model_name)
#   2. Select Template based on mode
#   3. Inject MASTER_SPEC or Examples
#   4. Return final prompt string
# ==============================================================================

import logging

logger = logging.getLogger(__name__)

# ==============================================================================
# [2026-01-30 新增] Ab1 Bare Prompt Template - 模擬一般用戶
# ==============================================================================
# 設計理念：
# - 模擬「一般老師」會如何跟 AI 下 Prompt
# - 使用自然語言，無工程化指導
# - 給 1-2 個參考例題，讓 AI 自己推理
# - 完全獨立於 UNIVERSAL_GEN_CODE_PROMPT 和 MASTER_SPEC
# ==============================================================================

BARE_PROMPT_TEMPLATE = """【角色設定】
你是一位中學數學老師的「出題助理」。

【任務說明】
請幫我寫一個 Python 程式，用來自動生成數學題目。
★ 題目主題是：「{topic}」（請務必針對此主題出題，不要生成其他類型的題目）
這個程式需要隨機產生數字，每次執行都能變換數值。
請使用跟課本一樣的格式表達數學式子。

【參考例題】
以下是我們想模仿的題目類型（請參考這個邏輯來寫程式）：
{textbook_example}

【程式要求】
1. 請寫成兩個函式：
   - `def generate(level=1, **kwargs)`: 生成題目
   - `def check(user_answer, correct_answer)`: 檢查答案是否正確

2. `generate` 函式要回傳一個字典 (Dictionary)，包含以下欄位（請照抄 key 名稱）：
   - 'question_text': 題目文字
   - 'answer': 空字串 ''
   - 'correct_answer': 正確答案（必須是字串，例如："24" 或 "3x^2+5"；多個答案用逗號分隔）
   - 'mode': 1

3. `check` 函式請回傳一個字典，包含：
   - 'correct': True 或 False
   - 'result': 回傳 '正確' 或 '錯誤'

4. 請使用 Python 的 standard library (如 random, math) 即可。
   - 🔴 重要：不要使用 sympy、numpy 或其他外部套件

⚠️ 重要：只輸出 Python 程式碼！
- ✅ 正確：直接從 import 開始寫
- ❌ 錯誤：不要加任何說明文字或註解在程式碼之外
- ❌ 錯誤：不要在程式碼後面加「這個程式碼會...」的說明
- ❌ 錯誤：不要在程式碼後面加英文說明（如 "This code defines..."）
- ❌ 錯誤：不要用 ```python 包裹代碼
- ❌ 錯誤：不要加 Example usage 或 `if __name__ == '__main__'`
- ❌ 錯誤：不要加 Explanation/說明段落
- 🔴 CRITICAL：程式碼結束後不可有任何文字（包括空白行後的說明）
"""

# ==============================================================================
# [Fallback] BARE_MINIMAL_PROMPT - 保留作為備用
# ==============================================================================
# 注意：這個已被 BARE_PROMPT_TEMPLATE 取代，但保留以保持向後相容
# ==============================================================================

BARE_MINIMAL_PROMPT = r"""你是 Python 程式設計師。請根據以下 MASTER_SPEC 生成數學題目生成函數。

要求：
1. 實作函數：def generate(level=1, **kwargs)
2. ⚠️ 回傳字典格式（必須同時包含雙鍵）：
   return {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}
3. 只輸出 Python 代碼，不要有任何說明或 Markdown 標記

🔴 LaTeX 格式鐵律（必須遵守）：
   question_text 格式：
      ✅ 正確："計算 $(-3) + 5$ 的值"（中文在外，數學式用 $ $ 包裹）
      ✅ 正確："求 $2 \times (-4)$ 的結果"
      ❌ 錯誤："$(-3) + 5$"（缺少中文說明）
      ❌ 錯誤："計算$(-3) + 5$的值"（$ $ 與中文直接相連）
   
   answer 格式：
      ✅ 正確："42"（純數字）
      ✅ 正確："\frac{3}{7}"（LaTeX 分數，不含 $ $）
      ❌ 錯誤："答案是 42"（不要加中文說明）

📐 題目字串拼接範例（3步驟標準流程）：
   # 步驟1: 先拼接數學式（不含 $ $）
   math_expr = f"{fmt_num(n1)} {op_latex['+']} {fmt_num(n2)}"
   
   # 步驟2: 組合中文與數學式（手動加 $ $）
   q = f"計算 ${math_expr}$ 的值"  # ⚠️ 使用簡短變量名 q
   
   # 步驟3: 最後呼叫 clean_latex_output()（可選，用於進階清洗）
   q = clean_latex_output(q)
   
   # 步驟4: 格式化答案為純數字字符串
   a = str(answer)  # ⚠️ 使用簡短變量名 a
   
   # ⚠️ 返回格式（必須完全遵守）：
   return {
       'question_text': q,
       'correct_answer': a,
       'answer': a,         # ⚠️ CRITICAL: 必須同時包含此鍵（與 correct_answer 值相同）
       'mode': 1
   }

❌ 常見錯誤（絕對不要這樣寫）：
   # 錯誤1: 在 f-string 內呼叫 clean_latex_output()
   q_str = f"計算 {clean_latex_output(expr)} 的值"  # ❌ 錯誤
   
   # 錯誤2: 字串拼接時用 + 運算符混合函式呼叫
   q_str = f"計算 {clean_latex_output(fmt_num(n1) + op_latex['*'] + fmt_num(n2))} 的值"  # ❌ 錯誤
   
   # 錯誤3: 只返回單一 answer 鍵
   return {'question_text': q, 'answer': a, 'mode': 1}  # ❌ 缺少 'correct_answer'
   
   # 錯誤4: 變量名過長
   question_text = "..."  # ❌ 應使用 q
   answer = "..."         # ❌ 應使用 a

📐 使用以下工具函數（已預先定義）：
   - fmt_num(x): 格式化數字（負數自動加括號）
   - op_latex: 運算符映射字典 {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
   - clean_latex_output(q_str): 自動清洗 LaTeX 格式（僅用於最後一步）

提示：你可以使用 Python 的 random, math, Fraction 等標準庫。
"""

# ==============================================================================
# 完整的 UNIVERSAL_GEN_CODE_PROMPT（針對 14B 模型優化的鷹架版）
# ==============================================================================

UNIVERSAL_GEN_CODE_PROMPT = r"""【角色】K12 數學演算法工程師

【任務】
實作 `def generate(level=1, **kwargs)` 函數，根據 MASTER_SPEC 生成數學問題的完整 Python 代碼。
該函數應返回 dict: {'question_text': str, 'correct_answer': str, 'answer': str, 'mode': 1}

【預載工具 API 手冊】(環境已實作，請直接調用，無需重新定義)

1. **基礎工具**
   - `fmt_num(n) -> str`: 格式化數字
   - `to_latex(n) -> str`: 轉 LaTeX 格式
   
2. **多項式專用工具**
   - `_coeffs_to_terms(coeffs: list) -> list[tuple]`: 係數轉 terms
   - `_differentiate_poly(terms, order=1) -> list[tuple]`: 求導
   - `_poly_to_latex(terms) -> str`: 生成題目用 LaTeX (不含 $)
   - `_poly_to_plain(terms) -> str`: 生成答案用純文字
   - `_deriv_symbol_latex(order) -> str`: 導數符號 (不含 $)

【核心規則】
1. ✅ shuffle + slice 避免無限迴圈
2. ✅ 數學式用 $ 包裹
3. ✅ 答案純結果，不含符號
4. ✅ Data Flow: coeffs -> terms -> 計算 -> plain text
5. ✅ 只輸出代碼

⚠️ **返回格式檢查**
• 必須返回字典 {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}
• correct_answer 必須是字串
• question_text 數學式必須用 $ 包裹
"""


class PromptBuilder:
    """
    Prompt 構建引擎 - 負責生成不同 Ablation 模式的 Prompt
    
    支援 3 種 Ablation 模式：
    - Ab1: BARE_MINIMAL_PROMPT (最簡 Prompt)
    - Ab2: UNIVERSAL_GEN_CODE_PROMPT + MASTER_SPEC
    - Ab3: UNIVERSAL_GEN_CODE_PROMPT + MASTER_SPEC (默認)
    """
    
    @staticmethod
    def build(master_spec: str, ablation_id: int = 3, textbook_example: str = "", topic: str = "", skill_id: str = "") -> str:
        """
        構建 Prompt（[V47.13] 新增 Domain 函數庫自動注入）
        
        Args:
            master_spec: MASTER_SPEC 字串
            ablation_id: Ablation 模式 ID (1, 2, 3)
            textbook_example: [Ab1 專用] 教科書範例文字
            topic: [Ab1 專用] 題目主題（從 skill_id 提取）
            skill_id: [V47.13 新增] 用於自動識別所需 Domain 函數庫
            
        Returns:
            str: 完整的 Prompt（已自動注入 Domain 標準函數）
        """
        # [V47.13] 自動識別並注入 Domain 函數庫
        domain_injection = ""
        if skill_id:
            try:
                from core.prompts.domain_function_library import get_required_domains, get_domain_helpers_code
                required_domains = get_required_domains(skill_id)
                if required_domains:
                    domain_code = get_domain_helpers_code(required_domains)
                    domain_injection = f"""

### 🔧 標準函數庫（{', '.join(required_domains)}）

{domain_code}

⚠️ 規則：
1. 直接調用上述函數，禁止重新定義
2. 你只需實現 `def generate(level=1, **kwargs)`
3. 答案格式：純多項式逗號分隔，例 "6x-5, 6"（禁止包含 f'(x)= 或換行）
"""
                    logger.info(f"   ✅ Domain 函數庫注入: {required_domains}")
            except Exception as e:
                logger.warning(f"   ⚠️ Domain 函數庫注入失敗: {e}")
        
        if ablation_id == 1:
            # Ab1: 模擬一般用戶的 Prompt + 範例 + 主題
            # 如果沒有提供範例，使用預設範例
            if not textbook_example:
                textbook_example = "範例：計算 3 + 5 = ?"
            if not topic:
                topic = "數學題目"
            
            prompt = BARE_PROMPT_TEMPLATE.format(
                topic=topic,
                textbook_example=textbook_example
            )
            logger.info(f"Prompt Ab1 - BARE_PROMPT_TEMPLATE (自然語言)")
            logger.info(f"   Topic: {topic}")
            logger.info(f"   Bare Prompt: {len(BARE_PROMPT_TEMPLATE)} chars")
            logger.info(f"   Textbook Example: {len(textbook_example)} chars")
            logger.info(f"   Final Prompt: {len(prompt)} chars")
        elif ablation_id == 2:
            # Ab2: UNIVERSAL Prompt + MASTER_SPEC + Domain 函數庫
            # ✅ [V47.14 淨化 MASTER_SPEC] 移除會誤導 14B 模型的實作步驟
            clean_spec = PromptBuilder._clean_master_spec(master_spec)
            prompt = UNIVERSAL_GEN_CODE_PROMPT + domain_injection + f"\n\n### MASTER_SPEC:\n{clean_spec}"
            logger.info(f"Prompt Ab2 - UNIVERSAL_GEN_CODE_PROMPT + MASTER_SPEC + Domain")
            logger.info(f"   Universal Prompt: {len(UNIVERSAL_GEN_CODE_PROMPT)} chars")
            logger.info(f"   Domain Injection: {len(domain_injection)} chars")
            logger.info(f"   MASTER_SPEC (淨化前): {len(master_spec)} chars")
            logger.info(f"   MASTER_SPEC (淨化後): {len(clean_spec)} chars")
        else:
            # Ab3 (默認): UNIVERSAL Prompt + MASTER_SPEC + Domain 函數庫
            # ✅ [V47.14 淨化 MASTER_SPEC] 移除會誤導模型的實作步驟
            clean_spec = PromptBuilder._clean_master_spec(master_spec)
            prompt = UNIVERSAL_GEN_CODE_PROMPT + domain_injection + f"\n\n### MASTER_SPEC:\n{clean_spec}"
            logger.info(f"Prompt Ab{ablation_id} - UNIVERSAL_GEN_CODE_PROMPT + MASTER_SPEC + Domain")
            logger.info(f"   Universal Prompt: {len(UNIVERSAL_GEN_CODE_PROMPT)} chars")
            logger.info(f"   Domain Injection: {len(domain_injection)} chars")
            logger.info(f"   MASTER_SPEC (淨化前): {len(master_spec)} chars")
            logger.info(f"   MASTER_SPEC (淨化後): {len(clean_spec)} chars")
        
        return prompt
    
    @staticmethod
    def _clean_master_spec(master_spec: str) -> str:
        """
        [V47.14] MASTER_SPEC 淨化器 - 移除會誤導 14B 模型的實作細節
        
        核心邏輯：
        - 保留「做什麼」(entities, constraints, operators, templates.complexity_requirements)
        - 移除「怎麼做」(construction, implementation_checklist, formatting, variables)
        
        原因：14B 模型看到 construction 後會照抄步驟，反而不使用我們提供的 API 工具。
        
        Args:
            master_spec: 原始 MASTER_SPEC 字串
            
        Returns:
            str: 淨化後的 MASTER_SPEC
        """
        try:
            import yaml
            spec_dict = yaml.safe_load(master_spec)
            
            # 移除會誤導模型的「實作指引」
            keys_to_remove = ['construction', 'implementation_checklist', 'formatting', 'variables']
            
            # 保留 templates 裡的 name 和 complexity_requirements，但移除內部的實作細節
            if 'templates' in spec_dict:
                for template in spec_dict['templates']:
                    for key in keys_to_remove:
                        if key in template:
                            del template[key]
                            
            # 重新轉回字串
            clean_spec = yaml.dump(spec_dict, allow_unicode=True, sort_keys=False)
            logger.info(f"   ✅ MASTER_SPEC 淨化完成: 移除 {keys_to_remove}")
            return clean_spec
            
        except Exception as e:
            # 如果解析失敗，回退到原始 MASTER_SPEC
            logger.warning(f"   ⚠️ MASTER_SPEC 淨化失敗: {e}，使用原始版本")
            return master_spec
    
    @staticmethod
    def get_skeleton() -> str:
        """
        獲取代碼框架（用於向後兼容）
        
        Returns:
            str: 空字串（CALCULATION_SKELETON 已棄用）
        """
        return ""


# 導出常量（向後兼容）
__all__ = [
    'PromptBuilder',
    'BARE_MINIMAL_PROMPT',
    'UNIVERSAL_GEN_CODE_PROMPT',
]
