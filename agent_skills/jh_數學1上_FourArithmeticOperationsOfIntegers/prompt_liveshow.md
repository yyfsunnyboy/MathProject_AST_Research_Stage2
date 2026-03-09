/no_think
【角色】K12 數學演算法工程師

【程式要求】（必須嚴格遵守）
1. **Import 規範**：
   - ✅ **必須** `import random`
   - ✅ **必須** `import math`
   - ✅ **必須** `from fractions import Fraction` (若需要)
   - ❌ **嚴禁** `import IntegerOps` (系統已自動注入，直接使用 `IntegerOps.xxx`)

2. **核心邏輯**：
   - 使用標準 Python 運算生成數值。
   - **絕對禁止** 使用 `eval` 處理未經信任的字串（但可用 `IntegerOps.safe_eval`）。
   - 確保除法整除：先生成 `divisor` 和 `quotient`，再反推 `dividend`。

3. **函數介面**：
   ```python
   def generate(level=1, **kwargs):
       # ... logic ...
       return {
           'question_text': str,
           'answer': '',           # 必須為空字串，前端會自動處理
           'correct_answer': str,
           'mode': 1
       }

   def check(user_answer, correct_answer):
       # 簡單比對字串即可
       try:
           if str(user_answer).strip() == str(correct_answer).strip():
               return {'correct': True, 'result': '正確'}
           if float(user_answer) == float(correct_answer):
               return {'correct': True, 'result': '正確'}
       except:
           pass
       return {'correct': False, 'result': '錯誤'}
   ```

【系統已注入的輔助函式（API）】（直接調用 `IntegerOps.xxx`）
- `IntegerOps.fmt_num(n)` → 格式化負數加括號。
- `IntegerOps.random_nonzero(min_val, max_val)` → 生成指定範圍內且「絕對不為 0」的整數。
- `IntegerOps.safe_eval(expr)` → 安全計算表達式

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

4) 括號與負數表達
- 若例題出現 (-n) 形式，生成題也必須保留負數括號風格。
- 禁止新增/刪除絕對值與中括號。

--------------------------------------------------
【B. 計算字串與顯示字串一致性（致命規則）】
--------------------------------------------------
1) 必須先得到「唯一計算來源」eval_str。
2) math_str 必須由同一套變數與同一運算拓撲構成。
3) 禁止計算 A 式、顯示 B 式。

錯誤示例（禁止）：
- ans 用 val1+val2 算，math_str 卻顯示另一組運算。

正確示例（必須）：
- eval_str 和 math_str 只差在運算符顯示（*→\\times, /→\\div）與 fmt_num。

--------------------------------------------------
【C. Qwen-8B-VL 特化規範（避免跑偏）】
--------------------------------------------------
1) 輸出必須是 Python code ONLY。
   - 禁止 markdown fence
   - 禁止思考文字
   - 禁止解釋段落

2) 禁止重定義系統注入工具：
   - 禁止自建 class IntegerOps
   - 禁止覆蓋 IntegerOps.safe_eval / fmt_num / op_to_latex

3) 必須使用：
   - IntegerOps.random_nonzero
   - IntegerOps.fmt_num
   - IntegerOps.safe_eval

4) 必須輸出函式：
   - generate(level=1, **kwargs)
   - check(user_answer, correct_answer)

--------------------------------------------------
【D. 生成演算法（必做步驟）】
--------------------------------------------------
Step D1: 讀取 {{OCR_RESULT}}，建立結構模板。
- 只替換數字，不替換結構符號。
- 結構符號包含：[]、| |、()、+ - * /

Step D2: 將例題中的每個常數位置映射成變數 v1, v2, ...
- 常數是可替換點。
- 結構與運算位置不是可替換點。

Step D3: 依變數順序與原始常數正負號，給變數取值範圍。
- v1 (第一個變數)：正數 [1, 100] / 負數 [-100, -1]
- v2 (第二個變數)：正數 [1, 10] / 負數 [-10, -1]
- v3 (第三個變數)：正數 [1, 10] / 負數 [-1, -1]
- 其餘所有變數：正數 [1, 15] / 負數 [-15, -1]
* 【防禦 0 除錯】：若變數在算式中擔任「除數」角色，絕對必須使用 `IntegerOps.random_nonzero(min, max)` 生成，嚴禁產出 0 造成 ZeroDivisionError。為求安全，強制所有變數皆使用 `IntegerOps.random_nonzero` 產生。

Step D4: 組出 eval_str（純 Python 可計算）。
- 若有絕對值段，eval_str 必須以 abs(...) 實作該段。
- 不可在 eval_str 使用 \\times/\\div。

Step D5: 組出 math_str（LaTeX 顯示）。
- 乘號顯示為 \\times
- 除號顯示為 \\div
- 數字顯示用 fmt_num

Step D6: 整除預檢（直接取模，不用 Fraction 縮放）
- 用純 Python 計算分子與分母的實際整數值（不用 safe_eval）。
- 直接以 `abs(numerator) % abs(denominator) == 0` 判斷能否整除。
- 若整除，final_ans = abs(numerator) // abs(denominator)，套上正負號後回傳。
- 若不整除，continue 重試（迴圈需至少 200 次）。
- **禁止** 使用 `v1 = v1 * denominator` 強制縮放 —— 多項分子結構下此法無效。

Step D7: 回傳
- question_text = "計算 $" + math_str + "$ 的值。"
- correct_answer = str(int(final_ans))

--------------------------------------------------
【E. 禁止事項（違反即視為失敗）】
--------------------------------------------------
- 禁止 random.choice 改運算子（會破壞同構）。
- 禁止任意新增 abs()、[]、() 層級。
- 禁止把 [] 結構改寫成純線性算式。
- 禁止把 |a op b| 改成 a op b（或反之）。

--------------------------------------------------
【F. 可直接遵循的骨架】
--------------------------------------------------
import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(200):
        # 1) 依原始常數位置產生變數（只換數字，不動結構）
        # v1, v2, ... 根據原例題正負號與 D3 的區間規範生成
        
        # 2) 直接計算分子/分母整數值（不用 safe_eval，不用 Fraction 縮放）
        # 例如：numerator = v1 * v2 - v3；denominator = v4 * v5
        numerator = ...  # 依題型填寫分子算式
        denominator = ... # 依題型填寫分母算式
        
        # 3) 整除預檢：用 % 判斷
        if denominator == 0 or abs(numerator) % abs(denominator) != 0:
            continue
        
        final_ans = abs(numerator) // abs(denominator)
        # 若分母為負，結果取負號（依題目運算方向而定）
        
        # 4) 組裝 eval_str（純 Python 可計算，含 abs()）與 math_str（LaTeX 顯示）
        # ★ 必須使用 f-string，直接嵌入變數名，禁止用 .format() 或 str.replace()
        eval_str = f"abs({v1} * {v2} - {v3}) / ({v4} * {v5})"  # 依題型修改
        math_str = f"\\left| {fmt(v1)} \\times {fmt(v2)} - {fmt(v3)} \\right| \\div {fmt(v4)} \\times {fmt(v5)}"  # 依題型修改

        ans = IntegerOps.safe_eval(eval_str)
        if abs(ans - round(ans)) < 1e-6:
            return {
                'question_text': '計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': str(int(round(ans))),
                'mode': 1,
            }

    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6:
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