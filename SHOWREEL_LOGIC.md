# Math-Master Live Show — 架構與交接文件

**核心宗旨**：透過工程干預（Scaffold + Healer + Policy Registry）讓小型在地模型在教學情境中穩定可控。

---

## ⚡ 30 秒交接（先看這裡）

- 分層架構：Route 編排 → Pipeline 協調 → Healer 修復 → Code Utils → Skill Policy Registry。
- 不要在 route 寫硬編碼 skill mapping；技能策略與 alias 一律進 policy registry。
- 改技能行為優先順序：**policy 檔 → healer/code_utils → 最後才 route**。
- 修補計數必須可追溯（Code / Display / AST / O1）。
- 每次修改後至少跑 `py_compile` 與 `tests/test_live_show_healer_regression.py`。

---

## 1. 系統分層

| 層級 | 入口 | 職責 |
|------|------|------|
| Route Orchestration | `core/routes/live_show.py` | API 入口、流程編排，避免放複雜規則 |
| Pipeline Coordination | `core/routes/live_show_pipeline.py` | Ab2/Ab3 協調、output/debug_meta 組裝 |
| Healer Layer | `core/healers/live_show_healer.py`, `regex_healer.py`, `ast_healer.py` | 可追溯修復、fix-count 分帳 |
| Math/Struct Utils | `core/healers/live_show_iso_guard.py`, `core/code_utils/live_show_math_utils.py` | 同構比較、答案重算、ISO guard |
| Skill Policy Registry | `core/skill_policies/registry.py` + family policies | 技能策略開關、skill alias 正規化 |

---

## 2. 目錄結構（摘要）

```text
MathProject_AST_Research/
├─ core/
│  ├─ routes/          live_show.py, live_show_pipeline.py
│  ├─ healers/         live_show_healer.py, regex_healer.py, ast_healer.py, live_show_iso_guard.py
│  ├─ code_utils/      live_show_math_utils.py, math_utils.py, latex_utils.py
│  ├─ skill_policies/  registry.py, fraction.py, integer.py, polynomial.py, radical.py
│  ├─ prompts/         domain_function_library.py  ← RadicalOps / FractionOps 注入源
│  ├─ engine/          scaler.py, engine.py
│  └─ scaffold/        domain_libs.py
├─ agent_skills/
│  ├─ jh_數學1上_FourArithmeticOperationsOfIntegers/
│  ├─ jh_數學1上_FourArithmeticOperationsOfNumbers/
│  ├─ jh_數學2上_FourOperationsOfRadicals/
│  └─ jh_數學2上_FourOperationsOfPolynomials/
├─ tests/              test_live_show_healer_regression.py
├─ generated_scripts/  live_show_*.py  ← AI 產出的暫存腳本
└─ SHOWREEL_LOGIC.md
```

---

## 3. Live Show Pipeline（展示敘事）

1. 影像/文字輸入 → `/api/classify` → Qwen3-VL → skill DNA
2. Scaffold 注入（SKILL.md base + prompt_liveshow.md delta）
3. Ab1 原生推論（不過 healer）
4. Ab2 執行攔截（pipeline）：快速執行 + guard/fallback，不過 healer
5. Ab3 完整自癒（pipeline）：healer + guard + 同構驗證 + MCRI
6. Output 組裝（`assemble_visual_output`）
7. Route 回傳前端欄位整平

---

## 4. 新技能接入 SOP（Policy-Only）

### Step 1) 決定 family
- 分數→`fraction.py`、整數→`integer.py`、多項式→`polynomial.py`、根號→`radical.py`、新 family→新檔

### Step 2) policy 檔加入最少欄位
```python
{"policy_id": "...", "family": "...", "skill_ids": [...], "aliases": [...],
 "apply_fraction_eval_patch": False, "enable_fraction_display": False,
 "force_fraction_answer": False, "fallback_fraction_style": False}
```

### Step 3) 驗證 alias 正規化
```bash
python -c "from core.skill_policies import normalize_skill_id; print(normalize_skill_id('Arithmetic'))"
```

### Step 4) 最低驗證命令
```bash
python -m py_compile core/routes/live_show.py core/routes/live_show_pipeline.py \
  core/healers/live_show_healer.py core/skill_policies/registry.py
python -m pytest tests/test_live_show_healer_regression.py -q
```

---

## 5. AI 交接快速上手

