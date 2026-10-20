from typing import List, Dict, Any

class WordDictionary:

    def __init__(self):
        self.root = {}

    def addWord(self, word: str) -> None:
        node = self.root
        for char in word:
            if char not in node:
                node[char] = {}
            node = node[char]
        node['$'] = True  # mark the end of a word

    def search(self, word: str) -> bool:
        return self.match(word, 0, self.root)

    def match(self, word: str, index: int, node: Dict[str, Any]) -> bool:
        if index == len(word):
            return '$' in node
        if word[index] == '.':
            for char in node.keys():
                if self.match(word, index + 1, node[char]):
                    return True
            return False
        return word[index] in node and self.match(word, index + 1, node[word[index]])