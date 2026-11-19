; ======================================================================
; Bank 1 additions (free space after UA's game logic)

; --- M2 tables ---------------------------------------------------------
BossHi1:  .byte $00,$00,$01,$02,$02
BossLo1:  .byte $40,$E8,$90,$38,$E0
; seaweed clumps, scanned from the last entry down (ascending world X)
PlantHi:  .byte $02,$01,$01,$00
PlantLo:  .byte $BC,$F4,$2C,$64
; guards per boss by game variant (UA: 8/12/16/20; 20 overflowed the 2-digit display)
GuardBase: .byte 8,12,16,19
; fruit sink speed: frame mask (sinks on odd frames when FRAME & mask == 0)
SinkMask: .byte $06,$02,$02,$00

; --- Round check: all bosses dead and glow timers out -> next round -----
	SUBROUTINE
RoundChk:
	LDX #4
	LDA #0
.l	ORA GLEFT,X
	ORA BGLOW,X
	DEX
	BPL .l
	TAX
	BNE .x
	INC ROUND
	JSR RoundInit
.x	JMP TR_SWAP

	SUBROUTINE
RoundInit:
	LDA GSTATE
	AND #$03
	TAX
	LDA ROUND
	ASL
	CLC
	ADC GuardBase,X
	CMP #20
	BCC .g
	LDA #19
.g	LDX #4
.i	STA GLEFT,X
	DEX
	BPL .i
	LDA GSTATE
	AND #$FB                 ; guards no longer out
	STA GSTATE
	LDX #4
.p	LDA #$80                 ; park all guard slots (as at boss approach)
	STA GST-1,X
	LDA #0
	STA GY-1,X
	STA GTMR-1,X
	LDA PARKX
	STA GX-1,X
	DEX
	BNE .p
	STX BUBST
	LDA #BANNER_T            ; M4: "ROUND n" banner
	STA ROUNDT
	LDA #$FF                 ; refill power
	STA POWER
	LDA PLAYER               ; round-clear jingle: reuse the eat sound
	ORA #$20
	STA PLAYER
	LDA #$80
	STA EATTMR
	LDA #$50                 ; 500 point bonus
	JMP L1_F4E7

; difficulty helpers ----------------------------------------------------
; C set if guards should dart at the player (round 2+, or variants 3/4)
	SUBROUTINE
DartOn:
	LDA ROUND
	BNE .y
	LDA GSTATE
	AND #$02
	BNE .y
	CLC
	RTS
.y	SEC
	RTS

; --- Bubble hit test (from $F591): Z set for a target hit (swimmer or seahorse)
	SUBROUTINE
HitTest:
	LDA GST-1,X
	AND #$FD
	CMP #$01
	RTS

; bubble hit (from $F5C9)
	SUBROUTINE
HitDo:
	LDA GST-1,X
	CMP #$03
	BEQ .sea
	LDA GSTATE               ; UA: guard -> fruit
	AND #$03
	TAY
	LDA D1_F030,Y
	STA GTMR-1,X
	INC GST-1,X
	LDA #$00
	STA BUBST
	LDA #$01
	JMP L1_F4E7
.sea	LDA #$80                 ; seahorse popped: slot parked, 300 points
	STA GST-1,X
	LDA #$00
	STA GY-1,X
	STA GTMR-1,X
	STA BUBST
	LDA PARKX
	STA GX-1,X
	LDA #$30
	JMP L1_F4E7

; --- Guard / fruit / seahorse movement (replaces UA's $F3AF) -------------
; Slots X=0-3 (GST,X etc.). Screen X of the player = PLXLO-CAMXLO.
; State 1 swimmer: UA random walk; from round 2 it darts at a nearby player.
; State 2 fruit: no longer reverts to a guard; it sinks, and on reaching
;   the sea bed it wakes a seahorse (arcade rule).
; State 3 seahorse (also UA's roamers): homes on the player, leaves when its
;   timer runs out.
SEAHORSE_T = $50
GYMAX   = $5C         ; highest guard Y (band start line $72-$5C = 22 = BOSS_S+3)
	SUBROUTINE
GuardAI:
	LDA FRAME
	ADC CYC3
	ADC CAMXLO
	STA TMP1
	SEC
	LDA PLXLO
	SBC CAMXLO
	STA TMP3                 ; player screen X
	LDA FRAME
	LSR
	BCC .even
	JMP .odd
; even frames: timers and X movement
.even	LDX #$03
.el	LDA GST,X
	BMI .enext
	BEQ .enext
	JSR Expire
	BCS .enext               ; slot was removed
	LDA GST,X
	CMP #$02
	BEQ .enext               ; fruit: straight down
	CMP #$03
	BEQ .eseah
	JSR DartOn
	BCC .ewalk
	LDA GX,X
	SEC
	SBC TMP3
	BCS .ep
	EOR #$FF
	ADC #$01
.ep	CMP #$18
	BCS .ewalk
	LDA GX,X                 ; dart: 2 px toward the player
	CMP TMP3
	LDA #$FE
	BCS .eadd
	LDA #$02
	BNE .eadd
.eseah	LDA FRAME                ; seahorse: 1 px every 4th frame
	AND #$02
	BEQ .enext
	LDA GX,X
	CMP TMP3
	LDA #$FF
	BCS .eadd
	LDA #$01
	BNE .eadd
.ewalk	LDA TMP1                 ; UA random walk
	AND #$07
	TAY
	TXA
	LSR
	LSR
	BCS .ew2
	LDA D1_F000,Y
	JMP .eadd
.ew2	LDA D1_F008,Y
.eadd	CLC
	ADC GX,X
	CMP #$08
	BCC .ekill
	CMP #$94
	BCS .ekill
	STA GX,X
.enext	INC TMP1
	DEX
	BPL .el
	JMP L1_F45B              ; UA: keep each slot pair sorted by Y
.ekill	JSR KillSlot
	JMP .enext

; odd frames: timers and Y movement
.odd	LDX #$03
	BNE .ol
.oskp	JMP .onext
.ol	LDA GST,X
	BMI .oskp
	BEQ .oskp
	JSR Expire
	BCS .oskp
	LDA GST,X
	CMP #$02
	BEQ .ofruit
	CMP #$03
	BEQ .oseah
	JSR DartOn
	BCC .owalk
	LDA GX,X
	SEC
	SBC TMP3
	BCS .op
	EOR #$FF
	ADC #$01
.op	CMP #$18
	BCS .owalk
	LDA GY,X                 ; dart vertically, 2 px
	CMP PLY
	LDA #$FE
	BCS .oadd
	LDA #$02
	BNE .oadd
.oseah	LDA GY,X
	CMP PLY
	LDA #$FF
	BCS .oadd
	LDA #$01
	BNE .oadd
.ofruit	LDA ROUND
	CMP #3
	BCC .of1
	LDA #3
.of1	TAY
	LDA FRAME
	AND SinkMask,Y
	BNE .onext
	LDA GY,X
	SEC
	SBC #$01
	CMP #$0C
	BCS .ofst
	LDA #$03                 ; hit the sea bed: a seahorse wakes
	STA GST,X
	LDA #SEAHORSE_T
	STA GTMR,X
	LDA #$0C
.ofst	STA GY,X
	JMP .onext
.owalk	LDA TMP1                 ; UA vertical walk
	AND #$07
	TAY
	LDA GSTATE
	LSR
	LSR
	LSR
	LDA D1_F010,Y
	BCS .oadd
	LDA D1_F018,Y
.oadd	CLC
	ADC GY,X
	CMP #GYMAX+1             ; M3: guards stay below the boss band (P1 draws the boss there)
	BCS .onext
	CMP #$7A
	BCS .okill
	CMP #$0B
	BCC .okill
	STA GY,X
	TXA                      ; UA: keep 24 lines from the partner slot
	EOR #$01
	TAY
.osep	LDA.w GY,Y
	BEQ .onext
	CMP GY,X
	BCC .os1
	SBC #$18
	CMP GY,X
	BCS .onext
	DEC GY,X
	JMP .osep
.os1	ADC #$18
	CMP GY,X
	BCC .onext
	INC GY,X
	JMP .osep
.onext	INC TMP1
	DEX
	BMI .odone
	JMP .ol
.odone	JMP L1_F45B
.okill	JSR KillSlot
	JMP .onext

; timer ran out? swimmer: nothing; fruit: nothing (it sinks instead);
; seahorse/roamer: swims away (slot emptied). C set if the slot was removed.
	SUBROUTINE
Expire:
	LDA GTMR,X
	BNE .no
	LDA GST,X
	CMP #$03
	BNE .no
KillSlot:
	LDA #$00
	STA GST,X
	STA GY,X
	STA GTMR,X
	LDA PARKX
	STA GX,X
	SEC
	RTS
.no	CLC
	RTS

; --- M3: boss touch by position (the ball now draws the bubble) ----------
; V set if the fish overlaps the monster horizontally: fish X - boss X in
; -10..+8 (UA's ball collision measured -6..+4, widened for the 16 px
; monster). UA's code then checks PLY $66-$75 as before.
	SUBROUTINE
BossTouch:
	LDX BOSSIDX
	BMI .no
	SEC
	LDA PLXLO
	SBC BossLo1,X
	TAY
	LDA PLXHI
	SBC BossHi1,X
	BEQ .pos
	CMP #$FF
	BNE .no
	CPY #$F6                 ; -10..-1
	BCS .yes
.no	CLV
	RTS
.pos	CPY #$09                 ; 0..+8
	BCS .no
.yes	BIT .v40
	RTS
.v40	.byte $40

; M4: while the round banner is up the game logic is paused
	SUBROUTINE
PreLogic:
	LDA ROUNDT
	BEQ .go
	DEC ROUNDT
	PLA
	PLA
	JMP TR_SWAP
.go	JMP L1_F05D
