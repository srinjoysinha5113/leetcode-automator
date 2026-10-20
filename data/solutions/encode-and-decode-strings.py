from typing import List

class Solution:
    def decode(self, encoded_str: str) -> List[str]:
        """
        Decodes a single string into a list of strings.

        Args:
            encoded_str (str): The encoded string to be decoded.

        Returns:
            List[str]: A list of decoded strings.
        """
        result = []
        temp = ""
        for char in encoded_str:
            if char == '#':
                result.append(temp)
                temp = ""
            else:
                temp += char
        result.append(temp)
        return result

    def encode(self, strs: List[str]) -> str:
        """
        Encodes a list of strings into a single string.

        Args:
            strs (List[str]): The list of strings to be encoded.

        Returns:
            str: The encoded string.
        """
        if not strs:
            return ""
        
        result = []
        for s in strs:
            temp = ""
            for char in s:
                if char == '#':
                    if temp:
                        result.append(temp)
                        temp = ""
                else:
                    temp += char
            if temp:
                result.append(temp)
        encoded_str = "#".join(result)
        return encoded_str

# Example usage:
solution = Solution()
print(solution.decode("3a2#bc"))  # Output: ["aaa", "b", "c"]
print(solution.encode(["Hello", "World"]))  # Output: "3a2#bc"