### 5.1 當前架構約定（不要破壞）
- Route 只做 orchestration，不承擔複雜規則。
- Ab2/Ab3 協調與 debug_meta 組裝放 pipeline helper，不回塞 route。
- skill-specific 行為一律走 policy（避免 route/healer 寫硬編碼 skill_id）。
- fix count 採分帳：Code / Display / AST / O1，需可追溯。
- fallback log 必須保留，不能靜默吞掉。

### 5.2 典型開發出手順序
1. 策略問題 → 改 `core/skill_policies/*`
2. Ab2/Ab3 協調或 output 組裝 → 改 `core/routes/live_show_pipeline.py`
3. 顯示/答案問題 → 改 `core/healers/live_show_healer.py`
4. 結構同構/答案重算 → 改 `core/code_utils/live_show_math_utils.py`
5. 最後才碰 `core/routes/live_show.py`

### 5.3 常見坑位
- 在 route 重新加入硬編碼 skill map（破壞 registry 單一真相）。
- 只改 `regex_fixes`，忘了同步 `regex_code_fixes` / `regex_display_fixes`。
- fallback 成功但沒記錄 log，導致除錯不可追溯。

---

## 6. Agent Skill 三層架構規範

> ⚠️ 每次修改 agent_skills/ 前必讀此節

### 6.1 架構原則

```
agent_skills/{skill_name}/
    SKILL.md              ← base rules（Role 定義、imports、API 介面、domain 規則）
    prompt_liveshow.md    ← liveshow 專用 delta
    prompt_benchmark.md   ← benchmark 專用 delta
    evals.json, skill.json
```

- `SKILL.md` 末尾有且只有一個 `=== SKILL_END_PROMPT ===`，之後不得有任何內容。
- `prompt_liveshow.md` / `prompt_benchmark.md` 只含各自 delta，**不得複製 base 內容**。

### 6.2 Runtime 組合邏輯
```python
base   = SKILL.md.split("=== SKILL_END_PROMPT ===")[0].strip()
delta  = prompt_liveshow.md 全文
prompt = f"{base}\n=== SKILL_END_PROMPT ===\n\n{delta}"
```

### 6.3 維護規則

| 要修改的行為 | 修改哪個檔案 |
|---|---|
| Domain API / import / 共用 interface | `SKILL.md` |
| LiveShow 生成演算法（同構規則、格式要求） | `prompt_liveshow.md` |
| Benchmark 題型結構、難度等級 | `prompt_benchmark.md` |

---

## 7. 目前各技能狀態

| 技能 | SKILL.md | prompt_liveshow.md | prompt_benchmark.md |
|------|----------|-------------------|---------------------|
| jh_數學1上_Integers | ✅ | ✅ | ✅ |
| jh_數學1上_Numbers | ✅ | ✅ | ✅ |
| jh_數學2上_Radicals | ✅ | ✅（最新，含 7 情境 A–G） | ✅ |
| jh_數學2上_Polynomial | ✅ | ✅ | ✅ |

---

## 8. 最新工作進度（2026-03-14）

### 8.1 本次主要工作範疇

**LiveShow 根式題型（jh_數學2上_FourOperationsOfRadicals）穩定化**

從實際測試中發現並修復多個問題，確保 4 張課本圖片的題型全部可正確生成：
- 圖1：`√(5³)`, `√18`, `√8 × √45`
- 圖2：`2√3+3√3`, `4√6-3√6`, `5√10-3√5-2√10+4√5`
- 圖3：`2√3×(√12-√2)`, `(-3√2+√15)÷√3`, `(√3+√2)(√6-1)`
- 圖4：`1/(√3-√2)`, `√2/(3√2+4)`

### 8.2 修改的檔案與內容

| 檔案 | 修改內容 |
|------|---------|
| `agent_skills/jh_數學2上_FourOperationsOfRadicals/prompt_liveshow.md` | 全面重寫：加入 STEP 0 強制輸入分析模板、7 個情境（A–G）完整程式碼、情境 F（直接相乘/單根式化簡）、情境 G（分母有理化）、Situation C 有理化邏輯修正（nc_raw // denom_r）、simplify_term 參數順序警告 |
| `core/healers/regex_healer.py` | 新增 4 個修復方法：`fix_simplify_term_arg_order`、`fix_shadowed_correct_answer`、`fix_simplify_term_tuple_as_key`、`fix_missing_correct_answer`；擴充 `fix_hallucinated_methods` 加入 `simplify_root` 幻覺修復 |
| `core/healers/live_show_healer.py` | `sanitize_question_text_display` 加入 `$...$` 自動補加 guard：若 question_text 含 LaTeX 指令但無 $ 符號，自動補「計算 $...$ 的值。」 |
| `core/prompts/domain_function_library.py` | `RadicalOps` 類（L158）和 `RADICALOPS_HELPERS` 字串（L619）加入 `simplify_root` 防護方法 |

