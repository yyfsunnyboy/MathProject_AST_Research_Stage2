# while True 結構要求源頭修復報告

**修復日期**: 2026-02-02  
**修復範圍**: Architect Prompt + UNIVERSAL Prompt  
**問題類型**: 結構性錯誤（缺少外層 while True 迴圈）

---

## 📋 問題診斷

### 症狀
生成的代碼（Ab1, Ab2, Ab3）全部失敗：
```python
SyntaxError: 'continue' not properly in loop
```

### 根本原因
AI 遺漏了 **外層 `while True:` 迴圈**，導致：
1. `continue` 語句無效（不在迴圈內）
2. 無法進行物件再生驗證
3. 結構不符合系統要求

### 為什麼 Healer 無法修復？
現有的 Healer（AST Healer + Regex Healer）只能：
- ✅ **移除** `while True`（轉換為 `for loop`，避免無限迴圈）
- ✅ 修復縮排問題（前提是結構存在）

但**不能**：
- ❌ **添加**缺少的外層 `while True`（結構缺失）

因此，必須從 **Prompt 源頭** 修復。

---

## 🔧 修復方案

### 方案定位
**源頭修復法**：在 Prompt 中明確要求並示範 `while True` 結構

### 修復內容

#### 1. Architect Prompt 強化 (`core/prompt_architect.py`)

**位置**: `implementation_checklist` 部分

**修改前**:
```yaml
implementation_checklist: |
  工程師實作時必須確認：
  - [ ] 是否生成了所有必要的變數
  - [ ] 是否實現了所有必要的運算步驟
  - [ ] 是否達到複雜度要求
  - [ ] 是否遵守了所有 constraints
```

**修改後**:
```yaml
implementation_checklist: |
  工程師實作時必須確認：
  - [ ] **必須有外層 while True: 迴圈**（def generate 內第一行）
  - [ ] 所有驗證邏輯都在 while True 內（用 continue 或 break 控制重試）
  - [ ] 格式化和 return 都在 while True 外（break 後才執行）
  - [ ] 是否生成了所有必要的變數
  - [ ] 是否實現了所有必要的運算步驟
  - [ ] 是否達到複雜度要求
  - [ ] 是否遵守了所有 constraints
```

**新增**：工程師實作結構要求（完整範例）

```python
def generate(level=1, **kwargs):
    while True:  # ⚠️ CRITICAL: 外層 while True 是必須的！用於整個物件再生
        # === 步驟 1: 變數生成 ===
        <根據規格生成變數>
        
        # === 步驟 2: 運算與驗證 ===
        <執行必要的運算>
        
        # === 步驟 3: 驗證與重試控制 ===
        if <不符合要求>:
            continue  # 重新生成整個物件
        
        if <符合所有要求>:
            break  # 跳出迴圈，進入格式化
    
    # === 步驟 4: 格式化（必須在 while True 外層！） ===
    q = <格式化題目>
    a = <格式化答案>
    
    # === 步驟 5: 回傳 ===
    return {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}
```

**結構檢查清單**：
- ✅ 必須有外層 `while True:`（def generate 內第一行）
- ✅ 所有驗證邏輯都在 while True 內
- ✅ 格式化和 return 都在 while True 外
- ✅ 有 continue 語句時，確保在 while True 內
- ✅ 不可在內層有 while True（只有外層一個）

---

#### 2. UNIVERSAL Prompt 強化 (`core/prompts/prompt_builder.py`)

**位置 1**: 生成管線標準

**修改前**:
```
【生成管線標準】
1. 變數生成（嚴格遵守 MASTER_SPEC）
2. 運算（Python 直接計算，嚴禁 eval）
...
```

**修改後**:
```
【生成管線標準】
1. **結構要求**：必須有外層 `while True:` 迴圈（用於物件再生）
2. 變數生成（嚴格遵守 MASTER_SPEC）
3. 運算（Python 直接計算，嚴禁 eval）
...
```

**位置 2**: 安全生成範例

**修改前**:
```python
def generate(level=1, **kwargs):
    while True:  # 外層 while True 用於整個物件再生
    ...
    # 步驟 4: 格式化輸出
    q = f'...'
    a = '...'
    return {...}
```

**修改後**:
```python
def generate(level=1, **kwargs):
    while True:  # ⚠️ CRITICAL: 外層 while True 是必須的！用於整個物件再生
    ...
    # 步驟 4: 格式化輸出（必須在 while True 外層！）
    q = f'...'
    a = '...'
    return {...}
```

