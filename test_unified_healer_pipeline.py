# -*- coding: utf-8 -*-
"""
模擬統一 Healer 在代碼生成管道中的表現
不依賴完整的 Flask/DB 初始化
"""

import sys
sys.path.insert(0, r'e:\python\MathProject_AST_Research')

from core.healers.unified_cleanup_healer import heal_unified
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# 模擬 Regex Healer 後的代碼（第二階段輸出）
simulated_regex_healed_code = '''
def generate_question_and_answer():
    """生成四則運算題目"""
    
    # ======= 污染開始 =======
    # 這些是 AI 生成時的污染（應該被統一 Healer 刪除）
    IntegerOps = 0
    fmt_num = 0
    clean_latex_output = None
    to_latex = None
    
    # ======= 污染結束 =======
    
    # 真實邏輯開始
    class InnerClass:
        def method1(self):
            pass
    
    # 重複定義（應該被刪除）
    class InnerClass:  # 這是重複定義
        def method2(self):
            pass
    
    # 正常函數定義
    def helper_func():
        return IntegerOps.random_nonzero(-50, 50)
    
    # 重複定義的函數（應該被刪除）
    def helper_func():  # 這是重複定義
        return IntegerOps.random_nonzero(1, 10)
    
    # 實際計算
    n1 = IntegerOps.random_nonzero(-50, 50)
    n2 = IntegerOps.random_nonzero(-50, 50)
    
    # 題目
    problem = f"{n1} + {n2}"
    
    # 答案
    answer = n1 + n2
    
    return {
        'problem': problem,
        'problem_latex': to_latex(problem),
        'answer': answer,
        'answer_formatted': fmt_num(answer)
    }
'''

print("=" * 70)
print("TEST: 統一 Healer 在代碼生成流程中的表現")
print("=" * 70)

print("\n【輸入代碼統計】")
print(f"   行數: {len(simulated_regex_healed_code.splitlines())}")
print(f"   污染賦值 (IntegerOps = 0): {'✓ 存在' if 'IntegerOps = 0' in simulated_regex_healed_code else '✗ 不存在'}")
print(f"   污染賦值 (fmt_num = 0): {'✓ 存在' if 'fmt_num = 0' in simulated_regex_healed_code else '✗ 不存在'}")
print(f"   污染賦值 (clean_latex_output = None): {'✓ 存在' if 'clean_latex_output = None' in simulated_regex_healed_code else '✗ 不存在'}")

print("\n【執行統一 Healer】")
print("-" * 70)

# 執行修復
fixed_code, total_fixes = heal_unified(simulated_regex_healed_code)

print("-" * 70)

print("\n【修復結果】")
print(f"   總修復數量: {total_fixes}")

print("\n【輸出代碼驗證】")

pollution_items = {
    'IntegerOps = 0': '污染: IntegerOps 被覆蓋',
    'fmt_num = 0': '污染: fmt_num 被覆蓋',
    'clean_latex_output = None': '污染: clean_latex_output 被覆蓋',
    'to_latex = None': '污染: to_latex 被覆蓋',
}

pollution_found = False
for pattern, desc in pollution_items.items():
    if pattern in fixed_code:
        print(f"   ❌ 仍然存在: {desc}")
        pollution_found = True
    else:
        print(f"   ✅ 已移除: {desc}")

# 檢查重複定義
class_count = fixed_code.count('class InnerClass:')
func_count = fixed_code.count('def helper_func():')

print(f"\n   {'✅' if class_count == 1 else '❌'} 重複 class 檢查: {class_count} 個 InnerClass (預期: 1)")
print(f"   {'✅' if func_count == 1 else '❌'} 重複 func 檢查: {func_count} 個 helper_func (預期: 1)")

# 檢查語法
print("\n【語法檢查】")
try:
    import ast
    ast.parse(fixed_code)
    print("   ✅ 語法有效")
except SyntaxError as e:
    print(f"   ❌ 語法錯誤: {e}")

# 顯示修復後的代碼片段
print("\n【修復後代碼片段】")
print("-" * 70)
lines = fixed_code.splitlines()
for i, line in enumerate(lines[:40], 1):
    print(f"{i:3d}: {line}")

print("\n" + "=" * 70)
if not pollution_found and class_count == 1 and func_count == 1:
    print("✅ 所有測試通過！統一 Healer 工作正常")
else:
    print("❌ 部分測試失敗")
print("=" * 70)
