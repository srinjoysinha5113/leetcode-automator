from typing import List

class Solution:
    def partition(self, s: str) -> List[List[str]]:
        def is_palindrome(word: str) -> bool:
            return word == word[::-1]

        def backtrack(start: int, path: List[str]) -> None:
            if start == len(s):
                result.append(path[:])
                return
            for end in range(start + 1, len(s) + 1):
                word = s[start:end]
                if is_palindrome(word):
                    path.append(word)
                    backtrack(end, path)
                    path.pop()

        result = []
        backtrack(0, [])
        return result