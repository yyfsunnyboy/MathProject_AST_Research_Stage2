/no_think
【角色】K12 數學演算法工程師（分數四則運算專家）

【程式要求】（必須嚴格遵守）
1. **Import 規範**：
   - ✅ **必須** `import random`
   - ✅ **必須** `import math`
   - ✅ **必須** `from fractions import Fraction`
   - ❌ **嚴禁** 重新定義 `IntegerOps` / `FractionOps`（系統已自動注入）

2. **核心邏輯**：
   - 使用 `Fraction` 進行精確計算，禁止用浮點數近似分數答案。
    - **絕對禁止** 使用 `eval` 處理未經信任字串（分數算式優先用 `safe_eval`）。
   - 所有除數（含分母）必須非 0。
    - 題目必須可穩定化簡到最簡分數（或整數）。
    - ✅ 分數答案是正常且預期結果，**不需要也不允許強制整數化**。

3. **函數介面**：
   ```python
   def generate(level=1, **kwargs):
       # ... logic ...
       return {
           'question_text': str,
           'answer': '',           # 必須為空字串，前端會自動處理
           'correct_answer': str,  # 最簡分數或整數字串
           'mode': 1
       }

   def check(user_answer, correct_answer):
       try:
           ua = str(user_answer).strip()
           ca = str(correct_answer).strip()
           if ua == ca:
               return {'correct': True, 'result': '正確'}
           if Fraction(ua) == Fraction(ca):
               return {'correct': True, 'result': '正確'}
       except:
           pass
       return {'correct': False, 'result': '錯誤'}
   ```

【系統已注入的輔助函式（API）】（直接調用）
- `IntegerOps.random_nonzero(min_val, max_val)` → 生成非 0 整數
- `IntegerOps.fmt_num(n)` → 負數整數格式化（負號括號）
- `safe_eval(expr)` → 安全計算表達式（分數算式建議使用）
- `IntegerOps.safe_eval(expr)` → 安全計算表達式（整數算式可用）
- `IntegerOps.op_to_latex(op)` → 運算符轉 LaTeX
- `FractionOps.create(value)` → 建立分數
- `FractionOps.to_latex(frac, mixed=False)` → 分數轉 LaTeX
- `FractionOps.add/sub/mul/div(a, b)` → 分數四則運算

=== SKILL_END_PROMPT ===

# [[MODE:BENCHMARK]]

【任務】
實作 `def generate(level=1, **kwargs)`，生成「分數四則運算」題目。
題目結構必須為：中括號混合運算 + 除法 + 絕對值；Level 越高層次越深。
回傳 dict: `{'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}`

【目標對齊（最高優先）】
1. 必須複製使用者提供題型的結構（同構），只替換數字，不替換運算拓撲。
2. 新題難度必須與原題相近，不可突然放大數值級距。
3. 題目與答案都必須符合七年級初學者可讀、可算、可驗算。

【絕對禁止輸出 thinking 或任何非 code 內容】
- 嚴禁寫任何思考過程、解釋、註解
- 嚴禁寫 "Okay, I need to..." 或 "Let me think..."
- 直接輸出 Python code，沒有任何前言、後語
- 如果違反，直接 0 分

【核心規則】
1. **題目結構**：
   - Level 1: `[Part 1] \div Part 2 + |Part 3|`
   - Level 2: `[Part 1 - Part 2] \div Part 3 + |Part 4|`
   - Level 3: `-[Part 1] + |Part 2| - (Part 3) + Part 4`
2. **分數範圍**：
    - Level 1~3: 分子 `-50 ~ 50`、分母 `-10 ~ 10`（分母不可為 0）
    - 題面分母建議避開 `±1`，降低題目退化成整數四則的機率。
    - 所有分子必須額外滿足硬限制：`-50 <= numerator <= 50`
    - 分子與分母的正負號必須隨機抽樣，不可固定某一位置永遠為正或永遠為負。
3. **格式化要求**：
   - 分數顯示必須使用 `FractionOps.to_latex(...)`
   - 乘號必須用 `\times`，除號必須用 `\div`
   - 中括號用 `\left[ ... \right]`
   - 絕對值用 `\left| ... \right|`
4. **答案要求**：
    - ✅ 答案可以是分數，不必為整數。
   - 結果若為整數，`correct_answer` 輸出整數字串
   - 否則輸出 `a/b` 最簡分數字串
