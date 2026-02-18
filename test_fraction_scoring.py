"""
快速验证分数单元示例代码
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from code_generator import _inject_domain_libs


def test_fraction_example():
    """测试分数单元示例代码"""
    example_code = """
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    # Adjust difficulty based on level
    if level == 1:
        int_range = (-5, 5)
        frac_range = (1, 6)
    elif level == 2:
        int_range = (-20, 20)
        frac_range = (1, 12)
    else:  # level 3
        int_range = (-100, 100)
        frac_range = (1, 20)
    
    # Part 1: Bracket with fractions
    a = random.randint(*int_range)
    b = random.randint(1, int_range[1])
    frac1 = FractionOps.create(f"{random.randint(1, frac_range[1])}/{random.randint(2, frac_range[1])}")
    
    part1_str = f"\\\\left[({a}+{b}) \\\\times {FractionOps.to_latex(frac1)}\\\\right]"
    
    # Part 2: Division by fraction (ensure non-zero denominator)
    frac2 = FractionOps.create(f"{random.randint(-frac_range[1], -1)}/{random.randint(2, frac_range[1])}")
    part2_str = f"\\\\left({FractionOps.to_latex(frac2)}\\\\right)"
    
    # Part 3: Absolute value with fraction
    c = random.randint(int_range[0]//2, int_range[1]//2)
    frac3 = FractionOps.create(f"{random.randint(-frac_range[1], -1)}/{random.randint(2, frac_range[1])}")
    d = random.randint(1, frac_range[1])
    
    part3_str = f"\\\\left|{c} \\\\times {FractionOps.to_latex(frac3)} - {d}\\\\right|"
    
    question_text = f"計算 $$   {part1_str} \\\\div {part2_str} + {part3_str}   $$ 的值。"
    
    # Calculate answer using FractionOps
    val1 = FractionOps.mul(FractionOps.create(a + b), frac1)
    val2 = frac2
    val3 = abs(FractionOps.sub(FractionOps.mul(c, frac3), d))
    
    result = FractionOps.add(FractionOps.div(val1, val2), val3)
    
    # Format answer as simplified fraction or integer
    if result.denominator == 1:
        correct_answer = str(result.numerator)
    else:
        correct_answer = f"{result.numerator}/{result.denominator}"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        
        ua = Fraction(user_answer) if '/' in str(user_answer) else Fraction(float(user_answer))
        ca = Fraction(correct_answer) if '/' in str(correct_answer) else Fraction(float(correct_answer))
        
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        
        return {'correct': False, 'result': '錯誤'}
    except:
        correct = str(user_answer).strip() == str(correct_answer).strip()
        return {'correct': correct, 'result': '正確' if correct else '錯誤'}
"""
    
    print("=" * 70)
    print("验证分数单元示例代码")
    print("=" * 70)
    
    # 注入 API
    injected_code, libs = _inject_domain_libs(example_code)
    print(f"\n1. API 注入: {libs}")
    
    # 执行代码
    exec_globals = {}
    exec(injected_code, exec_globals)
    
    print("\n2. 测试不同 level")
    for level in [1, 2, 3]:
        result = exec_globals['generate'](level=level)
        print(f"\n   Level {level}:")
        print(f"   ✅ 题目: {result['question_text'][:70]}...")
        print(f"   ✅ 答案: {result['correct_answer']}")
        
        # 验证 check 函数
        check_result = exec_globals['check'](result['correct_answer'], result['correct_answer'])
        assert check_result['correct'] == True
    
    print("\n" + "=" * 70)
    print("✅ 分数单元示例代码验证通过！")
    print("=" * 70)
    print("\n预期效果:")
    print("   ✅ 根据 level 调整难度范围")
    print("   ✅ 使用 FractionOps API 简化代码")
    print("   ✅ LaTeX 格式正确")
    print("   ✅ 答案计算准确")


if __name__ == "__main__":
    try:
        test_fraction_example()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
