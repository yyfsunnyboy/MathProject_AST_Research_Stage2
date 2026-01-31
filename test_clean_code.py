"""
測試：如果代碼本身沒有無限迴圈問題，Healer 會怎麼做？
"""
from core.code_generator import fix_infinite_loop_patterns

# 測試案例：完全正常的代碼（使用推薦的洗牌+切片模式）
clean_code = """
def generate(level=1, **kwargs):
    import random
    
    # 使用推薦的洗牌+切片模式
    max_degree = random.randint(3, 5)
    num_terms = random.randint(3, min(5, max_degree + 1))  # 已經有保護
    
    # 生成可選的 degree 清單
    available_degrees = list(range(max_degree + 1))
    random.shuffle(available_degrees)
    
    # 取前 num_terms 個（安全模式）
    selected_degrees = available_degrees[:num_terms]
    
    # 生成多項式
    terms = []
    for deg in selected_degrees:
        coeff = random.randint(1, 5)
        terms.append((coeff, deg))
    
    return terms
"""

print("="*80)
print("測試：完全正常的代碼（無任何問題）")
print("="*80)

fixed_code, fixes = fix_infinite_loop_patterns(clean_code)

print(f"\n修復次數: {fixes}")

if fixes == 0:
    print("\n✅ 結果：代碼原封不動返回，沒有任何修改")
    print("✅ 這是理想情況！代表 LLM 生成的代碼品質很好")
else:
    print(f"\n⚠️  意外修復了 {fixes} 處")

print("\n" + "="*80)
print("代碼對比")
print("="*80)

if clean_code == fixed_code:
    print("✅ 原始代碼 == 修復後代碼（完全一致）")
else:
    print("❌ 代碼被修改了！")
    print("\n修復後的代碼:")
    print(fixed_code)
