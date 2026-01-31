"""
測試 F.13 導數答案格式修復
"""
import re

test_cases = [
    # 測試案例 1: f"{_deriv_symbol_plain(order)} = {poly}"
    (
        'ans_parts.append(f"{_deriv_symbol_plain(order)} = {derivative_poly_plain}")',
        'ans_parts.append(derivative_poly_plain)'
    ),
    # 測試案例 2: f"f'(x) = {poly}"
    (
        'ans_parts.append(f"f\'(x) = {poly_str}")',
        'ans_parts.append(f"{poly_str}")'
    ),
    # 測試案例 3: 實際代碼片段
    (
        '''    ans_parts = []
    for order, deriv_terms in sorted(derivative_results, key=lambda x: x[0]):
        derivative_poly_latex = _poly_to_plain(deriv_terms)
        ans_parts.append(f"{_deriv_symbol_plain(order)} = {derivative_poly_latex}")
    correct_answer = '\\n'.join(ans_parts)''',
        '''    ans_parts = []
    for order, deriv_terms in sorted(derivative_results, key=lambda x: x[0]):
        derivative_poly_latex = _poly_to_plain(deriv_terms)
        ans_parts.append(derivative_poly_latex)
    correct_answer = '\\n'.join(ans_parts)'''
    ),
]

print("測試 F.13 導數答案格式修復\n" + "="*60)

for idx, (before, expected) in enumerate(test_cases, 1):
    print(f"\n測試案例 {idx}:")
    print(f"修復前:\n{before}\n")
    
    # 應用修復邏輯
    after = before
    
    # 模式 1: ans_parts.append(f"{_deriv_symbol_plain(order)} = {variable_name}")
    after, n1 = re.subn(
        r'ans_parts\.append\s*\(\s*f(["\'])(?:\{[^}]+\})\s*=\s*\{([^}]+)\}\1\s*\)',
        r'ans_parts.append(\2)',
        after
    )
    
    # 模式 2: ans_parts.append(f"f'(x) = {variable_name}")
    after, n2 = re.subn(
        r'ans_parts\.append\s*\(\s*f(["\'])f[\'\"]*\([^)]+\)\s*=\s*\{([^}]+)\}\1\s*\)',
        r'ans_parts.append(\2)',
        after
    )
    
    print(f"修復後:\n{after}\n")
    print(f"替換次數: n1={n1}, n2={n2}")
    
    if after == expected:
        print("✅ 測試通過")
    else:
        print(f"❌ 測試失敗")
        print(f"期望結果:\n{expected}")

print("\n" + "="*60)
