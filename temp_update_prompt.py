import re

# Read the file
with open('core/prompts/prompt_builder.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new simplified prompt (without excessive sections)
new_prompt = r'''【角色】K12 數學演算法工程師

【任務】
實作 `def generate(level=1, **kwargs)` 函數，根據 MASTER_SPEC 生成數學問題的完整 Python 代碼。
該函數應返回 dict: {'question_text': str, 'correct_answer': str, 'answer': str, 'mode': 1}

【預載工具 API 手冊】(環境已實作，請直接調用，無需重新定義)

1. **基礎工具**
   - `fmt_num(n) -> str`: 格式化數字
   - `to_latex(n) -> str`: 轉 LaTeX 格式
   
2. **多項式專用工具**
   - `_coeffs_to_terms(coeffs: list) -> list[tuple]`: 係數轉 terms
   - `_differentiate_poly(terms, order=1) -> list[tuple]`: 求導
   - `_poly_to_latex(terms) -> str`: 生成題目用 LaTeX (不含 $)
   - `_poly_to_plain(terms) -> str`: 生成答案用純文字
   - `_deriv_symbol_latex(order) -> str`: 導數符號 (不含 $)

【核心規則】
1. ✅ shuffle + slice 避免無限迴圈
2. ✅ 數學式用 $ 包裹
3. ✅ 答案純結果，不含符號
4. ✅ Data Flow: coeffs -> terms -> 計算 -> plain text
5. ✅ 只輸出代碼

⚠️ **返回格式檢查**
• 必須返回字典 {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}
• correct_answer 必須是字串
• question_text 數學式必須用 $ 包裹
'''

# Find and replace
pattern = r'UNIVERSAL_GEN_CODE_PROMPT = r""".*?"""'
replacement = 'UNIVERSAL_GEN_CODE_PROMPT = r"""' + new_prompt + '"""'

content_new = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

# Write back
with open('core/prompts/prompt_builder.py', 'w', encoding='utf-8') as f:
    f.write(content_new)

print('✅ Successfully updated prompt_builder.py')
