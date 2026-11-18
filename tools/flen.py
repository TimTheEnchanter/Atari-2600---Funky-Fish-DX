# flen.py rom frames : frame length histogram + overscan headroom (INTIM at the overscan wait entry)
import sys, random, collections
sys.path.insert(0,'/home/claude/ff/tools')
from vcs import VCS
rom=open(sys.argv[1],'rb').read(); N=int(sys.argv[2])
sym={}
for l in open('/home/claude/ff/work/ff.sym'):
    p=l.split()
    if len(p)>=2:
        try: sym[p[0]]=int(p[1],16)
        except: pass
v=VCS(rom)
OSW=0xF448
head=collections.Counter(); worst=[]
def hook(v):
    if v.bank==0 and v.mpu.pc==OSW:
        t=v.intim(); el=v.cyc()-v.tim_base
        neg = el > (v.tim_val+1)<<v.tim_shift
        head['neg' if neg else min(t,40)]+=1
        if neg: worst.append((v.frame, v.ram.hex()))
random.seed(3)
for f in range(N):
    sw=0x0A if f%1500 in (100,101,102) else 0x0B
    if f%20==0: v.swcha=random.choice([0xFF,0x7F,0xBF,0xDF,0xEF,0x5F,0x6F,0x9F,0xAF]); v.fire=random.random()<0.5
    v.swchb=sw; v.run_frames(1,hook)
print(collections.Counter(v.frame_lines[5:]).most_common(10))
print(sorted(head.items(),key=lambda x:str(x[0]))[:12])
for w in worst[:3]: print(w[0], w[1][:64])
