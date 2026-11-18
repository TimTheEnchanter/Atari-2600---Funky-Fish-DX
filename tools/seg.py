import sys, collections
sys.path.insert(0,'/home/claude/ff/tools')
from vcs import VCS
rom=open(sys.argv[1],'rb').read()
v=VCS(rom)
marks={0xF44D:'vsync',0xF541:'vblank',0xF95B:'vbwait',0xF960:'kernel',0xFCEE:'kend',0xFD51:'logic',0xF448:'oswait'}
v.run_frames(60); v.swchb=0x0A; v.run_frames(3); v.swchb=0x0B; v.fire=True; v.run_frames(5); v.fire=False
log=collections.defaultdict(list); last={}
def hook(v):
    pc=v.mpu.pc
    if v.bank==0 and pc in marks:
        n=marks[pc]
        if n in last and False: pass
        last[n]=v.cyc()
        if n=='oswait':
            fs=last.get('vsync',0)
            row=[(k,(last[k]-fs)/76) for k in ('vblank','vbwait','kernel','kend','logic','oswait') if k in last]
            log['r'].append(row)
v.swcha=0xBF
v.run_frames(200,hook)
for r in log['r'][-6:]: print(' '.join('%s=%.0f'%x for x in r), )
print(collections.Counter(v.frame_lines[-150:]))
