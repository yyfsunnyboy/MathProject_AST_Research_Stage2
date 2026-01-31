from app import app
from models import TextbookExample

with app.app_context():
    examples = TextbookExample.query.filter_by(skill_id='gh_ApplicationsOfDerivatives').all()
    
    if examples:
        print(f"✅ 找到 {len(examples)} 個課本例題\n")
        for idx, ex in enumerate(examples[:3], 1):
            print(f"範例 {idx}:")
            print(f"  題目: {ex.problem_text[:150] if len(ex.problem_text) > 150 else ex.problem_text}")
            if ex.correct_answer:
                print(f"  答案: {ex.correct_answer[:100]}")
            if ex.detailed_solution:
                print(f"  解法: {ex.detailed_solution[:100]}...")
            print()
    else:
        print("❌ 資料庫中沒有 ApplicationsOfDerivatives 的課本例題")
        print("\n需要先匯入課本例題到資料庫")
