from typing import List
import heapq

class Solution:
    def findCheapestPrice(self, n: int, flights: List[List[int]], src: int, dst: int, k: int) -> int:
        graph = [[] for _ in range(n)]
        for u, v, p in sorted(flights):
            graph[u].append((v, p))
        
        pq = [(0, src, k + 1)]  
        
        while pq:
            cost, node, stops = heapq.heappop(pq)
            
            if node == dst and stops > 0:
                return cost
            
            for neighbor, price in graph[node]:
                new_cost = cost + price
                new_stops = stops - 1
                
                if new_stops >= 0:
                    heapq.heappush(pq, (new_cost, neighbor, new_stops))
        
        return -1