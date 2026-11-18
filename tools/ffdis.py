# Tracing disassembler for 2600 ROMs -> dasm source (byte-identical).
# usage: dis.py rom.a26 out.asm [cov.pkl] [extra.txt]
import sys, pickle

MODES = {}
def op(code, mn, mode): MODES[code] = (mn, mode)
tbl = """
00 BRK imp|01 ORA izx|05 ORA zp|06 ASL zp|08 PHP imp|09 ORA imm|0A ASL acc|0D ORA abs|0E ASL abs
10 BPL rel|11 ORA izy|15 ORA zpx|16 ASL zpx|18 CLC imp|19 ORA aby|1D ORA abx|1E ASL abx
20 JSR abs|21 AND izx|24 BIT zp|25 AND zp|26 ROL zp|28 PLP imp|29 AND imm|2A ROL acc|2C BIT abs|2D AND abs|2E ROL abs
30 BMI rel|31 AND izy|35 AND zpx|36 ROL zpx|38 SEC imp|39 AND aby|3D AND abx|3E ROL abx
40 RTI imp|41 EOR izx|45 EOR zp|46 LSR zp|48 PHA imp|49 EOR imm|4A LSR acc|4C JMP abs|4D EOR abs|4E LSR abs
50 BVC rel|51 EOR izy|55 EOR zpx|56 LSR zpx|58 CLI imp|59 EOR aby|5D EOR abx|5E LSR abx
60 RTS imp|61 ADC izx|65 ADC zp|66 ROR zp|68 PLA imp|69 ADC imm|6A ROR acc|6C JMP ind|6D ADC abs|6E ROR abs
70 BVS rel|71 ADC izy|75 ADC zpx|76 ROR zpx|78 SEI imp|79 ADC aby|7D ADC abx|7E ROR abx
81 STA izx|84 STY zp|85 STA zp|86 STX zp|88 DEY imp|8A TXA imp|8C STY abs|8D STA abs|8E STX abs
90 BCC rel|91 STA izy|94 STY zpx|95 STA zpx|96 STX zpy|98 TYA imp|99 STA aby|9A TXS imp|9D STA abx
A0 LDY imm|A1 LDA izx|A2 LDX imm|A4 LDY zp|A5 LDA zp|A6 LDX zp|A8 TAY imp|A9 LDA imm|AA TAX imp|AC LDY abs|AD LDA abs|AE LDX abs
B0 BCS rel|B1 LDA izy|B4 LDY zpx|B5 LDA zpx|B6 LDX zpy|B8 CLV imp|B9 LDA aby|BA TSX imp|BC LDY abx|BD LDA abx|BE LDX aby
C0 CPY imm|C1 CMP izx|C4 CPY zp|C5 CMP zp|C6 DEC zp|C8 INY imp|C9 CMP imm|CA DEX imp|CC CPY abs|CD CMP abs|CE DEC abs
D0 BNE rel|D1 CMP izy|D5 CMP zpx|D6 DEC zpx|D8 CLD imp|D9 CMP aby|DD CMP abx|DE DEC abx
E0 CPX imm|E1 SBC izx|E4 CPX zp|E5 SBC zp|E6 INC zp|E8 INX imp|E9 SBC imm|EA NOP imp|EC CPX abs|ED SBC abs|EE INC abs
F0 BEQ rel|F1 SBC izy|F5 SBC zpx|F6 INC zpx|F8 SED imp|F9 SBC aby|FD SBC abx|FE INC abx
"""
for line in tbl.strip().split('\n'):
    for e in line.split('|'):
        c, m, md = e.split(); op(int(c, 16), m, md)
SIZE = dict(imp=1, acc=1, imm=2, zp=2, zpx=2, zpy=2, izx=2, izy=2, rel=2, abs=3, abx=3, aby=3, ind=3)

TIAW = ['VSYNC','VBLANK','WSYNC','RSYNC','NUSIZ0','NUSIZ1','COLUP0','COLUP1','COLUPF','COLUBK','CTRLPF','REFP0','REFP1','PF0','PF1','PF2',
        'RESP0','RESP1','RESM0','RESM1','RESBL','AUDC0','AUDC1','AUDF0','AUDF1','AUDV0','AUDV1','GRP0','GRP1','ENAM0','ENAM1','ENABL',
        'HMP0','HMP1','HMM0','HMM1','HMBL','VDELP0','VDELP1','VDELBL','RESMP0','RESMP1','HMOVE','HMCLR','CXCLR']
