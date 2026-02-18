"""
测试分数单元的 FractionOps API 注入
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from code_generator import _inject_domain_libs


def test_fraction_skill_injection():
    """测试符合分数 SKILL.md 风格的代码注入"""
    print("=" * 70)
    print("测试分数单元 FractionOps API 注入")
    print("=" * 70)
    
    # 模拟 AI 根据分数 SKILL.md 生成的代码
    ai_generated_code = """
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    # 使用 FractionOps 创建分数
    f1 = FractionOps.create("1/3")
    f2 = FractionOps.create("1/2")
    
    # 分数运算
    result = FractionOps.add(f1, f2)
    
    # 转成 LaTeX
    f1_latex = FractionOps.to_latex(f1)
    f2_latex = FractionOps.to_latex(f2)
    result_latex = FractionOps.to_latex(result)
    
    question_text = f"計算 $$ {f1_latex} + {f2_latex} $$"
    
    # 答案格式化
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
    
    print("\n1. 检测 AI 生成的代码")
    print(f"   代码包含 FractionOps 调用: {'FractionOps' in ai_generated_code}")
    
    print("\n2. 执行注入")
    result_code, injected = _inject_domain_libs(ai_generated_code)
    
    print(f"   注入的类别: {injected}")
    print(f"   FractionOps 类定义已注入: {'class FractionOps:' in result_code}")
    
    # 验证关键方法
    print("\n3. 验证 FractionOps 方法")
    methods = ['create', 'to_latex', 'add', 'sub', 'mul', 'div']
    for method in methods:
        exists = f'def {method}' in result_code
        status = "✅" if exists else "❌"
        print(f"   {status} {method}()")
        assert exists, f"{method} 方法未找到！"
    
    print("\n4. 测试代码可执行性")
    exec_globals = {}
    exec(result_code, exec_globals)
    result = exec_globals['generate'](level=1)
    print(f"   ✅ 生成题目: {result['question_text']}")
    print(f"   ✅ 正确答案: {result['correct_answer']}")
    
    # 验证答案格式
    assert result['correct_answer'] == "5/6", f"答案错误: {result['correct_answer']}"
    print(f"   ✅ 答案正确 (1/3 + 1/2 = 5/6)")


if __name__ == "__main__":
    try:
        test_fraction_skill_injection()
        
        print("\n" + "=" * 70)
        print("🎉 分数单元注入测试通过！")
        print("=" * 70)
        print("\n✅ FractionOps API 可正确识别和注入")
        print("✅ 所有方法完整注入")
        print("✅ 注入后的代码可正常执行")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
