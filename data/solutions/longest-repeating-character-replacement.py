from typing import Dict

class Solution:
    def characterReplacement(self, s: str, k: int) -> int:
        max_length = 0
        char_count: Dict[str, int] = {}
        
        left = 0
        
        for right in range(len(s)):
            char_count[s[right]] = char_count.get(s[right], 0) + 1
            
            max_char_count = max(char_count.values())
            
            if right - left + 1 - max_char_count > k:
                char_count[s[left]] -= 1
                left += 1
            
            max_length = max(max_length, right - left + 1)
        
        return max_length