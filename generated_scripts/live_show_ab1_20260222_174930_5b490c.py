import random

def generate(level=1):
    def format_poly(terms):
        """將項列表轉換為字串，terms 為 (係數, 次方) 的列表"""
        res = ""
        for i, (coeff, exp) in enumerate(terms):
            # 處理符號
            if i == 0:
                sign = "-" if coeff < 0 else ""
            else:
                sign = "-" if coeff < 0 else "+"
            
            # 處理係數
            abs_c = abs(coeff)
            if abs_c == 1 and exp != 0:
                c_str = ""
            else:
                c_str = str(abs_c)
            
            # 處理變數與次方
            if exp == 0:
                term_str = str(abs_c)
            elif exp == 1:
                term_str = f"{c_str}x"
            else:
                term_str = f"{c_str}x^{exp}"
            
            res += sign + term_str
        return res

    def get_random_poly():
        """隨機生成多項式項與係數字典"""
        degrees = [3, 2, 1, 0]
        # 隨機選取 2 到 3 個項
        num_terms = random.randint(2, 3)
        chosen_degrees = random.sample(degrees, num_terms)
        
        poly_dict = {d: 0 for d in degrees}
        term_list = []
        for d in chosen_degrees:
            c = random.choice([i for i in range(-9, 10) if i != 0])
            poly_dict[d] = c
            term_list.append((c, d))
        
        return poly_dict, format_poly(term_list)

    # 生成兩個多項式
    p1_dict, p1_str = get_random_poly()
    p2_dict, p2_str = get_random_poly()
    
    # 隨機決定加法或減法
    op = random.choice(['+', '-'])
    
    # 組合題目字串 (模擬範例空格風格)
    question = f"( {p1_str})+({p2_str} )" if op == '+' else f"( {p1_str})-({p2_str} )"
    
    # 計算答案
    ans_dict = {}
    for d in range(4):
        if op == '+':
            ans_dict[d] = p1_dict.get(d, 0) + p2_dict.get(d, 0)
        else:
            ans_dict[d] = p1_dict.get(d, 0) - p2_dict.get(d, 0)
            
    # 格式化答案 (由高次方到低次方)
    ans_terms = []
    for d in sorted(ans_dict.keys(), reverse=True):
        if ans_dict[d] != 0:
            ans_terms.append((ans_dict[d], d))
            
    if not ans_terms:
        ans_str = "0"
    else:
        ans_str = format_poly(ans_terms)
        # 修正 format_poly 在答案開頭可能產生的正號 (雖然邏輯中已處理，但確保萬一)
        if ans_str.startswith('+'):
            ans_str = ans_str[1:]

    return {
        "question_text": question,
        "correct_answer": ans_str
    }