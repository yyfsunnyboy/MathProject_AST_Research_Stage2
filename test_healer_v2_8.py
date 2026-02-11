# -*- coding: utf-8 -*-
"""
测试 Regex Healer V2.8 的新功能
- remove_duplicate_class_definitions()
- fix_incorrect_class_method_calls()
"""

from core.healers.regex_healer import RegexHealer

def test_duplicate_class_removal():
    """测试移除重复的类定义"""
    print("=" * 80)
    print("TEST 1: 移除重复的类定义")
    print("=" * 80)
    
    code_with_duplicates = """
import random

class IntegerOps:
    '''完整的类定义'''
    
    @staticmethod
    def fmt_num(n):
        if n < 0:
            return f"({n})"
        return str(n)
    
    @staticmethod
    def random_nonzero(min_val, max_val):
        available = [x for x in range(min_val, max_val + 1) if x != 0]
        return random.choice(available)

# 其他代码...

class IntegerOps:
    @staticmethod
    def random_nonzero(min_val, max_val):
        available = [x for x in range(min_val, max_val + 1) if x != 0]
        return random.choice(available)

def generate():
    x = IntegerOps.random_nonzero(-10, 10)
    return {'answer': x}
"""
    
    healer = RegexHealer()
    fixed_code, removed = healer.remove_duplicate_class_definitions(code_with_duplicates)
    
    print(f"\n移除的重复定义数: {removed}")
    print(f"\n修复后的代码中 'class IntegerOps' 出现次数: {fixed_code.count('class IntegerOps')}")
    
    if removed > 0 and fixed_code.count('class IntegerOps') == 1:
        print("✅ PASS: 成功移除重复的类定义")
        return True
    else:
        print("❌ FAIL: 移除重复类定义失败")
        return False


def test_method_call_fix():
    """测试修复错误的类方法调用"""
    print("\n" + "=" * 80)
    print("TEST 2: 修复错误的类方法调用")
    print("=" * 80)
    
    code_with_wrong_calls = """
from domain_function_library import fmt_num, to_latex

class IntegerOps:
    @staticmethod
    def random_nonzero(min_val, max_val):
        available = [x for x in range(min_val, max_val + 1) if x != 0]
        return random.choice(available)

def generate():
    A = IntegerOps.random_nonzero(-10, 10)
    B = IntegerOps.random_nonzero(-10, 10)
    
    # 错误: fmt_num 是全局函数，不是 IntegerOps 的方法
    str_A = IntegerOps.fmt_num(A)
    str_B = IntegerOps.fmt_num(B)
    
    # 错误: to_latex 也是全局函数
    latex = IntegerOps.to_latex(str_A)
    
    return {'answer': str_A}
"""
    
    healer = RegexHealer()
    fixed_code, fix_count = healer.fix_incorrect_class_method_calls(code_with_wrong_calls)
    
    print(f"\n修复的错误调用数: {fix_count}")
    print(f"\n修复后包含 'IntegerOps.fmt_num(': {('IntegerOps.fmt_num(' in fixed_code)}")
    print(f"修复后包含 'fmt_num(': {('fmt_num(' in fixed_code)}")
    print(f"修复后包含 'IntegerOps.to_latex(': {('IntegerOps.to_latex(' in fixed_code)}")
    print(f"修复后包含 'to_latex(': {('to_latex(' in fixed_code)}")
    
    if (fix_count > 0 and 
        'IntegerOps.fmt_num(' not in fixed_code and 
        'IntegerOps.to_latex(' not in fixed_code and
        'fmt_num(' in fixed_code and
        'to_latex(' in fixed_code):
        print("✅ PASS: 成功修复错误的方法调用")
        return True
    else:
        print("❌ FAIL: 修复方法调用失败")
        return False


def test_full_heal_integration():
    """测试完整的 heal() 流程"""
    print("\n" + "=" * 80)
    print("TEST 3: 完整 heal() 流程集成测试")
    print("=" * 80)
    
    # 模拟 Ab3 的问题代码
    problematic_code = """
import random

class IntegerOps:
    '''完整的类定义'''
    
    @staticmethod
    def random_nonzero(min_val, max_val):
        available = [x for x in range(min_val, max_val + 1) if x != 0]
        return random.choice(available)

# [AI GENERATED CODE]
class IntegerOps:
    @staticmethod
    def random_nonzero(min_val, max_val):
        available = [x for x in range(min_val, max_val + 1) if x != 0]
        return random.choice(available)

def generate():
    A = IntegerOps.random_nonzero(-10, 10)
    B = IntegerOps.random_nonzero(-10, 10)
    
    # 错误的方法调用
    str_A = IntegerOps.fmt_num(A)
    str_B = IntegerOps.fmt_num(B)
    
    return {'answer': str_A}
"""
    
    healer = RegexHealer()
    fixed_code, stats = healer.heal(problematic_code)
    
    print(f"\n修复统计:")
    print(f"  - 总修复次数: {stats['regex_fix_count']}")
    print(f"  - 移除重复类: {stats.get('duplicates_removed', 0)}")
    print(f"  - 修复方法调用: {stats.get('method_calls_fixed', 0)}")
    print(f"  - 注入 imports: {stats['imports_injected']}")
    
    print(f"\n修复后检查:")
    print(f"  - 'class IntegerOps' 出现次数: {fixed_code.count('class IntegerOps')}")
    print(f"  - 包含 'IntegerOps.fmt_num(': {('IntegerOps.fmt_num(' in fixed_code)}")
    print(f"  - 包含 'fmt_num(': {('fmt_num(' in fixed_code)}")
    print(f"  - 包含 'from domain_function_library import fmt_num': {('from domain_function_library import fmt_num' in fixed_code)}")
    
    success = (
        stats['regex_fix_count'] > 0 and
        stats.get('duplicates_removed', 0) > 0 and
        stats.get('method_calls_fixed', 0) > 0 and
        fixed_code.count('class IntegerOps') == 1 and
        'IntegerOps.fmt_num(' not in fixed_code and
        'fmt_num(' in fixed_code
    )
    
    if success:
        print("\n✅ PASS: heal() 流程成功修复所有问题")
        return True
    else:
        print("\n❌ FAIL: heal() 流程未能修复所有问题")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("REGEX HEALER V2.8 测试套件")
    print("=" * 80)
    
    results = []
    
    # 测试 1: 移除重复类定义
    results.append(("移除重复类定义", test_duplicate_class_removal()))
    
    # 测试 2: 修复方法调用
    results.append(("修复错误方法调用", test_method_call_fix()))
    
    # 测试 3: 完整流程
    results.append(("完整 heal() 流程", test_full_heal_integration()))
    
    # 总结
    print("\n" + "=" * 80)
    print("测试结果总结")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n总计: {passed_count}/{total_count} 测试通过")
    
    if passed_count == total_count:
        print("\n🎉 所有测试通过！Healer V2.8 准备就绪！")
    else:
        print("\n⚠️  部分测试失败，需要检查修复逻辑")


if __name__ == "__main__":
    main()
