from typing import List

class Solution:
    def minCostClimbingStairs(self, cost: List[int]) -> int:
        dp = [0] * 2
        
        for i in range(len(cost)):
            dp[i % 2] = min(dp[(i - 1) % 2] + cost[i], dp[(i - 2) % 2] + cost[i])
        
        return min(dp)