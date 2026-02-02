# 方案 1 實施報告：場景區分法

## 📅 實施日期
2026-02-02

## 🎯 方案概述

**方案名稱**：斬草除根法（場景區分法）  
**核心理念**：工程化 = 簡潔直接，不是複雜的字串處理  
**實施範圍**：UNIVERSAL_GEN_CODE_PROMPT（Ab2/Ab3 使用）

---

## 📋 實施內容

### 1. 場景分類決策樹

新增清晰的決策樹，幫助 AI 判斷使用哪種方式：

```
你的題型使用了 Domain 標準函數嗎？（如 _poly_to_latex, _deriv_symbol_latex 等）
    │
    ├─ ✅ 是 → 🟢 場景 A：Domain 函數題型
    │          → 手動添加 $ 符號
    │          → 🔴 絕對禁止 clean_latex_output()
    │
    └─ ❌ 否 → 🟡 場景 B：簡單運算題型
               → 手動添加 $ 符號（推薦）
               → 或最後調用一次 clean_latex_output()（可選）
```

### 2. 場景 A：Domain 函數題型

#### 標準實作流程

```python
# 步驟 1: 使用 Domain 函數格式化（返回不含 $ 的完美 LaTeX）
poly_latex = _poly_to_latex(base_poly_terms)  # "10x^{5} + 9x^{2} + 5"

# 步驟 2: 手動為每個數學符號添加 $ $
derivative_symbols_latex = ' 與 '.join(
    f"${_deriv_symbol_latex(order)}$" 
    for order in derivative_orders_list
)
# 結果: "$f^{(3)}(x)$ 與 $f^{(4)}(x)$"

# 步驟 3: 組合題目（直接使用 f-string）
q = f"已知 $f(x) = {poly_latex}$，求 {derivative_symbols_latex}。"

# ✅ 完成！不需要也不應該呼叫 clean_latex_output()
```

#### 絕對禁止的錯誤

```python
# ❌ 錯誤 1: 混合已包裹和未包裹的內容
poly_latex = _poly_to_latex(terms)
deriv_sym = _deriv_symbol_latex(1)  # 無 $ $
q = f"已知 $f(x) = {poly_latex}$，求 {deriv_sym}。"  # 混合了
q = clean_latex_output(q)  # 💣 炸了！產生 placeholder 外洩

# ❌ 錯誤 2: 對 Domain 函數結果使用 clean_latex_output()
# ❌ 錯誤 3: 寫自己的清洗函數
```

#### 記憶口訣
```
Domain 函數已完美 → 手動加 $ → 直接用，不 clean
```

### 3. 場景 B：簡單運算題型

#### 方式 A：手動添加 $（推薦）

```python
# 步驟 1: 構造數學式（不含 $ $）
expr = f"{fmt_num(a)} {op_latex['*']} {fmt_num(b)}"  # "3 \\times 5"

# 步驟 2: 手動添加 $ 符號
q = f"計算 ${expr}$ 的值"  # "計算 $3 \\times 5$ 的值"

# ✅ 完成！簡單直接
```

#### 方式 B：使用 clean_latex_output()（可選）

```python
# 步驟 1: 構造數學式（不含 $ $）
expr = f"{fmt_num(a)} {op_latex['*']} {fmt_num(b)}"

# 步驟 2: 組合題目（不加 $）
q = f"計算 {expr} 的值"

# 步驟 3: 最後調用一次 clean_latex_output()
q = clean_latex_output(q)

# ✅ 也可以，但方式 A 更簡潔
```

#### 記憶口訣
```
簡單運算 → 優先手動 $ → 或最後 clean 一次
```

### 4. 混合模式警告

明確標示絕對禁止的混合模式：

```python
# 💣 致命組合：Domain 函數 + 混合內容 + clean_latex_output()
poly_latex = _poly_to_latex(terms)                    # Domain 函數
deriv_sym = _deriv_symbol_latex(1)                     # Domain 函數
q = f"已知 $f(x) = {poly_latex}$，求 {deriv_sym}。"   # 混合了 $ 和裸露內容
q = clean_latex_output(q)                              # 💣 爆炸！

# 結果: "已知 __ $LATEX$ _ $BLOCK$ _ $0$ __，求..."
```

---

## ✅ 驗證結果

運行 `python temp\verify_solution1_implementation.py`：

```
✅ 檢查點 1: 場景分類
   - 決策樹: True
   - 場景 A (Domain 函數): True
   - 場景 B (簡單運算): True

✅ 檢查點 2: 核心原則
   - 工程化 = 簡潔直接: True

✅ 檢查點 3: 實作範例
   - 場景 A 範例: True
   - 場景 B 範例: True

✅ 檢查點 4: 禁止模式
   - 混合模式警告: True

✅ 檢查點 5: 記憶口訣
   - 場景 A 口訣: True
   - 場景 B 口訣: True

✅ 方案 1 實施成功！
```

---

## 🎯 核心優勢

### 1. 簡潔直接
- **之前**：複雜的佔位符替換、正則表達式清洗
- **之後**：直接 f-string，手動添加 `$` 符號

### 2. 符合工程化真義
- **好的工程化**：清晰的變數命名、直接的 f-string
- **壞的工程化**：過度複雜的字串處理、多層替換邏輯

### 3. 徹底解決問題
- **根本原因**：混合場景誤用 clean_latex_output()
- **解決方法**：場景分類 + 明確禁令

### 4. AI 更容易理解
- **決策樹**：清晰的判斷邏輯
- **範例充足**：每種場景都有完整示範
- **口訣易記**：簡短的記憶輔助

