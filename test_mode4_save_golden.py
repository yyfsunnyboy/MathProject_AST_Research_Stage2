# -*- coding: utf-8 -*-
"""
測試模式 4 自動保存 Golden Prompts
驗證系統能在動態生成 Prompt 的同時保存到文件
"""

import sys
import os
import shutil

# 設置路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app
from core.code_generator import _build_prompt

def test_save_golden_prompt():
    """測試自動保存 Golden Prompt 功能"""
    
    print("="*60)
    print("🧪 測試模式 4：自動保存 Golden Prompts")
    print("="*60)
    
    # 測試技能
    skill_id = "jh_LinearEquations"
    
    # 準備測試環境
    golden_prompt_dir = os.path.join(
        project_root,
        'experiments', 'golden_prompts', 'temp'
    )
    
    # 備份現有文件（如果存在）
    backup_files = {}
    for ablation_id in [1, 2]:
        filename = f'{skill_id}_Ab{ablation_id}.txt'
        filepath = os.path.join(golden_prompt_dir, filename)
        if os.path.exists(filepath):
            backup_path = filepath + '.backup'
            shutil.copy2(filepath, backup_path)
            backup_files[filepath] = backup_path
            print(f"📦 已備份: {filename}")
            # 刪除原文件以測試生成
            os.remove(filepath)
    
    # 建立 Flask App Context
    app = create_app()
    with app.app_context():
        
        # 測試 1: Ab1 自動保存
        print("\n【測試 1】Ab1 自動保存 Golden Prompt")
        print("-" * 60)
        
        ab1_path = os.path.join(golden_prompt_dir, f'{skill_id}_Ab1.txt')
        
        # 確認文件不存在
        assert not os.path.exists(ab1_path), "測試前文件應該不存在"
        
        prompt_ab1, _, _ = _build_prompt(
            skill_id=skill_id,
            ablation_id=1,
            db_master_spec="測試規格書",
            use_golden_prompt=False,
            save_golden_prompt=True
        )
        
        # 驗證文件已生成
        if os.path.exists(ab1_path):
            print(f"✅ Ab1 Golden Prompt 已保存")
            with open(ab1_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()
            
            if saved_content == prompt_ab1:
                print(f"✅ 保存內容與生成內容一致")
                print(f"   長度: {len(saved_content)} 字符")
            else:
                print(f"❌ 保存內容與生成內容不一致！")
        else:
            print(f"❌ Ab1 Golden Prompt 未保存")
        
        # 測試 2: Ab2 自動保存
        print("\n【測試 2】Ab2 自動保存 Golden Prompt")
        print("-" * 60)
        
        ab2_path = os.path.join(golden_prompt_dir, f'{skill_id}_Ab2.txt')
        
        # 確認文件不存在
        assert not os.path.exists(ab2_path), "測試前文件應該不存在"
        
        prompt_ab2, _, _ = _build_prompt(
            skill_id=skill_id,
            ablation_id=2,
            db_master_spec="測試規格書",
            use_golden_prompt=False,
            save_golden_prompt=True
        )
        
        # 驗證文件已生成
        if os.path.exists(ab2_path):
            print(f"✅ Ab2 Golden Prompt 已保存")
            with open(ab2_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()
            
            if saved_content == prompt_ab2:
                print(f"✅ 保存內容與生成內容一致")
                print(f"   長度: {len(saved_content)} 字符")
            else:
                print(f"❌ 保存內容與生成內容不一致！")
        else:
            print(f"❌ Ab2 Golden Prompt 未保存")
        
        # 測試 3: Ab3 也應該保存到 Ab2 文件（共用）
        print("\n【測試 3】Ab3 保存到 Ab2 文件（共用測試）")
        print("-" * 60)
        
        # 先記錄 Ab2 文件的修改時間
        ab2_mtime_before = os.path.getmtime(ab2_path)
        
        # 等待 1 秒確保時間戳不同
        import time
        time.sleep(1)
        
        prompt_ab3, _, _ = _build_prompt(
            skill_id=skill_id,
            ablation_id=3,
            db_master_spec="測試規格書",
            use_golden_prompt=False,
            save_golden_prompt=True
        )
        
        # 檢查 Ab2 文件是否被更新
        ab2_mtime_after = os.path.getmtime(ab2_path)
        
        if ab2_mtime_after > ab2_mtime_before:
            print(f"✅ Ab3 成功更新 Ab2 文件（符合共用設計）")
            
            with open(ab2_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()
            
            if saved_content == prompt_ab3:
                print(f"✅ Ab3 保存內容正確")
            else:
                print(f"❌ Ab3 保存內容不正確")
        else:
            print(f"❌ Ab3 未更新 Ab2 文件")
        
        # 測試 4: 不保存模式
        print("\n【測試 4】save_golden_prompt=False 時不保存")
        print("-" * 60)
        
        # 刪除測試文件
        if os.path.exists(ab1_path):
            os.remove(ab1_path)
        
        prompt_no_save, _, _ = _build_prompt(
            skill_id=skill_id,
            ablation_id=1,
            db_master_spec="測試規格書",
            use_golden_prompt=False,
            save_golden_prompt=False
        )
        
        if not os.path.exists(ab1_path):
            print(f"✅ save_golden_prompt=False 時確實不保存文件")
        else:
            print(f"❌ save_golden_prompt=False 時仍然保存了文件！")
    
    # 恢復備份文件
    print("\n" + "="*60)
    print("🔄 恢復備份文件...")
    print("="*60)
    
    for original_path, backup_path in backup_files.items():
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, original_path)
            os.remove(backup_path)
            print(f"✅ 已恢復: {os.path.basename(original_path)}")
    
    print("\n" + "="*60)
    print("測試完成")
    print("="*60)

if __name__ == "__main__":
    test_save_golden_prompt()
