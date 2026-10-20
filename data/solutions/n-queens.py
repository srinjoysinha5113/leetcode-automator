from typing import List

class Solution:
    def solveNQueens(self, n: int) -> List[List[str]]:
        def is_valid(board: List[str], row: int, col: int) -> bool:
            for i in range(row):
                if board[i] == '.':
                    continue
                if board[i][col] == 'Q':
                    return False

                # Check the diagonal to the right and left
                x, y = i - (row - 1), col - row + abs(i - row)
                while 0 <= x < n and 0 <= y < n:
                    if board[x][y] == 'Q':
                        return False
                    x += 1
                    y -= 1

            return True

        def backtrack(board: List[str], row: int) -> None:
            if row == n:
                result.append([''.join(row) for row in board])
                return

            for col in range(n):
                if is_valid(board, row, col):
                    board[row][col] = 'Q'
                    backtrack(board, row + 1)
                    board[row][col] = '.'

        result = []
        board = [['.' for _ in range(n)] for _ in range(n)]
        backtrack(board, 0)
        return result