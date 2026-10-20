from typing import List

class Solution:
    def countComponents(self, n: int, edges: List[List[int]]) -> int:
        graph = {i: [] for i in range(1, n + 1)}
        
        for u, v in edges:
            if u not in graph or v not in graph:
                continue
            graph[u].append(v)
            graph[v].append(u)
        
        visited = set()
        
        def dfs(node):
            if node not in graph:
                return False
            if node in visited:
                return False
            visited.add(node)
            for neighbor in graph[node]:
                if not dfs(neighbor):
                    return False
            return True
        
        count = 0
        for i in range(1, n + 1):
            if i not in visited:
                dfs(i)
                count += 1
        
        return count