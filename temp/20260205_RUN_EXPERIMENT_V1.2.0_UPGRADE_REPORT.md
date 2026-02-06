# 🧪 run_experiment.py V1.2.0 升級報告

## 📋 概述

**升級日期**: 2026-02-05  
**版本**: V1.2.0 (Model Selection & Enhanced Statistics)  
**目標**: 在原有的 V1.1.0 (Real API Integration) 基礎上，加入：
1. ✅ 模型選擇菜單層級 [0]全部 [1]Gemini [2]14B [3]7B
2. ✅ 完整的實驗統計數據收集與彙總
3. ✅ 參考 code_generator.py 的標頭格式應用於每個生成程式

---

## 🎯 核心改進

### 1️⃣ 模型選擇菜單 (show_model_selection_menu)

#### 功能描述
在技能選擇之後、實驗開始之前，新增一層模型選擇菜單。

#### 使用者互動流程
```
[技能選擇] → [模型選擇] → [確認實驗配置] → [開始巢狀迴圈]
```

#### 菜單示例
```
======================================================================
🤖 [模型選擇] 請選擇要執行的模型範圍
======================================================================
   [0] ALL (全部 3 個模型)
   [1] Cloud Gemini 2.5 Flash
   [2] Local Qwen2.5-Coder 14B
   [3] Local Qwen2.5-Coder 7B

👉 請輸入選項 (0-3): 
```

#### 代碼位置
- 檔案: `scripts/run_experiment.py`
- 函數: `show_model_selection_menu()` (行 268-289)
- 調用位置: `main()` 函數內 (行 347)

---

### 2️⃣ 實驗統計數據結構 (ExperimentStats 類)

#### 全局統計字段
```python
class ExperimentStats:
    total_skills: int              # 技能總數
    total_models: int              # 選定的模型數
    total_strategies: int = 3      # 固定為 Ab1/Ab2/Ab3
    total_samples_per_run: int = 5 # 固定為 5 樣本
    total_planned_runs: int        # 計畫執行次數
    successful_runs: int = 0       # 實際成功次數
    failed_runs: int = 0           # 實際失敗次數
    total_tokens_prompt: int = 0   # 全部 Prompt tokens
    total_tokens_completion: int = 0 # 全部 Completion tokens
    total_time_seconds: float = 0  # 全部耗時 (秒)
    healed_count: int = 0          # 已應用 Healer 的數量
```

#### 模型級統計字段 (model_stats)
```python
model_stats[model_key] = {
    'success': 0,                  # 該模型成功次數
    'failure': 0,                  # 該模型失敗次數
    'tokens_prompt': 0,            # 該模型 Prompt tokens
    'tokens_completion': 0,        # 該模型 Completion tokens
    'time': 0.0                    # 該模型總耗時
}
```

#### 技能級統計字段 (skill_stats)
```python
skill_stats[skill_id] = {
    'success': 0,                  # 該技能成功次數
    'failure': 0,                  # 該技能失敗次數
    'tokens_prompt': 0,            # 該技能 Prompt tokens
    'tokens_completion': 0,        # 該技能 Completion tokens
    'time': 0.0                    # 該技能總耗時
}
```

#### 代碼位置
- 檔案: `scripts/run_experiment.py`
- 類: `ExperimentStats` (行 79-113)
- 全局實例: `stats = ExperimentStats()` (行 115)

---

### 3️⃣ 檔案標頭生成 (_format_file_header)

#### 功能說明
參考 `core/code_generator.py` 的 `_format_header` 模式，為每個生成的程式碼檔案添加標準化的元數據標頭。

#### 標頭格式範例
```python
# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: Cloud Gemini 2.5 Flash | Strategy: V1.1.0 Real API Integration
# Ablation ID: 1 | Name: Ab1 | Healer: OFF
# Performance: 2.35s | Tokens: In=1200, Out=850
# Created At: 2026-02-05 13:50:45
# Healer Fixes: 0
# ==============================================================================

[生成的程式碼內容...]
```

