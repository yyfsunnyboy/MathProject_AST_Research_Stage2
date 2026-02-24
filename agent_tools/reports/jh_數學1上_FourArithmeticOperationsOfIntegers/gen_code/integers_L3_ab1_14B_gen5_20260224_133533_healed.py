import random

def generate(level=1, **kwargs):
    question = []
    operations = ['+', '-', '*', '//']
    signs = ['+', '-']
    absolute = ['abs', 'abs']
    numbers = []
    ops = []
    brackets = 0

    if level == 1:
        num_range = (1, 20)
    else:
        num_range = (10, 100)

    for _ in range(4):
        if random.random() < 0.3:
            ops.append(random.choice(operations))
        else:
            ops.append(random.choice(operations))

    for _ in range(5):
        if random.random() < 0.5:
            numbers.append(random.randint(*num_range))
        else:
            numbers.append(random.randint(*num_range) * -1)

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"{random.choice(signs)}{abs(numbers[i])}"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"{random.choice(signs)}{abs(numbers[i])}"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"{random.choice(absolute)}({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.2:
            numbers[i] = f"({numbers[i]})"

    for i in range(len(numbers)):
        if random.random() < 0.1:
            numbers[i] = f"abs({numbers[i]})"

    for i in range(len(numbers)):
        if random