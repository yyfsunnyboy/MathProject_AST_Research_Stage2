#!/usr/bin/env python3
import sys
sys.path.append(r'e:\python\MathProject_AST_Research')

from core.healers.unified_cleanup_healer import heal_unified

# 读取 AB3 文件
with open(r'e:\python\MathProject_AST_Research\skills\jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab3.py', 'r', encoding='utf-8') as f:
    code = f.read()

print("="*80)
print("诊断 Unified Cleanup Healer 对 AB3 的处理")
print("="*80)

# 检测重复类定义
import ast

tree = ast.parse(code)
class_defs = {}

for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        if node.name not in class_defs:
            class_defs[node.name] = []
        class_defs[node.name].append((node.lineno, len(node.body)))

print("\n1. AST 检测到的类定义:")
for class_name, defs in class_defs.items():
    if len(defs) > 1:
        print(f"   ⚠️ 重复类: {class_name}")
        for i, (lineno, body_len) in enumerate(defs):
            print(f"      - 第 {i+1} 个定义: 第 {lineno} 行, 方法数: {body_len}")
    else:
        for i, (lineno, body_len) in enumerate(defs):
            print(f"   ✅ {class_name}: 第 {lineno} 行, 方法数: {body_len}")

print("\n2. 调用 heal_unified():")
fixed_code, fixes = heal_unified(code)

print(f"   修复数: {fixes}")

# 检查修复后是否还有重复
tree_fixed = ast.parse(fixed_code)
class_defs_fixed = {}

for node in ast.walk(tree_fixed):
    if isinstance(node, ast.ClassDef):
        if node.name not in class_defs_fixed:
            class_defs_fixed[node.name] = []
        class_defs_fixed[node.name].append((node.lineno, len(node.body)))

print("\n3. 修复后的类定义:")
for class_name, defs in class_defs_fixed.items():
    if len(defs) > 1:
        print(f"   ❌ 仍然重复: {class_name}")
        for i, (lineno, body_len) in enumerate(defs):
            print(f"      - 第 {i+1} 个定义: 第 {lineno} 行, 方法数: {body_len}")
    else:
        for i, (lineno, body_len) in enumerate(defs):
            print(f"   ✅ {class_name}: 第 {lineno} 行, 方法数: {body_len}")

print("\n" + "="*80)
