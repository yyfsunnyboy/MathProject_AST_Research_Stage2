"""顯示完整的 Ab2/Ab3 Prompt 並保存到文件"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 設置輸出編碼
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.prompts.prompt_builder import PromptBuilder, UNIVERSAL_GEN_CODE_PROMPT
from models import db, SkillGenCodePrompt
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

# 保存到文件
output_file = "temp/ab2_full_prompt.txt"
os.makedirs("temp", exist_ok=True)
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 100 + "\n")
    f.write("【完整 UNIVERSAL_GEN_CODE_PROMPT + Domain + MASTER_SPEC (Ab2/Ab3)】\n")
    f.write("=" * 100 + "\n\n")
    f.write(prompt_ab2)
    f.write("\n\n" + "=" * 100 + "\n")
    f.write(f"\nPrompt 總字數: {len(prompt_ab2)} 字元\n")
    f.write(f"Prompt 總行數: {len(prompt_ab2.splitlines())} 行\n\n")
    
    # 分段統計
    if "### 🔧 [強制規範] 標準函數庫" in prompt_ab2:
        universal_part = prompt_ab2.split("### 🔧 [強制規範] 標準函數庫")[0]
        f.write(f"UNIVERSAL_GEN_CODE_PROMPT 部分: {len(universal_part)} 字元, {len(universal_part.splitlines())} 行\n")
    
    if "### 🔧 [強制規範] 標準函數庫" in prompt_ab2 and "### MASTER_SPEC:" in prompt_ab2:
        domain_part = prompt_ab2.split("### 🔧 [強制規範] 標準函數庫")[1].split("### MASTER_SPEC:")[0]
        f.write(f"Domain 函數庫注入部分: {len(domain_part)} 字元, {len(domain_part.splitlines())} 行\n")
    
    if "### MASTER_SPEC:" in prompt_ab2:
        spec_part = prompt_ab2.split("### MASTER_SPEC:")[1]
        f.write(f"MASTER_SPEC 部分: {len(spec_part)} 字元, {len(spec_part.splitlines())} 行\n")
    
    f.write(f"\n【與 Ab1 的比較】\n")
    f.write(f"Ab1 (BARE_PROMPT): ~1,242 字元, 47 行\n")
    f.write(f"Ab2/Ab3 (UNIVERSAL + Domain + SPEC): {len(prompt_ab2)} 字元, {len(prompt_ab2.splitlines())} 行\n")
    f.write(f"差距: {len(prompt_ab2) - 1242} 字元 ({(len(prompt_ab2) / 1242):.1f}x)\n")

print(f"✅ Prompt 已保存到: {output_file}")
print(f"\nPrompt 統計:")
print(f"  總字數: {len(prompt_ab2)} 字元")
print(f"  總行數: {len(prompt_ab2.splitlines())} 行")
print(f"\n與 Ab1 比較:")
print(f"  Ab1: ~1,242 字元")
print(f"  Ab2/Ab3: {len(prompt_ab2)} 字元 ({(len(prompt_ab2) / 1242):.1f}x)")
print(f"\n請查看文件以了解完整內容：{output_file}")
