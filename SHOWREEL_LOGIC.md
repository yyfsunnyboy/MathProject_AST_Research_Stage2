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

### 8.9 今日進度（2026-03-17）

**根式技能（Radicals）Prompt/Extractor/Pattern 全面同步與穩定化**

| 類別 | 檔案 | 更新重點 |
|------|------|----------|
| Prompt 分層重構 | `agent_skills/jh_數學2上_FourOperationsOfRadicals/SKILL.md` / `prompt_liveshow.md` / `prompt_benchmark.md` | 形成「Constitution → Civil Law → Procedural」三層：SKILL.md 只保留角色、Pattern Catalogue、辨識優先規則、difficulty 建議、API/vars 參考；LiveShow 只放 Hybrid 分流與格式；Benchmark 保持 Level 1/2/3 並避免重複定義 Catalogue。 |
| LiveShow Prompt 壓力下降 | `agent_skills/.../prompt_liveshow.md` | 移除過長 Few-shot 與恐嚇式禁令，改為精簡規則；為維持路徑 A 一致性，加入「與 SKILL.md 同步」的完整 Pattern Catalogue 表與純加減防護網；確保 `p1b`/`p1c` 規則明確。 |
| 新增 Path A 題型（解決誤分類） | `SKILL.md` / `core/domain_functions.py` / `core/math_solvers/radical_solver.py` | 新增並落地：`p7_mixed_rad_add`（帶分數根式加減）、`p4d_frac_rad_div_mixed`（(a/√b)÷(√c/√d)）、`p1b_add_sub_bracket`（帶括號加減）、`p1c_mixed_frac_rad_add_sub`（a/√b ± (c/d)√b）。各 pattern 完整包含 vars 生成、格式化、求解（部分採 Sympy 特判）。 |
| Extractor 防誤判 + Alias Resolver | `core/engine/scaler.py` | Smart Interceptor 僅在短輸出且無 `def generate` 時才強制 Scaffold；pattern_id 偵測改成 anchor 在行首的 `pattern_id = ...`；加入 alias_map（p1/p1b/p1c/p4d/p7…）與合法 ID 校驗，避免假 pattern_id 綁架 Path B。 |
| Circuit Breaker 穩定化 | `core/engine/scaler.py` | Circuit Breaker 只在 Path B（非 Scaffold）時生效；並避免 Scaffold 內建 `pattern_id` 字串造成誤觸發（以 raw output / scaffold 特徵 bypass）。 |
| Sandbox 閉環環境 | `core/engine/scaler.py` | `_execute_code` 預載 `sp`/`sympy` 與 `df`（DomainFunctionHelper 實例）到 exec_globals，降低 LLM/Healer 漏 import 造成的 NameError。 |
| LaTeX 顯示修復 | `core/domain_functions.py` | 修復 `p4b/p4c` raw f-string 反斜線輸出問題；新增 `_fmt_term`，並重寫 `p2b/p2c` formatter 讓負係數更自然（`-2\\sqrt{7}` 取代 `(-2)\\sqrt{7}`）。 |
| 前端選單對齊 presets | `templates/live_show.html` | Ab1/Ab3 下拉只保留 `pause`/`gemini-3-flash`/`qwen3-vl-8b`；Phase 4 boot logs 依 model 顯示 Gemini(藍) / Qwen(綠) badge 與名稱。 |

### 8.10 今日進度（2026-03-18）

**分數 × 根式排版全面教材化（Healer 與 DomainFunction 同步）**

