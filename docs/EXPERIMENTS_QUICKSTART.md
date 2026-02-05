# 實驗架構快速入門

## 🎯 目標

將實驗輸入（Prompts）和輸出（生成結果）分開管理，提供清晰的目錄結構。

## 📁 新的目錄結構

```
experiments/
├── golden_prompts/          # [輸入] 定案的靜態 Prompt
│   ├── gh_ApplicationsOfDerivatives_Ab1.txt
│   ├── gh_ApplicationsOfDerivatives_Ab2.txt
│   └── gh_ApplicationsOfDerivatives_Ab3.txt
│
└── results/                 # [輸出] 實驗結果
    └── gh_ApplicationsOfDerivatives/
        ├── Ab1/             # 基礎版（Bare Prompt）
        │   ├── sample_1.py
        │   ├── sample_1.json
        │   ├── sample_2.py
        │   ├── sample_2.json
        │   └── ...
        ├── Ab2/             # 工程化版（Engineered Prompt）
        │   └── ...
        └── Ab3/             # 完整版（+ Healer）
            └── ...
```

## 🚀 快速開始

### 步驟 1: 執行一鍵設置

```bash
python scripts/setup_experiments.py
```

這會自動：
- ✅ 建立目錄結構
- ✅ 更新 .gitignore
- ✅ 匯出範例 Golden Prompts

### 步驟 2: 匯出所有 Golden Prompts

```bash
# 匯出所有技能
python scripts/export_golden_prompts.py --all

# 或只匯出特定技能
python scripts/export_golden_prompts.py --skill gh_ApplicationsOfDerivatives
```

### 步驟 3: 執行批次實驗

```bash
# 為單一技能執行 100 次生成（所有 Ablation）
python scripts/run_batch_experiment.py \
    --skill gh_ApplicationsOfDerivatives \
    --samples 100

# 只執行特定 Ablation
python scripts/run_batch_experiment.py \
    --skill gh_ApplicationsOfDerivatives \
    --samples 100 \
    --ablations 2,3
```

### 步驟 4: （可選）遷移現有檔案

如果您已經有在 `skills/` 目錄中的實驗檔案：

```bash
# 先預覽遷移操作
python scripts/migrate_to_experiments.py --dry-run

# 確認無誤後執行遷移
python scripts/migrate_to_experiments.py --backup
```

## 📊 實驗結果格式

### 程式碼檔案
- 路徑: `experiments/results/{skill_id}/Ab{n}/sample_{i}.py`
- 內容: 生成的完整 Python 程式碼

### 評測報告
- 路徑: `experiments/results/{skill_id}/Ab{n}/sample_{i}.json`
- 內容:

```json
{
  "sample_id": 1,
  "skill_id": "gh_ApplicationsOfDerivatives",
  "ablation_id": 2,
  "timestamp": "2026-02-04T10:30:00",
  "metadata": {
    "model": "qwen2.5-coder:14b",
    "tokens_in": 8192,
    "tokens_out": 661,
    "generation_time": 25.56
  },
  "validation": {
    "syntax_valid": true,
    "has_while_true": true,
    "verification_status": "PASSED"
  }
}
```

## 📚 可用腳本

| 腳本 | 功能 | 使用範例 |
|------|------|---------|
| `setup_experiments.py` | 一鍵設置實驗架構 | `python scripts/setup_experiments.py` |
| `export_golden_prompts.py` | 匯出靜態 Prompts | `python scripts/export_golden_prompts.py --all` |
| `run_batch_experiment.py` | 執行批次實驗 | `python scripts/run_batch_experiment.py --skill gh_ApplicationsOfDerivatives --samples 100` |
| `migrate_to_experiments.py` | 遷移現有檔案 | `python scripts/migrate_to_experiments.py --dry-run` |

## 🔧 進階使用

### 自訂實驗參數

編輯 `run_batch_experiment.py`，調整：
- 模型名稱
- Token 限制
- Healer 設定

### 分析實驗結果

實驗結果儲存為結構化 JSON，可用於：
- 統計分析（成功率、效能等）
- 視覺化（圖表、趨勢）
- 自動化報告生成

### Git 版本控制

- ✅ **追蹤**: Golden Prompts（靜態檔案）
- ❌ **忽略**: 實驗結果（動態生成，數量多）

## 📖 完整文件

詳細說明請參考：[experiments/README.md](../experiments/README.md)
