; Bank 0 additions in UA's old title body $F558-$F718 (dead since F555 jumps to the bank 3 title)
; overrun-safe end of the game vblank (from $F95B): X=0 as UA's loop left it
	SUBROUTINE
VbWait:
	BIT TIMINT
	BPL VbWait
	LDX #$00
	STX WSYNC
	STX VBLANK
	JMP L0_F964

; guard animation frames per boss (UA's $F2B7 had 4 bosses; boss 5 read past it)
GuardFr: .byte $48,$5E,$74,$8A,$A0,$B6,$CC,$E2,$48,$5E

; M4: frame type. A pending round banner uses the bank 3 title kernel.
	SUBROUTINE
SelK:
	LDA ROUNDT
	BNE .t
	LDA GSTATE
	AND #$A0
	BEQ .t
	JMP L0_F719
.t	JMP L0_F555

; M4: the dying fish flashes through the colours (UA: plain grey $09)
	SUBROUTINE
DeathCol:
	LDA FRAME
	ASL
	ASL
	ASL
	ORA #$0A
	STA $B5
	RTS
