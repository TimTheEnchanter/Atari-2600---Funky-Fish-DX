# build.py [skip-patch-names...]: regenerate F6 base, apply patches, assemble -> work/ff_f6.bin
import subprocess, sys, re
skip = set(sys.argv[1:])
subprocess.check_call(['python3', '-I', '/home/claude/ff/tools/mkport.py'])
s = open('/home/claude/ff/src/ff_base.asm').read()
# (name, bank, first-tag, last-tag, replacement)   tags are the original addresses
P = []
def rep(name, bank, a, b, new): P.append((name, bank, a, b or a, new))
# M1 NTSC timing
rep('ntsc overscan', 0, 'FCF4', None, '\tLDA #OSCAN_GAME')
rep('ntsc vblank',   0, 'F547', None, '\tLDA #VBLANK_T')
# M2 arcade content
M2 = 'm2'
rep(M2, 0, 'FBB5', None, '\tLDY #$06              ; sky band 6 lines (was 8): +2 lines of overscan')
rep('fix1', 0, 'FCDC', None, '\tJSR Digit1               ; was JSR $FEF2 (F6 dummy-read crash)')
rep('fix1', 0, 'F448', None, 'L0_F448:\n\tBIT TIMINT              ; overrun-safe: wait for the timer flag')
rep('fix1', 0, 'F44B', None, '\tBPL L0_F448')
rep('fix1', 0, 'F95B', None, '\tJMP VbWait')
rep('fix1', 0, 'F95E', None, '\t.byte $00,$00')
rep('fix1', 0, 'F960', None, '\t.byte $00,$00')
rep('fix1', 0, 'F962', None, '\t.byte $00,$00')
rep('fix1', 0, 'F964', None, 'L0_F964:\n\tSTA COLUBK')
rep('fix1', 0, 'F96C', 'F96F', '\tJMP L0_F9A1              ; score only (UA alternated with hi score)\n\tNOP\n\tNOP')
rep('fix1', 0, 'F555', 'F557', '\tJMP TR_TITLE             ; new flicker-free title in bank 2')
rep('m4', 0, 'F54C', 'F552', '\tJMP SelK                 ; M4: title / round banner / game\n\tds.b 6, $EA')
rep('m4', 0, 'F758', 'F75A', '\tJSR DeathCol             ; M4: flashing death\n\tNOP')
rep('m4', 0, 'FDD3', None, '\tCMP #$04                 ; M4: attract demo after ~17 s (was ~68 s)')
rep('m4', 1, 'F03C', None, '\tJSR PreLogic             ; M4: pause during the round banner')
rep(M2, 0, 'F403', 'F405', '\tJSR InitRound\n\tNOP')
rep(M2, 0, 'F40D', None, '\tLDX #$05')
rep(M2, 0, 'F774', None, '\tLDA BossLo0,X')
rep(M2, 0, 'F77B', None, '\tLDA BossHi0,X')
rep(M2, 0, 'FA46', None, '\tSBC RadThrLo,X')
rep(M2, 0, 'FA4D', None, '\tSBC RadThrHi,X')
rep(M2, 0, 'FF11', None, '\tLDY #$C0')
rep(M2, 0, 'FA7D', 'FA7F', '\tJMP RadarBlips')
rep(M2, 0, 'FAEC', None, 'L0_FAEC:\n\tLDX BOSSIDX')
rep('m3', 0, 'F72C', 'F72E', '\tJMP L0_F74E              ; M3: P0 is always the fish (bubble = ball)\n\tNOP')
rep('m3', 0, 'F824', None, '\tLDA GuardFr,Y            ; M3: 5-boss guard frame table')
rep('m3', 1, 'F3A7', None, '\tLDA #$5A                 ; M3: guards spawn below the boss band (was $6E)')
rep('m3', 1, 'F239', None, '\tJSR BossTouch            ; M3: boss touch by position (V)')
rep(M2, 1, 'F04B', None, '\tJSR GuardAI')
rep(M2, 1, 'F05A', None, '\tJMP RoundChk')
rep(M2, 1, 'F08B', None, '\tCMP #$03')
rep(M2, 1, 'F091', None, '\tCMP #$20')
rep(M2, 1, 'F133', None, '\tCMP #$03')
rep(M2, 1, 'F139', None, '\tCMP #$20')
rep(M2, 1, 'F516', None, '\tLDA #$DA')
rep(M2, 1, 'F18A', None, '\tLDX #$03')
rep(M2, 1, 'F18D', None, '\tLDA PlantLo,X')
rep(M2, 1, 'F194', None, '\tLDA PlantHi,X')
rep(M2, 1, 'F302', None, '\tLDA BossLo1,X')
rep(M2, 1, 'F309', None, '\tLDA BossHi1,X')
rep(M2, 1, 'F356', None, '\tLDA BossLo1,X')
rep(M2, 1, 'F557', None, '\tLDX #$05')
rep(M2, 1, 'F591', 'F593', '\tJSR HitTest')
rep(M2, 1, 'F5C9', 'F5DE', '\tJMP HitDo')
hdr = '''VBLANK_T = $7C
OSCAN_GAME = $2B
OSCAN_TITLE = $28
ROUND    = $DE      ; M2: round number (0 = first)
ROUNDT   = $DF      ; M4: round banner frames left
BANNER_T = 120
RADA_HM  = $F0
RADA_CO  = 6
RADB_HM  = $10
RADB_CO  = 8
RADM_HM  = $10
RADM_CO  = 10
T_HM0    = $F0
T_HM1    = $00
'''
lines = s.split('\n')
banks = []; b = -1
for l in lines:
    m = re.search(r'SEG BANK(\d)', l)
    if m: b = int(m.group(1))
    banks.append(b)
