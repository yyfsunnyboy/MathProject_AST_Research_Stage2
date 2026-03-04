# 🎭 Math-Master Live Show 劇本邏輯與重構後架構

**核心宗旨**: 透過工程干預（Scaffold + Healer + Policy Registry）讓小型在地模型在教學情境中穩定可控。

## ⚡ 30 秒交接摘要（先看這裡）

- 這個專案已改成分層架構：Route 編排、Pipeline 協調（Ab2/Ab3 + output 組裝）、Healer 修復、Code Utils 結構分析、Skill Policy Registry 策略管理。
- 不要在 route 新增硬編碼 skill mapping；技能策略與 alias 一律進 policy registry。
- 改技能行為優先順序：policy 檔 → healer/code_utils → 最後才 route。
- 修補計數必須可追溯（Code / Display / AST / O1）。
- 每次修改後至少跑 compile 與 `tests/test_live_show_healer_regression.py`。
- 新技能接入原則：優先 policy-only；只有規則不足才擴充 healer/code_utils。

---

## 1. 最新系統分層（重構後）

### A. Route Orchestration
- `core/routes/live_show.py`
- 職責：API 入口與流程編排（偏 orchestration），主要負責請求解析與呼叫 pipeline helper。
- 原則：避免放複雜規則，規則改下沉到 `healers` / `code_utils` / `skill_policies`。

### B. Pipeline Coordination（新增）
- `core/routes/live_show_pipeline.py`
- 職責：
    - `run_ab2_interception(...)`：Ab2 快速執行與 guard/fallback
    - `run_ab3_full_healer(...)`：Ab3 完整 healer/guard/fallback/MCRI/trace
    - `assemble_visual_output(...)`：集中組裝 `output/debug_meta`

### C. Healer Layer（可追溯修復）

### D. Math/Structure Utilities
- `core/healers/live_show_healer.py`
- `core/healers/live_show_iso_guard.py`
- 職責：
    - 題面 sanitize（display 清理）
    - regex/display/o1/ast fix-count 分帳
    - 可讀化 healer log
    - ISO / STYLE guard 決策與 fallback log

### E. Skill Policy Registry（新）
- `core/code_utils/live_show_math_utils.py`
- 職責：表達式抽取、結構指紋、同構比較、答案重算等通用計算工具。

- `core/skill_policies/registry.py`
- family policies:
    - `core/skill_policies/fraction.py`
    - `core/skill_policies/integer.py`
    - `core/skill_policies/polynomial.py`
    - `core/skill_policies/radical.py`
- 職責：
    - 技能策略開關（是否套 fraction eval patch、是否啟用 fraction display、是否強制分數答案）
    - skill alias 正規化（`normalize_skill_id`）

---

## 2. 目前核心目錄結構（摘要）

```text
MathProject_AST_Research/
├─ core/
│  ├─ routes/
│  │  ├─ live_show.py
│  │  ├─ live_show_pipeline.py
│  │  └─ ...
│  ├─ healers/
│  │  ├─ live_show_healer.py
│  │  ├─ live_show_iso_guard.py
│  │  ├─ ast_healer.py
│  │  ├─ regex_healer.py
│  │  └─ ...
│  ├─ code_utils/
│  │  ├─ live_show_math_utils.py
│  │  ├─ math_utils.py
│  │  ├─ latex_utils.py
│  │  └─ file_utils.py
│  ├─ skill_policies/
│  │  ├─ registry.py
│  │  ├─ fraction.py
│  │  ├─ integer.py
│  │  ├─ polynomial.py
│  │  ├─ radical.py
│  │  └─ __init__.py
│  ├─ engine/
│  └─ scaffold/
├─ tests/
│  ├─ test_live_show_healer_regression.py
│  └─ ...
├─ generated_scripts/
└─ SHOWREEL_LOGIC.md
```

---

## 3. Live Show Pipeline（展示敘事）

1. **感知層**：影像/文字輸入 + skill DNA 分類
2. **Scaffold 注入**：根據 skill 與結構約束生成 prompt
3. **Ab1 原生推論**：展示模型原始輸出
4. **Ab2 執行攔截**（pipeline）：快速執行 + guard/fallback 最小干預
5. **Ab3 完整自癒**（pipeline）：healer + guard + 結構一致性驗證 + MCRI
6. **Output 組裝**（pipeline）：集中產生 `output/debug_meta`
7. **Route 回傳前端欄位整平**：統一前端使用欄位

---

## 4. 本次大改版重點（供簡報）

- `live_show.py` 從巨型規則檔，改為「路由編排器」
- 新增 `live_show_pipeline.py`，承接 Ab2/Ab3 協調與 output 組裝
- Healer 修復責任集中到 `core/healers/*`
- 同構分析與答案重算集中到 `core/code_utils/live_show_math_utils.py`
- 新增 `core/skill_policies/*`，技能策略與 alias 正規化由 registry 統一管理
- 後續新增技能：原則上新增/調整 policy 檔即可接軌

