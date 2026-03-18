# 🧬 Math-Master: Small but Precise (GEMINI.md)

**Project Title:** `Small but Precise: Outperforming Large Models through Engineered Self-Healing`

---

## 1. 核心實驗架構 (Experimental Framework)

### **Ab1 (Native)**
- **定義**: 原生 8B 模式。
- **邏輯**: 不提供 `@SKILL.md` 導引，測試模型的原生隨機性與錯誤率。

### **Ab2 (Scaffold)**
- **定義**: 鷹架引導模式。
- **邏輯**: 注入 `@SKILL.md` 規範，鎖定變數命名與 LaTeX 結構，測試語義對齊。

### **Ab3 (Healed)**
- **定義**: 完整自癒模式。
- **邏輯**: 開啟 **Active Healer** 監控與 **MCRI** 驗證，達成 100% 確定性。

---

## 2. 展示敘事邏輯 (The Live Show Narrative)

- **核心論點**: 證明小型在地化模型 (8B/14B) 透過工程干預 (Scaffold + Healer)，在特定任務上能超越雲端大模型。

- **視覺流程**:
    1. **捕捉輸入**: Handwriting (手寫) / Capture (截圖) / Text (文字).
    2. **基因辨識**: `🧬 Skill DNA Identification` (於右上角白框即時顯示).
    3. **平行對決**: Ab1 vs Ab3 實時生成對比，展示「自癒」過程。

- **算力展示**:
    - 展現 $O(\text{Inference})$ (雲端 API 網路延遲) 與 $O(1)$ (本地 CPU 高速執行) 的脫鉤優勢。

---

## 3. Agent 執行規範 (Strict Guidelines)

- **Codebase 感知**:
    - 生成任何程式碼前必須檢索 `@SKILL.md`，嚴格遵守 `is_first` 邏輯與渲染規範。

- **命名空間**:
    - 嚴格對照 `engine.py` 定義之 `RadicalOps`, `IntegerOps` 等封裝工具類別。禁止隨意自創函式名稱。

- **UI 色系規範 (Visual Identity)**:
    - 🟦 **Gemini (Cloud)**: `#4285F4`
    - 🟨 **Qwen-14B (Local)**: `#F4B400`
    - 🟩 **Qwen-8B (Local)**: `#0F9D58`
    - 🟧 **Active Healer**: `#FF6D00` (用於高亮修復歷史與警報)。

---

## 4. 安全與診斷攔截 (Safety & Diagnostics)

- **教學安全 (Math Safety)**:
    - **禁止** 分母為 0。
    - **禁止** 根號內出現負數。
    - **確保** 整數除法結果符合 K12 教學規範。

- **LaTeX 渲染安全**:
    - **括號策略（2026-03-18 更新）**：題幹端優先使用**標準 LaTeX 括號** `(...)`；由 Healer 負責 token-level 的「負數整項括號」修復與去重。
    - **Healer token 辨識範圍**：已支援在負數整數後延伸掃描 `\\frac{...}{...}` 與 `\\sqrt{...}`，避免像 `(-4\\sqrt{6})` 被誤拆造成重複加括號或括號層級誤升級。
    - 確保所有數學符號通過渲染檢核，避免破圖。

- **Live Show 分設架構 (Hybrid Architecture)**:
    - **OCR & Classification**: 必須由 **Gemini (Cloud)** 執行，確保 100% 辨識準確率。
    - **Practice Generation**: 由 **Qwen (Local)** 執行，展示本地算力與 Healer 修正能力。
    - **禁止** 使用 Qwen 進行初次題目辨識與技能分類，以避免 Live Show 出現分類不準確的風險。

- **數據回傳要求**:
    - 每次生成必須包含 `debug_meta` 物件，內含：`latency_ms` (延遲)、`healer_fix_count` (修復次數) 與 `MCRI_score` (可靠性評分)。

---

## 5. 系統架構現狀 (Current Architecture)

