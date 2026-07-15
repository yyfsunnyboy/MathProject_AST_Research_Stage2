def differ_At_One_Bit_Pos(a, b):
    return bin(a ** b).count('1') == 1
