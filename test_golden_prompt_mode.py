# -*- coding: utf-8 -*-
"""
測試 Golden Prompt 模式（實驗模式 2）
驗證系統能正確讀取固定的 Prompt 文件而不是動態生成
"""

import sys
import os

# 設置路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app
from core.code_generator import _build_prompt

def test_golden_prompt_loading():
    """測試 Golden Prompt 讀取功能"""
    
    print("="*60)
    print("🧪 測試 Golden Prompt 模式")
    print("="*60)
    
    # 測試技能
    skill_id = "gh_ApplicationsOfDerivatives"
    
    # 建立 Flask App Context
    app = create_app()
    with app.app_context():
        
        # 測試 1: 動態生成模式（原有邏輯）
        print("\n【測試 1】動態生成模式 (use_golden_prompt=False)")
        print("-" * 60)
        
        prompt_dynamic, topic, example = _build_prompt(
            skill_id=skill_id,
            ablation_id=2,
            db_master_spec="測試規格書",
            use_golden_prompt=False
        )
        
        print(f"✅ 動態生成成功")
        print(f"   長度: {len(prompt_dynamic)} 字符")
        print(f"   前 100 字: {prompt_dynamic[:100]}...")
        
        # 測試 2: Golden Prompt 模式（新邏輯）
        print("\n【測試 2】Golden Prompt 模式 (use_golden_prompt=True)")
        print("-" * 60)
        
        # 檢查文件是否存在
        golden_prompt_path = os.path.join(
            project_root,
            'experiments', 'golden_prompts', 'temp',
            f'{skill_id}_Ab2.txt'
        )
        
        print(f"📄 預期路徑: {golden_prompt_path}")
        
        if os.path.exists(golden_prompt_path):
            print(f"✅ Golden Prompt 文件存在")
            
            prompt_golden, _, _ = _build_prompt(
                skill_id=skill_id,
                ablation_id=2,
                db_master_spec="測試規格書（應該被忽略）",
                use_golden_prompt=True
            )
            
            print(f"✅ Golden Prompt 讀取成功")
            print(f"   長度: {len(prompt_golden)} 字符")
            print(f"   前 100 字: {prompt_golden[:100]}...")
            
            # 測試 3: 比較兩者是否不同
            print("\n【測試 3】比較動態生成 vs Golden Prompt")
            print("-" * 60)
            
            if prompt_dynamic == prompt_golden:
                print("⚠️ 兩者內容相同（可能是巧合）")
            else:
                print("✅ 兩者內容不同（符合預期）")
                
            # 測試 4: Ab2/Ab3 共用邏輯
            print("\n【測試 4】Ab2/Ab3 共用測試")
            print("-" * 60)
            
            prompt_ab2, _, _ = _build_prompt(
                skill_id=skill_id,
                ablation_id=2,
                db_master_spec="測試規格書",
                use_golden_prompt=True
            )
            
            prompt_ab3, _, _ = _build_prompt(
                skill_id=skill_id,
                ablation_id=3,
                db_master_spec="測試規格書",
                use_golden_prompt=True
            )
            
            if prompt_ab2 == prompt_ab3:
                print("✅ Ab2 和 Ab3 使用同一個 Golden Prompt（符合預期）")
            else:
                print("❌ Ab2 和 Ab3 使用不同的 Prompt（不符合預期）")
                
        else:
            print(f"❌ Golden Prompt 文件不存在")
            print(f"   請先執行以下步驟：")
            print(f"   1. 生成一次成功的 Ab2 Prompt")
            print(f"   2. 將其保存到: {golden_prompt_path}")
    
    print("\n" + "="*60)
    print("測試完成")
    print("="*60)

if __name__ == "__main__":
    test_golden_prompt_loading()
