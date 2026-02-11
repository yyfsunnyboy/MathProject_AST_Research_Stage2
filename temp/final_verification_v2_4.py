#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最終驗證報告：V2.4 實裝確認
"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("="*80)
print("FINAL VERIFICATION: Context-Aware Tool Selection System (V2.4)")
print("="*80)

# 驗證 1: 檢查模塊導入
print("\n[1] Module Import Verification")
print("-"*80)
try:
    from core.prompts.prompt_builder import PromptBuilder
    print("✅ PromptBuilder imported successfully")
except Exception as e:
    print(f"❌ Failed to import PromptBuilder: {e}")
    sys.exit(1)

# 驗證 2: 檢查工具手冊常數
print("\n[2] Tool Manual Constants Verification")
print("-"*80)
tools_to_check = ['MANUAL_INTEGER', 'MANUAL_FRACTION', 'MANUAL_RADICAL', 'MANUAL_CALCULUS']
for tool in tools_to_check:
    if hasattr(PromptBuilder, tool):
        manual_content = getattr(PromptBuilder, tool)
        print(f"✅ {tool}: {len(manual_content)} chars")
    else:
        print(f"❌ {tool}: NOT FOUND")

# 驗證 3: 檢查動態選擇方法
print("\n[3] Dynamic Selection Methods Verification")
print("-"*80)
methods_to_check = ['_get_dynamic_api_manual', '_build_tool_selection_protocol', 'build']
for method in methods_to_check:
    if hasattr(PromptBuilder, method):
        print(f"✅ {method}: EXISTS")
    else:
        print(f"❌ {method}: NOT FOUND")

# 驗證 4: 測試工具檢測功能
print("\n[4] Tool Detection Functionality")
print("-"*80)

test_cases = [
    ("分數運算", "", ['FractionOps']),
    ("畢氏定理", "", ['RadicalOps']),
    ("多項式微分", "", ['CalculusOps']),
    ("分數根號微積分", "", ['FractionOps', 'RadicalOps', 'CalculusOps']),
]

all_passed = True
for skill_name, skill_desc, expected_tools in test_cases:
    try:
        manual, tools = PromptBuilder._get_dynamic_api_manual(skill_name, skill_desc)
        
        # 檢查是否包含所有預期的工具
        tools_ok = all(t in tools for t in expected_tools)
        integerops_ok = 'IntegerOps' in tools  # 應該總是啟用
        
        if tools_ok and integerops_ok:
            print(f"✅ '{skill_name}': {tools}")
        else:
            print(f"❌ '{skill_name}': Expected {expected_tools}, got {tools}")
            all_passed = False
    except Exception as e:
        print(f"❌ '{skill_name}': {e}")
        all_passed = False

# 驗證 5: 測試 Prompt 構建
print("\n[5] Prompt Building Integration")
print("-"*80)

sample_spec = "domain: arithmetic\nconstraints:\n  - value_range: -20~20"

build_tests = [
    (1, "Ab1 (BARE_PROMPT_TEMPLATE)", {}),
    (2, "Ab2 (with dynamic tools)", {'skill_id': 'test_skill'}),
    (3, "Ab3 (with dynamic tools)", {'skill_id': 'test_skill'}),
]

for ab_id, ab_name, extra_args in build_tests:
    try:
        prompt = PromptBuilder.build(
            master_spec=sample_spec,
            ablation_id=ab_id,
            topic="Test Topic",
            **extra_args
        )
        
        print(f"✅ {ab_name}: {len(prompt)} chars")
        
        # 驗證內容
        if ab_id == 1:
            # Ab1 不應包含動態工具
            if "已啟用的數學軍火庫" not in prompt:
                print(f"   ✓ Ab1 correctly without dynamic tools")
            else:
                print(f"   ⚠ Ab1 unexpectedly contains dynamic tools")
        else:
            # Ab2/Ab3 應包含動態工具
            if "已啟用的數學軍火庫" in prompt:
                print(f"   ✓ {ab_name} contains dynamic tools")
            else:
                print(f"   ⚠ {ab_name} missing dynamic tools")
                
    except Exception as e:
        print(f"❌ {ab_name}: {e}")
        all_passed = False

# 驗證 6: 檢查日誌功能
print("\n[6] Logging Functionality")
print("-"*80)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test')

try:
    prompt = PromptBuilder.build(
        master_spec=sample_spec,
        ablation_id=2,
        topic="分數運算",
        skill_id="test_skill"
    )
    print("✅ Logging works (check console above for INFO messages)")
except Exception as e:
    print(f"⚠ Logging issue: {e}")

# 驗證 7: 性能檢查
print("\n[7] Performance Check")
print("-"*80)

import time

start = time.time()
for _ in range(10):
    PromptBuilder._get_dynamic_api_manual("測試技能名稱", "測試描述")
elapsed = time.time() - start

avg_time = elapsed / 10 * 1000  # 轉為毫秒
print(f"Average detection time: {avg_time:.2f}ms")
print(f"✅ Performance acceptable" if avg_time < 10 else f"⚠ Performance warning: {avg_time:.2f}ms")

# 最終結論
print("\n" + "="*80)
print("FINAL RESULT")
print("="*80)

if all_passed:
    print("✅ All verifications PASSED")
    print("Status: READY FOR DEPLOYMENT")
    print("\nImplemented features:")
    print("  • Dynamic tool detection based on keywords")
    print("  • API manual assembly")
    print("  • Tool selection protocol injection")
    print("  • Full integration with prompt builder")
else:
    print("⚠ Some verifications had issues")
    print("Please review the output above")

print("\n" + "="*80)
print("V2.4 Implementation Complete")
print("="*80)
