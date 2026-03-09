import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    try:
        for _ in range(100):
            # Step 1: Generate numerators and denominators (denominators only take integers from 2-10, numerators can be positive or negative)
            n1 = random.randint(-99, 99)
            d1 = random.randint(2, 10)
            n2 = random.randint(-99, 99)
            d2 = random.randint(2, 10)

    except Exception as e:
        pass

    return {'correct': False, 'result': '錯誤'}