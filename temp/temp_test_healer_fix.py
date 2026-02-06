"""測試 Regex Healer 的答案格式修復"""

test_code_newline = """
def generate(level=1, **kwargs):
    ans_parts = ['6x-5', '6']
    a = '\\n'.join(ans_parts)
    return {'answer': a}
"""

test_code_space = """
def generate(level=1, **kwargs):
    ans_parts = ['6x-5', '6']
    a = ' '.join(ans_parts)
    return {'answer': a}
"""

test_code_comma_correct = """
def generate(level=1, **kwargs):
    ans_parts = ['6x-5', '6']
    a = ','.join(ans_parts)
    return {'answer': a}
"""

from core.healers.regex_healer import RegexHealer

healer = RegexHealer()

print("=" * 70)
print("測試 1: 換行分隔符 -> 逗號")
print("=" * 70)
fixed1, fixes1 = healer.heal(test_code_newline)
print(f"修復次數: {fixes1}")
if "','.join" in fixed1:
    print("✅ 成功：已轉換為逗號分隔")
else:
    print("❌ 失敗：未轉換")
    print(f"結果: {[line for line in fixed1.split('\\n') if 'join' in line]}")

print("\n" + "=" * 70)
print("測試 2: 空格分隔符（應保持不變或轉為逗號）")
print("=" * 70)
fixed2, fixes2 = healer.heal(test_code_space)
print(f"修復次數: {fixes2}")
if "','.join" in fixed2 or "' '.join" in fixed2:
    print("✅ 通過")
else:
    print("❌ 異常")
    print(f"結果: {[line for line in fixed2.split('\\n') if 'join' in line]}")

print("\n" + "=" * 70)
print("測試 3: 正確的逗號分隔（應保持不變）")
print("=" * 70)
fixed3, fixes3 = healer.heal(test_code_comma_correct)
print(f"修復次數: {fixes3}")
if "','.join" in fixed3:
    print("✅ 成功：保持逗號分隔")
else:
    print("❌ 失敗：被錯誤修改")
    print(f"結果: {[line for line in fixed3.split('\\n') if 'join' in line]}")
