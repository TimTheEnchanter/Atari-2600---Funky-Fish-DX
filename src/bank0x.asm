; ======================================================================
; Bank 0 additions (replaces the leftover assembler text at $FF3A-$FFD7)
; Everything here is reached by same-size JMP/JSR patches so that the
; display kernel keeps its original addresses (page-crossing timing).

; --- Radar boss blips (replaces $FA7D-$FAEB; same line count) -----------
; Even frames: P1 at boss 0 (bit7) / boss 1 (bit0). Odd: bosses 2 / 3.
; M1 shows boss 4 on odd frames, so every blip flickers at 30 Hz as before.
	SUBROUTINE
RadarBlips:
	LDA FRAME
	LSR
	BCS .rb
	LDA #RADA_HM
	LDX #$01
	LDY #RADA_CO
	JSR L0_F388              ; 2 lines
	LDA #$00
	STA GRP0
	LDX GLEFT
	BNE .r1
	LDX BGLOW
	BEQ .r2
.r1	ORA #$80
.r2	LDX GLEFT+1
	BNE .r3
	LDX BGLOW+1
	BEQ .rm
.r3	ORA #$01
	JMP .rm
.rb	LDA #RADB_HM
	LDX #$01
	LDY #RADB_CO
	JSR L0_F388              ; 2 lines
	LDA #$00
	STA GRP0
	LDX GLEFT+2
	BNE .r4
	LDX BGLOW+2
	BEQ .r5
.r4	ORA #$80
.r5	LDX GLEFT+3
	BNE .r6
	LDX BGLOW+3
	BEQ .rm
.r6	ORA #$01
.rm	STA TMP1
	LDA #RADM_HM
	LDX #$03
	LDY #RADM_CO
	JSR L0_F388              ; 2 lines (paid for by 2 lines removed below)
	LDA FRAME
	LSR
	LDA GLEFT+4
	ORA BGLOW+4
	BCC .rn                  ; even frame: no M1
	BEQ .rn
	LDY #$02
.rn	LDA TMP1
	STA WSYNC                ; (orig $FAC5)
	STA GRP1
	STY ENAM1
	LDY #$00
	LDX #$0A
.rcl	STY DIGBUF-1,X
	DEX
	BNE .rcl
	STA WSYNC
	STA WSYNC
	STY GRP1
	STY ENAM1
	LDA #$81                 ; (2 lines of the box removed here)
	STA GRP0
	STA WSYNC
	STA WSYNC
	LDA #$FF
	STA GRP0
	STA WSYNC
	STY PF2
	STY GRP0
	JMP L0_FAEC

