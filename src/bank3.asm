; ======================================================================
; Bank 3 - title screen
; Title screen: replaces UA's two-page title, which showed half of each
; text row on alternate frames (heavy flicker). Uses the standard
; 48-pixel routine (P0/P1 three copies close, VDEL), so nothing flickers.
	SEG BANK3
	ORG $3000
	RORG $F000

TPTR    = $E7         ; 6 pointers $E7-$F2 (title only; game reuses as temps/digits)
TCNT    = $E5
TTMP    = $E6
T_VIS   = 249         ; TIM64T for the visible area (~210 lines; overscan cut to match)

	MAC ALIGNCOL      ; {1} = block size: keep a block inside one page
	IF (<.) + {1} > 256
	ALIGN 256
	ENDIF
	ENDM

	MAC TEXT          ; {1} block label, {2} colour
	LDA #>{1}
	STA TMP1
	LDA #{2}
	LDX #<{1}
	LDY #{1}_H
	JSR SetText
	ENDM

TitleK:
.vb	LDA INTIM                ; end of vblank (timer from bank 0 $F547)
	BNE .vb
	STA WSYNC
	STA VBLANK
	STA COLUBK
	LDA #T_VIS
	STA TIM64T
	; position P0 at pixel 55 and P1 at 63, three copies close, VDEL on
	STA WSYNC
	LDX #6
.p	DEX
	BNE .p
	NOP
	NOP
	STA RESP0                ; P0 ~ pixel 54, P1 9 px right of it;
	STA RESP1                ; T_HM0/T_HM1 trim them to 55/63
	LDA #T_HM0
	STA HMP0
	LDA #T_HM1
	STA HMP1
	STA WSYNC
	STA HMOVE
	LDA #$03
	STA NUSIZ0
	STA NUSIZ1
	LDA #$01
	STA VDELP0
	STA VDELP1
	LDA GSTATE               ; not in a game: no banner pending
	BMI .ing
	LDA #0
	STA ROUNDT
.ing	LDA ROUNDT
	BEQ .title
	JMP Banner
.title	LDX #6
	JSR Blank
	LDA FRAME                ; logo hue cycles slowly
	LSR
	LSR
	LSR
	AND #$F0
	ORA #$0A
	LDX #>TxFunky
	STX TMP1
	LDX #<TxFunky
	LDY #TxFunky_H
	JSR SetText
	LDX #2
	JSR Blank
	LDA FRAME
	LSR
	LSR
	LSR
	AND #$F0
	EOR #$80
	ORA #$0C
	LDX #>TxFish
	STX TMP1
	LDX #<TxFish
	LDY #TxFish_H
	JSR SetText
	LDX #6
	JSR Blank
	LDA GSTATE               ; GAME n (Select)
	AND #$03
	TAX
	LDA GameTxHi,X
	STA TMP1
	LDA GameTx,X
	TAX
	LDA #$0E
	LDY #TxGame1_H
	JSR SetText
	LDX #6
	JSR Blank
	TEXT TxHi, $36
	LDX #2
	JSR Blank
	; hi score: 4 BCD digits + a fixed 0, leading zeros blanked
	LDX #10                  ; blank cell
	STX TPTR+0               ; (code list in TPTR even bytes, converted below)
	LDA HISCHI
	LSR
	LSR
	LSR
	LSR
	STA TPTR+2
	LDA HISCHI
	AND #$0F
	STA TPTR+4
	LDA HISCLO
	LSR
	LSR
	LSR
	LSR
	STA TPTR+6
	LDA HISCLO
	AND #$0F
	STA TPTR+8
	LDA #0
	STA TPTR+10
	LDX #2                   ; blank leading zeros (keep the last two digits)
.lz	LDA TPTR,X
	BNE .lzd
	LDA #10
	STA TPTR,X
	INX
	INX
	CPX #8
	BNE .lz
.lzd	LDA #$36
	JSR DigRow
	LDX #6
	JSR Blank
	TEXT TxUa, $86
	LDX #2
	JSR Blank
	TEXT TxYear, $86
TitleEnd:
	LDA INTIM
	BNE TitleEnd
	STA WSYNC
	LDA #OSCAN_TITLE
	STA TIM64T
	LDA #0
	STA GRP0
	STA GRP1
	STA GRP0
	STA VDELP0
	STA VDELP1
	JMP TR_BACK              ; -> bank 0 $FD51 (switches / overscan logic)

