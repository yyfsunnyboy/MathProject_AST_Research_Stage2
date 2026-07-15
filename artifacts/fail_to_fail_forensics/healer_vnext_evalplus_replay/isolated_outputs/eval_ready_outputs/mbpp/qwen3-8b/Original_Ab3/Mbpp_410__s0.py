def min_val(lst):
    return min((x for x in lst if isinstance(x, numbers.Number)))