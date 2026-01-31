# -*- coding: utf-8 -*-
import re

# 测试上标转换
test_cases = [
    "f(x) = -5x^{7}-7x^{6}-7x^{5}-6x^{4}+7x^{3}-7x-5",
    "已知 $f(x) = -5x^{7}-7x^{6}-7x^{5}-6x^{4}+7x^{3}-7x-5$, 求 f'(x) 的值。"
]

superscript_map = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
}

def replace_superscript(match):
    num_str = match.group(1) or match.group(2)
    return ''.join(superscript_map.get(d, d) for d in num_str)

for latex_str in test_cases:
    text_version = latex_str.replace('$', '').strip()
    text_version = re.sub(r'\^\{(\d+)\}|\^(\d)', replace_superscript, text_version)
    
    # 写入文件避免编码问题
    with open('temp/output.txt', 'a', encoding='utf-8') as f:
        f.write(f"原始: {latex_str}\n")
        f.write(f"转换: {text_version}\n")
        f.write("-" * 80 + "\n")
    
print("结果已保存到 temp/output.txt")
