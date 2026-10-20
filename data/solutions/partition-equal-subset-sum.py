from typing import List

class Solution:
    def canPartition(self, nums: List[int]) -> bool:
        total_sum = sum(nums)
        
        # If the total sum is odd, it's impossible to partition into two equal subsets
        if total_sum % 2 != 0:
            return False
        
        target_sum = total_sum // 2
        n = len(nums)
        
        # Create a dynamic programming table with size (n * target_sum) + 1
        dp = [False] * ((n * target_sum) + 1)
        dp[0] = True
        
        for num in nums:
            for i in range(target_sum, num - 1, -1):
                # If the current sum minus the number is reachable, then the current sum is also reachable
                if dp[i - num]:
                    dp[i] = True
        
        return dp[target_sum]