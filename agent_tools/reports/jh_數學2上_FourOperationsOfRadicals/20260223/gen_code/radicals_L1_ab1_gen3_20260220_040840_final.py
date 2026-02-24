# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 231.06s | Tokens: In=631, Out=14348
# Created At: 2026-02-20 04:08:40
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    terms1 = []
    for _ in range(3):
        square_num = random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10])
        square_free = random.choice([2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23, 26, 29, 30, 31, 33, 34, 35, 37, 38, 39, 41, 42, 43, 46, 47, 49, 51, 53, 55, 57, 58, 59, 61, 62, 65, 66, 67, 69, 71, 73, 74, 77, 78, 79, 82, 83, 85, 86, 87, 89, 91, 93, 94, 95, 97, 101])
        radicand = square_num * square_free
        coefficient = random.randint(1, 5)
        terms1.append((coefficient, square_num, square_free))
    
    binom1 = []
    for _ in range(2):
        square_num = random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10])
        square_free = random.choice([2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23, 26, 29, 30, 31, 33, 34, 35, 37, 38, 39, 41, 42, 43, 46, 47, 49, 51, 53, 55, 57, 58, 59, 61, 62, 65, 66, 67, 69, 71, 73, 74, 77, 78, 79, 82, 83, 85, 86, 87, 89, 91, 93, 94, 95, 97, 101])
        radicand = square_num * square_free
        coefficient = random.randint(1, 1)
        binom1.append((coefficient, square_num, square_free))
    
    binom2 = []
    for _ in range(2):
        square_num = random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10])
        square_free = random.choice([2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23, 26, 29, 30, 31, 33, 34, 35, 37, 38, 39, 41, 42, 43, 46, 47, 49, 51, 53, 55, 57, 58, 59, 61, 62, 65, 66, 67, 69, 71, 73, 74, 77, 78, 79, 82, 83, 85, 86, 87, 89, 91, 93, 94, 95, 97, 101])
        radicand = square_num * square_free
        coefficient = random.randint(1, 1)
        binom2.append((coefficient, square_num, square_free))
    
    part1_terms = []
    for coeff, sq_num, sf in terms1:
        sqrt_sq_num = int(math.isqrt(sq_num))
        radicand_str = f"{sq_num * sf}"
        part1_terms.append(f"{coeff}\\sqrt{{{radicand_str}}}")
    part1_text = " + ".join(part1_terms)
    
    part2_terms1 = []
    for coeff, sq_num, sf in binom1:
        radicand_str = f"{sq_num * sf}"
        part2_terms1.append(f"{coeff}\\sqrt{{{radicand_str}}}")
    part2_text1 = " + ".join(part2_terms1)
    
    part2_terms2 = []
    for coeff, sq_num, sf in binom2:
        radicand_str = f"{sq_num * sf}"
        part2_terms2.append(f"{coeff}\\sqrt{{{radicand_str}}}")
    part2_text2 = " - ".join(part2_terms2)
    
    part2_text = f"({part2_text1})({part2_text2})"
    
    problem_text = f"({part1_text}) + {part2_text}"
    
    simplified_terms1 = {}
    for coeff, sq_num, sf in terms1:
        sqrt_sq_num = int(math.isqrt(sq_num))
        simplified_coeff = coeff * sqrt_sq_num
        key = sf
        if key in simplified_terms1:
            simplified_terms1[key] += simplified_coeff
        else:
            simplified_terms1[key] = simplified_coeff
    
    expanded_terms = []
    for term1 in binom1:
        for term2 in binom2:
            coeff1, sq_num1, sf1 = term1
            coeff2, sq_num2, sf2 = term2
            radicand1 = sq_num1 * sf1
            radicand2 = sq_num2 * sf2
            product_radicand = radicand1 * radicand2
            expanded_terms.append((coeff1 * coeff2, product_radicand))
    
    simplified_expanded = {}
    for coeff, radicand in expanded_terms:
        key = radicand
        if key in simplified_expanded:
            simplified_expanded[key] += coeff
        else:
            simplified_expanded[key] = coeff
    
    combined = {}
    for key, value in simplified_terms1.items():
        if key in combined:
            combined[key] += value
        else:
            combined[key] = value
    for key, value in simplified_expanded.items():
        if key in combined:
            combined[key] += value
        else:
            combined[key] = value
    
    correct_answer_parts = []
    for key, value in combined.items():
        if value > 0:
            correct_answer_parts.append(f"{value}\\sqrt{{{key}}}")
        elif value < 0:
            correct_answer_parts.append(f"{value}\\sqrt{{{key}}}")
    correct_answer = " + ".join(correct_answer_parts)
    
    return {
        'question_text': f'${problem_text}$',
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}