### 8.3 新增的 Healer 詳細說明

**`regex_healer.py` 新增方法（heal() pipeline 執行順序）：**

| Step | 方法 | 修復的問題 |
|------|------|-----------|
| 2.8 | `fix_hallucinated_methods` | `simplify_root(X)` → `simplify_term(1, X)` |
| 3.2 | `fix_simplify_term_arg_order` | `simplify_term(r1*r2, 1)` → `simplify_term(1, r1*r2)`（radicand=1 永遠返回整數，是大錯）|
| 3.3b | `fix_simplify_term_tuple_as_key` | `root=simplify_term(1, X); final_terms[root]=1` → `new_c, new_r=simplify_term(1, X); final_terms[new_r]+=new_c` |
| 3.4 | `fix_missing_correct_answer` | 有 `final_terms` 但沒有 `correct_answer =` → 自動補加 `correct_answer = format_expression(final_terms)` |
| 3.5 | `fix_shadowed_correct_answer` | 兩行 `correct_answer =` 並存時，保留含 `denominator=` 的行，刪除只傳 `final_terms` 的行 |

### 8.4 prompt_liveshow.md 情境判斷表（Radicals 專用）

| 情境 | 辨識特徵 | 典型例題 |
|------|---------|---------|
| G | 分母有根式，需共軛有理化 | `1/(√3-√2)`, `√2/(3√2+4)` |
| F | 根式直接相乘（無括號）或單根式化簡 | `√8×√45`, `√18`, `√(5³)`, `√2×√3` |
| E | 純分數 × 分子含根式的分數 | `(2/3)×(√3/3)` |
| D | 被開方數為分數結構 | `√A/√B` |
| C | 含 ÷，除數為單一根式 | `(-3√2+√15)÷√3` |
| B | 含 × 且有括號分配律 | `2√3×(√12-√2)`, `(√3+√2)(√6-1)` |
| A | 純加減法 | `2√3+3√3`, `5√10-3√5-2√10+4√5` |

**重要規則：**
- `simplify_term(係數coeff, 被開方數radicand)`：第一個是係數、第二個是被開方數
- `simplify_term(1, r1*r2)` ✓ vs `simplify_term(r1*r2, 1)` ✗
- 原題質數根號（√2,√3）→ 用 `simple=[2,3,5,7,11]`；有完全平方因子（√8,√45）→ 用 `simplifiable=[8,12,18,...]`
- `question_text` 必須有 `$...$` 包裹；題目與答案必須用同一組變數

### 8.5 最低驗證命令
```bash
python -X utf8 -m py_compile core/healers/regex_healer.py core/healers/live_show_healer.py \
  core/prompts/domain_function_library.py
python -X utf8 -m pytest tests/test_live_show_healer_regression.py -q
```

### 8.6 今日進度（2026-03-15）

**根式 Orchestrator：動態項數 term_count + Healer 保護 + Git 衝突清理**

| 項目 | 檔案 | 內容 |
|------|------|------|
| 動態項數 | `core/prompt_architect.py` | RADICAL_V4 改為 3 行輸出：`pattern_id`、`difficulty`、`term_count`；scaffold 傳 `term_count=term_count` 給 `get_safe_vars_for_pattern` |
| | `core/routes/live_show.py` | `_assemble_radical_orchestrator_code` 用 regex 抽取 `term_count`，fallback `None`；decisions 三行；system_prompt 改為 3 行 |
| | `core/domain_functions.py` | `get_safe_vars_for_pattern(..., term_count=None)`；p1_add_sub 時呼叫 `_vars_p1(difficulty, term_count=term_count)`；`_vars_p1` 內 `n_terms = term_count`（≥2）時覆寫 difficulty 預設 |
| Healer 不刪 DomainFunctionHelper | `core/healers/regex_healer.py` | 兩處 `remove_invalid_dependencies`：`from core.* import` 改為負向 lookahead `(?!.*DomainFunctionHelper).*from\s+core\..*\s+import`，含 DomainFunctionHelper 的行不刪 |
| AST 允許 core import | `core/healers/ast_healer.py` | （已具備）`visit_ImportFrom` 的 `safe_modules` 已含 `'core'` |
| Git 衝突清理 | `agent_skills/jh_數學2上_FourOperationsOfRadicals/SKILL.md` | 移除 `<<<<<<<` / `=======` / `>>>>>>>`，保留 DomainFunctionHelper 版，scaffold 改為 3 行 + `term_count`，API 註明 `term_count=term_count` |
| | `agent_skills/jh_數學2上_FourOperationsOfRadicals/prompt_liveshow.md` | 辨識 4、scaffold 範例三行、API 與禁令與 term_count 一致 |

