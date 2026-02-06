# 實驗執行驗證清單 (Quick Checklist)

## 🚀 前置準備

### 環境檢查
- [ ] Python 3.9+ 已安裝
- [ ] Flask + SQLAlchemy 已安裝
- [ ] Google Generative AI SDK 已安裝
- [ ] .env 檔案已配置 (GEMINI_API_KEY 等)
- [ ] 資料庫已初始化 (`python utils/init_db.py`)

### 代碼檢查
- [ ] scripts/run_experiment.py 語法正確
- [ ] models.py ExperimentLog 模型存在
- [ ] test_new_experiment_features.py 已通過

---

## 📋 實驗執行步驟

### 步驟 1: 啟動實驗
```bash
cd e:\Python\MathProject_AST_Research
python scripts/run_experiment.py
```

### 步驟 2: 選擇模型
```
[0] ALL (全部 3 個模型)
[1] Cloud Gemini 2.5 Flash
[2] Local Qwen2.5-Coder 14B
[3] Local Qwen2.5-Coder 7B

選擇: 1  # 選擇 Gemini (推薦用於測試)
```

### 步驟 3: 等待執行完成
```
進度提示:
✅ Skill: gh_ApplicationsOfDerivatives
   ✅ Model: Cloud Gemini 2.5 Flash
      ✅ Ab1 (No Healer): Run 1 (5.23s) | Tokens: In=1592, Out=388 | Success
      ...
```

---

## ✅ 驗證檢查項目

### A. 檔案生成驗證
```
位置: experiments/{date}/{model}/{skill}/

檢查項目:
- [ ] 檔案存在 (格式: {skill}_{model}_{ab}_{run}.py)
- [ ] 檔案數量正確 (應為: 技能數 × 模型數 × Ablation × 樣本數)
- [ ] 檔案編碼為 UTF-8
- [ ] 檔案大小 > 500 bytes
```

### B. 標頭格式驗證

**檔案位置**: `experiments/{date}/{model}/{skill}/{filename}.py`

**驗證步驟**:
1. 開啟生成的 .py 檔案
2. 檢查前 10 行 (標頭)
3. 驗證以下字段:

#### 必需字段檢查清單
```
# ══════════════════════════════════════════════════════════════════════════════
# ID: {skill_id}                                                          ✅ 檢查
# Model: {model_name} | Strategy: V10.1 Modular Refactored                ✅ 檢查
# Ablation ID: {id} | Basic Cleanup: ENABLED | Advanced Healer: {ON/OFF}  ✅ 檢查
# Performance: {time}s | Tokens: In={prompt}, Out={completion}            ✅ 檢查
# Created At: {timestamp}                                                  ✅ 檢查
# Fix Status: {status} | Fixes: {details}                                 ✅ 檢查
# Verification: Internal Logic Check = PASSED                              ✅ 檢查
# ══════════════════════════════════════════════════════════════════════════════
```

### C. Fix Status 驗證

**Ab1 預期格式**:
```
Fix Status: [No Healer] | Fixes: None
```

**Ab2 預期格式**:
```
Fix Status: [Basic Only] | Fixes: Basic=1, Advanced=None
```

**Ab3 預期格式**:
```
Fix Status: [Advanced Healer] | Fixes: Basic=1, Advanced=(Regex={N}, AST=0)
```

### D. 資料庫記錄驗證

**查詢命令**:
```python
# 連接到 Flask app
from app import app
from models import db, ExperimentLog

with app.app_context():
    # 查詢最近的實驗記錄
    recent = db.session.query(ExperimentLog)\
        .order_by(ExperimentLog.id.desc())\
        .limit(5).all()
    
    for log in recent:
        print(f"Skill: {log.skill_id}")
        print(f"  Model: {log.model_name}")
        print(f"  Duration: {log.duration_seconds:.2f}s")
        print(f"  Tokens: {log.prompt_tokens}/{log.completion_tokens}")
        print(f"  Success: {log.is_success}")
        print(f"  Repaired: {log.repaired}")
        print()
```

**驗證項目**:
- [ ] 記錄數量正確
- [ ] skill_id 正確
- [ ] model_name 正確
- [ ] ablation_id 正確
- [ ] duration_seconds > 0
- [ ] prompt_tokens > 0
- [ ] completion_tokens > 0
- [ ] is_success = True
- [ ] raw_response 不為空
- [ ] final_code 不為空

---

## 🐛 常見問題排查

### 問題 1: 標頭格式不匹配
**症狀**: 生成的檔案標頭與預期不符  
**排查步驟**:
1. 檢查 _format_file_header() 函數
2. 檢查傳遞的參數是否正確
3. 驗證 ablation_id 值 (應為 1/2/3)

### 問題 2: 資料庫記錄失敗
**症狀**: 沒有新記錄被添加到 ExperimentLog  
**排查步驟**:
1. 檢查 HAS_DB 標誌是否為 True
2. 檢查資料庫連接是否正常
3. 查看 tqdm 輸出中的異常信息

### 問題 3: 檔案未生成
**症狀**: 沒有新的 .py 檔案被建立  
**排查步驟**:
1. 檢查輸出目錄是否存在
2. 檢查檔名格式是否正確
3. 檢查是否有文件寫入權限

---

## 📊 驗證結果記錄

### 第一次運行
```
日期: ________
時間: ________
模型: ________
技能數: ________
檔案數: ________
成功率: ________
總耗時: ________
```

### 標頭格式驗證
```
檔案名: ________
Ab1 標頭格式: ________
Ab2 標頭格式: ________
Ab3 標頭格式: ________
Fix Status 正確性: ________
```

### 資料庫驗證
```
總記錄數: ________
表名: ExperimentLog
主鍵 ID: ________
最新記錄時間: ________
資料完整性: ________
```

---

## 🎯 驗收標準

### 滿分標準 (Green ✅)
- [ ] 所有檔案正確生成
- [ ] 標頭格式完全匹配
- [ ] Fix Status 字段正確
- [ ] 資料庫記錄完整
- [ ] 執行無異常

### 合格標準 (Yellow ⚠️)
- [ ] 大部分檔案正確生成 (90%+)
- [ ] 標頭格式基本正確
- [ ] Fix Status 字段大部分正確
- [ ] 資料庫記錄較完整 (85%+)

### 不合格標準 (Red ❌)
- [ ] 檔案生成失敗率 > 10%
- [ ] 標頭格式不符
- [ ] Fix Status 字段缺失
- [ ] 資料庫記錄異常

---

## 📝 備註

**Last Updated**: 2026-02-05  
**Version**: V1.2.0 驗收清單  
**Prepared by**: GitHub Copilot

### 相關文檔
- EXPERIMENT_V1_2_0_VERIFICATION.md - 詳細驗證報告
- README.md - 專案概述
- code_generator.py - 標頭格式參考

