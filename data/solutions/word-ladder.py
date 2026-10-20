from typing import List

class Solution:
    def ladderLength(self, beginWord: str, endWord: str, wordList: List[str]) -> int:
        # Create a set for efficient lookups of words in the dictionary
        word_set = set(wordList)
        
        # Initialize a queue with the starting word and its distance (1)
        queue = [(beginWord, 1)]
        
        while queue:
            word, dist = queue.pop(0)
            
            # If the current word is the end word, return its distance
            if word == endWord:
                return dist
            
            # Generate all possible transformations of the current word
            for i in range(len(word)):
                for c in 'abcdefghijklmnopqrstuvwxyz':
                    next_word = word[:i] + c + word[i+1:]
                    
                    # If the transformation is a valid word and not visited before, add it to the queue
                    if next_word in word_set and (next_word not in [w for w, d in queue]):
                        queue.append((next_word, dist + 1))
                        
                        # Remove the transformed word from the set to avoid revisiting it
                        word_set.remove(next_word)
        
        # If no transformation sequence is found, return 0
        return 0