from typing import List

class Solution:
    def lengthOfLIS(self, nums: List[int]) -> int:
        if not nums:
            return 0
        
        dp = [nums[0]]
        
        for num in nums[1:]:
            if num > dp[-1]:
                dp.append(num)
            else:
                idx = binary_search(dp, num)
                dp[idx] = num
        
        return len(dp)

def binary_search(arr: List[int], target: int) -> int:
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return left