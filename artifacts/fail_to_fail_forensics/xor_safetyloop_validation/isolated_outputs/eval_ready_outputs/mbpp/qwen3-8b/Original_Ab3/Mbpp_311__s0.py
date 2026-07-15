def set_left_most_unset_bit(n):
    return n | n ** (n + 1) & -(n + 1) ** n
