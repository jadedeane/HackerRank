/* Produce Fibonacci sequence for a given number of terms using loop, and recursion. */

#include <stdio.h>

int fibonacci_recursion(int t) {
    if (t <= 1) {
        return t;
    } else {
        return fibonacci_recursion(t-1) + fibonacci_recursion(t-2);
    }
}

int main(void) {

    /* Vars */
    int n; /* Maximum number of terms. */
    int x, y, z; /* Term loop values. */

    /* Get maximum number */
    printf("Enter a positive integer: ");
    scanf("%d", & n);

    /* Produce sequence using loop */
    printf("Fibonacci sequence (loop): ");
    x = 0;
    y = 1;
    for ( int i=0; i < n+1; i = i+1 ) {
        printf("%d, ", x);
        z = x + y;
        x = y;
        y = z;
    }
    printf("\n");

    /* Produce sequence using recursion */
    printf("Fibonacci sequence (recursion): ");
    for ( int i=0; i < n+1; i = i+1 ) {
        printf("%d, ", fibonacci_recursion(i));
    }
    printf("\n");
}
