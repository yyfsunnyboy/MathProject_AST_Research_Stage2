"""
測試 MAX_ATTEMPTS 守門員注入 - 包含複雜縮排
"""
import re
import textwrap

test_code = """
def generate(level=1, **kwargs):
    x = random.randint(1, 10)
    y = x * 2
    
    # 內層迴圈
    results = []
    for i in range(3):
        if i > 0:
            results.append(i * 2)
    
    q = f"計算 {x} 的兩倍"
    a = str(y)
    
    # 多行 return 字典（Qwen 常見格式）
    return {
        'question_text': q,
        'correct_answer': a,
        'answer': a,
        'mode': 1
    }
"""

print("原始代碼:")
print(test_code)
print("\n" + "="*80 + "\n")

# 模擬注入邏輯
clean_code = test_code
if "def generate(" in clean_code and "MAX_ATTEMPTS" not in clean_code:
    lines = clean_code.split('\n')
    func_def_idx = -1
    for idx, line in enumerate(lines):
        if 'def generate(' in line:
            func_def_idx = idx
            break
    
    if func_def_idx >= 0:
        func_def = lines[func_def_idx]
        func_body_lines = lines[func_def_idx + 1:]
        
        # 找到基礎縮排
        base_indent = ''
        for line in func_body_lines:
            if line.strip():
                base_indent = line[:len(line) - len(line.lstrip())]
                break
        
        if not base_indent:
            base_indent = '    '
        
        extra_indent = '        '
        
        # 組裝新的函數體
        new_func_body = [
            f"{base_indent}MAX_ATTEMPTS = 200",
            f"{base_indent}for __guard in range(MAX_ATTEMPTS):",
            f"{base_indent}    try:",
        ]
        
        # 處理每一行，保持相對縮排
        for line in func_body_lines:
            if line.strip():
                stripped_line = line.lstrip()
                original_indent_count = len(line) - len(stripped_line)
                base_indent_count = len(base_indent)
                
                relative_indent_count = original_indent_count - base_indent_count
                if relative_indent_count < 0:
                    relative_indent_count = 0
                
                new_line = base_indent + extra_indent + (' ' * relative_indent_count) + stripped_line
                new_func_body.append(new_line)
            else:
                new_func_body.append('')
        
        # 找到第一個 return 語句，在完整的字典之後加 break
        return_found = False
        return_indent = ''
        in_return_dict = False
        
        for idx, line in enumerate(new_func_body):
            stripped = line.strip()
            
            # 檢測 return 語句開始
            if not return_found and ('return {' in stripped or 'return{' in stripped):
                return_found = True
                return_indent = line[:len(line) - len(line.lstrip())]
                
                # 檢查是否是單行 return（整個字典在同一行）
                if stripped.endswith('}'):
                    # 單行 return，直接在下一行插入 break
                    new_func_body.insert(idx + 1, f"{return_indent}break")
                    break
                else:
                    # 多行 return，需要找到字典結束的 }
                    in_return_dict = True
            
            # 如果在多行 return 字典中，找到結束的 }
            elif return_found and in_return_dict:
                if '}' in stripped:
                    # 找到字典結束，在下一行插入 break
                    new_func_body.insert(idx + 1, f"{return_indent}break")
                    break
        
        # 加入 except 和保底
        new_func_body.extend([
            f"{base_indent}    except Exception:",
            f"{base_indent}        continue",
            f"{base_indent}else:",
            f"{base_indent}    q = \"保底\"",
            f"{base_indent}    a = \"答案\"",
            f"{base_indent}    return {{'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}}",
        ])
        
        new_lines = lines[:func_def_idx + 1] + new_func_body
        clean_code = '\n'.join(new_lines)

print("注入後的代碼:")
print(clean_code)

# 測試語法
try:
    compile(clean_code, '<test>', 'exec')
    print("\n✅ 語法正確！")
except SyntaxError as e:
    print(f"\n❌ 語法錯誤: {e}")
    print(f"   行號: {e.lineno}")
    print(f"   位置: {e.offset}")
