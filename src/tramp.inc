; ---- F6 bankswitching (16K): hotspots $1FF6-$1FF9 select banks 0-3 ----
HOT0     = $1FF6
HOT1     = $1FF7
HOT2     = $1FF8
HOT3     = $1FF9
TR_RESET = $FFD0      ; all banks: -> bank 0, JMP Reset
TR_SWAP  = $FFD6      ; bank 0 -> bank 1 logic ($F03C); bank 1 -> bank 0 ($FDBD)
TR_TITLE = $FFDC      ; bank 0 -> bank 3 title kernel
TR_BACK  = $FFDC      ; bank 3 -> bank 0 $FD51
TR_KERN  = $FFE2      ; bank 0 -> bank 2 game kernel (copy of bank 0)
TR_KBACK = $FFE2      ; bank 2 -> bank 0 $FD51
FILLB    SET $00

	MAC TRAMP          ; {1} = bank number; pads to $FFE0 and writes trampolines/vectors
	IF {1} == 0
	ds.b $FFD0 - ., $00
	ELSE
	ds.b $FFD0 - ., $FF
	ENDIF
	sta HOT0           ; FFE0
	jmp L0_F3D1        ; FFE3 (executes in bank 0)
	IF {1} == 0
	sta HOT1           ; FFE6  bank 0 -> 1
	jmp L0_FDBD        ; FFE9  (arrival from bank 1)
	ELSE
	IF {1} == 1
	sta HOT0           ; FFE6  bank 1 -> 0
	jmp L1_F03C        ; FFE9  (arrival from bank 0)
	ELSE
	sta HOT0
	jmp L0_FDBD
	ENDIF
	ENDIF
	IF {1} == 0
	sta HOT3           ; FFDC  bank 0 -> 3 (title)
	jmp L0_FD51        ; FFDF  (arrival from bank 3)
	sta HOT2           ; FFE2  bank 0 -> 2 (kernel)
	jmp L0_FD51        ; FFE5  (arrival from bank 2)
	ENDIF
	IF {1} == 3
	sta HOT0           ; FFDC  bank 3 -> 0
	jmp TitleK         ; FFDF  (arrival from bank 0)
	ENDIF
	IF {1} == 2
	ds.b 6, $FF        ; FFDC
	sta HOT0           ; FFE2  bank 2 -> 0
	jmp K_KernEntry    ; FFE5  (arrival from bank 0)
	ENDIF
	ds.b $FFFC - ., $FF
	.word TR_RESET, TR_RESET
	ENDM
