from typing import List

class Solution:
    def maxProduct(self, nums: List[int]) -> int:
        if not nums:
            return 0
        
        max_product = min_product = result = nums[0]
        
        for i in range(1, len(nums)):
            temp = max_product
            
            # update max_product
            max_product = max(nums[i], temp * nums[i])
            
            # update min_product
            min_product = min(nums[i], temp * nums[i])
            
            # update result
            result = max(result, max_product)
        
        return result