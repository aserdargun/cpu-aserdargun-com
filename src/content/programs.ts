export const programs=[
{id:'add',tr:'İlk toplama',en:'First addition',source:`# İki sayı, bir komut / Two numbers, one instruction\naddi x1, x0, 5\naddi x2, x0, 7\nadd x3, x1, x2\nebreak`,expected:'x3 = 12'},
{id:'fibonacci',tr:'Fibonacci ve döngü',en:'Fibonacci and loop',source:`addi x1, x0, 0\naddi x2, x0, 1\naddi x4, x0, 10\nloop:\n  add x3, x1, x2\n  mv x1, x2\n  mv x2, x3\n  addi x4, x4, -1\n  bnez x4, loop\nebreak`,expected:'x2 = 89'},
{id:'sum',tr:'Bellekten dizi toplamı',en:'Array sum from memory',source:`lui x1, 0x10000\naddi x2, x0, 5\naddi x3, x0, 0\nloop:\n  lw x4, 0(x1)\n  add x3, x3, x4\n  addi x1, x1, 4\n  addi x2, x2, -1\n  bnez x2, loop\nebreak\n.data\n.word 3, 7, 11, 13, 17`,expected:'x3 = 51'},
{id:'hazard',tr:'Load-use bağımlılığı',en:'Load-use dependency',source:`lui x1, 0x10000\nlw x2, 0(x1)\nadd x3, x2, x2\nadd x4, x3, x2\nsw x4, 4(x1)\nebreak\n.data\n.word 21, 0`,expected:'x4 = 63'},
{id:'uart',tr:'UART ve GPIO',en:'UART and GPIO',source:`lui x1, 0x20000\nli x2, 72\nsb x2, 0(x1)\nli x2, 105\nsb x2, 0(x1)\nli x2, 10\nsb x2, 0(x1)\nli x2, 5\nsw x2, 4(x1)\nebreak`,expected:'UART = Hi · GPIO = 5'},
{id:'call',tr:'Fonksiyon ve stack',en:'Function and stack',source:`lui sp, 0x10010\naddi sp, sp, -16\nli a0, 7\ncall twice\nebreak\ntwice:\n  sw ra, 0(sp)\n  add a0, a0, a0\n  lw ra, 0(sp)\n  ret`,expected:'a0 = 14'},
{id:'multiply',tr:'Çarpma ve bölme · RV32IM',en:'Multiply and divide · RV32IM',source:`li x1, -21\nli x2, 4\nmul x3, x1, x2\ndiv x4, x1, x2\nrem x5, x1, x2\nebreak`,expected:'x3 = -84 · x4 = -5 · x5 = -1'},
{id:'locality',tr:'Önbellek ve yerellik',en:'Cache and locality',source:`lui x1, 0x10000\nli x2, 20\nli x3, 0\nloop:\n  lw x4, 0(x1)\n  add x3, x3, x4\n  addi x2, x2, -1\n  bnez x2, loop\nebreak\n.data\n.word 7`,expected:'x3 = 140'},
{id:'sort',tr:'Bellekte sıralama',en:'Sorting in memory',source:`lui x1, 0x10000\nli x2, 4\nouter:\n  mv x3, x1\n  mv x4, x2\ninner:\n  lw x5, 0(x3)\n  lw x6, 4(x3)\n  bge x6, x5, next\n  sw x6, 0(x3)\n  sw x5, 4(x3)\nnext:\n  addi x3, x3, 4\n  addi x4, x4, -1\n  bnez x4, inner\n  addi x2, x2, -1\n  bnez x2, outer\nebreak\n.data\n.word 9, 2, 7, 1, 5`,expected:'RAM = 1, 2, 5, 7, 9'}
];
