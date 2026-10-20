from typing import List

class Solution:
    def findOrder(self, numCourses: int, prerequisites: List[List[int]]) -> List[int]:
        graph = [[] for _ in range(numCourses)]
        indegree = [0] * numCourses
        
        # Build the graph and calculate indegrees
        for course, prereq in prerequisites:
            graph[prereq].append(course)
            indegree[course] += 1
        
        queue = [i for i in range(numCourses) if indegree[i] == 0]
        
        result = []
        
        # Perform topological sorting
        while queue:
            course = queue.pop(0)
            result.append(course)
            
            for neighbor in graph[course]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)
        
        # If there are remaining courses with non-zero indegrees, it's impossible to finish all courses
        return result if len(result) == numCourses else []