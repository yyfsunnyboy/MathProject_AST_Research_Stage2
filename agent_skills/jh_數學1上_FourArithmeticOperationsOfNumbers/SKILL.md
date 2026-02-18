【絕對禁止輸出 thinking 或任何非 code 內容】
- 嚴禁寫任何思考過程、解釋、註解
- 嚴禁寫 "Okay, I need to..." 或 "Let me think..." 或 "讓我思考一下"
- 直接輸出 Python code，沒有任何前言、後語
- 如果違反，直接 0 分

【代碼輸出格式】（違反直接 0 分）
✅ 第一行：import random
✅ 第二行：from fractions import Fraction
✅ 第三行：空行
✅ 第四行開始：def generate(level=1, **kwargs):
❌ 絕對不要：```python、```、思考過程、解釋文字、class 定義

【第一優先規則】
- 只能 import random 和 from fractions import Fraction！
- **嚴禁定義任何類（class）**！只寫 generate() 和 check() 兩個函數！
- 系統已注入輔助函數（to_latex, safe_eval, fmt_num）直接調用即可！

【角色】K12 數學演算法工程師

【任務】
實作 def generate(level=1, **kwargs)，生成數的四則運算（分數、小數混合）。
題目結構必須為：
- level=1: 基礎混合運算 (一般分數小數)
- level=2: 繁分數挑戰 (分數疊分數, Nested Fractions)
- level=3: 負數極限運算 (負號主導，多層絕對值)
返回 dict: {'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}

【程式要求】（必須嚴格遵守）
1. ⚠️ **只需寫兩個函式（不要定義其他類）**：
   - def generate(level=1, **kwargs): 生成題目
   - def check(user_answer, correct_answer): 檢查答案是否正確
2. generate 函式要回傳一個字典，包含以下欄位（請照抄 key 名稱）：
   - 'question_text': 題目文字
   - 'answer': 空字串 ''
   - 'correct_answer': 正確答案（必須是字串，例如 "3/5" 或 "-2.5"）
   - 'mode': 1



【參考例題與風格】（必須參考此風格，但生成多樣化題目）
計算 $$   \left[(-2+5) \times \frac{1}{3}\right] \div \left(-\frac{5}{2}\right) + \left|8 \times \left(-\frac{1}{4}\right) - 5\right|   $$ 的值。

【LaTeX 格式要求】（必須嚴格遵守）
1. 乘法用 \times，除法用 \div
2. 分數用 \frac{分子}{分母}
3. 絕對值必須使用 \left| ... \right|
4. 中括號用 \left[ ... \right]
5. ⚠️ 數學式完整用 $$   ...   $$ 包裹（注意前後有空格）
6. 負數分數：\left(-\frac{5}{2}\right) 或 -\frac{5}{2}
7. LaTeX 語法嚴格：$$ 符號只能出現在最外層

【LaTeX 字符串警告】（最常見錯誤，必看）
⚠️ Python 字符串中的反斜杠必須雙寫：
   ✅ 正確：f"\\times"  → 輸出 \times
   ✅ 正確：f"\\div"    → 輸出 \div
   ✅ 正確：f"\\frac{{a}}{{b}}" → 輸出 \frac{a}{b}
   ✅ 正確：f"\\left|"  → 輸出 \left|
   ❌ 錯誤：f"\times"   → SyntaxError！
   ❌ 錯誤：f"\frac{{a}}{{b}}" → SyntaxError！
   
   記住：f-string 裡的 \ 要寫成 \\

【核心規則】（必須嚴格遵守）
1. **系統已自動注入輔助函數（直接調用）**：
    - `to_latex(num)` - 轉成 LaTeX 分數格式
    - `fmt_num(num)` - 格式化數字（自動加括號）
    - `safe_eval(expr)` - 安全計算表達式
    
    ✅ **正確用法範例**：
    ```python
    import random
    from fractions import Fraction
    
    def generate(level=1, **kwargs):
        # ✅ 使用 Fraction 直接定義分數
        f1 = Fraction(1, 3) 
        f2 = Fraction(2, 5)
        
        # ✅ 使用標準運算符
        result = f1 + f2
        
        # ✅ 使用注入函數 to_latex
        latex_str = to_latex(result)
    ```
    
    ❌ **錯誤示範（絕對禁止）**：
    ```python
    f1 = create("1/3")  # 錯誤！create 未定義
    result = add(f1, f2) # 錯誤！add 未定義
    ```
    - ✅ 如果不想用 API，可直接使用 Fraction，但須手動處理 LaTeX 格式

2. 題目必須為：[括號內混合運算] + 絕對值結構
3. 必須包含分數運算，可混合整數
4. 包含四種運算符 +, -, \times, \div
5. ⚠️ 答案必須為最簡分數：使用 Fraction 自動化簡
6. ⚠️ 分數除法要確保有意義：避免分母為 0
7. ⚠️ 手動構建 LaTeX 字符串：使用 f-string 組合 \frac{分子}{分母} 格式
8. 計算使用 Fraction 確保精確
9. ⚠️ 答案格式化：
   - 如果是整數：result.numerator (當 denominator == 1)
   - 如果是分數：f"{result.numerator}/{result.denominator}"
10. ⚠️ 絕對禁止任何中文註解、中文標點符號（，。！？）！只能寫英文註解或不寫註解！
11. 只輸出 Python 代碼，無說明、無 Markdown、無額外文字
12. 程式碼結束後絕對無任何內容

【強烈建議結構】（請模仿此邏輯）
```python
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    # Adjust difficulty based on level
    if level == 1:
        int_range = (-5, 5)
        frac_range = (1, 6)
    elif level == 2:
        int_range = (-20, 20)
        frac_range = (1, 12)
    else:  # level 3
        int_range = (-100, 100)
        frac_range = (1, 20)
    
    # Part 1: Bracket with fractions
    a = random.randint(*int_range)
    b = random.randint(1, int_range[1])
    # Use Fraction(n, d) directly
    num1 = random.randint(1, frac_range[1])
    den1 = random.randint(2, frac_range[1])
    frac1 = Fraction(num1, den1)
    
    # Note: to_latex is injected globally
    part1_str = f"\\left[({a}+{b}) \\times {to_latex(frac1)}\\right]"
    
    # Part 2: Division by fraction (ensure non-zero denominator)
    num2 = random.randint(-frac_range[1], -1)
    den2 = random.randint(2, frac_range[1])
    frac2 = Fraction(num2, den2)
    part2_str = f"\\left({to_latex(frac2)}\\right)"
    
    # Part 3: Absolute value with fraction
    c = random.randint(int_range[0]//2, int_range[1]//2)
    num3 = random.randint(-frac_range[1], -1)
    den3 = random.randint(2, frac_range[1])
    frac3 = Fraction(num3, den3)
    d = random.randint(1, frac_range[1])
    
    part3_str = f"\\left|{c} \\times {to_latex(frac3)} - {d}\\right|"
    
    question_text = f"計算 $$   {part1_str} \\div {part2_str} + {part3_str}   $$ 的值。"
    
    # Calculate answer using standard operators
    val1 = (a + b) * frac1
    val2 = frac2
    val3 = abs((c * frac3) - d)
    
    # Use Fraction for final calculation to keep precision
    result = (val1 / val2) + val3
    
    # Format answer as simplified fraction or integer
    if result.denominator == 1:
        correct_answer = str(result.numerator)
    else:
        correct_answer = f"{result.numerator}/{result.denominator}"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

   def check(user_answer, correct_answer):
       try:
           # 1. Strip and clean string
           ua_str = str(user_answer).strip()
           ca_str = str(correct_answer).strip()
           
           # 2. Exact string match
           if ua_str == ca_str:
               return {'correct': True, 'result': '正確'}
           
           # 3. Numeric comparison (support fraction string like "3/4")
           ua = float(Fraction(ua_str))
           ca = float(Fraction(ca_str))
           
           if abs(ua - ca) < 1e-9:
                return {'correct': True, 'result': '正確'}
                
           return {'correct': False, 'result': '錯誤'}
       except:
           return {'correct': False, 'result': '錯誤'}
```
⚠️ check 函式【必須返回字典】，不能只返回布爾值！

【常見錯誤警告】（從失敗案例學習）
❌ **字符串轉義錯誤** → f"\times" 應該是 f"\\times"（最常見！）
❌ **使用類前綴調用** → FractionOps.create() 是錯的！應該直接寫 Fraction()
❌ **自己定義 FractionOps 類** → 浪費時間且會導致缺少 generate() 函數！
❌ **輸出 Markdown 代碼塊** → 不要寫 ```python，直接寫代碼！
❌ 分數 LaTeX 寫錯：應該是 \frac{1}{2} 不是 1/2
❌ 負分數括號遺漏：應該是 \left(-\frac{5}{2}\right)
❌ 使用單個 $ 而非 $$   ...   $$ → 格式不統一
❌ check 函數返回布爾值而非字典 → 系統錯誤
❌ 答案未化簡：必須用 Fraction 自動化簡
❌ 寫中文註解 → 違反規定
⚠️ Output Python code ONLY. No introduction. No comments. No thinking.
/no_think