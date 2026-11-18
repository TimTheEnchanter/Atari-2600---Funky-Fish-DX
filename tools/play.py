# play.py rom script.txt outprefix : script lines "frames action [shot]" ; actions per ALE ids
import sys
from ale_py import ALEInterface
from PIL import Image
ale=ALEInterface(); ale.setInt('random_seed',1); ale.setFloat('repeat_action_probability',0.0)
ale.setBool('truncate_on_loss_of_life',False)
ale.loadROM(sys.argv[1])
n=0
for l in open(sys.argv[2]):
    p=l.split()
    if not p: continue
    fr,act=int(p[0]),int(p[1])
    for i in range(fr): ale.act(act); n+=1
    if len(p)>2:
        Image.fromarray(ale.getScreenRGB()).resize((320,420),Image.NEAREST).save('%s_%s.png'%(sys.argv[3],p[2]))
        print(p[2],n,bytes(ale.getRAM()).hex())
