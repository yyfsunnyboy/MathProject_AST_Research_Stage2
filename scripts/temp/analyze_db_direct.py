# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱: analyze_db_direct.py
功能說明: 直接讀取 SQLite 資料庫，分析 textbook_examples 表
版本資訊: V1.0
更新日期: 2026-01-29
=============================================================================
"""
import sqlite3
import os
from collections import defaultdict
import json

def analyze_textbook_examples():
    """直接查詢資料庫，分析教科書例題"""
    
    # 資料庫路徑
    db_path = r'E:\Python\MathProject_AST_Research\instance\kumon_math.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 資料庫不存在: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 120)
    print(f"📊 教科書例題分析報告 | 資料庫: {db_path}")
    print("=" * 120)
    
    # 查詢所有技能
    cursor.execute("SELECT skill_id, skill_ch_name FROM skills_info ORDER BY skill_id")
    skills = {row['skill_id']: row['skill_ch_name'] for row in cursor.fetchall()}
    
    print(f"\n📚 系統中共有 {len(skills)} 個技能\n")
    
    # 按技能分組查詢例題
    categories = {
        'visualization': [],      # 圖形題
        'pure_computation': [],   # 純計算題
        'mixed': [],              # 混合題
        'uncertain': []           # 不確定
    }
    
    for skill_id, skill_ch_name in sorted(skills.items()):
        cursor.execute("""
            SELECT id, problem_text, detailed_solution, difficulty_level 
            FROM textbook_examples 
            WHERE skill_id = ?
            ORDER BY difficulty_level
        """, (skill_id,))
        
        examples = cursor.fetchall()
        
        if not examples:
            continue
        
        print(f"🔹 {skill_id}")
        print(f"   📝 中文名: {skill_ch_name}")
        print(f"   📊 例題數: {len(examples)}")
        
        # 分類例題
        viz_count = 0
        comp_count = 0
        mixed_count = 0
        
        for i, example in enumerate(examples, 1):
            problem = example['problem_text']
            solution = example['detailed_solution'] or ""
            difficulty = example['difficulty_level']
            
            # 簡短顯示問題
            problem_short = problem[:60] + "..." if len(problem) > 60 else problem
            print(f"      例題 {i}: [{difficulty}級] {problem_short}")
            
            # 判斷類型
            category = _classify_example(problem, solution, skill_ch_name)
            
            if category == 'visualization':
                viz_count += 1
            elif category == 'pure_computation':
                comp_count += 1
            elif category == 'mixed':
                mixed_count += 1
        
        # 決定該技能的最終分類
        total = len(examples)
        if viz_count >= total * 0.4:
            final_category = 'visualization'
        elif comp_count >= total * 0.4:
            final_category = 'pure_computation'
        elif mixed_count > 0:
            final_category = 'mixed'
        else:
            final_category = 'uncertain'
        
        categories[final_category].append({
            'skill_id': skill_id,
            'skill_name': skill_ch_name,
            'example_count': len(examples),
            'viz': viz_count,
            'comp': comp_count,
            'mixed': mixed_count
        })
        
        print(f"   ✅ 分類: {final_category} | 統計: 圖形={viz_count}, 計算={comp_count}, 混合={mixed_count}\n")
    
    # 彙總統計
    print("\n" + "=" * 120)
    print("📊 分類彙總統計")
    print("=" * 120)
    
    for category in ['visualization', 'pure_computation', 'mixed', 'uncertain']:
        items = categories[category]
        if items:
            print(f"\n【{category.upper()}】({len(items)} 個技能)")
            for item in items:
                print(f"  ✓ {item['skill_id']:50s} | {item['skill_name']:30s} | "
                      f"例題: {item['example_count']:2d} | "
                      f"[圖={item['viz']} 計={item['comp']} 混={item['mixed']}]")
    
    # 挑選推薦的 20 個技能
    print("\n" + "=" * 120)
    print("🏆 推薦的 20 個實驗技能")
    print("=" * 120)
    
    recommendations = []
    
    # 優先級 1: 圖形題（最有視覺衝擊力）
    for item in categories['visualization']:
        if len(recommendations) < 20:
            recommendations.append({
                'rank': len(recommendations) + 1,
                'skill_id': item['skill_id'],
                'skill_name': item['skill_name'],
                'category': 'visualization',
                'priority': 'HIGH',
                'example_count': item['example_count']
            })
    
    # 優先級 2: 純計算題（基礎驗證）
    for item in categories['pure_computation']:
        if len(recommendations) < 20:
            recommendations.append({
                'rank': len(recommendations) + 1,
                'skill_id': item['skill_id'],
                'skill_name': item['skill_name'],
                'category': 'pure_computation',
                'priority': 'MEDIUM',
                'example_count': item['example_count']
            })
    
    # 優先級 3: 混合題（補充）
    for item in categories['mixed']:
        if len(recommendations) < 20:
            recommendations.append({
                'rank': len(recommendations) + 1,
                'skill_id': item['skill_id'],
                'skill_name': item['skill_name'],
                'category': 'mixed',
                'priority': 'MEDIUM',
                'example_count': item['example_count']
            })
    
    # 輸出推薦列表
    print()
    for rec in recommendations:
        print(f"{rec['rank']:2d}. {rec['skill_id']:50s} | {rec['skill_name']:30s} | "
              f"分類: {rec['category']:20s} | 優先級: {rec['priority']:6s} | "
              f"例題數: {rec['example_count']}")
    
    # 保存為 JSON
    output_file = os.path.join(os.path.dirname(__file__), 'recommended_skills_analysis.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recommendations, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 推薦清單已保存至: {output_file}")
    
    # 生成 Domain 分類建議
    print("\n" + "=" * 120)
    print("💡 Domain 分類建議")
    print("=" * 120)
    
    domain_suggestions = _suggest_domains(recommendations)
    for domain_name, skills in domain_suggestions.items():
        print(f"\n【{domain_name}】({len(skills)} 個技能)")
        for skill_info in skills:
            print(f"  • {skill_info['skill_id']:50s} ({skill_info['skill_name']})")
    
    conn.close()
    
    return recommendations, domain_suggestions


def _classify_example(problem_text, solution_text, skill_name):
    """分類例題類型"""
    
    problem_lower = problem_text.lower()
    solution_lower = (solution_text or "").lower()
    skill_lower = skill_name.lower()
    
    # 圖形關鍵詞（中英文）
    visualization_keywords = [
        '圖形', '圖像', '畫圖', '繪製', '繪圖', '座標', '坐標', '坐标',
        '數線', '数线', '圓', '圆', '三角形', '三角', '拋物線', '抛物线',
        '直線', '直线', '曲線', '曲线', '平面', '軸', '轴', '象限',
        'graph', 'plot', 'figure', 'line', 'circle', 'triangle', 'curve',
        'coordinate', 'axes', 'axis', 'slope', 'intercept', 'vertex',
        '線圖', '线图', '柱狀圖', '柱状图', '折線圖', '折线图', '箱線圖', '箱线图',
        '圖表', '图表', '統計圖', '统计图', '分布', '直方圖', '直方图', '趨勢',
        '視覺', '视觉', '顯示', '显示', '繪製'
    ]
    
    # 計算關鍵詞
    computation_keywords = [
        '計算', '计算', '求', '解', '化簡', '化简', '比較', '比较', '約分', '约分',
        '通分', '分數', '分数', '整數', '整数', '根式', '方程', '方程式',
        '運算', '运算', '加法', '減法', '减法', '乘法', '除法', '四則', '四则',
        'calculate', 'compute', 'solve', 'simplify', 'add', 'subtract', 'multiply', 'divide'
    ]
    
    # 計數
    viz_score = sum(1 for kw in visualization_keywords 
                    if kw in problem_lower or kw in solution_lower or kw in skill_lower)
    comp_score = sum(1 for kw in computation_keywords 
                     if kw in problem_lower or kw in solution_lower or kw in skill_lower)
    
    if viz_score > comp_score:
        return 'visualization'
    elif comp_score > 0 and viz_score == 0:
        return 'pure_computation'
    elif viz_score > 0 and comp_score > 0:
        return 'mixed'
    else:
        return 'uncertain'


def _suggest_domains(recommendations):
    """根據推薦列表建議 Domain 分組"""
    
    domain_map = {
        'integer_arithmetic': [],
        'fraction_arithmetic': [],
        'equation_and_algebra': [],
        'polynomial_and_quadratic': [],
        'number_line_visual': [],
        'coordinate_plane_visual': [],
        'quadratic_graph': [],
        'sequences_and_series': []
    }
    
    # 簡單的 skill_id 到 domain 的對應
    keywords_to_domain = {
        'integer': 'integer_arithmetic',
        '整數': 'integer_arithmetic',
        'fraction': 'fraction_arithmetic',
        '分數': 'fraction_arithmetic',
        'equation': 'equation_and_algebra',
        '方程式': 'equation_and_algebra',
        'polynomial': 'polynomial_and_quadratic',
        '多項式': 'polynomial_and_quadratic',
        'quadratic': 'polynomial_and_quadratic',
        '二次': 'polynomial_and_quadratic',
        'number_line': 'number_line_visual',
        '數線': 'number_line_visual',
        'coordinate': 'coordinate_plane_visual',
        '座標': 'coordinate_plane_visual',
        'graph': 'quadratic_graph',
        '圖形': 'quadratic_graph',
        'sequence': 'sequences_and_series',
        '數列': 'sequences_and_series'
    }
    
    for rec in recommendations:
        skill_id = rec['skill_id'].lower()
        skill_name = rec['skill_name'].lower()
        
        matched = False
        for keyword, domain in keywords_to_domain.items():
            if keyword in skill_id or keyword in skill_name:
                domain_map[domain].append(rec)
                matched = True
                break
        
        if not matched:
            # 預設分類
            if rec['category'] == 'visualization':
                domain_map['number_line_visual'].append(rec)
            else:
                domain_map['integer_arithmetic'].append(rec)
    
    # 移除空的 domain
    return {k: v for k, v in domain_map.items() if v}


if __name__ == '__main__':
    print("🚀 開始分析教科書例題（直接數據庫查詢）...\n")
    recommendations, domains = analyze_textbook_examples()
    print("\n✅ 分析完成！")
