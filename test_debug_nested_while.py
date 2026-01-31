"""
調試嵌套 while 檢測
"""
import re

code = """
def generate(level=1, **kwargs):
    derivative_orders_list = []
    while len(derivative_orders_list) < num_derivatives:
        while len(derivative_orders_list) < num_derivatives:
            order = random.randint(1, min(max_degree, 4))
        if all((order != o for o in derivative_orders_list)):
            derivative_orders_list.append(order)
    return derivative_orders_list
"""

lines = code.split('\n')
for i, line in enumerate(lines):
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())
    
    print(f"Line {i}: indent={indent}, stripped='{stripped[:50]}'")
    
    if stripped.startswith('while len'):
        print(f"  → 找到外層 while!")
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            next_stripped = next_line.strip()
            next_indent = len(next_line) - len(next_line.lstrip())
            print(f"  → 下一行: indent={next_indent}, stripped='{next_stripped[:50]}'")
            
            if next_stripped.startswith('while len') and next_indent > indent:
                print(f"  ✅ 檢測到嵌套 while!")
                
                outer_match = re.match(r'while\s+len\s*\(\s*(\w+)\s*\)\s*<\s*(.+):', stripped)
                inner_match = re.match(r'while\s+len\s*\(\s*(\w+)\s*\)\s*<\s*(.+):', next_stripped)
                
                if outer_match and inner_match:
                    print(f"  → 外層: var={outer_match.group(1)}, target={outer_match.group(2)}")
                    print(f"  → 內層: var={inner_match.group(1)}, target={inner_match.group(2)}")
