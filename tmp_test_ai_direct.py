import os
import sys

# Setup environment to use core.ai_wrapper directly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from core.code_generator import _call_ai
from config import Config

def simple_test():
    prompt_path = os.path.join(os.path.dirname(__file__), "agent_skills", "jh_數學2上_FourOperationsOfRadicals", "prompt_liveshow.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    
    # Simulate LiveShow injecting user text
    prompt = prompt_template.replace("{{OCR_RESULT}}", r"\sqrt{35} \div \sqrt{5}")

    print("Calling Qwen...")
    model_config = Config.CODER_PRESETS.get('qwen3.5-9b') or Config.CODER_PRESETS.get('qwen3-8b')
    res, _, _, _ = _call_ai(prompt, model_config=model_config)
    print("AI Output: \n", res)

if __name__ == '__main__':
    simple_test()
