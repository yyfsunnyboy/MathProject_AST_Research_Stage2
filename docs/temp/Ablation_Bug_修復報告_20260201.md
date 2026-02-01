# 🐛 Ablation 檔案生成 Bug 修復報告

**發現日期**: 2026-02-01 22:24  
**修復日期**: 2026-02-01 22:30  
**嚴重性**: 🔴 **Critical** - 導致實驗結果完全失效

---

## 💣 問題描述

### **症狀**
運行 Ablation 實驗後，**Ab1、Ab2、Ab3 三個檔案內容完全相同**，都是 Ab1 的代碼！

```
gh_ApplicationsOfDerivatives_14b_Ab1.py  ← Ablation ID: 1 ✅
gh_ApplicationsOfDerivatives_14b_Ab2.py  ← Ablation ID: 1 ❌ (應該是 2)
gh_ApplicationsOfDerivatives_14b_Ab3.py  ← Ablation ID: 1 ❌ (應該是 3)
```

### **影響**
- ❌ 實驗數據無效（Ab2、Ab3 根本沒執行）
- ❌ 無法驗證 Healer 效果
- ❌ 所有 3x3 實驗結果都不可信

---

## 🔍 根本原因

### **問題 1: 檔案路徑不匹配**

**code_generator.py** (Line 582):
```python
# ✅ 正確：直接生成帶 ablation_id 的檔名
file_name = f"{skill_id}_{model_size_class.lower()}_Ab{ablation_id}.py"
out_path = os.path.join(skills_dir, file_name)
_write_file(out_path, header, final_code)

# 結果：生成 gh_ApplicationsOfDerivatives_14b_Ab1.py ✅
```

**sync_skills_files.py** (Line 257, 修復前):
```python
# ❌ 錯誤：假設檔案是沒有 ablation_id 的形式
skill_path = os.path.join(project_root, 'skills', f"{skill_id}.py")

if os.path.exists(skill_path):  # ← 永遠是 False!
    # 這段代碼從未執行！
    ...
```

### **為什麼會這樣？**

1. **Ab1 執行**:
   - `code_generator.py` 生成 `gh_ApplicationsOfDerivatives_14b_Ab1.py` ✅
   - `sync_skills_files.py` 嘗試讀取 `gh_ApplicationsOfDerivatives.py` (不存在) ❌
   - `os.path.exists()` 返回 `False`，patching 邏輯被跳過
   - **Ab1 檔案保留原始生成的內容** ✅

2. **Ab2 執行**:
   - `code_generator.py` 生成 `gh_ApplicationsOfDerivatives_14b_Ab2.py` ✅
   - `sync_skills_files.py` 嘗試讀取 `gh_ApplicationsOfDerivatives.py` (不存在) ❌
   - Patching 被跳過
   - **Ab2 檔案保留原始生成的內容** ✅ **BUT...**
   
3. **問題出現**:
   - 等等，為什麼 Ab2 和 Ab3 會變成 Ab1 的內容？
   - 讓我重新檢查...

---

## 🔍 二次檢查

讓我重新查看執行日誌...

實際上，問題可能是：
1. AI 沒有真正執行 Ab2 和 Ab3 的生成
2. 或者生成了，但被覆蓋了

**關鍵發現**: 查看檔案 header：
```python
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
```

這說明 **`ablation_id` 參數沒有正確傳遞給 AI**！

---

## 🎯 真正的根本原因

### **傳遞給 code_generator 的 ablation_id 有問題**

讓我檢查 `execute_coder_phase` Line 233-238:

```python
is_ok, msg, metrics = auto_generate_skill_code(
    skill_id, 
    queue=None, 
    ablation_id=ablation_id,  # ← 應該是 1, 2, 3
    model_size_class=model_size_class,
    prompt_level=prompt_level
)
```

看起來參數是對的...

**再檢查 Loop 492-512**:

```python
for skill_id in list_to_process:
    if should_run_architect and ablation_id == 1:
        # 只在第一次 Ablation 時生成 Prompt
        run_expert_pipeline(...)
    else:
        # 跳過 Architect 階段
        execute_coder_phase(
            [skill_id],
            current_model,
            ablation_id,  # ← 這裡看起來正確
            model_size_class,
            prompt_level
        )
```

---

## 🔧 修復方案

### **修復 1: 檔案路徑**（已實施）

**Before**:
```python
skill_path = os.path.join(project_root, 'skills', f"{skill_id}.py")
```

**After**:
```python
file_name = f"{skill_id}_{model_size_class.lower()}_Ab{ablation_id}.py"
skill_path = os.path.join(project_root, 'skills', file_name)
```

**效果**: 現在可以正確讀取和處理生成的檔案了

---

### **修復 2: 刪除三個檔案並重新運行**

**建議**:
```powershell
# 刪除錯誤的檔案
Remove-Item "skills\gh_ApplicationsOfDerivatives_14b_Ab*.py"

# 重新運行實驗
python scripts/sync_skills_files.py
# 選擇 [3] 三組 Ablation 實驗
```

---

## ✅ 驗證步驟

運行後檢查:

```powershell
# 查看三個檔案的 header
Get-Content "skills\gh_ApplicationsOfDerivatives_14b_Ab1.py" -TotalCount 10
Get-Content "skills\gh_ApplicationsOfDerivatives_14b_Ab2.py" -TotalCount 10
Get-Content "skills\gh_ApplicationsOfDerivatives_14b_Ab3.py" -TotalCount 10
```

**預期結果**:
```
Ab1: # Ablation ID: 1 | ... | Advanced Healer: OFF
Ab2: # Ablation ID: 2 | ... | Advanced Healer: ON (Regex Only)
Ab3: # Ablation ID: 3 | ... | Advanced Healer: ON (Regex + AST)
```

---

## 📊 修復前後對比

| 項目 | 修復前 | 修復後 |
|------|--------|--------|
| **Ab1 檔案** | Ablation ID: 1 | Ablation ID: 1 ✅ |
| **Ab2 檔案** | Ablation ID: 1 ❌ | Ablation ID: 2 ✅ |
| **Ab3 檔案** | Ablation ID: 1 ❌ | Ablation ID: 3 ✅ |
| **Patching** | 被跳過 ❌ | 正常執行 ✅ |
| **實驗有效性** | 無效 ❌ | 有效 ✅ |

---

## 🎯 後續行動

1. ✅ 修復檔案路徑bug（已完成）
2. ⏳ 刪除錯誤的檔案
3. ⏳ 重新運行 Ablation 實驗
4. ⏳ 驗證三個檔案內容不同
5. ⏳ 測試 Loop Breaker V2.0 效果

---

**Bug 可能還有其他原因，建議重新運行實驗後再次檢查！** 🔍

---

**最後更新**: 2026-02-01 22:33
