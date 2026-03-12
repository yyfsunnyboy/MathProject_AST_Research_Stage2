from fractions import Fraction
from core.scaffold.domain_libs import RadicalOps, FractionOps

# Mocking the new behavior we want in domain_libs a bit to verify logic
def format_term_new(coeff, radicand, is_first=True):
    if coeff == 0:
        return ""
    
    # Handle Fraction coefficients
    if isinstance(coeff, Fraction):
        coeff_str = FractionOps.to_latex(coeff, mixed=False)
        # Handle the 1 and -1 cases for Fraction (though they should be integers, let's be safe)
        if coeff == 1:
            coeff_str = ""
        elif coeff == -1:
            coeff_str = "-"
    else:
        if coeff == 1:
            coeff_str = ""
        elif coeff == -1:
            coeff_str = "-"
        else:
            coeff_str = str(coeff)

    if radicand == 0:
        return "0"
    elif radicand == 1:
        term_str = FractionOps.to_latex(coeff) if isinstance(coeff, Fraction) else str(coeff)
    else:
        term_str = f"{coeff_str}\\sqrt{{{radicand}}}"
    
    if not is_first and coeff > 0:
        return "+" + term_str
    return term_str

def format_expression_new(terms_dict, denominator=1):
    if not terms_dict:
        return "0"
    
    sorted_radicands = sorted(terms_dict.keys())
    
    parts = []
    is_first_term = True
    for rad in sorted_radicands:
        coeff = terms_dict[rad]
        if coeff == 0:
            continue
        
        part_str = format_term_new(coeff, rad, is_first=is_first_term)
        if part_str:
            parts.append(part_str)
            is_first_term = False
    
    if not parts:
        return "0"
    
    expr = "".join(parts)
    
    if denominator != 1:
        return f"\\frac{{{expr}}}{{{denominator}}}"
    return expr

print("1. ", format_term_new(Fraction(-2, 3), 5, is_first=True))
print("2. ", format_term_new(Fraction(4, 1), 7, is_first=False))
print("3. ", format_expression_new({5: Fraction(-2, 3), 7: Fraction(4, 1)}))
print("4. ", format_expression_new({5: Fraction(2, 3), 7: Fraction(-4, 1)}))
