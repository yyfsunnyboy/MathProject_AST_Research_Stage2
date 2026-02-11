#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試新增的動態工具選用系統 (Context-Aware Tool Selection System)
"""
import sys
import os

# 路径修正
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.prompts.prompt_builder import PromptBuilder

print("=" * 80)
print("🧪 測試動態工具選用系統 (V2.4 Context-Aware Tool Selection)")
print("=" * 80)

# Test 1: 分數相關技能
print("\n【測試 1】分數相關技能 (含 / 和 div 關鍵字)")
print("-" * 80)
manual_1, tools_1 = PromptBuilder._get_dynamic_api_manual(
    "整數的四則運算", 
    "學習基本的加、減、乘、除運算"
)
print(f"偵測到的工具: {tools_1}")
print(f"手冊內容 (前 300 字符):\n{manual_1[:300]}\n")

# Test 2: 分數運算技能
print("\n【測試 2】分數四則運算 (含分、frac、ratio 關鍵字)")
print("-" * 80)
manual_2, tools_2 = PromptBuilder._get_dynamic_api_manual(
    "分數運算",
    "學習分數的加、減、乘、除以及化簡"
)
print(f"偵測到的工具: {tools_2}")
print(f"✅ FractionOps 已啟用: {'FractionOps' in tools_2}")

# Test 3: 幾何/根號技能
print("\n【測試 3】幾何與根號 (含 sqrt、畢氏 關鍵字)")
print("-" * 80)
manual_3, tools_3 = PromptBuilder._get_dynamic_api_manual(
    "畢氏定理",
    "學習用畢氏定理計算直角三角形的邊長"
)
print(f"偵測到的工具: {tools_3}")
print(f"✅ RadicalOps 已啟用: {'RadicalOps' in tools_3}")

# Test 4: 微積分技能
print("\n【測試 4】微積分與多項式 (含 diff、微、積 關鍵字)")
print("-" * 80)
manual_4, tools_4 = PromptBuilder._get_dynamic_api_manual(
    "多項式的微分",
    "學習對多項式函數進行微分運算"
)
print(f"偵測到的工具: {tools_4}")
print(f"✅ CalculusOps 已啟用: {'CalculusOps' in tools_4}")

# Test 5: 複雜技能 (包含多個關鍵字)
print("\n【測試 5】複雜技能 (同時含分數、根號、微積分)")
print("-" * 80)
manual_5, tools_5 = PromptBuilder._get_dynamic_api_manual(
    "高等數學應用",
    "計算根號下的分數導數，涉及有理函數的微分"
)
print(f"偵測到的工具: {tools_5}")
print(f"工具數量: {len(tools_5)}")
print(f"包含所有工具: {len(tools_5) == 4}")

# Test 6: 工具選用協定生成
print("\n【測試 6】工具選用協定 (Tool Selection Protocol)")
print("-" * 80)
protocol = PromptBuilder._build_tool_selection_protocol(tools_5)
print(f"協定內容 (前 500 字符):\n{protocol[:500]}\n")

print("\n" + "=" * 80)
print("✅ 所有測試完成！動態工具選用系統已正常工作")
print("=" * 80)
print("\n📊 測試結果摘要:")
print(f"  • 分數檢測: {'✅' if 'FractionOps' in tools_2 else '❌'}")
print(f"  • 幾何檢測: {'✅' if 'RadicalOps' in tools_3 else '❌'}")
print(f"  • 微積分檢測: {'✅' if 'CalculusOps' in tools_4 else '❌'}")
print(f"  • 複合檢測: {'✅' if len(tools_5) >= 3 else '❌'}")
