# SHOWREEL_LOGIC (2026-03-23)

本文件是給下一位 AI / 工程師接手 `live_show` 展演系統時使用的交接總表。
目標不是只記錄單一 bug，而是讓接手者能快速理解：

- 現在的展演生成架構怎麼運作
- 今天到底修了哪些問題
- 四個核心 skill 現在各自走哪條生成路徑
- 還有哪些規則不能被破壞
- 接下來若要擴 skill / 做診斷 / 做展演，要從哪裡下手

---

## 1. 今日總結

截至 2026-03-23，以下四個 skill 已整理到可展演的高規格狀態：

- `jh_數學1上_FourArithmeticOperationsOfIntegers`
- `jh_數學1上_FourArithmeticOperationsOfNumbers`
- `jh_數學2上_FourArithmeticOperationsOfPolynomial`
- `jh_數學2上_FourOperationsOfRadicals`

今天最重要的結論：

1. `live_show` 不再是「主要靠模型自由發揮出題」。
2. 現在的核心策略是：
   - 先 `classify skill_id`
   - 再判 `family / pattern`
   - 能走 deterministic helper 就不要交給模型亂寫
   - helper 不足時才走 scaffold prompt + healer
3. 分數 skill 已補成完整 deterministic helper 路徑，並新增大量 runtime-friendly 變體邏輯。
4. 多項式 skill 的 family catalogue / answer format / division display 已補齊。
5. 根式 skill 維持 pattern orchestrator 為主，規格完整度最高。
6. 整數 skill 現在文件結構已補成與 polynomial 同級，可作為 family-preserving scaffold。

---

## 2. 現在的生成架構

### 2.1 高層流程

`學生輸入題目 -> OCR / canonical text -> classify skill_id -> deterministic override -> 讀 SKILL.md / prompt_liveshow.md -> 判 family / pattern -> helper 或 scaffold 生成 -> healer / guard -> execute -> render`

簡單說：

- `skill_id` 決定用哪個技能
- `family / pattern` 決定用哪一種題型骨架
- `helper / pattern engine` 決定大部分真正的題面格式與答案格式
- Qwen3 8B 只是在 scaffold 路徑中補 generator，不是唯一真相來源

### 2.2 關鍵分流

#### A. Deterministic Helper Path

主要由 `core/routes/live_show.py` 直接分流：

- Polynomial -> `PolynomialFunctionHelper`
- Integer -> `IntegerFunctionHelper`
- Fraction -> `FractionFunctionHelper`

這條路徑下：

- 題型不是靠模型猜，而是 helper 的 `build_config()` 先判 family
- `generate_from_config()` 決定 `question_text` / `correct_answer`
- `build_runtime_config()` 決定「下一題」如何保持同 family 但改數值

#### B. Pattern Orchestrator Path

Radicals 主要走這條：

- `Pattern Catalogue`
- `pattern_id`
- `vars schema`
- `DomainFunctionHelper`
- `RadicalOps`

根式 skill 不應被視為單純 prompt skill，它更像一份「pattern 規格 + vars 契約 + API 契約」。

#### C. Scaffold Prompt Path

當 helper / pattern 無法完全接手時：

- 系統讀取 `SKILL.md`
- 優先疊加 `prompt_liveshow.md`
- 將 OCR 結果注入 `{{OCR_RESULT}}`
- 組成 scaffold prompt 給模型
- 再經 healer / AST / regex / pattern guard 收斂

這就是為什麼 `SKILL.md` 不需要堆超多逐題範例也能運作：
真正格式很多時候是 helper / domain API 決定，不是模型自由創作。

---

## 3. 目前四個 skill 的主路徑

### 3.1 Integers

skill:
- `jh_數學1上_FourArithmeticOperationsOfIntegers`

主策略：
- deterministic classify
- integer helper path
- 文件提供 family-preserving 規範

定位：
- 規則分類 + 結構 fingerprint + family-preserving generator scaffold

目前 family：
- `I1 int_numberline_add_sub`
- `I2 int_flat_add_sub`
- `I3 int_flat_mul_div_exact`
- `I4 int_flat_mixed_four_ops`
- `I5 int_bracket_mixed`
- `I6 int_abs_value`
- `I7 int_division_exact_nested`
- `I8 int_composite_structure`

### 3.2 Fractions

skill:
- `jh_數學1上_FourArithmeticOperationsOfNumbers`

主策略：
- deterministic classify
- `FractionFunctionHelper` 為主要真相來源
- prompt/scaffold 退居輔助

定位：
- helper 主導的 family-preserving fraction engine

目前 family：
- `F1 Fraction Simplification`
- `F2 Equivalent Fraction Fill-Blank`
- `F3 Preserve-Value Fraction Invariance`
- `F4 Fraction Comparison`
- `F5 Fraction Add/Subtract`
- `F6 Fraction Multiply`
- `F7 Fraction Divide`
- `F8 Reciprocal`
- `F9 Decimal-Fraction Mixed Evaluation`
- `F10 Fraction Word Problems`

