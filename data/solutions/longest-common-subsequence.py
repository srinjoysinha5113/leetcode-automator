from typing import List

class Solution:
    def longestCommonSubsequence(self, text1: str, text2: str) -> int:
        m = len(text1)
        n = len(text2)

        # Create a table to store lengths of longest common subsequences of substrings.
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        # Fill the table in bottom-up manner
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if text1[i - 1] == text2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        # The value at the bottom-right corner of the table is the length of longest common subsequence.
        return dp[m][n]