"""
驗證 while True 結構要求是否已加入 Prompt
檢查點：
1. Architect Prompt 是否要求 while True 結構
2. UNIVERSAL Prompt 是否明確示範 while True
3. 是否有結構檢查清單
"""

import sys
import os

def read_file(filepath):
    """讀取檔案內容"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def verify_architect():
    """驗證 Architect Prompt"""
    print("=" * 80)
    print("檢查 1: Architect Prompt 是否要求 while True 結構")
    print("=" * 80)
    
    filepath = "e:\\Python\\MathProject_AST_Research\\core\\prompt_architect.py"
    content = read_file(filepath)
    
    # 檢查點
    checks = {
        "提到 'while True'": "while True" in content,
        "提到 '外層 while True'": "外層 while True" in content or "外層迴圈" in content,
        "有結構要求章節": "結構要求" in content or "結構檢查" in content,
        "有 implementation_checklist": "implementation_checklist" in content,
        "checklist 包含 while True": "必須有外層 while True" in content or "外層 while True 是必須的" in content,
        "有結構檢查清單": "結構檢查清單" in content,
    }
    
    all_pass = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if not result:
            all_pass = False
    
    # 顯示相關片段
    if "while True" in content:
        print("\n📝 找到的相關片段（前 5 處）：")
        lines = content.split('\n')
        count = 0
        for i, line in enumerate(lines):
            if 'while True' in line.lower() or '結構要求' in line or 'implementation_checklist' in line:
                if count >= 5:
                    break
                # 顯示前後各 1 行
                start = max(0, i-1)
                end = min(len(lines), i+2)
                context = '\n'.join(lines[start:end])
                print(f"\n第 {i+1} 行附近：")
                print(context)
                print("-" * 60)
                count += 1
    
    return all_pass

def verify_universal():
    """驗證 UNIVERSAL Prompt"""
    print("\n" + "=" * 80)
    print("檢查 2: UNIVERSAL Prompt 是否示範 while True 結構")
    print("=" * 80)
    
    filepath = "e:\\Python\\MathProject_AST_Research\\core\\prompts\\prompt_builder.py"
    content = read_file(filepath)
    
    # 檢查點
    checks = {
        "提到 'while True'": "while True" in content,
        "有安全生成範例": "安全生成範例" in content or "請參照此模式" in content,
        "範例包含 while True": "def generate" in content and "while True" in content,
        "有結構檢查清單": "結構檢查清單" in content or "結構要求" in content,
        "明確標註 CRITICAL": "CRITICAL" in content or "必須" in content,
        "有 continue/break 說明": "continue" in content and "break" in content,
    }
    
    all_pass = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if not result:
            all_pass = False
    
    # 顯示範例片段
    if "def generate" in content:
        print("\n📝 找到的 generate 範例（第一處）：")
        lines = content.split('\n')
        in_example = False
        example_lines = []
        
        for line in lines:
            if 'def generate' in line:
                in_example = True
            if in_example:
                example_lines.append(line)
                if 'return {' in line and len(example_lines) > 5:
                    break
        
        print('\n'.join(example_lines[:25]))  # 只顯示前 25 行
    
    return all_pass

def verify_structure_requirements():
    """驗證結構要求是否完整"""
    print("\n" + "=" * 80)
    print("檢查 3: 結構要求是否完整且清晰")
    print("=" * 80)
    
    architect_file = "e:\\Python\\MathProject_AST_Research\\core\\prompt_architect.py"
    universal_file = "e:\\Python\\MathProject_AST_Research\\core\\prompts\\prompt_builder.py"
    
    architect_content = read_file(architect_file)
    universal_content = read_file(universal_file)
    
    combined_content = architect_content + "\n" + universal_content
    
    required_elements = {
        "外層 while True 是必須的": ("外層 while True" in combined_content and "必須" in combined_content),
        "驗證邏輯在 while True 內": ("驗證邏輯" in combined_content or "continue" in combined_content),
        "格式化在 while True 外": ("格式化" in combined_content and ("while True 外" in combined_content or "break 後" in combined_content)),
        "有 continue/break 說明": ("continue" in combined_content and "break" in combined_content),
        "禁止內層 while True": ("內層" in combined_content or "只有外層" in combined_content),
    }
    
    all_pass = True
    for element, result in required_elements.items():
        status = "✅" if result else "❌"
        print(f"{status} {element}")
        if not result:
            all_pass = False
    
    return all_pass

def main():
    print("🔍 驗證 while True 結構要求是否已加入 Prompt\n")
    
    results = []
    results.append(("Architect Prompt", verify_architect()))
    results.append(("UNIVERSAL Prompt", verify_universal()))
    results.append(("結構要求完整性", verify_structure_requirements()))
    
    print("\n" + "=" * 80)
    print("📊 總結")
    print("=" * 80)
    
    all_pass = all(r[1] for r in results)
    
    for name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{name}: {status}")
    
    print("\n" + "=" * 80)
    if all_pass:
        print("🎉 所有檢查通過！while True 結構要求已正確加入源頭 Prompt")
    else:
        print("⚠️  部分檢查失敗，需要進一步強化")
    print("=" * 80)
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
