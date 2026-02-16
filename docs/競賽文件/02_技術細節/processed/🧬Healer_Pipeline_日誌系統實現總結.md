# Healer Pipeline 日誌系統實現總結

**實現日期**: 2026-02-01 11:45  
**版本**: V1.0  
**預設級別**: VERBOSE_LEVEL=2 (詳細版)

---

## ✅ 已實現功能

### 1. **配置系統**

添加了環境變數配置：

```python
DEBUG_MODE = os.getenv('HEALER_DEBUG', '0') == '1'
VERBOSE_LEVEL = int(os.getenv('HEALER_VERBOSE', '2'))  # 0=minimal, 1=normal, 2=detailed
```

**使用方法**:
```powershell
# Windows PowerShell
$env:HEALER_VERBOSE = "0"  # 極簡版
$env:HEALER_VERBOSE = "1"  # 簡潔版
$env:HEALER_VERBOSE = "2"  # 詳細版（預設）
```

---

### 2. **日誌函數**

創建了5個專用日誌函數：

| 函數 | 用途 | 輸出級別 |
|------|------|---------| 
| `log_pipeline_header()` | Pipeline 啟動標題 | ≥1 |
| `log_step_start()` | 步驟開始 | ≥1 |
| `log_step_result()` | 步驟結果總結 | ≥1 |
| `log_fix_detail()` | 修復細節 | ≥2 |
| `log_pipeline_summary()` | Pipeline 總結 | ≥0 |

---

### 3. **詳細日誌輸出**

#### **Step 0: AI Generation**
- ✅ 模型名稱
- ✅ Prompt 長度
- ✅ Response tokens
- ✅ 生成時間

#### **Step 1: Basic Cleanup**
- ✅ 4 個清理項詳細說明
- ✅ 代碼長度變化（Before → After）

#### **Step 2: Regex Healer**
- ✅ 9 個子項檢查詳情
  - Complexity Checker
  - Loop Breaker
  - Garbage Cleaner
  - Hallucination Killer
  - LaTeX Protector
  - Tuple Return Fixer
  - Answer Format Fixer
- ✅ 代碼長度變化

#### **Step 3: AST Healer**
- ✅ 語法樹解析狀態
- ✅ 6 個子項檢查詳情
  - Parse AST
  - Hallucination Function Fixer
  - Dangerous Call Remover
  - Loop Condition Fixer
- ✅ Fail-fast 保護機制顯示
- ✅ AST 修復結果

#### **Step 5: Dynamic Sampling**
- ✅ Subprocess 執行狀態
- ✅ 每個 Sample 的成功/失敗
- ✅ 3/3 通過率顯示
- ✅ 5秒 Timeout 提示

#### **Final Summary**
- ✅ Pipeline 執行成功/失敗狀態
- ✅ 總修復統計（Basic + Regex + AST）
- ✅ 驗證狀態（PASSED/FAILED）
- ✅ 總耗時

---

## 📊 輸出範例

### **VERBOSE_LEVEL = 2 (詳細版，預設)**

