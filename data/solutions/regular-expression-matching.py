class Solution:
    def isMatch(self, s: str, p: str) -> bool:
        dp = [[False] * (len(p) + 1) for _ in range(len(s) + 1)]
        
        # An empty pattern matches an empty string.
        dp[0][0] = True
        for j in range(1, len(p) + 1):
            if p[j - 1] == '*':
                dp[0][j] = dp[0][j - 2]
        
        for i in range(1, len(s) + 1):
            for j in range(1, len(p) + 1):
                match = i > 0 and p[j - 1] == s[i - 1] or p[j - 1] == '.'
                if p[j - 1] == '*':
                    dp[i][j] = dp[i][j - 2] or (match and dp[i - 1][j])
                else:
                    dp[i][j] = match and dp[i - 1][j - 1]
        
        return dp[len(s)][len(p)]