/* Build with --isa rv32im; inspect the result symbol in the generated debug JSON. */
volatile int limit = 7;
volatile int result;
int main(void) {
    int value = 1;
    for (int i = 1; i <= limit; ++i) value *= i;
    result = value; /* 7! = 5040 */
    return 0;
}