TIAR = ['CXM0P','CXM1P','CXP0FB','CXP1FB','CXM0FB','CXM1FB','CXBLPF','CXPPMM','INPT0','INPT1','INPT2','INPT3','INPT4','INPT5']
RIOT = {0x280:'SWCHA',0x281:'SWACNT',0x282:'SWCHB',0x283:'SWBCNT',0x284:'INTIM',0x285:'TIMINT',0x294:'TIM1T',0x295:'TIM8T',0x296:'TIM64T',0x297:'T1024T'}

RAMN = {}; RAMDEF = []
for _l in open(__file__.replace('ffdis.py','ramnames.txt')):
    _l = _l.split('#')[0].split(None, 2)
    if len(_l) >= 2:
        _a = int(_l[0], 16); RAMDEF.append((_l[1], _a, _l[2].strip() if len(_l) > 2 else ''))
        RAMN[_a] = _l[1]
for _n, _a, _c in list(RAMDEF):
    for _k in (1, 2, 3):
        if _a - _k not in RAMN: RAMN[_a - _k] = '%s-%d' % (_n, _k)
def is_read(mn): return mn in ('LDA','LDX','LDY','CMP','CPX','CPY','BIT','ORA','AND','EOR','ADC','SBC')

class Bank:
    def __init__(self, data, base, idx):
        self.d = data; self.base = base; self.idx = idx
        self.code = {}       # addr -> (mn, mode, operand)
        self.labels = {}     # addr -> name
        self.isdata = set()
        self.jumpind = set()
    def b(self, a): return self.d[a - self.base]
    def inb(self, a): return self.base <= a < self.base + len(self.d)

def trace(bk, entries):
    todo = list(entries)
    while todo:
        a = todo.pop()
        while bk.inb(a) and a not in bk.code:
            c = bk.b(a)
            if c not in MODES: print('bad opcode bank%d %04X %02X' % (bk.idx, a, c)); break
            mn, md = MODES[c]; sz = SIZE[md]
            if not bk.inb(a + sz - 1): break
            opnd = None
            if sz == 2: opnd = bk.b(a + 1)
            if sz == 3: opnd = bk.b(a + 1) | bk.b(a + 2) << 8
            bk.code[a] = (mn, md, opnd)
            if md == 'rel':
                t = (a + 2 + (opnd - 256 if opnd > 127 else opnd)) & 0xFFFF
                todo.append(t); bk.labels.setdefault(t, None)
            if mn in ('JSR', 'JMP') and md == 'abs':
                if bk.inb(opnd) and not (0xFFF0 <= opnd):
                    todo.append(opnd); bk.labels.setdefault(opnd, None)
            if mn in ('RTS', 'RTI', 'BRK') or (mn == 'JMP'):
                break
            a += sz