---

## 5. 驗證基線（當前）

- 回歸測試：`tests/test_live_show_healer_regression.py`（fix count / log / guard）
- 編譯檢查：至少覆蓋 `core/routes/live_show.py`、`core/routes/live_show_pipeline.py`

---

## 6. UI 視覺回饋規範

- 正常輸出：綠色漸層 `#0F9D58`
- Healer 介入：橘色 `#FF6D00`
- 錯誤偵測：紅色 `#D93025`
- 背景：實驗室精密網格風格

---

## 7. 新技能接入 SOP（Policy-Only）

> 目標：**新增技能時，盡量不改 `live_show.py`／healer 主流程**，只透過 policy 檔接軌。

### Step 1) 決定技能歸屬 family

- 若是分數類：放 `fraction.py`
- 若是整數類：放 `integer.py`
- 若是多項式類：放 `polynomial.py`
- 若是根號類：放 `radical.py`
- 若是全新 family：新增一個新的 policy 檔（例如 `geometry.py`）

### Step 2) 在 policy 檔加入 skill 設定

每個 policy 至少包含：

- `policy_id`
- `family`
- `skill_ids`
- `aliases`
- `apply_fraction_eval_patch`
- `enable_fraction_display`
- `force_fraction_answer`
- `fallback_fraction_style`

範例（節錄）：

```python
POLICIES = [
    {
        "policy_id": "integer-core",
        "family": "integer",
        "skill_ids": ["jh_數學1上_FourArithmeticOperationsOfIntegers"],
        "aliases": ["Arithmetic", "IntegerArithmetic"],
        "apply_fraction_eval_patch": False,
        "enable_fraction_display": False,
        "force_fraction_answer": False,
        "fallback_fraction_style": False,
    }
]
```

### Step 3) 驗證 skill 正規化是否生效

```bash
python -c "from core.skill_policies import normalize_skill_id; print(normalize_skill_id('Arithmetic'))"
```

預期：輸出對應 canonical `skill_id`。

### Step 4) 編譯檢查

```bash
python -m py_compile core/skill_policies/__init__.py core/skill_policies/registry.py core/routes/live_show.py core/healers/live_show_healer.py
```

### Step 5) 回歸測試

```bash
python tests/test_live_show_healer_regression.py
```

### Step 6) 驗收清單（PR Checklist）

- [ ] 新技能 `skill_id` 已加入對應 policy 檔
- [ ] alias 能正規化到 canonical `skill_id`
- [ ] 不需修改 `live_show.py` 的硬編碼 mapping
- [ ] `py_compile` 通過
- [ ] 回歸測試通過

### 例外情況（需要動 code）

若新技能需要**全新數學顯示規則或 guard 指紋規則**，才應修改：

- `core/healers/live_show_healer.py`（顯示/答案策略）
- `core/code_utils/live_show_math_utils.py`（結構分析策略）

原則：先 policy，後程式。

---

## 8. AI 交接快速上手（給下一位 Agent）

### 8.1 10 分鐘上手路線

1. 先看本文件第 1、2、4、7 節（架構 + 目錄 + 變更重點 + SOP）。
2. 聚焦三個核心入口：
     - `core/routes/live_show.py`（流程編排）
    - `core/routes/live_show_pipeline.py`（Ab2/Ab3 + output 組裝）
     - `core/healers/live_show_healer.py`（修復與分帳）
     - `core/skill_policies/registry.py`（技能策略與 alias 正規化）
3. 任何技能行為異常，先查 policy，再查 healer，最後才改 route。

### 8.2 必看檔案（優先序）

- P0（一定先讀）
    - `SHOWREEL_LOGIC.md`
    - `core/routes/live_show.py`
    - `core/routes/live_show_pipeline.py`
    - `core/skill_policies/registry.py`
    - `core/healers/live_show_healer.py`
- P1（需要時）
    - `core/healers/live_show_iso_guard.py`
    - `core/code_utils/live_show_math_utils.py`
    - `tests/test_live_show_healer_regression.py`

### 8.3 當前架構約定（不要破壞）

- Route 只做 orchestration，不承擔複雜規則。
- Ab2/Ab3 協調與 `output/debug_meta` 組裝優先放在 pipeline helper，不回塞 route。
- skill-specific 行為一律走 policy（避免在 route/healer 寫硬編碼 skill_id）。
- fix count 採分帳：Code / Display / AST / O1，需可追溯。
- 同構檢查與 fallback log 必須保留，不能靜默吞掉。

### 8.4 典型開發出手順序

1. 先判斷是「策略問題」還是「演算法問題」。
2. 策略問題：改 `core/skill_policies/*`。
3. Ab2/Ab3 協調或 output 組裝問題：先改 `core/routes/live_show_pipeline.py`。
4. 顯示/答案問題：改 `core/healers/live_show_healer.py`。
5. 結構同構/答案重算問題：改 `core/code_utils/live_show_math_utils.py`。
6. 最後才碰 `core/routes/live_show.py`。

