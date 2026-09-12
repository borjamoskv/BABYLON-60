
bits 64

; --- CABECERA MULTIBOOT2 ---
section .multiboot_header
align 8
header_start:
    dd 0xE85250D6                ; magic number
    dd 0                         ; architecture 0 (i386)
    dd header_end - header_start ; header length
    dd 0x100000000 - (0xE85250D6 + 0 + (header_end - header_start)) ; checksum
    dw 0
    dw 0
    dd 8
header_end:

; --- MEMORIA FÍSICA (BSS) ---
section .bss
align 16
stack_bottom:
    resb 16384 ; Pila del Kernel de 16 KB
stack_top:

heap_ptr:
    resq 1 ; Puntero físico al tope del montículo

; --- CÓDIGO BARE-METAL ---
section .text
global _start

; SOBERANÍA: Implementación nativa de sys_alloc (Bump Allocator)
sys_alloc:
    mov rax, qword [rel heap_ptr]
    mov rcx, rax
    add rcx, rdi
    mov qword [rel heap_ptr], rcx
    ret

; SOBERANÍA: Implementación nativa de sys_free (No-op)
sys_free:
    ret

_start:
    mov rsp, stack_top
    ; Setup del heap a partir del megabyte 2 (fuera del kernel base)
    mov rax, 0x200000
    mov qword [rel heap_ptr], rax
    
    call kernel_main
    
.hang:
    cli
    hlt
    jmp .hang

kernel_main:
    push rbp
    mov rbp, rsp
    sub rsp, 32

    ; Payload termodinámico: C5-REAL IR -> ASM
    mov rdi, 16
    call sys_alloc
    mov qword [rbp - 8], rax  ; Reg(0) = Pointer

    ; Mutación
    mov rax, qword [rbp - 8]
    lea rcx, [rax + 0]
    mov qword [rcx], 42

    ; Apoptosis
    mov rdi, qword [rbp - 8]
    call sys_free

    mov rsp, rbp
    pop rbp
    ret
