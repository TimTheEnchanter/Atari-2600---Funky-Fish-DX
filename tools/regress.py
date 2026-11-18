# regress.py romA romB frames [mask-addrs-hex,...] : run both with identical scripted inputs, compare RAM per frame
import sys, random
sys.path.insert(0,'/home/claude/ff/tools')
from vcs import VCS
A=open(sys.argv[1],'rb').read(); B=open(sys.argv[2],'rb').read(); N=int(sys.argv[3])
mask=set(int(x,16) for x in sys.argv[4].split(',')) if len(sys.argv)>4 and sys.argv[4] else set()
va,vb=VCS(A),VCS(B)
random.seed(7); diffs=0
for f in range(N):
    if f%1500 in (100,101,102): sw=0x0A
    else: sw=0x0B
    if f%20==0:
        ja=random.choice([0xFF,0x7F,0xBF,0xDF,0xEF,0x5F,0x6F,0x9F,0xAF]); fi=random.random()<0.5
    if f%3000==2000: v_sel=0x09  # select
    for v in (va,vb): v.swcha=ja; v.fire=fi; v.swchb=sw
    va.run_frames(1); vb.run_frames(1)
    d=[i+0x80 for i in range(128) if va.ram[i]!=vb.ram[i] and (i+0x80) not in mask]
    if d:
        diffs+=1
        if diffs<5: print('frame',f,'diff',' '.join('%02X:%02X/%02X'%(a,va.ram[a-0x80],vb.ram[a-0x80]) for a in d))
print('frames',N,'diff frames',diffs,'lines A',sorted(set(va.frame_lines[5:]))[:3],max(va.frame_lines[5:]),'B',sorted(set(vb.frame_lines[5:]))[:3],max(vb.frame_lines[5:]))
