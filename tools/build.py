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
rep('ntsc title',    0, 'F70C', None, '\tLDA #OSCAN_TITLE')
# M2 arcade content
M2 = 'm2'
rep(M2, 0, 'FBB5', None, '\tLDY #$06              ; sky band 6 lines (was 8): +2 lines of overscan')
rep(M2, 0, 'F403', 'F405', '\tJSR InitRound\n\tNOP')
rep(M2, 0, 'F40D', None, '\tLDX #$05')
rep(M2, 0, 'F774', None, '\tLDA BossLo0,X')
rep(M2, 0, 'F77B', None, '\tLDA BossHi0,X')
rep(M2, 0, 'FA46', None, '\tSBC RadThrLo,X')
rep(M2, 0, 'FA4D', None, '\tSBC RadThrHi,X')
rep(M2, 0, 'FF11', None, '\tLDY #$C0')
rep(M2, 0, 'FA7D', 'FA7F', '\tJMP RadarBlips')
rep(M2, 0, 'FAEC', None, 'L0_FAEC:\n\tLDX BOSSIDX')
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
OSCAN_GAME = $2C
OSCAN_TITLE = $46
ROUND    = $DE      ; M2: round number (0 = first)
RADA_HM  = $F0
RADA_CO  = 6
RADB_HM  = $10
RADB_CO  = 8
RADM_HM  = $10
RADM_CO  = 10
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
open('/home/claude/ff/src/ff.asm', 'w').write(s)
r = subprocess.run(['/home/claude/ff/tools/dasm/bin/dasm', 'ff.asm', '-f3', '-o../work/ff_f6.bin', '-l../work/ff.lst', '-s../work/ff.sym'], cwd='/home/claude/ff/src', capture_output=True, text=True)
print(r.stdout[-600:]); sys.exit(r.returncode)
