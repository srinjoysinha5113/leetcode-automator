class Solution:
    def countSubstrings(self, s: str) -> int:
        n = len(s)
        
        # Initialize dp table with all False values
        dp = [[False] * n for _ in range(n)]
        
        # All substrings of length 1 are palindromes
        for i in range(n):
            dp[i][i] = True
        
        # Check for substring of length 2
        for i in range(n - 1):
            if s[i] == s[i + 1]:
                dp[i][i + 1] = True
        
        # Check for substrings of length >= 3
        for length in range(3, n + 1):
            for start in range(n - length + 1):
                end = start + length - 1
                
                if s[start] == s[end]:
                    dp[start][end] = dp[start + 1][end - 1]
                else:
                    dp[start][end] = False
        
        # Count the number of palindromic substrings
        count = sum(sum(row) for row in dp)
        
        return count