from typing import List

class Solution:
    def longestIncreasingPath(self, matrix: List[List[int]]) -> int:
        if not matrix:
            return 0
        
        m, n = len(matrix), len(matrix[0])
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        def dfs(i, j):
            """Depth-first search to find the longest increasing path."""
            if memo[i][j] != -1:
                return memo[i][j]
            
            max_length = 1
            for dx, dy in directions:
                x, y = i + dx, j + dy
                if (0 <= x < m) and (0 <= y < n) and matrix[x][y] > matrix[i][j]:
                    max_length = max(max_length, dfs(x, y) + 1)
            
            memo[i][j] = max_length
            return max_length
        
        memo = [[-1] * n for _ in range(m)]
        
        longest_path = 0
        for i in range(m):
            for j in range(n):
                longest_path = max(longest_path, dfs(i, j))
        
        return longest_path