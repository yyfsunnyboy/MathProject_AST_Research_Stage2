#!/usr/bin/env python3
"""
查看推薦技能的實際課本例題內容
理解我們要生成的真正題型
"""
import sqlite3
import json
from pathlib import Path

# 20個推薦的技能（來自 analyze_db_direct.py 的輸出）
RECOMMENDED_SKILLS = [
    "gh_DistancesRelatedToLines",
    "gh_GeometricApplicationsOfEllipse", 
    "gh_AreaBetweenCurves",
    "gh_ParametricEquationsAndVectorInPlane",
    "gh_DefiniteIntegralApplications",
    "gh_HyperbolicFunctions",
    "gh_SequencesAndSeries",
    "gh_PropertiesOfPowers",
    "gh_BasicTrigonometry",
    "gh_DefiniteIntegrals",
    "gh_UndefiniteIntegrals",
    "gh_DerivativeApplications",
    "gm_SineAndCosineRules",
    "gm_CircleIntersections",
    "gm_AreaOfTriangle",
    "gm_SolidGeometry",
    "gm_PointAndLineDistance",
    "gm_CoordinateGeometry",
    "gm_AngleProblems",
    "gm_TriangleProperties"
]

DB_PATH = Path("E:/Python/MathProject_AST_Research/instance/kumon_math.db")

def examine_skill_examples(skill_id: str, limit: int = 3):
    """檢查某個技能的課本例題"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 獲取技能信息
    cursor.execute("""
        SELECT skill_id, skill_name, domain, domain_confidence
        FROM skill_info
        WHERE skill_id = ?
    """, (skill_id,))
    skill = cursor.fetchone()
    
    if not skill:
        print(f"❌ 找不到技能: {skill_id}")
        conn.close()
        return None
    
    print(f"\n{'='*80}")
    print(f"技能: {skill['skill_name']} ({skill_id})")
    print(f"Domain: {skill['domain']} (confidence: {skill['domain_confidence']})")
    print(f"{'='*80}")
    
    # 獲取例題
    cursor.execute("""
        SELECT rowid, problem_text, detailed_solution, difficulty_level
        FROM textbook_example
        WHERE skill_id = ?
        LIMIT ?
    """, (skill_id, limit))
    
    examples = cursor.fetchall()
    print(f"共有 {cursor.execute('SELECT COUNT(*) FROM textbook_example WHERE skill_id = ?', (skill_id,)).fetchone()[0]} 個例題\n")
    
    for idx, example in enumerate(examples, 1):
        print(f"\n【例題 #{idx}】(難度: {example['difficulty_level']})")
        print(f"\n題目:\n{example['problem_text']}")
        print(f"\n解答:\n{example['detailed_solution'][:300]}..." if len(example['detailed_solution']) > 300 else f"\n解答:\n{example['detailed_solution']}")
        print(f"\n{'-'*80}")
    
    conn.close()
    return skill

def main():
    """檢查前5個推薦技能"""
    print("\n🔍 檢查推薦技能的實際課本例題\n")
    
    examined_skills = []
    for skill_id in RECOMMENDED_SKILLS[:5]:  # 先檢查前5個
        try:
            skill = examine_skill_examples(skill_id, limit=2)
            if skill:
                examined_skills.append({
                    'skill_id': skill_id,
                    'skill_name': skill['skill_name'],
                    'domain': skill['domain'],
                    'example_count': 3
                })
        except Exception as e:
            print(f"❌ 錯誤處理 {skill_id}: {e}")
    
    # 統計摘要
    print("\n\n" + "="*80)
    print("📊 技能摘要")
    print("="*80)
    for skill in examined_skills:
        print(f"✓ {skill['skill_name']} ({skill['skill_id']}) - Domain: {skill['domain']}")

if __name__ == "__main__":
    main()
