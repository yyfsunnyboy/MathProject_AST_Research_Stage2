# -*- coding: utf-8 -*-
# ==============================================================================
# ID: core/prompts/domain_library.py
# Description: 集中管理所有數學題型的模組設定與邏輯規範
# ==============================================================================

class DomainLibrary:
    # 所有題型共用的鐵律規範
    BASE_RULES = """
【絕對禁止輸出 thinking 或任何非 code 內容】
- 嚴禁寫任何思考過程、解釋、註解
- 直接輸出 Python code，沒有任何前言、後語
- 如果違反，直接 0 分

【⚠️ 通用資源鎖定與安全憲法】(絕對不可牴觸)
1. **禁止分支**：嚴禁寫出 `if level == ...` 或 `if mode == ...` 結構，只需一條主代碼路徑。
2. **禁止重構工具**：指定的工具模組 (`IntegerOps`, `FractionOps`, `PolyOps`, `RadicalOps`) 已經在執行環境中預載，你【嚴禁】自己重新定義這些 class，直接呼叫其 static methods 即可。
3. **安全運算**：嚴禁呼叫 `eval()`, `exec()`, 或 `safe_eval()`，所有計算皆須使用 Python 標準語法或指定模組。
4. **初始化防護**：函式第一行必須先定義 `question_text = ""` 以及 `correct_answer = ""`。
5. **回傳格式**：`generate(level=1, **kwargs)` 必須回傳字典 `{'question_text': question_text, 'correct_answer': correct_answer, 'answer': correct_answer, 'mode': 1}`。
"""

    DOMAINS = {
        "integer": {
            "role": "Python Math Builder (積木組裝工程師)",
            "tools": """
- 工具模組：`IntegerOps` (系統已注入，直接用 `IntegerOps.xxx`，嚴禁 import IntegerOps)
- API 規範：
  - `IntegerOps.fmt_num(n)`: 格式化數字 (負數自動加括號)
  - `IntegerOps.rand_nz(min, max)`: 隨機生成非零整數
""",
            "logic": """
【任務】
你不是數學家，你是 **「積木組裝員」**。
請根據 **[目標 DNA]** 的結構，將題目拆解為 2~3 個「運算積木 (Blocks)」，然後組裝起來。

【嚴格開發規範 (Violations = 0 Score)】
1.  **變數命名**：
    - ❌ **嚴禁** 使用 `a, b, c...z` 這種無意義名稱。
    - ✅ **必須** 使用 `term1, term2` (區塊運算結果) 或 `v1, v2` (數值)。
2.  **禁止變數爆炸**：
    - 嚴禁定義超過 6 個數值變數。如果題目很長，請分段計算。
3.  **除法補丁**：
    - 遇到 `/` 或 `\\div`，必須先生成 `divisor` 和 `quotient`，再反推 `dividend`。

【代碼骨架 (請嚴格模仿此結構，不要自創)】
(以下範例展示如何處理 "A * B - C / D" 結構，請依此類推)

```python
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    question_text = ""
    
    # [Block 1] 處理乘法部分 (對應 DNA 前段)
    v1 = random.randint(-10, 10)
    v2 = random.randint(2, 9)
    term1_val = v1 * v2
    
    # [Block 2] 處理除法部分 (對應 DNA 後段 - 需確保整除)
    divisor = random.choice([x for x in range(-9, 10) if x not in [0, 1, -1]])
    quotient = random.randint(-9, 9)
    dividend = divisor * quotient  # 反推被除數
    term2_val = quotient           # 除法結果就是商
    
    # [Block 3] 處理絕對值或其他 (若 DNA 有)
    # v3 = ...
    # term3_val = abs(v3)
    
    # [Main] 計算總結果
    final_res = term1_val - term2_val # 依 DNA 運算符調整 (+, -, *)
    
    # [Format] 格式化
    # 定義輔助排版函數 (把數值轉字串)
    def fmt(n):
        return f"({n})" if n < 0 else f"{n}"
        
    s1 = fmt(v1)
    s2 = fmt(v2)
    s_div = fmt(dividend)
    s_dvr = fmt(divisor)
    
    # [Assembly] 組裝題目字串 (LaTeX)
    # 結構: term1 - term2
    math_str = f"{s1} \\times {s2} - {s_div} \\div {s_dvr}"
    question_text = f"計算 $${math_str}$$ 的值。"
    
    # [Answer]
    correct_answer = str(final_res)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        return float(user_answer) == float(correct_answer)
    except:
        return user_answer.strip() == correct_answer.strip()
```
"""
        },
        "fraction": {
            "role": "中學有理數與分數題型專家",
            "tools": """
- 工具模組：`FractionOps` (基於 `fractions.Fraction`)
- API 規範：
  - `FractionOps.create(num, den)`: 建立分數並自動約分。
  - `FractionOps.add(a, b)`, `sub`, `mul`, `div`: 安全的分數四則運算 API。
  - `FractionOps.format_latex(frac)`: 輸出標準 LaTeX 格式 (包含 `\\frac{}{}`)。
""",
            "logic": """
- 邏輯導引：
  - 嚴禁使用 `float` 進行計算，所有數值操作必須依賴 `Fraction` 物件以保證精度。
  - 生成的答案必須是最簡分數。
  - 遇到分數除法時，確保除數不為 0。
"""
        },
        "polynomial": {
            "role": "中學多項式與代數運算專家",
            "tools": """
- 工具模組：`PolyOps`
- API 規範：
  - `PolyOps.add(p1, p2)`, `sub`, `mul`: 多項式運算。
  - `PolyOps.format_latex(poly)`: 自動將多項式轉換為 LaTeX 字串，處理升降冪與省略 1 的細節。
""",
            "logic": """
- 邏輯導引：
  - 多項式以係數列表或特定字典形式表示。
  - 題目中如果要求合併同類項，程式碼需實作產生未合併前字串的邏輯，但 `correct_answer` 必須是合併後的結果。
"""
        },
        "radical": {
            "role": "中學無理數與根號運算專家",
            "tools": """
- 工具模組：`RadicalOps`
- API 規範：
  - `RadicalOps.create(inner)`: 建立根號化簡結果。
  - `RadicalOps.format_latex(expr)`: 轉換根式為 LaTeX。
""",
            "logic": """
- 邏輯導引：
  - 根號內的數值必須為非負數。
  - 生成的結果必須為最簡根式 (即將完全平方數提取至根號外)。
"""
        }
    }

    @classmethod
    def get_domain_config(cls, domain_tag: str):
        default = cls.DOMAINS["integer"]
        return cls.DOMAINS.get(domain_tag.lower(), default)
