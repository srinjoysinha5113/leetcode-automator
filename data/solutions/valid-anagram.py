from typing import Dict

class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        if len(s) != len(t):
            return False
        
        char_count: Dict[str, int] = {}
        
        for char in s:
            char_count[char] = char_count.get(char, 0) + 1
        
        for char in t:
            char_count[char] = char_count.get(char, 0) - 1
            if char_count[char] < 0:
                return False
        
        return True