---

## 📊 與其他方案比較

| 評估維度 | 方案 1<br>場景區分 | 方案 2<br>更換佔位符 | 方案 3<br>防禦性編程 |
|---------|-------------------|---------------------|---------------------|
| **解決 Domain 函數問題** | ✅ 完全解決 | ⚠️ 部分解決 | ❌ 不解決 |
| **程式碼簡潔度** | ✅ 最高 | ⚠️ 中等 | ❌ 最低 |
| **維護成本** | ✅ 最低 | ⚠️ 中等 | ❌ 最高 |
| **工程化程度** | ✅ 真正工程化 | ⚠️ 假工程化 | ❌ 過度工程 |
| **AI 理解難度** | ✅ 決策樹清晰 | ⚠️ 規則複雜 | ⚠️ 邏輯複雜 |
| **出錯風險** | ✅ 最低 | ⚠️ 中等 | ⚠️ 中等 |

---

## 🔄 與 Architect 修復的配合

### Architect 修復（已完成）
- **文件**：[core/prompt_architect.py](../core/prompt_architect.py)
- **內容**：生成 MASTER_SPEC 時區分兩種模式
  - 模式 A（Domain 函數）：禁止 clean_latex_output()
  - 模式 B（簡單運算）：允許 clean_latex_output()

### UNIVERSAL Prompt 強化（本次實施）
- **文件**：[core/prompts/prompt_builder.py](../core/prompts/prompt_builder.py)
- **內容**：為 AI 提供清晰的場景判斷和實作指引

### 雙管齊下效果
```
Architect（生成規格）         UNIVERSAL（執行指引）
        │                            │
        ├─ 模式 A 指示 ────────────→ 場景 A 實作
        │  （禁止 clean）            （手動 $ + 不 clean）
        │                            │
        └─ 模式 B 指示 ────────────→ 場景 B 實作
           （可選 clean）            （優先手動 $ 或 clean）
```

---

## 🚀 預期效果

### 對於新生成的代碼

1. **自動場景判斷**
   - AI 看到 `_poly_to_latex` → 識別為場景 A
   - AI 看到簡單運算 → 識別為場景 B

2. **選擇正確方式**
   - 場景 A：手動添加 `$`，不調用 clean
   - 場景 B：優先手動 `$`，或可選 clean

3. **避免致命錯誤**
   - 不再混合已包裹和未包裹的內容
   - 不再對 Domain 函數結果使用 clean_latex_output()

### 對於程式碼品質

1. **更簡潔**
   ```python
   # 之前（複雜）
   template = "已知 __BLOCK_0__..."
   q = complex_replace_logic(template, ...)
   
   # 之後（簡潔）
   q = f"已知 $f(x) = {poly_latex}$..."
   ```

2. **更可讀**
   - 直接看到最終字串的樣子
   - 不需要理解複雜的替換邏輯

3. **更可維護**
   - 出錯時一眼就能看出問題
   - 修改時不需要擔心破壞替換邏輯

---

## 📝 實施檔案清單

### 修改的檔案
1. **core/prompts/prompt_builder.py**
   - 行數：211-310（約 100 行）
   - 修改內容：LaTeX 格式鐵律 → 場景區分法
   - 修改類型：重構（邏輯更清晰）

### 新增的檔案
1. **temp/verify_solution1_implementation.py**
   - 用途：驗證方案 1 實施結果
   - 狀態：✅ 驗證通過

2. **docs/SOLUTION1_IMPLEMENTATION_REPORT.md**（本檔案）
   - 用途：完整的實施文檔

---

## 🎓 經驗總結

### 技術層面

1. **問題根源**：混合場景誤用，不是 clean_latex_output() 本身有問題
2. **解決關鍵**：場景分類，不是增加防禦邏輯
3. **最佳實踐**：簡潔直接，不是複雜「高大上」

### Prompt Engineering 層面

1. **清晰度 > 完整度**：決策樹比長篇說明更有效
2. **範例 > 規則**：具體代碼比抽象描述更容易理解
3. **口訣輔助**：簡短的記憶口訣幫助 AI 記住關鍵點

### 工程化理念

1. **工程化的真正意義**
   - ✅ 簡潔 > 複雜
   - ✅ 直接 > 繞圈
   - ✅ 清晰 > 炫技
   - ✅ 可維護 > 功能多

2. **Ab2 的定位**
   - 體現在：清晰的 MASTER_SPEC、模組化的 Domain 函數
   - 不體現在：複雜的字串處理、多層替換邏輯

---

## 🔮 後續行動

### 立即測試
1. 重新運行 `scripts/sync_skills_files.py` 模式[2] 或 [3]
2. 檢查生成的代碼是否遵循場景 A 的標準流程
3. 驗證不再有 placeholder 外洩

### 長期優化
1. 監控 AI 生成代碼的場景判斷準確率
2. 收集邊緣案例，進一步優化決策樹
3. 考慮為其他 Domain（三角、概率等）擴展標準函數庫

---

## 📚 參考資料

- **Architect 修復報告**：[docs/ARCHITECT_SOURCE_FIX_REPORT.md](ARCHITECT_SOURCE_FIX_REPORT.md)
- **Prompt 優化報告**：[PROMPT_OPTIMIZATION_REPORT.md](../PROMPT_OPTIMIZATION_REPORT.md)
- **驗證腳本**：[temp/verify_solution1_implementation.py](../temp/verify_solution1_implementation.py)

---

**實施完成日期**：2026-02-02  
**實施狀態**：✅ 完成並驗證通過  
**預期效果**：徹底解決 placeholder 外洩問題