#### 標頭字段說明
| 字段 | 說明 | 示例 |
|------|------|------|
| ID | 技能識別碼 | `gh_ApplicationsOfDerivatives` |
| Model | 使用的模型名稱 | `Cloud Gemini 2.5 Flash` |
| Strategy | 實驗策略版本 | `V1.1.0 Real API Integration` |
| Ablation ID | Ablation 編號 (1-3) | `1` |
| Name | Ablation 名稱 | `Ab1` |
| Healer | Healer 啟用狀態 | `OFF` 或 `ON` |
| Performance | 單次執行耗時 | `2.35s` |
| Tokens | Prompt/Completion token 計數 | `In=1200, Out=850` |
| Created At | 建立時間戳記 | `2026-02-05 13:50:45` |
| Healer Fixes | Healer 應用的修復次數 | `0` |

#### 代碼位置
- 檔案: `scripts/run_experiment.py`
- 函數: `_format_file_header()` (行 232-261)
- 調用位置: 巢狀迴圈內 (行 551-562)

---

### 4️⃣ 巢狀迴圈中的統計收集

#### 迴圈結構
```
for skill in selected_skills:
    for model_key in selected_models:
        for ablation_strategy in [Ab1, Ab2, Ab3]:
            for sample_index in range(1, 6):
                [執行 LLM 呼叫]
                [收集統計數據]
                [應用 Healer]
                [生成標頭]
                [存檔]
```

#### 統計數據收集點
```python
# 單次運行內
run_start_time = time.time()
raw_code, usage = call_llm(model_key, prompt_text)
run_duration = time.time() - run_start_time

# 更新全局統計
stats.successful_runs += 1
stats.total_tokens_prompt += usage.get('prompt', 0)
stats.total_tokens_completion += usage.get('completion', 0)
stats.total_time_seconds += run_duration

# 更新模型級統計
stats.model_stats[model_key]['success'] += 1
stats.model_stats[model_key]['tokens_prompt'] += usage.get('prompt', 0)
stats.model_stats[model_key]['tokens_completion'] += usage.get('completion', 0)
stats.model_stats[model_key]['time'] += run_duration

# 更新技能級統計
stats.skill_stats[skill]['success'] += 1
stats.skill_stats[skill]['tokens_prompt'] += usage.get('prompt', 0)
stats.skill_stats[skill]['tokens_completion'] += usage.get('completion', 0)
stats.skill_stats[skill]['time'] += run_duration
```

#### 代碼位置
- 檔案: `scripts/run_experiment.py`
- 巢狀迴圈開始: 行 521-522
- 統計收集: 行 554-570

---

### 5️⃣ 實驗完成摘要輸出

#### 完成摘要示例
```
======================================================================
🎉 全部實驗完成！
======================================================================

📊 [全局統計]
  ✅ 成功: 15 / 90
  ❌ 失敗: 0
  ⚡ Token 總計: Prompt=12000, Completion=8500
  ⏱️  總耗時: 45.67s
  🔧 已修復: 3 個 (Healer 應用)

📈 [模型統計]
  Cloud Gemini 2.5 Flash:
    ✅ 5 | ❌ 0 | Token(4000/3000) | Time 15.50s
  Local Qwen2.5-Coder 14B:
    ✅ 5 | ❌ 0 | Token(4000/2750) | Time 18.20s
  Local Qwen2.5-Coder 7B:
    ✅ 5 | ❌ 0 | Token(4000/2750) | Time 11.97s

🎓 [技能統計]
  gh_ApplicationsOfDerivatives: ✅ 8 | ❌ 0 | Token(6500/4500)
  gh_FunctionComposition: ✅ 7 | ❌ 0 | Token(5500/4000)

📂 結果目錄: E:\Python\MathProject_AST_Research\experiments\results
======================================================================
```

#### 代碼位置
- 檔案: `scripts/run_experiment.py`
- 摘要生成: 行 572-600

---

## 📊 實驗流程對比

