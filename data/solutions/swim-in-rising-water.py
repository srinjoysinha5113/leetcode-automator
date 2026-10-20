from collections import deque
import heapq

class Solution:
    def swimInWater(self, grid: list[list[int]]) -> int:
        n = len(grid)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        pq = [(grid[0][0], 0, 0)]
        visited = set((0, 0))
        
        while pq:
            time, x, y = heapq.heappop(pq)
            
            if (x, y) == (n - 1, n - 1):
                return time
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                if 0 <= nx < n and 0 <= ny < n and (nx, ny) not in visited:
                    if grid[nx][ny] <= time:
                        heapq.heappush(pq, (time + 1, nx, ny))
                        visited.add((nx, ny))
        
        return -1