from typing import List

class Solution:
    def wallsAndGates(self, rooms: List[List[int]]) -> None:
        rows, cols = len(rooms), len(rooms[0])
        
        # Initialize directions for DFS
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        # Create a queue to store cells to visit and their distances from the gate
        queue = []
        
        # Find the first cell with value -1 (gate) and add it to the queue
        for r in range(rows):
            for c in range(cols):
                if rooms[r][c] == -1:
                    queue.append((r, c))
        
        # If there are no gates, return immediately
        if not queue:
            return
        
        # Perform BFS from each gate
        while queue:
            r, c = queue.pop(0)
            
            # Visit all neighboring cells and update their distances
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                
                # Check if the neighboring cell is within bounds and has not been visited yet
                if 0 <= nr < rows and 0 <= nc < cols and rooms[nr][nc] == float('inf'):
                    rooms[nr][nc] = rooms[r][c] + 1
                    
                    # Add the neighboring cell to the queue for further visits
                    queue.append((nr, nc))