### 3.3 Polynomial

skill:
- `jh_數學2上_FourArithmeticOperationsOfPolynomial`

主策略：
- deterministic classify
- `PolynomialFunctionHelper` 主導
- family catalogue + answer type contract

定位：
- family-preserving polynomial generator with strong answer formatting rules

目前 family：
- `F1 poly_add_sub_flat`
- `F2 poly_add_sub_nested`
- `F3 poly_add_sub_unknown`
- `F4 poly_mul_monomial`
- `F5 poly_mul_poly`
- `F6 poly_mul_special_identity`
- `F7 poly_div_monomial_eval`
- `F8 poly_div_monomial_qr`
- `F9 poly_div_poly_qr`
- `F10 poly_div_reverse`
- `F11 poly_mixed_simplify`
- `F12 poly_geom_formula_direct`
- `F13 poly_geom_region_composite`

### 3.4 Radicals

skill:
- `jh_數學2上_FourOperationsOfRadicals`

主策略：
- classify -> pattern catalogue -> orchestrator scaffold -> `DomainFunctionHelper` / `RadicalOps`

定位：
- pattern engine + strict vars schema + domain API contract

目前 pattern family：
- `p0_simplify`
- `p1_add_sub`
- `p1b_add_sub_bracket`
- `p1c_mixed_frac_rad_add_sub`
- `p2a_mult_direct`
- `p2b_mult_distrib`
- `p2c_mult_binomial`
- `p2d_perfect_square`
- `p2e_diff_of_squares`
- `p2f_int_mult_rad`
- `p2g_rad_mult_frac`
- `p2h_frac_mult_rad`
- `p3a_div_expr`
- `p3b_div_simple`
- `p3c_div_direct`
- `p4_frac_mult`
- `p4b_frac_rad_div`
- `p4c_nested_frac_chain`
- `p4d_frac_rad_div_mixed`
- `p5a_conjugate_int`
- `p5b_conjugate_rad`
- `p6_combo`
- `p7_mixed_rad_add`

---

## 4. 今天完成的重點異動

### 4.1 分數 skill 升級為高規格 deterministic helper

核心檔案：
- `core/fraction_domain_functions.py`
- `core/routes/live_show.py`
- `tests/test_fraction_domain_functions.py`
- `tests/test_live_show_fraction_helper.py`
- `tests/comprehensive_stress_test_fraction.py`

完成內容：

1. 補完整 family 規格與 `build_config()`
2. 新增 `FractionFunctionHelper` 為 live_show 主路徑
3. 補齊 textbook-style LaTeX 題面格式：
   - `\frac{a}{b}`
   - `\times`
   - `\div`
   - 混合數顯示
4. 修正 image classify 誤判 polynomial 的情況
5. 修正 mixed number 被錯當成乘法：
   - `9\frac{1}{5}` 不能被當成 `9 * 1/5`
6. 補齊 common-factor family：
   - 右公因數：`A×k ± B×k`
   - 左公因數：`k×A ± k×B`
7. common-factor runtime 變體不再只改一兩個數字，而是保留骨架且全部數值位可變
8. 對學生不友善的大數值模板已改成 friendly templates
9. 補 decimal-mix friendly templates：
   - `fraction ÷ decimal × fraction ± fraction`
   - `fraction × (fraction + decimal) ÷ fraction`
10. 補齊 fraction stress report

### 4.2 多項式 skill 文件與答案格式補強

核心檔案：
- `core/polynomial_domain_functions.py`
- `agent_skills/jh_數學2上_FourArithmeticOperationsOfPolynomial/SKILL.md`
- `agent_skills/jh_數學2上_FourArithmeticOperationsOfPolynomial/prompt_liveshow.md`
- `tests/test_polynomial_division_latex.py`
- `tests/test_polynomial_division_negative_divisor.py`

完成內容：

1. `SKILL.md` / `prompt_liveshow.md` 升級為完整 family catalogue
2. 補齊 sub-skill graph
3. 補齊 answer-type contract
4. 修正多項式除法答案格式：
   - `(3/4)x` 而不是 `3/4x`
5. 多項式 division latex 輸出更穩定

### 4.3 整數 skill 文件重構

核心檔案：
- `agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers/SKILL.md`
- `agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers/prompt_liveshow.md`

完成內容：

1. 補齊 `Family Catalogue`
2. 補齊 `Sub-skill Graph`
3. 補齊 structural schema
4. 補齊 live_show family decision rules

### 4.4 根式 skill 文件補成完整規格書

核心檔案：
- `agent_skills/jh_數學2上_FourOperationsOfRadicals/SKILL.md`
- `agent_skills/jh_數學2上_FourOperationsOfRadicals/prompt_liveshow.md`

完成內容：

1. 保留 pattern / vars / orchestrator 優勢
2. 補齊 pattern catalogue 與 family decision
3. 補齊 sub-skill graph
4. 強調 `vars` 不得用運算式字串濫充

---

## 5. 已知重要規則

### R1. `下一題` 必須依賴可執行 generator

