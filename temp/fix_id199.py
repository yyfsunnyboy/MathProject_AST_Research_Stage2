#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修復 ID 199 的 MASTER_SPEC"""
import sqlite3

conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()

# 讀取當前內容
content = cur.execute('SELECT prompt_content FROM skill_gencode_prompt WHERE id=199').fetchone()[0]

# 修復 1: 移除 clean_latex_output 指令
content = content.replace(
    '最後呼叫 `clean_latex_output(q)`',
    '**禁止**呼叫 `clean_latex_output(q)` (會導致LaTeX錯誤)'
)

# 修復 2: 更新答案格式說明（答案只包含多項式，不包含 f'(x) = ）
old_answer = '''answer_display: |
        蝑??澆?????憭?獢??蝚?`\\n` ??嚗?
        - 撠瘥?蝞????$f^{(k)}(x)$嚗?
          - 擐?雿輻??`question_display` 銝剜撘???憭?撘???孵?嚗? $f^{(k)}(x)$ ?澆?? LaTeX 摮葡 `derivative_poly_latex`??
          - ?嗅?蝯???`f^{(k)}(x) = {derivative_poly_latex}` ?耦撘?
          - 蝭?嚗f"f'(x) = 4x^3 - 6x^2 + 5\\nf'''(x) = 24x - 12"`'''

new_answer = '''answer_display: |
        🔴 **重要**：答案只包含多項式本身，不包含 f'(x) = 部分。
        將多個導數用換行符 `\\n` 分隔：
        - 對每個導數 $f^{(k)}(x)$：
          - 使用與 `question_display` 中相同的多項式格式化方法，將 $f^{(k)}(x)$ 格式化為 LaTeX 字串 `derivative_poly_latex`。
          - 直接將多項式加入答案：`ans_parts.append(derivative_poly_latex)`
          - ❌ 錯誤：`f"f'(x) = {poly}"` 
          - ✅ 正確：`f"{poly}"`
          - 範例：`"4x^3 - 6x^2 + 5\\n24x - 12"` (只有多項式)'''

content = content.replace(old_answer, new_answer)

# 修復 3: 添加禁止尾部說明文字的規則
if '禁止在代碼結尾加說明文字' not in content:
    content += '''\n
⚠️ **代碼規範**：
- 只生成 Python 函數代碼
- 禁止在代碼結尾加任何說明文字或註解段落
- 錯誤示例：
  ```
  print(generate())
  This implementation follows...  # ❌ 禁止
  ```
- 正確示例：
  ```
  print(generate())
  # 檔案結束 ✅
  ```
'''

# 修復 4: 移除係數限制檢查（避免合理導數被拒絕）
content = content.replace(
    '導數結果的係數範圍: 絕對值不超過 100',
    '導數結果的係數: 計算過程自然產生（不設上限，避免拒絕合理結果）'
)

# 更新資料庫
cur.execute('UPDATE skill_gencode_prompt SET prompt_content = ? WHERE id = 199', (content,))
conn.commit()

print(f'✅ ID 199 已更新')
print(f'新長度: {len(content)} 字元')
print(f'\n包含禁止 clean_latex_output: {"clean_latex_output" in content and "禁止" in content}')
print(f'包含答案格式規範: {"只包含多項式本身" in content}')
print(f'包含代碼規範: {"禁止在代碼結尾加說明文字" in content}')

conn.close()
