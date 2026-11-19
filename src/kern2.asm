; ======================================================================
; M3: boss monster band (bank 2 kernel copy only).
; The top BOSS_S lines of the sea are drawn here: P0 = fish (as UA's loop),
; P1 = the boss monster (double width), ball = UA's boss block, now
; now the bubble (M3b); the boss touch is checked in software (bank 1).
; Then P1 moves to the first guard band and UA's loop takes over.
BOSS_S  = 19          ; lines in the boss band (UA's ball rows are 10-18)
BPTR    = $E1         ; boss graphics pointer (kernel-time temp)
BLINE   = $E3
BOSSFR  = $E0         ; monster frame (low byte), chosen at kernel entry
BALLHM   = $F8         ; bubble HM|coarse for the ball (kernel)
BUBROW  = $F9         ; ball row counter start (bubble), $80 = none
BUBCOL  = $0E
BUB_DX  = 2
BUB_DY  = 4
WATER   = $C3

; monster graphics, BOSS_S bytes each, drawn from line 0 (rows 4-19)
BossNone:
	.byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00   ; 20 bytes, bottom row first
BossGfxA:
	.byte $00,$42,$99,$5A,$A5,$A5,$7E,$66,$DB,$FF,$99,$99,$FF,$7E,$3C,$00,$00,$00,$00,$00   ; 20 bytes, bottom row first
BossGfxB:
	.byte $00,$A5,$5A,$A5,$5A,$5A,$7E,$66,$DB,$FF,$99,$99,$FF,$7E,$3C,$00,$00,$00,$00,$00   ; 20 bytes, bottom row first
BossGfxC:                    ; dazed (glowing): X eyes, open mouth
	.byte $00,$42,$99,$5A,$A5,$A5,$7E,$42,$FF,$BD,$DB,$BD,$FF,$7E,$3C,$00,$00,$00,$00,$00   ; 20 bytes, bottom row first

; bank 2 entry (from TR_KERN): pick the monster frame while vblank runs
	SUBROUTINE
KernEntry:
	PHA                      ; A = UA's score-band background colour (used at $F964)
	LDY #<BossNone           ; pick the monster frame (before the kernel)
	LDX BOSSIDX
	BMI .kf
	LDY #<BossGfxC
	LDA BGLOW,X
	BNE .kf
	LDY #<BossGfxA
	LDA FRAME
	AND #$08
	BEQ .kf
	LDY #<BossGfxB
.kf	STY BOSSFR
	LDA BOSSHM               ; no bubble: park the ball at a valid position
	STA BALLHM               ; (coarse 0 would make $F388 loop 256 times)
	LDA #$80                 ; bubble -> ball position and first row
	BIT BUBST
	BPL .nb
	LDA $84                  ; (UA showed it on 2 frames in 3 too)
	SEC
	LDA BUBXLO
	SBC CAMXLO
	CLC
	ADC #BUB_DX
	JSR L0_FE8F
	STA BALLHM
	LDA BUBY
	SEC
	SBC #$72+BUB_DY
.nb	STA BUBROW
	PLA
	JMP L0_F95B

; P1 at the boss X minus 4 px (centres the 16 px monster on the 8 px block)
	SUBROUTINE
BossPos:
	LDA $93
	AND #$0F
	TAY                      ; coarse
	LDA $93
	CLC
	ADC #$40                 ; fine +4 = 4 px further left
	BVC .ok                  ; still within -8..+7
	CPY #$01
	BCC .edge                ; coarse 0: leave it
	DEY                      ; one coarse step (15 px) right ...
	SEC
	SBC #$F0                 ; ... and 11 px back left (fine +4-15 = -11 -> wraps)
	AND #$F0
	STA BLINE
	TYA
	ORA BLINE
	JMP .go
.edge	LDA $93
.ok	AND #$F0
	STA BLINE
	TYA
	ORA BLINE
.go	LDX #$01
	JMP L0_F388            ; positions P1 (2 lines), RTS to the caller

; replaces UA's $FBF0-$FBFF (band colour, PF colour, HMCLR, CXCLR) + boss band
	SUBROUTINE
BossK:
	LDA BOSSFR
	STA BPTR
	LDA #>BossGfxA
	STA BPTR+1
	LDA #BUBCOL
	STA COLUPF               ; the ball is the bubble now
	LDA $B6
	STA COLUP1
	LDA #$05
	STA NUSIZ1               ; double width
	STA HMCLR
	STA CXCLR
	LDA #BOSS_S-1
	STA BLINE                ; graphics are stored bottom row first
	LDX #$01
	LDY #$FF                 ; no fish on the first line
; 1 line per pass (~66 cycles)
.l	STA WSYNC
	STX ENABL
	CPY #$0B
	BCS .nf
	STA GRP0
.nf	LDY BLINE
	LDA (BPTR),Y
	STA GRP1
	INC $E7
	INC $E5
	LDX #$01                 ; ball on for the bubble rows (E7 0..3)
	LDY $E7
	BMI .b0
	CPY #$04
	BCS .b0
	INX
.b0	LDY $E5
	LDA ($9D),Y
	DEC $E8
	DEC BLINE
	BPL .l
; --- line A: tidy up, sample the boss touch, set up the P1 move ---
	STA WSYNC
	STX ENABL
	CPY #$0B
	BCS .nf2
	STA GRP0
.nf2	LDA #0
	STA GRP1
	STA NUSIZ1
	STA CXCLR
	LDA $C7
	STA COLUP1
	LDA $C2
	TAY
	AND #$0F
	TAX
; --- line B: RESP1 at the same cycle as UA's $FC85 (loop entered at cycle 7) ---
	STA WSYNC
	LDA BLINE                ; 3
	NOP                      ; 5 (measured against UA: guards at the same pixel)
.d	DEX
	BNE .d
	STA RESP1,X
	STY HMP1,X
; --- line C: HMOVE, then counters for the BOSS_S+3 lines used ---
	STA WSYNC
	STA HMOVE
	LDA $E6
	CLC
	ADC #BOSS_S+3
	STA $E6
	LDA $E7
	ADC #$03
	STA $E7
	LDA $E5
	ADC #$03
	STA $E5
	LDA $E8
	SEC
	SBC #$03
	STA $E8
	LDY $E6                  ; band 1 wholly inside the boss band?
	BMI .go
	CPY $BC
	BCC .go
	LDA $BC                  ; then UA's loop switches to the next band at once
	STA $E6
.go	LDX #$01
	LDY $E5
	LDA #0                   ; fish sprite: UA's loop only clears GRP0 by
	CPY #$0B                 ; drawing the fish's blank last row; if that
	BCS .gz                  ; row fell on lines A-C it was skipped and the
	LDA ($9D),Y              ; last fish row stayed on down the screen
.gz	STA GRP0
	LDA ($9D),Y
	JMP L0_FC02

