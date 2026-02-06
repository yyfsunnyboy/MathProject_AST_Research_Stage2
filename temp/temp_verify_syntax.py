from core.prompts.domain_function_library import POLYNOMIAL_HELPERS

print("📋 检查 POLYNOMIAL_HELPERS:")

# 检查正确版本（转义的换行符）
if r"'\n'.join()" in POLYNOMIAL_HELPERS:
    print("  ✅ 正确: 包含 '\\n'.join()")
# 检查错误版本（实际换行符 - 会导致语法错误）
elif "'\n'.join()" in POLYNOMIAL_HELPERS:  
    print("  ❌ 错误: 包含实际换行符（语法错误）")
else:
    print("  ⚠️  未找到该注释")

# 显示相关行
print("\n📝 POLYNOMIAL_HELPERS 前 10 行:")
for i, line in enumerate(POLYNOMIAL_HELPERS.split('\n')[:10], start=1):
    print(f"  Line {i}: {line}")
