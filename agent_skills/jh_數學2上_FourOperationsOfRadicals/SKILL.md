【角色】Edge AI — 根式四則運算

════════════════════════════════════════════════════════════════
Pattern Catalogue（按優先順序匹配，第一個符合的為答案）
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
  ⚠ p5b 優先於 p5a（看分子是否為根式）。
  ⚠ p2c 優先於 p2b（看是否有雙括號）。
  ⚠ 若算式中同時出現分式 (fraction) 與加減號，且根號內的數字相同時，請優先選擇 p1c_mixed_frac_rad_add_sub。
  ⚠ 單純的根式相除 (如 √98 ÷ √14) 請選 p3c_div_direct。
  ⚠ 帶有括號與加減號的除法 (如 (−3√2+√15)÷√3) 才選 p3a_div_expr。
  ⚠ 如遇無法辨識，預設 p1_add_sub，difficulty="mid"。

════════════════════════════════════════════════════════════════
各 pattern 的 difficulty 建議
════════════════════════════════════════════════════════════════
  easy  → p0, p1（2 項）, p2a, p2f, p2g, p2h, p3b
  mid   → p1（3 項）, p1b, p1c, p2b, p3a, p3c, p4, p5a
  hard  → p1（4 項）, p2c, p2d, p2e, p4b, p4c, p4d, p5b, p6_combo, p7_mixed_rad_add

════════════════════════════════════════════════════════════════
DomainFunctionHelper 公開 API 速查
════════════════════════════════════════════════════════════════
df.get_safe_vars_for_pattern(pattern_id, difficulty, term_count=term_count, style=...)  → dict
df.solve_problem_pattern(pattern_id, vars, difficulty) → (str, List[str])
df.format_question_LaTeX(pattern_id, vars)             → str

════════════════════════════════════════════════════════════════
vars 結構參考（各 pattern 的變數鍵）
════════════════════════════════════════════════════════════════
p0_simplify      : {"r": int}
p1_add_sub       : {"terms": [(coeff, radicand, op), ...]}   op ∈ {"+", "-"}
p1b_add_sub_bracket : {"c1","r1","c2","r2","c3","r3","c4","r4","op_bracket"}   op_bracket ∈ {"+","-"}
p1c_mixed_frac_rad_add_sub : {"a","b","c","d","op"}   b is shared radicand, op ∈ {"+","-"}
p2a_mult_direct  : {"c1", "r1", "c2", "r2"}
p2b_mult_distrib : {"c1", "r1", "c2", "r2", "c3", "r3", "op"}
p2c_mult_binomial: {"c1","r1","c2","r2","c3","r3","c4","r4"}
p2d_perfect_square: {"c1","r1","c2","r2","op"}   op ∈ {"+","-"}
p2e_diff_of_squares: {"c1","r1","c2","r2"}
p2f_int_mult_rad : {"c1", "c2", "r"}
p2g_rad_mult_frac, p2h_frac_mult_rad : {"k", "r", "num", "den"}
p3a_div_expr     : {"c1","r1","c2","r2","denom_r","op"}
p3c_div_direct   : {"c1","r1","c2","r2"}
p3b_div_simple   : {"a": int, "b": int}
p4_frac_mult     : {"a","b","r","c"}
p4b_frac_rad_div : {"n1","d1","n2","d2"}
p4c_nested_frac_chain: {"n1","d1","n2","d2","n3","d3"}
p5a_conjugate_int: {"b","q","c","sign"}   sign ∈ {1,-1}
p5b_conjugate_rad: {"p","b","q","c","sign"}
p6_combo         : {"sub_pattern1","vars1","sub_pattern2","vars2","combo_op"}
p7_mixed_rad_add : {"w1","f_n1","d1","n1","w2","f_n2","d2","n2","op"}   op ∈ {"+","-"}

=== SKILL_END_PROMPT ===
