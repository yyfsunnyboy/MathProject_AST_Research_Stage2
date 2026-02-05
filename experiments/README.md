# 實驗管理目錄

本目錄用於管理所有 Ablation 實驗的輸入與輸出。

## 目錄結構

```
experiments/
├── golden_prompts/          # [輸入] 定案的靜態 Prompt 檔案
│   ├── {skill_id}_Ab1.txt   # Ab1: Bare Prompt (基礎版)
│   ├── {skill_id}_Ab2.txt   # Ab2: Engineered Prompt (工程化版)
│   └── {skill_id}_Ab3.txt   # Ab3: Engineered + Healer (完整版)
│
└── results/                 # [輸出] 生成的實驗結果
    └── {skill_id}/          # 第一層：技能名稱
        ├── Ab1/             # 第二層：實驗組別
        │   ├── sample_1.py       # 生成的程式碼
        │   ├── sample_1.json     # 該次生成的評測報告
        │   ├── sample_2.py
        │   ├── sample_2.json
        │   └── ...
        ├── Ab2/
        │   └── ...
        └── Ab3/
            └── ...
```

## 使用說明

### 1. Golden Prompts（靜態 Prompt 檔案）

這些是經過驗證、定案的 Prompt 模板，用於確保實驗的可重現性：

- **Ab1**: 模擬一般用戶的 Bare Prompt
- **Ab2**: 完整的 Engineered Prompt（含 Domain 函數庫）
- **Ab3**: 與 Ab2 相同，但會經過 AST Healer 修復

### 2. Results（實驗結果）

每個技能的實驗結果按照以下方式組織：

#### 檔案命名規範

- **程式碼檔案**: `sample_{n}.py`
  - `n`: 樣本編號（1-based）
  
- **評測報告**: `sample_{n}.json`
  - 包含：
    - `score`: MCRI 綜合評分
    - `metadata`: 生成時的 metadata（model, tokens, time 等）
    - `validation`: 驗證結果（syntax, logic, format 等）
    - `logs`: 生成與修復過程的日誌

#### JSON 報告範例

```json
{
  "sample_id": 1,
  "skill_id": "gh_ApplicationsOfDerivatives",
  "ablation_id": 2,
  "timestamp": "2026-02-04T10:30:00",
  "score": {
    "total": 85.5,
    "L1_syntax": 100,
    "L2_logic": 90,
    "L3_math": 75
  },
  "metadata": {
    "model": "qwen2.5-coder:14b",
    "tokens_in": 8192,
    "tokens_out": 661,
    "generation_time": 25.56
  },
  "validation": {
    "syntax_valid": true,
    "has_while_true": true,
    "answer_format_clean": false
  },
  "logs": [
    "✅ 代碼生成成功",
    "⚠️ 答案格式檢測到問題：包含符號前綴",
    "🔧 AST Healer 未啟用 (Ab2)"
  ]
}
```

## 實驗工作流程

### 階段 1: 準備 Golden Prompts

```bash
# 生成並儲存 Golden Prompts
python scripts/export_golden_prompts.py --skill gh_ApplicationsOfDerivatives
```

這會生成：
- `experiments/golden_prompts/gh_ApplicationsOfDerivatives_Ab1.txt`
- `experiments/golden_prompts/gh_ApplicationsOfDerivatives_Ab2.txt`
- `experiments/golden_prompts/gh_ApplicationsOfDerivatives_Ab3.txt`

### 階段 2: 執行批次實驗

```bash
# 為指定技能執行 100 次生成（每個 Ablation 組別）
python scripts/run_batch_experiment.py \
    --skill gh_ApplicationsOfDerivatives \
    --samples 100 \
    --ablations 1,2,3
```

這會生成：
- `experiments/results/gh_ApplicationsOfDerivatives/Ab1/sample_1.py` ~ `sample_100.py`
- `experiments/results/gh_ApplicationsOfDerivatives/Ab1/sample_1.json` ~ `sample_100.json`
- （同樣的結構用於 Ab2, Ab3）

### 階段 3: 分析實驗結果

```bash
# 生成統計報告
python scripts/analyze_experiment_results.py \
    --skill gh_ApplicationsOfDerivatives \
    --output reports/gh_ApplicationsOfDerivatives_analysis.md
```

## 遷移說明

### 從舊結構遷移

如果您有現有的實驗檔案在 `skills/` 目錄：

```bash
# 執行遷移腳本
python scripts/migrate_to_experiments.py
```

這會：
1. 將現有的 `skills/*_Ab*.py` 移動到對應的 `experiments/results/{skill}/Ab{n}/` 目錄
2. 生成對應的 JSON 報告（從檔案 metadata 提取）
3. 建立 Golden Prompts（從 PromptBuilder 生成）

## 維護建議

1. **定期備份**: Golden Prompts 是實驗的基礎，請使用 Git 追蹤
2. **清理舊結果**: 定期封存或刪除過時的實驗結果
3. **版本控制**: 在 Golden Prompts 檔案中標註版本號和修改日期

## 相關腳本

- `scripts/export_golden_prompts.py` - 匯出靜態 Prompt 檔案
- `scripts/run_batch_experiment.py` - 執行批次實驗
- `scripts/analyze_experiment_results.py` - 分析實驗結果
- `scripts/migrate_to_experiments.py` - 從舊結構遷移
