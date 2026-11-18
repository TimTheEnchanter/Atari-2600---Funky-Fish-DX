import sys
from ale_py import ALEInterface
ale=ALEInterface(); ale.setInt('random_seed',1); ale.setFloat('repeat_action_probability',0.0)
ale.loadROM(sys.argv[1])
seq=[(10,0),(5,1),(60,0),(120,3),(120,4),(60,1),(200,11)]
n=0; prev=None
for fr,a in seq:
    for i in range(fr):
        ale.act(a); n+=1
        r=bytes(ale.getRAM())
        if prev is not None and r==prev: print('frozen at',n); 
        if prev is not None and r==prev and n>3: 
            print(r.hex()); sys.exit()
        prev=r
