【角色】K12 數學演算法工程師

【任務】
實作 def generate(level=1, **kwargs)，生成「多項式導數應用」題目。
題目結構必須為：
- level=1: 基礎導數計算 (求 f'(x))
- level=2: 切線方程式應用 (求過點 (x0, y0) 的切線，需計算斜率)
- level=3: 極值問題 (求極大/極小值，需使用二階導數判別)
返回 dict: {'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}

【輸出規範】(非常重要，請嚴格遵守)
1.  **禁止廢話**：不要輸出 "好的"、"Sure"、"Here is..."、"讓我思考一下" 等任何對話內容。
2.  **直接代碼**：直接開始寫 `import ...` 或 `def generate...`。
3.  **純淨代碼**：不要包含 Markdown 代碼塊標記 (```python)，直接輸出純文本代碼。
4.  **禁止中文註釋**：代碼中的註解請使用英文，或完全不寫註解 (No Chinese Comments)。

【預載工具 API 手冊】(環境已實作，請直接調用，無需重新定義)

1. **基礎工具**
   - `fmt_num(n) -> str`: 格式化數字 (如 "5", "-3", "1/2")
   - `to_latex(n) -> str`: 轉 LaTeX 格式
   - `clean_latex_output(q) -> str`: (⚠️ 僅限簡單題型使用，本題型禁止使用)

2. **多項式專用工具** (請優先使用)
   - `_coeffs_to_terms(coeffs: list) -> list[tuple]`: 
     * 輸入: `[3, -5, 2]` (代表 3x^2 - 5x + 2)
     * 輸出: `[(3, 2), (-5, 1), (2, 0)]`
   
   - `_differentiate_poly(terms: list[tuple], order=1) -> list[tuple]`:
     * 輸入: terms 列表 (🔴 注意：必須是 list，不能是字串)
     * 輸出: 微分後的 terms 列表
   
   - `_poly_to_latex(terms: list[tuple]) -> str`:
     * 用途: 生成題目用的 LaTeX (不含 $)
     * 範例: "3x^{2} - 5x + 2"
   
   - `_poly_to_plain(terms: list[tuple]) -> str`:
     * 用途: 生成答案用的純文字 (無空格)
     * 範例: "3x^2-5x+2"
   
   - `_deriv_symbol_latex(order: int) -> str`:
     * 輸出: "f'(x)", "f''(x)" (不含 $)

3. **常用數學庫**
   - `random`, `math`, `re`, `ast`, `operator` (已匯入)
   - `gcd(a, b)`, `lcm(a, b)`, `is_prime(n)`

【核心規則】(Violating these leads to crash)

1. ✅ **安全的迴圈設計**
   - 使用 shuffle + slice：`available = list(range(n)); random.shuffle(available); selected = available[:k]`
   - 外層 `while True` 只用於整個物件再生 (Retry Loop)
   - 🔴 **禁止**在內層使用 `while True` 或不確定終止條件的迴圈

2. ✅ **LaTeX 格式**
   - 所有數學式必須被 $ 包裹：`f"計算 ${expr}$ 的值"`
   - 中文與 $ 必須分離：`f"求 ${expr}$ 的因式分解"`

3. ✅ **答案格式**
   - 純結果，不含符號、等號、換行
   - ✅ 正確：`"6x^2-10x, 12x-10"`
   - ❌ 錯誤：`"f'(x) = ..."`

4. ✅ **資料流 (Data Flow)**
   - 先轉換格式：`terms = _coeffs_to_terms(coeffs)`
   - 再調用計算：`deriv = _differentiate_poly(terms, order=1)` (🔴 輸入必須是 terms)
   - 最後轉字串：`ans = _poly_to_plain(deriv)`

5. ✅ **只輸出代碼**
   - 不使用 `eval` / `exec`
   - 不加任何 Markdown 說明

【成功的代碼模式】(Logic Closed Loop)

```python
def generate(level=1, **kwargs):
    # 外層循環：負責整個物件的重試
    while True:
        # 步驟 1: 生成參數
        degree = random.randint(3, 5)
        
        # 步驟 2: 使用 shuffle + slice 確保「至少 3 個非零項」
        # (這是滿足 MASTER_SPEC 約束的關鍵技巧)
        coeffs = [0] * (degree + 1)
        
        # 2.1 確保最高次項係數非零
        coeffs[degree] = random.randint(-10, 10)
        while coeffs[degree] == 0:
            coeffs[degree] = random.randint(1, 10)
            
        # 2.2 決定還需要幾個非零項
        min_extra = 2 
        max_extra = degree 
        num_extra = random.randint(min_extra, max_extra)
        
        # 2.3 從剩餘的位置中隨機選取
        remaining_indices = list(range(degree))
        random.shuffle(remaining_indices)
        selected_indices = remaining_indices[:num_extra]
        
        # 2.4 填入係數
        for idx in selected_indices:
            c = random.randint(-10, 10)
            while c == 0: c = random.randint(-10, 10)
            coeffs[idx] = c
            
        # 步驟 3: 格式轉換 (Standard Domain Tool)
        # ✅ 關鍵：terms 是 List，專門給計算用的
        terms = _coeffs_to_terms(coeffs)
        
        # 步驟 4: 計算結果 (包含錯誤處理)
        try:
            orders = list(range(1, degree))
            random.shuffle(orders)
            target_orders = sorted(orders[:2])
            
            deriv_results = []
            for order in target_orders:
                # ✅ 關鍵：傳入的是 terms (List)，絕對不是字串！
                d_terms = _differentiate_poly(terms, order=order)
                deriv_results.append(d_terms)
                
        except ValueError:
             continue # 數值過大等錯誤，重試整個題目

        # 步驟 5: 組裝題目（手動加 $，絕對不 call clean）
        poly_latex = _poly_to_latex(terms)
        symbols = " 與 ".join(f"${_deriv_symbol_latex(o)}$" for o in target_orders)
        q = f'已知 $f(x) = {poly_latex}$，求 {symbols}。'
        
        # 步驟 6: 組裝答案（純多項式，逗號分隔）
        ans_parts = [_poly_to_plain(d) for d in deriv_results]
        a = ", ".join(ans_parts)
        
        return {
            'question_text': q,
            'correct_answer': a,
            'answer': a,
            'mode': 1
        }
