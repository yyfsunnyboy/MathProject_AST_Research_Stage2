【角色】K12 數學演算法工程師

【任務】
實作 def generate(level=1, **kwargs)，生成整數四則運算題目。
題目結構必須為：
- level=1: 基礎四則運算 (3-4項，數值範圍 -20~20)
- level=2: 進階運算 (5-8項，包含多層括號，數值範圍 -100~100)
- level=3: 挑戰運算 (包含大數運算，數值範圍 -10000~10000，或極端零值測試)
返回 dict: {'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}

【輸出規範】(非常重要，請嚴格遵守)
1.  **禁止廢話**：不要輸出 "好的"、"Sure"、"Here is..."、"讓我思考一下" 等任何對話內容。
2.  **直接代碼**：直接開始寫 `import ...` 或 `def generate...`。
3.  **純淨代碼**：不要包含 Markdown 代碼塊標記 (```python)，直接輸出純文本代碼。
4.  **禁止中文註釋**：代碼中的註解請使用英文，或完全不寫註解 (No Chinese Comments)。

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

【參考例題與風格】（必須參考此風格，但生成多樣化題目）
範例：計算 $[(-20) + (-10)] \div (-5) \times 3 + |8 \times (-2) - 5|$ 的值。

【要求】
1. 乘法用 \times (×)，除法用 \div (÷)。
2. 絕對值必須使用 \left| ... \right|。
3. LaTeX 語法嚴格：$ 符號只能出現在最外層。
4. 確保除法運算 A \div B 中的 A 必須是 B 的倍數，建議先隨機產生除數與商，再相乘得到被除數。

【核心規則】（必須嚴格遵守）
1. 題目必須為括號內混合運算 + 絕對值結構
2. 包含 +, -, \times, \div 運算符，至少有負數
3. 數字範圍 -100 ~ 100，非零
4. 嚴禁使用 build_polynomial_text 或任何非標準工具
5. 嚴禁自己 import 任何模組（系統已注入必要工具）
6. 答案為整數或簡單分數，計算使用 eval 或 Fraction
7. question_text 數學式完整用 $...$ 包裹
8. 只輸出 Python 代碼，無註解、無說明、無 Markdown、無額外文字
9. 程式碼結束後絕對無任何內容

【強烈建議結構】（模仿此邏輯）
- 第一部分：括號內加減 + 除法乘法
- 第二部分：絕對值內混合運算
- 用隨機產生除法整除（先產生除數與商，再反推被除數）
- 計算答案使用 eval 確保優先級正確

【輸出範例】（僅供參考，請勿直接抄襲）
```python
import random
from fractions import Fraction

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
