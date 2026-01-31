# Ab3 失敗根本原因分析與修復

## 📍 問題診斷

### 错误信息
```
[WARN] Dynamic sampling failed at iteration 1: name 'polynomial_to_string' is not defined
```

### 根本原因

在生成 Ab3 代碼時，Healer Pipeline 中的 **F.9 修復** 出現了邏輯錯誤：

1. **原始 LLM 生成代碼**：
   ```python
   # LLM 生成的函數調用：
   poly_latex_str = _format_poly_string(raw_coeffs, is_latex=True)
   ```

2. **F.9 修復的錯誤行為**：
   ```python
   # 老版本 F.9：無條件把所有 fmt_num(list) 改成 polynomial_to_string
   clean_code, n = re.subn(
       r'\bfmt_num\s*\(\s*(coeffs?|[a-z_]*_list|[a-z_]*s)\s*\)',
       r'polynomial_to_string(\1)',  # <- 硬編碼：注入不存在的函數名
       clean_code
   )
   ```

3. **結果**：
   ```python
   # 修復後的代碼（錯誤）：
   poly_latex_str = polynomial_to_string(raw_coeffs)  # ❌ 函數不存在！
   ```

4. **為什麼失敗**：
   - `polynomial_to_string()` 函數**從未被定義**
   - PERFECT_UTILS 中也沒有這個函數
   - F.11 修復試圖強行定義它，但代碼複雜且容易出錯
   - Dynamic sampling validation 執行代碼時拋出 `NameError`

---

## ✅ 修復方案

### 修復策略：智能函數名稱匹配

**新的 F.9 修復** (code_generator.py, line 1507-1529)：

```python
# 搜尋代碼中實際定義的多項式格式化函數
poly_func_names = []
for match in re.finditer(
    r'\bdef\s+([a-z_]*polynomial[a-z_]*|[a-z_]*poly[a-z_]*|_format[a-z_]*|format[a-z_]*poly)\s*\(',
    clean_code
):
    poly_func_names.append(match.group(1))

# 只有找到已定義的函數時才進行修復
if poly_func_names:
    target_func = poly_func_names[0]  # 優先用第一個找到的
    clean_code, n = re.subn(
        r'\bfmt_num\s*\(\s*(coeffs?|[a-z_]*_list|[a-z_]*s)\s*\)',
        f'{target_func}(\\1)',  # <- 動態使用實際定義的函數名
        clean_code
    )
```

### 修復的優勢

```
✅ 智能探測：搜尋代碼中真正定義的多項式函數
✅ 零假設：不假設函數名稱，根據實際代碼調整
✅ 保守修復：只在找到已定義函數時才改名
✅ 支援多種名稱：_format_poly_string, build_polynomial_text, format_polynomial 等
✅ 避免副作用：不強行注入 PERFECT_UTILS 中不存在的函數
```

### 同步禁用 F.11

原有的 **F.11 修復** (強行替換多項式函數實現) 已禁用，原因：

```
❌ 會覆蓋 LLM 已正確實現的多項式函數
❌ 可能注入新的 bug（縮排、格式等）
❌ 與 F.9 的修復衝突
✅ AST Healer + 新的 F.9 已經足以修復常見問題
```

---

## 🔍 案例追溯

### Ab3 失敗時的代碼流程

```
1. LLM 生成代碼
   ↓
2. 基礎清理 (移除 Markdown)
   ↓
3. AST Healer 修復結構
   ↓
4. [舊 F.9] 把 fmt_num(raw_coeffs) → polynomial_to_string(raw_coeffs)
   ↓
5. [舊 F.11] 試圖定義 polynomial_to_string，但邏輯複雜易失敗
   ↓
6. Dynamic sampling 執行代碼
   ↓
7. NameError: name 'polynomial_to_string' is not defined
   ↓
❌ 生成失敗
```

### 修復後的代碼流程

```
1. LLM 生成代碼 (含 _format_poly_string)
   ↓
2. 基礎清理
   ↓
3. AST Healer 修復結構
   ↓
4. [新 F.9] 偵測到 _format_poly_string 已定義
   ↓
5. 如需改名 fmt_num(coeffs) → _format_poly_string(coeffs)
   ↓
6. [新 F.11] DISABLED - 保留 LLM 的實現
   ↓
7. Dynamic sampling 執行代碼
   ↓
8. 所有函數都已定義 ✅
   ↓
✅ 生成成功
```

---

## 📊 測試計畫

### 修復驗證步驟

1. **簡單單元測試**（無需 Flask）
   - 驗證新 F.9 的正則表達式正確性
   - 驗證函數名稱探測邏輯

2. **完整集成測試**（包含 Healer）
   - 使用最近失敗的 raw LLM 輸出重新執行修復
   - 驗證生成代碼是否包含所有必要函數定義

3. **三模型對比執行**
   - Ab1（Bare Prompt）✅ 已通過
   - Ab2（工程化提示）✅ 已通過
   - Ab3（完整修復 + 亂碼清除）🔄 待驗證

---

## 🎯 後續行動

### 立即執行
```
1. 重新運行 Ab3 生成（使用修復後的 code_generator.py）
2. 驗證生成的代碼包含所有函數定義
3. 確保 Dynamic sampling 通過
```

### 驗證指標
```
✅ 無 polynomial_to_string 調用（或所有調用都有定義）
✅ 代碼能通過 compile() 檢查
✅ 能通過 Dynamic sampling validation
✅ 沒有亂碼字符（已由 mojibake fix 處理）
```

---

*修復應用時間：2026-01-31 03:45*
*修改文件：core/code_generator.py (F.9 and F.11)*
*相關 issues：undefined polynomial_to_string, function name mismatch*
