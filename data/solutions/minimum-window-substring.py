from collections import defaultdict

class Solution:
    def minWindow(self, s: str, t: str) -> str:
        if not t or not s:
            return ""

        dict_t = defaultdict(int)
        for char in t:
            dict_t[char] += 1

        required_chars = len(dict_t)
        formed_chars = 0
        window_counts = defaultdict(int)
        ans = float("inf")
        ans_string = ""
        left = 0

        for right in range(len(s)):
            character = s[right]
            window_counts[character] += 1

            if character in dict_t and window_counts[character] == dict_t[character]:
                formed_chars += 1

            while left <= right and formed_chars == required_chars:
                character = s[left]

                if right - left + 1 < ans:
                    ans = right - left + 1
                    ans_string = s[left:right+1]

                window_counts[character] -= 1
                if character in dict_t and window_counts[character] < dict_t[character]:
                    formed_chars -= 1

                left += 1

        return ans_string