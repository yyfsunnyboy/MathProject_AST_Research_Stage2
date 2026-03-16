def generate():
    from random import randint
    import sympy as sp

    # STEP 1: Pattern Identification
    # Target: 4\sqrt{2}\times\frac{1}{6} → This is a "root × fraction" pattern → p2h_frac_mult_rad
    pattern_id = "p2h_frac_mult_rad"
    term_count = 1  # Only one term in multiplication

    # STEP 2: Get safe variables for pattern
    vars_dict = df.get_safe_vars_for_pattern(pattern_id, "easy", term_count=term_count)

    # STEP 3: Solve using DomainFunctionHelper
    latex_answer, steps = df.solve_problem_pattern(pattern_id, vars_dict, "easy")

    # STEP 4: Format question text
    question_text = df.format_question_LaTeX(pattern_id, vars_dict)

    # STEP 5: Return structured output
    return {
        "question_text": question_text,
        "correct_answer": latex_answer,
        "steps": steps
    }

def check(user_answer, correct_answer):
    # Simple string comparison for correctness
    return user_answer.strip() == correct_answer.strip()