**驗證**：根式題型下，模型看到 2 項（如 `3√2+√8`）可輸出 `term_count=2`，引擎依此生成 2 項，不再被 mid 預設 3 項覆蓋。

### 8.7 今日進度（2026-03-16）

**根式 Hybrid 雙軌修補：Path A / Path B 分流、Aggressive Extractor、Prompt 衝突解除**

| 項目 | 檔案 | 內容 |
|------|------|------|
| Path A 模板改回 3 行輸出 | `agent_skills/jh_數學2上_FourOperationsOfRadicals/SKILL.md` | `🔴 路徑 A` 明確規定：若符合 Pattern Catalogue，只能輸出 3 行純文字宣告 `pattern_id` / `difficulty` / `term_count`；禁止自行寫 `def generate()`、`from ...` |
| Pattern Catalogue 優先權 | `agent_skills/jh_數學2上_FourOperationsOfRadicals/SKILL.md` | 在表前新增「若符合列表結構，務必優先選擇【路徑 A】」說明，避免明明能走 Orchestrator 卻誤走 sympy 自寫程式 |
| Path B 防誤判強化 | `agent_skills/jh_數學2上_FourOperationsOfRadicals/SKILL.md` | 新增「☠️ 生死禁令」：路徑 B 的程式碼與註解嚴禁出現 `pattern_id = `；若需註解，改用 `custom_mode = True`，避免後端 Extractor 誤攔截 |
| Path B 邊界案例模板 | `agent_skills/jh_數學2上_FourOperationsOfRadicals/SKILL.md` | 新增「分數根式 × 負整數」sympy 範例：`\frac{\sqrt{5}}{12} \times (-16)`，固定使用 `sp.Rational(1, den) * sp.sqrt(r) * c`，確保題型同構 |
| Prompt 規則 Hybrid-aware | `core/engine/scaler.py` | 兩處 prompt 字串中的 Rule 4 由「必須包含 generate」改為「依所選路徑輸出：Path A 只需 3 行，Path B 才需完整 generate」，解除底部硬規則與 SKILL.md 的衝突 |
| Smart Wrapper V3 | `core/engine/scaler.py` | 先前加上 df 補丁邏輯：若 AI 寫了 `df.` 卻沒匯入 `DomainFunctionHelper`，會在 `def generate()` 內部補注入，避免 local/global scope 不一致導致 `NameError` |
| Aggressive Extraction | `core/engine/scaler.py` | `[ROOT FIX]` 與 `[UNIVERSAL ORCHESTRATOR FIX]` 改成「只要抓到 pattern id，就直接丟棄 AI 其餘 boilerplate，只萃取 3 個決策變數並重建 golden scaffold」，避免 `if __name__ == "__main__":`、全形字元、雜訊註解污染 |
| Extractor regex 放寬 | `core/engine/scaler.py` | `pattern_id` 偵測由 `pattern_id = "..."` 改為搜尋任何被引號包住的 `p0~p6...` pattern token：`r'["\\'](p[0-6][a-zA-Z0-9_]+)["\\']'`，即使 AI 不是用指定賦值格式也能攔到 |
| Prompt cleanup 後的補洞 | `agent_skills/jh_數學2上_FourOperationsOfRadicals/prompt_liveshow.md`, `core/engine/scaler.py` | 已移除舊的互斥禁令段落，並把 scaler 內對根式題的硬性規則改為允許 Python 計算用 `sp.sqrt()`、但輸出 `question_text` / `correct_answer` 必須是標準 LaTeX |
| p2g / p2h 支援補齊 | `agent_skills/jh_數學2上_FourOperationsOfRadicals/SKILL.md`, `core/domain_functions.py`, `core/solver/radical_solver.py` | Pattern Catalogue 已納入 `p2g_rad_mult_frac` / `p2h_frac_mult_rad`，DomainFunction 與 solver 端也已補上對應生成與求解邏輯 |

