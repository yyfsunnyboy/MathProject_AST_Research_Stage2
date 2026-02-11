"""
Test Script for Regex Healer V2.6
- Verify remove_trailing_artifacts() works correctly
- Verify Golden Prompt anti-C language instructions are present
- Test end-to-end healing pipeline with C-style code
"""

import sys
sys.path.insert(0, r'e:\\python\\MathProject_AST_Research')

from core.healers.regex_healer import RegexHealer
import os

def test_remove_trailing_artifacts():
    """Test the new remove_trailing_artifacts() method in V2.6"""
    print("\n" + "="*80)
    print("TEST 1: remove_trailing_artifacts() - Trailing Garbage Cleanup")
    print("="*80)
    
    healer = RegexHealer()
    
    test_cases = [
        {
            "name": "C-style closing brace",
            "input": "def generate():\n    x = 1\n    return x\n}",
            "expected_clean": "def generate():\n    x = 1\n    return x"
        },
        {
            "name": "Markdown fence + python keyword",
            "input": "def generate():\n    return 42\n```\npython",
            "expected_clean": "def generate():\n    return 42"
        },
        {
            "name": "Semicolon ending",
            "input": "def generate():\n    print('hello');",
            "expected_clean": "def generate():\n    print('hello')"
        },
        {
            "name": "Multiple trailing artifacts",
            "input": "def generate():\n    x = 1\n};\npython\n```",
            "expected_clean": "def generate():\n    x = 1"
        },
        {
            "name": "Clean code (no artifacts)",
            "input": "def generate():\n    return 42",
            "expected_clean": "def generate():\n    return 42"
        }
    ]
    
    all_passed = True
    for i, test in enumerate(test_cases, 1):
        result = healer.remove_trailing_artifacts(test["input"])
        passed = result == test["expected_clean"]
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status} | Test {i}: {test['name']}")
        print(f"  Input:    {repr(test['input'][:50])}...")
        print(f"  Expected: {repr(test['expected_clean'][:50])}...")
        print(f"  Got:      {repr(result[:50])}...")
        
        if not passed:
            all_passed = False
            print(f"  ⚠️ Mismatch!")
    
    return all_passed

def test_golden_prompt_syntax_rules():
    """Verify Golden Prompt has anti-C language instructions"""
    print("\n" + "="*80)
    print("TEST 2: Golden Prompt - Anti-C Language Instructions")
    print("="*80)
    
    golden_prompt_path = r"e:\python\MathProject_AST_Research\experiments\golden_prompts\temp\jh_數學1上_FourArithmeticOperationsOfIntegers_Ab2.txt"
    
    if not os.path.exists(golden_prompt_path):
        print(f"❌ FAIL: Golden prompt file not found: {golden_prompt_path}")
        return False
    
    with open(golden_prompt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_keywords = [
        "⚠️ PYTHON SYNTAX STRICTNESS",
        "NEVER put a closing brace",
        "NEVER use `return { ... };`",
        "NEVER use C-style syntax",
        "Just end the `def generate`"
    ]
    
    all_found = True
    for keyword in required_keywords:
        if keyword in content:
            print(f"✅ FOUND: {keyword[:50]}...")
        else:
            print(f"❌ MISSING: {keyword}")
            all_found = False
    
    return all_found

def test_healer_version():
    """Verify Regex Healer is version V2.6"""
    print("\n" + "="*80)
    print("TEST 3: Regex Healer Version Check")
    print("="*80)
    
    regex_healer_path = r"e:\python\MathProject_AST_Research\core\healers\regex_healer.py"
    
    with open(regex_healer_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "Version: V2.6" in content:
        print("✅ PASS: Regex Healer version is V2.6")
        return True
    else:
        print("❌ FAIL: Regex Healer version not updated to V2.6")
        return False

def test_healer_integration():
    """Test the full heal() pipeline with trailing artifacts"""
    print("\n" + "="*80)
    print("TEST 4: Healer Integration - Full Pipeline")
    print("="*80)
    
    healer = RegexHealer()
    
    # Simulate a code with C-style artifacts and other issues
    problematic_code = """def generate():
    x = 5
    y = 3
    result = x + y
    return result
}
python"""
    
    print(f"Input code with C-style artifacts:")
    print(f"  {repr(problematic_code)}")
    
    # heal() takes only code_str parameter, returns (fixed_code, stats_dict)
    fixed_code, stats = healer.heal(problematic_code)
    
    print(f"\nHealer returned stats: {stats}")
    print(f"Fixed code:\n  {repr(fixed_code)}")
    
    # Check if trailing artifacts were removed and code is executable
    if fixed_code.rstrip().endswith("}"):
        print("❌ FAIL: Trailing brace not removed!")
        return False
    
    if "python" in fixed_code.lower() and fixed_code.rstrip().endswith("python"):
        print("❌ FAIL: Trailing 'python' keyword not removed!")
        return False
    
    try:
        compile(fixed_code, '<string>', 'exec')
        print("✅ PASS: Fixed code is syntactically valid Python")
        return True
    except SyntaxError as e:
        print(f"❌ FAIL: Fixed code has syntax error: {e}")
        return False

if __name__ == "__main__":
    print("\n🧪 TESTING REGEX HEALER V2.6 - Trailing Artifacts & Golden Prompt Fixes")
    print("="*80)
    
    results = []
    
    # Run all tests
    results.append(("Remove Trailing Artifacts", test_remove_trailing_artifacts()))
    results.append(("Golden Prompt Syntax Rules", test_golden_prompt_syntax_rules()))
    results.append(("Healer Version Check", test_healer_version()))
    results.append(("Healer Integration", test_healer_integration()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")
    
    total_passed = sum(1 for _, p in results if p)
    total_tests = len(results)
    
    print(f"\n📊 Result: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All tests passed! V2.6 remediation is working correctly.")
    else:
        print("⚠️ Some tests failed. Review output above.")
