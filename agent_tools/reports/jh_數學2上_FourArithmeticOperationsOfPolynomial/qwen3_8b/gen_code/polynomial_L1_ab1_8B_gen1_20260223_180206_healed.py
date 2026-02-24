Okay, I need to create a Python program that generates math problems about polynomial arithmetic operations. The user wants two functions: generate and check. Let me start by understanding the requirements.

First, the generate function must create questions involving addition, subtraction, multiplication, or division of polynomials. The level parameter is for difficulty, but the example shows level 1. Maybe level 1 is addition/subtraction, level 2 is multiplication, and maybe level 3 is division? But the user hasn't specified, so perhaps the initial version will handle addition and multiplication, and maybe later expand.

The generate function should return a dictionary with 'question_text', 'answer', 'correct_answer', and 'mode'. The question text needs to be in LaTeX format, like $(...)$.

For the check function, it must compare the user's answer with the correct one, returning a dictionary with 'correct' and 'result'.

Now, how to generate the polynomials. Let's think about the operations. For addition and subtraction, we can generate two polynomials and add or subtract them. For multiplication, generate two polynomials and multiply. Division might be more complex, but maybe the user wants to include it. However, the example shows multiplication, so maybe the initial version includes addition, subtraction, and multiplication.

Let me outline the steps for generate:

1. Choose a random operation: addition, subtraction, multiplication.
2. Generate two polynomials with random coefficients.
3. For addition/subtraction, combine them and simplify.
4. For multiplication, multiply them and simplify.
5. Format the question and the correct answer in LaTeX.

But how to represent polynomials? Maybe as dictionaries where keys are exponents and values are coefficients. For example, {2: 3, 1: -2, 0: 1} represents 3x² -2x +1.

But generating random polynomials with varying degrees. Let's say for level 1, the polynomials are of degree up to 2. For higher levels, maybe higher degrees. But the user hasn't specified levels, so perhaps the initial version uses level 1, which could be addition or subtraction.

Wait, the user says the generate function has a level parameter. So maybe level 1 is addition/subtraction, level 2 is multiplication, etc. But the example shows both addition and multiplication. So perhaps the level determines the operation type.

But the user's example includes both addition and multiplication. So maybe the generate function can randomly select between different operations based on the level. For example, level 1 could be addition or subtraction, level 2 multiplication, and level 3 division. But the user hasn't specified, so perhaps the initial version includes addition and multiplication, and the level parameter is for different types of operations.

Alternatively, maybe the level is for the complexity, like degree of polynomials. For example, level 1 has degree 1, level 2 degree 2, etc. But the user's example shows degree 2 polynomials. So perhaps the level determines the maximum degree of the polynomials.

But the user's example shows both addition and multiplication. So maybe the generate function can randomly select between different operations. Let me think.

The generate function needs to create a question. Let's first handle addition and subtraction. For example, generate two polynomials, then add or subtract them. For multiplication, generate two polynomials and multiply them.

So, the generate function will first select an operation (addition, subtraction, multiplication). Then generate two polynomials, perform the operation, and format the question and answer.

But how to generate the polynomials. Let's think about generating polynomials with random coefficients. For example, for a polynomial of degree up to 2, generate coefficients for x², x, and the constant term. The coefficients can be integers between -5 and 5, but maybe with some randomness.

But the user wants the numbers to be random each time. So for each polynomial, generate random coefficients. Let's say for each polynomial, the maximum degree is 2. So for each polynomial, generate coefficients for x², x, and the constant term. The coefficients can be integers between -5 and 5, but maybe with some variation.

Wait, but the example shows (3x² -2x +1) + (-x² +5x -3). So the coefficients are integers. So the generate function should generate polynomials with integer coefficients.

So, for generating a polynomial, we can create a dictionary where each key is the exponent, and the value is the coefficient. For example, {2: 3, 1: -2, 0: 1} represents 3x² -2x +1.