; "ROUND n" banner between rounds (ROUNDT counts down in bank 1; game paused)
	SUBROUTINE
Banner:
	LDA ROUNDT               ; rising arpeggio while the banner is up
	CMP #24
	BCC .q
	LSR
	LSR
	LSR
	AND #$07
	TAX
	LDA JingleF,X
	STA AUDF0
	LDA #$0C
	STA AUDC0
	LDA #$08
	BNE .v
.q	LDA #0
.v	STA AUDV0
	LDA #0
	STA AUDV1
	LDX #50
	JSR Blank
	TEXT TxRound, $1C
	LDX #10
	JSR Blank
	; round number ROUND+1 as two big digits, centred
	LDA ROUND
	CLC
	ADC #1
	LDX #0
.tens	CMP #10
	BCC .u
	SBC #10
	INX
	BNE .tens
.u	STA TPTR+6
	TXA
	BNE .t
	LDX #10                  ; no leading zero
.t	STX TPTR+4
	LDA #10
	STA TPTR+0
	STA TPTR+2
	STA TPTR+8
	STA TPTR+10
	LDA #$1C
	JSR DigRowBig
	JMP TitleEnd

JingleF: .byte 24,24,19,19,16,16,12,12   ; high .. low (counts down)

; A = colour; TPTR+0,2,..,10 hold digit codes (0-9, 10 = blank)
	SUBROUTINE
DigRow:
	STA COLUP0
	STA COLUP1
	LDA #<DigFont
	LDX #>DigFont
	LDY #DigFont_H
	BNE DigGo
DigRowBig:
	STA COLUP0
	STA COLUP1
	LDA #<DigBig
	LDX #>DigBig
	LDY #DigBig_H
DigGo:
	STA TTMP                 ; font base (low)
	STX TMP1                 ; font page
	STY TCNT                 ; cell height
	LDX #0
.c	LDA TPTR,X
	TAY
	LDA TTMP
.m	DEY
	BMI .s
	CLC
	ADC TCNT
	JMP .m
.s	STA TPTR,X
	INX
	LDA TMP1
	STA TPTR,X
	INX
	CPX #12
	BNE .c
	LDY TCNT
	DEY
	STY TTMP
	JMP DrawText

GameTx:	.byte <TxGame1, <TxGame2, <TxGame3, <TxGame4
GameTxHi: .byte >TxGame1, >TxGame2, >TxGame3, >TxGame4

Blank:	STA WSYNC
	DEX
	BNE Blank
	RTS

; A = colour, X = block low byte, TMP1 = its high byte, Y = height.
; The 6 columns follow each other inside one page (ALIGNCOL).
	SUBROUTINE
SetText:
	STA COLUP0
	STA COLUP1
	STY TCNT
	DEY
	STY TTMP                 ; line counter start (H-1)
	TXA
	LDX #0
.sp	STA TPTR,X
	CLC
	ADC TCNT
	INX
	INX
	CPX #12
	BNE .sp
	LDA TMP1
	LDX #1
.sh	STA TPTR,X
	INX
	INX
	CPX #13
	BNE .sh
DrawText:
	STA WSYNC
; the 48-pixel loop: 72 cycles a line, stores to GRP at cycles 44/47/50/53
.ln	LDY TTMP                 ; 3
	LDA (TPTR),Y             ; 5
	STA GRP0                 ; 3
	STA WSYNC
	LDA (TPTR+2),Y           ; 5   5
	STA GRP1                 ; 3   8
	LDA (TPTR+4),Y           ; 5  13
	STA GRP0                 ; 3  16
	LDA (TPTR+6),Y           ; 5  21
	STA TCNT                 ; 3  24
	LDA (TPTR+8),Y           ; 5  29
	TAX                      ; 2  31
	LDA (TPTR+10),Y          ; 5  36
	TAY                      ; 2  38
	LDA TCNT                 ; 3  41
	STA GRP1                 ; 3  44
	STX GRP0                 ; 3  47
	STY GRP1                 ; 3  50
	STA GRP0                 ; 3  53
	DEC TTMP                 ; 5  58
	BPL .ln                  ; 3  61 (+11 before WSYNC = 72)
	LDA #0
	STA WSYNC
	STA GRP0
	STA GRP1
	STA GRP0
	RTS

	ALIGN 256
TitleData:
	include "titledata.inc"

	TRAMP 3
