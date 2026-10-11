/* Bare-metal RV32I. ELF loader initializes data and zeroes bss. */
volatile unsigned values[5] = {3,7,11,13,17};
volatile unsigned result;
void main(void) {
    unsigned total = 0;
    for (unsigned i=0;i<5;i++) total += values[i];
    result = total;
    *(volatile unsigned*)0x20000004 = total & 255;
    *(volatile unsigned char*)0x20000000 = 'O';
    *(volatile unsigned char*)0x20000000 = 'K';
}
