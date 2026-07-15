def min_val(lst):
    import numbers
    return min((x for x in lst if isinstance(x, numbers.Number)))