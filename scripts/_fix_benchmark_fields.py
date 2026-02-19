"""Fix benchmark.py data field bugs:
1. Remove duplicate wrong-key healer_fixes lines in load_failed block
2. Add 'response and' guard to hasattr() for token/latency fields
"""
path = r'E:\Python\MathProject_AST_Research\agent_tools\benchmark.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed = []
for i, line in enumerate(lines):
    lineno = i + 1

    # Fix 1: Remove lines with wrong healer_fixes keys ('fixes_basic', 'fixes_regex', 'fixes_ast')
    if ("healer_fixes.get('fixes_basic'" in line or
        "healer_fixes.get('fixes_regex'" in line or
        "healer_fixes.get('fixes_ast'" in line):
        print(f'REMOVING line {lineno}: {repr(line.rstrip())}')
        continue  # drop this line

    # Fix 2: Add 'response and' guard where missing
    for field in ['prompt_tokens', 'completion_tokens', 'total_tokens', 'latency_ms']:
        if field in line and 'if hasattr(response,' in line and 'response and' not in line:
            line = line.replace('if hasattr(response,', 'if response and hasattr(response,')
            print(f'FIXED {field} guard at line {lineno}')
            break  # one check per line is enough

    fixed.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(fixed)
print('Done. Total lines written:', len(fixed))
