Okay, let's tackle this problem step by step. The user wants me to generate a math problem that mirrors the given example exactly in structure and complexity. Let me start by understanding the requirements thoroughly.

First, the target question is $(-60) \div [(-7) \times 2 - 1]$. I need to replicate this structure precisely. The key elements here are:

- A division operation (÷)
- A bracketed expression with a multiplication and subtraction
- Specific numbers and their signs

The example has four numbers: -60, -7, 2, and 1. The operations are one division and one multiplication, along with a subtraction inside the brackets. The structure must maintain exactly two binary operators (÷ and -) and three numbers in the bracketed part.

Now, following the guidelines from section D, I need to map each constant in the original problem to variables while preserving the structure. Let's break down the original expression:

Original: (-60) ÷ [(-7) × 2 - 1]

Breaking it into parts:
- The main division is between -60 and the bracketed part.
- Inside the brackets, there's a multiplication of -7 and 2, then subtracting 1.

So, variables should replace each number while keeping their positions. Let me assign variables v1, v2, v3, v4 based on their positions in the original problem. Wait, but how many variables do I need? The original has four numbers: -60, -7, 2, and 1. So variables v1 to v4.

But according to D3, each variable's range depends on its position and sign. Let me check:

Original numbers:
- -60 (negative) → v1 should be in [-100, -1]
- -7 (negative) → v2 in [-10, -1]
- 2 (positive) → v3 in [1, 10]
- 1 (positive) → v4 in [1, 15]

Wait, but the original has four numbers. However, looking at the example structure again: the main division is between a number and a bracketed expression. Inside the brackets, there's a multiplication of two numbers and then subtracting another. So total numbers are four.

But according to D3, v1 (first variable) should be in [-100,-1], v2 in [-10,-1], etc. But wait, the original example has -60 as the first number, which is a negative value. So v1 would take that range. Similarly for others.

Now, I need to generate variables with these ranges and ensure that when calculating, the division results in an integer. The step D6 requires checking if the numerator divided by denominator is an integer. Let me think about how to structure this.

The original problem's calculation is (-60) ÷ [(-7)*2 -1] = (-60) ÷ (-14 -1) = (-60)/(-15) = 4. So the final answer is 4.

In my generated problem, I need to ensure that when substituting variables, the division results in an integer. Let me outline the steps:

1. Assign variables v1 (for -60), v2 (for -7), v3 (for 2), v4 (for 1) with their respective ranges.
2. Compute numerator and denominator based on the structure: numerator is v1, denominator is (v2 * v3 - v4).
3. Check if denominator is not zero and if abs(numerator) % abs(denominator) == 0. If yes, proceed.

Wait, but in the original example, the denominator is (-7)*2 -1 = -15. The numerator is -60. So the division is -60 / -15 = 4. So for my generated problem, I need to ensure that when substituting variables, the same structure holds.

But according to D3, v1 (first number) should be in [-100,-1], so let's generate v1 as a negative value. Similarly, v2 is another negative, v3 and v4 are positive.

So, for example:

v1 = IntegerOps.random_nonzero(-100, -1)
v2 = IntegerOps.random_nonzero(-10, -1)
v3 = IntegerOps.random_nonzero(1, 10)
v4 = IntegerOps.random_nonzero(1, 15)

Then compute denominator as (v2 * v3 - v4). Wait, but in the original example, it's (-7)*2 -1. So the structure is (v2 * v3) - v4.

But wait, the original problem has a subtraction after multiplication. So the denominator is (v2 * v3) - v4. Then the main division is v1 divided by that denominator.

So numerator = v1
denominator = (v2 * v3) - v4

Then check if abs(numerator) % abs(denominator) == 0, and denominator != 0.

Once that's satisfied, proceed to build the eval_str and math_str.

For the eval_str, it should be something like "abs(v1) / ((v2 * v3) - v4)" but wait, in the original example, the division is between -60 and the bracketed part. However, since we're using variables that can be negative, perhaps we need to handle signs correctly.

Wait, the original problem's denominator is (-7)*2 -1 = -15. The numerator is -60. So the division is -60 / -15 = 4. But in our generated problem, if v1 is a negative number (like -60), and the denominator is also negative (like -15), then dividing them gives a positive result.

But according to D6, we need to check if abs(numerator) % abs(denominator) == 0. So regardless of signs, as long as the absolute values divide evenly, it's okay.

So in code:

numerator = v1
denominator = (v2 * v3) - v4

Check if denominator is not zero and abs(numerator) % abs(denominator) == 0.

Once that's true, compute final_ans = abs(numerator) // abs(denominator). But since the actual division could be positive or negative based on signs, but in the example it was positive. However, according to the problem statement, we need to ensure that the result is an integer.

Now, for the math_str, it should mirror the original structure with LaTeX formatting. The original has a division symbol ÷, and inside the brackets, multiplication × and subtraction -.

So the math_str would be something like:

\left| {fmt(v1)} \div [ {fmt(v2)} \times {fmt(v3)} - {fmt(v4)} ] \right|

Wait, but in the original example, it's (-60) ÷ [(-7) × 2 - 1]. The LaTeX is written as $(-60) \div [(-7) \times 2 - 1]$. So the structure is: numerator (v1) divided by a bracketed expression containing multiplication and subtraction.

But in our generated problem, we need to ensure that the same structure is maintained. However, according to the example's structure, there are two binary operators: one division and one subtraction inside the brackets. Also, three numbers inside the brackets (v2, v3, v4), but wait, original has three numbers inside the brackets? Let me check:

Original bracketed part: (-7) × 2 -1 → that's three numbers: -7, 2, 1. So in our variables, v2, v3, v4.

So the structure is: [v2 × v3 - v4], which has two operations (× and -), but according to the problem statement, the total binary operators must be consistent with the original example. The original has one division and one subtraction, totaling two operators. So our generated problem should have exactly two binary operators.

Wait, in the original example: there's a division (÷) and a subtraction (-). That's two operators. So our generated problem must also have two operators: one division and one subtraction inside the brackets.

So the structure is:

Main operation: division (÷)
Inside the bracketed part: multiplication (×) followed by subtraction (-)

Thus, in code, the denominator is calculated as (v2 * v3) - v4. So that's two operations: × and -, totaling two binary operators. The main division is another operator, making three total? Wait no, the original example has one division and one subtraction, totaling two operators. Let me recount:

Original problem: (-60) ÷ [(-7) × 2 - 1]

Breaking down:
- Division (÷)
- Multiplication (×)
- Subtraction (-)

Wait that's three binary operators. But according to the user's note in G, the example has two binary operators: division and subtraction. Wait, maybe I miscounted.

Original problem structure:

The main operation is division between -60 and the bracketed part. Inside the bracketed part, there's a multiplication (×) and a subtraction (-). So total of three binary operators? Or does the subtraction count as one?

Wait, in the original example: [(-7) × 2 - 1]. The operations inside are × and -, so two operators. Then the main division is another operator. Total three operators. But according to the user's note in G under "硬性一致性