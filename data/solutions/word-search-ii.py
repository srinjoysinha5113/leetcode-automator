from typing import List

class Solution:
    def findWords(self, board: List[List[str]], words: List[str]) -> List[str]:
        m, n = len(board), len(board[0])
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        word_set = set(words)
        
        def dfs(i, j, word):
            if not word:
                return True
            if i < 0 or i >= m or j < 0 or j >= n or board[i][j] not in word_set:
                return False
            temp, board[i][j] = board[i][j], '/'
            for dx, dy in directions:
                if dfs(i + dx, j + dy, word[1:]):
                    return True
            board[i][j] = temp
            return False
        
        result = set()
        for i in range(m):
            for j in range(n):
                for word in words:
                    if dfs(i, j, word):
                        result.add(word)
        
        return list(result)