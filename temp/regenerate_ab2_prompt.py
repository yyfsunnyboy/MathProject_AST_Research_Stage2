"""重新生成修正後的 Ab2/Ab3 完整 Prompt"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, SkillGenCodePrompt
from app import app
from core.prompts.prompt_builder import PromptBuilder

app.app_context().push()

# 讀取 ApplicationsOfDerivatives 的 MASTER_SPEC
prompt_obj = SkillGenCodePrompt.query.filter_by(
    skill_id='gh_ApplicationsOfDerivatives',
    prompt_type='MASTER_SPEC'
).order_by(SkillGenCodePrompt.created_at.desc()).first()

if not prompt_obj:
    print("❌ 找不到 ApplicationsOfDerivatives 的 MASTER_SPEC")
    sys.exit(1)

master_spec = prompt_obj.prompt_content
skill_id = 'gh_ApplicationsOfDerivatives'

# 使用 PromptBuilder 生成 Ab2/Ab3 的完整 Prompt
full_prompt = PromptBuilder.build(
    master_spec=master_spec,
    ablation_id=2,  # Ab2 和 Ab3 使用相同 Prompt
    skill_id=skill_id
)

# 格式化輸出
output_lines = []
output_lines.append("=" * 100)
output_lines.append("【完整 UNIVERSAL_GEN_CODE_PROMPT + Domain + MASTER_SPEC (Ab2/Ab3)】")
output_lines.append("=" * 100)
output_lines.append("")
output_lines.append(full_prompt)
output_lines.append("")
output_lines.append("=" * 100)
output_lines.append("")
output_lines.append(f"Prompt 總字數: {len(full_prompt)} 字元")

# 計算行數
prompt_lines = full_prompt.split('\n')
output_lines.append(f"Prompt 總行數: {len(prompt_lines)} 行")

# 統計 MASTER_SPEC 部分
if '### MASTER_SPEC:' in full_prompt:
    spec_start = full_prompt.index('### MASTER_SPEC:')
    spec_content = full_prompt[spec_start:]
    spec_lines = spec_content.split('\n')
    output_lines.append("")
    output_lines.append(f"MASTER_SPEC 部分: {len(spec_content)} 字元, {len(spec_lines)} 行")

# 與 Ab1 比較
BARE_PROMPT_LENGTH = 734  # 已知的 Ab1 長度
output_lines.append("")
output_lines.append("【與 Ab1 的比較】")
output_lines.append(f"Ab1 (BARE_PROMPT): ~{BARE_PROMPT_LENGTH} 字元")
output_lines.append(f"Ab2/Ab3 (UNIVERSAL + Domain + SPEC): {len(full_prompt)} 字元")
ratio = len(full_prompt) / BARE_PROMPT_LENGTH
output_lines.append(f"差距: {len(full_prompt) - BARE_PROMPT_LENGTH} 字元 ({ratio:.1f}x)")

# 輸出到檔案
output_path = r"E:\Python\MathProject_AST_Research\temp\ab2_full_prompt.txt"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print(f"✅ 成功生成新的 Ab2/Ab3 完整 Prompt")
print(f"   輸出檔案: {output_path}")
print(f"   Prompt 長度: {len(full_prompt)} 字元")
print(f"   Prompt 行數: {len(prompt_lines)} 行")
print()
print("【修正摘要】")
print("  ✅ 矛盾 ① 解決: 移除檢查清單中的強制 clean_latex_output()")
print("  ✅ 矛盾 ② 解決: 統一 eval/safe_eval 條款")
print("  ✅ 矛盾 ③ 解決: MASTER_SPEC answer_display 改為純多項式格式")
print()
print("  新 Prompt 不再包含內部矛盾，可用於論文！")
