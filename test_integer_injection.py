"""
测试整数单元的 IntegerOps API 注入
模拟 AI 根据 SKILL.md 生成的代码，验证注入机制是否正常工作
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from code_generator import _inject_domain_libs


def test_integer_skill_injection():
    """测试符合整数 SKILL.md 风格的代码注入"""
    print("=" * 70)
    print("测试整数单元 IntegerOps API 注入（模拟 SKILL.md 示例）")
    print("=" * 70)
    
    # 模拟 AI 根据 SKILL.md 生成的代码
    ai_generated_code = """
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    # Part 1: Bracket expression with division (ensure divisible)
    divisor = random.choice([2, 3, 4, 5])
    quotient = IntegerOps.random_nonzero(-10, 10)
    dividend = divisor * quotient  # Ensure divisible!
    
    a = IntegerOps.random_nonzero(-20, 20)
    b = IntegerOps.random_nonzero(-20, 20)
    
    # Use IntegerOps.fmt_num() to format negative numbers
    part1_str = f"[{IntegerOps.fmt_num(a)} + {IntegerOps.fmt_num(b)}] \\\\div {IntegerOps.fmt_num(divisor)} \\\\times {quotient}"
    
    # Part 2: Absolute value expression
    c = IntegerOps.random_nonzero(-10, 10)
    d = IntegerOps.random_nonzero(-10, 10)
    e = random.randint(1, 10)
    
    part2_str = f"\\\\left|{c} \\\\times {IntegerOps.fmt_num(d)} - {e}\\\\right|"
    
    question_text = f"計算 $$   {part1_str} + {part2_str}   $$ 的值。"
    
    # Calculate answer using IntegerOps.safe_eval()
    expr = f"(({a}) + ({b})) / ({divisor}) * {quotient} + abs({c} * ({d}) - {e})"
    correct_answer = str(int(IntegerOps.safe_eval(expr)))
    
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
        
        ua = float(user_answer)
        ca = float(correct_answer)
        
        if abs(ua - ca) < 1e-6:
            return {'correct': True, 'result': '正確'}
        
        return {'correct': False, 'result': '錯誤'}
    except:
        correct = str(user_answer).strip() == str(correct_answer).strip()
        return {'correct': correct, 'result': '正確' if correct else '錯誤'}
"""
    
    print("\n1. 检测 AI 生成的代码")
    print(f"   代码包含 IntegerOps 调用: {'IntegerOps' in ai_generated_code}")
    print(f"   代码长度: {len(ai_generated_code)} 字符")
    
    print("\n2. 执行注入")
    result_code, injected = _inject_domain_libs(ai_generated_code)
    
    print(f"   注入的类别: {injected}")
    print(f"   注入后代码长度: {len(result_code)} 字符")
    print(f"   IntegerOps 类定义已注入: {'class IntegerOps:' in result_code}")
    
    # 验证关键方法是否存在
    print("\n3. 验证 IntegerOps 方法")
    methods_to_check = ['fmt_num', 'random_nonzero', 'safe_eval']
    for method in methods_to_check:
        exists = f'def {method}' in result_code
        status = "✅" if exists else "❌"
        print(f"   {status} {method}() 方法存在: {exists}")
        assert exists, f"{method} 方法未找到！"
    
    print("\n4. 测试代码可执行性")
    # 尝试执行注入后的代码
    exec_globals = {}
    try:
        exec(result_code, exec_globals)
        print("   ✅ 代码编译成功")
        
        # 执行 generate 函数
        result = exec_globals['generate'](level=1)
        print(f"   ✅ generate() 执行成功")
        print(f"   生成题目: {result['question_text'][:60]}...")
        print(f"   正确答案: {result['correct_answer']}")
        
        # 验证返回结构
        assert 'question_text' in result
        assert 'correct_answer' in result
        assert 'mode' in result
        assert result['mode'] == 1
        print("   ✅ 返回结构正确")
        
        # 测试 check 函数
        check_result = exec_globals['check'](result['correct_answer'], result['correct_answer'])
        assert check_result['correct'] == True
        print(f"   ✅ check() 函数正常工作: {check_result}")
        
    except Exception as e:
        print(f"   ❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    print("\n5. 验证多次执行稳定性")
    for i in range(3):
        result = exec_globals['generate'](level=1)
        print(f"   第 {i+1} 次: {result['question_text'][:40]}... → 答案: {result['correct_answer']}")
        assert result['correct_answer'].lstrip('-').isdigit(), "答案应该是整数"
    print("   ✅ 多次执行稳定")


def test_mixed_operations():
    """测试混合使用 random 和 IntegerOps 的情况"""
    print("\n" + "=" * 70)
    print("测试混合使用场景")
    print("=" * 70)
    
    mixed_code = """
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    # 混合使用 random 和 IntegerOps
    a = random.randint(-20, 20)  # 传统方式
    b = IntegerOps.random_nonzero(-20, 20)  # 使用 API
    
    # 混合格式化
    if a < 0:
        a_str = f"({a})"  # 手动处理
    else:
        a_str = str(a)
    
    b_str = IntegerOps.fmt_num(b)  # 使用 API
    
    question_text = f"计算 $$ {a_str} + {b_str} $$"
    correct_answer = str(a + b)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {'correct': str(user_answer) == str(correct_answer), 'result': '正确'}
"""
    
    result_code, injected = _inject_domain_libs(mixed_code)
    print(f"   注入的类别: {injected}")
    assert 'IntegerOps' in injected
    
    # 执行测试
    exec_globals = {}
    exec(result_code, exec_globals)
    result = exec_globals['generate'](level=1)
    print(f"   ✅ 混合使用场景正常工作: {result['question_text']}")


if __name__ == "__main__":
    try:
        test_integer_skill_injection()
        test_mixed_operations()
        
        print("\n" + "=" * 70)
        print("🎉 所有整数单元注入测试通过！")
        print("=" * 70)
        print("\n✅ IntegerOps API 可正确识别")
        print("✅ 所有方法完整注入 (fmt_num, random_nonzero, safe_eval)")
        print("✅ 注入后的代码可正常执行")
        print("✅ generate() 和 check() 函数正常工作")
        print("✅ 混合使用 random 和 IntegerOps 没有冲突")
        print("\n整数单元已准备好进行 benchmark 测试！")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
