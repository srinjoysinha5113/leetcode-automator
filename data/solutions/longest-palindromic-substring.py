class Solution:
    def longestPalindrome(self, s: str) -> str:
        def expand_around_center(left: int, right: int) -> str:
            while left >= 0 and right < len(s) and s[left] == s[right]:
                left -= 1
                right += 1
            return s[left + 1:right]

        longest_palindrome = ""
        for i in range(len(s)):
            palindrome_odd = expand_around_center(i, i)
            palindrome_even = expand_around_center(i, i + 1)
            if len(palindrome_odd) > len(longest_palindrome):
                longest_palindrome = palindrome_odd
            if len(palindrome_even) > len(longest_palindrome):
                longest_palindrome = palindrome_even

        return longest_palindrome