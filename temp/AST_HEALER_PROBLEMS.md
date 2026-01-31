# AST Healer 問題檢查報告

## 🔴 發現的問題

### 問題 1：visit_Call 中的 fmt_num 重定向邏輯

**位置**: [ast_healer.py](core/healers/ast_healer.py#L119-L131)

```python
# 3. 格式化函式重定向
if isinstance(node.func, ast.Name):
    protected = {
        'fmt_num', 'to_latex', 'clean_latex_output', 'check', 'safe_eval',
        ...
    }
    
    if node.func.id not in protected and re.search(r'(format|latex|display)', node.func.id, re.IGNORECASE):
        self.fixes += 1
        node.func.id = 'fmt_num'  # <- 問題在這裡
        node.keywords = [k for k in node.keywords if k.arg in ['signed', 'op']]
        return node
```

**問題描述**：
- 這段代碼會把 `_format_poly_string()` 改名為 `fmt_num`
- 然後後續的 F.9 修復試圖改回去，但卻改成了 `polynomial_to_string`
- 導致函數名稱不匹配

### 問題 2：visit_Call 的第 2 部分（fmt_num 參數修復）

**位置**: [ast_healer.py](core/healers/ast_healer.py#L108-L118)

```python
# 2. 處理 fmt_num
if isinstance(node.func, ast.Name) and node.func.id == 'fmt_num':
    # 移除幻想參數
    if node.keywords:
        original_len = len(node.keywords)
        node.keywords = [k for k in node.keywords if k.arg in ['signed', 'op']]
        # ... 刪減了參數 ...
```

**問題描述**：
- 當 LLM 調用 `_format_poly_string(raw_coeffs)` 時...
- AST Healer 會把它改名為 `fmt_num(raw_coeffs)`  <- 🔴 錯誤！
- `fmt_num()` 不能接受 list/coeffs 作為參數
- 這是根本原因！

### 問題 3：visit_Assign 的元組拆分邏輯

**位置**: [ast_healer.py](core/healers/ast_healer.py#L210-L233)

```python
def visit_Assign(self, node):
    if len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
        target_tuple = node.targets[0]
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'fmt_num':
            # 這段邏輯會拆分：
            # val, latex = fmt_num(x)
            # 成為：
            # val = x
            # latex = fmt_num(val)
```

**問題描述**：
- 這個邏輯假設 `fmt_num()` 返回元組
- 但 LLM 調用的 `_format_poly_string()` 本身返回字串，不返回元組
- 這個修復會導致邏輯破裂

---

## 💡 根本原因鏈

```
LLM 生成：poly_str = _format_poly_string(coeffs)
    ↓
AST Healer visit_Call (第 3 部分)：
    檢查到 _format_poly_string 包含 'format'、'latex' 關鍵字
    改名為 fmt_num → poly_str = fmt_num(coeffs)
    ❌ 這是錯誤！fmt_num 不能接受 list
    ↓
F.9 修復試圖改正：
    偵測到 fmt_num(coeffs)
    改名為 polynomial_to_string → poly_str = polynomial_to_string(coeffs)
    ❌ 這個函數根本不存在
    ↓
❌ 生成失敗
```

---

## ✅ 修復方案

### 修復 1：禁用 AST Healer 的格式化函數重定向

**位置**: [ast_healer.py](core/healers/ast_healer.py#L119-L131)

應改為：

```python
# 3. 格式化函式重定向 [DISABLED V47.11]
# [理由] LLM 生成的多項式格式化函數（_format_poly_string 等）應保留原名
# 它們與 fmt_num 不兼容，強行改名會導致後續修復混亂
# AST 層級不應該做這種函數名稱轉換 - 應該保留原代碼
if False:  # 禁用此修復
    if isinstance(node.func, ast.Name):
        protected = { ... }
        if node.func.id not in protected and re.search(...):
            ...
```

或更好的方式：

```python
# 不重定向已經定義的多項式格式化函數
if isinstance(node.func, ast.Name):
    protected = {
        'fmt_num', 'to_latex', 'clean_latex_output', 'check', 'safe_eval',
        'gcd', 'lcm', 'is_prime', 'get_factors',
        # [NEW] 保護已知的多項式函數
        '_format_poly_string', 'build_polynomial_text', 'format_polynomial',
        'polynomial_to_latex', '_format_derivative_symbol', '_differentiate_coeffs'
    }
    
    if node.func.id not in protected and re.search(r'(format|latex|display)', node.func.id, re.IGNORECASE):
        # 只有在確實是「幻覺函數」時才改名
        # 幻覺函數的特徵：被調用但從未定義
        # 這需要在此前掃描整個代碼樹來確認
        ...
```

### 修復 2：加強 visit_Call 的 fmt_num 檢查

在改名為 `fmt_num` 之前，檢查參數類型：

```python
# 2. 處理 fmt_num [增強版]
if isinstance(node.func, ast.Name) and node.func.id == 'fmt_num':
    # 只有在參數看起來合理時才修復
    # fmt_num 期望：int/float/Fraction，不期望：list/array/coeffs
    if node.args and isinstance(node.args[0], (ast.List, ast.Tuple)):
        # 這是在調用 fmt_num(list)，根本不對 - 不修復
        return node
    
    # 只在看起來是正常調用時進行其他修復
    if node.keywords:
        ...
```

---

## 📋 建議的修復步驟

### 立即修復

1. **禁用 AST Healer 的格式化函數重定向**
   - 在 visit_Call 第 3 部分添加保護名單
   - 或乾脆註解掉這部分邏輯

2. **加強 visit_Call 的參數類型檢查**
   - 在修改 fmt_num 之前檢查參數類型
   - 避免把 `func(list)` 改成 `fmt_num(list)`

### 驗證

```python
# 測試用例
test_cases = [
    "_format_poly_string([1,2,3])",      # 應保留原函數名
    "build_polynomial_text(coeffs)",     # 應保留原函數名
    "fmt_num(5)",                        # 可以修復
    "polynomial_to_latex(x)",            # 應保留（如果已定義）
]
```

---

## 🎯 优先级

| 優先級 | 問題 | 影響 | 修復難度 |
|--------|------|------|---------|
| 🔴 P0 | AST 重定向導致函數名不匹配 | Ab3 直接失敗 | 低 |
| 🟠 P1 | fmt_num(list) 邏輯檢查不足 | 潛在隱患 | 低 |
| 🟡 P2 | visit_Assign 的元組拆分過度 | 邊界情況 | 中 |

---

*分析時間：2026-01-31 03:50*
*相關文件：core/healers/ast_healer.py*
*根本原因：AST Healer 的過度修復導致函數名稱混亂*
