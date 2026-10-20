from typing import List

class Solution:
    def isValidSudoku(self, board: List[List[str]]) -> bool:
        rows = [set() for _ in range(9)]
        cols = [set() for _ in range(9)]
        boxes = [set() for _ in range(9)]

        for i in range(9):
            for j in range(9):
                val = board[i][j]
                if val == '.':
                    continue
                num = int(val)
                box_index = (i // 3) * 3 + j // 3

                # Check row and column
                if num in rows[i] or num in cols[j]:
                    return False
                rows[i].add(num)
                cols[j].add(num)

                # Check box
                if num in boxes[box_index]:
                    return False
                boxes[box_index].add(num)

        return True