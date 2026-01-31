# -*- coding: utf-8 -*-
"""
更新 Ablation Setting 的名稱以符合新的實驗設計
"""
import sys
import os

# 添加專案根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from models import db, AblationSetting

def update_ablation_names():
    """更新 Ablation 名稱以符合新的學術標準定義"""
    
    app = create_app()
    with app.app_context():
        # 更新 Ab1
        ab1 = AblationSetting.query.get(1)
        if ab1:
            ab1.name = 'Bare'
            ab1.description = '天真使用者 (Naive User) - Bare Prompt + 無工具 + 無 Healer'
            print(f"✅ Ab1 更新: {ab1.name}")
        
        # 更新 Ab2
        ab2 = AblationSetting.query.get(2)
        if ab2:
            old_name = ab2.name
            ab2.name = 'Engineered'
            ab2.description = '專業架構師 (Expert Architect) - MASTER_SPEC + 有工具 + 無 Healer'
            print(f"✅ Ab2 更新: {old_name} → {ab2.name}")
        
        # 更新 Ab3
        ab3 = AblationSetting.query.get(3)
        if ab3:
            ab3.name = 'Full_Healing'
            ab3.description = '自動化系統 (Autonomous System) - MASTER_SPEC + 有工具 + 有 Healer'
            print(f"✅ Ab3 更新: {ab3.name}")
        
        db.session.commit()
        print("\n🎉 Ablation 名稱更新完成！")
        
        # 顯示當前設定
        print("\n📊 當前 Ablation Settings:")
        for ab in AblationSetting.query.all():
            print(f"   ID={ab.id}: {ab.name}")
            print(f"      Regex={ab.use_regex}, AST={ab.use_ast}")
            print(f"      描述: {ab.description}")
            print()

if __name__ == '__main__':
    update_ablation_names()
