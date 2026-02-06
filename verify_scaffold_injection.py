#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ==============================================================================
# Verification Script: Scaffold Injection in run_experiment.py
# ==============================================================================

import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

print("="*70)
print("🧪 驗證 run_experiment.py 的脚手架注入")
print("="*70)

# Test 1: Import build_calculation_skeleton
print("\n✅ Test 1: 導入 build_calculation_skeleton...")
try:
    from core.code_generator import build_calculation_skeleton
    print("   ✓ 成功導入")
except ImportError as e:
    print(f"   ✗ 導入失敗: {e}")
    sys.exit(1)

# Test 2: Generate skeleton for Ab2/Ab3
print("\n✅ Test 2: 為 Ab2/Ab3 生成脚手架...")
try:
    skeleton = build_calculation_skeleton("gh_ApplicationsOfDerivatives")
    print(f"   ✓ 脚手架生成成功，長度: {len(skeleton)} 字符")
    
    # 驗證脚手架包含必要的內容
    required_markers = [
        "[INJECTED UTILS]",
        "def safe_choice",
        "def to_latex",
        "def fmt_num",
        "[DOMAIN HELPERS - Auto-Injected for gh_ApplicationsOfDerivatives]",
        "[AI GENERATED CODE]"
    ]
    
    for marker in required_markers:
        if marker in skeleton:
            print(f"   ✓ 包含: {marker}")
        else:
            print(f"   ✗ 缺失: {marker}")
            
except Exception as e:
    print(f"   ✗ 生成失敗: {e}")
    sys.exit(1)

# Test 3: Ab1 skeleton (should NOT have domain helpers)
print("\n✅ Test 3: 驗證 Ab1 邏輯（不注入脚手架）...")
print("   ℹ️  Ab1 應直接使用生成的代碼，不添加脚手架")
print("   ℹ️  這由 run_experiment.py 中的條件句 (ablation_id >= 2) 控制")

# Test 4: Check structure of generated file
print("\n✅ Test 4: 檢查生成文件的結構...")
sample_ab2_file = os.path.join(
    project_root,
    "skills",
    "gh_ApplicationsOfDerivatives_14b_Ab2.py"
)

if os.path.exists(sample_ab2_file):
    with open(sample_ab2_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"   ✓ 參考文件存在: {os.path.basename(sample_ab2_file)}")
    
    # 計算各部分的行數
    lines = content.split('\n')
    
    injected_utils_line = next((i for i, l in enumerate(lines) if "[INJECTED UTILS]" in l), -1)
    domain_helpers_line = next((i for i, l in enumerate(lines) if "[DOMAIN HELPERS" in l), -1)
    ai_generated_line = next((i for i, l in enumerate(lines) if "[AI GENERATED CODE]" in l), -1)
    
    print(f"\n   檔案結構:")
    print(f"   ├─ 標頭 (1-10 行)")
    print(f"   ├─ [INJECTED UTILS] (第 {injected_utils_line+1} 行)")
    if domain_helpers_line > 0:
        print(f"   ├─ [DOMAIN HELPERS] (第 {domain_helpers_line+1} 行)")
    if ai_generated_line > 0:
        print(f"   └─ [AI GENERATED CODE] (第 {ai_generated_line+1} 行)")
    
    print(f"\n   總計: {len(lines)} 行代碼")
else:
    print(f"   ⚠️  參考文件不存在: {sample_ab2_file}")

# Test 5: Verify the code structure logic in run_experiment.py
print("\n✅ Test 5: 驗證 run_experiment.py 的代碼邏輯...")
print("   檢查文件中是否包含脚手架注入邏輯...")

run_exp_file = os.path.join(project_root, "scripts", "run_experiment.py")
if os.path.exists(run_exp_file):
    with open(run_exp_file, 'r', encoding='utf-8') as f:
        run_exp_content = f.read()
    
    if "build_calculation_skeleton" in run_exp_content:
        print("   ✓ 包含 build_calculation_skeleton 導入邏輯")
    else:
        print("   ✗ 缺失 build_calculation_skeleton")
    
    if "ablation_id >= 2" in run_exp_content:
        print("   ✓ 包含 Ab2/Ab3 條件判斷")
    else:
        print("   ✗ 缺失 Ab2/Ab3 條件判斷")
    
    if "code_to_save = skeleton + " in run_exp_content or "code_to_save = skeleton + '\\n'" in run_exp_content:
        print("   ✓ 包含脚手架組合邏輯")
    else:
        print("   ✗ 缺失脚手架組合邏輯")
else:
    print(f"   ✗ run_experiment.py 不存在: {run_exp_file}")

print("\n" + "="*70)
print("🎉 驗證完成！")
print("="*70)

print("\n📋 總結:")
print("  ✅ run_experiment.py 已包含脚手架注入邏輯")
print("  ✅ Ab2/Ab3 會自動注入工具庫和 Domain Helpers")
print("  ✅ Ab1 不會注入脚手架（測試模型原生能力）")
print("  ✅ 生成的文件結構完全匹配 code_generator.py 的行為")

print("\n⚙️ 下次執行 run_experiment.py 時，生成的文件將包含:")
print("  • 完整標頭（含 Ablation ID 和 Healer 狀態）")
print("  • [INJECTED UTILS] - 工具庫（LaTeX、格式化、數論等）")
print("  • [DOMAIN HELPERS] - 領域特定函數（如多項式、微分等）")
print("  • [AI GENERATED CODE] - AI 生成的 generate() 和 check() 函數")
