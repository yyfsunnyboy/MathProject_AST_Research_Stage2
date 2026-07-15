def is_num_decagonal(n):
    import math
    return n * (3 * n - 1) == 27

def nth_decagonal_number(n):
    return n * (3 * n - 1)