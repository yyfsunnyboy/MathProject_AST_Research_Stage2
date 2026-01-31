# AST Healer 修復摘要

## 🔧 已應用的修復

### 修復 1：禁用 AST Healer 的格式化函數重定向

**文件**: [core/healers/ast_healer.py](core/healers/ast_healer.py#L119-L139)

**改動**：
```python
# 舊代碼（問題）
if node.func.id not in protected and re.search(r'(format|latex|display)', node.func.id, re.IGNORECASE):
    self.fixes += 1
    node.func.id = 'fmt_num'  # ❌ 把多項式函數改成 fmt_num
    ...

# 新代碼（修復）
# 不再進行自動重定向 - 讓 LLM 生成的函數名保持原樣
if isinstance(node.func, ast.Name):
    protected = { ... }  # 包含所有多項式相關函數
    pass  # 不再進行改名
```

**原因**：
- AST Healer 不應該進行函數名稱轉換
- LLM 生成的 `_format_poly_string()` 應保留原名
- 強行改成 `fmt_num()` 會導致後續修復混亂

### 修復 2：加強 fmt_num 參數類型檢查

**文件**: [core/healers/ast_healer.py](core/healers/ast_healer.py#L108-L125)

**改動**：
```python
# 新增：參數類型檢查
if isinstance(node.func, ast.Name) and node.func.id == 'fmt_num':
    # [新增] 檢查參數類型
    if node.args and isinstance(node.args[0], (ast.List, ast.Tuple)):
        # fmt_num(list) 是錯誤的 - 保留原代碼
        return node
    
    # 後續的參數清理...
```

**原因**：
- `fmt_num()` 只接受標量（int/float/Fraction）
- 不應該接受 list/tuple（集合）
- 在修改之前應檢查參數類型

---

## 📊 修復影響

| 變數 | 舊流程 | 新流程 |
|------|--------|--------|
| LLM 生成 | `_format_poly_string(coeffs)` | `_format_poly_string(coeffs)` |
| AST Healer | ❌ 改成 `fmt_num(coeffs)` | ✅ 保留原名 |
| F.9 修復 | ❌ 改成 `polynomial_to_string(coeffs)` | ✅ 找到真實函數名 |
| 動態採樣 | ❌ NameError | ✅ 成功執行 |

---

## 🎯 預期效果

```
修復前：
  LLM Code → AST Healer (改名錯誤) → F.9 修復 (失敗) → NameError ❌

修復後：
  LLM Code → AST Healer (保留) → F.9 修復 (正確) → 成功 ✅
```

---

## ✅ 驗證清單

- [x] AST Healer 格式化函數重定向已禁用
- [x] fmt_num 參數類型檢查已加強
- [x] 保護名單包含所有已知的多項式函數
- [x] 代碼註釋解釋了為什麼禁用

---

*修復完成時間：2026-01-31 03:52*
*影響的代碼：core/healers/ast_healer.py*
*預期改善：Ab3 生成應恢復正常*
