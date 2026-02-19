import random
import math
from math import gcd
from functools import reduce

def generate(level=1, **kwargs):
    while True:
        if level == 1:
            # 基礎導數計算
            degree = random.randint(3, 5)
            coeffs = [0] * (degree + 1)
            
            # 確保最高次項非零
            coeffs[degree] = random.randint(1, 10) * random.choice([-1, 1])
            while coeffs[degree] == 0:
                coeffs[degree] = random.randint(1, 10) * random.choice([-1, 1])
            
            # 確保至少3個非零項
            min_extra = 2
            max_extra = degree
            num_extra = random.randint(min_extra, max_extra)
            
            remaining_indices = list(range(degree))
            random.shuffle(remaining_indices)
            selected_indices = remaining_indices[:num_extra]
            
            for idx in selected_indices:
                c = random.randint(1, 10) * random.choice([-1, 1])
                while c == 0:
                    c = random.randint(1, 10) * random.choice([-1, 1])
                coeffs[idx] = c
            
            terms = _coeffs_to_terms(coeffs)
            deriv = _differentiate_poly(terms, order=1)
            ans = _poly_to_plain(deriv)
            
            poly_latex = _poly_to_latex(terms)
            q = f'計算 ${poly_latex}$ 的導數。'
            
            return {
                'question_text': q,
                'correct_answer': ans,
                'answer': ans,
                'mode': 1
            }
            
        elif level == 2:
            # 切線方程式應用
            while True:
                degree = random.randint(3, 5)
                coeffs = [0] * (degree + 1)
                
                # 確保最高次項非零
                coeffs[degree] = random.randint(1, 10) * random.choice([-1, 1])
                while coeffs[degree] == 0:
                    coeffs[degree] = random.randint(1, 10) * random.choice([-1, 1])
                
                # 確保至少3個非零項
                min_extra = 2
                max_extra = degree
                num_extra = random.randint(min_extra, max_extra)
                
                remaining_indices = list(range(degree))
                random.shuffle(remaining_indices)
                selected_indices = remaining_indices[:num_extra]
                
                for idx in selected_indices:
                    c = random.randint(1, 10) * random.choice([-1, 1])
                    while c == 0:
                        c = random.randint(1, 10) * random.choice([-1, 1])
                    coeffs[idx] = c
                
                terms = _coeffs_to_terms(coeffs)
                x0 = random.randint(-5, 5)
                y0 = sum(coeff * (x0 ** (deg)) for coeff, deg in terms)
                
                # 計算斜率
                deriv = _differentiate_poly(terms, order=1)
                slope = sum(coeff * deg * (x0 ** (deg - 1)) for coeff, deg in deriv)
                
                # 生成切線方程式
                if slope == 0:
                    continue
                
                poly_latex = _poly_to_latex(terms)
                q = f'求過點 $({x0}, {y0})$ 且與 $f(x) = {poly_latex}$ 相切的直線方程式。'
                a = f'y={y0}+{slope}(x-{x0})'
                
                return {
                    'question_text': q,
                    'correct_answer': a,
                    'answer': a,
                    'mode': 1
                }
                
        elif level == 3:
            # 極值問題
            while True:
                degree = random.randint(3, 5)
                coeffs = [0] * (degree + 1)
                
                # 確保最高次項非零
                coeffs[degree] = random.randint(1, 10) * random.choice([-1, 1])
                while coeffs[degree] == 0:
                    coeffs[degree] = random.randint(1, 10) * random.choice([-1, 1])
                
                # 確保至少3個非零項
                min_extra = 2
                max_extra = degree
                num_extra = random.randint(min_extra, max_extra)
                
                remaining_indices = list(range(degree))
                random.shuffle(remaining_indices)
                selected_indices = remaining_indices[:num_extra]
                
                for idx in selected_indices:
                    c = random.randint(1, 10) * random.choice([-1, 1])
                    while c == 0:
                        c = random.randint(1, 10) * random.choice([-1, 1])
                    coeffs[idx] = c
                
                terms = _coeffs_to_terms(coeffs)
                deriv1 = _differentiate_poly(terms, order=1)
                deriv2 = _differentiate_poly(terms, order=2)
                
                # 找臨界點
                critical_points = []
                for coeff, deg in deriv1:
                    if deg == 0:
                        continue
                    if coeff == 0:
                        continue
                    if deg == 1:
                        critical_points.append(-coeff / 0)
                        continue
                    if deg == 2:
                        critical_points.append(-coeff / (2 * coeff))
                        continue
                    # 更高次方需要解方程，暫時只處理二次
                    if deg == 2:
                        critical_points.append(-coeff / (2 * coeff))
                
                if not critical_points:
                    continue
                
                x0 = critical_points[0]
                y0 = sum(coeff * (x0 ** (deg)) for coeff, deg in terms)
                d2 = sum(coeff * deg * (deg - 1) * (x0 ** (deg - 2)) for coeff, deg in deriv2)
                
                poly_latex = _poly_to_latex(terms)
                q = f'求 $f(x) = {poly_latex}$ 的極值。'
                a = f'極值點在 x={x0}，二階導數為 {d2}'
                
                return {
                    'question_text': q,
                    'correct_answer': a,
                    'answer': a,
                    'mode': 1
                )