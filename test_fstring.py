import re
import ast

code = r"""
def generate(level=1):
    question_text = f'計算 it\'s 
 的值。'
    ans = 10
"""

def fix(code_str):
    # Regex:
    # f? -> Optional 'f'
    # ' -> Single quote
    # (?: [^'\\] | \\. )*? -> Any char except ' or \, or a \ followed by any char.
    # We use r"..." so we need:
    # [^'\\] to match any char except ' and \
    # \\. to match \ followed by any char. (r"\\." -> `\\` and `.` -> regex `\\` matches `\`, `.` matches any char)
    
    code_str, c1 = re.subn(r"(f?)(['])((?:[^'\\]|\\.)*?\n(?:[^'\\]|\\.)*?)[']", r"\1'''\3'''", code_str)
    code_str, c2 = re.subn(r'(f?)(["])((?:[^"\\]|\\.)*?\n(?:[^"\\]|\\.)*?)["]', r'\1"""\3"""', code_str)
    return code_str, c1+c2

fixed_code, c = fix(code)
print("Fixed code:")
print(fixed_code)
# Test ast.parse
ast.parse(fixed_code)
print("AST parsed successfully!")
