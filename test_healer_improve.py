#!/usr/bin/env python3
import sys
sys.path.append(r'e:\python\MathProject_AST_Research')

from core.healers.unified_cleanup_healer import heal_unified

# 测试代码：包含重复的 IntegerOps 类
test_code = '''
class IntegerOps:
    @staticmethod
    def fmt_num(n):
        return f"({n})" if n < 0 else str(n)

    @staticmethod
    def random_nonzero(min_val, max_val):
        available = [x for x in range(min_val, max_val + 1) if x != 0]
        return random.choice(available)
        
    @staticmethod
    def method_c():
        pass

# [DUPLICATE - should be removed]
class IntegerOps:
    @staticmethod
    def random_nonzero(min_val, max_val):
        available = [x for x in range(min_val, max_val + 1) if x != 0]
        return random.choice(available)

def generate():
    return IntegerOps.fmt_num(5)
'''

print("="*80)
print("测试改进的重复类删除")
print("="*80)

print("\n1. 原始代码:")
print(f"   行数: {len(test_code.split(chr(10)))}")

import ast
try:
    tree = ast.parse(test_code)
    class_defs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if node.name not in class_defs:
                class_defs[node.name] = 0
            class_defs[node.name] += 1
    
    for class_name, count in class_defs.items():
        status = "✅" if count == 1 else "⚠️"
        print(f"   {status} 类 {class_name}: {count} 个定义")
except SyntaxError as e:
    print(f"   ❌ 解析失败: {e}")

print("\n2. 调用 heal_unified()...")
fixed_code, fixes = heal_unified(test_code)
print(f"   修复数: {fixes}")

print("\n3. 修复后的代码:")
print(f"   行数: {len(fixed_code.split(chr(10)))}")

try:
    tree_fixed = ast.parse(fixed_code)
    class_defs_fixed = {}
    for node in ast.walk(tree_fixed):
        if isinstance(node, ast.ClassDef):
            if node.name not in class_defs_fixed:
                class_defs_fixed[node.name] = 0
            class_defs_fixed[node.name] += 1
    
    all_ok = True
    for class_name, count in class_defs_fixed.items():
        if count == 1:
            print(f"   ✅ 类 {class_name}: {count} 个定义")
        else:
            print(f"   ❌ 类 {class_name}: {count} 个定义（仍然重复！）")
            all_ok = False
    
    if all_ok and fixes > 0:
        print("\n✅ 测试通过！重复类已被成功删除")
    elif all_ok:
        print("\n⚠️ 没有检测到重复，可能测试代码需要调整")
    else:
        print("\n❌ 测试失败！仍有重复类定义")
        
except SyntaxError as e:
    print(f"   ❌ 修复后解析失败: {e}")
    print(f"\n修复后代码预览:\n{fixed_code[:200]}...")

print("\n" + "="*80)
