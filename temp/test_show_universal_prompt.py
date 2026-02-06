"""顯示完整的 Ab2/Ab3 Prompt (UNIVERSAL + Domain + MASTER_SPEC)"""

from core.prompts.prompt_builder import PromptBuilder
from models import db, SkillInfo, SkillGenCodePrompt
from app import app

# 需要 app context 來查詢資料庫
app.app_context().push()

# 從資料庫讀取真實的 MASTER_SPEC
active_prompt = SkillGenCodePrompt.query.filter_by(
    skill_id='gh_ApplicationsOfDerivatives', 
    prompt_type="MASTER_SPEC"
).order_by(SkillGenCodePrompt.created_at.desc()).first()

master_spec = active_prompt.prompt_content if active_prompt else "[MASTER_SPEC 未找到]"

# 生成 Ab2 的完整 Prompt
prompt_ab2 = PromptBuilder.build(
    master_spec=master_spec,
    ablation_id=2,
    skill_id="gh_ApplicationsOfDerivatives"
)

print("=" * 100)
print("【完整 UNIVERSAL_GEN_CODE_PROMPT + Domain + MASTER_SPEC (Ab2/Ab3)】")
print("=" * 100)
print(prompt_ab2)
print("=" * 100)
print(f"\nPrompt 總字數: {len(prompt_ab2)} 字元")
print(f"Prompt 總行數: {len(prompt_ab2.splitlines())} 行")
print()

# 分段統計
sections = {
    "UNIVERSAL_GEN_CODE_PROMPT 部分": prompt_ab2.split("### 🔧 [強制規範] 標準函數庫")[0] if "### 🔧 [強制規範] 標準函數庫" in prompt_ab2 else "",
    "Domain 函數庫注入部分": prompt_ab2.split("### 🔧 [強制規範] 標準函數庫")[1].split("### MASTER_SPEC:")[0] if "### 🔧 [強制規範] 標準函數庫" in prompt_ab2 and "### MASTER_SPEC:" in prompt_ab2 else "",
    "MASTER_SPEC 部分": prompt_ab2.split("### MASTER_SPEC:")[1] if "### MASTER_SPEC:" in prompt_ab2 else ""
}

print("【分段統計】")
for section_name, section_content in sections.items():
    if section_content:
        print(f"{section_name}: {len(section_content)} 字元, {len(section_content.splitlines())} 行")

print()
print("【與 Ab1 的比較】")
print(f"Ab1 (BARE_PROMPT): ~1,242 字元, 47 行")
print(f"Ab2/Ab3 (UNIVERSAL + Domain + SPEC): {len(prompt_ab2)} 字元, {len(prompt_ab2.splitlines())} 行")
print(f"差距: {len(prompt_ab2) - 1242} 字元 ({(len(prompt_ab2) / 1242):.1f}x)")
