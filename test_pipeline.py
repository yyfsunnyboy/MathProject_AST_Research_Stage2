# -*- coding: utf-8 -*-
import os
import sys

# 確保能 import project root modules
basedir = os.path.abspath(os.path.dirname(__file__))
if basedir not in sys.path:
    sys.path.insert(0, basedir)

from core.prompts.assembler import assemble_prompt
from core.healers.regex_healer import RegexHealer
from config import Config
from core.ai_wrapper import get_ai_client

def main():
    print("=== [Pipeline Test] Dynamic Math Prompt Assembler ===")
    
    # 1. 模擬分類器給出的例題與標籤
    target_question_dna = r"計算 $$[ (-8) + 3 ] \times 5 \div (-5) - [ 6 \times 6 - 4 ] \div (-8)$$ 的值。(運算結構：兩個獨立的大型項相減)"
    domain_tag = "integer"
    
    # 2. 組裝 Prompt
    prompt = assemble_prompt(target_question_dna, domain_tag)
    
    with open("pipeline_output_utf8.log", "w", encoding="utf-8") as f:
        f.write("=== [Pipeline Test] Dynamic Math Prompt Assembler ===\n")
        f.write(f"\n[1] 收到目標例題: {target_question_dna}\n")
        f.write(f"    分類器標籤: {domain_tag}\n")
        f.write("\n[2] 組裝完成的 Prompt:\n")
        f.write("-" * 40 + "\n")
        f.write(prompt + "\n")
        f.write("-" * 40 + "\n")
        
        # 3. 呼叫 LLM
        print("\n[3] 正在呼叫 LLM 進行生成 (這可能需要幾十秒)...")
        Config.MODEL_ROLES['coder'] = Config.CODER_PRESETS['qwen3-8b']
        client = get_ai_client(role='coder')
        
        response = client.generate_content(prompt)
        raw_output = response.text if hasattr(response, 'text') else str(response)
        
        f.write("\n[4] 啟動 RegexHealer 進行修復與 Import 注入...\n")
        healer = RegexHealer()
        clean_code = healer.remove_markdown_fences(raw_output)
        final_code, stats = healer.heal(clean_code)
        
        f.write("\n[5] 最終輸出的 Python 代碼:\n")
        f.write("=" * 60 + "\n")
        f.write(final_code + "\n")
        f.write("=" * 60 + "\n")
        f.write(f"修復統計: {stats}\n")
    print("Test complete. Results written to pipeline_output_utf8.log")

if __name__ == "__main__":
    main()
