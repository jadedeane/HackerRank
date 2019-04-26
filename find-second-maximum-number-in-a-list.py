"""
Solves https://www.hackerrank.com/challenges/find-second-maximum-number-in-a-list
"""

if __name__ == '__main__':
    n = int(input())
    arr = map(int, input().split())

    x = set(arr)
    x.remove(max(x))
    print(max(x))
