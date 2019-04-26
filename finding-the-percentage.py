"""
Solves https://www.hackerrank.com/challenges/finding-the-percentage
"""

if __name__ == '__main__':
    n = int(input())
    student_grades = {}
    for _ in range(n):
        name, *line = input().split()
        scores = list(map(float, line))
        student_grades[name] = scores
    query_name = input()

    grades = student_grades[query_name]  # Find list of grades for student
    print("{0:.2f}".format(sum(grades) / len(grades)))  # Find the mean
