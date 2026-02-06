#!/usr/bin/env python3
"""查看各種題型的課本例題 - 了解我們要生成什麼"""
import sqlite3

conn = sqlite3.connect('instance/kumon_math.db')
cursor = conn.cursor()

# 查看不同領域的技能例題
skills_by_category = {
    "計算型 - 導數應用": "gh_ApplicationsOfDerivatives",
    "計算型 - 積分面積": "gh_AreaBetweenCurves",
    "計算型 - 對數方程": "gh_ApplicationsOfLogarithmicFunctions",
    "文字題 - 正負數": "jh_數學1上_PositiveAndNegativeNumbers",
}

# 添加一些幾何/圖形相關的技能
cursor.execute('''
    SELECT DISTINCT skill_id FROM textbook_examples 
    WHERE skill_id LIKE 'gm_%' OR skill_id LIKE 'gh_%geo%' OR skill_id LIKE 'gh_%shape%'
    LIMIT 5
''')
geometry_skills = cursor.fetchall()

for skill_id, in geometry_skills:
    cursor.execute('SELECT COUNT(*) FROM textbook_examples WHERE skill_id = ?', (skill_id,))
    count = cursor.fetchone()[0]
    if count > 0:
        skills_by_category[f"幾何 - {skill_id[:20]}"] = skill_id

print("查看不同題型的課本例題")
print("="*90)

for category, skill_id in skills_by_category.items():
    cursor.execute('''
        SELECT problem_text, problem_type, detailed_solution, difficulty_level
        FROM textbook_examples
        WHERE skill_id = ?
        LIMIT 1
    ''', (skill_id,))
    
    result = cursor.fetchone()
    if result:
        problem_text, problem_type, solution, difficulty = result
        print(f"\n【{category}】")
        print(f"技能: {skill_id}")
        print(f"題型: {problem_type} | 難度: {difficulty}")
        print(f"-" * 90)
        print(f"題目: {problem_text[:150]}..." if len(problem_text) > 150 else f"題目: {problem_text}")
        print(f"解答: {solution[:150]}..." if len(solution) > 150 else f"解答: {solution}")

conn.close()
