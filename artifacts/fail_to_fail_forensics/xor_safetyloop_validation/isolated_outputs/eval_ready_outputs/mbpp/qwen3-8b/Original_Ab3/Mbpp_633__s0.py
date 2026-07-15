def pair_xor_Sum(nums, k):
    total = 0
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            total += nums[i] ** nums[j]
    return total
