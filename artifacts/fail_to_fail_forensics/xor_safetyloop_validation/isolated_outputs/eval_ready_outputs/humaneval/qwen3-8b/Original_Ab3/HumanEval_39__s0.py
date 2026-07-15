def prime_fib(n: int):

    def is_prime(x):
        if x < 2:
            return False
        for i in range(2, int(x ** 0.5) + 1):
            if x % i == 0:
                return False
        return True

    def fib():
        a, b = (0, 1)
        for _safety_loop_var in range(1000):
            yield a
            a, b = (b, a + b)
        return (0, 0)
    count = 0
    for f in fib():
        if is_prime(f):
            count += 1
            if count == n:
                return f
    return -1