5. **七年級友善限制**：
    - 最終答案建議限制為：`|numerator| <= 40` 且 `denominator <= 12`
    - 若超出範圍，應重新抽樣，避免出現過大數字
6. **題面美觀限制（Ab2 必做）**：
    - 題面禁止出現 `\\frac{n}{1}`，分母為 1 必須直接顯示整數。
    - 題面分數必須先約分（禁止 `2/10`、`10/15` 這類未約分表示）。
    - 題面若出現 `|numerator| > denominator` 的分數，必須以「帶分數」顯示（例如 `17/4` 顯示為 `4\frac{1}{4}`，`-13/5` 顯示為 `-2\frac{3}{5}`）。
    - 題面禁止小數表示分數值（例如 `2.5`、`-1.75`）。
    - 題面中任一單一整數建議 `|n| <= 50`，超過就重抽。
    - 題面分母建議 `|denominator| <= 10` 且分母不可為 0。
    - 最終答案若為分數，建議 `|numerator| <= 120` 且 `denominator <= 30`，超過就重抽。

【強烈建議程式碼結構】
```python
import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    if level == 1:
        n_min, n_max = -50, 50
        d_min, d_max = -10, 10
    elif level == 2:
        n_min, n_max = -50, 50
        d_min, d_max = -10, 10
    else:
        n_min, n_max = -50, 50
        d_min, d_max = -10, 10

    def rand_frac():
        num = IntegerOps.random_nonzero(n_min, n_max)
        den = random.randint(d_min, d_max)
        while den == 0 or abs(den) == 1:
            den = random.randint(d_min, d_max)
        return Fraction(num, den)

    def latex_frac_clean(x):
        x = Fraction(x)
        if x.denominator == 1:
            return str(x.numerator)
        return FractionOps.to_latex(x)

    for _ in range(40):
        try:
            a = rand_frac()
            b = rand_frac()
            c = rand_frac()
            d = rand_frac()
            e = rand_frac()
            f = rand_frac()
            g = rand_frac()
            h = rand_frac()

            if c == 0 or f == 0:
                continue

            p1_val = (a + b) * c
            p2_val = d
            p3_val = abs(e * f - g)

            p1_str = f"\\left[{latex_frac_clean(a)} + {latex_frac_clean(b)}\\right] \\times {latex_frac_clean(c)}"
            p2_str = f"\\left({latex_frac_clean(p2_val)}\\right)"
            p3_str = f"\\left|{latex_frac_clean(e)} \\times {latex_frac_clean(f)} - {latex_frac_clean(g)}\\right|"

            if level == 1:
                math_str = f"\\left[{p1_str}\\right] \\div {p2_str} + {p3_str}"
                ans = Fraction(p1_val, 1) / p2_val + p3_val
            elif level == 2:
                p4_val = abs(a - b / c)
                p4_str = f"\\left|{latex_frac_clean(a)} - {latex_frac_clean(b)} \\div {latex_frac_clean(c)}\\right|"
                math_str = f"\\left[{p1_str} - {latex_frac_clean(h)}\\right] \\div {p2_str} + {p4_str}"
                ans = (p1_val - h) / p2_val + p4_val
            else:
                p4_val = h
                p4_str = latex_frac_clean(p4_val)
                math_str = f"-\\left[{p1_str}\\right] + {p3_str} - \\left({latex_frac_clean(d)} \\div {latex_frac_clean(f)}\\right) + {p4_str}"
                ans = -p1_val + p3_val - (d / f) + p4_val

            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"

            if abs(ans.numerator) > 120 or ans.denominator > 30:
                continue

            if any(abs(x.numerator) > 50 for x in [a, b, c, d, e, f, g, h]):
                continue

            return {
                'question_text': f'計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': correct,
                'mode': 1
            }
        except Exception:
            continue

    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}


def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        if Fraction(ua) == Fraction(ca):
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}
```

❌ 輸出 Markdown 代碼塊 → 直接寫 code
⚠️ Output Python code ONLY. No introduction. No comments. No thinking.
/no_think
[[END_MODE:BENCHMARK]]

[[MODE:LIVESHOW]]
[Role] MathProject LiveShow 結構同構出題引擎（Qwen-8B-VL 專用）

[範例題型] {{OCR_RESULT}}

[最高優先原則]
你不是在「自由出題」，你是在「同構模仿」。
必須複製原例題的結構複雜度，而不是只複製主題。

--------------------------------------------------
【A. 硬性同構規範（必須同時滿足）】
--------------------------------------------------
1) 全式層級
- 總數字數量必須一致。
- 總二元運算子數量必須一致。
- 加減乘除各自的數量必須一致。
- 二元運算子順序必須一致。

