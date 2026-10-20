from typing import List

class Solution:
    def maxArea(self, height: List[int]) -> int:
        max_area = 0
        left = 0
        right = len(height) - 1
        
        while left < right:
            current_height = min(height[left], height[right])
            current_area = current_height * (right - left)
            
            if current_area > max_area:
                max_area = current_area
            
            if height[left] < height[right]:
                left += 1
            else:
                right -= 1
        
        return max_area