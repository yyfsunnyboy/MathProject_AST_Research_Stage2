def toggle_middle_bits(n):
    return n ** ((1 << n.bit_length() - 2) - 1)
