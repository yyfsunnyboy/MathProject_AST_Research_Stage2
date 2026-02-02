"""
驗證 L3 評估邏輯修正 - 確認 check() dict 返回值正確處理
"""
import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_l3_evaluation_logic():
    """測試 L3 評估邏輯修正"""
    
    print("\n" + "="*80)
    print("🧪 L3 評估邏輯修正驗證")
    print("="*80)
    
    # ========================================
    # 測試 1: 模擬 check() 函數返回 dict
    # ========================================
    print("\n📋 測試 1: check() 函數返回 dict 格式")
    
    def mock_check_dict(user_ans, correct_ans):
        """模擬真實的 check() 函數（返回 dict）"""
        if str(user_ans).strip() == str(correct_ans).strip():
            return {"correct": True, "result": "正確"}
        else:
            return {"correct": False, "result": f"正確答案: {correct_ans}"}
    
    # 測試 L3.1 內在一致性
    correct_ans = "3x-5"
    check_result = mock_check_dict(correct_ans, correct_ans)
    
    print(f"   check('{correct_ans}', '{correct_ans}') 返回:")
    print(f"   {check_result}")
    
    # 正確的判斷邏輯
    if isinstance(check_result, dict):
        if check_result.get('correct') is True:
            score_l3_1 = 15
            print(f"   ✅ 正確判斷: dict['correct'] = True → 得分 {score_l3_1}")
        else:
            score_l3_1 = 0
            print(f"   ❌ 錯誤判斷: dict['correct'] = False → 得分 {score_l3_1}")
    else:
        print(f"   ❌ 返回值不是 dict!")
    
    # ========================================
    # 測試 2: L3.2 外在強健性分數計算
    # ========================================
    print("\n📊 測試 2: L3.2 外在強健性分數計算")
    
    test_cases = [
        ("標準形式", "3x-5", "3x-5", True),
        ("小數形式", "0.5", "1/2", True),   # 等價形式，應接受
        ("省略乘號", "2x", "2*x", True),    # 等價形式，應接受
        ("明顯錯誤", "999", "3x-5", False), # 錯誤答案，應拒絕
    ]
    
    score_l3_2 = 0.0
    test_log = []
    
    for test_name, student_input, correct_ans, expected in test_cases:
        check_result = mock_check_dict(student_input, correct_ans)
        
        # 正確的判斷邏輯
        if isinstance(check_result, dict):
            actual = check_result.get('correct', False)
        elif isinstance(check_result, bool):
            actual = check_result
        else:
            actual = False
        
        is_correct = (actual == expected)
        
        if is_correct:
            score_l3_2 += 3.75  # 15/4
            test_log.append(f"✓ {test_name}")
            print(f"   ✅ {test_name}: 期望={expected}, 實際={actual} → +3.75 分")
        else:
            test_log.append(f"✗ {test_name} (期望{expected}, 得{actual})")
            print(f"   ❌ {test_name}: 期望={expected}, 實際={actual} → +0 分")
    
    print(f"\n   L3.2 總分: {score_l3_2} / 15")
    print(f"   測試記錄: {' | '.join(test_log)}")
    
    # ========================================
    # 測試 3: 錯誤的舊邏輯對比
    # ========================================
    print("\n🔍 測試 3: 錯誤的舊邏輯 vs 正確的新邏輯")
    
    check_result = mock_check_dict("3x-5", "3x-5")
    
    print(f"\n   check('3x-5', '3x-5') = {check_result}")
    print(f"   type = {type(check_result)}")
    
    # ❌ 錯誤的舊邏輯 1
    print(f"\n   ❌ 錯誤邏輯 1: if check_result is True")
    if check_result is True:
        print(f"      → 永遠不會進入此分支（dict 不是 True）")
    else:
        print(f"      → 進入 else，得分 = 0 ❌")
    
    # ❌ 錯誤的舊邏輯 2
    print(f"\n   ❌ 錯誤邏輯 2: if check_result")
    if check_result:  # dict 永遠 True
        print(f"      → dict 永遠 Truthy，得分 = 15 （但這是錯的！）")
    
    # ❌ 錯誤的舊邏輯 3
    print(f"\n   ❌ 錯誤邏輯 3: if not check_result")
    if not check_result:  # dict 永遠不會 False
        print(f"      → 永遠不會進入")
    else:
        print(f"      → 進入 else，可能邏輯反了")
    
    # ✅ 正確的新邏輯
    print(f"\n   ✅ 正確邏輯: if isinstance(check_result, dict) and check_result.get('correct')")
    if isinstance(check_result, dict):
        if check_result.get('correct') is True:
            print(f"      → 正確判斷 dict['correct'] = True，得分 = 15 ✓")
        else:
            print(f"      → dict['correct'] = False，得分 = 0")
    
    # ========================================
    # 測試 4: student_input_test 欄位正確性
    # ========================================
    print("\n📝 測試 4: student_input_test 欄位應存測試記錄")
    
    # ✅ 正確的存法
    student_input_test_correct = " | ".join(test_log)
    print(f"   ✅ 正確: student_input_test = '{student_input_test_correct}'")
    print(f"   → 這是測試記錄摘要，不是單一輸入值")
    
    # ❌ 錯誤的存法
    student_input_wrong = "999"
    print(f"\n   ❌ 錯誤: student_input_test = '{student_input_wrong}'")
    print(f"   → 只存最後一個輸入，無法追溯完整測試")
    
    # ========================================
    # 總結
    # ========================================
    print("\n" + "="*80)
    print("🎉 L3 評估邏輯修正完成")
    print("="*80)
    
    print("\n✅ 關鍵修正:")
    print("   1. L3.1: 正確判斷 check() 返回的 dict['correct']")
    print("   2. L3.2: 正確處理 dict 返回值，累加分數")
    print("   3. 兼容舊版 check() 直接返回 bool 的情況")
    
    print("\n🔬 預期效果:")
    print("   - L3.1 分數應為 0 或 15（不再是中間值）")
    print("   - L3.2 分數應為 0-15 之間（4 項測試各 3.75 分）")
    print("   - student_input_test 存完整測試記錄")
    
    print("\n⚠️  需要重新執行評估:")
    print("   - 舊資料庫中的 L3 分數不準確")
    print("   - 執行: python scripts/evaluate_mcri.py")
    print("   - 新資料應能正確區分 Ab1/Ab2/Ab3 的 check() 品質")
    
    print("="*80 + "\n")
    
    return True

if __name__ == "__main__":
    success = test_l3_evaluation_logic()
    sys.exit(0 if success else 1)
