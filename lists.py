"""
Solves https://www.hackerrank.com/challenges/python-lists
"""

if __name__ == '__main__':
    n = int(input())

    l = []
    for _ in range(n):
        s = input().split()
        c = s[0]
        args = s[1:]
        if c != "print":
            c += "(" + ",".join(args) + ")"
            eval("l." + c)
        else:
            print(l)