**目前判定流程（2026-03-16 版）**

1. AI 若輸出中含任何被引號包住的 `p0~p6...` pattern token，`scaler.py` 直接進 Aggressive Extraction，只保留 `pattern_id` / `difficulty` / `term_count`。
2. 若沒有 pattern token，視為真正的 Path B，保留 AI 的 sympy 程式碼。
3. 若 Path B 程式碼誤用了 `df.` 且沒匯入 helper，Smart Wrapper 會補齊 `DomainFunctionHelper`。

**已知風險 / 明天第一優先驗證**

- Path B 現在依賴「AI 絕不在註解或字串裡提到 `pattern_id = `」；若模型仍偷寫變體字樣，Extractor 仍可能誤判。
- 放寬後的 regex 會把任何被引號包住的 `p0...` token 視為 orchestrator 線索；需確認不會誤打到一般字串常數。
- `RADICAL_V4_SCAFFOLD_PREFIX` 目前仍是全域 `df = DomainFunctionHelper()` 版本；若後續要完全統一路徑，可再決定是否改成函式內注入。

### 8.8 明天從這裡繼續

1. **Live 驗收**：瀏覽器端用根式課本圖（2 項 / 3 項）確認 term_count 辨識與生成項數一致。
2. **Path A / Path B 實機驗收**：至少各測 3 題。
   Path A：`p2g`, `p2h`, `p2c`, `p5a/p5b` 看是否只輸出 3 行後被正確組裝。
   Path B：`\\frac{\\sqrt{5}}{12} \\times (-16)`、一般分數根式混合連乘除，確認不會被 Aggressive Extraction 誤吃掉。
