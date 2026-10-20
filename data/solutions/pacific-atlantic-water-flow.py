from typing import List

class Solution:
    def pacificAtlantic(self, heights: List[List[int]]) -> List[List[int]]:
        m, n = len(heights), len(heights[0])
        
        # Directions to explore (up, down, left, right)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        # Pacific Ocean
        pacific_reachable = [[False] * n for _ in range(m)]
        stack_pacific = []
        for i in range(m):
            for j in range(n):
                if heights[i][j] > 0:
                    stack_pacific.append((i, j))
                    pacific_reachable[i][j] = True
        
        while stack_pacific:
            x, y = stack_pacific.pop()
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < m and 0 <= ny < n and not pacific_reachable[nx][ny] and heights[nx][ny] >= heights[x][y]:
                    stack_pacific.append((nx, ny))
                    pacific_reachable[nx][ny] = True
        
        # Atlantic Ocean
        atlantic_reachable = [[False] * n for _ in range(m)]
        stack_atlantic = []
        for i in range(m):
            for j in range(n):
                if heights[i][j] > 0:
                    stack_atlantic.append((i, j))
                    atlantic_reachable[i][j] = True
        
        while stack_atlantic:
            x, y = stack_atlantic.pop()
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < m and 0 <= ny < n and not atlantic_reachable[nx][ny] and heights[nx][ny] >= heights[x][y]:
                    stack_atlantic.append((nx, ny))
                    atlantic_reachable[nx][ny] = True
        
        # Find cells reachable to both oceans
        result = []
        for i in range(m):
            for j in range(n):
                if pacific_reachable[i][j] and atlantic_reachable[i][j]:
                    result.append([i, j])
        
        return result