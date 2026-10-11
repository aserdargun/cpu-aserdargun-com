ENTRY(_start)
MEMORY { ROM (rx) : ORIGIN = 0, LENGTH = 64K
         RAM (rw) : ORIGIN = 0x10000000, LENGTH = 64K }
SECTIONS {
 .text : { KEEP(*(.text.start)) *(.text*) } > ROM
 .rodata : { *(.rodata*) } > ROM
 .data : { *(.data*) *(.sdata*) } > RAM
 .bss : { *(.bss*) *(.sbss*) *(COMMON) } > RAM
 /DISCARD/ : { *(.comment) *(.eh_frame) }
}