def addr(l):
    if l is None: return None
    m = re.search(r'; ([0-9A-F]{4}): ', l)
    return m.group(1) if m else None
for name, bank, a, z, new in P:
    if name in skip: continue
    i = [k for k, l in enumerate(lines) if banks[k] == bank and addr(l) == a]
    j = [k for k, l in enumerate(lines) if banks[k] == bank and addr(l) == z]
    assert len(i) == 1 and len(j) == 1, (name, a, z)
    i, j = i[0], j[0]
    # keep labels inside the range (they must not be targets we remove)
    labs = [l for l in lines[i:j+1] if l.endswith(':')]
    lines[i:j+1] = labs + [new + '    ; patch %s (was %s-%s)' % (name, a, z)] + [None] * (j - i - len(labs))
    banks[i:j+1] = [bank] * (j - i + 1)
lines = [l for l in lines if l is not None]
s = '\n'.join(lines)
if M2 in skip:
    for f in ('bank0x', 'bank0y', 'bank1x'): s = s.replace('\tinclude "%s.asm"' % f, '')
else:
    s = re.sub(r'^BGLOW\s*= \$DD', 'BGLOW      = $F3', s, flags=re.M)
s = s.replace('\tprocessor 6502', '\tprocessor 6502\n' + hdr, 1)

# ---- M3: bank 2 = relabelled copy of bank 0; the game kernel runs from it ----
def inline_includes(txt):
    def rep_inc(m):
        f = m.group(1)
        if f.startswith('bank0') and f.endswith('.asm'):
            return open('/home/claude/ff/src/' + f).read()
        return m.group(0)
    return re.sub(r'^\tinclude "([^"]+)".*$', rep_inc, txt, flags=re.M)
i0 = s.index('\tSEG BANK0'); i1 = s.index('\tTRAMP 0')
blk = inline_includes(s[i0:i1])
# bank-2-only code goes into the free tail of bank0z ($F558-$F718)
if 'm3' not in skip:
    blk = blk.replace('\tds.b $F719 - ., $00', open('/home/claude/ff/src/kern2.asm').read() + '\n\tds.b $F719 - ., $00', 1)
    KP = [('FB83', None, '\tLDA BALLHM                ; M3: ball = bubble'),
          ('FB88', None, '\tLDA BALLHM'),
          ('FB93', None, '\tLDA BUBROW'),
          ('FC24', None, '\tCPY #$04                 ; bubble 4 lines'),
          ('FAF2', None, '\tLDA #$20                 ; ball 4 px'),
          ('FAF9', None, '\tAND #$00'),
          ('FB78', 'FB80', '\tJSR BossPos              ; M3: P1 starts at the boss\n\tds.b 8, $EA'),
          ('FBF0', 'FC00', '\tJMP BossK                ; M3: boss monster band\n\tds.b 15, $00')]
    for a, z, new in KP:
        z = z or a
        ls = blk.split('\n')
        ia = [n for n, l in enumerate(ls) if re.search(r'; %s: ' % a, l)]
        iz = [n for n, l in enumerate(ls) if re.search(r'; %s: ' % z, l)]
        assert len(ia) == 1 and len(iz) == 1, (a, z)
        keep = [l for l in ls[ia[0]:iz[0]+1] if l.endswith(':')]
        ls[ia[0]:iz[0]+1] = keep + [new]
        blk = '\n'.join(ls)
