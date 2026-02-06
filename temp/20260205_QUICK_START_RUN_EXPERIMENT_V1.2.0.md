# 🚀 快速使用指南：run_experiment.py V1.2.0

## 📋 三層選擇菜單

### 層級 1️⃣：技能選擇
```
======================================================================
📚 [技能選擇] 請選擇要執行實驗的技能範圍
======================================================================
   [0] ALL (全部 20 個技能)
   [1] gh_ApplicationsOfDerivatives
   [2] gh_FunctionComposition
   ...
   [20] gh_SkillName

👉 請輸入選項: 0  ← 選擇全部或單一技能
```

### 層級 2️⃣：模型選擇 ⭐ 新增
```
======================================================================
🤖 [模型選擇] 請選擇要執行的模型範圍
======================================================================
   [0] ALL (全部 3 個模型)
   [1] Cloud Gemini 2.5 Flash          ← Google Cloud
   [2] Local Qwen2.5-Coder 14B         ← 本地 14B 版本
   [3] Local Qwen2.5-Coder 7B          ← 本地 7B 版本

👉 請輸入選項 (0-3): 0  ← 選擇全部或單一模型
```

### 層級 3️⃣：確認與配置統計 ⭐ 增強
```
已選擇: 1 個技能
已選擇: 2 個模型
  - Cloud Gemini 2.5 Flash
  - Local Qwen2.5-Coder 14B

📊 實驗配置統計:
  技能數: 1
  模型數: 2
  策略數: 3
  每組樣本數: 5
  📈 總執行次數: 30

👉 確定要開始實驗嗎? (y/n): y
```

---

## 🎯 常見使用場景

### 場景 1: 快速測試單一模型
```
技能選擇: 1 (選擇第一個技能)
模型選擇: 1 (選擇 Gemini)
↓
執行次數: 1 × 1 × 3 × 5 = 15 次實驗
預計耗時: ~2-5 分鐘
```

### 場景 2: 測試本地模型對比
```
技能選擇: 0 (全部技能，假設 3 個)
模型選擇: 2 或 3 (選擇 Qwen 其中一個)
↓
執行次數: 3 × 1 × 3 × 5 = 45 次實驗
預計耗時: ~15-30 分鐘
```

### 場景 3: 完整實驗執行
```
技能選擇: 0 (全部 20 個技能)
模型選擇: 0 (全部 3 個模型)
↓
執行次數: 20 × 3 × 3 × 5 = 900 次實驗
預計耗時: ~2-4 小時（取決於 API 和本地模型速度）
```

---

## 📊 生成文件的標頭範例

### Ab1 (簡單 Prompt，無修復)
```python
# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: Cloud Gemini 2.5 Flash | Strategy: V1.1.0 Real API Integration
# Ablation ID: 1 | Name: Ab1 | Healer: OFF
# Performance: 2.45s | Tokens: In=1200, Out=850
# Created At: 2026-02-05 14:30:12
# Healer Fixes: 0
# ==============================================================================

def generate(level=1):
    """生成題目"""
    ...
```

### Ab2 (精細 Prompt，無修復)
```python
# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: Local Qwen2.5-Coder 14B | Strategy: V1.1.0 Real API Integration
# Ablation ID: 2 | Name: Ab2 | Healer: OFF
# Performance: 3.12s | Tokens: In=2500, Out=1750
# Created At: 2026-02-05 14:30:15
# Healer Fixes: 0
# ==============================================================================

def generate(level=1):
    """生成題目"""
    ...
```

### Ab3 (精細 Prompt，啟用修復)
```python
# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: Local Qwen2.5-Coder 7B | Strategy: V1.1.0 Real API Integration
# Ablation ID: 3 | Name: Ab3 | Healer: ON
# Performance: 1.89s | Tokens: In=2500, Out=1200
# Created At: 2026-02-05 14:30:17
# Healer Fixes: 2
# ==============================================================================

def generate(level=1):
    """生成題目"""
    ...
```

---

## 📈 實驗完成摘要

### 全局統計
```
📊 [全局統計]
  ✅ 成功: 885 / 900
  ❌ 失敗: 15
  ⚡ Token 總計: Prompt=1,050,000, Completion=756,000
  ⏱️  總耗時: 3,245.67s (約 54 分鐘)
  🔧 已修復: 285 個 (Healer 應用)
```

### 模型級對比
```
📈 [模型統計]
  Cloud Gemini 2.5 Flash:
    ✅ 300 | ❌ 0 | Token(350000/250000) | Time 850.5s
  Local Qwen2.5-Coder 14B:
    ✅ 295 | ❌ 5 | Token(350000/255000) | Time 1200.2s
  Local Qwen2.5-Coder 7B:
    ✅ 290 | ❌ 10 | Token(350000/251000) | Time 1195.0s
```

### 技能級分析
```
🎓 [技能統計]
  gh_ApplicationsOfDerivatives: ✅ 135 | ❌ 0 | Token(157500/112500)
  gh_FunctionComposition: ✅ 135 | ❌ 0 | Token(157500/112500)
  ...
```

