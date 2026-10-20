from typing import List

class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        n = len(nums)
        
        # Initialize left and right prefix/suffix products arrays
        L = [1] * n
        R = [1] * n
        
        # Compute the left prefix products
        for i in range(1, n):
            L[i] = nums[i - 1] * L[i - 1]
        
        # Compute the right suffix products
        for i in range(n - 2, -1, -1):
            R[i] = nums[i + 1] * R[i + 1]
        
        # Combine left and right prefix/suffix products arrays
        ans = [L[i] * R[i] for i in range(n)]
        
        return ans