任何會落地到 `generated_scripts/*.py` 且供 `run_generated_code` 使用的腳本，至少要：

1. 有 `def generate(level=1, **kwargs)`
2. 可 `compile()`
3. 每次重跑真的能改數值，而不是固定題面

### R2. 先保 family，再談亂數

不能為了出新題，把 family 改掉。

例：
- 共同因數題不能退化成普通乘減題
- 多項式長除法不能退化成單純加減題
- 根式有理化不能退化成根式相加減

### R3. 題面與答案格式必須 textbook-style

最低標準：

- visible math 用 `$...$`
- 分數優先 `\frac{}{}`
- 乘法 `\times`
- 除法 `\div`
- 負數括號風格要保留，例如 `(-2)`

### R4. display format 不是附屬品，是 correctness 的一部分

本系統中，下列都算 correctness 範圍：

- 題型有沒有漂移
- family 是否保留
- 題面是否為課本式 LaTeX
- 答案顯示是否會造成誤讀

### R5. image route 與 text route 要在 canonical OCR 之後匯流

不能讓 image 路徑和 text 路徑因 skill 判定邏輯不同而產生兩套真相。

現在策略：
- 先取 OCR
- 再做 deterministic override
- 再進 generate_live

---

## 6. 目前最重要的程式入口

### `core/routes/live_show.py`

最重要。

責任：
- classify
- deterministic override
- direct helper path dispatch
- scaffold prompt assembly
- answer sync
- top-level output normalization

### `core/fraction_domain_functions.py`

目前是分數 skill 的主戰場。

責任：
- family detection
- question_text formatting
- correct_answer generation
- runtime variation
- friendly template generation

### `core/polynomial_domain_functions.py`

多項式 deterministic helper 主體。

### `core/domain_functions.py`

根式 pattern / vars / LaTeX / solve 主體之一。

### `core/routes/live_show_pipeline.py`

scaffold 與 healer 組裝的重要路徑，特別是 radical orchestrator。

---

## 7. 目前的測試狀態

本日已重跑且通過：

- `tests/test_fraction_domain_functions.py`
- `tests/test_live_show_fraction_helper.py`
- `tests/test_polynomial_division_latex.py`
- `tests/test_polynomial_division_negative_divisor.py`

總計：
- `31 passed`

另外已重新生成：
- `tests/stress_test_report_fraction.html`

注意：
- 整數與根式今天主要是規格巡檢，不是重新跑完整的新壓測
- 若明天要正式 demo 前再做一次保險，建議優先補跑 integer / radical live_show smoke set

---

## 8. 目前已知非阻塞風險

### A. 舊字串仍有少量 mojibake / 編碼殘留

主要仍存在於部分舊文案或歷史檔案，不一定會影響生成，但會影響維護閱讀。

### B. 分數 helper 中仍保留 `unsupported` 防呆分支

這不是 bug，而是明確拒收：
- catalogue 之外的 very exotic ellipsis / chain patterns

### C. Radical 仍是最複雜 skill

它最依賴：
- pattern_id
- vars schema
- orchestrator scaffold

所以如果未來 radical 出錯，先查 pattern / vars，不要第一時間怪 Qwen3。

---

## 9. 明天接手 AI 應先知道的事

如果明天要繼續開發或討論，先接受下面幾個前提：

1. 這套系統不是純 prompt system，而是 hybrid system
2. helper / pattern engine 的地位高於模型自由生成
3. `SKILL.md` 是共用規格書，`prompt_liveshow.md` 是 live_show delta
4. family catalogue 與 sub-skill graph 現在已經是後續診斷系統的核心資料源
5. 若要新增 skill，優先問：
   - 這個 skill 適合 helper path、pattern path、還是 scaffold path？
   - family catalogue 是否足夠細？
   - 是否需要 vars schema？
   - display format 是否有教材敏感性？

---

## 10. 推薦的下一步

### P0

1. 對 integer / radical 補一輪專屬 live_show smoke tests
2. 清理舊 mojibake 文案
3. 對 `generated_scripts` 加清理策略

### P1

1. 將四個 skill 的 `family -> subskill node -> diagnosis breakpoint` 接到學生診斷
2. 建立 family-level analytics
3. 針對 common-factor / decimal-mix / long-division 做展示樣本集

### P2

1. 將 `docs/skill_breakpoint_catalog.csv`
2. 與 `docs/skill_breakpoint_catalog.md`
接到後續學習斷點判讀流程

---

## 11. 交接結論

今天的核心成果不是只修幾個 bug，而是把 `live_show` 從「容易漂移的模型生成展示」推進成：

- skill-aware
- family-aware
- helper-first
- prompt-assisted
- healer-guarded
- textbook-display-aware

的穩定展演系統。

如果明天 AI 要接手，應直接從：

1. `core/routes/live_show.py`
2. `core/fraction_domain_functions.py`
3. `core/polynomial_domain_functions.py`
4. `core/domain_functions.py`
5. `docs/skill_breakpoint_catalog.md`

開始讀。
