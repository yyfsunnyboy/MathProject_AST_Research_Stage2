def generate(level=1, **kwargs):
    # generate a question and correct answer

The generate function needs to create two polynomials, apply an operation, and then format the question and answer.

Let me think about how to generate the polynomials. For each polynomial, generate terms with varying degrees. For example, for a degree 2 polynomial, terms like x², x, and constant. But how to generate the coefficients?

Let me create a helper function to generate a polynomial. For example, generate a polynomial of degree up to max_degree, with coefficients in a certain range.

But how to handle the degrees. For example, for a polynomial of degree 2, the terms are x², x, and constant. So for each term, the coefficient is random, and the exponent is from 0 to max_degree.

But the user's example has (3x² -2x +1) and (-x² +5x -3). So the polynomials are of degree 2. So perhaps for level 1, the polynomials are of degree 2, with coefficients between -5 and 5.

So, for generating a polynomial, let's say for level 1, the max degree is 2. For higher levels, maybe higher degrees. But since the user hasn't specified, perhaps the level is used to adjust the max degree and coefficient ranges.

But for simplicity, let's assume that level 1 is degree 2, coefficients between -5 and 5. For level 2, maybe degree 3, coefficients between -10 and 10. But since the user hasn't specified, perhaps the generate function can have parameters for max_degree and coefficient_range, but since the user's example uses level 1, maybe the level is used to determine these parameters.

But the user's generate function has level=1 as default. So perhaps the level is used to determine the max degree and coefficient range. For example:

level 1: max_degree=2, coefficient_range=(-5,5)
level 2: max_degree=3, coefficient_range=(-10,10)
etc.

But how to implement that. Let's proceed.

Now, for generating the polynomials. Let's create a function to generate a polynomial. For example, generate a polynomial with terms up to max_degree, each term's coefficient is random in the given range.

But how to represent the polynomial. Let's represent it as a list of coefficients, where the index corresponds to the exponent. For example, [a, b, c] represents a*x² + b*x + c. Wait, no. Wait, the index would be the exponent. So for exponents 0, 1, 2, the coefficients are [c, b, a]. Wait, no. Let me think. For example, 3x² -2x +1 would be represented as [3, -2, 1], where the index 0 is x^0 (constant term), index 1 is x^1, index 2 is x^2. Wait, no. Wait, if the list is [a, b, c], then it's a*x^0 + b*x^1 + c*x^2? No, that would be a + b x + c x². So the index corresponds to the exponent. So for exponents 0, 1, 2, the coefficients are [a, b, c]. So the list is ordered from x^0 to x^max_degree.

Wait, but when generating, for a max_degree of 2, the exponents are 0, 1, 2. So the coefficients list would have length max_degree + 1. For example, for max_degree 2, the list has 3 elements: [c0, c1, c2], representing c0 + c1 x + c2 x².

But when generating the polynomial, we need to create terms for each exponent from 0 to max_degree. So for each exponent, generate a coefficient.

But how to generate the coefficients. For example, for each exponent, generate a random integer between min_coeff and max_coeff.

So, the helper function to generate a polynomial could be:

def generate_poly(max_degree, min_coeff, max_coeff):
    coeffs = []
    for i in range(max_degree + 1):
        coeffs.append(random.randint(min_coeff, max_coeff))
    return coeffs

But then, when converting to a string, we need to format each term. For example, for coeffs [3, -2, 1], the polynomial is 3x² -2x +1.

But how to handle terms with zero coefficients. For example, if a coefficient is zero, we can skip that term. But in the generate function, we need to ensure that the generated polynomials have non-zero coefficients for some terms. Wait, but the user's example includes terms like -x², which is allowed. So perhaps the generate function can have coefficients that can be zero, but when converting to the string, we need to handle that.

But for the purpose of generating the question, even if some coefficients are zero, the polynomial is still valid. However, when generating the question, we need to format the polynomial correctly.

So, the next step is to convert the coefficients list into a string representation of the polynomial. For example, for coeffs [3, -2, 1], the string is "3x^2 - 2x + 1".

But how to handle exponents. For exponents 0, it's the constant term. For exponent 1, it's x. For exponent 2, x^2, etc.

So, the function to convert the coefficients to a string:

def poly_to_str(coeffs):
    terms = []
    for i, coeff in enumerate(coeffs):
        if coeff == 0:
            continue
        if i == 0:
            term = f"{coeff}"
        elif i == 1:
            term = f"{coeff}x"
        else:
            term = f"{coeff}x^{i}"
        terms.append(term)
    # Handle the case where all coefficients are zero, but that's unlikely
    if not terms:
        return "0"
    # Combine terms with + or -
    # Need to handle signs
    # For example, if the first term is negative, we need to adjust the signs
    # Let's build the string with proper signs
    # Start with the first term
    result =