---

## 🔄 工作流程圖

```
開始
  ↓
掃描技能目錄
  ↓
顯示技能菜單
  ↓
用戶選擇技能 [0全部/1-N單一] ←→ 驗證選擇
  ↓
顯示模型菜單 ⭐ 新增
  ↓
用戶選擇模型 [0全部/1-3單一] ←→ 驗證選擇 ⭐ 新增
  ↓
計算總次數並顯示配置統計 ⭐ 新增
  ↓
用戶確認開始
  ↓
┌─ 技能迴圈
│  ├─ 模型迴圈
│  │  ├─ 策略迴圈 (Ab1/Ab2/Ab3)
│  │  │  ├─ 樣本迴圈 (1-5)
│  │  │  │  ├─ 呼叫 LLM
│  │  │  │  ├─ 收集統計 ⭐ 新增
│  │  │  │  ├─ 應用 Healer
│  │  │  │  ├─ 生成標頭 ⭐ 新增
│  │  │  │  └─ 存檔
│  │  │  └─ 更新模型/技能統計 ⭐ 新增
│  │  └─
│  └─
└─
  ↓
生成詳細統計摘要 ⭐ 新增
  ↓
顯示完成信息
  ↓
結束
```

---

## 🛠️ 數據結構速查

### 每個 run 的標頭信息
```python
{
    'skill_id': str,           # 技能 ID
    'model_name': str,         # 顯示名稱 (如 "Cloud Gemini 2.5 Flash")
    'ablation_id': int,        # 1/2/3
    'ablation_name': str,      # "Ab1"/"Ab2"/"Ab3"
    'duration': float,         # 秒
    'prompt_tokens': int,      # 前向 token 數
    'completion_tokens': int,  # 后向 token 數
    'created_at': str,         # ISO 時間戳
    'healer_status': str,      # "ON"/"OFF"
    'healer_fixes': int        # 修復次數
}
```

### 全局統計容器
```python
stats.total_planned_runs      # = skills × models × 3 × 5
stats.successful_runs         # 實際成功數
stats.failed_runs             # 實際失敗數
stats.total_tokens_prompt     # 累計
stats.total_tokens_completion # 累計
stats.total_time_seconds      # 累計
stats.healed_count            # 已應用 Healer 的次數
stats.model_stats[key]        # 模型級統計
stats.skill_stats[key]        # 技能級統計
```

---

## 💾 檔案組織

### 目錄結構
```
experiments/results/
├── gh_ApplicationsOfDerivatives/
│   ├── gh_ApplicationsOfDerivatives_gemini-2.5-flash_Ab1_run01.py
│   ├── gh_ApplicationsOfDerivatives_gemini-2.5-flash_Ab1_run02.py
│   ├── ...
│   ├── gh_ApplicationsOfDerivatives_qwen2.5-coder-14b_Ab2_run01.py
│   ├── ...
│   └── gh_ApplicationsOfDerivatives_qwen2.5-coder-7b_Ab3_run05.py
├── gh_FunctionComposition/
│   └── ...
└── ...
```

### 檔名格式
```
{skill_id}_{model_key}_{ablation_name}_run{sample:02d}.py

例如:
gh_ApplicationsOfDerivatives_gemini-2.5-flash_Ab1_run01.py
│                                 │                 │   │
│                                 │                 │   └─ 樣本編號 (01-05)
│                                 │                 └────── Ablation (Ab1/Ab2/Ab3)
│                                 └──────────────────────── 模型 Key (連字號)
└───────────────────────────────────────────────────────── 技能 ID
```

---

## 🎓 科學應用

### 1. Ablation Study（消融研究）
比較三個策略的效果：
- **Ab1**: 簡單 Prompt → 測試模型基線能力
- **Ab2**: 精細 Prompt → 測試提示工程的貢獻
- **Ab3**: + Healer 修復 → 測試系統完整能力

### 2. 模型對比
- **Gemini (Cloud)**: 高準確度，高成本
- **Qwen 14B (Local)**: 中等質量，無網路依賴
- **Qwen 7B (Local)**: 快速推理，較低資源消耗

### 3. 效率分析
通過 Token 統計和執行時間，評估：
- 模型的推理效率 (Token/秒)
- 成本效益 (正確性 vs Token 消耗)
- 硬件資源消耗

---

## 📞 故障排除

| 問題 | 原因 | 解決方案 |
|------|------|--------|
| 找不到技能 | `experiments/results` 目錄為空 | 先運行 `python generate_and_validate_applications.py` |
| Gemini API 失敗 | 未設定 `GEMINI_API_KEY` | 檢查 `.env` 檔案，確保 API Key 正確 |
| Ollama 連接失敗 | Ollama 服務未啟動 | 執行 `ollama serve`，確保監聽 `http://localhost:11434` |
| Token 數為 0 | 響應為空 | 檢查 Prompt 檔案是否存在，LLM API 是否正常 |

---

**準備好了嗎？執行以下命令開始實驗：**

```bash
python scripts/run_experiment.py
```

祝您實驗順利！🚀

