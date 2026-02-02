#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from core.prompts.prompt_builder import UNIVERSAL_GEN_CODE_PROMPT, PromptBuilder
from core.prompts.domain_function_library import get_required_domains, get_domain_helpers_code

skill_id = 'gh_ApplicationsOfDerivatives'
domains = get_required_domains(skill_id)
code = get_domain_helpers_code(domains)

template_prefix = f"""

### 🔧 [強制規範] 標準函數庫 (請務必使用以下函數，禁止自創同名函數)

此題目屬於以下數學領域：{', '.join(domains)}

請**優先使用**以下預定義的標準函數（禁止重新定義相同功能的函數）：

"""

template_suffix = """

⚠️ 重要規則：
1. 如果標準函數庫已提供相應函數（例如 _poly_to_latex），請直接調用，不要自己重新實現
2. 你只需要實現 `def generate(level=1, **kwargs)` 函數
3. 標準函數庫的函數簽名和命名必須嚴格遵守，不得修改
4. 禁止創建 CamelCase 命名的函數（例如 FormatPolynomial）

🔴 **導數題型答案格式（CRITICAL）**：
當使用 _differentiate_poly() 等函數時，答案格式要求：
- ✅ 正確：直接用 _poly_to_plain() 轉換每個導數，然後用 ', '.join() 連接
  ```python
  ans_parts = []
  for order, deriv_terms in derivative_results:
      ans_parts.append(_poly_to_plain(deriv_terms))
  correct_answer = ', '.join(ans_parts)  # 例如："35x^4 - 8x^3 + 5, 420x^2 - 48x"
  ```
- ❌ 錯誤：包含導數符號或等號
  ```python
  # 不要這樣做：
  ans_parts.append(f"f'(x) = {{_poly_to_plain(deriv_terms)}}")  # ❌
  ```
"""

total_injection = template_prefix + code + template_suffix

print("=== Domain Injection 組成 ===")
print(f"前綴:   {len(template_prefix):,} chars")
print(f"程式碼: {len(code):,} chars")
print(f"後綴:   {len(template_suffix):,} chars")
print(f"總計:   {len(total_injection):,} chars")
print()
print("=== 完整 Prompt 組成 ===")
print(f"UNIVERSAL:        {len(UNIVERSAL_GEN_CODE_PROMPT):,} chars")
print(f"Domain Injection: {len(total_injection):,} chars")
print(f"小計:              {len(UNIVERSAL_GEN_CODE_PROMPT) + len(total_injection):,} chars")
print()
print("加上 MASTER_SPEC 後:")
import sqlite3
conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()
master = cur.execute(
    'SELECT prompt_content FROM skill_gencode_prompt WHERE skill_id=? ORDER BY id DESC LIMIT 1',
    (skill_id,)
).fetchone()[0]
conn.close()

print(f"MASTER_SPEC (最新): {len(master):,} chars")

header = "\n\n### MASTER_SPEC:\n"
total = len(UNIVERSAL_GEN_CODE_PROMPT) + len(total_injection) + len(header) + len(master)
print(f"Header:            {len(header)} chars")
print(f"===")
print(f"總計:               {total:,} chars")
print()
print("=== Token 估算 ===")
print(f"以 2.0 chars/token: {total//2:,} tokens")
print(f"以 2.5 chars/token: {total/2.5:.0f} tokens")
print(f"以 3.0 chars/token: {total//3:,} tokens")
print()
print(f"🔴 實際報告: 18,052 tokens")
print(f"反推比例: {total/18052:.2f} chars/token")
