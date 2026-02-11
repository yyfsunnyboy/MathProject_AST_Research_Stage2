#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终验证报告：FourArithmeticOperationsOfNumbers Golden Prompts 已包含课本例题
"""

print("=" * 70)
print("最终验证报告: FourArithmeticOperationsOfNumbers Golden Prompts")
print("=" * 70)

base_dir = r'e:\python\MathProject_AST_Research\experiments\golden_prompts\temp'
ab1_file = base_dir + r'\jh_數學1上_FourArithmeticOperationsOfNumbers_Ab1.txt'
ab2_file = base_dir + r'\jh_數學1上_FourArithmeticOperationsOfNumbers_Ab2.txt'

def verify_file(filepath, ablation_type):
    print(f"\n✅ {ablation_type} 文件验证:")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本检查
        print(f"   • 文件存在: True")
        print(f"   • 文件大小: {len(content)} 字符")
        
        # 检查关键部分
        has_example = '【參考例題】' in content
        has_master_spec = '### MASTER_SPEC:' in content if ablation_type == "Ab2" else "BARE_PROMPT_TEMPLATE" in content or "參考例題" in content
        
        print(f"   • 包含【參考例題】: {has_example}")
        if ablation_type == "Ab2":
            print(f"   • 包含 MASTER_SPEC: {has_master_spec}")
        
        # 显示例题内容
        if has_example:
            example_start = content.find('【參考例題】')
            example_end = content.find('\n', content.find('範例：') + 50)
            if example_end == -1:
                example_end = example_start + 200
            example_text = content[example_start:example_end]
            print(f"\n   --> 課本例題內容:")
            for line in example_text.split('\n')[:3]:
                if line.strip():
                    print(f"       {line[:60]}")
        
        return has_example and has_master_spec
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False

# 验证两个文件
ab1_ok = verify_file(ab1_file, "Ab1")
ab2_ok = verify_file(ab2_file, "Ab2")

print("\n" + "=" * 70)
print("验证结果汇总:")
print("=" * 70)
print(f"• Ab1 (BARE_MINIMAL_PROMPT): {'✅ PASS' if ab1_ok else '❌ FAIL'}")
print(f"• Ab2 (UNIVERSAL_GEN_CODE_PROMPT): {'✅ PASS' if ab2_ok else '❌ FAIL'}")

if ab1_ok and ab2_ok:
    print("\n✅ 所有验证通过！課本例題已成功添加到 Golden Prompts 中。")
else:
    print("\n❌ 某些验证失败，请检查文件内容。")

print("=" * 70)
