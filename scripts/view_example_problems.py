#!/usr/bin/env python3
"""查看實際的課本例題內容"""
import sqlite3

conn = sqlite3.connect('instance/kumon_math.db')
cursor = conn.cursor()

# 查看幾個有較多例題的技能
test_skills = [
    'gh_ApplicationsOfDerivatives',
    'gh_AreaBetweenCurves', 
    'gh_ApplicationsOfLogarithmicFunctions',
    'jh_數學1上_PositiveAndNegativeNumbers'
]

for skill_id in test_skills:
    cursor.execute('''
        SELECT problem_text, problem_type, detailed_solution, difficulty_level
        FROM textbook_examples
        WHERE skill_id = ?
        LIMIT 1
    ''', (skill_id,))
    
    result = cursor.fetchone()
    if result:
        problem_text, problem_type, solution, difficulty = result
        print(f"\n{'='*80}")
        print(f"技能: {skill_id}")
        print(f"題型: {problem_type} | 難度: {difficulty}")
        print(f"{'='*80}")
        print(f"\n【題目】\n{problem_text[:300]}")
        print(f"\n【解答】\n{solution[:300]}")
        print()

conn.close()
