import re

def to_latex(op_str):
    if op_str == '*': return '\\times'
    if op_str == '/': return '\\div'
    return op_str

op1 = '/'
op2 = '*'
l_op1 = to_latex(op1)
l_op2 = to_latex(op2)
math_str = f"|5 {l_op1} 2| {l_op2} 3"

print("Original f-string result:", math_str)
print("After replace (live_show.py):", math_str.replace('\\div', '\\\\div').replace('\\times', '\\\\times'))
