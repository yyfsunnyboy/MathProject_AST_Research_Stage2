"""
Simulate the <think> tag scenario that was breaking classify_input.
The model outputs <think>...</think> with JSON-like content inside,
followed by the actual JSON answer.
"""
import re, json

# Simulate model output with <think> block that has { } inside
raw_out = """<think>
I need to identify the math skill. Looking at the image showing "12 / (-4) x (-3)".
Let me check the skills list: {"possible": "integers or arithmetic"}.
I'll select the integer operations skill.
</think>
{
  "ocr_text": "12 \\div (-4) \\times (-3)",
  "skill_id": "jh_數學1上_FourArithmeticOperationsOfIntegers",
  "confidence": 95
}"""

print("=== OLD BEHAVIOR (no think strip) ===")
# Old code: directly search {.*} in raw_out
old_match = re.search(r'(\{.*\})', raw_out, re.DOTALL)
if old_match:
    old_str = old_match.group(0)
    print(f"Extracted: {repr(old_str[:200])}")
    try:
        fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', old_str)
        parsed = json.loads(fixed)
        print(f"Parsed: {parsed}")
    except json.JSONDecodeError as e:
        print(f"FAILED to parse: {e}")
else:
    print("No match found")

print()
print("=== NEW BEHAVIOR (strip think first) ===")
# New code: strip <think>...</think> first
raw_out_clean = re.sub(r'<think>.*?</think>', '', raw_out, flags=re.DOTALL).strip()
if not raw_out_clean:
    raw_out_clean = raw_out
print(f"Clean text: {repr(raw_out_clean[:300])}")

new_match = re.search(r'(\{.*\})', raw_out_clean, re.DOTALL)
if new_match:
    new_str = new_match.group(0)
    print(f"Extracted: {repr(new_str)}")
    try:
        fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', new_str)
        parsed = json.loads(fixed)
        print(f"Parsed: {parsed}")
        print("SUCCESS!")
    except json.JSONDecodeError as e:
        print(f"FAILED to parse: {e}")
else:
    print("No match found")
