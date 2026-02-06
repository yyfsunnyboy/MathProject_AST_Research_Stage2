"""
測試修正後的 Ab1 代碼生成（使用真實課本例題）
"""
from app import app
from core.code_generator import generate_skill_code_v01

with app.app_context():
    print("="*70)
    print("🧪 測試 Ab1 (V47.14) - 使用真實課本例題")
    print("="*70)
    
    result = generate_skill_code_v01(
        skill_id='gh_ApplicationsOfDerivatives',
        model_name='gemini',
        ablation_id=1,
        custom_output_path='skills/gh_ApplicationsOfDerivatives_Cloud_Ab1_V2.py'
    )
    
    if result['success']:
        print("\n✅ 代碼生成成功！")
        print(f"📂 輸出位置: {result['output_path']}")
    else:
        print(f"\n❌ 生成失敗: {result.get('error', 'Unknown error')}")
