# 🔴 Ab3 大翻車分析報告

**日期**: 2026-01-31 01:02:32  
**事件**: Dynamic sampling failed - 無法生成有效題目  
**模型**: Gemini 2.5 Flash (❌ 錯誤選擇)  
**預期模型**: Qwen 2.5-Coder 14B  
**優先級**: 🔴 **CRITICAL**

---

## 🎯 核心問題診斷

### ❌ 問題 1: 模型選擇錯誤

```
實際：gemini-2.5-flash (通用模型)
應該：Qwen 2.5-Coder 14B (代碼專用模型)

影響：Gemini 會產生幻覺函數和編碼問題
```

### ❌ 問題 2: Gemini 生成的代碼包含亂碼

**Gemini raw 輸出中的亂碼證據**:

```python
# ❌ 原始代碼
polynomial_degree = random.randint(2, 5)
num_terms = random.randint(2, 4)
variable_name = 'x'

# 2. ?冽??? exponents ?"嚗Ⅱ靽?瑕漲??num_terms嚗澆 0 ??polynomial_degree
#    銝???polynomial_degree??
#    蝣箔??喳????活?詨之??1嚗誑?踹?撠?蝪∪??
```

**問題分析**:
- `?冽???` - 亂碼
- `?"嚗Ⅱ靽?` - UTF-8 編碼損壞
- `銝???polynomial_degree??` - 中文名詞與亂碼混合
- 這使得代碼無法執行

### ❌ 問題 3: Dynamic Sampling 失敗鏈

```
生成亂碼代碼
    ↓
AST Parser 無法解析
    ↓
執行失敗
    ↓
Dynamic sampling 無法驗證
    ↓
[WARN] Failed to generate a valid problem
    ↓
Ab3 最終失敗 ❌
```

---

## 📊 三個版本對比

| 版本 | 模型 | 結果 | 原因 |
|------|------|------|------|
| **Ab1** | Gemini | ✅ 成功 | 無工具，無SPEC，簡單任務 |
| **Ab2** | Gemini | ✅ 成功 | 有SPEC指導，但無需執行代碼 |
| **Ab3** | Gemini | ❌ **失敗** | 需執行生成的代碼，遇到亂碼 |

### 🔍 為什麼 Ab1/Ab2 成功，Ab3 失敗？

```
Ab1/Ab2:
  ✅ 靜態驗證（只檢查結構和邏輯）
  ✅ Gemini 的代碼足夠好

Ab3:
  ❌ 動態驗證（需要實際執行代碼）
  ❌ Gemini 的亂碼導致執行失敗
  ❌ Dynamic sampling 無法完成
```

---

## 🔧 立即修復方案

### 方案 1: 更換模型為 Qwen (推薦)

```bash
# 更新 config.py 中的模型配置
[生成配置]
model = "ollama:qwen2.5-coder:14b"  # ← 改為本地 Qwen
```

**優點**:
- Qwen 是代碼專用模型，不會產生亂碼
- 本地運行，無成本
- 已驗證的成功模型

**預期結果**:
- Ab3 會成功
- Dynamic sampling 會通過

### 方案 2: 修改 Gemini 的 Prompt (次要)

```python
# 在 prompt 中明確要求
"請使用 ASCII 字符和英文。不要混合 UTF-8 中文和亂碼。"
"All code comments should be in English only."
```

**缺點**:
- 不根本解決問題
- Gemini 仍會產生幻覺函數

---

## 📈 失敗堆積量

```
skills_shadow/ 中存在 31 個失敗檔案：

├─ 2026-01-29: 20 個失敗 (舊測試)
├─ 2026-01-30: 10 個失敗 (評估階段)  
├─ 2026-01-31: 1 個失敗 (最新)
   └─ gh_ApplicationsOfDerivatives_FAILED_20260131_010232.py
      ├─ 原因: UTF-8 編碼亂碼
      ├─ 檔案大小: 22.75 KB
      └─ 時間: 2026-01-31 01:02:32
```

### 成功的失敗堆積清理

```bash
# 清空失敗檔案（保留最新的一個用於分析）
Remove-Item -Path "skills_shadow/*FAILED*" -Exclude "*20260131*" -Force

# 或完全清空
Remove-Item -Path "skills_shadow/*.FAILED*" -Force
```

---

## 🎯 建議行動計畫

### 立即 (現在)
- [ ] **使用 Qwen 14B 替代 Gemini**
- [ ] 修改 config.py 的模型設定
- [ ] 清理 skills_shadow/ 的失敗檔案堆積

### 短期 (1 小時)
- [ ] 重新執行 Ab3 生成（預期成功）
- [ ] 驗證 Dynamic sampling 能否通過

### 後續 (明天)
- [ ] 驗證新升級的 remove_system_overrides 是否正常運作
- [ ] 測試其他技能

---

## 📌 根本原因總結

```
問題來源：
  1. 使用了 Gemini 而非 Qwen（模型選擇錯誤）
  2. Gemini 生成包含 UTF-8 亂碼的代碼
  3. AST Parser 無法解析亂碼
  4. Dynamic sampling 失敗

解決方案：
  → 使用 Qwen 2.5-Coder 14B（本地，已驗證）
  → 避免 Gemini 的亂碼問題
  → Ab3 應該能成功
```

---

**責任**: 模型配置錯誤  
**影響**: Ab3 無法執行  
**修復難度**: 🟢 簡單（只需改配置）  
**預期修復時間**: 5-10 分鐘