But how to generate these polynomials. Let's say for each polynomial, we generate coefficients for exponents 0, 1, 2. But maybe the degree can vary. For example, some polynomials might have degree 1, others degree 2. But to keep it simple, maybe generate polynomials with degrees up to 2, but some may have lower degrees.

But how to handle that. For example, for a polynomial, generate coefficients for x², x, and constant term. But if the coefficient for x² is zero, then the degree is lower. However, generating a polynomial with leading zero might not be desired. So perhaps ensure that the leading coefficient is non-zero. Wait, but the user's example includes polynomials like -x² +5x -3, which has a non-zero x² term. So maybe for each polynomial, generate coefficients for x², x, and constant term, but ensure that the leading coefficient (for x²) is non-zero. Wait, but maybe not. For example, a polynomial could be of degree 1, like 2x +3. So perhaps the generate function should allow for varying degrees.

Alternatively, for simplicity, generate polynomials with degrees up to 2, but allow for lower degrees. However, when generating, we need to make sure that the leading coefficient is not zero. Wait, but that's complicated. Maybe for the purpose of this problem, we can generate polynomials with coefficients for x², x, and constant term, but allow for some coefficients to be zero. For example, a polynomial could be 0x² + 3x + 1, which simplifies to 3x +1. But in that case, the question might have redundant terms. However, the user's example includes terms like -x², so perhaps it's acceptable.

But generating polynomials with leading zero might not be ideal. So perhaps for each polynomial, generate coefficients for x², x, and constant term, but ensure that the x² coefficient is non-zero. Wait, but that would make all polynomials have degree 2. But the user's example includes a polynomial with x² term, but maybe other polynomials could have lower degrees. Hmm.

Alternatively, perhaps the generate function can generate polynomials with varying degrees. For example, for a polynomial, generate a random degree between 0 and 2, and then generate coefficients for that degree. But that complicates things. Maybe for simplicity, generate polynomials with up to degree 2, and allow for some coefficients to be zero. But when generating, ensure that the leading coefficient (for the highest degree present) is non-zero. For example, if the highest degree is 2, then the x² coefficient is non-zero. If the highest degree is 1, then the x coefficient is non-zero, etc.

But this requires checking the highest degree present. For example, if the x² coefficient is zero, but x coefficient is non-zero, then the highest degree is 1. So, perhaps for generating a polynomial, we can generate coefficients for x², x, and constant term, but ensure that the highest non-zero coefficient is non-zero. However, this might complicate the code.

Alternatively, for simplicity, generate polynomials with coefficients for x², x, and constant term, and allow for some coefficients to be zero. Then, when combining them, the resulting polynomial may have terms that cancel out. For example, adding (3x² -2x +1) and (-3x² +2x -1) would result in 0, but that's a possible case. However, the user's example shows that the answer is simplified, so the code must handle combining like terms.

So, the steps for generating a question:

1. Choose an operation: addition, subtraction, multiplication.
2. Generate two polynomials.
3. Perform the operation on the two polynomials.
4. Simplify the result.
5. Format the question and the correct answer.

Now, how to represent polynomials. Let's use dictionaries where keys are exponents and values are coefficients. For example, {2: 3, 1: -2, 0: 1} represents 3x² -2x +1.

For generating a polynomial, we can generate coefficients for exponents 0, 1, 2. Let's say for each exponent, generate a random integer between -5 and 5. But to avoid leading zeros, perhaps for the highest exponent present, the coefficient is non-zero. However, this might be complex. Alternatively, just generate coefficients for all exponents, and during simplification, combine like terms.

But for the purpose of generating the question, perhaps it's acceptable to have polynomials with leading zeros. For example, a polynomial could be 0x² + 3x + 1, which simplifies to 3x +1. However, when generating the question, the user might want to see the full polynomial, even if some terms cancel out. But the example shows that the answer is simplified, so the code must handle that.

So, the generate function will generate two polynomials, perform the operation, and then simplify the result.

Now