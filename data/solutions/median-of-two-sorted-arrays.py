from typing import List

class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = []
        i, j = 0, 0
        
        while i < len(nums1) and j < len(nums2):
            if nums1[i] < nums2[j]:
                merged.append(nums1[i])
                i += 1
            else:
                merged.append(nums2[j])
                j += 1
                
        merged.extend(nums1[i:])
        merged.extend(nums2[j:])
        
        n = len(merged)
        mid = n // 2
        
        if n % 2 == 0:
            return (merged[mid - 1] + merged[mid]) / 2
        else:
            return float(merged[mid])