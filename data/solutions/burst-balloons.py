from typing import List

class Solution:
    def maxCoins(self, nums: List[int]) -> int:
        n = len(nums)
        nums = [1] + nums + [1]
        
        dp = [[0] * (n + 2) for _ in range(n + 2)]
        
        for i in range(1, n + 2):
            for j in range(i):
                for k in range(i + 1, n + 2):
                    dp[j][k] = max(dp[j][k], dp[j][i - 1] + dp[i][k] - 2 * nums[j - 1] * nums[i] * nums[k])
        
        return dp[1][n]