def main():
    rom = open(sys.argv[1], 'rb').read(); out = sys.argv[2]
    cov = pickle.load(open(sys.argv[3], 'rb')) if len(sys.argv) > 3 else set()
    extra = {}
    if len(sys.argv) > 4:
        for l in open(sys.argv[4]):
            l = l.split('#')[0].split()
            if l: extra.setdefault(int(l[0]), []).append((l[1], l[2:] if len(l) > 2 else []))
    nb = len(rom) // 4096
    banks = [Bank(rom[i*4096:(i+1)*4096], 0xF000, i) for i in range(nb)]
    for bk in banks:
        ents = [a for (b, a) in cov if b == bk.idx and a >= 0xF000]
        for (kind, args) in extra.get(bk.idx, []):
            if kind == 'code': ents.append(int(args[0], 16))
        trace(bk, ents)
    # bank-specific entry from vectors etc. is via cov or extra
    lines = ['; Funky Fish (UA Ltd, unreleased) - disassembly', '; generated by tools/dis.py', '', '\tprocessor 6502', '']
    for i, n in enumerate(TIAW): lines.append('%-8s = $%02X' % (n, i))
    for i, n in enumerate(TIAR): lines.append('%-8s = $%02X' % (n, i))
    for a, n in sorted(RIOT.items()): lines.append('%-8s = $%04X' % (n, a))
    lines.append('BANK0    = $0220   ; UA hotspot: any access selects bank 0')
    lines.append('BANK1    = $0240   ; UA hotspot: any access selects bank 1')
    lines.append('')
    lines.append('; ---- RAM map ----')
    for _n, _a, _c in RAMDEF: lines.append('%-10s = $%02X   ; %s' % (_n, _a, _c))
    lines.append('')
    # collect data-referenced labels
    for bk in banks:
        for a, (mn, md, o) in bk.code.items():
            if md in ('abs', 'abx', 'aby', 'ind') and o is not None and bk.inb(o):
                if mn not in ('JSR', 'JMP') or md == 'ind':
                    bk.labels.setdefault(o, None)
            if md == 'imm' and False: pass
    for bk in banks:
        for a in sorted(bk.labels):
            p = 'L' if a in bk.code else 'D'
            bk.labels[a] = '%s%d_%04X' % (p, bk.idx, a)
        lines.append('; ' + '=' * 70)
        lines.append('\tSEG BANK%d' % bk.idx)
        lines.append('\tORG $%04X' % (bk.idx * 0x1000))
        lines.append('\tRORG $F000')
        a = 0xF000
        end = 0xF000 + len(bk.d)
        def lab(t, off=0):
            if t in bk.labels and bk.labels[t]: return bk.labels[t]
            # within a label range? use nearest preceding label + offset for data
            return None
        while a < end:
            if a in bk.labels and bk.labels[a]:
                lines.append('%s:' % bk.labels[a])
            if a in bk.code:
                mn, md, o = bk.code[a]
                sz = SIZE[md]
                # ensure no label falls inside instruction
                inner = [x for x in range(a + 1, a + sz) if x in bk.labels and bk.labels[x]]
                if inner:
                    for x in inner: lines.append('%s = $%04X' % (bk.labels[x], x)); bk.labels[x] = '%s' % bk.labels[x]
                def name(v, wr):
                    if bk.inb(v):
                        return bk.labels.get(v) or '$%04X' % v
                    if 0x80 <= v < 0x100 and v in RAMN:
                        return RAMN[v]
                    if v < 0x80 and v >= 0:
                        if wr:
                            return TIAW[v] if v < len(TIAW) else '$%02X' % v
                        return TIAR[v] if v < len(TIAR) else '$%02X' % v
                    if v in RIOT: return RIOT[v]
                    if v == 0x220: return 'BANK0'
                    if v == 0x240: return 'BANK1'
                    return '$%02X' % v if v < 0x100 else '$%04X' % v
                wr = mn in ('STA', 'STX', 'STY', 'INC', 'DEC', 'ASL', 'LSR', 'ROL', 'ROR')
                if md == 'imp': s = mn
                elif md == 'acc': s = mn
                elif md == 'imm': s = '%s #$%02X' % (mn, o)
                elif md == 'zp': s = '%s %s' % (mn, name(o, wr))
                elif md == 'zpx': s = '%s %s,X' % (mn, name(o, wr))
                elif md == 'zpy': s = '%s %s,Y' % (mn, name(o, wr))
                elif md == 'izx': s = '%s (%s,X)' % (mn, name(o, False))
                elif md == 'izy': s = '%s (%s),Y' % (mn, name(o, False))
                elif md == 'rel':
                    t = (a + 2 + (o - 256 if o > 127 else o)) & 0xFFFF
                    s = '%s %s' % (mn, bk.labels[t])
                else:
                    sfx = '.w' if o < 0x100 else ''
                    n = name(o, wr)
                    if md == 'abs': s = '%s%s %s' % (mn, sfx, n)
                    elif md == 'abx': s = '%s%s %s,X' % (mn, sfx, n)
                    elif md == 'aby': s = '%s%s %s,Y' % (mn, sfx, n)
                    elif md == 'ind': s = '%s (%s)' % (mn, n)
                raw = ' '.join('%02X' % bk.b(x) for x in range(a, a + sz))
                lines.append('\t%-24s; %04X: %s' % (s, a, raw))
                a += sz
            else:
                # data run until next code or label
                run = []
                while a < end and a not in bk.code and len(run) < 8:
                    if run and a in bk.labels and bk.labels[a]: break
                    run.append(bk.b(a)); a += 1
                lines.append('\t.byte %-40s; %04X' % (','.join('$%02X' % x for x in run), a - len(run)))
                continue
        lines.append('')
    open(out, 'w').write('\n'.join(lines) + '\n')
    for bk in banks: print('bank', bk.idx, 'code bytes', sum(SIZE[m[1]] for m in bk.code.values()), 'labels', len(bk.labels))

main()
