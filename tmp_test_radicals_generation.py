import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.engine.scaler import AdaptiveScaler

def test():
    scaler = AdaptiveScaler()

    print("Testing generation for jh_數學2上_FourOperationsOfRadicals (Ab3)...")
    
    ocr_text = r"(-\frac{2}{3}\sqrt{5}) \times 4\sqrt{7}"
    
    try:
        # Generate with custom wrapper
        res = scaler.generate_custom_problems(
            skill_name='jh_數學2上_FourOperationsOfRadicals', 
            input_text=ocr_text, 
            count=1,
            model_id='qwen3.5-9b',
            ablation_mode=False
        )
        print("--- GENERATION RESULT ---")
        if res and "problems" in res and res["problems"]:
            prob = res["problems"][0]
            print(f"File Path: {res.get('debug_meta', {}).get('file_path')}")
            print(f"Question: {prob.get('question_text')}")
            print(f"Correct Answer: {prob.get('correct_answer')}")
            print(f"RAW Generated code:\n{res.get('debug_meta', {}).get('raw_code')}")
        else:
            print("No result.")
    except Exception as e:
        print(f"Generation failed: {e}")

if __name__ == '__main__':
    test()
