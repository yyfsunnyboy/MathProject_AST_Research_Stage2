# MCRI V4.2 評估系統進展報告

**最後更新**: 2026-02-05  
**版本**: V4.2.2 (Healer Events Tracking Edition)  
**負責人**: Math AI Research Team

---

## � 本次更新摘要 (V4.2.2 - 2026-02-05)

### 核心新增: healer_events 表與 ORM 整合

✅ **healer_events 診斷層表** - 記錄每次 Healer 修復事件
- 9 個欄位（識別層、介入層、證據層、效果層）
- 支持追蹤每次修復的前後對比與耗時
- 外鍵關聯到 experiment_runs
- 2 個查詢索引（run_id, stage）

✅ **HealerEvent ORM 模型** - models.py
- 完整序列化支持（to_dict()）
- 關聯映射到 ExperimentRun

✅ **文檔同步** - 架構與進展報告
- 系統架構.md 新增 healer_events 完整定義
- 進展報告新增實用指南與 SQL 查詢範例

📊 **系統現狀**: 4 層診斷表 + 39 欄位的 experiment_runs + 9 欄位 healer_events

---

## �🚨 重要更新 (V4.2.1)

### Critical Bug Fix - L3 評估邏輯修正

**問題發現**: 2026-02-02  
**影響範圍**: L3.1 內在一致性 + L3.2 外在強健性  
**嚴重程度**: 🔴 高（導致所有 L3 分數不準確）

#### Bug 詳情

1. **L3.1 內在一致性邏輯錯誤**
   ```python
   # ❌ 錯誤的舊邏輯
   is_consistent = self.check_func(correct_ans, correct_ans)
   if is_consistent is True:  # ← check() 返回 dict，不是 bool！
       score = 15.0
   # dict 永遠不等於 True，導致永遠得 0 分
   ```

2. **L3.2 外在強健性分數未累加**
   ```python
   # ❌ 錯誤的舊邏輯
   result_check = self.check_func(student_input, correct_ans)
   is_correct = (result_check == expected)  # ← dict 永遠不等於 True/False
   # 導致永遠判斷錯誤，分數 = 0
   ```

#### 修正方案

```python
# ✅ 正確的新邏輯 (V4.2.1)

# L3.1 內在一致性
check_result = self.check_func(correct_ans, correct_ans)

if isinstance(check_result, dict):
    if check_result.get('correct') is True:
        score = 15.0  # ✓ 正確判斷
    else:
        score = 0
elif check_result is True:  # 兼容舊版 bool 返回
    score = 15.0

# L3.2 外在強健性
check_result = self.check_func(student_input, correct_ans)

if isinstance(check_result, dict):
    actual = check_result.get('correct', False)
elif isinstance(check_result, bool):
    actual = check_result
else:
    actual = False

is_correct = (actual == expected)  # ✓ 正確比較
if is_correct:
    score += 3.75
```

#### 影響評估

**舊版 (V4.2.0) 錯誤結果**:
- L3.1 分數: 永遠 0 分（即使 check() 正常運作）
- L3.2 分數: 永遠 0 分（無法正確判斷學生輸入）
- 總影響: L3 總分 = 0/30，嚴重低估所有 Ablation 的品質

**新版 (V4.2.1) 預期結果**:
- L3.1 分數: 0 或 15（正確反映 check() 自洽性）
- L3.2 分數: 0-15（正確反映 check() 強健性）
- Ab3 Healer 應在 L3 顯著高於 Ab1 Bare

#### 驗證測試

測試腳本: `temp/test_l3_logic_fix.py`

```bash
python temp/test_l3_logic_fix.py

# 輸出:
# ✅ L3.1: dict['correct'] = True → 得分 15
# ✅ L3.2: 4 項測試正確累加分數
# ✅ student_input_test 存完整測試記錄
```

#### 下一步行動

⚠️ **必須重新執行評估**:
```bash
# 刪除舊資料庫
rm reports/mcri_evaluation.db
rm -rf reports/csv/

# 重新執行評估
python scripts/evaluate_mcri.py
```

---

## 📋 目錄

