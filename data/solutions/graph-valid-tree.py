from typing import List, Dict

class Solution:
    def validTree(self, n: int, edges: List[List[int]]) -> bool:
        if not edges:
            return True
        
        graph: Dict[int, List[int]] = {i: [] for i in range(n)}
        
        for edge in edges:
            u, v = edge
            graph[u].append(v)
            graph[v].append(u)
        
        visited: set = set()
        
        def dfs(node: int) -> bool:
            if node in visited:
                return False
            
            visited.add(node)
            
            for neighbor in graph[node]:
                if not dfs(neighbor):
                    return False
            
            return True
        
        for i in range(n):
            if len(graph[i]) == 1 and i not in visited:
                return dfs(i) or False
        
        return len(visited) == n