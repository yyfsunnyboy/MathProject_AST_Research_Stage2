import re, json

cases = [
    # 情境1: num_ctx 截斷，</think> 消失
    '<think>\nLet me think...\n{\n"something": "inside think"\n}',
    # 情境2: 模型照抄 // 注解
    '{\n  "ocr_text": "12 \\div 3", // 禁止注解\n  "skill_id": "jh_test",\n  "confidence": 95\n}',
    # 情境3: markdown 包裝
    '```json\n{\n  "ocr_text": "12+3",\n  "skill_id": "jh_test",\n  "confidence": 90\n}\n```',
    # 情境4: 正常 <think> 閉合
    '<think>\nsome {fake: true}\n</think>\n{\n  "ocr_text": "5-3",\n  "skill_id": "jh_test",\n  "confidence": 95\n}',
]

for i, raw_out in enumerate(cases, 1):
    print(f'=== 情境 {i} ===')
    # Step1: 移除閉合 think
    clean = re.sub(r'<think>.*?</think>', '', raw_out, flags=re.DOTALL)
    # Step2: 移除未閉合 think（截斷造成 </think> 消失）
    clean = re.sub(r'<think>.*', '', clean, flags=re.DOTALL)
    clean = clean.strip()
    if not clean:
        clean = raw_out
    # Step3: 移除 ```json 包裝
    clean = re.sub(r'```(?:json)?\s*', '', clean).replace('```', '').strip()

    json_match = re.search(r'(\{.*\})', clean, re.DOTALL)
    if json_match:
        candidate = json_match.group(0)
        # 修正非法 LaTeX 反斜線
        candidate = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', candidate)
        # 移除 // 行尾注解
        candidate = re.sub(r'\s*//[^\n"]*', '', candidate)
        try:
            parsed = json.loads(candidate)
            print(f'  ✅ 成功: {parsed}')
        except json.JSONDecodeError as e:
            print(f'  ❌ 失敗: {e}')
            print(f'     候選字串: {repr(candidate[:200])}')
    else:
        print('  ❌ 找不到 JSON')