### V1.1.0 (舊版本)
```
1. 掃描技能
   ↓
2. 選擇技能
   ↓
3. 確認開始 (目標模型固定為 [Gemini, 14B, 7B])
   ↓
4. 執行巢狀迴圈
   ↓
5. 簡單的成功/失敗統計
```

### V1.2.0 (新版本) ⭐
```
1. 掃描技能
   ↓
2. 選擇技能 (支援單一或全部)
   ↓
3. 選擇模型 [0]全部 [1]Gemini [2]14B [3]7B ⭐新增
   ↓
4. 顯示實驗配置統計 ⭐新增
   ↓
5. 確認開始
   ↓
6. 執行巢狀迴圈 (實時統計收集) ⭐增強
   ↓
7. 詳細的全局/模型/技能級統計 ⭐新增
   ↓
8. 每個生成檔案帶有完整標頭 ⭐新增
```

---

## 🔧 技術實現細節

### 新增依賴
```python
from collections import defaultdict  # 用於簡化統計字典
```

### 新增常數
```python
MODEL_DISPLAY_NAMES = {
    "gemini-2.5-flash": "Cloud Gemini 2.5 Flash",
    "qwen2.5-coder-14b": "Local Qwen2.5-Coder 14B",
    "qwen2.5-coder-7b": "Local Qwen2.5-Coder 7B"
}
```

### 新增類別
```python
class ExperimentStats:
    # 完整的實驗統計數據容器
```

### 新增函數
1. `show_model_selection_menu()` - 模型選擇菜單
2. `_format_file_header()` - 檔案標頭生成

### 修改的函數
1. `main()` - 加入模型選擇和統計收集邏輯

---

## ✅ 測試驗證

### 測試腳本
- 檔案: `test_new_experiment_features.py`
- 測試項目:
  1. ✅ 檔案標頭格式化 - **通過**
  2. ✅ 實驗統計數據結構 - **通過**
  3. ✅ 模型選擇菜單數據 - **通過**

### 測試結果
```
🎉 所有測試通過！
```

---

## 📈 預期改進效果

### 1. 使用者體驗
- ✅ 模型選擇的靈活性 (可選單一或全部)
- ✅ 實驗前清晰的配置預覽
- ✅ 實驗後詳細的統計摘要

### 2. 科學價值
- ✅ 為每個生成檔案記錄完整的元數據 (便於后續分析)
- ✅ 按模型/技能的層級統計 (支援對比分析)
- ✅ Token 消耗和執行時間追蹤 (支援效率分析)

### 3. 研究可重現性
- ✅ 標頭中記錄模型/策略/時間 (支援複現)
- ✅ Healer 應用次數記錄 (支援修復追蹤)
- ✅ Token 統計 (支援成本分析)

---

## 🚀 後續工作

### 短期
- [ ] 執行完整的模型菜單測試 (互動式)
- [ ] 用真實 API 執行一次實驗 (驗證統計收集正確性)
- [ ] 驗證生成檔案的標頭完整性

### 中期
- [ ] 整合資料庫記錄 (持久化統計數據)
- [ ] 生成實驗報告 JSON/CSV
- [ ] 建立統計可視化儀表板

### 長期
- [ ] 支援部分 Ablation 組合執行
- [ ] 實驗結果的 ML 分析
- [ ] 科展報告自動生成

---

## 📝 更新日誌

| 版本 | 日期 | 變化 |
|------|------|------|
| V1.0.0 | 2026-01-29 | 初版 Mock 實現 |
| V1.1.0 | 2026-02-05 (A) | 真實 API 整合 |
| **V1.2.0** | **2026-02-05 (B)** | **模型選擇 + 統計 + 標頭** ⭐ |

---

## 📄 檔案修改摘要

### 修改的檔案
- `scripts/run_experiment.py` (~1095 行)
  - 新增: 3 個函數 + 1 個類別
  - 修改: main() 函數流程
  - 行數變化: 918 → 1095 (+177 行)

### 新增的檔案
- `test_new_experiment_features.py` (測試檔案，非生產)

---

**準備就緒！現在可以執行**: `python scripts/run_experiment.py`

