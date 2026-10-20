from typing import List

class Solution:
    def findTargetSumWays(self, nums: List[int], target: int) -> int:
        memo = {}
        
        def dp(i, total):
            if i == len(nums):
                return 1 if total == target else 0
            
            key = (i, total)
            if key in memo:
                return memo[key]
            
            add = dp(i + 1, total + nums[i])
            subtract = dp(i + 1, total - nums[i])
            
            memo[key] = add + subtract
            return memo[key]
        
        return dp(0, 0)