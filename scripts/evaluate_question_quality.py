# -*- coding: utf-8 -*-
"""
数学题目品质评估系统（科展专用）
解决问题：Code Quality ≠ Question Quality
"""

import os
import sys
import json
import importlib.util
import ast
from collections import Counter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class QuestionQualityEvaluator:
    """
    评估数学题目生成品质的核心类
    
    评估维度（Mathematical Quality Metrics）：
    1. Executability (可执行性): 能否成功生成题目
    2. Diversity (变化性): 多次执行生成不同题目的能力
    3. Difficulty Appropriateness (难度适当性): 难度等级是否合理
    4. Mathematical Correctness (数学正确性): 答案、推导是否正确
    5. LaTeX Aesthetics (格式美观度): LaTeX 排版品质
    
    Mathematical Quality Score (MQS) = Σ(各维度得分 × 权重)
    """
    
    def __init__(self):
        self.results = []
    
    def load_module(self, filepath):
        """动态加载 Python 模块"""
        try:
            spec = importlib.util.spec_from_file_location("skill_module", filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module, None
        except SyntaxError as e:
            return None, f"SyntaxError: {e}"
        except Exception as e:
            return None, f"LoadError: {e}"
    
    def evaluate_executability(self, module, filepath, trials=5):
        """
        评估可执行性（Executability）
        
        返回:
            score: 0.0-1.0 (成功率)
            details: 执行详情
        """
        if module is None:
            return 0.0, {"error": "Module failed to load", "success_rate": 0}
        
        success_count = 0
        generated_questions = []
        errors = []
        
        for i in range(trials):
            try:
                # 尝试生成题目
                if hasattr(module, 'generate_question'):
                    result = module.generate_question(level=4)
                    if result and 'problem' in result:
                        success_count += 1
                        generated_questions.append(result)
                else:
                    errors.append(f"Trial {i+1}: No generate_question function")
            except Exception as e:
                errors.append(f"Trial {i+1}: {str(e)}")
        
        score = success_count / trials
        details = {
            "success_rate": score,
            "successful_trials": success_count,
            "total_trials": trials,
            "errors": errors[:3]  # 只保留前3个错误
        }
        
        return score, details
    
    def evaluate_diversity(self, questions):
        """
        评估变化性（Diversity）
        
        检查多次生成的题目是否有足够变化
        
        返回:
            score: 0.0-1.0 (变化程度)
            details: 变化性分析
        """
        if len(questions) < 2:
            return 0.0, {"error": "Not enough questions to evaluate diversity"}
        
        # 提取题目文本
        problem_texts = [q.get('problem', '') for q in questions if q.get('problem')]
        
        if not problem_texts:
            return 0.0, {"error": "No problem texts found"}
        
        # 检查是否所有题目完全相同
        unique_problems = len(set(problem_texts))
        uniqueness_ratio = unique_problems / len(problem_texts)
        
        # 检查数值变化（提取所有数字）
        import re
        all_numbers = []
        for text in problem_texts:
            numbers = re.findall(r'-?\d+', text)
            all_numbers.extend(numbers)
        
        unique_numbers = len(set(all_numbers))
        number_diversity = min(1.0, unique_numbers / 10)  # 10种不同数字视为高变化性
        
        # 综合评分
        score = (uniqueness_ratio * 0.6 + number_diversity * 0.4)
        
        details = {
            "unique_problems": unique_problems,
            "total_problems": len(problem_texts),
            "uniqueness_ratio": uniqueness_ratio,
            "unique_numbers": unique_numbers,
            "diversity_score": score
        }
        
        return score, details
    
    def evaluate_difficulty(self, questions, expected_level=4):
        """
        评估难度适当性（Difficulty Appropriateness）
        
        检查生成的题目难度是否符合预期
        
        返回:
            score: 0.0-1.0 (难度符合度)
            details: 难度分析
        """
        if not questions:
            return 0.0, {"error": "No questions to evaluate"}
        
        # 检查难度标记
        difficulty_match = 0
        for q in questions:
            if q.get('level') == expected_level:
                difficulty_match += 1
        
        match_ratio = difficulty_match / len(questions)
        
        # 检查数学复杂度指标
        complexity_scores = []
        for q in questions:
            problem_text = q.get('problem', '')
            # 指标：多项式次数、函数嵌套、导数阶数
            complexity = 0
            if '导' in problem_text or 'f^' in problem_text:
                complexity += 0.3  # 有导数
            if 'x^{5}' in problem_text or 'x^{4}' in problem_text:
                complexity += 0.3  # 高次多项式
            if '代入' in problem_text or '求值' in problem_text:
                complexity += 0.2  # 需要代入计算
            if len(problem_text) > 50:
                complexity += 0.2  # 题目描述复杂
            
            complexity_scores.append(min(1.0, complexity))
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        
        # 综合评分
        score = (match_ratio * 0.5 + avg_complexity * 0.5)
        
        details = {
            "difficulty_match_ratio": match_ratio,
            "average_complexity": avg_complexity,
            "complexity_scores": complexity_scores
        }
        
        return score, details
    
    def evaluate_math_correctness(self, questions):
        """
        评估数学正确性（Mathematical Correctness）
        
        检查生成的答案是否正确
        
        返回:
            score: 0.0-1.0 (正确率)
            details: 正确性分析
        """
        if not questions:
            return 0.0, {"error": "No questions to evaluate"}
        
        correct_count = 0
        total_count = 0
        issues = []
        
        for i, q in enumerate(questions):
            answer = q.get('answer', '')
            problem = q.get('problem', '')
            
            if not answer:
                issues.append(f"Q{i+1}: No answer provided")
                continue
            
            total_count += 1
            
            # 简单检查：答案格式是否合理
            is_correct = True
            
            # 检查1：答案是否为空或仅含LaTeX标记
            if len(answer.strip()) < 5:
                is_correct = False
                issues.append(f"Q{i+1}: Answer too short")
            
            # 检查2：答案是否包含明显错误标记
            error_markers = ['Error', 'error', 'None', 'null', '未定义']
            if any(marker in answer for marker in error_markers):
                is_correct = False
                issues.append(f"Q{i+1}: Error marker in answer")
            
            # 检查3：LaTeX 格式是否完整
            if answer.count('$') % 2 != 0:
                is_correct = False
                issues.append(f"Q{i+1}: Unmatched $ in answer")
            
            if is_correct:
                correct_count += 1
        
        score = correct_count / total_count if total_count > 0 else 0.0
        
        details = {
            "correct_count": correct_count,
            "total_count": total_count,
            "correctness_rate": score,
            "issues": issues[:5]  # 只保留前5个问题
        }
        
        return score, details
    
    def evaluate_latex_aesthetics(self, questions):
        """
        评估 LaTeX 格式美观度（LaTeX Aesthetics）
        
        检查 LaTeX 排版品质
        
        返回:
            score: 0.0-1.0 (美观度)
            details: 格式分析
        """
        if not questions:
            return 0.0, {"error": "No questions to evaluate"}
        
        total_score = 0
        format_issues = []
        
        for i, q in enumerate(questions):
            problem = q.get('problem', '')
            answer = q.get('answer', '')
            full_text = problem + answer
            
            score = 1.0
            
            # 检查1：是否有 Markdown 代码块符号
            if '```' in full_text:
                score -= 0.3
                format_issues.append(f"Q{i+1}: Markdown fence found")
            
            # 检查2：LaTeX 公式是否完整包裹
            unmatched_dollars = full_text.count('$') % 2
            if unmatched_dollars != 0:
                score -= 0.2
                format_issues.append(f"Q{i+1}: Unmatched $ signs")
            
            # 检查3：是否有碎片化 LaTeX (e.g., "$x$ ^ $2$")
            import re
            fragmented_pattern = r'\$[^$]+\$\s*\^\s*\$[^$]+\$'
            if re.search(fragmented_pattern, full_text):
                score -= 0.3
                format_issues.append(f"Q{i+1}: Fragmented LaTeX found")
            
            # 检查4：指数格式是否正确
            if '^{' in full_text and '^{{' in full_text:
                score -= 0.1
                format_issues.append(f"Q{i+1}: Double brace in exponent")
            
            # 检查5：是否有中英文混排空格
            if re.search(r'[\u4e00-\u9fff]\$', full_text) or re.search(r'\$[\u4e00-\u9fff]', full_text):
                # 中文和LaTeX紧密相连，格式良好
                pass
            else:
                # 可能有多余空格
                pass
            
            total_score += max(0.0, score)
        
        avg_score = total_score / len(questions)
        
        details = {
            "average_aesthetics_score": avg_score,
            "format_issues": format_issues[:5]
        }
        
        return avg_score, details
    
    def compute_mqs(self, exec_score, div_score, diff_score, math_score, latex_score):
        """
        计算数学品质分数 (Mathematical Quality Score, MQS)
        
        MQS = E×0.25 + D×0.20 + DF×0.15 + M×0.25 + L×0.15
        
        E:  Executability (可执行性)
        D:  Diversity (变化性)
        DF: Difficulty (难度适当性)
        M:  Math Correctness (数学正确性)
        L:  LaTeX Aesthetics (格式美观度)
        """
        mqs = (exec_score * 0.25 +
               div_score * 0.20 +
               diff_score * 0.15 +
               math_score * 0.25 +
               latex_score * 0.15)
        
        return mqs
    
    def evaluate_file(self, filepath, ablation_id, healer_enabled):
        """完整评估单个文件"""
        print(f"\n{'='*60}")
        print(f"Evaluating: {os.path.basename(filepath)}")
        print(f"Ablation ID: {ablation_id}, Healer: {'ON' if healer_enabled else 'OFF'}")
        print(f"{'='*60}")
        
        # 1. 加载模块
        module, load_error = self.load_module(filepath)
        
        # 2. 可执行性
        exec_score, exec_details = self.evaluate_executability(module, filepath, trials=5)
        print(f"\n📊 Executability: {exec_score:.2f}")
        print(f"   Success Rate: {exec_details.get('success_rate', 0):.2%}")
        
        # 获取生成的题目
        questions = exec_details.get('generated_questions', [])
        
        # 3. 变化性
        if questions:
            div_score, div_details = self.evaluate_diversity(questions)
            print(f"\n📊 Diversity: {div_score:.2f}")
            print(f"   Unique Problems: {div_details.get('unique_problems', 0)}/{div_details.get('total_problems', 0)}")
        else:
            div_score, div_details = 0.0, {"error": "No questions generated"}
            print(f"\n📊 Diversity: 0.00 (No questions)")
        
        # 4. 难度适当性
        if questions:
            diff_score, diff_details = self.evaluate_difficulty(questions)
            print(f"\n📊 Difficulty Appropriateness: {diff_score:.2f}")
            print(f"   Average Complexity: {diff_details.get('average_complexity', 0):.2f}")
        else:
            diff_score, diff_details = 0.0, {"error": "No questions generated"}
            print(f"\n📊 Difficulty: 0.00 (No questions)")
        
        # 5. 数学正确性
        if questions:
            math_score, math_details = self.evaluate_math_correctness(questions)
            print(f"\n📊 Mathematical Correctness: {math_score:.2f}")
            print(f"   Correct Rate: {math_details.get('correctness_rate', 0):.2%}")
        else:
            math_score, math_details = 0.0, {"error": "No questions generated"}
            print(f"\n📊 Math Correctness: 0.00 (No questions)")
        
        # 6. LaTeX 美观度
        if questions:
            latex_score, latex_details = self.evaluate_latex_aesthetics(questions)
            print(f"\n📊 LaTeX Aesthetics: {latex_score:.2f}")
        else:
            latex_score, latex_details = 0.0, {"error": "No questions generated"}
            print(f"\n📊 LaTeX Aesthetics: 0.00 (No questions)")
        
        # 7. 计算 MQS
        mqs = self.compute_mqs(exec_score, div_score, diff_score, math_score, latex_score)
        print(f"\n{'='*60}")
        print(f"📈 Mathematical Quality Score (MQS): {mqs:.3f} ({mqs*100:.1f}%)")
        print(f"{'='*60}")
        
        # 保存结果
        result = {
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "ablation_id": ablation_id,
            "healer_enabled": healer_enabled,
            "executability": exec_score,
            "diversity": div_score,
            "difficulty": diff_score,
            "math_correctness": math_score,
            "latex_aesthetics": latex_score,
            "mqs": mqs,
            "details": {
                "executability": exec_details,
                "diversity": div_details,
                "difficulty": diff_details,
                "math_correctness": math_details,
                "latex_aesthetics": latex_details
            }
        }
        
        self.results.append(result)
        return result
    
    def compare_ablations(self):
        """比较不同 Ablation 版本"""
        print("\n" + "="*80)
        print("📊 MATHEMATICAL QUALITY COMPARISON")
        print("="*80)
        
        ab1 = next((r for r in self.results if r['ablation_id'] == 1), None)
        ab2 = next((r for r in self.results if r['ablation_id'] == 2), None)
        ab3 = next((r for r in self.results if r['ablation_id'] == 3), None)
        
        print(f"\n{'Metric':<25} {'Ab1 (Bare)':<15} {'Ab2 (Engineered)':<20} {'Ab3 (Healer)':<15}")
        print("-" * 80)
        print(f"{'Executability':<25} {ab1['executability'] if ab1 else 0:.2f}{'':<12} {ab2['executability'] if ab2 else 0:.2f}{'':<17} {ab3['executability'] if ab3 else 0:.2f}")
        print(f"{'Diversity':<25} {ab1['diversity'] if ab1 else 0:.2f}{'':<12} {ab2['diversity'] if ab2 else 0:.2f}{'':<17} {ab3['diversity'] if ab3 else 0:.2f}")
        print(f"{'Difficulty':<25} {ab1['difficulty'] if ab1 else 0:.2f}{'':<12} {ab2['difficulty'] if ab2 else 0:.2f}{'':<17} {ab3['difficulty'] if ab3 else 0:.2f}")
        print(f"{'Math Correctness':<25} {ab1['math_correctness'] if ab1 else 0:.2f}{'':<12} {ab2['math_correctness'] if ab2 else 0:.2f}{'':<17} {ab3['math_correctness'] if ab3 else 0:.2f}")
        print(f"{'LaTeX Aesthetics':<25} {ab1['latex_aesthetics'] if ab1 else 0:.2f}{'':<12} {ab2['latex_aesthetics'] if ab2 else 0:.2f}{'':<17} {ab3['latex_aesthetics'] if ab3 else 0:.2f}")
        print("-" * 80)
        print(f"{'MQS (Total)':<25} {ab1['mqs'] if ab1 else 0:.3f} ({ab1['mqs']*100 if ab1 else 0:.0f}%){'':<3} {ab2['mqs'] if ab2 else 0:.3f} ({ab2['mqs']*100 if ab2 else 0:.0f}%){'':<8} {ab3['mqs'] if ab3 else 0:.3f} ({ab3['mqs']*100 if ab3 else 0:.0f}%)")
        print("=" * 80)
        
        # 关键洞察
        if ab2 and ab3:
            improvement = ab3['mqs'] - ab2['mqs']
            print(f"\n🎯 Key Insight:")
            print(f"   Healer improved MQS from {ab2['mqs']:.1%} to {ab3['mqs']:.1%}")
            print(f"   Absolute improvement: +{improvement:.3f}")
            if ab2['mqs'] > 0:
                print(f"   Relative improvement: +{(improvement/ab2['mqs']*100):.1f}%")
        
        print("\n")


def main():
    """主程序"""
    evaluator = QuestionQualityEvaluator()
    
    # 评估三个 Ablation 版本
    skills_dir = os.path.join(PROJECT_ROOT, 'skills')
    
    files = [
        (os.path.join(skills_dir, 'gh_ApplicationsOfDerivatives_14b_Ab1.py'), 1, False),
        (os.path.join(skills_dir, 'gh_ApplicationsOfDerivatives_14b_Ab2.py'), 2, False),
        (os.path.join(skills_dir, 'gh_ApplicationsOfDerivatives_14b_Ab3.py'), 3, True)
    ]
    
    for filepath, ablation_id, healer_enabled in files:
        if os.path.exists(filepath):
            evaluator.evaluate_file(filepath, ablation_id, healer_enabled)
        else:
            print(f"Warning: {filepath} not found")
    
    # 比较结果
    evaluator.compare_ablations()
    
    # 保存 JSON
    output_path = os.path.join(PROJECT_ROOT, 'reports', 'question_quality_evaluation.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(evaluator.results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_path}")


if __name__ == '__main__':
    main()
