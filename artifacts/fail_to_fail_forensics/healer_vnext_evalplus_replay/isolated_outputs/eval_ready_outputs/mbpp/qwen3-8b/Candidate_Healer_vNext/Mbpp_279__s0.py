def is_num_decagonal(n):
    import math
    x = (1 + math.sqrt(1 + 24 * n)) / 6
    return x.is_integer() and x >= 1

def nth_decagonal_number(n):
    return n * (3 * n - 1)