import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    for _ in range(100):  # 多迭代確保一定能找到樣本
        try:
            # Step 1: 生成各分子/分母（分母只取 2-10 正整數，分子可正可負）
            n1 = IntegerOps.random_nonzero(-99, 99)
            d1 = IntegerOps.random_nonzero(2, 10)
            n2 = IntegerOps.random_nonzero(-99, 99)
            d2 = IntegerOps.random_nonzero(2, 10)
            n3 = IntegerOps.random_nonzero(-99,