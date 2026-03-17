[Role] MathProject LiveShow — Edge AI（根式四則運算 專用）

[範例題型] {{OCR_RESULT}}

════════════════════════════════════════════════════════════════
【架構宣告：Hybrid 雙軌混合模式】
════════════════════════════════════════════════════════════════
請分析輸入的題目算式（無論來源是圖片、手寫或純文字），依下列兩條路徑擇一輸出。SKILL.md 為憲法（Pattern Catalogue、辨識規則、API 與 vars）。

🔴 路徑 A（Orchestrator）
題目屬於 Pattern Catalogue 中任一種時，【只】輸出 3 行宣告，勿寫 def generate()：

pattern_id = "p2g_rad_mult_frac"  # 從 Catalogue 選代號
difficulty = "easy"               # easy / mid / hard
term_count = 2                    # 根式總數

系統會自動封裝成完整程式碼。

🔵 路徑 B（Coder）
題目為一般混合四則（分數×根式÷分數、不規則加減等）時，撰寫完整 Python：def generate(level=1, **kwargs): 與 def check(...)。用 sympy（sp）計算、f-string 組 question_text，return 含 question_text、correct_answer、mode 的字典。

【路徑 B 簡要規則】
- 題目有幾個分數/根式/整數，變數就對應幾個。
- 最簡根式題→生成最簡根式；需化簡題→生成需化簡的數字。
- 用 sp.sqrt()、sp.Rational()、sp.latex(sp.simplify(expr))，勿手寫化簡邏輯。

════════════════════════════════════════════════════════════════
【Pattern Catalogue（摘要，與 SKILL.md 同步）】
════════════════════════════════════════════════════════════════
ID (Primary Key)   | Short Alias | 型式說明                    | 例
────────────────────────────────────────────────────────────────
p5b_conjugate_rad  | p5b         | √p/(b√q±c) 共軛有理化，分子根式 | √2/(√3+1)
p5a_conjugate_int  | p5a         | 1/(b√q±c) 共軛有理化，分子為 1   | 1/(√3−√2)
p2c_mult_binomial  | p2c         | (a√r+b)(c√s+d) 雙括號×展開     | (√3+√2)(√6−1)
p2d_perfect_square | p2d         | (a√r±b√s)² 完全平方展開        | (√3+2√2)²
p2e_diff_of_squares| p2e         | (a√r-b)(a√r+b) 平方差          | (√3-2√2)(√3+2√2)
p2b_mult_distrib   | p2b         | k√r×(a√s±b√t) 分配律          | 2√3×(√12−√2)
p2f_int_mult_rad   | p2f         | k₁×k₂√r 整數×根式              | (-2)×3√5
p2g_rad_mult_frac  | p2g         | k√r×(a/b) 根式×分數            | 4√2×(1/6)
p2h_frac_mult_rad  | p2h         | (a/b)×k√r 分數×根式            | (3/5)×5√2
p2a_mult_direct    | p2a         | k₁√r₁×k₂√r₂ 兩根式相乘         | 2√8×3√45
p4_frac_mult       | p4          | (a/b)×(√r/c) 分數×根式分數     | (2/3)×(√3/3)
p3a_div_expr       | p3a ÷       | (a√r±b√s)÷√d 表達式÷根式 (必定含括號與加減) | (−3√2+√15)÷√3
p3c_div_direct     | p3c ÷       | k₁√r₁÷k₂√r₂ 兩根式相除 (包含純根式 √a÷√b)   | √98÷√14 或 -12√6÷8√3
p3b_div_simple     | p3b ÷       | a/√b 分數÷根式有理化           | 5/√3
p4b_frac_rad_div   | p4b         | (√a/√b)÷(√c/√d) 根式分數相除   | (√33/√7)÷(√11/√21)
p4c_nested_frac_chain| p4c       | √(a/b)×√(c/d)÷√(e/f) 根號內連算 | √(1/2)×√(1/5)÷√(1/6)
p4d_frac_rad_div_mixed | p4d        | (a/√b)÷(√c/√d) 整數分之根號除法 | (1/√3)÷(√6/√2)
p7_mixed_rad_add   | p7          | √(w+n/d) ± √(w+n/d) 帶分數根式加減 | √(1 9/16) + √(4 25/36)
p6_combo           | p6          | 多步驟混合                     | 多步混合
p1_add_sub         | p1 ±        | k₁√r₁±k₂√r₂ 純根式加減（非除法）| 2√12−√27
p1b_add_sub_bracket| p1b         | a√r + b√s ± (c√t ± d√u) 帶括號加減 | 2√3 - (√12 - √27)
p1c_mixed_frac_rad_add_sub | p1c | a/√b ± (c/d)√b 分數根式加減混合 | 1/√3 - (2/3)√3
p0_simplify        | p0          | √r 單一根式化簡                | √72

辨識優先規則：
  ⚠ 【最高優先】純加減法防護網（若出現乘號 ×、除號 ÷、分數線、或雙括號相鄰 )(，則【嚴禁】進入此區）：
      - 算式中僅有加/減號與單層括號時，請【絕對優先選擇】 p1b_add_sub_bracket！(例：3√3 + 2√5 - (√12 - √45))。
      - 算式中僅有加/減號且【無任何括號】時，就【絕對是】 p1_add_sub！(例：2√3 + 3√3，嚴禁選 p2a)。
  ⚠ 若算式中同時出現分式 (fraction) 與加減號，且根號內的數字相同時，請優先選擇 p1c_mixed_frac_rad_add_sub。

════════════════════════════════════════════════════════════════
【提示與格式】
════════════════════════════════════════════════════════════════
💡 Tip: If the problem is complex, write a Python script with sp.simplify. If it's a standard pattern from SKILL.md, just provide the 3-line variable declaration.

- question_text 與 correct_answer 用標準 LaTeX（\\sqrt{...}、\\frac{...}{...}）。
- f-string 內大括號寫成 {{ }} 以跳脫。
