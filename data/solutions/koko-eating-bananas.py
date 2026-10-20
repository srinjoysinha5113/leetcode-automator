from typing import List

class Solution:
    def minEatingSpeed(self, piles: List[int], h: int) -> int:
        def canEat(k: int) -> bool:
            hours = 0
            for pile in piles:
                hours += (pile - 1) // k + 1
            return hours <= h

        left, right = 1, max(piles)
        while left < right:
            mid = left + (right - left) // 2
            if canEat(mid):
                right = mid
            else:
                left = mid + 1
        return left