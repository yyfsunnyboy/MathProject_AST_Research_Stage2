"""
验证 Ablation Study 的实验条件是否正确设置
"""
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app import create_app
from models import db, AblationSetting, SkillGenCodePrompt

print("="*70)
print("🔍 实验条件验证")
print("="*70)

app = create_app()
with app.app_context():
    print("\n📊 Ablation Settings (数据库配置):")
    print("-"*70)
    
    ablations = AblationSetting.query.all()
    for ab in ablations:
        print(f"\n  Ab{ab.id}: {ab.name}")
        print(f"    Regex Healer: {'✅ Enabled' if ab.use_regex else '❌ Disabled'}")
        print(f"    AST Healer:   {'✅ Enabled' if ab.use_ast else '❌ Disabled'}")
        print(f"    说明: {ab.description}")
    
    print("\n" + "="*70)
    print("📝 实验条件总结:")
    print("="*70)
    
    print("\n  Ab1 (Bare):")
    print("    - Prompt: BARE_MINIMAL_PROMPT (270 chars) + MASTER_SPEC")
    print("    - Healer: ❌ 无")
    print("    - 预期: 生成代码质量最差，可能有严重语法错误")
    print("    - 用途: 测试最简单配置的基线性能")
    
    print("\n  Ab2 (MASTER_SPEC_Only):")
    print("    - Prompt: 纯数据库 MASTER_SPEC (无额外工程化 Prompt)")
    print("    - Healer: ❌ 无")
    print("    - 预期: 有工程化 Prompt，代码质量中等，可能有部分错误")
    print("    - 用途: 测试 MASTER_SPEC 工程化 Prompt 的单独价值")
    
    print("\n  Ab3 (Full-Healing):")
    print("    - Prompt: 纯数据库 MASTER_SPEC (与 Ab2 相同)")
    print("    - Healer: ✅ 完整启用 (Regex + AST)")
    print("    - 预期: 工程化 Prompt + 自愈机制 = 最高成功率")
    print("    - 用途: 测试完整系统的最佳性能")
    
    print("\n" + "="*70)
    print("🎯 关键对比点:")
    print("="*70)
    
    print("\n  Ab1 vs Ab2:")
    print("    - Prompt 差异: Bare (270 chars) vs MASTER_SPEC (通常 1500-2500 chars)")
    print("    - Healer 差异: 都无 Healer")
    print("    - 预期差异: 20-40 percentage points")
    print("    - 验证内容: MASTER_SPEC 工程化 Prompt 的价值")
    
    print("\n  Ab2 vs Ab3:")
    print("    - Prompt 差异: 相同 (都使用纯 MASTER_SPEC)")
    print("    - Healer 差异: 无 vs 完整 (Regex+AST)")
    print("    - 预期差异: 30-50 percentage points")
    print("    - 验证内容: Healer 自愈机制的独立价值 ⭐")
    
    print("\n  Ab1 vs Ab3:")
    print("    - Prompt 差异: Bare vs MASTER_SPEC")
    print("    - Healer 差异: 无 vs 完整")
    print("    - 预期差异: 50-70 percentage points")
    print("    - 验证内容: 完整系统的整体价值")
    
    # 检查测试技能的 MASTER_SPEC
    print("\n" + "="*70)
    print("📚 测试技能的 MASTER_SPEC 状态:")
    print("="*70)
    
    TEST_SKILLS = [
        ('jh_數學1上_IntegerAdditionOperation', '整数的加法运算'),
        ('jh_數學1上_IntegerSubtractionOperation', '整数的减法运算'),
        ('jh_數學1上_IntegerMultiplication', '整数的乘法运算'),
        ('jh_數學1上_IntegerDivision', '整数的除法运算'),
    ]
    
    missing = []
    for skill_id, skill_name in TEST_SKILLS:
        spec = SkillGenCodePrompt.query.filter_by(
            skill_id=skill_id,
            prompt_type="MASTER_SPEC"
        ).order_by(SkillGenCodePrompt.created_at.desc()).first()
        
        if spec:
            print(f"\n  ✅ {skill_name}")
            print(f"     MASTER_SPEC: {len(spec.prompt_content)} chars")
        else:
            print(f"\n  ❌ {skill_name}")
            print(f"     缺少 MASTER_SPEC")
            missing.append(skill_id)
    
    if missing:
        print(f"\n⚠️  警告: {len(missing)} 个技能缺少 MASTER_SPEC")
        print("   执行 ablation_bare_vs_healer.py 时将提示生成")
    else:
        print(f"\n✅ 所有测试技能都有 MASTER_SPEC，可以开始实验！")
    
    print("\n" + "="*70)
    print("✅ 验证完成")
    print("="*70)
