"""
Test for bracket mismatch fix
验证 fix_mismatched_braces() 是否能正确处理缺失括号问题
"""

import sys
sys.path.insert(0, r'e:\\python\\MathProject_AST_Research')

from core.healers.regex_healer import RegexHealer

print("="*80)
print("BRACKET MISMATCH FIX TEST")
print("="*80)

healer = RegexHealer()

# 测试 1: 缺少返回字典的右括号
print("\n[TEST 1] 缺少返回字典的右括号")
code_with_missing_brace = """def generate():
    return {
        'question_text': 'test',
        'answer': '42',
        'mode': 1"""

print(f"输入 (缺少最后的}}): ")
print(code_with_missing_brace)
print()

fixed, stats = healer.heal(code_with_missing_brace)

print("修复后:")
print(fixed)
print()

if '}' in fixed[-20:]:
    print("✅ PASS: 缺失的括号已修复")
else:
    print("❌ FAIL: 括号仍未修复")

# 测试 2: 多个缺失括号
print("\n" + "="*80)
print("[TEST 2] 多个缺失括号")
code_with_multiple = """def test(x, y):
    result = [
        {'a': 1, 'b': 2"""

print(f"输入 (缺少 }} 和 ]):  ")
print(code_with_multiple)
print()

fixed, stats = healer.heal(code_with_multiple)

print("修复后:")
print(fixed)
print()

if '}' in fixed and ']' in fixed:
    print("✅ PASS: 多个括号已修复")
else:
    print("❌ FAIL: 仍有括号未修复")

# 测试 3: 实际的 Ab3 错误场景
print("\n" + "="*80)
print("[TEST 3] 实际 Ab3 错误 - 返回字典缺少右括号")
ab3_error_code = """def generate(level=1, **kwargs):
    final_val = 42
    q = "计算的值"
    
    return {
        'question_text': q,
        'correct_answer': str(final_val),
        'answer': str(final_val),
        'mode': 1"""

print("输入 (模拟 Ab3 错误):")
print(ab3_error_code[-50:])  # 显示末尾 50 字符
print()

fixed, stats = healer.heal(ab3_error_code)

print("修复后末尾:")
print(fixed[-50:])  # 显示末尾 50 字符
print()

# 验证语法
try:
    compile(fixed, '<string>', 'exec')
    print("✅ PASS: 修复后的代码可以编译")
    print(f"   修复统计: {stats}")
except SyntaxError as e:
    print(f"❌ FAIL: 编译失败: {e}")

print("\n" + "="*80)
print("✅ 括号修复测试完成")
print("="*80)