3. **回歸**：`python -X utf8 -m pytest tests/test_live_show_healer_regression.py -q`；必要時跑 `py_compile` 至少覆蓋 `core/engine/scaler.py`、`core/prompt_architect.py`、`core/domain_functions.py`、`core/solver/radical_solver.py`。
4. **若仍有誤判**：優先檢查 `scaler.py` 的放寬 regex 是否抓到非 pattern 用字串，再考慮加入更嚴格上下文 guard。
5. **若仍有 df NameError**：檢查實際執行路徑到底走 `RADICAL_V4_SCAFFOLD_PREFIX`、Aggressive Extraction，還是 Smart Wrapper 補丁分支。
6. **generated_scripts/**：Live Show 新跑仍會持續寫入，可視需要定期清空；正式驗證請以 `tests/` 內 regression 為準。

---

## 9. 歷史修復摘要（僅關鍵清單）

| Bug | 日期 | 修復位置 | 簡述 |
|-----|------|---------|------|
| #8 | 03-09 | `domain_function_library.py` | FractionOps 負數 floor-division 修正 |
| #11 | 03-09 | `evaluate_mcri.py` | SymPy 帶分數 regex 加 `\s*` |
| #12 | 03-09 | `ast_healer.py` | target_funcs 移除 safe_eval |
| #13 | 03-09 | `live_show_healer.py` | enforce_negative_parentheses 掃描延伸至 \frac |
| #14 | 03-09 | `evaluate_mcri.py` | _ForbiddenVisitor class-aware eval 掃描 |
| #15 | 03-09 | `live_show_pipeline.py` | Ab2 加入 optimize_live_execution_code_fn |
| #16 | 03-10 | `live_show_pipeline.py`, `scaler.py` | bare eval() 保底 regex → safe_eval |
| #17-19 | 03-10 | `live_show.py` | classify_input JSON 清理（think 剝除、// 注解、markdown block） |
| #21 | 03-11 | `live_show.py` | greedy regex → raw_decode scan |
| #22 | 03-11 | `live_show.py` | Bug17 fix regex 加 lookbehind 避免二次逃逸 |
| #23 | 03-11 | `live_show.py` | apply_strict_mirroring 加 _skip_abs_block 狀態機 |
| #24 | 03-11 | `live_show_healer.py` | recompute_result_answer 整數技能分數答案拒絕 guard |
| #25 | 03-11 | `live_show_pipeline.py` | FRAC_GUARD：非分數技能有 \frac → fallback |
| #26 | 03-11 | `live_show_pipeline.py`, `live_show.py` | MIXED_GUARD：帶分數/純分數顯示風格與輸入不一致 |
| #27 | 03-11 | `prompt_liveshow.md` Integers, `live_show.py` | 無絕對值輸入→動態禁令 |
| #28 | 03-11 | 4 個 `prompt_liveshow.md` | CoT Step 0 強制結構分析（結構漂移 / math_str 未定義） |
| #29 | 03-11 | `live_show_healer.py` | 絕對值隱含乘法恢復 regex |
| #30 | 03-11 | 4 個 `prompt_liveshow.md` | 加入【致命嚴禁】硬編碼原題數字 |
| #31 | 03-11 | `prompt_liveshow.md` Radicals, `domain_libs.py` | add_dicts / multiply_dicts 防止手寫展開 |
| Radicals-F | 03-14 | `regex_healer.py`, `prompt_liveshow.md` | simplify_term 參數順序反轉 bug |
| Radicals-G | 03-14 | `regex_healer.py`, `live_show_healer.py` | simplify_root 幻覺、missing correct_answer、tuple-as-key、$...$ 自動補加 |
| V3.5 Radical Guard | 03-15 | `regex_healer.py` | remove_invalid_dependencies 負向 lookahead 保護 DomainFunctionHelper import |

---

## 15. 今日下班交接（2026-03-13）

### 15.1 本日已完成（Confirmed ✅）

#### RadicalOps 領域函數抽離與優化
- **目標**：將複雜的根式運算（加減合併、乘法、有理化除法）從 AI 提示詞中抽離，改為調用 `RadicalOps` 標準 API，減輕 Qwen3-8B-VL 的計算負擔。
- **改動檔案**：
  - `core/scaffold/domain_libs.py`：新增 `add_term`、`mul_terms`、`div_terms` 靜態方法。
  - `core/prompts/domain_function_library.py`：同步更新 `RADICALOPS_HELPERS` 字串與 `RadicalOps` 類別，確保生成的程式碼包含這些方法。
  - `agent_skills/jh_數學2上_FourOperationsOfRadicals/`：更新 `SKILL.md`、`prompt_liveshow.md`、`prompt_benchmark.md` 以全面改用新 API。
- **修復 Bug**：
  - **Bug 30**：修復了因 `RadicalOps` 在注入時缺少 `mul_terms` 等方法導致的 `AttributeError`。現在生成的腳本能正確調用新 API 進行根式運算。
- **例題驗算**：
  - 已用本機 `core/scaffold/domain_libs.py::RadicalOps.div_terms` 驗證：`\sqrt{35} \div \sqrt{5}` 會化簡為 `\sqrt{7}`（`(c, r) = (1, 7)`）。

### 15.2 尚待完成（Pending ⏳）

1. **Live 驗收（Radical 題組）**：
   - 雖然已在本地 `py_compile` 與 `regression` 測試通過，但仍需在瀏覽器端針對 `7√2 × 5√2` 等複雜題型進行最後驗收。
   - 確認生成題目的 LaTeX 格式是否符合 8 年級教學規範（例如項數、係數類型是否 100% 同構）。

2. **核心架構維護**：
   - 持續監控 `domain_function_library.py` 與 `domain_libs.py` 的同步狀況，避免未來再次出現「本地有改但注入沒改」的 AttributeError。

### 15.3 接手建議（與下一位 Agent 交接）

1. **環境啟動**：
   - `python app.py`（確保 Ollama 中 `qwen3-vl:8b` 已啟動）。
2. **測試建議**：
   - 使用包含「除法有理化」或「多項分配律」的根式截圖進行測試，觀察 `add_term` 與 `div_terms` 的執行穩定性。
3. **文件參考**：
   - 若遇到 API 遺失錯誤，優先檢查 `core/prompts/domain_function_library.py` 中的字串常數是否已更新。

---

## 16. Agent 執行規範補充 (2026-03-13)

- **自動執行權限**：在執行 `view_file` 或不具破壞性的 `run_command` 時，應主動使用 `SafeToAutoRun: true`，以減少對使用者的審批干擾。
- **注入同步**：修改 `core/scaffold/domain_libs.py` 內的操作類別時，**必須同時**修改 `core/prompts/domain_function_library.py` 的對應字串。
- **技能凍結協議 (Freeze Protocol)**：以下技能已通過完整測試驗收，**嚴禁**修改其關聯檔案與專屬邏輯（包含 `IntegerOps` / `FractionOps` 的現有行為）：
  - `jh_數學1上_FourArithmeticOperationsOfIntegers`
  - `jh_數學1上_FourArithmeticOperationsOfNumbers`
