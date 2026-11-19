import sys, random, collections
sys.path.insert(0,'/home/claude/ff/tools')
from vcs import VCS
rom=open(sys.argv[1],'rb').read(); N=int(sys.argv[2])
v=VCS(rom); random.seed(3)
calls=[0xF03F,0xF042,0xF045,0xF048,0xF04B,0xF04E,0xF051,0xF054,0xF057,0xF05A]
names=['F05D','F1F4','F2F9','F34D','F495','AI','F22F','F584','F52E','F544']
t={}; cur={}; mx=collections.defaultdict(int); tot=collections.defaultdict(int)
seg={}
def hook(v):
    pc=v.mpu.pc
    if v.bank==1:
        if pc==0xF03C: cur['s']=v.cyc()
        if pc in calls:
            i=calls.index(pc); d=v.cyc()-cur['s']; cur['s']=v.cyc()
            mx[names[i]]=max(mx[names[i]],d)
    if v.bank==0:
        if pc==0xFCEE: seg['k']=v.cyc()
        if pc==0xFDBD: seg['b1']=v.cyc()
        if pc==0xF44D and 'k' in seg:
            pass
        if pc==0xF448 and 'k' in seg:
            d=(v.cyc()-seg['k'])/76; mx['logic_lines']=max(mx['logic_lines'],d); seg.clear()
for f in range(N):
    sw=0x0A if f%1500 in (100,101,102) else 0x0B
    if f%20==0: v.swcha=random.choice([0xFF,0x7F,0xBF,0xDF,0xEF,0x5F,0x6F,0x9F,0xAF]); v.fire=random.random()<0.5
    v.swchb=sw; v.run_frames(1,hook)
for k,x in mx.items(): print(k, x if k=='logic_lines' else '%d cyc = %.1f lines'%(x,x/76))
