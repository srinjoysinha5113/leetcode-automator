from typing import Dict, List

class Solution:
    def isValid(self, s: str) -> bool:
        stack: List[str] = []
        
        mapping: Dict[str, str] = {')': '(', '}': '{', ']': '['}
        
        for char in s:
            if char in mapping.values():
                stack.append(char)
            elif char in mapping.keys():
                if not stack or mapping[char] != stack.pop():
                    return False
        
        return not stack