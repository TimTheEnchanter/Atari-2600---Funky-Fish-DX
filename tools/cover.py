import sys, random, pickle, time
sys.path.insert(0,'/home/claude/ff/tools')
from vcs import VCS
rom=open(sys.argv[1],'rb').read()
N=int(sys.argv[2]) if len(sys.argv)>2 else 3000
v=VCS(rom)
random.seed(1)
t=time.time()
v.run_frames(200)
print('attract done', v.frame, time.time()-t, 'lines', v.frame_lines[-5:])
for f in range(N):
    if f%400 < 3: v.swchb = 0x0A   # reset
    else: v.swchb = 0x0B
    if f%30==0:
        v.swcha = random.choice([0xFF,0x7F,0xBF,0xDF,0xEF,0x5F,0x6F,0x9F,0xAF])
        v.fire = random.random()<0.5
    v.run_frames(1)
print('frames',v.frame,time.time()-t)
print('cov',len(v.cov))
pickle.dump(v.cov,open('cov.pkl','wb'))
print('ram',v.ram.hex())
import collections; print(collections.Counter(v.frame_lines).most_common(8))
