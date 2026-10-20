from typing import List
from collections import deque

class Solution:
    def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
        if not nums or k == 0:
            return []

        # Initialize the result list and the deque to store indices of elements in the window
        result = []
        dq = deque()

        for i, num in enumerate(nums):
            # Remove elements from the back of the deque that are out of the current window
            while dq and dq[0] < i - k + 1:
                dq.popleft()

            # Remove elements from the front of the deque that are smaller than the current element
            while dq and nums[dq[-1]] < num:
                dq.pop()

            # Add the current index to the back of the deque
            dq.append(i)

            # If the window is full, add the maximum element to the result list
            if i >= k - 1:
                result.append(nums[dq[0]])

        return result