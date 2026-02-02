#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修復 ID 199 的 MASTER_SPEC - 使用SQL直接更新關鍵部分"""
import sqlite3
import re

conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()

# 讀取當前內容
content = cur.execute('SELECT prompt_content FROM skill_gencode_prompt WHERE id=199').fetchone()[0]

print(f'原始長度: {len(content)} 字元\n')

# 在 answer_display 區塊後添加重要警告
insertion_point = content.find('answer_display:')
if insertion_point > 0:
    # 找到下一個主要區塊
    next_section = content.find('\n\n    notes:', insertion_point)
    if next_section > 0:
        # 在 answer_display 區塊結尾前插入警告
        warning = '''
        
        ⚠️ **答案格式重要規則**：
        - 🔴 答案只包含多項式，不包含 f'(x) = 部分
        - 題目已經問「求 f'(x) 與 f''(x)」，答案只需給出多項式
        - ❌ 錯誤：`ans_parts.append(f"f'(x) = {poly}")`
        - ✅ 正確：`ans_parts.append(poly)`
        - 範例：正確答案 = "4x^3 - 6x^2 + 5\\n24x - 12"
'''
        content = content[:next_section] + warning + content[next_section:]
        print('✅ 已添加答案格式警告')

# 在檔案結尾添加代碼規範
if '禁止在代碼結尾' not in content:
    content += '''

⚠️ **代碼生成規範**：
1. **禁止在代碼結尾加說明文字**
   - ❌ 錯誤：在 Python 代碼後直接寫英文或中文說明
   - ✅ 正確：代碼結束後不加任何文字
   
2. **禁止呼叫 clean_latex_output()**
   - 題目字串已經包含 $ $ 符號
   - 再次包裝會導致 LaTeX 錯誤
   
3. **不設導數係數上限**
   - 移除任何「係數超過 100 就拒絕」的檢查
   - 導數計算自然產生的係數都是有效的
'''
    print('✅ 已添加代碼規範')

# 更新資料庫
cur.execute('UPDATE skill_gencode_prompt SET prompt_content = ? WHERE id = 199', (content,))
conn.commit()

print(f'\n✅ ID 199 已更新')
print(f'新長度: {len(content)} 字元')
print(f'\n驗證:')
print(f'  包含答案格式警告: {"只包含多項式" in content}')
print(f'  包含代碼規範: {"禁止在代碼結尾" in content}')

conn.close()
