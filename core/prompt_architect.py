# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱 (Module Name): core/prompt_architect.py
功能說明 (Description): 
    V42.0 Architect (Pure Math Edition)
    專注於分析「純符號計算題」的數學結構，產出 MASTER_SPEC。
    此版本已移除圖形 (Geometry) 與情境 (Scenario) 的干擾，
    指導 Coder 生成精準的數論與運算邏輯。
    
版本資訊 (Version): V42.0
更新日期 (Date): 2026-01-21
維護團隊 (Maintainer): Math AI Project Team
=============================================================================
"""

import os
import json
import re
import time
from datetime import datetime
from flask import current_app
from models import db, SkillInfo, SkillGenCodePrompt, TextbookExample
from core.ai_wrapper import get_ai_client

# ==============================================================================
# V42.0 SYSTEM PROMPT (Pure Symbolic Math)
# ==============================================================================
ARCHITECT_SYSTEM_PROMPT = r"""【角色】K12 數學架構師 (DNA 解析專家)

【任務】
分析輸入算式，產出 JSON 格式的 MASTER_SPEC。你的目標是將數學邏輯「降維」成極簡的 Python 實作步驟，讓後端 Coder (Qwen) 只需要執行，不需要思考。

【支援技能清單】
- jh_數學1上_FourArithmeticOperationsOfIntegers (整數四則：若算式只包含整數、絕對值，請優先選此)
- jh_數學1上_FourArithmeticOperationsOfNumbers (分數四則：只有當算式中明確出現分數 Fraction 或小數時才選此)
- jh_數學2上_FourArithmeticOperationsOfPolynomial (多項式四則：出現未知數 x)
- jh_數學2上_RadicalOperations (根號運算：出現 \\sqrt 等根式)

【MASTER_SPEC 產出規範】
{
  "ocr_result": "LaTeX 格式的原始算式",
  "skill_name": "匹配的資料夾全名",
  "logic_recipe": [
    "Step 1 (變數): 定義 v1, v2, v3, v4, v5 (最多 5 個變數，必須是原始數字，確保除法整除)。絕對值盡量分佈在 5 到 25 之間。",
    "Step 2 (計算): 先計算 raw_val = (v1 + v2) * v3... (運算必須使用「原始未格式化的變數」進行，嚴禁拿轉成字串之後的變數去計算。確保最終答案絕對值 > 1)。",
    "Step 3 (渲染): 指定 question_text = f\"計算 $${f(v1)}...$$\" (使用 [DOMAIN_API] 中定義的格式化函式進行渲染)。"
  ],
  "variable_plan": "Python 偽代碼 (例如: f1=Fraction(r1, r2); res=f1*f2)",
  "latex_template": "帶有 {v1} 槽位的 LaTeX 字串，注意反斜線須雙寫 (\\\\frac)"
}

【MASTER_SPEC 生成憲法】
- 變數限額：嚴禁定義超過 5 個隨機變數（v1~v5）。
- 結構抽象化：如果 DNA 算式很長，請將其抽象化為『(v1 + v2) * v3 - v4』的簡潔結構。
- 明確賦值：必須明確寫出每個變數的生成範圍（例如：v1 = rand_nz(-10, 10)）。
- 型別防禦：若屬於「分數四則」，所有的變數必須初始化為 Fraction 物件 (例如 `v1 = Fraction(1, 2)`)，嚴禁讓純整數直接相除產生 float。

【MASTER_SPEC 流程規範】
- 必須先寫『Step 1: 計算 raw_ans』。
- 再寫『Step 2: 嚴格使用 [DOMAIN_API] 提供的工具進行最後的 question_text 渲染』。
- 嚴禁讓 Coder 自行決定計算邏輯。

【指令要求】
5. **嚴格模仿**：生成的 `logic_recipe` 必須 100% 複製原題的運算結構（但若超過變數限額，優先服從【結構抽象化】簡化結構）。
6. **嚴禁重複與過度複雜**：請嚴格遵守上述憲法與流程規範，確保邏輯可執行。
7. **【計算與排版分離】（防錯補丁）**：
   - 函式內必須分為兩個明確區域：
     - **計算區**：所有的 `+`, `-`, `*`, `//`, `abs()` 運算必須使用「原始純數字變數」。
     - **排版區**：僅在最後組裝 `question_text` 時，才對變數呼叫 `fmt_num` 或 `format_latex`。
   - **嚴禁行為**：嚴禁將格式化後的變數（字串）重新賦值給原始變數名。
8. **消除雜訊**：不要提及 Level 1/2/3，只針對「這一題」進行解析。
"""
# ==============================================================================
# AUXILIARY FUNCTION DESIGN GUIDELINES
# ==============================================================================
AUXILIARY_FUNCTION_PROMPT = r"""你是 K12 數學教案設計專家。

當設計「輔助函數」章節時，請注意：

1. **系統已預載工具**：
   - `fmt_num(num)`: 格式化數字為 LaTeX（自動處理括號，**不含外層 $**）
   - `to_latex(num)`: 轉換分數為 LaTeX（**不含外層 $**）
   - `clean_latex_output(q_str)`: 清洗題目字串並在最外層**自動加一對 $ 符號**（你不要再自己加）
   - `Fraction(num, den)`: Python 內建分數類別；小數請用 `Fraction(str(decimal_value))` 避免浮點誤差
   - `random.randint()`, `random.choice()`: 隨機數生成
   - `check()`: 驗證答案的數論工具
   - `op_latex`: **全域已定義的運算子映射表** `{'+': '+', '-': '-', '*': '\\times', '/': '\\div'}`
     - ✅ 直接使用: `f"{fmt_num(n1)} {op_latex[op]} {fmt_num(n2)}"`
     - ❌ **嚴禁重新定義**: 不要在 generate() 內部再寫 `op_latex = {...}`

