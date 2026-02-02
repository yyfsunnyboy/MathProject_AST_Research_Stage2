"""验证 Architect 修复：确认新的格式化规则不包含 clean_latex_output() 冲突"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.prompt_architect import ARCHITECT_SYSTEM_PROMPT

def check_architect_prompt():
    """检查 Architect System Prompt 是否已修复"""
    
    print("=" * 80)
    print("【Architect System Prompt 检查】")
    print("=" * 80)
    print()
    
    # 检查点 1: 是否包含 Domain 函数的正确指导
    has_domain_mode = "模式 A：使用 Domain 標準函數" in ARCHITECT_SYSTEM_PROMPT
    has_domain_warning = "絕對禁止**對 Domain 函數結果調用 clean_latex_output()" in ARCHITECT_SYSTEM_PROMPT
    
    # 检查点 2: 是否移除了旧的 clean_latex_output 强制指令
    has_old_instruction = "最後呼叫 clean_latex_output(q)" in ARCHITECT_SYSTEM_PROMPT and \
                          "組合：將式子插入敘述，最後呼叫 clean_latex_output(q)" in ARCHITECT_SYSTEM_PROMPT
    
    # 检查点 3: 是否区分了两种模式
    has_simple_mode = "模式 B：簡單運算式" in ARCHITECT_SYSTEM_PROMPT
    
    print("✅ 检查点 1: Domain 函数模式指导")
    print(f"   - 包含 Domain 模式说明: {has_domain_mode}")
    print(f"   - 包含禁止 clean 警告: {has_domain_warning}")
    print()
    
    print("✅ 检查点 2: 旧指令移除")
    print(f"   - 仍包含旧的强制 clean 指令: {has_old_instruction}")
    print()
    
    print("✅ 检查点 3: 模式区分")
    print(f"   - 包含简单运算模式说明: {has_simple_mode}")
    print()
    
    # 提取格式化规则部分
    if "formatting:" in ARCHITECT_SYSTEM_PROMPT:
        formatting_start = ARCHITECT_SYSTEM_PROMPT.index("formatting:")
        formatting_section = ARCHITECT_SYSTEM_PROMPT[formatting_start:formatting_start+3000]
        
        print("=" * 80)
        print("【格式化规则摘录】")
        print("=" * 80)
        print()
        
        # 显示关键段落
        if "模式 A：使用 Domain 標準函數" in formatting_section:
            mode_a_start = formatting_section.index("模式 A：使用 Domain 標準函數")
            mode_a_end = formatting_section.find("🟡 **模式 B", mode_a_start)
            if mode_a_end == -1:
                mode_a_end = mode_a_start + 800
            
            print("🟢 模式 A（Domain 函数）：")
            print("-" * 80)
            print(formatting_section[mode_a_start:mode_a_end].strip())
            print()
        
        if "模式 B：簡單運算式" in formatting_section:
            mode_b_start = formatting_section.index("模式 B：簡單運算式")
            mode_b_end = formatting_section.find("**絕對禁止", mode_b_start)
            if mode_b_end == -1:
                mode_b_end = mode_b_start + 600
            
            print("🟡 模式 B（简单运算）：")
            print("-" * 80)
            print(formatting_section[mode_b_start:mode_b_end].strip())
            print()
    
    # 最终判断
    print("=" * 80)
    print("【修复验证结果】")
    print("=" * 80)
    print()
    
    all_pass = has_domain_mode and has_domain_warning and has_simple_mode and not has_old_instruction
    
    if all_pass:
        print("✅ 修复成功！Architect 现在会生成正确的 MASTER_SPEC")
        print()
        print("新的行为：")
        print("  - 对 Domain 函数题型：禁止 clean_latex_output()")
        print("  - 对简单运算题型：允许在最后调用一次 clean_latex_output()")
        print("  - 明确区分两种模式，避免混淆")
        print()
        print("下次使用 scripts/sync_skills_files.py 模式[4] 生成的 MASTER_SPEC")
        print("将不会再包含导致 placeholder 泄漏的冲突指令！")
        return True
    else:
        print("❌ 修复不完整，请检查：")
        if not has_domain_mode:
            print("  - 缺少 Domain 函数模式说明")
        if not has_domain_warning:
            print("  - 缺少禁止 clean 警告")
        if not has_simple_mode:
            print("  - 缺少简单运算模式说明")
        if has_old_instruction:
            print("  - 仍包含旧的强制 clean 指令")
        return False

if __name__ == "__main__":
    success = check_architect_prompt()
    sys.exit(0 if success else 1)
