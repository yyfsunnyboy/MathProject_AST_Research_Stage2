【角色】K12 數學演算法工程師

【任務】
實作 def generate(level=1, **kwargs)，生成數的四則運算（分數、小數混合）。
題目結構必須為：
- level=1: 基礎混合運算 (一般分數小數)
- level=2: 繁分數挑戰 (分數疊分數, Nested Fractions)
- level=3: 負數極限運算 (負號主導，多層絕對值)
返回 dict: {'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}

【程式要求】（必須嚴格遵守）
1. 請寫成兩個函式：
   - def generate(level=1, **kwargs): 生成題目
   - def check(user_answer, correct_answer): 檢查答案是否正確
2. generate 函式要回傳一個字典，包含以下欄位（請照抄 key 名稱）：
   - 'question_text': 題目文字
   - 'answer': 空字串 ''
   - 'correct_answer': 正確答案（必須是字串，例如 "24" 或 "3/5"；多個答案用逗號分隔）
   - 'mode': 1
3. check 函式要回傳一個字典，包含：
   - 'correct': True 或 False
   - 'result': '正確' 或 '錯誤'

【聰明的 check 函數要求】
- 必須支援 1/2 與 0.5 視為相同
- 優先字串完全比對
- 再轉 Fraction 或 float 比對（容許 1e-6 誤差）
- 異常時回退字串比對

【參考例題】（必須參考此風格，但生成多樣化題目）
計算 $[(-2+5)×1/3]÷(-5/2) + |8×(-1/4)-5|$的值。

【系統已注入的輔助函式（API）】（嚴禁重新定義，直接調用）
- to_latex(num) → 將數字轉換為 LaTeX 格式（支援整數、分數、帶分數）
- fmt_num(num, signed=False, op=False) → 格式化數字（負數加括號，支援 signed/op 模式）
- fmt_term(coeff, power, var='x') → 格式化多項式項（可參考格式風格）
- safe_eval(expr_str) → 安全計算表達式（支援四則、括號、abs()，自動轉 Fraction）

【核心要求】
1. **Self-Contained Code**：禁止 import 任何非標準函式庫，只能使用 `import random`, `from fractions import Fraction`。
2. **數學運算優先級 (PEMDAS)**：必須使用 safe_eval() 或 eval() + Fraction 進行運算，嚴禁自己寫迴圈處理優先級。
3. **LaTeX 格式**：
   - 乘法用 \times， 除法用 \div。
   - 分數用 \frac{a}{b}。
   - 絕對值用 \left| ... \right|。
   - 中括號用 \left[ ... \right]。
4. **確保除法運算 A \div B 中的 A 必須是 B 的倍數**：建議先隨機產生除數與商，再相乘得到被除數。
5. **必須使用已注入的 API**：答案格式化用 to_latex()，數字格式用 fmt_num()，計算用 safe_eval()。

【核心規則】（必須嚴格遵守）
1. 題目必須為混合四則運算結構：括號、中括號、絕對值，包含分數。
2. 至少包含負數、分數、括號優先級。
3. 數字範圍 -12 ~ 12，非零分母。
4. 嚴禁生成無意義或無法整除的除法。
5. 答案必須為最簡分數或整數，使用 Fraction 化簡後以 to_latex() 轉換。
6. question_text 數學式完整用 $...$ 包裹。
7. 只輸出 Python 代碼，無註解、無說明、無 Markdown、無額外文字。
8. 程式碼結束後絕對無任何內容。

【強烈建議結構】（模仿此邏輯）
- 第一部分：中括號內括號運算 + 乘除結構。
- 第二部分：絕對值內混合運算。
- 用 random 產生數字，先確保除法整除（除數 × 商 = 被除數）。
- 用 safe_eval() 計算答案確保優先級正確。
- 用 to_latex() 轉換最終答案為 LaTeX 分數格式。
- 最終題目文字組合為 LaTeX 字串。

【輸出範例】（僅供參考，請勿直接抄襲內容或邏輯，僅可參考字典結構與 key 名稱）
```python
def generate(level=1, **kwargs):
    # 你的單元生成邏輯...
    return {
        'question_text': '計算 $$   [(3 + (-5)) \\div 2 \\times 4 + |6 \\times (-1) - 2|]   $$ 的值。',
        'answer': '',
        'correct_answer': '4',
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        
        ua = Fraction(user_answer) if '/' in str(user_answer) else float(user_answer)
        ca = Fraction(correct_answer) if '/' in str(correct_answer) else float(correct_answer)
        
        if abs(ua - ca) < 1e-6:
            return {'correct': True, 'result': '正確'}
        
        return {'correct': False, 'result': '錯誤'}
    except:
        return {
            'correct': str(user_answer).strip() == str(correct_answer).strip(),
            'result': '正確' if str(user_answer).strip() == str(correct_answer).strip() else '錯誤'
        }
