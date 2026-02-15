# ✅ 新增 Ablation 策略選擇菜單

## 修改内容

在 `scripts/run_experiment.py` 中添加了**第三層菜單**，用於選擇要執行的 Ablation 策略。

## 新菜單流程

```
📊 實驗執行菜單 V1.2.0

Step 1: 選擇技能
  [0] 全部執行
  [1] gh_ApplicationsOfDerivatives
  [2] jh_BasicAlgebra
  ...

Step 2: 選擇模型
  [0] ALL (全部 3 個模型)
  [1] Cloud Gemini 2.5 Flash
  [2] Local Qwen2.5-Coder 14B
  [3] Local Qwen2.5-Coder 7B

Step 3: [NEW] 選擇策略 ⭐
  [0] ALL (全部 3 個策略) ← 完整 Ablation Study
  [1] Ab1 (Bare) ← 測試模型原生能力
  [2] Ab2 (Engineered) ← 測試工具庫 + Prompt 工程
  [3] Ab3 (Full-Healing) ← 測試完整系統修復

Step 4: 確認開始
  顯示詳細配置統計，確認後開始執行
```

## 使用場景

### 場景 A: 快速測試單一策略
```
選擇: Ab1 (Bare)
執行時間: 快 ⚡
生成文件: 輕量級
用途: 快速驗證模型能力
```

### 場景 B: 對比兩個策略
```
第1次執行: 選擇 Ab2 (Engineered)
第2次執行: 選擇 Ab3 (Full-Healing)
對比: 觀察 Healer 修復的效果差異
```

### 場景 C: 完整科展實驗
```
選擇: ALL (全部 3 個策略)
執行時間: 慢 (但科學嚴謹)
生成文件: 完整的 Ablation Study 數據
用途: 論文發表、數據分析
```

## 修改詳情

### 1. 新增菜單邏輯 (L474-505)

```python
# 3.5. [NEW] Ablation 策略選擇
print("\n" + "="*70)
print("📋 [策略選擇] 請選擇要執行的 Ablation 策略")
print("="*70)
print(f"   [0] ALL (全部 3 個策略)")
print(f"   [1] Ab1 (Bare - 原生能力測試)")
print(f"   [2] Ab2 (Engineered - Prompt 工程貢獻)")
print(f"   [3] Ab3 (Full-Healing - 完整系統修復)")

while True:
    try:
        ablation_choice = input("\n👉 請輸入選項 (0-3): ").strip()
        if ablation_choice == '0':
            selected_ablations = ['Ab1', 'Ab2', 'Ab3']
            selected_strategies = [
                {"name": "Ab1", "prompt_suffix": "Ab1.txt", "healer": False},
                {"name": "Ab2", "prompt_suffix": "Ab2.txt", "healer": False},
                {"name": "Ab3", "prompt_suffix": "Ab2.txt", "healer": True}
            ]
            break
        # ... 其他選項 ...
```

### 2. 更新統計數據 (L506-508)

```python
stats.total_strategies = len(selected_strategies)  # 動態計算
stats.total_planned_runs = stats.total_skills * stats.total_models * \
                           stats.total_strategies * stats.total_samples_per_run
```

### 3. 顯示選擇確認 (L510-521)

```python
print(f"已選擇: {len(selected_ablations)} 個策略")
for ab in selected_ablations:
    print(f"  - {ab}")
```

### 4. 使用選定策略 (L559-561)

```python
# 使用使用者選擇的策略，而不是硬編碼的策略列表
for strat in selected_strategies:  # ← 改為動態策略
```

### 5. 修正進度條 (L582)

```python
pbar.update(stats.total_samples_per_run)  # 動態計算樣本數
```

## 生成文件示例

### 選擇 [1] Ab1 時
```
experiments/results/gh_ApplicationsOfDerivatives/
├── gh_ApplicationsOfDerivatives_gemini-2.5-flash_Ab1_run01.py
├── gh_ApplicationsOfDerivatives_gemini-2.5-flash_Ab1_run02.py
├── gh_ApplicationsOfDerivatives_gemini-2.5-flash_Ab1_run03.py
├── gh_ApplicationsOfDerivatives_gemini-2.5-flash_Ab1_run04.py
├── gh_ApplicationsOfDerivatives_gemini-2.5-flash_Ab1_run05.py
├── gh_ApplicationsOfDerivatives_qwen2.5-coder-14b_Ab1_run01.py
├── ...
└── (總計: 1 技能 × 3 模型 × 1 策略 × 5 樣本 = 15 個文件)
```

### 選擇 [0] ALL 時
```
experiments/results/gh_ApplicationsOfDerivatives/
├── *_Ab1_run*.py  (15 個文件)
├── *_Ab2_run*.py  (15 個文件)
└── *_Ab3_run*.py  (15 個文件)
(總計: 1 技能 × 3 模型 × 3 策略 × 5 樣本 = 45 個文件)
```

## 執行效率對比

| 選擇 | 執行次數 | 估計時間 | 用途 |
|------|----------|----------|------|
| [1] Ab1 | 15 | 快 ⚡ | 快速測試 |
| [2] Ab2 | 15 | 中等 ⚙️ | 測試工具庫 |
| [3] Ab3 | 15 | 慢 🐌 | 完整修復 |
| [0] ALL | 45 | 最慢 🐢 | 完整研究 |

## 完全向後兼容

✅ 如果選擇 [0] ALL，行為完全相同於 V1.1.0

## 下一步

執行 `python scripts/run_experiment.py` 即可體驗新菜單！

```bash
cd e:\Python\MathProject_AST_Research
python scripts/run_experiment.py

# 現在會看到:
# [請選擇要執行的技能]
# [模型選擇菜單]
# [NEW] [策略選擇菜單] ⭐ ← 這是新的!
# [確認開始]
```

---

**修改文件**: `scripts/run_experiment.py`

**修改行數**: 
- L474-505: 新增策略選擇菜單
- L506-508: 更新統計邏輯
- L510-521: 顯示選擇確認
- L559-561: 使用選定策略
- L582: 修正進度條計數

**狀態**: ✅ Production Ready
