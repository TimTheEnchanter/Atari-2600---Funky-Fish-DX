# build.py [skip-patch-names...]: regenerate F6 base, apply patches, assemble -> work/ff_f6.bin
import subprocess, sys, re
skip = set(sys.argv[1:])
subprocess.check_call(['python3', '-I', '/home/claude/ff/tools/mkport.py'])
s = open('/home/claude/ff/src/ff_base.asm').read()
PATCHES = [
 # name, address-tag of the line, replacement text
 ('ntsc overscan', 'FCF4', '\tLDA #OSCAN_GAME          ; FCF4 (was $34: 278-line frames)'),
 ('ntsc vblank',   'F547', '\tLDA #VBLANK_T           ; F547 (was $CD)'),
 ('ntsc title',    'F70C', '\tLDA #OSCAN_TITLE         ; F70C (was $32: 253-line frames)'),
]
hdr = 'VBLANK_T = $8B\nOSCAN_GAME = $29\nOSCAN_TITLE = $45\n'
for name, tag, new in PATCHES:
    if name in skip: continue
    pat = re.compile(r'^\t[^\n]*; %s: [^\n]*$' % tag, re.M)
    s, n = pat.subn(new.replace('\\', '\\\\'), s)
    assert n == 1, (name, n)
s = s.replace('\tprocessor 6502', '\tprocessor 6502\n' + hdr, 1)
open('/home/claude/ff/src/ff.asm', 'w').write(s)
r = subprocess.run(['/home/claude/ff/tools/dasm/bin/dasm', 'ff.asm', '-f3', '-o../work/ff_f6.bin', '-l../work/ff.lst', '-s../work/ff.sym'], cwd='/home/claude/ff/src', capture_output=True, text=True)
print(r.stdout[-300:]); sys.exit(r.returncode)
