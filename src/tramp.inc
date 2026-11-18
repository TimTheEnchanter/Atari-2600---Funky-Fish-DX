; ---- F6 bankswitching (16K): hotspots $1FF6-$1FF9 select banks 0-3 ----
HOT0     = $1FF6
HOT1     = $1FF7
HOT2     = $1FF8
HOT3     = $1FF9
TR_RESET = $FFE0      ; all banks: -> bank 0, JMP Reset
TR_SWAP  = $FFE6      ; bank 0 -> bank 1 logic ($F03C); bank 1 -> bank 0 ($FDBD)
FILLB    SET $00

	MAC TRAMP          ; {1} = bank number; pads to $FFE0 and writes trampolines/vectors
	IF {1} == 0
	ds.b $FFE0 - ., $00
	ELSE
	ds.b $FFE0 - ., $FF
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
	ds.b $FFFC - ., $FF
	.word TR_RESET, TR_RESET
	ENDM