**新增**：結構檢查清單

```
【結構檢查清單 - 提交代碼前必須確認】
✅ **必須有外層 `while True:`**（def generate 內第一行）
✅ **所有驗證邏輯都在 while True 內**
✅ **格式化和 return 都在 while True 外**
✅ **有 continue 語句時，確保在 while True 內**
✅ **不可在內層有 while True**（只有外層一個）
```

---

## ✅ 驗證結果

執行驗證腳本 `temp/verify_while_true_requirement.py`：

```
🔍 驗證 while True 結構要求是否已加入 Prompt

================================================================================
檢查 1: Architect Prompt 是否要求 while True 結構
================================================================================
✅ 提到 'while True'
✅ 提到 '外層 while True'
✅ 有結構要求章節
✅ 有 implementation_checklist
✅ checklist 包含 while True
✅ 有結構檢查清單

================================================================================
檢查 2: UNIVERSAL Prompt 是否示範 while True 結構
================================================================================
✅ 提到 'while True'
✅ 有安全生成範例
✅ 範例包含 while True
✅ 有結構檢查清單
✅ 明確標註 CRITICAL
✅ 有 continue/break 說明

================================================================================
檢查 3: 結構要求是否完整且清晰
================================================================================
✅ 外層 while True 是必須的
✅ 驗證邏輯在 while True 內
✅ 格式化在 while True 外
✅ 有 continue/break 說明
✅ 禁止內層 while True

================================================================================
📊 總結
================================================================================
Architect Prompt: ✅ 通過
UNIVERSAL Prompt: ✅ 通過
結構要求完整性: ✅ 通過

================================================================================
🎉 所有檢查通過！while True 結構要求已正確加入源頭 Prompt
================================================================================
```

---

## 📊 修復效果預測

### 預期改善

1. **結構完整性**：
   - ✅ 未來生成的代碼都會有外層 `while True`
   - ✅ `continue` 語句將正常運作
   - ✅ 物件再生驗證機制完整

2. **減少手動修復**：
   - ⬇️ 減少 SyntaxError: 'continue' not properly in loop
   - ⬇️ 減少結構性錯誤
   - ⬇️ 減少手動介入需求

3. **提升代碼品質**：
   - ⬆️ 結構一致性
   - ⬆️ 符合系統架構要求
   - ⬆️ 可維護性

### 不影響的部分

- ✅ 方案 1（場景區分法）仍然有效
- ✅ Domain 函數使用正確
- ✅ 無 placeholder 外洩

---

## 🎯 下一步建議

### 短期（立即執行）
1. **重新生成測試**：用新的 Prompt 重新生成 Ab1/Ab2/Ab3
2. **驗證結構**：確認新生成的代碼有外層 `while True`
3. **測試運行**：確認所有版本都能正常執行

### 中期（未來優化）
1. **增強 Healer**：
   - 考慮添加結構檢測器（偵測缺少的 while True）
   - 自動添加基本結構（如果檢測到 continue 但無迴圈）

2. **Prompt 版本管理**：
   - V1: 場景區分（已完成）
   - V2: 結構要求（已完成）
   - V3: 完整模板（未來考慮）

### 長期（系統改進）
1. **建立結構驗證測試套件**
2. **自動化結構檢查**（CI/CD 整合）
3. **Prompt 效果追蹤與優化**

---

## 📚 相關文件

- **修復檔案**：
  - `core/prompt_architect.py` (Lines 87-207)
  - `core/prompts/prompt_builder.py` (Lines 170-210)

- **驗證腳本**：
  - `temp/verify_while_true_requirement.py`

- **相關報告**：
  - `docs/ARCHITECT_SOURCE_FIX_REPORT.md` (方案 1 場景區分法)
  - `docs/SOLUTION1_IMPLEMENTATION_REPORT.md` (方案 1 實施報告)

---

## 🔍 關鍵學習

1. **Prompt 工程是多層的**：
   - 場景區分（LaTeX 格式）✅
   - 結構要求（while True）✅
   - 兩者缺一不可

2. **Healer 有局限性**：
   - 只能修復，不能創造
   - 結構缺失必須從源頭解決

3. **源頭修復才是王道**：
   - 手動修復是臨時方案
   - Prompt 修復是永久方案
   - 驗證機制確保修復有效

---

**修復完成時間**: 2026-02-02 23:00  
**預期生效**: 下次 MASTER_SPEC 生成時  
**修復狀態**: ✅ 完成並驗證
