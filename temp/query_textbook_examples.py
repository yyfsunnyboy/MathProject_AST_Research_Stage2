#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查询指定技能的课本例题
"""
import sys
import os

# 路径修正
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app
from models import db, TextbookExample

# 创建应用上下文
app = create_app()
with app.app_context():
    # 查询 FourArithmeticOperationsOfNumbers 技能的例题
    skill_id = 'jh_數學1上_FourArithmeticOperationsOfNumbers'
    examples = TextbookExample.query.filter_by(skill_id=skill_id).order_by(
        TextbookExample.id.asc()
    ).all()
    
    print(f"技能: {skill_id}")
    print(f"找到 {len(examples)} 个例题\n")
    
    for idx, ex in enumerate(examples[:3], 1):  # 显示前3个
        print(f"--- 例题 {idx} (ID={ex.id}) ---")
        print(f"问题文本: {ex.problem_text}")
        print(f"答案: {ex.correct_answer}")
        print()
    
    if len(examples) > 0:
        print(f"\n✅ 第一个例题:")
        first_ex = examples[0]
        print(f"问题: {first_ex.problem_text}")
        print(f"答案: {first_ex.correct_answer}")
