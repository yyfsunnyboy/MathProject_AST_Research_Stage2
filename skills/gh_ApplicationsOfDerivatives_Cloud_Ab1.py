# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: gemini-2.5-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 51.90s | Tokens: In=552, Out=1731
# Created At: 2026-02-04 23:23:23
# Fix Status: [Clean Pass] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
import random

def _poly_to_string(poly_terms):
    """Converts a list of (coefficient, power) tuples to a string representation."""
    if not poly_terms:
        return "$0$"
    
    terms_str = []
    
    # Sort terms by power in descending order
    poly_terms.sort(key=lambda x: x[1], reverse=True)

    for coeff, power in poly_terms:
        if coeff == 0:
            continue

        term_str = ""
        # Handle sign
        if coeff > 0 and len(terms_str) > 0: # Only add '+' if it's not the very first term
            term_str += "+"
        elif coeff < 0:
            term_str += "-"

        abs_coeff = abs(coeff)

        # Handle coefficient and power
        if power == 0: # Constant term
            term_str += str(abs_coeff)
        elif abs_coeff == 1: # x^n or -x^n
            if power == 1:
                term_str += "x"
            else:
                term_str += f"x^{power}"
        else: # ax^n where a != 1
            if power == 1:
                term_str += f"{abs_coeff}x"
            else:
                term_str += f"{abs_coeff}x^{power}"
        terms_str.append(term_str)
    
    if not terms_str: # All coefficients were 0, or only 0 terms were passed
        return "$0$"
        
    return "$" + "".join(terms_str) + "$"

def _differentiate_poly(poly_terms):
    """Differentiates a polynomial represented as a list of (coefficient, power) tuples."""
    derived_terms = []
    for coeff, power in poly_terms:
        if power > 0:
            derived_terms.append((coeff * power, power - 1))
    
    # Filter out terms with zero coefficient that might result from differentiation (e.g. 0*x^2)
    derived_terms = [(c, p) for c, p in derived_terms if c != 0]
    
    return derived_terms

def generate(level=1, **kwargs):
    # Generate a random polynomial with degree from 3 to 5
    degree = random.randint(3, 5) 
    poly_terms = []
    
    # Ensure the highest degree term has a non-zero coefficient
    leading_coeff = random.choice([-3, -2, -1, 1, 2, 3])
    poly_terms.append((leading_coeff, degree))

    # Generate other coefficients
    for p in range(degree - 1, -1, -1):
        coeff = random.randint(-5, 5)
        if coeff != 0:
            poly_terms.append((coeff, p))
            
    f_x_str = _poly_to_string(poly_terms)

    # Calculate all possible derivatives up to the 4th order
    current_poly = poly_terms
    derivative_results = []
    
    # Compute f'(x)
    current_poly = _differentiate_poly(current_poly)
    if current_poly:
        derivative_results.append(('f\'(x)', _poly_to_string(current_poly)))
    
    # Compute f''(x)
    if current_poly: # Only if f'(x) was not 0
        current_poly = _differentiate_poly(current_poly)
        if current_poly:
            derivative_results.append(('f\'\'(x)', _poly_to_string(current_poly)))
            
    # Compute f'''(x)
    if current_poly: # Only if f''(x) was not 0
        current_poly = _differentiate_poly(current_poly)
        if current_poly:
            derivative_results.append(('f\'\'\'(x)', _poly_to_string(current_poly)))
            
    # Compute f''''(x) - less common, only for higher degree polynomials
    if current_poly and degree >= 4 and random.random() < 0.3: # ~30% chance for 4th derivative if possible
        current_poly = _differentiate_poly(current_poly)
        if current_poly:
            derivative_results.append(('f\'\'\'\'(x)', _poly_to_string(current_poly)))

    # Ensure there's at least one derivative to ask for.
    # This fallback is for highly unlikely edge cases where all derivatives become zero.
    if not derivative_results:
        # Re-generate with a guaranteed non-zero derivative for f'(x)
        poly_terms = [(random.choice([-3, -2, -1, 1, 2, 3]), 1), (random.randint(-5, 5), 0)] # e.g., 2x + 3
        f_x_str = _poly_to_string(poly_terms)
        derivative_results.append(('f\'(x)', _poly_to_string(_differentiate_poly(poly_terms))))


    # Choose 1 or 2 derivatives to ask for
    num_to_ask = random.randint(1, min(len(derivative_results), 2))
    
    # Randomly select distinct derivatives
    chosen_derivatives = random.sample(derivative_results, num_to_ask)
    
    # Sort chosen derivatives by their order (e.g., f' before f'') for consistent output
    def get_derivative_order(label):
        if label == 'f\'(x)': return 1
        if label == 'f\'\'(x)': return 2
        if label == 'f\'\'\'(x)': return 3
        if label == 'f\'\'\'\'(x)': return 4
        return 0 # Should not happen

    chosen_derivatives.sort(key=lambda x: get_derivative_order(x[0]))

    question_parts = [f'${q_label}$' for q_label, _ in chosen_derivatives]
    correct_answers = [ans_str for _, ans_str in chosen_derivatives]
    
    question_text = f"已知 {f_x_str}，求 {', '.join(question_parts)}。"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': ','.join(correct_answers),
        'mode': 1
    }

def check(user_answer, correct_answer):
    # Normalize answers: remove spaces and dollar signs, then split by comma
    def _normalize_answer_string(ans_str):
        # Remove all whitespace and '$'
        normalized = ans_str.replace(" ", "").replace("$", "")
        # Split by comma and clean each part
        parts = [p.strip() for p in normalized.split(',') if p.strip()]
        return parts

    user_parts = _normalize_answer_string(user_answer)
    correct_parts = _normalize_answer_string(correct_answer)

    # Compare lists of parts in order
    is_correct = (user_parts == correct_parts)

    if is_correct:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}