```text
MathProject_AST_Research/
├─ core/
│  ├─ routes/
│  │  ├─ live_show.py          ← API 入口 + 流程編排（Route Orchestration）
│  │  └─ live_show_pipeline.py ← Ab2/Ab3 協調 + output 組裝
│  ├─ healers/
│  │  ├─ live_show_healer.py   ← 題面 sanitize + display/regex/o1/ast fix-count
│  │  ├─ live_show_iso_guard.py← ISO / STYLE guard 決策 + fallback log
│  │  ├─ ast_healer.py
│  │  └─ regex_healer.py
│  ├─ code_utils/
│  │  ├─ live_show_math_utils.py ← 表達式抽取 + 同構比較 + 答案重算
│  │  ├─ math_utils.py
│  │  └─ latex_utils.py
│  ├─ skill_policies/          ← 技能策略 + alias 正規化（Policy Registry）
│  │  ├─ registry.py
│  │  ├─ integer.py / fraction.py / polynomial.py / radical.py
│  │  └─ __init__.py
│  ├─ engine/
│  │  ├─ engine.py             ← MathEngine 總入口
│  │  ├─ classifier.py         ← SkillClassifier（動態掃 agent_skills/）
│  │  └─ scaler.py             ← AdaptiveScaler（JIT 題目生成）
│  └─ scaffold/
│     └─ domain_libs.py        ← IntegerOps / FractionOps / RadicalOps / PolynomialOps 實作
├─ agent_skills/               ← 每個技能目錄（含 SKILL.md）
│  ├─ jh_數學1上_FourArithmeticOperationsOfIntegers/
│  ├─ jh_數學1上_FourArithmeticOperationsOfNumbers/
│  ├─ jh_數學2上_FourArithmeticOperationsOfPolynomial/
│  └─ jh_數學2上_FourOperationsOfRadicals/
├─ templates/live_show.html    ← 前端 UI（Ab1/Ab2/Ab3 平行對決面板）
└─ tests/
   └─ test_live_show_healer_regression.py
```

**關鍵資料流（統一路徑）**  
```
使用者輸入（圖片貼上 或 文字輸入）
    ↓  [/api/classify]
    Qwen3-VL 聯合推理 → ocr_text + skill_id + json_spec（含 operator_fingerprint）
    ↓  前端儲存 resolvedJsonSpec
    ↓  [/api/generate_live]  ← 兩種輸入路徑在此合流
    canonical_ocr_text = json_spec["ocr_text"]（圖片/文字共用同一份）
    → image_monolithic_ab3 路徑（有圖時）  ┐
    → text_engine_ab3 路徑（文字時）       ┘  → 同一套 healer + iso_guard + MCRI
    ↓
    assemble_visual_output → HTTP JSON 回前端
```

---

## 5.1 Prompt 分層架構（必讀：Radicals 已套用）

> 目標：降低 8B 模型壓力，讓 **Path A（Orchestrator）** 走後端引擎、**Path B（Coder）** 只在必要時啟用。

### 三層檔案（Constitution → Civil Law → Procedural Law）

```
agent_skills/<skill_id>/
  SKILL.md             ← Constitution：Pattern Catalogue、辨識規則、difficulty 建議、API/vars 參考（可被 Practice/Quiz 共用）
  prompt_liveshow.md   ← Civil Law：LiveShow delta（Hybrid 分流規則、輸出格式、少量提示；不可塞大量模板）
  prompt_benchmark.md  ← Procedural Law：批次/實驗用結構（保留 Level 1/2/3 code skeleton）
```

### Runtime 組裝（`core/engine/scaler.py`）

- base = `SKILL.md` 在 `=== SKILL_END_PROMPT ===` 前的內容
- delta = `prompt_liveshow.md`（或 benchmark mode 時讀 `prompt_benchmark.md`）
- prompt = `f"{base}\n=== SKILL_END_PROMPT ===\n\n{delta}"`

---

## 5.2 Radicals：Hybrid 雙軌（Path A / Path B）

### Path A（Orchestrator）
- **輸出只允許 3 行**：`pattern_id` / `difficulty` / `term_count`
- 後端會以 pattern_id 走 `DomainFunctionHelper` → `RadicalSolver` 完成出題與解題

### Path B（Coder）
- 只有在「非 catalogue 標準題型、或複雜混合」才用
- 後端 sandbox 已預載 `sympy as sp` 與 `df`（DomainFunctionHelper 實例），降低漏 import 崩潰

---

## 5.3 scaler.py 的防故障機制（Radicals 重點）

### Smart Interceptor（避免綁架 Path B）
- 只有在 **輸出很短** 且 **沒有 `def generate`** 時才把 AI 輸出視為 Path A 決策並強制組裝 scaffold

### Alias Resolver（短別名容錯）
- 支援 `p1`/`p1b`/`p1c`/`p4d`/`p7` 等 short alias → full pattern_id
- 避免 AI 用短別名導致後端拒收

