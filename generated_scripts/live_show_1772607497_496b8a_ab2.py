import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    last_ans = None
    last_math_str = None
    
    for attempt in range(25):
        vars_dict = {}
        vars_dict['v1'] = IntegerOps.random_nonzero(-50, 50)
        vars_dict['v2'] = IntegerOps.random_nonzero(-10, 10)
        while abs(vars_dict['v2']) <= 1:
            vars_dict['v2'] = IntegerOps.random_nonzero(-10, 10)
        vars_dict['v3'] = IntegerOps.random_nonzero(-50, 50)
        vars_dict['v4'] = IntegerOps.random_nonzero(-50, 50)
        vars_dict['v5'] = IntegerOps.random_nonzero(-10, 10)
        while abs(vars_dict['v5']) <= 1:
            vars_dict['v5'] = IntegerOps.random_nonzero(-10, 10)
        vars_dict['v6'] = IntegerOps.random_nonzero(-50, 50)
        _o1_healed = False

        # 智慧型倒算法 (Intelligent Reverse Calculation) 的結構同構攔截與縮放
        try:
            eval_str_init = "((((((((({v1}/{v2})))))))))*({v3})-((((((((({v4}/{v5})))))))))*({v6})"
            
            # 使用 Fraction 強制保留精確分母
            for k, v in vars_dict.items():
                key1 = chr(123) + k + chr(125)
                key2 = chr(123) + "fmt(" + k + ")" + chr(125)
                if isinstance(v, float):
                    frac_str = "Fraction('" + format(v, '.1f') + "')"
                else:
                    frac_str = "Fraction(" + str(v) + ", 1)"
                eval_str_init = eval_str_init.replace(key1, frac_str)
                eval_str_init = eval_str_init.replace(key2, frac_str)
                
            ans_init = safe_eval(eval_str_init)
            
            # 若第一波計算產生分數，代表存在除法截斷。
            # 直接將結構中的「第一個變數」乘上分母，強制使得整組式中存在能夠被整除的公倍數，實現完美的 O(1) 倒算法！
            if False and type(ans_init).__name__ == "Fraction" and ans_init.denominator != 1:
                # [保護機制] 如果隨機出的分母過大（例如幾百萬），乘回 v1 會導致出現天文數字。
                # 國中範圍的分母通常在 1000 以內。超過 1000 直接拒絕，讓外層迴圈重新隨機洗牌。
                if ans_init.denominator > 1000:
                    continue
                    
                # 取得第一個生成的變數名 (例如 v1) 並將它乘上剛剛算出來的分母
                first_var = "v1" if 6 > 0 else None
                if first_var:
                    vars_dict[first_var] = vars_dict[first_var] * ans_init.denominator
                    _o1_healed = True
                    
            # 變數縮放完成後，重新組裝字串與算式
            eval_str = "((((((((({v1}/{v2})))))))))*({v3})-((((((((({v4}/{v5})))))))))*({v6})"
            math_str = "({fmt(v1)}/{fmt(v2)})\\\\times({v3})-({fmt(v4)}/{fmt(v5)})\\\\times({v6})"
            
            for k, v in vars_dict.items():
                key1 = chr(123) + k + chr(125)
                key2 = chr(123) + "fmt(" + k + ")" + chr(125)
                
                # 最終答案計算也用 Fraction 以確保絕對精確
                if isinstance(v, float):
                    frac_str = "Fraction('" + format(v, '.1f') + "')"
                else:
                    frac_str = "Fraction(" + str(v) + ", 1)"
                eval_str = eval_str.replace(key1, frac_str)
                eval_str = eval_str.replace(key2, frac_str)

                if isinstance(v, float):
                    disp_v = format(v, '.1f')
                else:
                    disp_v = str(v)
                math_str = math_str.replace(key1, disp_v)
                math_str = math_str.replace(key2, disp_v if isinstance(v, float) else IntegerOps.fmt_num(v))
                
            ans = safe_eval(eval_str)
            
            last_ans = ans
            last_math_str = math_str
            
            if type(ans).__name__ == "Fraction":
                if abs(ans.numerator) > 120 or ans.denominator > 30:
                    continue
                if ans.denominator == 1:
                    final_ans = str(ans.numerator)
                else:
                    final_ans = f"{ans.numerator}/{ans.denominator}"
                return {
                    'question_text': "計算 $" + math_str + "$ 的值。",
                    'correct_answer': final_ans,
                    'mode': 1,
                    '_o1_healed': _o1_healed
                }
            elif abs(ans - round(ans)) < 1e-6:
                return {
                    'question_text': "計算 $" + math_str + "$ 的值。",
                    'correct_answer': str(int(round(ans))),
                    'mode': 1,
                    '_o1_healed': _o1_healed
                }
            
        except Exception:
            continue
            
    # 如果極端情況 25 次都找不到，退避到最後一次結果
    if last_ans is not None:
        if type(last_ans).__name__ == "Fraction":
            if last_ans.denominator == 1:
                final_ans = str(last_ans.numerator)
            else:
                final_ans = f"{last_ans.numerator}/{last_ans.denominator}"
        else:
            final_ans = f"{last_ans:.2f}"
        return {
            'question_text': "計算 $" + last_math_str + "$ 的值。",
            'correct_answer': final_ans,
            'mode': 1,
            '_o1_healed': False
        }

        
    return {'question_text': 'Error', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6:
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}