| 類別 | 檔案 | 更新重點 |
|------|------|----------|
| Healer：負數括號修復升級 | `core/healers/live_show_healer.py` | `enforce_negative_parentheses()` 在原本「數字後緊接 `\\frac{...}{...}`」的 token 延伸掃描後，新增「數字後緊接 `\\sqrt{...}`」延伸掃描。目的：遇到 `(-4\\sqrt{6})` 時能把 `-4\\sqrt{6}` 視為單一 token，正確判斷 already_wrapped，避免重複加括號或括號層級被誤升級。 |
| DomainFunction：p2f 題幹與詳解一致 | `core/domain_functions.py` | `p2f_int_mult_rad` 題幹與 `solve_problem_pattern` 的 `step1` 皆改為標準 LaTeX（負係數根式整項括號：`({raw_t2})`），並依賴 Healer 新的 `\\sqrt{...}` token 辨識來避免誤判。 |
| DomainFunction：新增排版工具（分子帶根號） | `core/domain_functions.py` | 在 `DomainFunctionHelper` 內新增 `_format_single_fraction_radical(coeff, r)`：把分數係數根式強制排成「分子帶根號」形式（例：`\\dfrac{3\\sqrt{7}}{4}`），供題幹與詳解共用。 |
| DomainFunction：攔截分數題型求解（避免舊 solver/格式破壞） | `core/domain_functions.py` | `solve_problem_pattern()` 新增攔截：`p2g_rad_mult_frac`、`p2h_frac_mult_rad`、`p4_frac_mult`，以 `RadicalOps.format_expression(..., denominator=...)` 產生答案並回傳固定的兩步教材式詳解（分子相乘、分母相乘），確保前端顯示一致且可控。 |
| Prompt 注入 mapping | `core/prompts/domain_function_library.py` | `SKILL_DOMAIN_MAPPING['FourOperationsOfRadicals']` 由 `['radicalops']` 擴充為 `['radicalops','fractionops']`，使根式技能在 scaffold 注入時同時擁有 FractionOps（讓 RadicalOps 產生分數 LaTeX 時可穩定呼叫）。 |

**今日結論（重要決策）**
- Orchestrator（Path A / DomainFunctionHelper / RadicalSolver）方向：**優先以 RadicalOps/FractionOps 的 deterministic API 完成出題/排版/求解**，避免把版面控制丟回 LLM 或 SymPy。
- 括號/排版策略：題幹端維持標準 LaTeX，Healer 負責 token-level 的「負數整項括號」修復，並已擴充到 `\\sqrt{...}`。

### 8.11 今日進度（2026-03-19）

**主題：Live Show 根式單元「分類前置 → Monolithic Orchestrator → Healer」實戰修正與壓測對齊**

| 類別 | 檔案 | 今日最終狀態 |
|------|------|-------------|
| 壓測流程對齊 UI | `tests/comprehensive_stress_test.py` | 改為兩階段：先打 `/api/classify`，再用回傳 `ocr_text/json_spec/skill_id` 打 `/api/generate_live`；HTML 報表新增 classify 資訊與 cls/gen 耗時。 |
| 壓測 classify 輸入 | `tests/comprehensive_stress_test.py` | `build_classify_text_data` 最終改為**只送純算式**：`"${safe_expr}$"`（拔除中文敘述干擾）。 |
| 壓測 normalize 行為 | `tests/comprehensive_stress_test.py` | 已刪除「把 classify 的 ocr_text 強制洗回 math_expr（條件式重置）」那段；僅保留 `if not ocr_text` fallback。 |
| 根式統一路徑 | `core/routes/live_show.py` | 根式 skill（`FourOperationsOfRadicals`）在 Ab3 下可走 monolithic 編排（含 `text_monolithic_ab3` / `image_monolithic_ab3`）；payload 動態加 `images`，避免 `None` 造成上游 API 問題。 |
| 根式分類 Prompt | `core/routes/live_show.py` | Radical prompt 多次迭代後，最終採「4 行輸出 + 結構觀察」版本：`structure_analysis` + `pattern_id` + `difficulty` + `term_count`，並強化分數/單根式誤判警告。 |
| Orchestrator scaffold 組裝 | `core/routes/live_show.py` | 目前保持簡化版：根式分支直接 `_assemble_radical_orchestrator_code(final_code)`，不再做額外 pattern 強制覆寫。 |
| UI 同構顯示真實化 | `core/routes/live_show_pipeline.py` | Radical 分支移除 `iso_isomorphic=True` 硬綁，改為 `_build_radical_profile` + `_is_radical_isomorphic(expected_fp, generated_expr_final)` 真實比對。 |
| Regex Healer 防護 | `core/healers/regex_healer.py` | `apply_professor_strong_meds` 的 safe injection 升級為終極版：先替 `{text}`→`{_math_str_fb}`，再注入 `_math_str_fb/question_text/correct_answer` 防護塊。 |

#### 8.11.1 今天實際踩到的關鍵問題

1. `classify` 偶發回傳 `skill_id=Unknown`，且 `ocr_text` 夾帶整段提示語，導致 `generate_live` 回 `HTTP 400`。  
2. 根式 prompt 若含 `<VALUE>` 佔位字，模型容易照抄模板而非真分類。  
3. UI 曾把 Radical 同構結果強制標綠（`iso_isomorphic=True`），造成誤導，已改為真比對。  
4. `regex_healer` 在 `text` 變數幻覺情境可能出現 NameError 或題幹缺 `$`，已補注入防護。  

