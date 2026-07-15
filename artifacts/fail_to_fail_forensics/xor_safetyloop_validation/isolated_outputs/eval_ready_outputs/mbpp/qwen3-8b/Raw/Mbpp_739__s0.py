def find_Index(n):
    import math
    k = 1
    while True:
        tri = k * (k + 1) // 2
        if len(str(tri)) == n:
            return k
        k += 1
