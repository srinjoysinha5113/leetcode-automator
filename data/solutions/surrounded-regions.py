from typing import List

class Solution:
    def solve(self, board: List[List[str]]) -> None:
        """
        Do not return anything, modify board in-place instead.
        """
        
        if not board or not board[0]:
            return
        
        rows, cols = len(board), len(board[0])
        
        def dfs(r: int, c: int) -> None:
            """Mark all connected 'O' cells as visited."""
            if 0 <= r < rows and 0 <= c < cols and board[r][c] == 'O':
                board[r][c] = '#'
                dfs(r - 1, c)
                dfs(r + 1, c)
                dfs(r, c - 1)
                dfs(r, c + 1)
        
        def restore() -> None:
            """Replace '#' with 'O' to restore the original board."""
            for r in range(rows):
                for c in range(cols):
                    if board[r][c] == '#':
                        board[r][c] = 'O'
        
        # Mark all connected 'O' cells as visited.
        dfs(0, 0)
        dfs(rows - 1, 0)
        dfs(0, cols - 1)
        dfs(rows - 1, cols - 1)
        
        # Replace '#' with 'X'.
        for r in range(rows):
            for c in range(cols):
                if board[r][c] == '#':
                    board[r][c] = 'X'
        
        # Restore the original board.
        restore()