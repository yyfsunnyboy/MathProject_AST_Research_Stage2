import sys

def fix_math_brackets(math_str):
    s = str(math_str)
    
    # 1. 統一所有群組括號為純 ()
    s = s.replace(r'\left(', '(').replace(r'\right)', ')')
    s = s.replace(r'\left[', '(').replace(r'\right]', ')')
    s = s.replace('[', '(').replace(']', ')')
    s = s.replace(r'\left\{', '(').replace(r'\right\}', ')')
    s = s.replace(r'\{', '(').replace(r'\}', ')')
    
    # 2. 移除冗餘的雙括號 (( ... )) -> ( ... )
    while True:
        stack = []
        pairs = {}
        valid = True
        for i, c in enumerate(s):
            if c == '(':
                stack.append(i)
            elif c == ')':
                if not stack:
                    valid = False; break
                start = stack.pop()
                pairs[start] = i
        if stack or not valid:
            break
            
        redundant_start = -1
        redundant_end = -1
        for start, end in pairs.items():
            first_non_space = start + 1
            while first_non_space < end and s[first_non_space].isspace():
                first_non_space += 1
                
            last_non_space = end - 1
            while last_non_space > start and s[last_non_space].isspace():
                last_non_space -= 1
                
            if first_non_space < end and s[first_non_space] == '(' and s[last_non_space] == ')':
                if pairs.get(first_non_space) == last_non_space:
                    redundant_start = start
                    redundant_end = end
                    break
                    
        if redundant_start != -1:
            s = s[:redundant_start] + ' ' + s[redundant_start+1:redundant_end] + ' ' + s[redundant_end+1:]
        else:
            break
            
    # 3. 確保括號平衡再進行升級
    temp_count = 0
    balanced = True
    for c in s:
        if c == '(': temp_count += 1
        elif c == ')':
            temp_count -= 1
            if temp_count < 0:
                balanced = False; break
    if temp_count != 0: balanced = False
    
    if not balanced:
        return math_str # 降級處理
        
    nodes = []
    temp_stack = []
    root_nodes = []
    
    for i, c in enumerate(s):
        if c == '(':
            new_node = {'start': i, 'end': -1, 'children': [], 'depth': 1}
            nodes.append(new_node)
            if temp_stack:
                temp_stack[-1]['children'].append(new_node)
            else:
                root_nodes.append(new_node)
            temp_stack.append(new_node)
        elif c == ')':
            if temp_stack:
                node = temp_stack.pop()
                node['end'] = i
                
    def compute_depth(node):
        if not node['children']:
            node['depth'] = 1
        else:
            max_child_depth = max(compute_depth(child) for child in node['children'])
            node['depth'] = max_child_depth + 1
        return node['depth']
        
    for root in root_nodes:
        compute_depth(root)
        
    replacements = {}
    for node in nodes:
        d = node['depth']
        if d == 1:
            replacements[node['start']] = '('
            replacements[node['end']] = ')'
        elif d == 2:
            replacements[node['start']] = r'\left['
            replacements[node['end']] = r'\right]'
        else:
            replacements[node['start']] = r'\left\{'
            replacements[node['end']] = r'\right\}'
            
    parts = []
    for i, c in enumerate(s):
        if i in replacements:
            parts.append(replacements[i])
        else:
            parts.append(c)
            
    return "".join(parts)

def test():
    cases = [
        ("((-32\\frac{1}{2}))", "( -32\\frac{1}{2} )"),
        ("(( -32\\frac{1}{2} ))", " ( -32\\frac{1}{2} ) "),
        ("(3 - (-2))", "\\left[3 - (-2)\\right]"),
        ("((1 + (2 - (-3))))", "\\left\\{ 1 + \\left[2 - (-3)\\right] \\right\\}"),
        ("(-69) - ((-32\\frac{1}{2}))", "(-69) - ( -32\\frac{1}{2} )"),
        ("(-60) \\div ((-7) \\times 2 - 1)", "(-60) \\div \\left[(-7) \\times 2 - 1\\right]"),
        ("\\frac{1}{((-2)})", "Error - unbalance or weird, fallback expected? Wait no"), 
    ]
    
    for ipt, exp in cases:
        out = fix_math_brackets(ipt)
        print(f"I: {ipt}\nO: {out}\nE: {exp}\n--")

if __name__ == '__main__':
    test()
