from typing import List

class Solution:
    def carFleet(self, target: int, position: List[int], speed: List[int]) -> int:
        n = len(position)
        cars = [(pos/speed[i], i) for i, pos in enumerate(position)]
        
        cars.sort(reverse=True)
        
        fleets = 0
        prev_time = 0
        
        for time, idx in cars:
            if target / speed[idx] < time:
                continue
            if prev_time <= target - (time - prev_time):
                fleets += 1
                prev_time = time
        return fleets