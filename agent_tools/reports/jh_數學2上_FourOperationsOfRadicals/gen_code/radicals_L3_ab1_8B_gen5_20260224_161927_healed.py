import random
import math

def generate(level=1, **kwargs):
    def simplify_radical(expr):
        terms = expr.split('+')
        simplified = []
        for term in terms:
            term = term.strip()
            if term.startswith('-'):
                term = term[1:]
            if term.startswith('sqrt('):
                inside = term[5:-1]
                if inside.isdigit():
                    root = int(inside)
                    if root >= 1:
                        factor = int(math.isqrt(root))
                        remainder = root - factor * factor
                        if remainder == 0:
                            simplified.append(f"{factor}")
                        else:
                            simplified.append(f"{factor}\\sqrt{{{remainder}}}")
            elif term.startswith('sqrt('):
                inside = term[5:-1]
                if inside.isdigit():
                    root = int(inside)
                    if root >= 1:
                        factor = int(math.isqrt(root))
                        remainder = root - factor * factor
                        if remainder == 0:
                            simplified.append(f"{factor}")
                        else:
                            simplified.append(f"{factor}\\sqrt{{{remainder}}}")
            else:
                simplified.append(term)
        simplified_str = '+'.join(simplified)
        simplified_str = simplified_str.replace('+-', '-')
        simplified_str = simplified_str.replace('+', '+')
        simplified_str = simplified_str.replace('--', '+')
        return simplified_str

    def generate_term():
        if random.random() < 0.5:
            sign = '+' if random.random() < 0.5 else '-'
            num = random.randint(1, 10)
            root = random.randint(2, 5)
            return f"{sign}{num}\\sqrt{{{root}}}"
        else:
            num = random.randint(1, 10)
            return f"{num}"

    def generate_expression():
        terms = [generate_term() for _ in range(random.randint(2, 4))]
        expr = '+'.join(terms)
        return expr

    expr1 = generate_expression()
    expr2 = generate_expression()
    question_text = f"\\left({expr1}\\right) + \\left({expr2}\\right)"
    answer = simplify_radical(expr1) + '+' + simplify_radical(expr2)
    correct_answer = simplify_radical(expr1) + '+' + simplify_radical(expr2)
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Wrong'}