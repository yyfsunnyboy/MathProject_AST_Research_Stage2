# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: gemini-2.5-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 29.87s | Tokens: In=573, Out=1453
# Created At: 2026-02-05 23:54:01
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def _format_polynomial(terms):
    """
    Formats a list of (coefficient, power) tuples into a polynomial string.
    Examples:
    [(3, 3), (-5, 2), (2, 0)] -> "3x^3 - 5x^2 + 2"
    [(9, 2), (-10, 1)] -> "9x^2 - 10x"
    [(18, 1), (-10, 0)] -> "18x - 10"
    [(0, 0)] -> "0"
    """
    # Filter out zero coefficients and sort by power in descending order
    non_zero_terms = sorted([t for t in terms if t[0] != 0], key=lambda x: x[1], reverse=True)

    if not non_zero_terms:
        return "0"

    poly_str_parts = []
    
    # Handle the first term separately to avoid leading '+' or ' - '
    first_coeff, first_power = non_zero_terms[0]
    first_term_str = ""
    if first_coeff < 0:
        first_term_str += "-"
    
    abs_first_coeff = abs(first_coeff)
    if abs_first_coeff != 1 or first_power == 0: # Include coefficient if not 1 or if it's a constant
        first_term_str += str(abs_first_coeff)
    
    if first_power > 0: # Include 'x' if power is not 0
        first_term_str += "x"
    
    if first_power > 1: # Include '^power' if power is greater than 1
        first_term_str += f"^{first_power}"
    
    poly_str_parts.append(first_term_str)

    # Handle subsequent terms
    for i in range(1, len(non_zero_terms)):
        coeff, power = non_zero_terms[i]
        term_str = ""
        
        if coeff > 0:
            term_str += " + "
        else: # coeff < 0
            term_str += " - "
        
        abs_coeff = abs(coeff)
        if abs_coeff != 1 or power == 0:
            term_str += str(abs_coeff)
        
        if power > 0:
            term_str += "x"
        
        if power > 1:
            term_str += f"^{power}"
        
        poly_str_parts.append(term_str)

    return "".join(poly_str_parts)

def _differentiate_polynomial(terms):
    """
    Calculates the derivative of a polynomial represented by a list of (coefficient, power) tuples.
    """
    new_terms = []
    for coeff, power in terms:
        if power > 0:
            new_coeff = coeff * power
            new_power = power - 1
            new_terms.append((new_coeff, new_power))
    return new_terms

def generate(level=1, **kwargs):
    """