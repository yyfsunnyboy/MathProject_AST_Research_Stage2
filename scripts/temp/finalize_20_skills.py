#!/usr/bin/env python3
"""
最終確認：基於 backup_20260129 的代碼品質
選出 20 個最值得做的技能
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("instance/kumon_math.db")

# 從分析中獲得的高品質技能
TOP_SKILLS = [
    'jh_數學2下_FunctionGraph',
    'jh_數學2下_FunctionValue', 
    'jh_數學2下_NthTermOfGeometricSequence',
    'jh_數學2上_FourOperationsOfRadicals',
    'jh_數學2上_BasicPropertiesOfRadicalOperations',
    'jh_數學1下_DrawingGraphsOfTwoVariableLinearEquations',
    'jh_數學2下_GeometricSequence',
    'jh_數學1下_RectangularCoordinatePlaneAndCoordinateRepresentation',
    'jh_數學2上_PolynomialDivision',
    'jh_數學2下_GeometricMean',
    'jh_數學1上_IntegerAdditionOperation',
    'jh_數學2上_WordProblems',
    'jh_數學2上_PolynomialAdditionAndSubtraction',
    'jh_數學1上_CommonDivisibilityRules',
    'jh_數學2上_PolynomialMultiplication',
]

# 需要再選 5 個
ADDITIONAL_SKILLS = [
    'jh_數學1上_FractionAdditionAndSubtraction',
    'jh_數學1上_FractionMultiplication',
    'jh_數學1上_FractionDivision',
    'jh_數學2上_FourArithmeticOperationsOfIntegers',
    'jh_數學2上_FactorizationByMultiplicationFormulas',
]

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

print("🏆 最終確認 20 支技能（基於 backup_20260129 的成功代碼）\n")
print("=" * 100)

# Domain 分類
DOMAIN_MAP = {
    # 四則運算與基礎
    'jh_數學1上_IntegerAdditionOperation': 'arithmetic_basic',
    'jh_數學1上_FractionAdditionAndSubtraction': 'arithmetic_basic',
    'jh_數學1上_FractionMultiplication': 'arithmetic_basic',
    'jh_數學1上_FractionDivision': 'arithmetic_basic',
    'jh_數學1上_CommonDivisibilityRules': 'arithmetic_basic',
    
    # 代數與方程
    'jh_數學1下_DrawingGraphsOfTwoVariableLinearEquations': 'algebra',
    'jh_數學1下_RectangularCoordinatePlaneAndCoordinateRepresentation': 'algebra',
    'jh_數學1下_GraphOfTwoVariableLinearEquation': 'algebra',
    'jh_數學2上_PolynomialAdditionAndSubtraction': 'algebra',
    'jh_數學2上_PolynomialMultiplication': 'algebra',
    'jh_數學2上_PolynomialDivision': 'algebra',
    
    # 根號與冪
    'jh_數學2上_FourOperationsOfRadicals': 'radical_powers',
    'jh_數學2上_BasicPropertiesOfRadicalOperations': 'radical_powers',
    
    # 分解與因式
    'jh_數學2上_FactorizationByMultiplicationFormulas': 'factorization',
    
    # 數列與函數
    'jh_數學2下_FunctionGraph': 'functions_sequences',
    'jh_數學2下_FunctionValue': 'functions_sequences',
    'jh_數學2下_NthTermOfGeometricSequence': 'functions_sequences',
    'jh_數學2下_GeometricSequence': 'functions_sequences',
    'jh_數學2下_GeometricMean': 'functions_sequences',
    
    # 應用問題
    'jh_數學2上_WordProblems': 'applications',
}

final_20 = TOP_SKILLS + ADDITIONAL_SKILLS

print(f"【最終選定的 20 支技能】\n")

# 按 domain 分類輸出
from collections import defaultdict
by_domain = defaultdict(list)

for skill_id in final_20:
    # 查詢例題數
    db_skill_id = skill_id  # 資料庫中直接用這個名字
    cursor.execute('SELECT COUNT(*) FROM textbook_examples WHERE skill_id = ?', (db_skill_id,))
    count = cursor.fetchone()[0]
    
    # 查詢代碼行數
    backup_path = Path(f"skills/backup_20260129/{skill_id}.py")
    if backup_path.exists():
        with open(backup_path, 'r', encoding='utf-8') as f:
            lines = len(f.readlines())
    else:
        lines = 0
    
    domain = DOMAIN_MAP.get(skill_id, 'other')
    by_domain[domain].append((skill_id, count, lines))

# 按 domain 輸出
for domain in sorted(by_domain.keys()):
    skills = by_domain[domain]
    print(f"\n【{domain.upper()}】({len(skills)} 個)")
    print("-" * 100)
    
    for i, (skill_id, examples, lines) in enumerate(sorted(skills, key=lambda x: -x[1]), 1):
        status = "✓" if examples > 0 else "!"
        print(f"{status} {i}. {skill_id}")
        print(f"       行數: {lines} | 例題: {examples} 個")

conn.close()

print("\n" + "=" * 100)
print("【Domain 分類方案】\n")

domains = {
    'arithmetic_basic': '基礎四則運算',
    'algebra': '代數與方程',
    'radical_powers': '根號與冪',
    'factorization': '因式分解',
    'functions_sequences': '函數與數列',
    'applications': '應用問題',
}

for code, name in sorted(domains.items()):
    count = len([s for s in by_domain.values() if any(code in s for s in [str(x[0]) for x in by_domain[code]])])
    # 重新計算
    count = 0
    for domain_key in by_domain:
        if code in domain_key:
            count += len(by_domain[domain_key])
    
    if count > 0:
        print(f"  • {code}: {name}")

print("\n\n✅ 最終確認的 20 個 skill_id (按推薦順序)：")
print("-" * 100)

# 輸出最終列表
print("\n".join([f"{i+1:2d}. {skill}" for i, skill in enumerate(final_20)]))

# 保存到文件
with open('FINAL_20_SKILLS.txt', 'w', encoding='utf-8') as f:
    f.write("【最終確認的 20 支技能】\n")
    f.write("=" * 100 + "\n\n")
    
    for domain in sorted(by_domain.keys()):
        skills = sorted(by_domain[domain], key=lambda x: -x[1])
        f.write(f"【{domain.upper()}】({len(skills)} 個)\n")
        f.write("-" * 100 + "\n")
        for skill_id, examples, lines in skills:
            f.write(f"{skill_id}, {examples}, {lines}\n")
        f.write("\n")

print("\n\n✅ 已保存到 FINAL_20_SKILLS.txt")