defs = set(re.findall(r'^([A-Za-z_][A-Za-z0-9_]*):', blk, flags=re.M))
defs |= set(re.findall(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=', blk, flags=re.M))
def relabel(t):
    return re.sub(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', lambda m: 'K_' + m.group(1) if m.group(1) in defs else m.group(1), t)
lines = []
for l in blk.split('\n'):
    if 'SEG BANK0' in l: l = '\tSEG BANK2'
    elif re.match(r'^\tORG \$0000', l): l = '\tORG $2000'
    else:
        code, sep, com = l.partition(';')
        l = relabel(code) + sep + com
    lines.append(l)
k = '\n'.join(lines)
k = re.sub(r'^\t[^\n]*; FD51: [^\n]*$', '\tJMP TR_KBACK              ; kernel done -> bank 0 $FD51', k, count=1, flags=re.M)
open('/home/claude/ff/src/bank2.asm', 'w').write('; GENERATED by tools/build.py: bank 0 copy (labels prefixed K_), runs the game kernel\n' + k + '\n\tTRAMP 2\n')
# bank 0 itself enters the copy at the start of the game kernel
s = re.sub(r'^\tJMP VbWait[^\n]*$', '\tJMP TR_KERN              ; game kernel runs in bank 2', s, count=1, flags=re.M)
open('/home/claude/ff/src/ff.asm', 'w').write(s)
r = subprocess.run(['/home/claude/ff/tools/dasm/bin/dasm', 'ff.asm', '-f3', '-o../work/ff_f6.bin', '-l../work/ff.lst', '-s../work/ff.sym'], cwd='/home/claude/ff/src', capture_output=True, text=True)
print(r.stdout[-600:])
if r.returncode: sys.exit(r.returncode)
# F6 safety: a page-crossing branch does a dummy read at (old page | target low);
# indexed modes crossing a page do one at (base page | low). Either must never hit $xFF6-$xFF9.
d = open('/home/claude/ff/work/ff_f6.bin', 'rb').read()
DEAD = {(0, 0xFF02), (2, 0xFF02)}       # UA's old $FEF2 loop, no longer called
bad = []
for bk in range(4):
    m = d[bk*4096:(bk+1)*4096]
    for a in range(0xF000, 0xFFFE):
        op = m[a - 0xF000]
        if op in (0x10,0x30,0x50,0x70,0x90,0xB0,0xD0,0xF0):
            o = m[a - 0xF000 + 1]; n = a + 2; t = (n + (o - 256 if o > 127 else o)) & 0xFFFF
            if (t >> 8) != (n >> 8) and 0xFFF6 <= ((n & 0xFF00) | (t & 0xFF)) <= 0xFFF9 and (bk, a) not in DEAD:
                bad.append('bank %d branch at %04X' % (bk, a))
if bad:
    print('F6 HOTSPOT HAZARD:', bad); sys.exit(3)
print('F6 hotspot scan: clean')
# ---- M3: sprite graphics patched straight into the bank 2 copy (the kernel's bank) ----
if 'm3' not in skip:
    SPR = {  # address: rows top first (9 shown, 11 stored)
        0xF11C: ['..##....', '.###....', '##.#....', '...##...', '...###..', '....##..', '...##...', '....#.#.', '.....#..'],
        0xF132: ['..##....', '.###....', '##.#.#..', '...###..', '...##...', '....##..', '...##...', '...#.#..', '....#...'],
    }
    rom = bytearray(open('/home/claude/ff/work/ff_f6.bin', 'rb').read())
    for a, rows in SPR.items():
        bs = [int(r.replace('#', '1').replace('.', '0'), 2) for r in rows] + [0, 0]
        o = 2 * 4096 + (a - 0xF000)
        rom[o:o + 11] = bytes(bs)
    open('/home/claude/ff/work/ff_f6.bin', 'wb').write(rom)
    print('sprites patched:', ', '.join('%04X' % a for a in SPR))
