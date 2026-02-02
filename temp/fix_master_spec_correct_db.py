#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修復正確資料庫的 MASTER_SPEC
Database: instance/kumon_math.db
Table: skill_gencode_prompt
"""
import sqlite3

# 完整的新 MASTER_SPEC（包含所有修復）
NEW_MASTER_SPEC = """## 多項式微分應用 - 生成規範

### 題目類型
給定一個多項式 $f(x)$，要求計算指定階數的導數。

### 約束條件
1. **多項式結構**：
   - 最高次數 `max_degree` 必須 ≥ 3（確保有足夠複雜度）
   - 項數 `num_terms` 不能超過 `max_degree + 1`（避免重複項）
   - 最低次數範圍：0 到 2
   - 係數範圍：[-12, 12]，排除 0 和 ±1（避免過於簡單）

2. **導數階數選擇**：
   - 從 1 到 `max_degree` 範圍內隨機選 2-3 個不同階數
   - 必須確保階數 < 多項式次數（避免全為 0 的無效導數）
   - 排序後顯示（從低到高）

3. **LaTeX 格式**：
   - 題目用 LaTeX 格式：`$f(x) = ...$`
   - 答案用純文字格式（plain text）
   - 🔴 **禁止**: 不要呼叫 `clean_latex_output(q)`
   - 🔴 **禁止**: 不要在代碼結尾加任何說明文字或註解段落
   - 多項式係數顯示：
     * 正數係數：`+1x^3`（保留正號）
     * 負數係數：`-2x^2`（直接負號）
     * 係數 1：`+1x` 而非 `+x`（保持統一格式）

4. **格式化導數符號 ⚠️ 關鍵步驟**：
   - 資料結構：`derivative_results = [(order, deriv_terms), ...]`
     * `order` (int): 導數階數
     * `deriv_terms` (list): 導數多項式的項 [(係數, 次數), ...]
   
   - **正確解包**：`for order, _ in derivative_results:` 或 `for order, deriv_terms in derivative_results:`
   - **錯誤解包**：`for _, order in derivative_results:` ❌ 會把 list 當成階數
   
   - **答案格式**：
     * 🔴 **重要**：`correct_answer` 只包含多項式本身，**不包含** `f'(x) =` 部分
     * 題目中已經詢問 `f'(x)` 和 `f''(x)`，答案只需給出多項式
     * 多個導數用換行符 `\n` 分隔（或逗號 `, `）
   
   - **正確範例**：
     ```python
     ans_parts = []
     for order, deriv_terms in derivative_results:
         poly = _poly_to_plain(deriv_terms)  # 只要多項式
         ans_parts.append(poly)              # 不要加 f'(x) = 
     correct_answer = "\n".join(ans_parts)   # 用換行分隔
     ```
   
   - **錯誤範例** ❌：
     ```python
     # 錯誤：包含了 f'(x) = 
     ans_parts.append(f"f^{{({order})}}(x) = {poly}")
     ```

### 輔助函數（必須實作）
```python
def _deriv_symbol_latex(order):
    \"\"\"生成 LaTeX 導數符號\"\"\"
    if order == 1:
        return "f'(x)"
    elif order == 2:
        return "f''(x)"
    elif order == 3:
        return "f'''(x)"
    else:
        return f"f^{{({order})}}(x)"

def _deriv_symbol_plain(order):
    \"\"\"生成純文字導數符號（與 LaTeX 相同）\"\"\"
    return _deriv_symbol_latex(order)

def _poly_to_latex(terms):
    \"\"\"將多項式項轉換為 LaTeX 字串\"\"\"
    # [(coef, deg), ...] → "3x^2 + 2x - 1"
    pass

def _poly_to_plain(terms):
    \"\"\"將多項式項轉換為純文字字串\"\"\"
    # 與 _poly_to_latex 相同格式
    pass

def _differentiate_poly(terms, order):
    \"\"\"計算多項式的 order 階導數\"\"\"
    # 回傳: [(coef, deg), ...]
    pass
```

### 返回格式
```python
{
    'question_text': str,      # LaTeX 格式的題目
    'correct_answer': str,     # 純文字格式的答案（多行，每行一個導數）
    'answer': str,             # 與 correct_answer 相同
    'mode': 1                  # 固定為 1
}
```

### ⚠️ 代碼規範
- **只生成 Python 代碼**，不要在檔案結尾加任何說明文字
- 錯誤示例：
  ```python
  # 代碼結尾
  print(generate())
  This implementation follows the guidelines...  # ❌ 禁止
  這個程式碼會生成一個隨機的四次多項式...     # ❌ 禁止
  ```
- 正確示例：
  ```python
  # 代碼結尾
  print(generate())
  # 檔案結束，沒有任何說明文字 ✅
  ```

### 範例
```python
# 輸入參數
max_degree = 4
num_derivatives = 2

# 生成結果
question_text = "已知 $f(x) = 2x^4 + -3x^3 + 5x - 2$，求 $f'(x)$ 與 $f'''(x)$。"
correct_answer = "8x^3 + -9x^2 + 5\n48x + -18"  # 只有多項式，用換行分隔
```
"""

# 連接資料庫
conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()

# 查詢當前 MASTER_SPEC
cur.execute("""
    SELECT id, prompt_content 
    FROM skill_gencode_prompt 
    WHERE skill_id = 'gh_ApplicationsOfDerivatives' 
    AND prompt_type = 'MASTER_SPEC'
""")
result = cur.fetchone()

if not result:
    print("❌ 找不到 MASTER_SPEC 記錄")
    conn.close()
    exit(1)

record_id, old_content = result
print(f"找到記錄 ID: {record_id}")
print(f"舊內容長度: {len(old_content)} 字元")
print(f"新內容長度: {len(NEW_MASTER_SPEC)} 字元")

# 檢查舊內容問題
has_clean_latex = 'clean_latex_output' in old_content
has_deriv_symbol = '_deriv_symbol_plain' in old_content
print(f"\n舊內容檢查:")
print(f"  包含 clean_latex_output: {has_clean_latex} {'❌' if has_clean_latex else '✅'}")
print(f"  包含 _deriv_symbol_plain: {has_deriv_symbol} {'✅' if has_deriv_symbol else '❌'}")

# 更新資料庫
cur.execute("""
    UPDATE skill_gencode_prompt 
    SET prompt_content = ?
    WHERE id = ?
""", (NEW_MASTER_SPEC, record_id))

conn.commit()
print(f"\n✅ MASTER_SPEC 已更新")

# 驗證更新
cur.execute("SELECT prompt_content FROM skill_gencode_prompt WHERE id = ?", (record_id,))
updated = cur.fetchone()[0]
print(f"\n驗證:")
print(f"  更新後長度: {len(updated)} 字元")
print(f"  包含 clean_latex_output: {'clean_latex_output' in updated} {'❌ 更新失敗' if 'clean_latex_output' in updated else '✅'}")
print(f"  包含 _deriv_symbol_plain: {'_deriv_symbol_plain' in updated} {'✅' if '_deriv_symbol_plain' in updated else '❌ 更新失敗'}")
print(f"  包含 for order, _: {'for order, _' in updated or 'for order, deriv' in updated}")

conn.close()
print("\n✅ 完成")
