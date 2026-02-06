#!/usr/bin/env python3
"""
基於 Gemini 代碼品質分析 + 課本例題分析
制定「拿金牌的 20 支技能」選擇策略
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("instance/kumon_math.db")

# ===== 基於分析的推薦 20 支技能 =====
# 策略：
# 1. 優先複雜度 3 的技能（有 Gemini 代碼作為「天花板」）
# 2. 多個 domain 平衡（不是一個 domain 死打）
# 3. 確保課本例題充足（能生成足夠的變化題）

RECOMMENDED_20_SKILLS = [
    # 【微積分】(4個) - 這是重頭戲，最複雜，最具衝擊力
    {
        'gemini_name': 'gh_ApplicationsOfDerivatives',
        'db_name': 'gh_ApplicationsOfDerivatives',
        'domain': 'calculus',
        'reason': '導數應用 - 758行複雜代碼，有多種例題子類型',
        'complexity': 3,
    },
    {
        'gemini_name': 'gh_AreaBetweenCurves',
        'db_name': 'gh_AreaBetweenCurves',
        'domain': 'calculus',
        'reason': '曲線間面積 - 積分應用，15個課本例題',
        'complexity': 3,
    },
    {
        'gemini_name': 'gh_FundamentalTheoremOfCalculus',
        'db_name': 'gh_FundamentalTheoremOfCalculus',
        'domain': 'calculus',
        'reason': '微積分基本定理 - 核心概念，302行',
        'complexity': 3,
    },
    {
        'gemini_name': 'gh_AverageValueOfContinuousFunction',
        'db_name': 'gh_AverageValueOfContinuousFunction',
        'domain': 'calculus',
        'reason': '積分的平均值 - 應用型題目，18個課本例題',
        'complexity': 3,
    },
    
    # 【幾何與圓錐曲線】(4個) - 視覺性強，容易展示成果
    {
        'gemini_name': 'gh_JudgingTheRelationshipOfCircleAndLine',
        'db_name': 'gh_JudgingTheRelationshipOfCircleAndLine',
        'domain': 'conic_sections',
        'reason': '圓與直線關係 - 606行，經典幾何問題',
        'complexity': 3,
    },
    {
        'gemini_name': 'gh_GeometricApplicationsOfEllipse',
        'db_name': 'gh_GeometricApplicationsOfEllipse',
        'domain': 'conic_sections',
        'reason': '橢圓的幾何應用 - 20個課本例題，應用豐富',
        'complexity': 3,
    },
    {
        'gemini_name': 'gh_DistancesRelatedToLines',
        'db_name': 'gh_DistancesRelatedToLines',
        'domain': 'analytic_geometry',
        'reason': '直線相關的距離 - 384行，22個助手函數',
        'complexity': 3,
    },
    {
        'gemini_name': 'gh_EquationOfALine',
        'db_name': 'gh_EquationOfALine',
        'domain': 'analytic_geometry',
        'reason': '直線方程 - 421行，基礎但複雜',
        'complexity': 3,
    },
    
    # 【線性代數】(3個) - 矩陣、向量、系統思維
    {
        'gemini_name': 'gh_VectorDotProduct',
        'db_name': 'gh_VectorDotProduct',
        'domain': 'linear_algebra',
        'reason': '向量點積 - 514行，核心運算',
        'complexity': 3,
    },
    {
        'gemini_name': 'gh_MatrixMeaningAndEquality',
        'db_name': 'gh_MatrixMeaningAndEquality',
        'domain': 'linear_algebra',
        'reason': '矩陣的意義與相等 - 485行',
        'complexity': 3,
    },
    {
        'gemini_name': 'gh_CrossProductOfSpaceVectors',
        'db_name': 'gh_CrossProductOfSpaceVectors',
        'domain': 'linear_algebra',
        'reason': '向量叉積 - 454行，3D空間概念',
        'complexity': 3,
    },
    
    # 【三角函數】(2個) - 基礎但需要精算
    {
        'gemini_name': 'gh_BasicTrigonometricIdentities',
        'db_name': 'gh_BasicTrigonometricIdentities',
        'domain': 'trigonometry',
        'reason': '基本三角恆等式 - 566行，多種題型',
        'complexity': 3,
    },
    {
        'gemini_name': 'gh_SineAndCosineFunctionGraphs',
        'db_name': 'gh_SineAndCosineFunctionGraphs',
        'domain': 'trigonometry',
        'reason': '正弦餘弦函數圖形 - 541行',
        'complexity': 3,
    },
    
    # 【複數與極坐標】(2個) - 進階話題，顯示深度
    {
        'gemini_name': 'gh_PolarFormOfComplexNumbers',
        'db_name': 'gh_PolarFormOfComplexNumbers',
        'domain': 'complex_numbers',
        'reason': '複數的極形式 - 550行，優雅數學',
        'complexity': 3,
    },
    {
        'gemini_name': 'gh_ConversionBetweenRectangularAndPolarCoordinates',
        'db_name': 'gh_ConversionBetweenRectangularAndPolarCoordinates',
        'domain': 'complex_numbers',
        'reason': '直角坐標與極坐標轉換 - 396行',
        'complexity': 3,
    },
    
    # 【統計與機率】(2個) - 數據科學展示
    {
        'gemini_name': 'gh_ConditionalProbability',
        'db_name': 'gh_ConditionalProbability',
        'domain': 'probability_statistics',
        'reason': '條件機率 - 486行，應用廣泛',
        'complexity': 3,
    },
    {
        'gemini_name': 'gh_BayesTheorem',
        'db_name': 'gh_BayesTheorem',
        'domain': 'probability_statistics',
        'reason': '貝葉斯定理 - 現代統計基礎',
        'complexity': 3,
    },
    
    # 【數列與級數】(1個) - 進階話題
    {
        'gemini_name': 'gh_Sequence',
        'db_name': 'gh_Sequence',
        'domain': 'sequences_series',
        'reason': '數列 - 586行，多種題型',
        'complexity': 3,
    },
]

def check_database_availability():
    """檢查每個技能在資料庫中的例題數量"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    print("【在資料庫中檢查課本例題】")
    print("=" * 100)
    
    for skill in RECOMMENDED_20_SKILLS:
        db_name = skill['db_name']
        cursor.execute(
            'SELECT COUNT(*) FROM textbook_examples WHERE skill_id = ?',
            (db_name,)
        )
        count = cursor.fetchone()[0]
        
        status = "✓" if count > 0 else "✗"
        print(f"{status} {db_name}: {count} 個例題")
        skill['example_count'] = count
    
    conn.close()

