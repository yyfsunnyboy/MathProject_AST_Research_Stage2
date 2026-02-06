# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱: analyze_textbook_examples.py
功能說明: 
    讀取資料庫中的 textbook_examples 表，分析例題內容
    評估哪些技能適合科展實驗（純計算 / 圖形生成）
版本資訊: V1.0
更新日期: 2026-01-29
=============================================================================
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, TextbookExample, SkillInfo
from app import create_app
from collections import defaultdict
import json
from datetime import datetime

def analyze_examples():
    """分析所有例題，評估適配性"""
    
    app = create_app()
    with app.app_context():
        # 查詢所有例題
        all_examples = TextbookExample.query.all()
        
        print("=" * 100)
        print(f"📊 教科書例題分析報告 | 總數: {len(all_examples)} 個例題")
        print("=" * 100)
        
        # 按 skill_id 分組
        skills_dict = defaultdict(list)
        for example in all_examples:
            skills_dict[example.skill_id].append(example)
        
        # 分類結果
        categories = {
            'pure_computation': [],      # 純計算題
            'visualization': [],          # 包含圖形元素
            'mixed': [],                  # 混合型
            'uncertain': []                # 不確定
        }
        
        skill_info_dict = {}
        for skill in SkillInfo.query.all():
            skill_info_dict[skill.skill_id] = skill.skill_ch_name
        
        print("\n📋 逐一分析技能與例題...")
        print("-" * 100)
        
        for skill_id in sorted(skills_dict.keys()):
            examples = skills_dict[skill_id]
            skill_name = skill_info_dict.get(skill_id, "未命名")
            
            print(f"\n🔹 技能: {skill_id}")
            print(f"   中文名: {skill_name}")
            print(f"   例題數: {len(examples)}")
            
            # 分析每個例題
            category_confidence = {
                'pure_computation': 0,
                'visualization': 0,
                'mixed': 0
            }
            
            for i, example in enumerate(examples, 1):
                problem = example.problem_text
                solution = example.detailed_solution or ""
                
                print(f"\n   📝 例題 {i}:")
                print(f"      問題: {problem[:80]}..." if len(problem) > 80 else f"      問題: {problem}")
                
                # 判斷例題類型
                category = _classify_example(problem, solution, skill_name)
                print(f"      分類: {category}")
                
                if category == 'pure_computation':
                    category_confidence['pure_computation'] += 1
                elif category == 'visualization':
                    category_confidence['visualization'] += 1
                elif category == 'mixed':
                    category_confidence['mixed'] += 1
            
            # 判斷整個技能的分類
            total = len(examples)
            if category_confidence['visualization'] >= total * 0.5:
                final_category = 'visualization'
                categories['visualization'].append((skill_id, skill_name, examples))
            elif category_confidence['pure_computation'] >= total * 0.5:
                final_category = 'pure_computation'
                categories['pure_computation'].append((skill_id, skill_name, examples))
            elif category_confidence['mixed'] > 0:
                final_category = 'mixed'
                categories['mixed'].append((skill_id, skill_name, examples))
            else:
                final_category = 'uncertain'
                categories['uncertain'].append((skill_id, skill_name, examples))
            
            print(f"\n   ✅ 最終分類: {final_category}")
            print(f"   統計: 純計算={category_confidence['pure_computation']}, "
                  f"圖形={category_confidence['visualization']}, "
                  f"混合={category_confidence['mixed']}")
        
        # 輸出彙總
        print("\n" + "=" * 100)
        print("📊 最終分類彙總")
        print("=" * 100)
        
        for category_name, items in categories.items():
            if items:
                print(f"\n【{category_name.upper()}】({len(items)} 個技能)")
                for skill_id, skill_name, examples in items:
                    print(f"  ✓ {skill_id} ({skill_name}) - {len(examples)} 個例題")
        
        # 推薦的 20 個技能
        print("\n" + "=" * 100)
        print("🏆 推薦的 20 個實驗技能")
        print("=" * 100)
        
        recommendations = []
        
        # 優先選圖形題
        for skill_id, skill_name, examples in categories['visualization'][:5]:
            recommendations.append({
                'skill_id': skill_id,
                'skill_name': skill_name,
                'category': 'visualization',
                'num_examples': len(examples),
                'priority': 'HIGH'
            })
        
        # 次優先選純計算題
        for skill_id, skill_name, examples in categories['pure_computation'][:10]:
            recommendations.append({
                'skill_id': skill_id,
                'skill_name': skill_name,
                'category': 'pure_computation',
                'num_examples': len(examples),
                'priority': 'MEDIUM'
            })
        
        # 填充混合題
        for skill_id, skill_name, examples in categories['mixed'][:5]:
            recommendations.append({
                'skill_id': skill_id,
                'skill_name': skill_name,
                'category': 'mixed',
                'num_examples': len(examples),
                'priority': 'MEDIUM'
            })
        
        # 只取前 20 個
        recommendations = recommendations[:20]
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i:2d}. {rec['skill_id']:45s} | {rec['skill_name']:30s} | "
                  f"分類: {rec['category']:20s} | 優先級: {rec['priority']:6s} | "
                  f"例題數: {rec['num_examples']}")
        
        # 輸出為 JSON
        output_file = os.path.join(os.path.dirname(__file__), 'recommended_skills.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 推薦清單已保存至: {output_file}")
        
        return recommendations


def _classify_example(problem_text, solution_text, skill_name):
    """
    根據問題和解答文本，判斷例題類型
    
    Returns:
        'pure_computation': 純數值計算
        'visualization': 包含圖形/繪圖元素
        'mixed': 混合類型
        'uncertain': 不確定
    """
    
    problem_lower = problem_text.lower()
    solution_lower = (solution_text or "").lower()
    skill_lower = skill_name.lower()
    
    # 圖形相關關鍵詞
    visualization_keywords = [
        '圖形', '圖像', '畫圖', '繪製', '繪圖', '座標', '坐標', '坐标',
        '數線', '数线', '圓', '圆', '三角形', '三角', '拋物線', '抛物线',
        '直線', '直线', '曲線', '曲线', '平面', '軸', '轴', '象限',
        'graph', 'plot', 'figure', 'line', 'circle', 'triangle', 'curve',
        'coordinate', 'axes', 'axis', 'slope', 'intercept', 'vertex',
        '線圖', '线图', '柱狀圖', '柱状图', '折線圖', '折线图', '箱線圖', '箱线图',
        '圖表', '图表', '統計圖', '统计图', '分布', '直方圖', '直方图'
    ]
    
    # 計算相關關鍵詞
    computation_keywords = [
        '計算', '计算', '求', '解', '化簡', '化简', '比較', '比较', '約分', '约分',
        '通分', '分數', '分数', '整數', '整数', '根式', '方程', '方程式',
        '運算', '运算', '加法', '減法', '减法', '乘法', '除法', '四則', '四则',
        'calculate', 'compute', 'solve', 'simplify', 'add', 'subtract', 'multiply', 'divide'
    ]
    
    # 計數
    visualization_score = sum(1 for kw in visualization_keywords 
                             if kw in problem_lower or kw in solution_lower or kw in skill_lower)
    computation_score = sum(1 for kw in computation_keywords 
                           if kw in problem_lower or kw in solution_lower or kw in skill_lower)
    
    # 判斷邏輯
    if visualization_score > computation_score:
        return 'visualization'
    elif computation_score > 0 and visualization_score == 0:
        return 'pure_computation'
    elif visualization_score > 0 and computation_score > 0:
        return 'mixed'
    else:
        return 'uncertain'


if __name__ == '__main__':
    print("🚀 開始分析教科書例題...")
    recommendations = analyze_examples()
    print("\n✅ 分析完成！")
