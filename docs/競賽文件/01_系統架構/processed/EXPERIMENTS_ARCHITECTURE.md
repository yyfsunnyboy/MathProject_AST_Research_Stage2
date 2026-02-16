# 實驗目錄架構總覽

## 📂 完整目錄結構

```
MathProject_AST_Research/
│
├── core/                               # 核心程式碼
│   ├── prompts/
│   │   ├── prompt_builder.py          # Prompt 構建器
│   │   ├── domain_function_library.py # Domain 函數庫
│   │   └── polynomial_helpers_template.py
│   ├── code_generator.py              # 代碼生成器
│   ├── healer/                        # AST 修復器
│   └── ...
│
├── experiments/                        # ⭐ 新增：實驗管理中心
│   │
│   ├── golden_prompts/                # [輸入] 靜態 Prompt 檔案
│   │   ├── gh_ApplicationsOfDerivatives_Ab1.txt
│   │   ├── gh_ApplicationsOfDerivatives_Ab2.txt
│   │   ├── gh_ApplicationsOfDerivatives_Ab3.txt
│   │   ├── jh_LinearEquations_Ab1.txt
│   │   └── ...
│   │
│   ├── results/                       # [輸出] 實驗結果
│   │   │
│   │   ├── gh_ApplicationsOfDerivatives/   # 技能 1
│   │   │   ├── Ab1/                        # Baseline (Bare Prompt)
│   │   │   │   ├── sample_1.py
│   │   │   │   ├── sample_1.json
│   │   │   │   ├── sample_2.py
│   │   │   │   ├── sample_2.json
│   │   │   │   └── ...（共 100 個樣本）
│   │   │   │
│   │   │   ├── Ab2/                        # Engineered Prompt
│   │   │   │   ├── sample_1.py
│   │   │   │   ├── sample_1.json
│   │   │   │   └── ...
│   │   │   │
│   │   │   └── Ab3/                        # Engineered + Healer
│   │   │       ├── sample_1.py
│   │   │       ├── sample_1.json
│   │   │       └── ...
│   │   │
│   │   ├── jh_LinearEquations/            # 技能 2
│   │   │   ├── Ab1/
│   │   │   ├── Ab2/
│   │   │   └── Ab3/
│   │   │
│   │   └── ...（其他技能）
│   │
│   └── README.md                      # 實驗說明文件
│
├── scripts/                           # 工具腳本
│   ├── setup_experiments.py           # ⭐ 新增：一鍵設置
│   ├── export_golden_prompts.py       # ⭐ 新增：匯出 Prompts
│   ├── run_batch_experiment.py        # ⭐ 新增：批次實驗
│   ├── migrate_to_experiments.py      # ⭐ 新增：遷移工具
│   ├── sync_skills_files.py           # 現有：單次生成
│   └── research_runner.py             # 現有：研究執行器
│
├── skills/                            # 現有：暫時保留（將逐步淘汰）
│   ├── gh_ApplicationsOfDerivatives_14b_Ab1.py
│   ├── gh_ApplicationsOfDerivatives_14b_Ab2.py
│   ├── gh_ApplicationsOfDerivatives_14b_Ab3.py
│   └── ...
│
├── docs/                              # 文件
│   ├── EXPERIMENTS_QUICKSTART.md      # ⭐ 新增：實驗快速入門
│   └── ...
│
├── reports/                           # 分析報告（保留）
├── temp/                              # 臨時檔案（保留）
└── ...
```

## 🔄 工作流程對比

### 舊工作流程
```
1. 執行 sync_skills_files.py
2. 生成到 skills/ 目錄
3. 檔案混在一起，難以管理
4. 手動分析結果
```

### 新工作流程
```
1. 準備階段
   ├─ 匯出 Golden Prompts (一次性)
   └─ 設置實驗目錄結構

2. 實驗階段
   ├─ 執行批次實驗 (100 次/Ablation)
   ├─ 自動儲存到分類目錄
   └─ 自動生成評測報告 (JSON)

3. 分析階段
   ├─ 讀取 JSON 報告
   ├─ 統計分析（成功率、效能）
   └─ 生成視覺化圖表
```

## 📊 資料流向

```
┌─────────────────────┐
│  MASTER_SPEC (DB)   │
│  ↓                  │
│  PromptBuilder      │ ─────────┐
└─────────────────────┘          │
                                 ↓
                    ┌─────────────────────────┐
                    │ Golden Prompts (靜態)    │
                    │ experiments/golden_prompts/│
                    └─────────────────────────┘
                                 │
                                 ↓
                    ┌─────────────────────────┐
                    │  Batch Experiment       │
                    │  (run_batch_experiment)  │
                    └─────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ↓                         ↓
        ┌──────────────────┐      ┌──────────────────┐
        │  Code Generator   │      │  Code Generator   │
        │  + Basic Cleanup  │      │  + Healer         │
        │  (Ab2)            │      │  (Ab3)            │
        └──────────────────┘      └──────────────────┘
                    │                         │
                    ↓                         ↓
        ┌──────────────────┐      ┌──────────────────┐
        │ results/Ab2/     │      │ results/Ab3/     │
        │ ├─ sample_1.py   │      │ ├─ sample_1.py   │
        │ ├─ sample_1.json │      │ ├─ sample_1.json │
        │ └─ ...           │      │ └─ ...           │
        └──────────────────┘      └──────────────────┘
                    │                         │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │  Analysis & Reports     │
                    │  (統計、視覺化、論文)    │
                    └─────────────────────────┘
```

## 🎯 關鍵優勢

### 1. 可重現性
- Golden Prompts 固定，確保實驗可重複
- 每次實驗的完整參數都記錄在 JSON

### 2. 可擴展性
- 輕鬆添加新技能（只需新增目錄）
- 支援多模型對比（14b, cloud 等）

### 3. 易於分析
- 結構化資料（JSON）便於程式化分析
- 自動化報告生成

### 4. 版本控制友善
- Golden Prompts 可追蹤（Git）
- 實驗結果被忽略（避免污染 repo）

## 📝 檔案命名規範

### Golden Prompts
```
{skill_id}_Ab{n}.txt

範例:
- gh_ApplicationsOfDerivatives_Ab1.txt
- jh_LinearEquations_Ab2.txt
```

### 實驗結果
```
sample_{序號}.py       # 程式碼
sample_{序號}.json     # 評測報告

範例:
- sample_1.py
- sample_1.json
- sample_42.py
- sample_42.json
```

## 🔧 維護指南

### 定期任務
1. **每週**：清理失敗的實驗結果
2. **每月**：封存舊的實驗資料
3. **版本更新時**：更新 Golden Prompts

### 備份建議
- Golden Prompts: Git 追蹤 ✅
- 實驗結果: 外部備份（Google Drive, S3 等）
- JSON 報告: 可考慮追蹤（檔案小）

## 📚 相關文件

- [實驗快速入門](EXPERIMENTS_QUICKSTART.md)
- [experiments/README.md](../experiments/README.md)
- [3x3 實驗設計詳解](競賽文件/🧬3x3實驗設計詳解與過程.md)
