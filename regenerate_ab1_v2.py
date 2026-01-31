"""
重新生成 Ab1，並立即測試一個樣本
"""
from app import app
from core.architect_v01 import generate_code

print("="*70)
print("🧪 生成 Ab1 V2 (使用真實課本例題)")
print("="*70)

with app.app_context():
    result = generate_code(
        skill_id='gh_ApplicationsOfDerivatives',
        model_choice='gemini',
        ablation_id=1,
        custom_output_path='skills/gh_ApplicationsOfDerivatives_Cloud_Ab1_V2.py'
    )
    
    if result.get('success'):
        print(f"\n✅ Ab1 V2 生成成功！")
        print(f"📂 {result['output_path']}")
        
        # Step 2: 測試生成題目
        print("\n" + "="*70)
        print("🧪 測試生成題目")
        print("="*70)
        
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "test_skill",
            result['output_path']
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        question = module.generate()
        print(f"\n✅ 題目生成成功！")
        print(f"\n題目: {question['question_text']}")
        print(f"答案: {question.get('correct_answer', question.get('answer', 'N/A'))}")
    else:
        print(f"\n❌ 生成失敗: {result.get('error', 'Unknown error')}")