```
╔════════════════════════════════════════════════════════════╗
║  🔬 Code Generation & Healing Pipeline                     ║
║  Skill: gh_ApplicationsOfDerivatives                       ║
║  Ablation: Ab3 (Full Healer)                               ║
╚════════════════════════════════════════════════════════════╝

┌─ Step 0: AI Code Generation ─────────────────────────────┐
│ Model: qwen2.5-coder:14b
│ ○ Prompt Length                     7120 tokens
│ ○ Response Tokens                   710 tokens
│ ○ Generation Time                   19.23s
│ 
│ 📊 結果: 0 項修復 | AI 生成完成 (19.23s, 710 tokens)
└──────────────────────────────────────────────────────────┘

┌─ Step 1: Basic Cleanup (All Ablations) ──────────────────┐
│ [進階修復啟動] Markdown + Trimming...
│ ✅ [1/4] 檢查 ```python 標記         → ✓ 發現 1 處
│ ○ [2/4] 檢查 ``` 標記                → ○ 無需修復
│ ○ [3/4] 檢查結尾標記                 → ○ 無需修復
│ ✅ [4/4] 清理前後空白                → ✓ 完成
│ 
│ 📊 結果: 1 項修復 | 代碼長度: 892 → 875 字符
└──────────────────────────────────────────────────────────┘

┌─ Step 2: Regex Healer (Ab2/Ab3) ─────────────────────────┐
│ [進階修復啟動] Regex Pattern Matching...
│ 
│ ⚠️  2.0  Complexity Checker          ⚠️  未使用分數 (建議檢查 MASTER_SPEC)
│ ✅ 2.05 Loop Breaker                 🔍 掃描危險迴圈: while True, while 1, while (True)
│ ○ 2.1  Garbage Cleaner              🔍 掃描孤立字符: `, ```...
│ ○ 2.2  Hallucination Killer          🔍 掃描幻覺函數: clean_expression
│ ✅ 2.5  LaTeX Protector              🔍 檢查 Domain Helper 輸出
│ ○ 2.3  Tuple Return Fixer           🔍 檢查返回格式
│ ✅ 2.35 Answer Format Fixer          🔍 檢查答案格式
│ 
│ 📊 結果: 3 項修復 | 代碼長度: 875 → 868 字符
└──────────────────────────────────────────────────────────┘

┌─ Step 3: AST Healer (Ab3 Only) ──────────────────────────┐
│ [語法樹修復啟動] Abstract Syntax Tree Analysis...
│ 
│ ✅ 3.1 Parse AST                     ✅ 語法樹解析成功
│ ○ 3.2 Hallucination Function Fixer  🔍 檢查未定義函數
│ ○ 3.3 Dangerous Call Remover        🔍 檢查危險函數: eval, exec, safe_eval
│ ○ 3.4 Loop Condition Fixer          🔍 檢查迴圈條件
│ 
│ 📊 結果: 0 項修復 | AST 結構正常
└──────────────────────────────────────────────────────────┘

┌─ Step 5: Dynamic Sampling (Safety Net) ──────────────────┐
│ [執行驗證] Subprocess with 5s Timeout...
│ 
│ ✅ Sample 1/3:                       ✓ 生成成功
│ ✅ Sample 2/3:                       ✓ 生成成功
│ ✅ Sample 3/3:                       ✓ 生成成功
│ 
│ 📊 結果: 0 項修復 | 驗證: 3/3 通過 | Timeout: 5s
└──────────────────────────────────────────────────────────┘

╔════════════════════════════════════════════════════════════╗
║  ✅ Pipeline 執行成功                                       ║
║                                                            ║
║  📊 修復統計（分階段累計）:                                    ║
║     • Basic Cleanup:    1 項                               ║
║     • Regex Healer:     3 項                               ║
║     • AST Healer:       0 項                               ║
║     • 總計修復:         4 項                               ║
║                                                            ║
║  驗證狀態: PASSED                                          ║
║  總耗時: 19.23s                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

### **VERBOSE_LEVEL = 1 (簡潔版)**

```
╔════════════════════════════════════════════════════════════╗
║  🔬 Code Generation & Healing Pipeline                     ║
║  Skill: gh_ApplicationsOfDerivatives                       ║
║  Ablation: Ab3 (Full Healer)                               ║
╚════════════════════════════════════════════════════════════╝

【Step 0】AI Code Generation
   📊 AI 生成完成: 0 項修復

【Step 1】Basic Cleanup (All Ablations)
   📊 代碼長度: 892 → 875 字符: 1 項修復

【Step 2】Regex Healer (Ab2/Ab3)
   📊 代碼長度: 875 → 868 字符: 3 項修復

【Step 3】AST Healer (Ab3 Only)
   📊 AST 結構正常: 0 項修復

【Step 5】Dynamic Sampling (Safety Net)
   📊 驗證: 3/3 通過 | Timeout: 5s: 0 項修復

╔════════════════════════════════════════════════════════════╗
║  ✅ Pipeline 執行成功                                       ║
║                                                            ║
║  📊 修復統計（分階段累計）:                                    ║
║     • Basic Cleanup:    1 項                               ║
║     • Regex Healer:     3 項                               ║
║     • AST Healer:       0 項                               ║
║     • 總計修復:         4 項                               ║
║                                                            ║
║  驗證狀態: PASSED                                          ║
║  總耗時: 19.23s                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

### **VERBOSE_LEVEL = 0 (極簡版)**

```
  ✅ PASSED | 總修復: Basic=1, Regex=3, AST=0
```

---

## 📝 使用說明

### 1. **查看詳細日誌**（預設）
```powershell
python scripts/sync_skills_files.py
```
自動使用 `VERBOSE_LEVEL=2`，顯示所有細節。

### 2. **切換到簡潔模式**
```powershell
$env:HEALER_VERBOSE = "1"
python scripts/sync_skills_files.py
```

### 3. **切換到極簡模式**（批量處理時使用）
```powershell
$env:HEALER_VERBOSE = "0"
python scripts/sync_skills_files.py
```

---

## 🎯 優勢

1. **可配置**: 3 種級別適應不同場景
2. **非侵入**: 不影響現有代碼邏輯
3. **詳細**: Level 2 提供完整的 21 層 Healer 資訊
4. **美觀**: 使用 Unicode 框線美化輸出
5. **調試友好**: 詳細模式下可快速定位問題

---

## 📂 相關檔案

- `core/code_generator.py` - 主要實現檔案
- `docs/競賽文件/代碼生成與修復技術詳解.md` - 技術文檔

---

**實現完成！** 🎉

現在運行 `python scripts/sync_skills_files.py` 即可看到詳細的 Pipeline 日誌輸出！