### Circuit Breaker（避免跳針/過長）
- 只對 **Path B（非 scaffold）** 生效，偵測到重複或異常過長就 fallback 到 emergency generate code

---

## 5.4 Radicals：後端單一真相（Source of Truth）

- **題型識別與變數生成**：`core/domain_functions.py`（`DomainFunctionHelper.get_safe_vars_for_pattern`）
- **題面格式化（LaTeX）**：`DomainFunctionHelper.format_question_LaTeX`
- **求解**：
  - 大多數 pattern：走 `core/math_solvers/radical_solver.py::RadicalSolver.solve_problem_pattern`
  - 少數顯示/格式高度敏感 pattern：由 `DomainFunctionHelper.solve_problem_pattern` 直接攔截並回傳 deterministic 詳解（例如 `p2f_int_mult_rad`、`p2g/p2h`、`p4_frac_mult`），避免舊 solver 或 LLM 產生破壞前端的非標準 LaTeX。

**架構決策（2026-03-18 更新）**
- **Orchestrator 路徑不依賴 SymPy**：Path A（pattern catalogue → DomainFunctionHelper/RadicalSolver）以 `RadicalOps`/`FractionOps` 的 deterministic API 完成出題、排版與求解。
- SymPy 僅保留作為 Path B（Coder）沙盒的可選工具，用於非 catalogue 的極端混合題；但展示/教學主路徑以「可控、可重現、可追溯」為最高優先。

目前 Radicals 已新增並落地的擴充 pattern（範例）：
- `p7_mixed_rad_add`（帶分數根式加減）
- `p4d_frac_rad_div_mixed`（(a/√b)÷(√c/√d)）
- `p1b_add_sub_bracket`（帶括號加減）
- `p1c_mixed_frac_rad_add_sub`（a/√b ± (c/d)√b）

> 後續要做「多項式四則」請沿用同樣方法：先在 `SKILL.md` 定義 catalogue + vars，再在 `DomainFunctionHelper` / solver 端落地，最後接上 scaler 的 alias/valid_id。

## 6. 修改優先序與執行計畫 (Roadmap)

### Phase 0 — 已完成項目 ✅

| 完成日期 | 項目 |
|---|---|
| 2026-03-06 | `live_show.py` 改為 Route Orchestration，複雜邏輯下沉到 pipeline / healer |
| 2026-03-06 | `live_show_pipeline.py` 新增，承接 Ab2/Ab3 協調與 output 組裝 |
| 2026-03-06 | `core/skill_policies/` 建立，技能策略與 alias 由 registry 統一管理 |
| 2026-03-06 | Healer fix-count 分帳（Code / Display / AST / O1）可追溯 |
| 2026-03-06 | Payload validity gate + emergency fallback（防 timeout / hallucination） |
| 2026-03-06 | SKILL.md 加入 fail-fast prompt contract（`/no_think`、banned tokens） |
| 2026-03-09 | **圖片貼上與文字輸入統一執行路徑**：classify 寫入 `json_spec["ocr_text"]`，generate_live 以 `canonical_ocr_text` 為單一來源，前端 `resolvedJsonSpec` 轉發 |

---

### Phase 1 — ✅ 已完成（P0，零破壞性）— 2026-03-09

**目標：修正現有 agent skill 架構的已知缺陷，改善 Qwen3 8B 輸出率。**

| 序號 | 檔案 | 動作 | 理由 | 狀態 |
|---|---|---|---|---|
| 1-A | `agent_skills/jh_數學1上_FourArithmeticOperationsOfNumbers/SKILL.md` | 移除最外層的 ` ```skill ` 破損 code fence | 模型看到後以為自己在 code block 內，role/task 文字解讀混亂 | ✅ |
| 1-B | 所有 4 個 `SKILL.md` | `/no_think` 統一放在第一行 | Qwen3 需要在 prompt 最開頭才能可靠壓制 thinking mode | ✅ |
| 1-C | 每個 `agent_skills/<id>/` | 新增 `skill.json` manifest | 建立單一 source of truth，解除 registry 硬編碼依賴 | ✅ |
| 1-D | Polynomial + Radicals `SKILL.md` | 補充完整 `[[MODE:LIVESHOW]]` section（含可運行範例程式碼） | Qwen3 8B 需要具體程式範例才能正確實作 | ✅ |
| 1-E | Integers + Numbers `SKILL.md` | 移除 Integers ` ```python ` 外層 fence | 同 1-A 原因 | ✅ |

