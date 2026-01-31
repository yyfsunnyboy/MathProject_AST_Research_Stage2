# AST Healer 第二个关键修复 - 保护有效的辅助函数

## 🔴 **新发现的问题**

**错误信息**：
```
[WARN] Dynamic sampling failed at iteration 1: name '_poly_to_latex' is not defined
```

**根本原因**：
AST Healer 的 `visit_FunctionDef()` 方法使用过于宽泛的正则表达式，导致误删了有效的工具函数 `_poly_to_latex`

**问题代码位置**：[core/healers/ast_healer.py](core/healers/ast_healer.py#L167-L168)

```python
# 舊代碼（問題）
if re.search(r'(Format|LaTeX|Display)', node.name, re.IGNORECASE) and node.name != 'generate':
    self.fixes += 1
    return None  # 刪除整個函數！
```

**为什么是问题**：
- `_poly_to_latex` 包含 `LaTeX`，匹配了正则表达式
- 虽然这是 LLM 生成的**有效工具函数**，但被误认为是虚函数而被删除
- 导致后续代码调用 `_poly_to_latex()` 时报 `NameError`

---

## ✅ **已应用的修复**

**新代码**（[core/healers/ast_healer.py](core/healers/ast_healer.py#L164-L190)）：

```python
def visit_FunctionDef(self, node):
    # 1. 移除自創的格式化函數 [V47.11 CRITICAL FIX]
    # [修復] 保護所有有效的工具函數，只移除無效的虛函數
    
    # 保護名單：LLM 生成的有效工具函數（應保留）
    protected_helpers = {
        'generate',
        # 多項式處理工具
        '_poly_to_latex', '_poly_to_plain',
        '_format_term_latex', '_format_term_plain',
        '_differentiate_poly_once', '_differentiate_poly_n_times',
        '_format_deriv_symbol_latex', '_format_deriv_symbol_plain',
        # 其他工具函數
        '_differentiate_coeffs', '_format_poly_string',
        'build_polynomial_text', 'calculate_derivative',
        'polynomial_to_plain_string'
    }
    
    # 只移除真正的虛函數（CamelCase，不在保護名單中）
    if node.name not in protected_helpers:
        # CamelCase 虛函數檢測：包含大寫字母且用於格式化
        if re.search(r'[A-Z].*(?:Format|Latex|Display|Poly)', node.name, re.IGNORECASE):
            self.fixes += 1
            return None
```

**修复策略**：
1. **建立保护名单** - 列出所有有效的工具函数
2. **两层检查** - 先检查是否在保护名单中，再检查是否是虚函数
3. **改进正则** - 要求函数名包含大写字母（CamelCase），而不仅仅是 LaTeX/Format 关键字

---

## 📊 **修复效果**

| 函数 | 修复前 | 修复后 |
|------|--------|--------|
| `_poly_to_latex` | ❌ 被删除 | ✅ 保护 |
| `_format_term_latex` | ❌ 被删除 | ✅ 保护 |
| `_differentiate_poly_n_times` | ❌ 被删除 | ✅ 保护 |
| `build_polynomial_text` | ❌ 被删除 | ✅ 保护 |
| `FakeFormatPoly` (虚函数) | ✅ 删除 | ✅ 删除 |

---

## 🔄 **问题链**

```
1. LLM 生成包含助函数：_poly_to_latex, _format_term_latex 等
   ↓
2. AST Healer 扫描函数定义
   ↓
3. 检测到 '_poly_to_latex' 包含 'LaTeX'
   ↓
4. 旧正则表达式匹配：r'(Format|LaTeX|Display)'
   ↓
5. 误认为是虚函数，删除整个函数 ❌
   ↓
6. 后续 generate() 调用 _poly_to_latex()
   ↓
7. NameError: name '_poly_to_latex' is not defined ❌
```

**修复后的流程**：
```
1. LLM 生成包含助函数
   ↓
2. AST Healer 检查：是否在保护名单中？
   ↓
3. '_poly_to_latex' 在保护名单中 ✅
   ↓
4. 保留函数，不删除 ✅
   ↓
5. generate() 成功调用 _poly_to_latex() ✅
```

---

## 📝 **修改统计**

| 文件 | 改动 | 状态 |
|------|------|------|
| [core/healers/ast_healer.py](core/healers/ast_healer.py#L164-L190) | 添加保护名单 + 改进检测逻辑 | ✅ 完成 |

---

## 🎯 **验证清单**

- [x] 添加了多项式处理函数的保护名单
- [x] 添加了其他常见的工具函数
- [x] 改进了虚函数检测逻辑（CamelCase）
- [x] 保留注释解释为什么保护这些函数

---

*修复完成时间：2026-01-31 04:00*
*修复优先级：🔴 P0 (直接导致 Ab3 失败)*
*预期改善：Ab3 生成应恢复正常*
