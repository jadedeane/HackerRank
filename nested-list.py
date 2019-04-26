"""
Solves https://www.hackerrank.com/challenges/nested-list
"""

if __name__ == '__main__':
    x = []
    for _ in range(int(input())):
        name = input()
        score = float(input())
        x.append([name, score])

    second_place = sorted(list(set([grade for name, grade in x])))[1]
    print('\n'.join([a for a, b in sorted(x) if b == second_place]))
