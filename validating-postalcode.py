"""
Solves https://www.hackerrank.com/challenges/validating-postalcode
"""

import re

regex_integer_in_range = r"^[1-9][0-9][0-9][0-9][0-9][0-9]$"  # Do not delete 'r'.
regex_alternating_repetitive_digit_pair = r"(\d)(?=(\d)\1)"  # Do not delete 'r'.

p = input()

print(bool(re.match(regex_integer_in_range, p)) and len(re.findall(regex_alternating_repetitive_digit_pair, p)) < 2)
