from collections import Counter
import heapq

class Solution:
    def leastInterval(self, tasks: list[str], n: int) -> int:
        task_count = Counter(tasks)
        max_freq = max(task_count.values())
        freq_count = sum(1 for count in task_count.values() if count == max_freq)

        return max(len(tasks), (max_freq - 1) * (n + 1) + freq_count)