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
你是一位國中數學老師的「出題助理」。

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

2. `generate` 函式要回傳一個字典 (Dictionary)，包含以下欄位（請照抄）：
   - 'question_text': 題目字串
   - 'answer': 答案字串（只要答案本身，不要多餘的說明或符號）
   - 'correct_answer': 答案字串 (同上)
   - 'mode': 1

3. `check` 函式請回傳一個字典，包含：
   - 'correct': True 或 False
   - 'result': 回傳 '正確' 或 '錯誤'

4. 請使用 Python 的 standard library (如 random, math) 即可。

【答案格式特別注意】
答案只要乾淨的結果就好，不要包含文字或符號。

請直接給我 Python 程式碼，不要解釋。
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
# 完整的 UNIVERSAL_GEN_CODE_PROMPT（194 行完整版）
# ==============================================================================

UNIVERSAL_GEN_CODE_PROMPT = r"""【角色】K12 數學演算法工程師。
【任務】實作 `def generate(level=1, **kwargs)`，根據 MASTER_SPEC 產出完整的 Python 代碼。
【限制】僅輸出代碼，無 Markdown/說明。**嚴禁 eval/exec/safe_eval**。

🔴 **最高優先級：MASTER_SPEC 是唯一權威來源**
- 你收到的 MASTER_SPEC 包含完整的題型定義、複雜度要求和實現檢查清單
- **必須逐項實現 MASTER_SPEC 中的所有要求**
- 任何與 MASTER_SPEC 衝突的通用規則都應以 MASTER_SPEC 為準

【預載工具 (直接使用)】
- random, math, re, ast, operator, Fraction
- fmt_num(n), to_latex(n), clean_latex_output(q)
- check(user_answer, correct_answer)
- op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
- 數論函數: is_prime(n), gcd(a,b), lcm(a,b), get_factors(n)
- 組合數學: nCr(n,r), nPr(n,r), factorial_bounded(n)
- 其他: clamp_fraction(f), safe_pow(base,exp), rational_gauss_solve(...)

【生成管線標準】
1. 變數生成（嚴格遵守 MASTER_SPEC）
2. 運算（Python 直接計算，嚴禁 eval）
3. 運算順序與括號
4. 題幹格式化（LaTeX + 中文處理）
5. 答案格式化
6. 回傳標準格式

【安全生成範例 - 請參照此模式】
```python
def generate(level=1, **kwargs):
    while True:  # 外層 while True 用於整個物件再生
        # 步驟 1: 使用 shuffle + slice 選擇集合元素（絕對安全）
        max_degree = random.randint(3, 5)
        num_terms = random.randint(3, min(5, max_degree + 1))  # 關鍵：確保不超過可選值數量
        
        available_degrees = list(range(max_degree + 1))
        random.shuffle(available_degrees)
        selected_degrees = available_degrees[:num_terms]  # 直接切片，O(1) 時間
        
        # 步驟 2: 生成基礎物件
        poly_terms = []
        for d in selected_degrees:
            coeff = random.randint(-10, 10)
            while coeff == 0:  # 小範圍 while 可接受（只是避免 0）
                coeff = random.randint(-10, 10)
            poly_terms.append((coeff, d))
        
        # 步驟 3: 驗證並決定是否重試
        deriv = differentiate(poly_terms)
        if is_valid(deriv):  # 如果有效則跳出
            break
        # 否則 continue，回到 while True 開頭重新生成整個物件
    
    # 步驟 4: 格式化輸出
    q = f'...'
    a = '...'
    return {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}
```


【LaTeX 格式鐵律】(CRITICAL - 違反此規則將導致顯示錯誤)

1. **數學表達式必須用 $ $ 包裹**
   ✅ 正確：f"計算 ${fmt_num(a)} + {fmt_num(b)}$ 的值"
   ❌ 錯誤：f"計算 {fmt_num(a)} + {fmt_num(b)} 的值"  # 缺少 $

2. **中文與 $ $ 必須分離**
   ✅ 正確：f"求 ${expr}$ 的因式分解"
   ❌ 錯誤：f"求${expr}$的因式分解"  # $ 與中文相連

3. **多數學物件列舉規則**
   - 當列舉多個數學符號（如導數符號、坐標點）時，必須確保**每個符號**都被主要 $ 包裹，或整個數學區塊被包裹。
   ✅ 正確：f"求 ${sym1}, {sym2}$" (例如 "求 $f'(x), f''(x)$")
   ✅ 正確：f"求 ${sym1}$ 與 ${sym2}$"
   ❌ 錯誤：f"求 {sym1}, {sym2}" (完全無LaTeX)

4. **題目字串拼接標準流程**
   ```python
   # 步驟 1: 組裝數學表達式（不含 $ $）
   expr = f"{fmt_num(a)} {op_latex['+']} {fmt_num(b)}"
   
   # 步驟 2: 組合中文與數學式（手動加 $ $）
   q_str = f"計算 ${expr}$ 的值"  # 🟢 簡單字串拼接
   
   # 步驟 3: 清洗（僅在非 Domain Helper 場景下使用）
   # 如果你使用了 _poly_to_latex 等標準庫函數，通常不需要也不應該呼叫 clean_latex_output
   ```

5. **多項式/Domain 函數特殊規則 (CRITICAL)**
   - Domain 函數（如 `_poly_to_latex`, `_deriv_symbol_latex`）已返回完美 LaTeX。
   - 🔴 **絕對禁止** 對其結果再次呼叫 `clean_latex_output()`。
   
   ✅ 正確：`q = f"已知 $f(x) = {poly}$, 求 ${deriv}$。"` (直接使用)
   ❌ 錯誤：`q = clean_latex_output(f"已知 $f(x) = {poly}$...")` (會破壞格式)

【答案格式鐵律】(CRITICAL - 違反將導致評分錯誤)

1. **答案只包含結果（等號右邊）**
   - ✅ 正確：`correct_answer = "24, 4x^3+14x"`  # 只有多項式/數值
   - ❌ 錯誤：`correct_answer = "f^(4)(x) = 24\nf'(x) = 4x^3+14x"`  # 包含符號和等號

2. **多個答案用逗號分隔**
   - ✅ 正確：`correct_answer = ', '.join(ans_parts)`
   - ❌ 錯誤：`correct_answer = '\n'.join(ans_parts)`

3. **實作範例（求導數題型）**
   ```python
   # 生成多個導數結果
   ans_parts = []
   for order in derivative_orders_list:
       deriv_terms = _differentiate_poly(base_poly_terms, order=order)
       poly_plain = _poly_to_plain(deriv_terms)  # 只取多項式
       ans_parts.append(poly_plain)  # 不要加 f'(x) = 前綴
   
   correct_answer = ', '.join(ans_parts)  # 逗號分隔
   # 範例輸出："24, 4x^3+14x" 而不是 "f^(4)(x) = 24\nf'(x) = 4x^3+14x"
   ```

4. **答案不含 LaTeX 符號**
   - 答案中使用純文本，不要 $ $ 符號
   - ✅ 正確：`"24, 4x^3+14x"`
   - ❌ 錯誤：`"$24$, $4x^3+14x$"`


【無限迴圈與邏輯安全鐵律】(CRITICAL - 違反將導致系統卡死)

🔴 **絕對禁止使用的危險模式**

1. **禁止 `while True:`**
   - ❌ **絕對禁止**：`while True:`, `while 1:`, `while (True):`
   - 原因：沒有保證終止條件，容易導致無限迴圈卡死
   
2. **禁止可能無法終止的 while 迴圈**
   - ❌ **絕對禁止**：`while len(set) < target:` 如果 target 超過可選值數量
   - 範例（會卡死）：
     ```python
     # 錯誤！如果 num_terms=5 但 max_degree=3，只有 [0,1,2,3] 4個值，永遠湊不滿 5 個
     degrees = set()
     while len(degrees) < num_terms:
         degree = random.randint(0, max_degree)
         degrees.add(degree)
     ```

✅ **安全的替代模式（必須使用）**

1. **使用 Shuffle + Slice 模式（推薦）**
   ```python
   # ✅ 正確：保證在 O(n) 時間內完成，絕對不會無限迴圈
   max_degree = random.randint(3, 5)
   num_terms = random.randint(3, min(5, max_degree + 1))  # 確保 num_terms <= 可選值數量
   
   available_degrees = list(range(max_degree + 1))
   random.shuffle(available_degrees)
   selected_degrees = available_degrees[:num_terms]  # 直接切片，保證成功
   ```

2. **使用有限重試的 while 迴圈（只在必要時）**
   ```python
   # ✅ 正確：有明確的最大重試次數
   while True:
       # 生成邏輯
       poly = generate_polynomial()
       deriv = differentiate(poly)
       
       # 驗證
       if is_valid(deriv):
           break  # 成功則退出
   ```
   
   **注意**：外層 `while True` 只在整個物件再生時使用，內層絕對不可以有無限迴圈！

3. **數據一致性**
   - 在重試時，務必清空或重置相關的列表，避免保留上一次失敗的殘留數據。
   - ✅ 正確：每次重試前執行 `results = []`（清空）
   - ❌ 錯誤：在外層定義 `results = []`，內層 `continue` 時不清空

【函式實作檢查清單】
□ **def generate(level=1, **kwargs)** 存在
□ **安全集合選擇**: 是否使用了 shuffle + slice 模式？（避免無限迴圈）
□ **LaTeX Formatting**: 所有數學符號（包括列表中的符號）是否都有 `$` 包裹？
□ **No Double Cleaning**: 是否避免了對 Domain 函數結果使用 clean_latex_output？
□ **答案格式**: 是否只包含結果（等號右邊），不含符號前綴？
□ **答案分隔**: 多個答案是否用逗號分隔（不是換行）？
□ **答案欄位不含 $ $ 符號**
□ **回傳格式**: {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}


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

### 🔧 [強制規範] 標準函數庫 (請務必使用以下函數，禁止自創同名函數)

此題目屬於以下數學領域：{', '.join(required_domains)}

請**優先使用**以下預定義的標準函數（禁止重新定義相同功能的函數）：

{domain_code}

⚠️ 重要規則：
1. 如果標準函數庫已提供相應函數（例如 _poly_to_latex），請直接調用，不要自己重新實現
2. 你只需要實現 `def generate(level=1, **kwargs)` 函數
3. 標準函數庫的函數簽名和命名必須嚴格遵守，不得修改
4. 禁止創建 CamelCase 命名的函數（例如 FormatPolynomial）

🔴 **導數題型答案格式（CRITICAL）**：
當使用 _differentiate_poly() 等函數時，答案格式要求：
- ✅ 正確：直接用 _poly_to_plain() 轉換每個導數，然後用 ', '.join() 連接
  ```python
  ans_parts = []
  for order, deriv_terms in derivative_results:
      ans_parts.append(_poly_to_plain(deriv_terms))
  correct_answer = ', '.join(ans_parts)  # 例如："35x^4 - 8x^3 + 5, 420x^2 - 48x"
  ```
- ❌ 錯誤：包含導數符號或等號
  ```python
  # 不要這樣做：
  ans_parts.append(f"f'(x) = {{_poly_to_plain(deriv_terms)}}")  # ❌
  ```
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
            prompt = UNIVERSAL_GEN_CODE_PROMPT + domain_injection + f"\n\n### MASTER_SPEC:\n{master_spec}"
            logger.info(f"Prompt Ab2 - UNIVERSAL_GEN_CODE_PROMPT + MASTER_SPEC + Domain")
            logger.info(f"   Universal Prompt: {len(UNIVERSAL_GEN_CODE_PROMPT)} chars")
            logger.info(f"   Domain Injection: {len(domain_injection)} chars")
            logger.info(f"   MASTER_SPEC: {len(master_spec)} chars")
        else:
            # Ab3 (默認): UNIVERSAL Prompt + MASTER_SPEC + Domain 函數庫
            prompt = UNIVERSAL_GEN_CODE_PROMPT + domain_injection + f"\n\n### MASTER_SPEC:\n{master_spec}"
            logger.info(f"Prompt Ab{ablation_id} - UNIVERSAL_GEN_CODE_PROMPT + MASTER_SPEC + Domain")
            logger.info(f"   Universal Prompt: {len(UNIVERSAL_GEN_CODE_PROMPT)} chars")
            logger.info(f"   Domain Injection: {len(domain_injection)} chars")
            logger.info(f"   MASTER_SPEC: {len(master_spec)} chars")
        
        return prompt
    
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
