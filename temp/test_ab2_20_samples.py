"""
測試 Ab2 連續生成 20 題是否會失敗
"""
import sys
sys.path.insert(0, 'E:\\Python\\MathProject_AST_Research')

from skills.gh_ApplicationsOfDerivatives_14b_Ab2 import generate

success_count = 0
fail_count = 0

print("🧪 測試連續生成 20 題\n")

for i in range(1, 21):
    try:
        result = generate()
        question = result.get('question_text', '')
        if question and len(question) > 10:
            success_count += 1
            print(f"✅ 第 {i:2d} 題成功: {question[:50]}...")
        else:
            fail_count += 1
            print(f"❌ 第 {i:2d} 題失敗: 題目太短或為空")
    except Exception as e:
        fail_count += 1
        print(f"❌ 第 {i:2d} 題失敗: {type(e).__name__}: {e}")

print(f"\n{'='*60}")
print(f"📊 測試結果:")
print(f"   成功: {success_count}/20 ({success_count*5}%)")
print(f"   失敗: {fail_count}/20 ({fail_count*5}%)")
print(f"{'='*60}")

if fail_count == 0:
    print("🎉 完美！所有 20 題都成功生成")
else:
    print(f"⚠️  仍有 {fail_count} 題失敗，需要進一步檢查")
