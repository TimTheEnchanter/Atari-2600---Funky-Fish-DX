import sys
sys.path.insert(0,'/home/claude/ff/tools')
from vcs import VCS
rom=open(sys.argv[1],'rb').read()
v=VCS(rom)
A={0:(0xFF,0),1:(0xFF,1),3:(0x7F,0),4:(0xBF,0),11:(0x7F,1),13:(0xDF,1),2:(0xEF,0),5:(0xDF,0)}
seq=[(60,0,'reset'),(10,0),(5,1),(60,0),(120,3),(120,4),(60,1),(200,11),(300,13)]
for s in seq:
    n,a=s[0],s[1]
    v.swcha,v.fire=A[a]
    v.swchb=0x0A if len(s)>2 else 0x0B
    f0=v.frame; steps=v.run_frames(n,maxsteps=n*40000)
    print(s, 'frames',v.frame-f0,'pc %04X bank %d'%(v.mpu.pc,v.bank),'ram',v.ram[:0x20].hex())
