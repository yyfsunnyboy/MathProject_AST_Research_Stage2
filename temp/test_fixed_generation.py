#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""測試修復後的代碼生成"""
import sys
sys.path.insert(0, '.')

from core.code_generator import CodeGenerator

# 測試生成
generator = CodeGenerator(
    skill_id='gh_ApplicationsOfDerivatives',
    model_name='qwen2.5-coder:14b',
    ablation_id=3,
    max_attempts=1
)

print("🔧 開始生成代碼...")
result = generator.generate()

print(f"\n📊 生成結果:")
print(f"   狀態: {result.get('status')}")
print(f"   代碼長度: {len(result.get('final_code', ''))} chars")
print(f"   Prompt Tokens: {result.get('prompt_tokens', 'N/A')}")
print(f"   Response Tokens: {result.get('response_tokens', 'N/A')}")

if result.get('status') == 'success':
    print(f"\n✅ 成功！正在測試生成的代碼...")
    
    # 寫入文件
    with open('skills/test_fixed_ab3.py', 'w', encoding='utf-8') as f:
        f.write(result['final_code'])
    
    # 測試執行
    try:
        exec_globals = {}
        exec(result['final_code'], exec_globals)
        generate = exec_globals['generate']
        
        # 執行 3 次
        for i in range(3):
            output = generate()
            print(f"\n測試 {i+1}:")
            print(f"   題目: {output['question_text'][:80]}...")
            print(f"   答案: {output['correct_answer']}")
            
            # 檢查答案格式
            answer = output['correct_answer']
            if 'f\'' in answer or 'f"' in answer or '=' in answer or '\n' in answer:
                print(f"   ❌ 答案格式錯誤！包含禁止符號")
            else:
                print(f"   ✅ 答案格式正確")
                
    except Exception as e:
        print(f"\n❌ 執行失敗: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"\n❌ 生成失敗")
    if 'error' in result:
        print(f"   錯誤: {result['error']}")
