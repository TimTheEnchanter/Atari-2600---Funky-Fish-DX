import sys, random, collections
sys.path.insert(0,'/home/claude/ff/tools')
from vcs import VCS
rom=open(sys.argv[1],'rb').read(); N=int(sys.argv[2])
v=VCS(rom); random.seed(3)
st={'first':None}; heads=collections.Counter(); long=collections.Counter(); ex=[]
def hook(v):
    pc=v.mpu.pc
    if v.bank==0 and pc==0xF448 and st['first'] is None:
        el=v.cyc()-v.tim_base
        st['first']=('neg' if el>(v.tim_val+1)<<v.tim_shift else v.intim())
    if v.bank==0 and pc==0xF44D: st['first']=None
pcs=collections.Counter()
for f in range(N):
    sw=0x0A if f%1500 in (100,101,102) else 0x0B
    if f%20==0: v.swcha=random.choice([0xFF,0x7F,0xBF,0xDF,0xEF,0x5F,0x6F,0x9F,0xAF]); v.fire=random.random()<0.5
    v.swchb=sw
    n0=len(v.frame_lines); v.run_frames(1,hook)
    heads[st['first']]+=1
    fl=v.frame_lines[-1]
    if fl>264 and f>5:
        long[(v.ram[1],v.ram[5]&0xF0)]+=1
        if len(ex)<4: ex.append((f,fl,v.ram[:0x20].hex()))
print('overscan headroom at wait (INTIM ticks):',sorted(heads.items(),key=lambda x:str(x[0]))[:8])
print('long frames by ($81,$85hi):',long.most_common(8))
for e in ex: print(e)
