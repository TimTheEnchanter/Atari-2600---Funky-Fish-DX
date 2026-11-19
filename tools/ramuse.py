import sys, random
sys.path.insert(0,'/home/claude/ff/tools')
import vcs
from vcs import VCS
rom=open(sys.argv[1],'rb').read()
v=VCS(rom); used=set(); rd=set()
ow,orr=v.write,v.read
def w(a,val):
    if v.frame<5: return ow(a,val)
    a2=a&0x1FFF
    if (a2&0x80) and not (a2&0x200) and not (a2&0x1000): used.add(0x80|(a2&0x7F))
    ow(a,val)
v.write=w
random.seed(3)
for f in range(8000):
    sw=0x0A if f%1500 in (100,101,102) else 0x0B
    if f%20==0: v.swcha=random.choice([0xFF,0x7F,0xBF,0xDF,0xEF,0x5F,0x6F,0x9F,0xAF]); v.fire=random.random()<0.5
    v.swchb=sw; v.run_frames(1)
print('never written:',' '.join('%02X'%a for a in range(0x80,0x100) if a not in used))
