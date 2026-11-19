# stress.py rom frames coll : random play + random collisions + pokes; reports overruns / frame lengths / headroom
import sys, random, collections
sys.path.insert(0,'/home/claude/ff/tools')
from vcs import VCS
v=VCS(open(sys.argv[1],'rb').read()); random.seed(int(sys.argv[4]) if len(sys.argv)>4 else 5)
v.coll=float(sys.argv[3]); N=int(sys.argv[2])
seen=set(); head=collections.defaultdict(lambda:999); minsp=[0xFF]
W={0xF448:'oscan',0xF95B:'vblank',0xF53C:'vsync',0xF5E8:'tvblank'}
def hook(v):
    pc=v.mpu.pc
    if v.mpu.sp<minsp[0]: minsp[0]=v.mpu.sp
    if v.bank==0 and pc in W and (v.frame,pc) not in seen:
        seen.add((v.frame,pc))
        t=-1 if v.expired() else v.intim()
        head[W[pc]]=min(head[W[pc]],t)
for f in range(N):
    sw=0x0A if f%2500 in (100,101,102) else 0x0B
    if f%15==0: v.swcha=random.choice([0xFF,0x7F,0xBF,0xDF,0xEF,0x5F,0x6F,0x9F,0xAF]); v.fire=random.random()<0.6
    if f%300==0:
        if random.random()<0.3:
            for i in range(5): v.ram[0xD9-0x80+i]=0; v.ram[0xF3-0x80+i]=0
        s=random.randrange(4); v.ram[0xC9-0x80+s]=random.choice([1,2,3]); v.ram[0xD1-0x80+s]=random.randrange(0x10,0x70)
    v.swchb=sw; v.run_frames(1,hook)
c=collections.Counter(v.frame_lines[5:])
print('overruns',v.overruns,'minSP %02X'%minsp[0],'headroom',dict(head),'lines',sorted(c.items())[:3],'...',sorted(c.items())[-3:])