`skill.json` 標準格式：
```json
{
  "skill_id": "jh_數學1上_FourArithmeticOperationsOfIntegers",
  "display_name": "整數四則運算",
  "family": "integer",
  "level_range": [1, 3],
  "injected_apis": ["IntegerOps"],
  "required_imports": ["random", "math"],
  "modes": ["BENCHMARK", "LIVESHOW"],
  "vision_input": false,
  "aliases": ["Arithmetic", "IntegerArithmetic"],
  "schema_version": "1.0"
}
```

---

### Phase 2 — ✅ 已完成（P1，中等工程量）— 2026-03-09

**目標：讓 registry 自動從 `skill.json` 載入，新技能加入不再需要改 `.py`。**

| 序號 | 檔案 | 動作 | 狀態 |
|---|---|---|---|
| 2-A | `core/skill_policies/registry.py` | 新增 `_load_from_manifests()` 自動掃 `skill.json`，與現有 POLICIES 合併 | ✅ |
| 2-B | `core/engine/classifier.py` | 優先讀 `skill.json["skill_id"]` 作為 available_skills，不再只依賴目錄名 | ✅ |

驗收步驟：
```bash
python -c "from core.skill_policies import normalize_skill_id; print(normalize_skill_id('Arithmetic'))"
# 預期：jh_數學1上_FourArithmeticOperationsOfIntegers
```

---

### Phase 3 — ✅ 已完成（P2，需要 scaler 改動）— 2026-03-09

**目標：SKILL.md 模式分割，降低 Qwen3 prompt 長度 50%（目標 ≤ 2048 tokens/call）。**

| 序號 | 動作 | 狀態 |
|---|---|---|
| 3-A | 每個 skill 目錄新增 `prompt_liveshow.md` 與 `prompt_benchmark.md`（由 SKILL.md 自動拆分產生） | ✅ |
| 3-B | `core/engine/scaler.py` 新增 `_load_skill_prompt(skill_path, mode)` 優先讀 mode-specific 檔，fallback 到 SKILL.md 切割 | ✅ |
| 3-C | Ab3 路徑現在使用 `prompt_liveshow.md`（含 `/no_think` + 規則 + LIVESHOW 範例程式碼），不再只走 BENCHMARK section | ✅ |

---

### Phase 4 — ✅ 已完成（P3，Qwen3-VL 視覺能力完整接入）— 2026-03-09

**目標：正式宣告視覺 skill，讓 Qwen3-8B-VL 的多模態能力有規範的接入路徑。**

| 序號 | 動作 | 狀態 |
|---|---|---|
| 4-A | `scaler.py` 新增 `_get_skill_vision_input()` 讀 `skill.json["vision_input"]`；新增 `_call_ai_vision()` 多模態 API 路徑；Ab3 路徑自動路由 | ✅ |
| 4-B | `_inject_domain_libs(code_str, skill_id=None)` 加入 skill_id 參數，讀 `skill.json["injected_apis"]` 防止靜默失敗 | ✅ |
| 4-C | `/api/run_generated_code` 接收 `json_spec`，補充 `source_ocr_text`；response 回傳 `json_spec` 供前端下一題連鎖使用 | ✅ |

---

## 7. 新技能接入 SOP（Policy-Only）

> 目標：新增技能時，**不改** `live_show.py`／healer 主流程，只透過檔案接軌。

```
Step 1) 建立目錄 agent_skills/<skill_id>/
Step 2) 新增 skill.json（填 family / aliases / injected_apis）
Step 3) 新增 SKILL.md（/no_think 置頂，分 SKILL_END_PROMPT / LIVESHOW 兩段）
Step 4) 在對應 core/skill_policies/<family>.py 加入 skill_id
Step 5) 驗證正規化：
        python -c "from core.skill_policies import normalize_skill_id; print(normalize_skill_id('<alias>'))"
Step 6) Compile check：
        python -m py_compile core/skill_policies/__init__.py core/routes/live_show.py
Step 7) 回歸測試：
        python tests/test_live_show_healer_regression.py
```

---

## 8. 開發守則提醒 (Agent Guidelines)

- **新增技能策略**：改 `core/skill_policies/<family>.py`，不動 `live_show.py`。
- **修改 healer 行為**：改 `core/healers/`，不在 route 加硬編碼。
- **新增 OCR text 處理**：在 `/api/classify` 內做，不在 `generate_live` 重複處理。
- **任何改動後**：`python -m py_compile core/routes/live_show.py` + `python tests/test_live_show_healer_regression.py`。