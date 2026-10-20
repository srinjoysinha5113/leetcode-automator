class Solution:
    def numDecodings(self, s: str) -> int:
        if not s or s[0] == '0':
            return 0
        
        n = len(s)
        dp = [0] * (n + 1)
        
        # Base case: there is one way to decode an empty string
        dp[0] = 1
        dp[1] = 1
        
        for i in range(2, n + 1):
            if s[i - 1] != '0':
                dp[i] += dp[i - 1]
            
            if i >= 2 and (s[i - 2] == '1' or (s[i - 2] == '2' and s[i - 1] <= '6')):
                dp[i] += dp[i - 2]
        
        return dp[n]