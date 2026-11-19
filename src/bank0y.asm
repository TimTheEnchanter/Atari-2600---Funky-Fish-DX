; Bank 0 additions in the zero-filled gap $F399-$F3D0
; --- M2: 5 bosses on a longer sea floor -------------------------------
; boss world X (ascending); radar scale is 12 world units per pixel
BossHi0:  .byte $00,$00,$01,$02,$02
BossLo0:  .byte $40,$E8,$90,$38,$E0
; camera thresholds for the radar marker (regions of $C0 = 16 radar px)
RadThrHi: .byte $00,$00,$01,$02
RadThrLo: .byte $00,$C0,$80,$40

; game-start init (from $F403): round 0, return the variant in A
	SUBROUTINE
InitRound:
	LDA #BANNER_T            ; M4: "ROUND 1" banner at game start
	STA ROUNDT
	LDA #0
	STA ROUND
	LDA GSTATE
	AND #$03
	RTS


; guard-count digits under a boss (UA's $FEF2). Moved here because its loop
; branch at $FF02 crossed back to $FEF8: the 6502's dummy read on that
; page-crossing branch hits $FFF8, an F6 hotspot (bank 2) -> crash.
	SUBROUTINE
Digit1:
	JSR L0_FF05
	TAY
	LDX #$0A
.d	LDA D0_F249,Y
	AND #$0F
	STA DIGBUF-1,X
	INY
	DEX
	DEX
	BNE .d
	RTS
