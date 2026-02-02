#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()
content = cur.execute('SELECT prompt_content FROM skill_gencode_prompt WHERE id=199').fetchone()[0]

key_reminder = '''

🔴 **關鍵提醒**：
1. 答案格式：只有多項式，不包含 f'(x) = 
2. 範例："3x^2 + 2x - 1\\n6x + 2" 而非 "f'(x) = 3x^2..." 
3. 禁止：clean_latex_output()、尾部說明文字、係數上限檢查
'''

content += key_reminder
cur.execute('UPDATE skill_gencode_prompt SET prompt_content = ? WHERE id = 199', (content,))
conn.commit()
print(f'✅ 更新完成，新長度: {len(content)}')
conn.close()
