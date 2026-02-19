import random
import math
import re
import ast
import operator

def generate(level=1, **kwargs):
    while True:
        if level == 1:
            degree = random.randint(3, 5)
            coeffs = [0] * (degree + 1)
            coeffs[degree] = random.randint(-10, 10)
            while coeffs[degree] == 0:
                coeffs[degree] = random.randint(1, 10)
            min_extra = 2
            max_extra = degree
            num_extra = random.randint(min_extra, max_extra)
            remaining_indices = list(range(degree))
            random.shuffle(remaining_indices)
            selected_indices = remaining_indices[:num_extra]
            for idx in selected_indices:
                c = random.randint(-10, 10)
                while c == 0:
                    c = random.randint(-10, 10)
                coeffs[idx] = c
            terms = _coeffs_to_terms(coeffs)
            try:
                deriv = _differentiate_poly(terms, order=1)
                poly_latex = _poly_to_latex(terms)
                q = f'計算 ${poly_latex}$ 的導數 $f\'(x)$。'
                a = _poly_to_plain(deriv)
                return {
                    'question_text': q,
                    'correct_answer': a,
                    'answer': a,
                    'mode': 1
                }
            except:
                continue

        elif level == 2:
            degree = random.randint(3, 5)
            coeffs = [0] * (degree + 1)
            coeffs[degree] = random.randint(-10, 10)
            while coeffs[degree] == 0:
                coeffs[degree] = random.randint(1, 10)
            min_extra = 2
            max_extra = degree
            num_extra = random.randint(min_extra, max_extra)
            remaining_indices = list(range(degree))
            random.shuffle(remaining_indices)
            selected_indices = remaining_indices[:num_extra]
            for idx in selected_indices:
                c = random.randint(-10, 10)
                while c == 0:
                    c = random.randint(-10, 10)
                coeffs[idx] = c
            terms = _coeffs_to_terms(coeffs)
            x0 = random.uniform(-5, 5)
            f_x0 = sum([coeff * (x0 ** (degree - i)) for i, coeff in enumerate(coeffs)])
            deriv = _differentiate_poly(terms, order=1)
            deriv_at_x0 = sum([coeff * (x0 ** (degree - 1 - i)) for i, coeff in enumerate(deriv)])
            poly_latex = _poly_to_latex(terms)
            q = f'求過點 $({fmt_num(x0)}, {fmt_num(f_x0)})$ 且與 $f(x) = {poly_latex}$ 相切的切線方程式。'
            a = f'{fmt_num(deriv_at_x0)}x + {fmt_num(f_x0 - deriv_at_x0 * x0)}'
            return {
                'question_text': q,
                'correct_answer': a,
                'answer': a,
                'mode': 1
            }

        elif level == 3:
            degree = random.randint(4, 6)
            coeffs = [0] * (degree + 1)
            coeffs[degree] = random.randint(-10, 10)
            while coeffs[degree] == 0:
                coeffs[degree] = random.randint(1, 10)
            min_extra = 2
            max_extra = degree
            num_extra = random.randint(min_extra, max_extra)
            remaining_indices = list(range(degree))
            random.shuffle(remaining_indices)
            selected_indices = remaining_indices[:num_extra]
            for idx in selected_indices:
                c = random.randint(-10, 10)
                while c == 0:
                    c = random.randint(-10, 10)
                coeffs[idx] = c
            terms = _coeffs_to_terms(coeffs)
            deriv1 = _differentiate_poly(terms, order=1)
            deriv2 = _differentiate_poly(terms, order=2)
            roots = []
            for i in range(len(deriv1)):
                if deriv1[i][0] != 0:
                    root = -deriv1[i][1] / deriv1[i][0]
                    roots.append(root)
            if not roots:
                continue
            x0 = roots[0]
            f_x0 = sum([coeff * (x0 ** (degree - i)) for i, coeff in enumerate(coeffs)])
            deriv1_x0 = sum([coeff * (x0 ** (degree - 1 - i)) for i, coeff in enumerate(deriv1)])
            deriv2_x0 = sum([coeff * (x0 ** (degree - 2 - i)) for i, coeff in enumerate(deriv2)])
            poly_latex = _poly_to_latex(terms)
            if deriv2_x0 > 0:
                extrema_type = '最小值'
            else:
                extrema_type = '最大值'
            q = f'求 $f(x) = {poly_latex}$ 的 {extrema_type} 及其位置。'
            a = f'在 $x = {fmt_num(x0)}$ 時取得 {extrema_type}，值為 {fmt_num(f_x0)}'
            return {
                'question_text': q,
                'correct_answer': a,
                'answer': a,
                'mode': 1
            }