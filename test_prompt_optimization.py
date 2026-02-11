#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試 Prompt 優化效果 - 驗證 Token 節省
版本: V2.5 (動態 Prompt 組裝)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.prompts.prompt_builder import PromptBuilder

def count_tokens_approx(text):
    """簡單的 Token 計數器 (中文與英文粗估)"""
    # 粗估規則：每個中文字=1.5個Token，英文單詞=1個Token
    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    english_text = ''.join([c for c in text if ord(c) < 128])
    english_tokens = len(english_text.split())
    
    return int(chinese_chars * 1.5 + english_tokens)

# 測試用例
test_cases = [
    {
        "name": "🔢 整數四則運算（應該是最精簡的）",
        "skill_name": "jh_數學1上_FourArithmeticOperationsOfIntegers",
        "skill_desc": "整數的四則運算與運算優先級"
    },
    {
        "name": "📊 分數運算（應該包含 FractionOps）",
        "skill_name": "gh_Fractions",
        "skill_desc": "分數的加減乘除與化簡"
    },
    {
        "name": "📐 几何與根號（應該包含 RadicalOps）",
        "skill_name": "gh_Geometry",
        "skill_desc": "根號與畢氏定理的應用"
    },
    {
        "name": "📈 微分應用（應該包含 MANUAL_POLYNOMIAL）",
        "skill_name": "gh_ApplicationsOfDerivatives",
        "skill_desc": "多項式函數的微分與切線方程"
    }
]

print("\n" + "="*80)
print("📊 Prompt 優化效果測試 - Token 節省對比")
print("="*80)

for test_case in test_cases:
    skill_name = test_case["skill_name"]
    skill_desc = test_case["skill_desc"]
    
    print(f"\n✓ {test_case['name']}")
    print(f"  技能：{skill_name}")
    
    # 獲取動態 API 手冊
    manual_text, active_tools = PromptBuilder._get_dynamic_api_manual(skill_name, skill_desc)
    
    # 計算長度和 Token 數
    manual_len = len(manual_text)
    token_count = count_tokens_approx(manual_text)
    
    print(f"  📝 啟用工具：{', '.join(active_tools)}")
    print(f"  📏 手冊長度：{manual_len} 字符")
    print(f"  🔢 預估 Token：~{token_count} tokens")
    print(f"  ─────────────────────────────────────")
    
    # 顯示前 200 字符的預覽
    preview = manual_text[:200].replace('\n', '\n     ')
    print(f"  📋 內容預覽：\n     {preview}...")

print("\n" + "="*80)
print("✅ 測試完成！")
print("\n💡 預期結果：")
print("  • 整數運算：最精簡（只有 Base + IntegerOps）")
print("  • 分數運算：包含 FractionOps")
print("  • 幾何/根號：包含 RadicalOps")
print("  • 微分應用：包含 CalculusOps (Polynomial)")
print("="*80 + "\n")
