from typing import List

class Solution:
    def minCostConnectPoints(self, points: List[List[int]]) -> int:
        n = len(points)
        graph = [[float('inf')] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                x1, y1 = points[i]
                x2, y2 = points[j]
                dist = abs(x1 - x2) + abs(y1 - y2)
                graph[i][j] = graph[j][i] = dist
        
        visited = [False] * n
        parent = [-1] * n
        edges = []
        
        for i in range(n):
            if not visited[i]:
                stack = [i]
                visited[i] = True
                while stack:
                    node = stack.pop()
                    for j in range(n):
                        if graph[node][j] != float('inf') and not visited[j]:
                            edges.append((graph[node][j], node, j))
                            visited[j] = True
                            parent[j] = node
                            stack.append(j)
        
        edges.sort(key=lambda x: x[0])
        
        cost = 0
        for edge in edges:
            if parent[edge[1]] != -1:
                continue
            cost += edge[0]
            visited[edge[2]] = True
        
        return cost