# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: gemini-2.5-flash | Strategy: V47.5 Unified-Cleanup + Advanced-Healer
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 29.50s | Tokens: In=375, Out=1596
# Created At: 2026-01-31 12:50:34
# Fix Status: [Basic Cleanup] | Fixes: Basic=2, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
import random

def _format_polynomial(coeffs):
    """
    Helper function to format polynomial coefficients into a LaTeX string.
    coeffs is a list [d, c, b, a] for ax^3 + bx^2 + cx + d
    """
    terms = []
    
    # x^3 term
    if coeffs[3] != 0:
        if coeffs[3] == 1:
            terms.append("x^3")
        elif coeffs[3] == -1:
            terms.append("-x^3")
        else:
            terms.append(f"{coeffs[3]}x^3")

    # x^2 term
    if coeffs[2] != 0:
        if coeffs[2] > 0:
            if coeffs[2] == 1:
                terms.append("+x^2")
            else:
                terms.append(f"+{coeffs[2]}x^2")
        else: # coeffs[2] < 0
            if coeffs[2] == -1:
                terms.append("-x^2")
            else:
                terms.append(f"{coeffs[2]}x^2")

    # x term
    if coeffs[1] != 0:
        if coeffs[1] > 0:
            if coeffs[1] == 1:
                terms.append("+x")
            else:
                terms.append(f"+{coeffs[1]}x")
        else: # coeffs[1] < 0
            if coeffs[1] == -1:
                terms.append("-x")
            else:
                terms.append(f"{coeffs[1]}x")

    # constant term
    if coeffs[0] != 0:
        if coeffs[0] > 0:
            terms.append(f"+{coeffs[0]}")
        else: # coeffs[0] < 0
            terms.append(f"{coeffs[0]}")
            
    if not terms:
        return "0" # Should not happen for a degree 3 polynomial with a non-zero leading coeff
    
    result = "".join(terms)
    # Remove leading '+' if present
    if result.startswith("+"):
        result = result[1:]
    
    return result

def _evaluate_polynomial(coeffs, x_val):
    """
    Helper function to evaluate a polynomial at a given x_val.
    coeffs is a list [d, c, b, a] for ax^3 + bx^2 + cx + d
    """
    return coeffs[3]*x_val**3 + coeffs[2]*x_val**2 + coeffs[1]*x_val + coeffs[0]

def generate(level=1, **kwargs):
    """
    Generates a calculus problem on applications of derivatives (local extrema).
    
    Args:
        level (int): Difficulty level (currently not used, defaults to 1).
        **kwargs: Additional keyword arguments (not used).

    Returns:
        dict: A dictionary containing the question text, correct answer,
              and other metadata in LaTeX format.
    """
    
    # 1. Randomly choose roots for f'(x) to ensure integer critical points for f(x)
    r1 = random.randint(-4, 4)
    r2 = random.randint(-4, 4)
    while r1 == r2: # Ensure distinct roots for local extrema
        r2 = random.randint(-4, 4)

    # 2. Choose leading coefficient for f'(x).
    #    To ensure f(x) has integer coefficients after integration, K must be a multiple of 6.
    K = random.choice([-6, 6, -12, 12]) 
    
    # 3. Choose the constant term for f(x)
    D = random.randint(-10, 10)

    # 4. Derive coefficients for f(x) = ax^3 + bx^2 + cx + d
    #    We start with f'(x) = K(x-r1)(x-r2) = K(x^2 - (r1+r2)x + r1*r2)
    #    Then integrate: f(x) = (K/3)x^3 - (K/2)(r1+r2)x^2 + (K*r1*r2)x + D
    a = K // 3
    b = -(K // 2) * (r1 + r2)
    c = K * r1 * r2
    d = D
    
    # Store coefficients in order [constant, x, x^2, x^3] for evaluation and formatting
    coeffs = [d, c, b, a] 

    # 5. Format the polynomial for the question using LaTeX
    f_x_str_latex = _format_polynomial(coeffs)
    
    # 6. Calculate critical values (y-coordinates of local extrema)
    #    These occur at x = r1 and x = r2
    
    # 7. Determine which critical point corresponds to a local maximum and which to a local minimum
    #    Sort roots for consistent logic
    root_min_val_x = min(r1, r2)
    root_max_val_x = max(r1, r2)

    if K > 0: # f'(x) is an upward-opening parabola, so f(x) goes up, then down, then up.
              # Smaller root (x) corresponds to local max, larger root (x) to local min.
        local_max_val = _evaluate_polynomial(coeffs, root_min_val_x)
        local_min_val = _evaluate_polynomial(coeffs, root_max_val_x)
    else: # K < 0 (f'(x) is a downward-opening parabola), so f(x) goes down, then up, then down.
          # Smaller root (x) corresponds to local min, larger root (x) to local max.
        local_max_val = _evaluate_polynomial(coeffs, root_max_val_x)
        local_min_val = _evaluate_polynomial(coeffs, root_min_val_x)

    # 8. Construct the question text in LaTeX format
    q = f"設函數 $f(x) = {f_x_str_latex}$，試求其函數的局部最大值與局部最小值。"
    
    # 9. Construct the answer text in LaTeX format
    a = f"局部最大值為 ${local_max_val}$，局部最小值為 ${local_min_val}$。"

    # 10. Return the dictionary as specified
    return {
        'question_text': q,
        'correct_answer': a,
        'answer': a, # Must include this key, same value as 'correct_answer'
        'mode': 1  # Fixed value
    }