### 8.5 最低驗證命令（每次改完必跑）

```bash
python -m py_compile core/routes/live_show.py core/routes/live_show_pipeline.py core/healers/live_show_healer.py core/healers/live_show_iso_guard.py core/code_utils/live_show_math_utils.py core/skill_policies/registry.py
python -m pytest tests/test_live_show_healer_regression.py -q
```

### 8.6 新技能接入最短路徑

1. 在對應 family policy 檔新增 `skill_ids` 與 `aliases`。
2. 用 `normalize_skill_id` 做 smoke test。
3. 跑 compile + regression。
4. 若仍不符，再補 healer/code_utils（避免先改 route）。

### 8.7 常見坑位

- 在 route 重新加入硬編碼 skill map（會破壞 registry 單一真相）。
- 在 route 重新堆疊 Ab2/Ab3 細節或 debug_meta 組裝（會讓維護退化）。
- 只改 `regex_fixes`，忘了同步 `regex_code_fixes` / `regex_display_fixes`。
- 先做 display format 再做同構比對（可能改壞結構指紋）。
- fallback 成功但沒記錄 log，導致除錯不可追溯。

### 8.8 函式對照表（Route ↔ Pipeline）

> 目的：快速回答「哪段流程在誰負責、輸入輸出是什麼」。

| 階段 | Route 呼叫點 | Pipeline 函式 | 主要輸入（來源） | 主要輸出（給 route） |
|---|---|---|---|---|
| Ab2 快速攔截 | `live_show.py` 內呼叫 `run_ab2_interception(...)` | `run_ab2_interception` | `final_code`、`skill_id`、`expected_fp`、`ocr_text`、`fraction_display_mode`、各種 *fn 注入（guard/sanitize/format/recompute） | `ab2_result`、`ab2_exec_elapsed`、`ab2_file_path`、`ab2_final_exec_code` |
| Ab3 完整自癒 | `live_show.py` 內呼叫 `run_ab3_full_healer(...)` | `run_ab3_full_healer` | `final_code`、`skill_id`、`expected_fp`、`decimal_style_mode`、`ocr_text`、`fraction_display_mode`、`advanced_healer_fn`、各種 *fn 注入（ISO/fallback/sanitize/format/recompute） | `problems_result`、`cpu_execution_time_sec`、`healed_code`、`file_path`、`regex_*`、`ast_fixes`、`o1_fixes`、`detail_logs`、`generated_fp`、`iso_isomorphic` |
| Output / debug_meta 組裝 | `live_show.py` 內呼叫 `assemble_visual_output(...)` | `assemble_visual_output` | Ab2/Ab3 結果 + `raw_out`、`api_stubs`、`system_prompt`、`json_spec`、`expected_fp` | 最終 `output`：`problems`、`debug_meta`、`ab2_result` |

#### `assemble_visual_output` 內 `debug_meta` 欄位對照

| `debug_meta` key | 值來源 |
|---|---|
| `performance.ai_inference_time_sec` | VL 推論耗時（route 計時） |
| `performance.cpu_execution_time_sec` | `run_ab3_full_healer` 回傳 |
| `raw_code` | 模型原始輸出 `raw_out` |
| `final_code` | `api_stubs + healed_code` |
| `file_path` | `run_ab3_full_healer` 回傳 |
| `scaffold_prompt` | route 中組出的 `system_prompt` |
| `gemini_raw_spec` | `json_spec` pretty JSON |
| `healer_trace.*` | `regex_fixes / regex_code_fixes / regex_display_fixes / ast_fixes / o1_fixes` |
| `healer_logs` | `detail_logs` |
| `iso_profile_expected` | `expected_fp` |
| `iso_profile_generated` | `generated_fp` |
| `iso_isomorphic` | `iso_isomorphic` |
| `fraction_display_mode` | `fraction_display_mode` |
| `mcri_report` | 固定摘要（MODERATE / Visual Generation with Full Healer） |

#### 修改建議（避免改壞）

1. **改 Ab2/Ab3 行為**：優先改 `live_show_pipeline.py` 對應 helper，不回塞 route。
2. **改輸出欄位**：只在 `assemble_visual_output` 動，並同步前端 flatten 區塊。
3. **改 skill 規則**：改 `core/skill_policies/*`，不要在 route/pipeline 寫 skill hardcode。
4. **改 heal/fix 計數**：確認 `regex_code_fixes` 與 `regex_display_fixes` 都維持可追溯。

### 8.9 交接完成定義（Definition of Done）

- 有清楚說明「改在哪一層、為什麼」。
- 測試與編譯指令結果可重現。
- 文件有更新（本檔至少更新變更重點或 SOP）。
- 不新增 route 硬編碼 skill 規則。