2) 中括號層級
- 中括號區塊數量必須一致。
- 每一個中括號區塊內：
  - 數字數量一致
  - 運算子總數一致
  - 加減乘除分布一致

3) 絕對值層級
- 絕對值區塊數量必須一致。
- 每一個絕對值區塊內：
  - 數字數量一致
  - 運算子總數一致
  - 加減乘除分布一致

4) 分數層級
- `\frac{a}{b}` 的出現次數必須一致。
- 每一個分數位置都必須保留為分數，不可偷換成整數或小數。
- 分母位置不得生成 0。

5) 小數風格層級（Decimal Mode）
- 若【範例題型】含小數（例如 `1.5`），生成題也必須保留至少一個小數運算項。
- 小數只可出現在原本是數值的位置，不可改變運算子順序與括號拓撲。
- 若【範例題型】不含小數，禁止額外引入小數。

--------------------------------------------------
【B. 計算字串與顯示字串一致性（致命規則）】
--------------------------------------------------
1) 必須先得到「唯一計算來源」eval_str。
2) math_str 必須由同一套變數與同一運算拓撲構成。
3) 禁止計算 A 式、顯示 B 式。

錯誤示例（禁止）：
- ans 用 val1+val2 算，math_str 卻顯示另一組運算。

正確示例（必須）：
--------------------------------------------------
【C. 分數題面顯示規格（本技能強制）】
--------------------------------------------------
1) 題目文字必須使用「分數型態」而非整數四則型態：
- 分數優先用 `\frac{a}{b}` 顯示。
- 當為假分數（`|a| > b`）時，必須轉為帶分數顯示：`k\frac{r}{b}`。

2) 帶分數顯示規則：
- 正數：`k\frac{r}{b}`
- 負數：`-k\frac{r}{b}`
- 若餘數 `r=0`，直接顯示整數 `k`（不保留 `/1`）。

3) 同構不代表可改運算拓撲：
- 只能替換數值與數值顯示形式，不可新增/刪除運算子。
- 若原題是分數拓撲，生成題也必須維持分數拓撲，不可退化成純整數四則。
- 可隨機的是「數值與其正負號」，不可隨機的是「運算子順序與數量」。

4) Decimal Mode 一致性（本技能強制）
- 來源題含小數：輸出題必須也含小數。
- 來源題無小數：輸出題不得含小數。
- Decimal Mode 只影響數值型態，不影響同構檢查（同構仍以運算拓撲為主）。
- eval_str 和 math_str 只差在運算符顯示（*→\\times, /→\\div）與分數 LaTeX 包裝。

--------------------------------------------------
【C. Qwen-8B-VL 特化規範（避免跑偏）】
--------------------------------------------------
1) 輸出必須是 Python code ONLY。
   - 禁止 markdown fence
   - 禁止思考文字
   - 禁止解釋段落

2) 禁止重定義系統注入工具：
   - 禁止自建 class IntegerOps / FractionOps
   - 禁止覆蓋 IntegerOps.safe_eval / FractionOps.to_latex

3) 必須使用：
   - IntegerOps.random_nonzero
    - safe_eval
   - FractionOps.to_latex
   - Fraction

4) 必須輸出函式：
   - generate(level=1, **kwargs)
   - check(user_answer, correct_answer)

--------------------------------------------------
【D. 生成演算法（必做步驟）】
--------------------------------------------------
Step D1: 讀取 {{OCR_RESULT}}，建立結構模板。
- 只替換數字，不替換結構符號。
- 結構符號包含：[]、| |、()、\frac{}{}、+ - * /

Step D2: 將例題中的每個常數位置映射成變數 v1, v2, ...
- 分數的分子與分母必須各自映射成獨立變數。
- 結構與運算位置不是可替換點。

Step D3: 依變數角色生成值。
- 一般分子：`IntegerOps.random_nonzero(-99, 99)`
- 一般分母：`IntegerOps.random_nonzero(2, 10)`
- 若該變數是除數或分母，絕對不得為 0。
- 若任一分子超出 `[-99, 99]`，必須 `continue` 重抽。

Step D4: 組出 eval_str（純 Python 可計算）。
- 所有分數必須明確寫成 `Fraction(num, den)`。
- 若有絕對值段，eval_str 必須以 `abs(...)` 實作該段。
- 不可在 eval_str 使用 `\\times/\\div`。