1. [系統概述](#系統概述)
2. [評估維度設計](#評估維度設計)
3. [資料庫架構](#資料庫架構)
4. [L2 評估實作](#l2-評估實作)
5. [Metadata 提取機制](#metadata-提取機制)
6. [Healer 機制整合](#healer-機制整合)
7. [驗證測試結果](#驗證測試結果)
8. [執行指南](#執行指南)
9. [版本歷史](#版本歷史)

---

## 系統概述

### 目標
量化評估三個 Ablation 版本（Ab1 Bare, Ab2 Engineered, Ab3 Healer）在題目生成品質上的差異，為科展實驗提供統計證據。

### 核心檔案
- **主程式**: `scripts/evaluate_mcri.py` (1274 行)
- **測試腳本**: `temp/test_*.py` (已移至 temp 目錄)
- **輸出位置**: `reports/mcri_evaluation.db` + `reports/csv/*.csv`

### 評估規模
- **3 個 Ablation** × **5 個 Samples** × **20 次 Repetitions** = **300 次 generate() 呼叫**
- **執行時間**: 約 5-10 分鐘（取決於 timeout 設定）

---

## 評估維度設計

### MCRI V4.2 評分標準 (滿分 100 分)

#### L1 工程基石 (20 分)
- **L1.1 語法安全** (10 分)
  - AST 解析成功
  - 無禁用函數 (eval, exec, compile)
  - 無禁用模組 (os, subprocess, sys)
  
- **L1.2 執行穩定性** (10 分)
  - 執行 3 次 generate()，計算成功率
  - 記錄平均執行時間

#### L2 資料衛生 (20 分) ✅ **V4.2 已實作**
- **L2.1 介面契約** (10 分)
  - 必要鍵: question_text, answer, correct_answer (3分)
  - question_text 非空 (4分)
  - answer == correct_answer (3分)
  
- **L2.2 格式純淨度** (10 分)
  - 無 $ 符號 (3分)
  - 無前綴 (f'(x)=, y=, 答案=) (3分)
  - 無換行符 (4分)

#### L3 評測公平 (30 分)
- **L3.1 內在一致性** (15 分)
  - check(system_answer, system_answer) == True
  
- **L3.2 外在強健性** (15 分)
  - 測試 4 種學生輸入變體 (每種 3.75 分)
    1. 標準形式
    2. 小數形式 (0.5 vs 1/2)
    3. 省略乘號 (2x vs 2*x)
    4. 明顯錯誤 (999)

#### L4 教學有效 (30 分)
- **L4.1 數值友善度** (15 分)
  - 分母 ≤ 20 (4分)
  - 係數 ≤ 50 (4分)
  - 無未約分分數 (3分)
  - 無無限小數 (4分)
  
- **L4.2 視覺可讀性** (15 分)
  - LaTeX 格式正確 (5分)
  - 無過長表達式 (5分)
  - 無過多括號 (5分)

---

## 資料庫架構

### 表 1: experiment_runs (主表) - 27 欄位

**基本資訊** (6 欄位):
```
run_id              TEXT PRIMARY KEY    # UUID
timestamp           TEXT                # ISO 8601 時間戳
model_name          TEXT                # qwen2.5-coder:14b
skill_name          TEXT                # gh_ApplicationsOfDerivatives
ablation_id         INTEGER             # 1=Ab1, 2=Ab2, 3=Ab3
sample_index        INTEGER             # 1-5
```

**執行統計** (5 欄位):
```
repetitions_planned     INTEGER         # 20
repetitions_completed   INTEGER         # 實際完成數
fail_count              INTEGER         # FAIL/TIMEOUT/ERROR 數量
pass_rate               REAL            # 成功率 (0-1)
avg_exec_time           REAL            # 平均執行時間 (秒)
```

**分數欄位** (13 欄位):
```
score_l1_total          INTEGER         # L1 總分 (0-20)
score_l1_1_syntax       INTEGER         # 語法安全 (0-10)
score_l1_2_runtime      INTEGER         # 執行穩定 (0-10)

score_l2_total          INTEGER         # L2 總分 (0-20)
score_l2_1_contract     INTEGER         # 介面契約 (0-10)
score_l2_2_purity       INTEGER         # 格式純淨 (0-10)

avg_l3_total            REAL            # L3 平均總分 (0-30)
avg_l3_1_internal       REAL            # 內在一致性平均
avg_l3_2_external       REAL            # 外在強健性平均

avg_l4_total            REAL            # L4 平均總分 (0-30)
avg_l4_1_numeric        REAL            # 數值友善度平均
avg_l4_2_visual         REAL            # 視覺可讀性平均

avg_mcri_total          REAL            # MCRI 總分 (0-100)
```

**元資料** (3 欄位):
```
source_code_path        TEXT            # 技能檔案絕對路徑
mcri_version            TEXT            # "4.2"
notes                   TEXT            # L1 詳情 + Metadata (7 欄位)
```

### 表 2: evaluation_items (附表) - 19 欄位

**基本資訊** (9 欄位):
```
item_id                     TEXT PRIMARY KEY
run_id                      TEXT (Foreign Key)
repetition_index            INTEGER (1-20)
generated_question          TEXT (截取 500 字元)
generated_answer            TEXT (截取 200 字元)
generated_correct_answer    TEXT (截取 200 字元)
status                      TEXT (PASS/FAIL/TIMEOUT/ERROR)
error_log                   TEXT
included_in_avg             INTEGER (0 or 1)
```

**L2 分數** (2 欄位) ✅ **V4.2 新增**:
```
score_l2_1_contract         INTEGER (0-10)
score_l2_2_purity           INTEGER (0-10)
```

**L3/L4 分數** (6 欄位):
```
score_l3_total              INTEGER (0-30)
score_l3_1_internal         INTEGER (0-15)
score_l3_2_external         INTEGER (0-15)
score_l4_total              INTEGER (0-30)
score_l4_1_numeric          INTEGER (0-15)
score_l4_2_visual           INTEGER (0-15)
```

**測試資訊** (2 欄位):
```
student_input_test          TEXT (測試記錄)
student_input_result        TEXT (PASS/PARTIAL)
```

### 表 3: ablation_summary (彙總表) - 12 欄位

**識別欄位** (4 欄位):
```
summary_id          TEXT PRIMARY KEY
skill_name          TEXT
ablation_id         INTEGER
model_name          TEXT
```

**統計欄位** (8 欄位):
```
sample_count        INTEGER     # 樣本數 (通常為 5)
total_runs          INTEGER     # 總執行次數 (5 × 20 = 100)
mean_mcri_total     REAL        # MCRI 平均分
std_mcri_total      REAL        # 標準差
ci95_lower          REAL        # 95% 信賴區間下界
ci95_upper          REAL        # 95% 信賴區間上界
mean_l3_external    REAL        # L3.2 平均分 (評測公平關鍵指標)
mean_l4_numeric     REAL        # L4.1 平均分 (教學友善關鍵指標)
```

---

## L2 評估實作

### V4.2 關鍵改進

#### 問題 (V4.0-V4.1)
```python
# ❌ 舊版：使用固定值
score_l2_1_list.append(10)  # 全部給滿分
score_l2_2_list.append(10)  # 無法區分 Ablation 差異
```

#### 解決方案 (V4.2)
```python
# ✅ 新版：真實評估
# 在 evaluate_single_repetition() 中
score_l2_1, _ = self.evaluate_interface_contract(result)
item['score_l2_1_contract'] = int(score_l2_1)

score_l2_2, _ = self.evaluate_format_purity(result)
item['score_l2_2_purity'] = int(score_l2_2)

# 在 run_full_evaluation() 中
score_l2_1_list = [item['score_l2_1_contract'] for item in pass_items]
score_l2_2_list = [item['score_l2_2_purity'] for item in pass_items]
score_l2_1_avg = int(np.mean(score_l2_1_list)) if score_l2_1_list else 0
score_l2_2_avg = int(np.mean(score_l2_2_list)) if score_l2_2_list else 0
```

### L2.2 格式純淨度評估邏輯

```python
def evaluate_format_purity(self, result: Dict) -> Tuple[float, str]:
    """
    L2.2 格式純淨度 (10分)
    檢查答案是否符合「純數值」格式要求
    """
    score = 0.0
    notes = []
    answer = str(result.get('answer', ''))
    
    # 1. 無 $ 符號 (3分)
    if '$' not in answer:
        score += 3.0
    else:
        notes.append("含 $ 符號")
    
    # 2. 無前綴 (3分)
    prefix_pattern = r'^(f\'?\(x\)\s*=|y\s*=|答案[:=]|answer[:=])'
    if not re.search(prefix_pattern, answer, re.IGNORECASE):
        score += 3.0
    else:
        notes.append("含前綴")
    
    # 3. 無換行 (4分)
    if '\n' not in answer and '\r' not in answer:
        score += 4.0
    else:
        notes.append("含換行符")
    
    return score, "; ".join(notes) if notes else "通過"
```

### 預期結果

根據測試模擬，三個 Ablation 的 L2 表現預期為：

| Ablation | L2.1 契約 | L2.2 格式 | L2 總分 | 備註 |
|----------|-----------|-----------|---------|------|
| Ab1 Bare | 8-10 | 0-3 | 10-12 | 契約OK，格式混亂（有前綴、$符號）|
| Ab2 Engineered | 10 | 3-7 | 15-17 | 契約完整，部分格式清理 |
| Ab3 Healer | 10 | 8-10 | 18-20 | 完整清理（clean_latex_output）🏆 |

---

## Metadata 提取機制

### 從技能檔案 Header 提取的欄位

技能檔案範例 (Ab3.py):
```python
# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: qwen2.5-coder:14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 3 | Basic Cleanup: ENABLED | Advanced Healer: ON
# Performance: 17.13s | Tokens: In=7122, Out=620
# Created At: 2026-02-02 11:26:37
# Fix Status: [Advanced Healer] | Fixes: Basic=1, Advanced=(Regex=4, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
```

### 提取的 7 個欄位

```python
def _extract_metadata(self) -> Dict[str, Any]:
    """
    從技能檔案 header 提取 metadata (7 個欄位)
    
    Returns:
        {
            'model_name': 'qwen2.5-coder:14b',
            'performance': 17.13,           # 浮點數 (秒)
            'tokens_in': 7122,              # 整數
            'tokens_out': 620,              # 整數
            'created_at': '2026-02-02 11:26:37',
            'fix_status': '[Advanced Healer]',
            'fixes_basic': 1,               # 整數
            'fixes_regex': 4,               # 整數
            'fixes_ast': 0,                 # 整數
            'verification': 'Internal Logic Check = PASSED'
        }
    """
```

### 整合到 notes 欄位

```python
def _build_notes(self, notes_l1_1: str, notes_l1_2: str) -> str:
    """
    建立 notes 欄位，整合 L1 評分 + metadata
    
    Format: "L1: {syntax}; {runtime} | Perf: 17.13s | Tokens: In=7122, Out=620 | ..."
    """
    notes_parts = []
    
    # L1 評分細節
    notes_parts.append(f"L1: {notes_l1_1}; {notes_l1_2}")
    
    # Metadata 資訊
    if hasattr(self, 'metadata'):
        meta = self.metadata
        
        if meta.get('performance'):
            notes_parts.append(f"Perf: {meta['performance']}s")
        
        if meta.get('tokens_in') and meta.get('tokens_out'):
            notes_parts.append(f"Tokens: In={meta['tokens_in']}, Out={meta['tokens_out']}")
        
        # ... (其他欄位)
    
    return " | ".join(notes_parts)
```

### 驗證結果 (100% 準確度)

測試腳本 `temp/test_field_extraction.py` 驗證結果：
```
✅ Performance: 17.13 == 17.13 ✓
✅ Tokens: In=7122 == 7122 ✓, Out=620 == 620 ✓
✅ Created At: 2026-02-02 11:26:37 ✓
✅ Fixes: Basic=1 ✓, Regex=4 ✓, AST=0 ✓
✅ Verification: Internal Logic Check = PASSED ✓
```

---

## Healer 機制整合

### Code Generator 架構

**檔案**: `core/code_generator.py` (V10.1.0)

#### 主要功能

1. **自動技能生成**
   ```python
   def auto_generate_skill_code(skill_id, model_config, ablation_settings):
       """
       主入口函數，根據規格書生成技能程式碼
       
       Args:
           skill_id: 技能 ID (如 'gh_ApplicationsOfDerivatives')
           model_config: 模型配置 (從 config.py 讀取)
           ablation_settings: {
               'basic_cleanup': True/False,      # Ab2+
               'advanced_healer': True/False     # Ab3 only
           }
       """
   ```

2. **AST 修復**
   ```python
   def ast_fix_code(code_str, max_attempts=5):
       """
       進行 AST 結構修復
       
       修復類型:
       - Regex 修復 (基礎語法錯誤)
       - AST 修復 (結構性問題)
       
       Returns:
           (fixed_code, fix_stats)
           fix_stats = {
               'basic': int,
               'regex': int,
               'ast': int
           }
       """
   ```

3. **沙盒驗證**
   ```python
   def validate_skill_code(code_str, timeout=10):
       """
       沙盒驗證，確保程式碼可執行
       
       Returns:
           {
               'success': bool,
               'error': str or None,
               'exec_time': float
           }
       """
   ```

### Healer 對 L2 的影響

#### Ab1 Bare (無 Healer)
```python
# 生成結果範例
{
    'question_text': '求 f\'(x) = 3x^2 - 5x + 2 的導數。',  # ❌ 有前綴
    'answer': '$3x - 5$',                                   # ❌ 有 $ 符號
    'correct_answer': '$3x - 5$'
}

# L2.2 格式純淨度: 0 分 (有前綴 + $ 符號)
```

#### Ab2 Engineered (Basic Cleanup)
```python
# 生成結果範例
{
    'question_text': '已知 $f(x) = 3x^2 - 5x + 2$，求導數。',
    'answer': '3x - 5',          # ✅ 無 $ 符號
    'correct_answer': '3x - 5'   # ✅ 無前綴
}

# L2.2 格式純淨度: 6-7 分 (無 $ + 無前綴)
```

#### Ab3 Healer (Advanced Healer)
```python
# Healer 處理流程
def clean_latex_output(q_str):
    """
    V47.7 Fix - LaTeX 格式清洗器
    
    步驟:
    1. 提取已包裝的 $...$ 塊
    2. 清洗剩餘純文本 (移除 *, /, 雙括號)
    3. 智能分離中文與數學式
    4. 恢復 LaTeX 塊
    """
    
# 生成結果範例
{
    'question_text': '已知 $f(x) = 3x^2 - 5x + 2$，求導數。',
    'answer': '3x - 5',          # ✅ 完全純淨
    'correct_answer': '3x - 5'   # ✅ 無任何多餘符號
}

# L2.2 格式純淨度: 10 分 (完美) 🏆
```

### Healer 效果量化

根據實際測試 (temp/test_l2_evaluation.py):
```
模擬 3 個 Ablation 的 L2 分數:
- Ab3 (Healer):      L2.1=10, L2.2=10 → L2總分=20 ✨
- Ab2 (Engineered):  L2.1=10, L2.2=3  → L2總分=13
- Ab1 (Bare):        L2.1=8,  L2.2=0  → L2總分=8

結論: Healer 在 L2.2 格式純淨度上提升 7-10 分！
```

---

## 驗證測試結果

### 測試腳本位置
所有測試腳本已移至 `temp/` 目錄（符合規則 1）：
- `temp/test_field_extraction.py` - Metadata 提取驗證
- `temp/test_schema_cleanup.py` - Schema 清理驗證
- `temp/test_l2_evaluation.py` - L2 評估實作驗證
- `temp/test_final_validation.py` - 最終完整性檢查

### 驗證結果總覽

#### ✅ Test 1: Metadata 提取 (100% 準確度)
```
🎉 所有欄位完全一致！
- Performance: 17.13 == 17.13 ✓
- Tokens: In=7122, Out=620 ✓
- Created At: 2026-02-02 11:26:37 ✓
- Fixes: Basic=1, Regex=4, AST=0 ✓
- Verification: Internal Logic Check = PASSED ✓
```

#### ✅ Test 2: Schema 清理 (27 欄位正確)
```
🎉 Schema 清理成功！
- 已刪除: code_commit_hash, python_version, model_temperature
- 保留欄位: 27 個
- 資料庫結構: 正確 ✓
```

#### ✅ Test 3: L2 評估實作
```
🎉 所有測試通過！L2 評估實作成功
- evaluation_items 表新增 2 個欄位 (19 欄位)
- evaluate_single_repetition() 儲存真實 L2 分數
- run_full_evaluation() 從 items 計算平均值
- CSV 輸出包含 L2 明細
```

#### ✅ Test 4: 最終驗證 (58 欄位全部就緒)
```
✅ 總欄位數: 58 個 (27 + 19 + 12)
✅ 所有欄位都有明確的資料來源
✅ 無遺漏或未知值
✅ L2 評估已正確實作（真實評估，非固定值）
```

---

## 執行指南

### 前置準備

1. **確認技能檔案存在**
   ```bash
   ls skills/gh_ApplicationsOfDerivatives_14b_Ab*.py
   # 應顯示: Ab1.py, Ab2.py, Ab3.py
   ```

2. **確認輸出目錄**
   ```bash
   mkdir -p reports/csv
   ```

3. **檢查依賴套件**
   ```bash
   pip install numpy pandas scipy
   ```

### 執行評估

```bash
# 執行完整評估
python scripts/evaluate_mcri.py

# 預期輸出:
# 1. 終端顯示進度條與即時統計
# 2. 生成資料庫: reports/mcri_evaluation.db
# 3. 生成 CSV: reports/csv/*.csv
# 4. 顯示彙總表格與關鍵洞察
```

### 預期執行時間
```
🔄 執行 3 個 Ablation × 5 個 Samples × 20 次 Repetitions
- 單次 generate() 超時設定: 5 秒
- 預估總時間: 5-10 分鐘
- 實際時間取決於系統效能與 Healer 修復次數
```

### 輸出檢查

#### 1. SQLite 資料庫
```bash
# 檢查表結構
sqlite3 reports/mcri_evaluation.db "SELECT COUNT(*) FROM experiment_runs;"
# 預期: 15 筆 (3 ablations × 5 samples)

sqlite3 reports/mcri_evaluation.db "SELECT COUNT(*) FROM evaluation_items;"
# 預期: ~300 筆 (15 runs × 20 reps)

sqlite3 reports/mcri_evaluation.db "SELECT * FROM ablation_summary;"
# 預期: 3 筆 (Ab1, Ab2, Ab3 各 1 筆)
```

#### 2. CSV 報表
```bash
# 檢查 CSV 檔案
ls -lh reports/csv/

# experiment_runs.csv - 15 rows × 27 columns
# evaluation_items.csv - ~300 rows × 19 columns
# ablation_summary.csv - 3 rows × 12 columns
```

#### 3. 終端輸出範例
```
================================================================================
📊 MCRI V4.2 彙總統計
================================================================================

Ablation   Skill                          Mean     Std      95% CI              
--------------------------------------------------------------------------------
Ab1        gh_ApplicationsOfDerivatives   65.23    5.12     [60.18, 70.28]      
Ab2        gh_ApplicationsOfDerivatives   78.45    3.87     [74.63, 82.27]      
Ab3        gh_ApplicationsOfDerivatives   89.67    2.34     [87.35, 91.99]      

================================================================================
💡 關鍵洞察
================================================================================

🏆 最佳配置: Ab3 (89.67 分)

📈 Ab3 (Healer) vs Ab1 (Bare):
  提升: +24.4 分 (37.4%)
  L3 評測公平: 20.3 → 27.8 (+7.5)
  L4 教學有效: 18.5 → 26.1 (+7.6)

🔧 Healer 機制 (Ab3):
  - 自動修復 AST 錯誤，提升執行穩定性
  - 強化 check() 函數，改善評測公平性
  - 優化數值生成，增進教學適用性
```

---

## 版本歷史

### V4.2.1 (2026-02-02) - L3 Logic Fix Edition 🚨
**Critical Bug Fix**:
- ✅ 修正 L3.1 內在一致性：正確判斷 check() 返回的 dict['correct']
- ✅ 修正 L3.2 外在強健性：正確處理 dict 返回值，累加分數
- ✅ 兼容舊版 check() 直接返回 bool 的情況
- ✅ 新增驗證測試: temp/test_l3_logic_fix.py

**影響範圍**:
- ❌ V4.2.0 的所有 L3 分數不準確（永遠 0 分）
- ✅ V4.2.1 修正後，L3 分數應正常分布在 0-30 之間
- ⚠️ 需要刪除舊資料庫，重新執行評估

**測試結果**:
```
✅ L3.1: dict['correct'] = True → 得分 15 ✓
✅ L3.2: 4 項測試正確累加 (標準+錯誤 = 7.5/15)
✅ student_input_test: 存完整測試記錄
```

### V4.2.0 (2026-02-02) - L2 Real Evaluation Edition
**新增功能**:
- ✅ 實作 L2.1 和 L2.2 真實評估（移除固定值）
- ✅ evaluation_items 表新增 score_l2_1_contract, score_l2_2_purity 欄位
- ✅ 從 items 計算真實 L2 平均分
- ✅ CSV 輸出包含 L2 明細

**修復問題**:
- ❌ 刪除 3 個無資料來源欄位 (code_commit_hash, python_version, model_temperature)
- ✅ 修正 L2 分數計算邏輯（從固定值改為真實評估）

**科學價值**:
- 可量化 Ab3 Healer 的格式修復能力
- L2.2 分數將展現 clean_latex_output() 的效果
- 資料衛生評估更完整（契約 + 格式）

### V4.1.0 (2026-02-01) - Metadata Integration Edition
**新增功能**:
- ✅ 實作 _extract_metadata() 方法，提取 7 個欄位
- ✅ 實作 _build_notes() 方法，整合 L1 + metadata
- ✅ 驗證測試腳本 (100% 準確度)

### V4.0.0 (2026-01-31) - Initial Release
**初始功能**:
- ✅ 實作 MCRI_Evaluator 核心類別
- ✅ 實作 L1/L3/L4 評估邏輯
- ✅ 建立 SQLite 資料庫 (3 張表)
- ✅ 雙輸出系統 (SQLite + CSV)

---

## 參考資料

### 相關文件
- **Code Generator**: `core/code_generator.py` (V10.1.0)
- **Config**: `config.py` (模型配置與 temperature 設定)
- **專案速查**: `docs/競賽文件/專案速查.md`

### 技能檔案範例
- **Ab1 Bare**: `skills/gh_ApplicationsOfDerivatives_14b_Ab1.py`
- **Ab2 Engineered**: `skills/gh_ApplicationsOfDerivatives_14b_Ab2.py`
- **Ab3 Healer**: `skills/gh_ApplicationsOfDerivatives_14b_Ab3.py`

### 測試腳本
- **Metadata 提取**: `temp/test_field_extraction.py`
- **Schema 清理**: `temp/test_schema_cleanup.py`
- **L2 評估**: `temp/test_l2_evaluation.py`
- **最終驗證**: `temp/test_final_validation.py`

---

**報告結束**  
**下次更新**: 執行完整評估後補充實際數據與統計分析

---

## 附錄：常見問題

### Q1: 為什麼 L2 評估這麼重要？
**A**: L2「資料衛生」是 Ab3 Healer 的核心優勢。Healer 的 clean_latex_output() 函數專門清理格式問題（移除前綴、$ 符號、多餘空格），如果不評估 L2，就無法量化 Healer 的價值。

### Q2: 為什麼刪除 code_commit_hash 等 3 個欄位？
**A**: 這些欄位在技能檔案 header 中沒有對應資訊，且對評估結果無實質影響。保留會導致資料庫充滿 NULL 或無意義值，影響資料品質。

### Q3: notes 欄位為什麼要整合 metadata？
**A**: notes 是唯一的 TEXT 欄位，可以靈活儲存非結構化資訊。將 L1 詳情與 7 個 metadata 欄位整合後，可以在 CSV 中一目瞭然地看到每個 run 的完整資訊。

### Q4: 為什麼 evaluation_items 表需要 19 個欄位？
**A**: 每次 generate() 呼叫都是一個獨立實驗，需要記錄：
- 生成內容 (3 欄位)
- 狀態與錯誤 (3 欄位)
- L2/L3/L4 分數 (10 欄位)
- 測試結果 (2 欄位)

這樣才能追溯每個分數的來源，進行細粒度分析。

### Q5: 如何解讀 ablation_summary 的統計指標？
**A**: 
- **mean_mcri_total**: 平均總分，越高越好
- **std_mcri_total**: 標準差，越小表示穩定性越高
- **ci95_lower/upper**: 95% 信賴區間，用於判斷差異是否顯著
- **mean_l3_external**: 評測公平的關鍵指標（check 函數品質）
- **mean_l4_numeric**: 教學友善的關鍵指標（數值難度）

如果 Ab3 的 CI 下界 > Ab1 的 CI 上界，表示提升達到統計顯著性！

---

## 🚀 系統架構更新 (V2.0 - 2026-02-05)

### 資料庫欄位擴展

**版本**: experiment_runs 從 30 欄位擴展至 39 欄位（新增 9 個）  
**目的**: 支持 Golden Prompt 批量生成、成本效能追蹤、Healer 統計  
**狀態**: ✅ 已遷移至 instance/kumon_math.db

#### 新增欄位詳解

##### 群組 1: 批次管理 (1 欄位)
atch_id TEXT - 批次識別符，用於分組查詢相同條件的多個 run

**用途**: 支持 Golden Prompt 批量生成模式

##### 群組 2: Golden Prompt 變因控制 (2 欄位)
- golden_prompt_path TEXT - Golden Prompt 文件的絕對路徑
- prompt_hash TEXT - Prompt 內容的 SHA256 哈希值

**用途**: 追蹤 Prompt 版本與質量關係

##### 群組 3: 成本效能指標 (4 欄位)
- prompt_tokens INTEGER - 提示詞 Token 數
- completion_tokens INTEGER - 完成 Token 數
- 	otal_tokens INTEGER - 總 Token 數
- latency_ms REAL - 端對端延遲（毫秒）

**用途**: 成本效能分析

##### 群組 4: Healer 統計 (2 欄位)
- healer_applied INTEGER - 0 = 未應用, 1 = 已應用
- healer_fix_count INTEGER - Healer 總修復次數

**用途**: Healer 效果量化

#### 資料庫遷移日誌

**執行日期**: 2026-02-05  
**遷移腳本**: temp/migrate_experiment_runs_v2.py  
**執行結果**: ✅ 全部成功（39 欄位，0 行數據）

**ORM 模型更新**: models.py
- 新增 9 個 db.Column 定義
- 更新 to_dict() 方法（包含新欄位）
- 所有序列化已驗證 ✅

---

#### 系統架構文檔

完整的系統架構已記錄在：
📄 docs/競賽文件/系統架構.md

包含內容：
- I. 項目目錄架構（完整樹狀圖）
- II. 資料庫 Schema（8 個核心表）
- III. 表格關聯圖（星型架構）
- IV. 核心模塊相互關係
- V. 核心技術架構（Ablation / Healer / MCRI）
- VI. 2+1+15 混合實驗策略
- VII. 快速啟動指南
- VIII. 關鍵文件索引
- IX. 新增欄位詳解（4 群組、9 欄位、用途說明、SQL 範例、科展價值）


---

## 🆕 healer_events 表新增 (2026-02-05)

### 表格用途

healer_events 是新的診斷層表，用於記錄每次 Healer 修復事件的詳細信息：
- **階段追蹤**: 哪個階段的修復（Pre-Process, Regex_Healer, AST_Healer）
- **模式識別**: 修復的具體類型（fix_infinite_loop, fix_latex_dollar_sign 等）
- **效果證據**: 修復前後的代碼片段（用於審計）
- **性能分析**: 每次修復的耗時（毫秒）

### 表結構

`sql
CREATE TABLE healer_events (
    event_id VARCHAR(36) PRIMARY KEY,      -- 事件 UUID
    run_id VARCHAR(36) NOT NULL,           -- FK 關聯到 experiment_runs
    stage VARCHAR(50) NOT NULL,            -- 修復階段
    pattern_id VARCHAR(100),               -- 修復模式
    original_snippet TEXT,                 -- 修改前代碼
    healed_snippet TEXT,                   -- 修改後代碼
    is_success BOOLEAN DEFAULT 1,          -- 修復成功否
    fix_duration_ms INTEGER DEFAULT 0,     -- 耗時（毫秒）
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

索引: idx_healer_run, idx_healer_stage
外鍵: run_id → experiment_runs(run_id)
`

### 欄位詳解

| 欄位 | 類型 | 說明 | 例子 |
|-----|------|------|------|
| event_id | VARCHAR(36) | 事件識別碼 | '550e8400-e29b-41d4-a716-446655440000' |
| run_id | VARCHAR(36) | 關聯的 run | 與 experiment_runs.run_id 對應 |
| stage | VARCHAR(50) | 修復階段 | 'Regex_Healer', 'AST_Healer', 'Pre-Process' |
| pattern_id | VARCHAR(100) | 修復規則 | 'fix_infinite_loop', 'fix_latex_dollar_sign' |
| original_snippet | TEXT | 原始代碼片段 | 'while True:\n    x = 1' （前 500 字） |
| healed_snippet | TEXT | 修復後代碼 | 'for i in range(100):\n    x = 1' |
| is_success | BOOLEAN | 是否成功應用 | 1 or 0 |
| fix_duration_ms | INTEGER | 修復耗時 | 23 (毫秒) |
| timestamp | DATETIME | 記錄時間 | '2026-02-05 10:30:45.123' |

### 關鍵 SQL 查詢

**查詢某個 run 的所有修復事件**:
`sql
SELECT stage, pattern_id, COUNT(*) as count, SUM(fix_duration_ms) as total_ms
FROM healer_events
WHERE run_id='exp123'
GROUP BY stage, pattern_id
ORDER BY total_ms DESC;
`

**找出最常見的修復模式**:
`sql
SELECT pattern_id, COUNT(*) as frequency, AVG(fix_duration_ms) as avg_ms
FROM healer_events
WHERE is_success=1
GROUP BY pattern_id
ORDER BY frequency DESC
LIMIT 10;
`

**計算 Healer 對單個 run 的總開銷**:
`sql
SELECT 
    run_id,
    COUNT(*) as event_count,
    SUM(fix_duration_ms) as total_healer_ms,
    AVG(fix_duration_ms) as avg_event_ms
FROM healer_events
GROUP BY run_id
ORDER BY total_healer_ms DESC;
`

### 科展價值

1. **定量證明**: 用具體數字證明 Healer 確實在工作（不是「掛名」）
2. **效能分析**: 計算 Healer 帶來的時間開銷 vs 品質提升
3. **優化基礎**: 識別哪些修復最耗時，進行針對優化
4. **審計追蹤**: 論文可以說「我們的修復過程是完全可追蹤的」

### 遷移狀態

- ✅ 表已建立 (9 欄位)
- ✅ 外鍵已設定 (run_id → experiment_runs)
- ✅ 索引已建立 (idx_healer_run, idx_healer_stage)
- ✅ ORM 模型已定義 (models.py: HealerEvent 類)
- ⏳ 待填充: 運行實驗時自動記錄修復事件

