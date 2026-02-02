"""驗證 MASTER_SPEC 修復"""
import sys
sys.path.insert(0, '.')
from models import SkillGenCodePrompt
from app import create_app

app = create_app()
with app.app_context():
    spec = SkillGenCodePrompt.query.filter_by(
        skill_id='gh_ApplicationsOfDerivatives',
        prompt_type='MASTER_SPEC'
    ).order_by(SkillGenCodePrompt.created_at.desc()).first()
    
    content = spec.prompt_content
    lines = content.split('\n')
    
    print('✅ 驗證 MASTER_SPEC 修復結果:')
    print('='*70)
    
    print('\n【修復1: num_terms 限制】')
    for i, line in enumerate(lines):
        if 'num_terms' in line and '3~5' in line:
            print(f'{line}')
    
    print('\n' + '='*70)
    print('【修復2: 導數符號格式化】')
    for i, line in enumerate(lines):
        if '格式化導數符號' in line:
            for j in range(i, min(i+12, len(lines))):
                print(lines[j])
            break
    
    print('\n' + '='*70)
    print('【修復3: 組合題目】')
    for i, line in enumerate(lines):
        if '組合題目' in line:
            for j in range(i, min(i+6, len(lines))):
                print(lines[j])
            break