2. **嚴禁事項 [V47 強制規定]**：
   - ❌ **嚴禁 eval/exec/safe_eval/字串算式**：所有數學結果必須用 Python 直接計算（`+`, `-`, `*`, `/`），不要建構字符串表達式再評估
     - ❌ 錯誤: `result = safe_eval(f'{a} + {b}')`
     - ✅ 正確: `result = a + b`
   - ❌ **嚴禁 import 任何模組**：預載工具已包含所有必要依賴（random, Fraction 等）
   - ❌ **嚴禁重新定義系統工具**：不可重新定義或覆蓋 `fmt_num`, `to_latex`, `clean_latex_output`, `check` 等

3. **輔助函數設計原則**：
   - ✅ 可以設計**領域專用**的輔助函數（例如 `_generate_chain_operation()`，用 `_` 前綴表示私有）
   - ❌ 不要重新設計格式化函式（例如 `ToLaTeX`, `FormatNumber`）
   - ❌ 不要重新設計隨機數生成器（例如 `GenerateInteger`）

4. **正確寫法範例**：
   ```
   **輔助函數**:
   - `_build_expression(terms, ops)`: 組合多項式表達式
   - `_validate_result(value)`: 檢查結果是否符合範圍
   
   **使用系統工具**:
   - 格式化數字：直接使用 `fmt_num(value)`
   - 生成隨機整數：直接使用 `random.randint(a, b)`
   - 生成分數：直接使用 `Fraction(num, den)`
   - 小數轉分數：使用 `Fraction(str(0.5))` 而非 `Fraction(0.5)`
   - 清洗題目字串：使用 `q = clean_latex_output(q)` **僅呼叫一次**
   ```

5. **錯誤示範（禁止）**：
   ```
   ❌ `ToLaTeX(value)`: 將數字轉為 LaTeX（這會誘導 AI 自己實作）
   ❌ `GenerateInteger(range)`: 生成隨機整數（應直接用 random.randint）
   ❌ `FormatFraction(num, den)`: 格式化分數（應直接用 to_latex(Fraction(num, den))）
   ❌ `calc_str = "1/2 + 3/4"; result = eval(calc_str)`: 字串評估（禁止！應直接用 Fraction(1,2) + Fraction(3,4)）
   ❌ `q = clean_latex_output(q); q = clean_latex_output(q)`: 重複呼叫（僅需一次）
   ```
"""

# ==============================================================================
# Core Generation Logic
# ==============================================================================

def generate_v15_spec(skill_id, model_tag="local_14b", architect_model=None):
    """
    [V42.0 Spec Generator]
    讀取例題 -> 呼叫 AI 架構師 -> 存入資料庫 (MASTER_SPEC)
    """
    try:
        # 1. 抓取 1 個範例 (避免過多 Context 干擾)
        skill = SkillInfo.query.filter_by(skill_id=skill_id).first()
        example = TextbookExample.query.filter_by(skill_id=skill_id).limit(1).first()
        
        if not example:
            return {'success': False, 'message': "No example found for this skill."}

        # 簡單清理例題文字，移除不必要的 HTML 或雜訊
        problem_clean = example.problem_text.strip()
        solution_clean = example.detailed_solution.strip()
        example_text = f"Question: {problem_clean}\nSolution: {solution_clean}"

        # 2. 構建 User Prompt
        user_prompt = f"""
當前技能 ID: {skill_id}
技能名稱: {skill.skill_ch_name}

參考例題：
{example_text}

任務：
請根據上述例題，撰寫一份 MASTER_SPEC，指導工程師生成同類型的「純計算題」。
重點：確保數值隨機但邏輯嚴謹（如整除、正負號處理）。
"""
        
        full_prompt = ARCHITECT_SYSTEM_PROMPT + "\n\n" + user_prompt

        # 3. 呼叫架構師 
        # (這裡建議使用邏輯能力較強的模型，如 Gemini Pro 或 Flash)
        client = get_ai_client(role='architect') 
        response = client.generate_content(full_prompt)
        spec_content = response.text

        # 4. 存檔 (永遠覆蓋 MASTER_SPEC，確保 Coder 讀到最新指令)
        new_prompt_entry = SkillGenCodePrompt(
            skill_id=skill_id,
            prompt_content=spec_content,
            prompt_type="MASTER_SPEC",
            system_prompt=ARCHITECT_SYSTEM_PROMPT, 
            user_prompt_template=user_prompt,
            model_tag=model_tag,
            created_at=datetime.now()
        )
        db.session.add(new_prompt_entry)
        db.session.commit()

        # [旺宏科學獎] 回傳 prompt_id 供實驗記錄使用
        return {'success': True, 'spec': spec_content, 'prompt_id': new_prompt_entry.id}

    except Exception as e:
        print(f"❌ Architect Error: {str(e)}")
        # 回傳錯誤訊息但不中斷程式，讓上層處理
        return {'success': False, 'message': str(e)}

def infer_model_tag(model_name):
    """
    [Legacy Support] 根據模型名稱自動判斷分級。
    """
    name = model_name.lower()
    if any(x in name for x in ['gemini', 'gpt', 'claude']): return 'cloud_pro'
    if '70b' in name or '32b' in name or '14b' in name: return 'local_14b'
    if 'phi' in name or '7b' in name or '8b' in name: return 'edge_7b'
    return 'local_14b'

# Alias for backward compatibility
generate_v9_spec = generate_v15_spec