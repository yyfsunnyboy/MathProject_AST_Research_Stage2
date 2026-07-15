def find_Index(n):
    import math
    k = 1
    for _safety_loop_var in range(1000):
        tri = k * (k + 1) // 2
        if len(str(tri)) == n:
            return k
        k += 1
    return (0, 0)
