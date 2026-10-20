from collections import Counter

class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        if len(s1) > len(s2):
            return False
        
        s1_count = Counter(s1)
        for i in range(len(s2) - len(s1) + 1):
            window_count = Counter(s2[i:i+len(s1)])
            
            if window_count == s1_count:
                return True
        
        return False