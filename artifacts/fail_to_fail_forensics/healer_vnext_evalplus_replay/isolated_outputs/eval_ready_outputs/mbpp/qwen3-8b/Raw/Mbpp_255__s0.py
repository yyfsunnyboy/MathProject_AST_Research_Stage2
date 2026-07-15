from itertools import combinations_with_replacement

def combinations_colors(lst, n):
    return list(combinations_with_replacement(lst, n))
