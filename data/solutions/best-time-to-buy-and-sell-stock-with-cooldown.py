from typing import List

class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        if not prices:
            return 0
        
        n = len(prices)
        dp = [[0] * 3 for _ in range(n)]
        
        # Initialize base case where no transaction is allowed
        dp[0][1] = -prices[0]
        dp[0][2] = 0
        
        # Fill up the dp table
        for i in range(1, n):
            # For each day, we can choose to do nothing (dp[i-1][0]), buy stock (dp[i-1][1]), or sell stock after cooldown (dp[i-1][2])
            dp[i][0] = max(dp[i-1][0], dp[i-1][2] + prices[i])
            
            # If we bought the stock on the previous day, we can either sell it today and then do nothing tomorrow
            dp[i][1] = max(dp[i-1][1], dp[i-1][0] - prices[i])
            
            # If we sold the stock on the previous day after cooldown, we can buy it today
            dp[i][2] = max(dp[i-1][2], dp[i-1][1] + prices[i])
        
        # The maximum profit is stored in dp[n-1][0]
        return dp[n-1][0]