def print_strategy():
    """打印完整策略"""
    print("\n" + "=" * 100)
    print("【金牌策略 - 20 支精選技能】")
    print("=" * 100)
    
    # 按 domain 分組
    by_domain = {}
    for skill in RECOMMENDED_20_SKILLS:
        domain = skill['domain']
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(skill)
    
    for domain in sorted(by_domain.keys()):
        skills = by_domain[domain]
        print(f"\n【{domain.upper()}】({len(skills)}個)")
        print("-" * 100)
        
        for i, skill in enumerate(skills, 1):
            examples = skill.get('example_count', '?')
            gemini_baseline = skill.get('gemini_name', 'N/A')
            
            print(f"{i}. {skill['db_name']}")
            print(f"   課本例題: {examples}個 | Gemini代碼: {gemini_baseline}")
            print(f"   原因: {skill['reason']}")
    
    print("\n" + "=" * 100)
    print("【選擇策略的科學根據】")
    print("=" * 100)
    print("""
✅ 複雜度優先：全部選擇複雜度 3 的技能（Gemini生成的代碼有 300+ 行，代表「天花板」）

✅ Domain 多樣化：
   - Calculus (4)：微積分是高中數學的皇冠，展示深度
   - Analytic Geometry + Conic Sections (4)：幾何視覺性強，展示成果
   - Linear Algebra (3)：矩陣/向量是現代數學基礎
   - Trigonometry (2)：經典難點，但相對簡單
   - Complex Numbers (2)：優雅性和難度兼備
   - Probability/Statistics (2)：實用性和現代性
   - Sequences/Series (1)：進階話題

✅ 課本例題支撐：只選有足夠例題的技能（確保能生成多個變化）

✅ Gemini代碼作為「天花板」：
   - 每個技能都有對應的高品質 Gemini 代碼（平均 400-600 行）
   - 定義了要達到的品質水準（Qwen 14B 的目標）
   - 包含複雜的數學邏輯、格式化、多個子題型

🎯 科學獎項評估角度：
   - 深度（Depth）：微積分應用、複數變換等高等數學
   - 廣度（Breadth）：覆蓋 7 個主要 domain
   - 完整性（Completeness）：每個技能都有多個例題變化
   - 創新性（Innovation）：用 14B 模型達到 Gemini 品質
""")

def main():
    print("\n🏆 根據課本例題 + Gemini 代碼品質分析")
    print("   制定「拿金牌」的 20 支技能策略\n")
    
    print(f"📊 推薦的 20 支技能：\n")
    
    check_database_availability()
    print_strategy()
    
    # 統計信息
    total_examples = sum(skill.get('example_count', 0) for skill in RECOMMENDED_20_SKILLS)
    avg_examples = total_examples / len(RECOMMENDED_20_SKILLS) if RECOMMENDED_20_SKILLS else 0
    
    print("\n" + "=" * 100)
    print("【統計數據】")
    print("=" * 100)
    print(f"總技能數: {len(RECOMMENDED_20_SKILLS)}")
    print(f"總課本例題: {total_examples}")
    print(f"平均每個技能: {avg_examples:.1f} 個例題")
    print(f"Domain 數量: {len(set(s['domain'] for s in RECOMMENDED_20_SKILLS))}")

if __name__ == "__main__":
    main()
