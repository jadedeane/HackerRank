"""
Produce Fibonacci sequence for a given number of terms using loop, and recursion.
"""


def fibonacci_recursion(t):
    """Recursively calculate fibonacci term."""
    if t <= 1:  # Return term as-is if first ot second term
        return t
    else:
        return fibonacci_recursion(t - 1) + fibonacci_recursion(t - 2)


def main():

    # Get maximum terms
    n = int(input("Enter a positive integer: "))

    # Produce sequence using loop
    s = []
    x, y = 0, 1
    for i in range(n+1):
        s.append(x)
        x, y = y, x + y
    print("Fibonacci sequence (loop): {}".format(s))

    # Produce sequence using recursive function
    s = []
    for i in range(n+1):
        s.append(fibonacci_recursion(i))
    print("Fibonacci sequence (recursion): {}".format(s))


if __name__ == '__main__':
    main()
