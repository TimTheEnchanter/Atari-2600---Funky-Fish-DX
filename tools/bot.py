# simple bot in ALE: go toward boss B, hover at Y target, fire; screenshot every K frames
import sys
from ale_py import ALEInterface
from PIL import Image
ale=ALEInterface(); ale.setInt('random_seed',int(sys.argv[4]) if len(sys.argv)>4 else 1); ale.setFloat('repeat_action_probability',0.0)
ale.loadROM(sys.argv[1]); N=int(sys.argv[2]); K=int(sys.argv[3])
BX=[0x40,0xE8,0x190,0x238]
for i in range(15): ale.act(1 if 10<=i<13 else 0)
shots=[]
def R(a): return int(ale.getRAM()[a-0x80])
tgt=1
for f in range(N):
    x=R(0x8B)*256+R(0x8C); y=R(0x94)
    if R(0xD9+tgt)==0 and R(0xDD+tgt)==0: tgt=(tgt+1)%4
    bx=BX[tgt]
    h = 0 if abs(x-bx-0x18)<6 else (1 if x<bx+0x18 else -1)
    ty=0x50
    v = 0 if abs(y-ty)<3 else (1 if y<ty else -1)
    fire = (f//8)%2
    # ALE: 2 UP 3 RIGHT 4 LEFT 5 DOWN 6 UR 7 UL 8 DR 9 DL ; +fire 10 UF 11 RF 12 LF 13 DF 14 URF 15 ULF 16 DRF 17 DLF
    tab={(0,0):0,(0,-1):2,(1,0):3,(-1,0):4,(0,1):5,(1,-1):6,(-1,-1):7,(1,1):8,(-1,1):9}
    a=tab[(h,v)]
    if fire: a={0:1,2:10,3:11,4:12,5:13,6:14,7:15,8:16,9:17}[a]
    ale.act(a)
    if f%K==0:
        im=Image.fromarray(ale.getScreenRGB()).resize((240,315)); shots.append(im)
        print(f,'x %03X y %02X'%(x,y),'81=%02X 85=%02X 86=%02X guards'%(R(0x81),R(0x85),R(0x86)),bytes(ale.getRAM()[0x48:0x61]).hex(),'tgt',tgt)
W=Image.new('RGB',(250*min(len(shots),10),320*((len(shots)+9)//10)),'white')
for i,im in enumerate(shots): W.paste(im,((i%10)*250,(i//10)*320))
W.save('bot.png')
