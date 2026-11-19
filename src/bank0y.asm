; Bank 0 additions in the zero-filled gap $F399-$F3D0
; --- M2: 5 bosses on a longer sea floor -------------------------------
; boss world X (ascending); radar scale is 12 world units per pixel
BossHi0:  .byte $00,$00,$01,$02,$02
BossLo0:  .byte $40,$E8,$90,$38,$E0
; camera thresholds for the radar marker (regions of $C0 = 16 radar px)
RadThrHi: .byte $00,$00,$01,$02
RadThrLo: .byte $00,$C0,$80,$40

; game-start init (from $F403): round 0, return the variant in A
InitRound:
	LDA #0
	STA ROUND
	LDA GSTATE
	AND #$03
	RTS

