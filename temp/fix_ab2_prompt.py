#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
在Ab2 prompt文件中添加参考例题部分
"""
import os

filepath = r'e:\python\MathProject_AST_Research\experiments\golden_prompts\temp\jh_數學1上_FourArithmeticOperationsOfNumbers_Ab2.txt'

# 读取原文件
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 查找MASTER_SPEC位置
master_spec_marker = '### MASTER_SPEC:'
master_spec_pos = content.find(master_spec_marker)

if master_spec_pos == -1:
    print("❌ 未找到 MASTER_SPEC 标记")
    exit(1)

print(f"✅ 找到 MASTER_SPEC 在位置: {master_spec_pos}")

# 检查是否已有参考例题
if '【參考例題】' in content[:master_spec_pos]:
    print("⚠️  已存在【參考例題】部分，跳过添加")
    exit(0)

# 构建参考例题部分
textbook_example_section = """【參考例題】
以下是該技能的課本真題範例（用於理解題型特徵）：
範例：計算 3/2÷(-0.6 )×(-3/5 )-1/2⑵ 3 9/11×(-57 )-1 9/11×(-57 )

"""

# 在MASTER_SPEC前插入
new_content = content[:master_spec_pos] + textbook_example_section + content[master_spec_pos:]

# 保存修改后的文件
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ 成功添加參考例題部分")
print(f"✅ 文件已保存")

# 验证
with open(filepath, 'r', encoding='utf-8') as f:
    verify_content = f.read()
    
if '【參考例題】' in verify_content:
    print("✅ 验证成功：參考例題已添加到文件中")
else:
    print("❌ 验证失败：無法找到新添加的內容")
