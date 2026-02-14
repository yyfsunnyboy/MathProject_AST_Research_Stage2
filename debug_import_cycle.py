
import sys
import os
import re

# 模擬環境設置
sys.path.append(os.getcwd())
from core.healers.regex_healer import RegexHealer

def test_healer_logic():
    healer = RegexHealer()
    
    print("="*50)
    print("🧪 RegexHealer Import/Remove Logic Simulation")
    print("="*50)

    # ---------------------------------------------------------
    # Scenario 1: Ab2/Ab3 正常情況 (Scaffolding 已注入)
    # AI 錯誤地 import 了 domain_function_library
    # ---------------------------------------------------------
    code_with_scaffold = """
class IntegerOps:
    pass

from domain_function_library import IntegerOps
from domain_function_library import fmt_num

def generate():
    op = IntegerOps()
    print(fmt_num(5))
"""
    print("\n[Scenario 1] Scaffolding Exists + AI adds Redundant Import")
    print("-" * 40)
    
    # Run inject_domain_imports (Step 1)
    # 預期：因為 IntegerOps 已定義 (class IntegerOps)，應該跳過注入
    added_code, count = healer.inject_domain_imports(code_with_scaffold)
    print(f"Step 1 (Inject): Added {count} imports")
    if count > 0:
        print("❌ FAILED: Should NOT inject imports when class is defined locally!")
    else:
        print("✅ PASSED: Correctly skipped injection due to local definition.")

    # Run remove_invalid_dependencies (Step 1.5)
    # 預期：移除 from domain_function_library...
    cleaned_code, removed_count = healer.remove_invalid_dependencies(added_code)
    print(f"Step 1.5 (Remove): Removed {removed_count} lines")
    
    if "from domain_function_library" not in cleaned_code:
        print("✅ PASSED: Successfully removed invalid imports.")
    else:
        print("❌ FAILED: Invalid imports still present!")
        print(cleaned_code)

    # ---------------------------------------------------------
    # Scenario 2: Ab3 依賴遺漏 (Missing Import)
    # AI 用到了 FractionOps 但沒 import，也沒 Scaffolding (假設某種極端情況)
    # ---------------------------------------------------------
    code_missing = """
def generate():
    f = FractionOps.add(1, 2)
"""
    print("\n[Scenario 2] Missing Import & No Scaffolding (Bad Case)")
    print("-" * 40)
    
    # Run inject_domain_imports
    # 預期：注入 from domain_function_library import FractionOps
    added_code_2, count_2 = healer.inject_domain_imports(code_missing)
    print(f"Step 1 (Inject): Added {count_2} imports")
    
    if "from domain_function_library import FractionOps" in added_code_2:
        print("✅ PASSED: Correctly injected missing import.")
    else:
        print("❌ FAILED: Did not inject missing import.")

    # Run remove_invalid_dependencies
    # 預期：剛剛注入的 import 會被刪除
    # 這展示了 "衝突"：如果沒有 Scaffolding，Healer 會先加後刪，導致代碼壞掉。
    # 但這是 "Correct Behavior" for our system，因為我們 *必須* 有 Scaffolding。
    cleaned_code_2, removed_count_2 = healer.remove_invalid_dependencies(added_code_2)
    print(f"Step 1.5 (Remove): Removed {removed_count_2} lines")
    
    if "from domain_function_library" not in cleaned_code_2:
        print("⚠️ NOTE: It removed the injected import (System Design Choice: We rely onScaffolding)")
    
    # ---------------------------------------------------------
    # Scenario 3: Ab1 (Bare) Simulation
    # ---------------------------------------------------------
    # Ab1 不應該調用 Healer，但我們測試如果是 Ab2 純環境
    print("\n[Scenario 3] Ab2 Minimal Mode (run heal_minimal)")
    print("-" * 40)
    
    ab2_code = """
import random
from domain_function_library import IntegerOps

# Scaffolding injected locally
class IntegerOps:
    pass

x = IntegerOps.add(1, 2)
"""
    final_code, stats = healer.heal_minimal(ab2_code)
    print(f"Heal Minimal Result Stats: {stats}")
    
    if "from domain_function_library" not in final_code:
        print("✅ PASSED: Ab2 correctly removed invalid import.")
    else:
        print(f"❌ FAILED: Ab2 kept invalid import.\n{final_code}")

if __name__ == "__main__":
    test_healer_logic()
