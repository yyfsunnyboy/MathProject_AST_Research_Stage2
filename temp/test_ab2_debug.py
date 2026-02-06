# -*- coding: utf-8 -*-
"""測試 Ab2 生成並診斷問題"""

import sys
import os
sys.path.insert(0, '.')

from app import create_app

def test_ab2_generation():
    app = create_app()
    with app.app_context():
        from core.code_generator import auto_generate_skill_code
        
        print("="*60)
        print("🧪 測試 Ab2 生成")
        print("="*60)
        
        # 設置詳細日誌
        os.environ['HEALER_VERBOSE'] = '2'
        
        try:
            is_ok, msg, metrics = auto_generate_skill_code(
                'gh_ApplicationsOfDerivatives',
                ablation_id=2,
                model_size_class='14b',
                prompt_level='Engineered-Only'
            )
            
            print(f"\n成功: {is_ok}")
            print(f"訊息: {msg}")
            print(f"\n指標: {metrics}")
            
            if not is_ok:
                print("\n❌ 生成失敗")
                print("錯誤訊息:", msg)
        except Exception as e:
            print(f"\n❌ 異常: {type(e).__name__}")
            print(f"詳情: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_ab2_generation()
