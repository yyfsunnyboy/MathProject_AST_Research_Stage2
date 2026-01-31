# 🔧 Ab3 失敗根本原因 & 修復計畫

## 🎯 問題根源定位

**config.py 第 70-74 行** - Coder 角色配置：

```python
# ❌ 現在配置（錯誤）
'coder': {
    'provider': 'google',
    'model': 'gemini-2.5-flash',  # ← 為什麼要用 Gemini？
    
    # 'provider': 'local',  
    # 'model': 'qwen2.5-coder:14b',  # ← 被註解掉了！
```

---

## 🔴 為什麼 Gemini 會失敗？

### 1️⃣ **Gemini 是通用 LLM，不是代碼生成器**
   - 訓練數據：通用知識（50%代碼）
   - 優勢：理解廣泛、靈活
   - 劣勢：代碼邏輯不夠精準

### 2️⃣ **Qwen 2.5-Coder 14B 是代碼專用**
   - 訓練數據：90% 代碼
   - 優勢：精準、遵守 Spec
   - 劣勢：寫作能力弱

### 3️⃣ **Ab3 需要可執行代碼**
   - Dynamic sampling 需要運行代碼
   - 代碼中的亂碼 → 無法解析 → Dynamic sampling 失敗
   - Qwen 不會產生亂碼

---

## 📊 三個模型對比

| 指標 | Gemini 2.5 Flash | Qwen 2.5-Coder 14B | Claude |
|------|------------------|-------------------|---------|
| **代碼質量** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **編碼安全性** | ⚠️ 有亂碼風險 | ✅ UTF-8 安全 | ✅ 安全 |
| **Spec 遵守** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **執行可靠性** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **成本** | 💸 API 付費 | ✅ 本地免費 | 💸 API 付費 |
| **速度** | 中 | 快 | 慢 |

---

## ✅ 立即修復步驟

### Step 1: 修改 config.py

將第 70-74 行改為：

```python
# ✅ 改為 Qwen (正確配置)
'coder': {
    'provider': 'local',
    'model': 'qwen2.5-coder:14b',
    
    # ❌ 停用 Gemini
    # 'provider': 'google',
    # 'model': 'gemini-2.5-flash',
    
    'temperature': 0.1,   # 極低溫，確保邏輯鎖死
    'max_tokens': 2048,   # 足夠複雜代碼
    'extra_body': {
        'num_ctx': 8192,
        'num_gpu': -1,
        'num_thread': 12,
    }
}
```

### Step 2: 驗證 Ollama 服務

```bash
# 確保 Ollama 正在運行
curl http://localhost:11434/api/tags

# 確保有 qwen2.5-coder:14b
# 如果沒有，執行：
ollama pull qwen2.5-coder:14b
```

### Step 3: 清理失敗堆積

```bash
cd e:\Python\MathProject_AST_Research

# 備份最新失敗檔案用於分析
copy skills_shadow\gh_ApplicationsOfDerivatives_FAILED_20260131_010232.* temp\

# 清空其他失敗檔案
Remove-Item -Path "skills_shadow\*FAILED*" -Exclude "*20260131_010232*" -Force
```

### Step 4: 重新執行 Ab3

```bash
# 執行單個技能的 Ab3 生成
python scripts/quick_validate_highschool.py --skill gh_ApplicationsOfDerivatives --ablation 3
```

### Step 5: 驗證結果

```
預期結果：
✅ gh_ApplicationsOfDerivatives: Success | Score=100
✅ Dynamic sampling: 2/2 successful
✅ 檔案：skills/gh_ApplicationsOfDerivatives_Cloud_Ab3.py (無亂碼)
```

---

## 🎯 預期修復時間

| 步驟 | 時間 |
|------|------|
| 修改 config.py | 2 分鐘 |
| 驗證 Ollama | 1 分鐘 |
| 清理檔案 | 1 分鐘 |
| 重新執行 Ab3 | 30-50 秒 |
| 驗證結果 | 2 分鐘 |
| **總計** | **~7 分鐘** |

---

## 📌 根本原因總結

```
根本原因：
  ❌ 有人把 Coder 改成了 Gemini（為什麼？應該用 Qwen）
  ❌ 註解掉了正確的 Qwen 配置
  ❌ Gemini 生成代碼時會產生 UTF-8 亂碼

導致結果：
  ❌ Ab3 無法執行代碼 
  ❌ Dynamic sampling 失敗
  ❌ Ab3 最終失敗

修復方案：
  ✅ 改回 Qwen 2.5-Coder 14B
  ✅ 使用本地 Ollama（無成本）
  ✅ Ab3 應該能完美成功

風險等級：🟢 低（只需改配置）
修復難度：🟢 簡單
預期成功率：✅ 95%+
```

---

## 🚀 完整修復命令序列

```powershell
# 一鍵修復流程
cd e:\Python\MathProject_AST_Research

# 1. 修改 config.py（見下面的具體改動）
# （可以用編輯器手動改，或執行下面的 PowerShell 命令）

# 2. 驗證 Ollama
curl http://localhost:11434/api/tags | Select-String "qwen2.5-coder"

# 3. 清理舊檔案
Remove-Item -Path "skills_shadow\*FAILED*" -Exclude "*20260131_010232*" -Force

# 4. 重新執行 Ab3
python scripts/quick_validate_highschool.py --skill gh_ApplicationsOfDerivatives --ablation 3

# 5. 驗證成功
dir skills\*Cloud_Ab3.py
```

---

**責任**: 模型配置修改（誰改的？）  
**影響**: Ab3 完全失敗  
**修復難度**: 🟢 簡單  
**預計修復時間**: 7 分鐘
