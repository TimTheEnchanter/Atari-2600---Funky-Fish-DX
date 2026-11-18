# head.py rom frames ADDR[,ADDR] : min INTIM (timer ticks left) at first arrival per frame at each address
import sys, random, collections
sys.path.insert(0,'/home/claude/ff/tools')
from vcs import VCS
rom=open(sys.argv[1],'rb').read(); N=int(sys.argv[2]); addrs=[int(x,16) for x in sys.argv[3].split(',')]
v=VCS(rom); random.seed(3)
seen=set(); res=collections.defaultdict(collections.Counter); f0=[0]
def hook(v):
    pc=v.mpu.pc
    if v.bank==0 and pc in addrs and (v.frame,pc) not in seen:
        seen.add((v.frame,pc)); el=v.cyc()-v.tim_base
        res[pc]['NEG' if el>(v.tim_val+1)<<v.tim_shift else v.intim()]+=1
for f in range(N):
    sw=0x0A if f%1500 in (100,101,102) else 0x0B
    if f%20==0: v.swcha=random.choice([0xFF,0x7F,0xBF,0xDF,0xEF,0x5F,0x6F,0x9F,0xAF]); v.fire=random.random()<0.5
    v.swchb=sw; v.run_frames(1,hook)
for a in addrs: print('%04X'%a, sorted(res[a].items(),key=lambda x:(str(type(x[0])),x[0]))[:6])
