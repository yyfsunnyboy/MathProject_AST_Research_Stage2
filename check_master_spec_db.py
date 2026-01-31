from app import app
from models import SkillGenCodePrompt
import re

with app.app_context():
    spec = SkillGenCodePrompt.query.filter_by(
        skill_id='gh_ApplicationsOfDerivatives',
        prompt_type='MASTER_SPEC'
    ).order_by(SkillGenCodePrompt.created_at.desc()).first()
    
    if spec:
        content = spec.prompt_content
        print(f"=== MASTER_SPEC for ApplicationsOfDerivatives ===")
        print(f"總長度: {len(content)} 字元\n")
        
        # 檢查是否有範例
        example_patterns = [
            r'【範例】(.*?)(?=【|$)',
            r'範例[：:](.*?)(?=\n\n|\n【|$)',
            r'例如[：:](.*?)(?=\n\n|\n【|$)',
            r'Example[：:](.*?)(?=\n\n|\n【|$)',
        ]
        
        found_example = False
        for pattern in example_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                print(f"✅ 找到範例段落:")
                print(f"Pattern: {pattern}")
                print(f"\n{match.group(1)[:500]}\n")
                found_example = True
                break
        
        if not found_example:
            print("❌ 未找到任何範例段落\n")
            print("前 500 字元:")
            print(content[:500])
    else:
        print("❌ 資料庫中未找到 MASTER_SPEC")
