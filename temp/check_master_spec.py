#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""檢查當前 MASTER_SPEC 內容"""
import sqlite3

conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()
spec = cur.execute(
    'SELECT prompt_content FROM skill_gencode_prompt WHERE skill_id="gh_ApplicationsOfDerivatives" AND prompt_type="MASTER_SPEC"'
).fetchone()[0]

print('='*80)
print('MASTER_SPEC 搜尋結果')
print('='*80)
print(f'長度: {len(spec)} 字元')
print(f'包含 _deriv_symbol_plain: {"_deriv_symbol_plain" in spec}')
print(f'包含 for order, _: {"for order, _" in spec}')
print(f'包含 for order, deriv: {"for order, deriv" in spec}')

# 找出格式化導數符號段落
import re
match = re.search(r'格式化導數符號.*?(?=\n\n##|\Z)', spec, re.DOTALL)
if match:
    print('\n' + '='*80)
    print('格式化導數符號段落')
    print('='*80)
    print(match.group(0)[:500])
else:
    print('\n找不到「格式化導數符號」段落')
    
# 檢查是否有禁止 clean_latex_output
if 'clean_latex_output' in spec:
    print('\n⚠️  仍包含 clean_latex_output')
    match2 = re.search(r'.*clean_latex_output.*', spec, re.MULTILINE)
    if match2:
        print('相關行:', match2.group(0))
else:
    print('\n✅ 已移除 clean_latex_output')

conn.close()
