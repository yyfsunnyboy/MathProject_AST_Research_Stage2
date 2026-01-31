#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重新生成 Ab3 測試腳本
"""

import sys
import os
sys.path.insert(0, '.')
os.environ['FLASK_ENV'] = 'production'

# 設置 Flask APP
from app import create_app
from core.code_generator import auto_generate_skill_code
from models import db, SkillInfo
import json

print("=" * 70)
print("【重新生成 Ab3】gh_ApplicationsOfDerivatives")
print("=" * 70)

try:
    # 創建 Flask 應用上下文
    app = create_app()
    with app.app_context():
        # 查詢技能
        skill = db.session.query(SkillInfo).filter_by(
            english_name='gh_ApplicationsOfDerivatives'
        ).first()
        
        if not skill:
            print("❌ 技能未找到")
            sys.exit(1)
        
        print(f"\n✅ 找到技能：{skill.english_name}")
        print(f"   中文名稱：{skill.name_zh}")
        
        # 執行生成（Ab3 = Healer 完全啟用）
        print("\n🔄 開始生成 Ab3（Healer 完全啟用）...")
        print("-" * 70)
        
        result = auto_generate_skill_code(
            skill_id=skill.english_name,
            ablation_id=3,  # Ab3 = Full Healing
            use_regex_healer=True,
            coder_model='gemini-2.5-flash'
        )
        
        print("-" * 70)
        print("\n✅ 生成完成！")
        
        # 檢查結果
        if result['success']:
            print(f"✅ 生成成功！")
            print(f"   檔案路徑：{result['file_path']}")
            print(f"   代碼行數：{result.get('line_count', 'N/A')}")
            print(f"   修復統計：Basic={result.get('basic_fixes', 0)}, Regex={result.get('regex_fixes', 0)}, AST={result.get('ast_fixes', 0)}")
            
            # 嘗試編譯
            try:
                with open(result['file_path'], 'r', encoding='utf-8') as f:
                    code = f.read()
                compile(code, result['file_path'], 'exec')
                print(f"✅ 代碼可以編譯")
            except SyntaxError as e:
                print(f"❌ 代碼有語法錯誤：{e}")
        else:
            print(f"❌ 生成失敗")
            print(f"   錯誤：{result.get('error', 'Unknown error')}")
            
except Exception as e:
    print(f"❌ 發生異常：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("完成！")
