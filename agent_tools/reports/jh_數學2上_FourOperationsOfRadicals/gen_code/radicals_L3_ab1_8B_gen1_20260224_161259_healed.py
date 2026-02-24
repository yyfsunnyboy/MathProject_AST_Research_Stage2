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
            if 'sqrt' in term:
                parts = term.split('sqrt')
                if len(parts) == 2:
                    num = parts[1].strip()
                    if num == '':
                        num = '1'
                    num = num.replace(')', '')
                    num = num.replace('(', '')
                    num = num.replace(' ', '')
                    num = num.replace('^', '')
                    if '^' in num:
                        num = num.split('^')[0]
                    if num == '':
                        num = '1'
                    num = int(num)
                    simplified.append(f'\\sqrt{{{num}}}')
                else:
                    simplified.append(term)
            else:
                simplified.append(term)
        return '+'.join(simplified)

    def create_radical_term():
        num = random.randint(1, 10)
        if random.random() < 0.5:
            num = num * random.randint(2, 5)
        return f'\\sqrt{{{num}}}'
    
    def create_expression(level):
        if level == 1:
            term1 = create_radical_term()
            term2 = create_radical_term()
            term3 = create_radical_term()
            term4 = create_radical_term()
            term5 = create_radical_term()
            term6 = create_radical_term()
            term7 = create_radical_term()
            term8 = create_radical_term()
            term9 = create_radical_term()
            term10 = create_radical_term()
            expr1 = f'({term1} + {term2} - {term3})'
            expr2 = f'({term4} + {term5})({term6} - {term7})'
            expr = f'{expr1} + {expr2}'
        elif level == 2:
            term1 = create_radical_term()
            term2 = create_radical_term()
            term3 = create_radical_term()
            term4 = create_radical_term()
            term5 = create_radical_term()
            term6 = create_radical
            term7 = create_radical_term()
            term8 = create_radical_term()
            term9 = create_radical_term()
            term10 = create_radical_term()
            expr1 = f'({term1} + {term2} - {term3})'
            expr2 = f'({term4} + {term5})({term6} - {term7})'
            expr3 = f'({term8} + {term9})({term10} - {term1})'
            expr = f'{expr1} + {expr2} + {expr3}'
        return expr

    expr = create_expression(level)
    simplified_expr = simplify_radical(expr)
    return {
        'question_text': f'\\text{{化簡}} {expr}',
        'answer': '',
        'correct_answer': simplified_expr,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Wrong'}