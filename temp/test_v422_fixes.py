#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速驗證 V4.2.2 四個優先級修復
==============================

驗證項目：
1. 優先級1: ALLOWED_IMPORTS 是否包含 re/ast/operator/os/typing
2. 優先級1: FORBIDDEN_BUILTINS 是否只有 eval/exec
3. 優先級2: L3.2 測試是否正確 replace 空白
4. 優先級3: exec_time 是否被記錄
5. 優先級4: L4.2 是否檢查 ^{} 和 $ 成對
"""

import sys
import re
from pathlib import Path

# 設置路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'scripts'))

# 讀取評估腳本內容
eval_script_path = project_root / 'scripts' / 'evaluate_mcri.py'

with open(eval_script_path, 'r', encoding='utf-8') as f:
    code = f.read()

print("="*80)
print("🧪 V4.2.2 修復驗證")
print("="*80)

# ========================================
# 優先級1: 白名單調整
# ========================================
print("\n📋 優先級1: L1 白名單調整")
print("-" * 80)

# 檢查 ALLOWED_IMPORTS
allowed_match = re.search(r"ALLOWED_IMPORTS\s*=\s*{([^}]+)}", code)
if allowed_match:
    allowed_str = allowed_match.group(1)
    required = ['re', 'ast', 'operator', 'os', 'typing']
    
    print(f"✓ 找到 ALLOWED_IMPORTS 定義")
    print(f"  內容: {allowed_str.strip()}")
    
    all_present = all(f"'{item}'" in allowed_str or f'"{item}"' in allowed_str for item in required)
    if all_present:
        print(f"✅ 白名單包含所有必要項目: {required}")
    else:
        missing = [item for item in required if f"'{item}'" not in allowed_str and f'"{item}"' not in allowed_str]
        print(f"❌ 缺少項目: {missing}")
else:
    print("❌ 找不到 ALLOWED_IMPORTS 定義")

# 檢查 FORBIDDEN_BUILTINS
forbidden_match = re.search(r"FORBIDDEN_BUILTINS\s*=\s*{([^}]+)}", code)
if forbidden_match:
    forbidden_str = forbidden_match.group(1)
    print(f"\n✓ 找到 FORBIDDEN_BUILTINS 定義")
    print(f"  內容: {forbidden_str.strip()}")
    
    # 應該只有 'eval', 'exec'，不應有 'compile', '__import__'
    has_compile = 'compile' in forbidden_str
    has_import = '__import__' in forbidden_str
    
    if not has_compile and not has_import:
        print(f"✅ 已移除誤判項目 (compile, __import__)")
    else:
        issues = []
        if has_compile:
            issues.append('compile')
        if has_import:
            issues.append('__import__')
        print(f"⚠️  仍包含誤判項目: {issues}")
else:
    print("❌ 找不到 FORBIDDEN_BUILTINS 定義")

# ========================================
# 優先級2: L3.2 測試嚴格度
# ========================================
print("\n📋 優先級2: L3.2 測試嚴格化")
print("-" * 80)

# 在 evaluate_external_robustness 中尋找 replace(" ", "")
if 'student_normalized = str(student_input).replace(" ", "")' in code:
    print("✅ L3.2 測試中加入了空白符號移除")
    print("   student_normalized = str(student_input).replace(\" \", \"\")")
    print("   answer_normalized = str(correct_ans).replace(\" \", \"\")")
else:
    print("❌ L3.2 測試中未找到空白符號移除邏輯")

# ========================================
# 優先級3: 記錄 exec_time
# ========================================
print("\n📋 優先級3: 記錄 avg_exec_time")
print("-" * 80)

# 檢查是否記錄 exec_time
if "exec_time = time.time() - start_time" in code:
    print("✅ 在 evaluate_single_repetition 中記錄了 exec_time")
    
    if "item['exec_time'] = round(exec_time, 4)" in code:
        print("✅ exec_time 被儲存到 item 字典")
    else:
        print("⚠️  exec_time 未儲存到 item 字典")
    
    if "exec_times_from_reps = [item.get('exec_time', 0.0) for item in pass_items" in code:
        print("✅ avg_exec_time 從 repetitions 計算")
    else:
        print("⚠️  avg_exec_time 未從 repetitions 計算")
else:
    print("❌ 未找到 exec_time 記錄邏輯")

# ========================================
# 優先級4: L4.2 視覺可讀加強
# ========================================
print("\n📋 優先級4: L4.2 視覺可讀性加強")
print("-" * 80)

# 檢查 ^{} 檢查
if r'\^[^{]' in code or r'\\^[^{]' in code:
    print("✅ 加入了指數未加大括號檢查 (^{} vs ^2)")
else:
    print("❌ 未找到指數大括號檢查")

# 檢查 $ 成對
if "dollar_count = question.count('$')" in code and "dollar_count % 2 != 0" in code:
    print("✅ 加入了數學模式符號成對檢查")
else:
    print("❌ 未找到 $ 成對檢查")

# ========================================
# 版本號確認
# ========================================
print("\n📋 版本號確認")
print("-" * 80)

version_match = re.search(r'MCRI_VERSION\s*=\s*["\']([^"\']+)["\']', code)
if version_match:
    version = version_match.group(1)
    print(f"當前版本: {version}")
    
    if version == "4.2.2":
        print("✅ 版本號已更新至 4.2.2")
    else:
        print(f"⚠️  版本號為 {version}，期望 4.2.2")
else:
    print("❌ 找不到版本號定義")

# ========================================
# 總結
# ========================================
print("\n" + "="*80)
print("📊 驗證總結")
print("="*80)

checks = {
    "優先級1 - 白名單擴充": 're' in code and 'ast' in code,
    "優先級1 - 移除誤判": 'compile' not in forbidden_str if forbidden_match else False,
    "優先級2 - L3.2 嚴格化": 'student_normalized' in code,
    "優先級3 - exec_time 記錄": "exec_time = time.time() - start_time" in code,
    "優先級4 - ^{} 檢查": r'\^[^{]' in code,
    "優先級4 - $ 成對檢查": "dollar_count % 2 != 0" in code,
    "版本號更新": version == "4.2.2" if version_match else False
}

passed = sum(1 for v in checks.values() if v)
total = len(checks)

print(f"\n通過: {passed}/{total}")
for name, result in checks.items():
    status = "✅" if result else "❌"
    print(f"  {status} {name}")

if passed == total:
    print("\n🎉 所有檢查通過！可以重新執行評估了。")
else:
    print(f"\n⚠️  還有 {total - passed} 項檢查未通過，請檢查程式碼。")

print("\n建議下一步：")
print("  1. 刪除舊資料庫: del reports\\mcri_evaluation.db")
print("  2. 執行評估: python scripts\\evaluate_mcri.py")
print("  3. 檢查 Ab1 的 L4.2 分數是否下降")
print("  4. 檢查 Ab3 的 L3.2 分數是否達到 15")
