#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""分析 Prompt 組成"""
import sqlite3
from core.prompts.prompt_builder import UNIVERSAL_GEN_CODE_PROMPT, PromptBuilder
from core.prompts.domain_function_library import get_required_domains, get_domain_helpers_code

skill_id = "gh_ApplicationsOfDerivatives"

# 1. UNIVERSAL_GEN_CODE_PROMPT
universal_len = len(UNIVERSAL_GEN_CODE_PROMPT)
print(f"1. UNIVERSAL_GEN_CODE_PROMPT: {universal_len:,} 字元 (≈{universal_len//3:,} tokens)")

# 2. Domain 注入
required_domains = get_required_domains(skill_id)
domain_code = get_domain_helpers_code(required_domains)
domain_injection_template = f"""

### 🔧 [強制規範] 標準函數庫 (請務必使用以下函數，禁止自創同名函數)

此題目屬於以下數學領域：{', '.join(required_domains)}

請**優先使用**以下預定義的標準函數（禁止重新定義相同功能的函數）：

{domain_code}

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
domain_len = len(domain_injection_template)
print(f"2. Domain 注入: {domain_len:,} 字元 (≈{domain_len//3:,} tokens)")

# 3. 最新的 MASTER_SPEC
conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()
master_spec = cur.execute(
    'SELECT prompt_content FROM skill_gencode_prompt WHERE skill_id=? ORDER BY id DESC LIMIT 1',
    (skill_id,)
).fetchone()[0]
master_len = len(master_spec)
print(f"3. MASTER_SPEC (最新): {master_len:,} 字元 (≈{master_len//3:,} tokens)")

# 4. 總和
total_len = universal_len + domain_len + master_len + 50  # 50 for joining text
print(f"\n總計: {total_len:,} 字元 (≈{total_len//3:,} tokens)")

# 5. Token 估算（考慮中英文混合）
estimated_tokens = int(total_len / 2.5)  # 混合中英文約 2.5 字元/token
print(f"精確估算: ≈{estimated_tokens:,} tokens")

# 6. 詳細分解
print(f"\n=== 詳細分解 ===")
print(f"UNIVERSAL: {universal_len/total_len*100:.1f}%")
print(f"Domain:    {domain_len/total_len*100:.1f}%")
print(f"MASTER:    {master_len/total_len*100:.1f}%")

conn.close()
