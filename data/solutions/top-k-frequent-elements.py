from typing import List
import heapq

class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        count = {}
        
        # Count frequency of each number
        for num in nums:
            if num not in count:
                count[num] = 1
            else:
                count[num] += 1
        
        # Use a heap to get the top k frequent elements
        return heapq.nlargest(k, count.keys(), key=count.get)