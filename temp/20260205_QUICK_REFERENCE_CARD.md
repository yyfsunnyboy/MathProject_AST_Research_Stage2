# 🎯 run_experiment.py V1.2.0 快速參考卡

## 🚀 執行命令
```bash
python scripts/run_experiment.py
```

---

## 📋 菜單流程

### 第 1 層：技能選擇
```
[0] ALL (全部技能)
[1-N] 單一技能
```

### 第 2 層：模型選擇 ⭐ 新增
```
[0] ALL (全部 3 個模型)
[1] Cloud Gemini 2.5 Flash
[2] Local Qwen2.5-Coder 14B
[3] Local Qwen2.5-Coder 7B
```

### 第 3 層：確認
```
📊 配置統計 (新增)
✅ 確認開始? (y/n)
```

---

## 📊 生成的輸出統計

### 全局統計
```
✅ 成功: N / 總次數
❌ 失敗: N
⚡ Token: Prompt=N, Completion=N
⏱️  耗時: N.NNs
🔧 已修復: N (Healer)
```

### 模型級統計
```
模型名稱:
  ✅ 成功 | ❌ 失敗 | Token(P/C) | Time Ns
```

### 技能級統計
```
技能ID: ✅ 成功 | ❌ 失敗 | Token(P/C)
```

---

## 📄 生成檔案的標頭

```python
# ==============================================================================
# ID: 技能ID
# Model: 模型顯示名 | Strategy: V1.1.0 Real API Integration
# Ablation ID: N | Name: AbN | Healer: ON/OFF
# Performance: N.NNs | Tokens: In=N, Out=N
# Created At: YYYY-MM-DD HH:MM:SS
# Healer Fixes: N
# ==============================================================================
```

---

## 🎯 使用場景快速查詢

| 場景 | 選擇 | 執行次數 | 耗時 |
|------|------|---------|------|
| 快速測試 | 1 技能 × 1 模型 | 15 | ~2-5m |
| 本地測試 | 3 技能 × 1 模型 | 45 | ~15-30m |
| 完整測試 | 全部 × 全部 | 900+ | ~2-4h |

---

## 📈 數據收集矩陣

```
技能 × 模型 × 策略 × 樣本
  │     │       │      └─ run01-run05 (5個)
  │     │       └─────── Ab1/Ab2/Ab3 (3個)
  │     └──────────────── 選定的模型
  └────────────────────── 選定的技能
```

**計算公式**: `總次數 = 選定技能 × 選定模型 × 3 × 5`

---

## 🔧 關鍵函數位置

| 函數 | 行數 | 功能 |
|------|------|------|
| `show_model_selection_menu()` | 269-289 | 模型菜單 |
| `_format_file_header()` | 232-261 | 標頭生成 |
| `ExperimentStats` (類) | 80-114 | 統計容器 |
| 統計收集 | 454-470 | 巢狀迴圈內 |
| 統計輸出 | 572-600 | 完成摘要 |

---

## ✅ 驗證清單

執行前:
- [ ] `python test_new_experiment_features.py` ✅
- [ ] API 金鑰配置正確 ✅
- [ ] Ollama 服務啟動 (本地模型) ✅

執行後:
- [ ] 檔案標頭格式正確 ✅
- [ ] 統計數據準確 ✅
- [ ] 無錯誤日誌 ✅

---

## 📚 文檔速查

| 文檔 | 用途 |
|------|------|
| UPGRADE_REPORT.md | 詳細技術說明 |
| QUICK_START_GUIDE.md | 完整使用指南 |
| CHANGES_SUMMARY.md | 變更詳情 |
| 本卡片 | 快速參考 |

---

## 🆘 故障排除

| 問題 | 原因 | 解決 |
|------|------|------|
| 找不到技能 | 目錄空 | 先生成測試數據 |
| Gemini 失敗 | API Key 無效 | 檢查 .env |
| Ollama 失敗 | 服務未啟動 | 執行 `ollama serve` |
| Token=0 | 響應空 | 檢查 Prompt 檔案 |

---

## 💾 檔案位置

```
實驗結果:
  experiments/results/{skill_id}/{filename}.py

檔名格式:
  {skill}_{model}_{ablation}_run{N:02d}.py

例如:
  gh_ApplicationsOfDerivatives_gemini-2.5-flash_Ab1_run01.py
```

---

## 📊 統計數據字段

### 全局統計 (stats)
- total_planned_runs: 計劃次數
- successful_runs: 成功次數
- failed_runs: 失敗次數
- total_tokens_prompt: 總 Prompt tokens
- total_tokens_completion: 總 Completion tokens
- total_time_seconds: 總耗時
- healed_count: 已修復次數

### 模型統計 (stats.model_stats)
- success: 成功次數
- failure: 失敗次數
- tokens_prompt: Prompt tokens
- tokens_completion: Completion tokens
- time: 執行時間

### 技能統計 (stats.skill_stats)
- 同模型統計結構

---

## 🎯 Ablation Study 解釋

```
Ab1 (Bare):
  Prompt: 簡單
  Healer: OFF
  目標: 測試模型基線能力

Ab2 (Engineered):
  Prompt: 精細 (同 Ab1 的 Ab2.txt)
  Healer: OFF
  目標: 測試提示工程的貢獻

Ab3 (Full-Healing):
  Prompt: 精細 (同 Ab2)
  Healer: ON
  目標: 測試系統完整能力
```

---

## ⚡ 性能優化提示

1. **選擇模型**: 單一模型比全部快 3 倍
2. **選擇技能**: 單一技能比全部快 20 倍
3. **Ollama 速度**: 需要預熱，首次較慢
4. **Token 預估**: 實際 ≈ len(text) / 4

---

## 🌟 新增特性速覽

| 特性 | 位置 | 狀態 |
|------|------|------|
| 模型菜單 | 第 1 層後 | ✅ 新增 |
| 配置統計 | 確認前 | ✅ 新增 |
| 檔案標頭 | 每個生成檔 | ✅ 新增 |
| 詳細摘要 | 實驗完成後 | ✅ 新增 |
| 統計收集 | 巢狀迴圈中 | ✅ 新增 |

---

**最後更新**: 2026-02-05  
**版本**: V1.2.0  
**狀態**: ✅ 準備就緒

