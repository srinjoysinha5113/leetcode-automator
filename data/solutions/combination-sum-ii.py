from typing import List

class Solution:
    def combinationSum2(self, candidates: List[int], target: int) -> List[List[int]]:
        if not candidates:
            return []
        
        candidates.sort()
        result = set()
        
        def backtrack(remain, comb, start):
            if remain == 0:
                result.add(tuple(sorted(comb)))
                return
            elif remain < 0:
                return
            
            for i in range(start, len(candidates)):
                if i > start and candidates[i] == candidates[i-1]:
                    continue
                backtrack(remain - candidates[i], comb + [candidates[i]], i+1)
        
        backtrack(target, [], 0)
        
        return [list(x) for x in result]