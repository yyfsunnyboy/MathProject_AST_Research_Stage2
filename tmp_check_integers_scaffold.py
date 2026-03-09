# -*- coding: utf-8 -*-
import re, sys, ast
sys.stdout.reconfigure(encoding='utf-8')

ls = open('agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers/prompt_liveshow.md', encoding='utf-8').read()
m = re.search(r'```python\s*(.*?)```', ls, re.DOTALL)
if m:
    code = m.group(1).strip()
    print('=== found code block ===')
    for i, line in enumerate(code.splitlines(), 1):
        print(f'{i:3}: {line}')
    print()
    try:
        ast.parse(code)
        print('AST: OK')
    except SyntaxError as e:
        print(f'AST ERROR: {e}')
else:
    print('no python block found')
