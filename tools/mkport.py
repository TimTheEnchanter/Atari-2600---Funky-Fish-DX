# Turns the byte-identical UA disassembly (src_ff.asm) into the F6 (16K) port base:
#  - UA hotspot trampolines at $FFF0-$FFFB are replaced by F6 trampolines at $FFE0-$FFEB
#    (the old spot overlaps the F6 hotspots $FFF6-$FFF9, which fire on instruction fetch).
#  - banks 2 and 3 are added for new code; each includes the same reset trampoline.
import re, sys
src = open('/home/claude/ff/src_ff.asm').read().split('\n')
out = []; bank = None
for l in src:
    m = re.search(r'SEG BANK(\d)', l)
    if m:
        if bank is not None: out.append('\tTRAMP %d' % bank)
        bank = int(m.group(1))
    a = re.search(r';\s*([0-9A-F]{4})(:|$)', l)
    if bank is not None and a and int(a.group(1), 16) >= 0xFFD8 and not l.strip().endswith(':'):
        continue
    l = l.replace('JMP $FFF6', 'JMP TR_SWAP')
    if l.startswith('\tSEG BANK0'):
        out.append(open('/home/claude/ff/src/tramp.inc').read())
    out.append(l)
out.append('\tTRAMP %d' % bank)
out.append('\tinclude "bank2.asm"')
out.append('\tinclude "bank3.asm"')
open('/home/claude/ff/src/ff_base.asm', 'w').write('\n'.join(out) + '\n')
