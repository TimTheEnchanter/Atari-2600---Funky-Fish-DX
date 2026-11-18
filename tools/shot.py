import sys, numpy as np
from ale_py import ALEInterface
from PIL import Image
rom=sys.argv[1]; frames=[int(x) for x in sys.argv[2].split(',')]; act=int(sys.argv[3]) if len(sys.argv)>3 else 0
ale=ALEInterface(); ale.setInt('random_seed',1); ale.setFloat('repeat_action_probability',0.0)
ale.setBool('truncate_on_loss_of_life',False)
ale.loadROM(rom)
n=0
for f in frames:
    while n<f:
        ale.act(act); n+=1
    Image.fromarray(ale.getScreenRGB()).resize((320,420),Image.NEAREST).save('shot_%d.png'%f)
print('ram',bytes(ale.getRAM()).hex())
