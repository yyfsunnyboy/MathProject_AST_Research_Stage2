from app import app
from models import SkillGenCodePrompt
import re

def _extract_example_from_spec(master_spec: str) -> str:
    """模擬實際的範例提取邏輯"""
    if not master_spec or len(master_spec) < 20:
        return "範例：計算 3 + 5 = ?"
    
    # 策略 1: 尋找「範例」或「例如」段落
    example_patterns = [
        r'【範例】(.*?)(?=【|$)',
        r'範例[：:](.*?)(?=\n\n|\n【|$)',
        r'例如[：:](.*?)(?=\n\n|\n【|$)',
        r'Example[：:](.*?)(?=\n\n|\n【|$)',
    ]
    
    for pattern in example_patterns:
        match = re.search(pattern, master_spec, re.DOTALL | re.IGNORECASE)
        if match:
            example_text = match.group(1).strip()
            if len(example_text) > 200:
                example_text = example_text[:200] + "..."
            example_text = example_text.replace('{', '{{').replace('}', '}}')
            return example_text
    
    # 策略 2: 如果找不到範例段落，提取前 150 字元作為參考
    first_section = master_spec[:150].strip()
    if first_section:
        first_section = first_section.replace('{', '{{').replace('}', '}}')
        return first_section + "..."
    
    # 策略 3: 預設範例
    return "範例：計算 3 + 5 = ?"

with app.app_context():
    spec = SkillGenCodePrompt.query.filter_by(
        skill_id='gh_ApplicationsOfDerivatives',
        prompt_type='MASTER_SPEC'
    ).order_by(SkillGenCodePrompt.created_at.desc()).first()
    
    if spec:
        content = spec.prompt_content
        extracted = _extract_example_from_spec(content)
        
        print("=== Ab1 實際傳入的 textbook_example ===\n")
        print(extracted)
        print("\n" + "="*70)
        print("\n這是從 MASTER_SPEC 前 150 字元提取的（因為沒有找到範例段落）")
        print("Gemini 看到的是：技術規格，不是課本例題")