#### 8.11.2 目前建議的「下次啟動順序」

1. 啟動服務：`python app.py`（確認 Ollama 模型可用）。  
2. 先跑小樣本（3~5 題）`tests/comprehensive_stress_test.py`，看 classify 是否仍出現 Unknown。  
3. 再跑全量 42 題，檢查：
   - Unknown 比率（是否需要在 `/api/classify` 再加 guard）  
   - `pattern_id` 是否仍常落到過粗類別（例如把分數根式乘法判成一般乘法）  
   - `iso_isomorphic` 是否與實際題幹骨架一致  
4. 若分類仍漂移，優先調整 `core/routes/live_show.py` 的 radical `system_prompt`，其次才調 Healer。  

#### 8.11.3 待完成事項（下次從這裡接）

- [ ] **A. classify 穩定性治理**：在 `/api/classify` 增加針對 Radical 的最小後處理（例如偵測 `\\sqrt`/`\\frac` 特徵後限制可選 skill 範圍），降低 `Unknown`。  
- [ ] **B. prompt A/B 驗證**：比較「4 行 CoT 版」vs「3 行極簡版」在真實題組的 pattern 命中率。  
- [ ] **C. 壓測報表加欄**：統計 `skill fallback` 次數、`iso_isomorphic` 通過率、pattern 分布。  
- [ ] **D. 回歸測試補件**：新增針對 Radical monolithic 的 smoke test（至少覆蓋：單根式化簡、分配律、分數根式乘除、有理化）。  
- [ ] **E. 文檔清理**：將 8.9/8.10/8.11 的重複口徑收斂成「現行生效規則」單一章節，避免交接誤讀。  

### 8.12 銜接筆記（2026-03-20）：「讀題後對不到預設題型」與 SHOWREEL_LOGIC 的易混點

**先釐清**：Live Show 執行路徑**不會**讀取專案根目錄的 `SHOWREEL_LOGIC.md`。該檔僅供人類／Agent 交接。實際注入模型的內容來自 `agent_skills/<skill_id>/` 下的 `prompt_liveshow.md`（優先）與 `SKILL.md`（base），見 `core/routes/live_show.py`（`/api/classify` 預覽與 `/api/generate_live` monolithic 分支）。

**為何會覺得「抓錯」**（與預設／預期題型不一致時）：

| 環節 | 行為 | 相關程式位置 |
|------|------|----------------|
| 辨識技能 | VL 回傳的 `skill_id` 經 `normalize_skill_id`；若對應資料夾不存在 → 強制 `Unknown` | `live_show.py` `/api/classify` |
| 根式安全閥 | 已判為根式技能，但 OCR 只有 `\frac` 等、**沒有** `\sqrt`／根號特徵 → 可改判到分數技能 | `_apply_skill_safety_guard()` |
| 壓測腳本 | `classify` 若為 `Unknown`，腳本可後備成固定 `FALLBACK_SKILL_ID`（預設根式），與「純 UI 流程」不同 | `tests/comprehensive_stress_test.py` → `normalize_classify_result` |
| Unknown 後 | `scaffold_prompt` 改為短句防禦文案，**不是**某個技能的完整 SKILL | `live_show.py` `/api/classify` `skill_name == "Unknown"` 分支 |

**昨天進度停在**：已把「兩階段 classify → generate」與純算式輸入等行為寫入 §8.11；若接下來要處理「預期根式卻被判分數／Unknown」，優先檢查上表三列，再決定要改 classify prompt、放寬或調整 `_apply_skill_safety_guard`，還是 UI 上允許**手動鎖定 skill**（目前 Live Show 以 classify 結果為準）。

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

---

## 17. 今日進度交接（2026-03-20）

### 17.1 今日修改方向（Radicals-only）

- 目標聚焦在 `jh_數學2上_FourOperationsOfRadicals`：
  - 強化 style/mirror 最終一致性。
  - 新增 mirror tolerance（`p2a_mult_direct` 條件容忍）。
  - 新增 quality gate（single-problem / anti-echo / operator-lock）。
  - 加入公式級 pattern detector（優先使用 SKILL.md 已定義題型）。
  - 不更動 Integers / Numbers 的既有 mirror、guard、pattern、fallback 規則。

