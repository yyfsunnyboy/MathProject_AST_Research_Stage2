# -*- coding: utf-8 -*-
"""Diagnostic: compare Ab2 vs Ab3 MCRI in a real live generation run"""
import sys, json
sys.path.insert(0, r'D:\Python\MathProject_AST_Research')
from core.engine.scaler import AdaptiveScaler

scaler = AdaptiveScaler(model_role='generator')

for trial in range(1, 4):
    print(f"\n{'='*60}")
    print(f"Trial {trial}")
    print('='*60)
    
    result = scaler.generate_custom_problems(
        skill_name='jh_數學1上_FourArithmeticOperationsOfNumbers',
        input_text='計算 (-2又1/6) + 1又2/9 - (-1又1/3) 的值。',
        count=1, model_id='qwen3-vl-8b', ablation_mode=False,
    )
    
    # Ab3 MCRI (from problems_result[0]._live_mcri -> debug_meta is what live_show route reads)
    problems = result.get('problems', [{}])
    first = problems[0] if problems else {}
    ab3_live_mcri = first.get('_live_mcri', {})
    
    # Ab2 MCRI (from ab2_result)
    ab2_raw = result.get('ab2_result', {})
    ab2_live_mcri = ab2_raw.get('_live_mcri', {})  # Might be empty here (computed later in route)
    ab2_hygiene = ab2_raw.get('_mcri_hygiene_score', None)
    
    print(f"Ab3 question: {first.get('question_text', '?')[:80]}")
    print(f"Ab3 answer:   {first.get('correct_answer', '?')}")
    
    if ab3_live_mcri:
        print(f"\nAb3 MCRI (from pipeline):")
        print(f"  syntax={ab3_live_mcri.get('syntax_score')}  logic={ab3_live_mcri.get('logic_score')}  render={ab3_live_mcri.get('render_score')}  stability={ab3_live_mcri.get('stability_score')}  TOTAL={ab3_live_mcri.get('total_score')}")
        bd = ab3_live_mcri.get('breakdown', {})
        print(f"  breakdown: robust_status={bd.get('l5_robust_status')} healer_fixes={bd.get('healer_fixes')}")
    else:
        print("Ab3 MCRI: NOT COMPUTED (no _live_mcri key)")
    
    if ab2_raw and 'error' not in ab2_raw:
        print(f"\nAb2 question: {ab2_raw.get('question_text', '?')[:80]}")
        print(f"Ab2 hygiene score: {ab2_hygiene}")
        
        # Simulate what live_show.py does for Ab2 MCRI
        try:
            from scripts.evaluate_mcri import evaluate_live_code
            ab2_code_for_eval = ab2_raw.get('raw_code', '')
            ab2_mcri_sim = evaluate_live_code(
                code=ab2_code_for_eval,
                exec_result=ab2_raw,
                healer_trace={},
                ablation_mode=False
            )
            print(f"\nAb2 MCRI (simulated - live_show.py path):")
            print(f"  syntax={ab2_mcri_sim.get('syntax_score')}  logic={ab2_mcri_sim.get('logic_score')}  render={ab2_mcri_sim.get('render_score')}  stability={ab2_mcri_sim.get('stability_score')}  TOTAL={ab2_mcri_sim.get('total_score')}")
            bd2 = ab2_mcri_sim.get('breakdown', {})
            print(f"  breakdown: robust_status={bd2.get('l5_robust_status')} healer_fixes={bd2.get('healer_fixes')}")
        except Exception as e:
            print(f"Ab2 MCRI simulation error: {e}")
    else:
        print(f"Ab2 error: {ab2_raw.get('error', 'unknown')}")
    
    if ab3_live_mcri and 'ab2_mcri_sim' in dir():
        total_ab3 = ab3_live_mcri.get('total_score', 0)
        total_ab2 = ab2_mcri_sim.get('total_score', 0)
        delta = total_ab3 - total_ab2
        verdict = 'OK ✅' if delta >= 0 else f'BUG ❌ Ab3 LOWER by {-delta:.1f}'
        print(f"\n==> Ab3={total_ab3} vs Ab2={total_ab2}  delta={delta:+.1f}  {verdict}")
