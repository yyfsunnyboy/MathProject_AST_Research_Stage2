"""Remove everything after the FIRST [[END_MODE:LIVESHOW]] in SKILL.md"""
path = r'd:\Python\MathProject_AST_Research\agent_skills\jh_數學1上_FourArithmeticOperationsOfIntegers\SKILL.md'

with open(path, encoding='utf-8') as f:
    content = f.read()

marker = '[[END_MODE:LIVESHOW]]'
idx = content.find(marker)
if idx == -1:
    print("Marker not found!")
else:
    # Keep up to and including the first occurrence + closing ```
    end_idx = idx + len(marker)
    # Also include the closing ``` and newline
    rest = content[end_idx:]
    closing = '\n```'
    close_idx = rest.find(closing)
    if close_idx != -1:
        end_idx += close_idx + len(closing)
    
    new_content = content[:end_idx]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Done! File trimmed to {len(new_content)} chars.")
    print("Last 200 chars:", repr(new_content[-200:]))
