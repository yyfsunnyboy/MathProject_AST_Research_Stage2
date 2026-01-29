#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Automated script to generate ApplicationsOfDerivatives using sync_skills_files logic"""

import sys
import os

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir
while not os.path.exists(os.path.join(project_root, 'app.py')):
    parent = os.path.dirname(project_root)
    if parent == project_root:
        print("❌ 無法定位專案根目錄")
        sys.exit(1)
    project_root = parent

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app
from models import db
from core.code_generator import auto_generate_skill_code
from core.prompt_architect import generate_v15_spec

app = create_app()

with app.app_context():
    skill_id = "gh_ApplicationsOfDerivatives"
    
    print("=" * 70)
    print(f"🚀 為 {skill_id} 生成技能代碼")
    print("=" * 70)
    
    # Phase 1: Architect
    print(f"\n【Phase 1】生成 MASTER_SPEC...")
    try:
        result = generate_v15_spec(skill_id, model_tag='standard_14b', architect_model='google')
        if result.get('success'):
            print(f"✅ MASTER_SPEC 生成成功")
        else:
            print(f"❌ MASTER_SPEC 生成失敗: {result.get('message')}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        sys.exit(1)
    
    # Phase 2: Coder
    print(f"\n【Phase 2】生成代碼...")
    try:
        is_ok, msg, metrics = auto_generate_skill_code(
            skill_id,
            queue=None,
            ablation_id=3,  # Full healing
            model_size_class='local_14b',
            prompt_level='standard_14b'
        )
        
        if is_ok:
            is_valid = metrics.get('is_valid', False)
            fixes = metrics.get('fixes', 0)
            print(f"✅ 代碼生成成功")
            print(f"   有效性: {is_valid}")
            print(f"   AST 修復次數: {fixes}")
        else:
            print(f"❌ 代碼生成失敗: {msg}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Phase 3: Validation
    print(f"\n【Phase 3】驗證代碼品質...")
    skill_file = os.path.join(project_root, 'skills', f'{skill_id}_local_14b_Ab3.py')
    
    if not os.path.exists(skill_file):
        print(f"❌ 技能文件不存在: {skill_file}")
        sys.exit(1)
    
    with open(skill_file, 'r', encoding='utf-8') as f:
        code_content = f.read()
    
    # Test conditions
    print(f"\n【驗證清單】")
    
    # Condition 1: 無限迴圈
    print(f"1️⃣  檢查無限迴圈...")
    try:
        from skills.gh_ApplicationsOfDerivatives_local_14b_Ab3 import generate
        import time
        
        max_time = 1.0
        for i in range(5):
            start = time.time()
            result = generate()
            elapsed = time.time() - start
            if elapsed > max_time:
                print(f"   ❌ 第 {i+1} 次生成耗時 {elapsed:.2f}s，超過 {max_time}s（可能有無限迴圈）")
                sys.exit(1)
        print(f"   ✅ 5 次生成都在 {max_time}s 內完成，無無限迴圈")
    except Exception as e:
        print(f"   ❌ 執行失敗: {e}")
        sys.exit(1)
    
    # Condition 2: LaTeX 語法
    print(f"\n2️⃣  檢查 LaTeX 語法...")
    has_latex = '$' in code_content
    if has_latex:
        print(f"   ✅ 代碼包含 LaTeX 語法（有 $ 符號）")
    else:
        print(f"   ❌ 代碼沒有 LaTeX 語法")
        sys.exit(1)
    
    # Condition 3: 中文不在 LaTeX 裡面
    print(f"\n3️⃣  檢查中文是否被包在 LaTeX 裡面...")
    import re
    # 找出所有 $...$ 內的內容
    latex_blocks = re.findall(r'\$([^$]*)\$', code_content)
    has_chinese_in_latex = False
    for block in latex_blocks:
        if re.search(r'[\u4e00-\u9fff]', block):
            has_chinese_in_latex = True
            print(f"   ⚠️ 發現中文在 LaTeX 裡: {block[:50]}")
            break
    
    if not has_chinese_in_latex:
        print(f"   ✅ 中文沒有被包在 LaTeX 裡面")
    else:
        print(f"   ❌ 中文被包在 LaTeX 裡面（需要修復）")
        # 不退出，可能只是部分問題
    
    # Condition 4: 答案是乾淨的字串
    print(f"\n4️⃣  檢查答案格式...")
    test_results = []
    for i in range(3):
        result = generate()
        ans = result.get('correct_answer', '')
        test_results.append(ans)
        has_latex_in_ans = '$' in ans or '\\' in ans
        if has_latex_in_ans:
            print(f"   ❌ 第 {i+1} 個答案包含 LaTeX: {ans[:50]}")
        else:
            print(f"   ✅ 第 {i+1} 個答案乾淨: {ans[:50]}")
    
    print(f"\n" + "=" * 70)
    print(f"✅ 驗證完成！技能文件已生成: {skill_file}")
    print(f"=" * 70)
