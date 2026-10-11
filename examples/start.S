.section .text.start
.global _start
_start:
  lui sp, 0x10010
  addi sp, sp, -16
  jal ra, main
  ebreak
1: j 1b