### 17.2 已完成成果（Completed ✅）

1. **Radicals mirror comparator**
   - 新增 `radical_complexity_mirror_compare(...)`，含 `p2a_mult_direct` 輕量容忍：
     - `style_preserved=True`
     - 乘法骨架
     - `fraction_count` 不變
     - `bracket_depth` 不惡化
     - `rad_count` 差異 `<=1`
   - `debug_meta` 已新增：
     - `mirror_tolerance_applied`
     - `mirror_tolerance_reason`

2. **Radicals quality gate**
   - `run_ab3_full_healer` 已掛入 Radicals-only gate：
     - `single_problem_violation`
     - `empty_expr_violation`
     - `echo_violation`
     - `operator_lock_violation`
   - 失敗後先做同 pattern anti-echo retry，再強制 deterministic fallback。
   - `debug_meta` 已新增：
     - `quality_gate_passed`
     - `quality_gate_reasons`
     - `anti_echo_retry_used`
     - `anti_echo_similarity`

3. **Pattern detector 高優先**
   - `apply_radical_pattern_p1_guard` 已補公式級判斷（先於 `\times/\div` 粗分流）：
     - `(A±B)^2 -> p2d_perfect_square`
     - `(A-B)(A+B) -> p2e_diff_of_squares`
     - `1/(b√q±c) -> p5a_conjugate_int`
     - `p√m/(b√q±c) -> p5b_conjugate_rad`
     - `√(a/b)×√(c/d)÷√(e/f) -> p4c_nested_frac_chain`
     - `(a/√b)÷(√c/√d) -> p4d_frac_rad_div_mixed`
   - 並新增 signals：`decimal_root`、`power_root`（禁止 `p1_add_sub`）。

4. **Style gate 對齊**
   - `RADICAL_STYLE_PATTERN_MAP` 已擴充：
     - `simple_radical` 至少允許 `p2c/p2d/p2e`
     - `simplifiable_radical` 允許 `p2d/p2e`
   - 目標是避免公式 pattern 被 style gate 回退到 `p1/p2a`。

5. **Exemplar anti-echo（Radicals-only）**
   - 已新增 `RADICAL_EXEMPLAR_POOL` 與 exemplar echo retry。
   - `debug_meta` 已新增：
     - `exemplar_echo_hit`
     - `exemplar_echo_retry_used`

6. **壓測腳本強化**
   - `tests/comprehensive_stress_test.py` 已新增 fail 檢查：
     - `single_problem_violation`
     - `echo_violation`
     - `operator_lock_violation`
   - 新增 pattern family 驗收：
     - `(√3+2√2)^2` 必須 `p2d family`
     - `(√3-2√2)(√3+2√2)` 必須 `p2e family`
     - `1/(√3-√2)` 必須 `p5a family`

### 17.3 當前驗證結果（截至本次）

- `python -m pytest tests/test_live_show_non_radical_regression.py -q`
  - 結果：`2 passed, 1 skipped`
  - 非 Radicals 回歸未退化（符合凍結原則）。

- `python tests/comprehensive_stress_test.py`（42 題）
  - 最新結果仍未達標（約 `35~36 / 42`）。
  - 仍有固定缺口：
    - 多題 Ab3 出現 `name 'IntegerOps' is not defined` 後轉為空輸出（#1/#12/#18/#26/#32 類）。
    - `#10` style drift（simple -> fraction）。
    - `#41` 仍有 `pattern_family_violation:p5a_required`（代表 `1/(√3-√2)` 仍偶發未鎖到 p5a）。

### 17.4 待完成 / 待測試（Tonight TODO）

1. **先修 Ab3 的 IntegerOps 缺口（最高優先）**
   - 將 Ab3 所有 execute/fallback 路徑統一走同一執行入口（含 `api_stubs`）。
   - 目標：清掉 `name 'IntegerOps' is not defined` 與空題幹連鎖。

2. **強化 p5a 鎖定**
   - 對 `\frac{1}{\sqrt{...}\pm...}` 再補一層 hard lock（guard/style gate 雙保險）。
   - 目標：`#41` 必須穩定命中 `p5a family`。

3. **再跑完整驗證**
   - `python tests/comprehensive_stress_test.py`
   - `python -m pytest tests/test_live_show_non_radical_regression.py -q`
   - 驗收目標：`>=41/42`（理想 `42/42`）、`#18/#40` 無空輸出、`#32` 雙題合併被擋下。