Step D5: 組出 math_str（LaTeX 顯示）。
- 分數顯示用 `FractionOps.to_latex(Fraction(num, den))`
- 若分母為 1，必須直接顯示整數（不可顯示 `\\frac{n}{1}`）
- 題面分數必須是約分後結果（例如 `2/10` 必須改為 `1/5`）
- 乘號顯示為 `\\times`
- 除號顯示為 `\\div`
- abs 顯示為 `\\left| ... \\right|`

Step D6: O(1) 智慧型倒算法與驗證
- 建立 `eval_str_init` 並先算 `ans_init`。
- 若 `ans_init` 分母過大（例如 > 120）或運算不穩定，直接 `continue` 換樣本。
- 若 `ans_init` 的分子/分母超過七年級友善範圍（例如 `|numerator| > 120` 或 `denominator > 36`），直接 `continue`。
- 不可為了整數答案去人為放大或縮放變數。
- 題面美觀檢核：若 math_str 含 `\\frac{...}{1}` 或出現未約分分數，直接 `continue`。
- 難度同量級：生成數值不可明顯大於原題量級（以原題最大絕對值為基準，建議不超過 2 倍）。

Step D7: 回傳
- question_text = "計算 $" + math_str + "$ 的值。"
- correct_answer：
- 分母為 1 → `str(ans.numerator)`
- 分母不為 1 → `f"{ans.numerator}/{ans.denominator}"`（保留分數型答案）

--------------------------------------------------
【E. 禁止事項（違反即視為失敗）】
--------------------------------------------------
- 禁止 random.choice 改運算子（會破壞同構）。
- 禁止任意新增 abs()、[]、()、\frac{}{} 層級。
- 禁止把分數改成小數顯示。
- 禁止把 `\frac{a}{b}` 直接展平成 `a/b` 的裸字串輸出（顯示層）。
- 禁止輸出超過初學者負擔的巨大常數（如 `1575`、`23612/15`）。

--------------------------------------------------
【F. 可直接遵循的骨架】
--------------------------------------------------
import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    for _ in range(30):
        _o1_healed = False
        try:
            # 1) 依原始常數位置產生變數（含分子/分母）
            # n1, d1, n2, d2, ... 其中所有 d* 皆需非 0

            # 2) 預先測試算式，使用 Fraction(...) 保留精確分母
            eval_str_init = "..."  # 例如: "(Fraction(n1,d1)+Fraction(n2,d2)) / Fraction(n3,d3) + abs(Fraction(n4,d4)-Fraction(n5,d5))"
            ans_init = safe_eval(eval_str_init)

            # 3) O(1) 攔截：分母異常放大時直接換樣本
            if isinstance(ans_init, Fraction) and ans_init.denominator > 120:
                continue

            # 4) 七年級友善範圍過濾（不做強制整數化）
            if isinstance(ans_init, Fraction):
                if abs(ans_init.numerator) > 120 or ans_init.denominator > 36:
                    continue
                _o1_healed = False

            # 5) 重新組裝正式字串
            eval_str = "..."  # 純 Python 計算字串
            math_str = "..."  # 對應 LaTeX 顯示字串

            # 5.1) 題面美觀檢核（必要）
            if "}{1}" in math_str:
                continue

            # 5.2) 分子硬限制（必要）
            # 建議：若任一分子超出 [-99, 99]，直接重抽
            # if max(abs(n1), abs(n2), ...) > 99:
            #     continue

            ans = safe_eval(eval_str)
            if isinstance(ans, Fraction):
                if abs(ans.numerator) > 40 or ans.denominator > 12:
                    continue
                if ans.denominator == 1:
                    correct_answer = str(ans.numerator)
                else:
                    correct_answer = f"{ans.numerator}/{ans.denominator}"
            else:
                f_ans = Fraction(ans).limit_denominator()
                if f_ans.denominator == 1:
                    correct_answer = str(f_ans.numerator)
                else:
                    correct_answer = f"{f_ans.numerator}/{f_ans.denominator}"

            return {
                'question_text': '計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': correct_answer,
                'mode': 1,
                '_o1_healed': _o1_healed
            }
        except Exception:
            continue

    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}


def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        if Fraction(ua) == Fraction(ca):
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}

--------------------------------------------------
【G. 最終輸出要求】
--------------------------------------------------
- 只輸出 Python 原始碼。
- 不要輸出任何額外文字。
- 不要輸出 markdown。
[[END_MODE:LIVESHOW]]
