# Minimal Atari 2600 harness on py65 for code coverage / RAM traces.
# Supports UA (8K, hotspots $0220/$0240) and F6/F8 bankswitching.
# No video; TIA reads return 0 (collisions) or "not pressed" for inputs.
from py65.devices.mpu6502 import MPU

class Mem:
    def __init__(self, vcs): self.v = vcs
    def __len__(self): return 0x10000
    def __getitem__(self, a):
        if isinstance(a, slice):
            return [self[i] for i in range(*a.indices(0x10000))]
        return self.v.read(a)
    def __setitem__(self, a, val): self.v.write(a, val)

class VCS:
    def __init__(self, rom, scheme=None):
        self.rom = rom
        n = len(rom)
        self.scheme = scheme or ('UA' if n == 8192 else 'F6' if n == 16384 else '4K')
        self.nb = max(1, n // 4096)
        self.bank = 0 if self.scheme == 'UA' else self.nb - 1
        self.ram = bytearray(128)
        self.mpu = MPU(memory=Mem(self))
        self.cov = set()        # (bank, addr) executed
        self.dread = set()      # (bank, addr) data reads from ROM
        self.tim_base = 0; self.tim_val = 0; self.tim_shift = 10
        self.frame = 0; self.line = 0
        self.swcha = 0xFF; self.swchb = 0x0B; self.fire = False
        self.tia_w = {}         # last writes
        self.audlog = None
        self.vsync_on = False
        self.lines_this_frame = 0
        self.frame_lines = []
        self.wsync_count = 0
        self.mpu.pc = self.word(0xFFFC)
        self.in_fetch = False

    def word(self, a): return self.read(a) | self.read(a + 1) << 8

    def cyc(self): return self.mpu.processorCycles

    def hot(self, a):
        a &= 0x1FFF
        if self.scheme == 'UA':
            if (a & 0x1260) == 0x0220: self.bank = 0
            elif (a & 0x1260) == 0x0240: self.bank = 1
        elif self.scheme == 'F6' and 0x1FF6 <= a <= 0x1FF9:
            self.bank = a - 0x1FF6
        elif self.scheme == 'F8' and 0x1FF8 <= a <= 0x1FF9:
            self.bank = a - 0x1FF8

    def intim(self):
        el = (self.cyc() - self.tim_base)
        v = self.tim_val - (el >> self.tim_shift)
        if v >= 0: return v & 0xFF
        # after underflow counts every cycle
        under = el - ((self.tim_val + 1) << self.tim_shift)
        return (0xFF - max(0, under)) & 0xFF

    def read(self, a):
        a &= 0x1FFF
        if a & 0x1000:
            off = self.bank * 4096 + (a & 0xFFF)
            self.hot(a)
            return self.rom[off]
        self.hot(a)
        if not (a & 0x80):           # TIA read
            r = a & 0x0F
            if r == 0x0C: return 0x00 if self.fire else 0x80   # INPT4
            if r == 0x0D: return 0x80
            if r in (0x08, 0x09, 0x0A, 0x0B): return 0x00
            return 0x00
        if not (a & 0x200):
            return self.ram[a & 0x7F]
        r = a & 0x07
        if a & 4:
            if r & 1: return 0  # TIMINT
            return self.intim()
        if r == 0: return self.swcha
        if r == 2: return self.swchb
        return 0

    def write(self, a, v):
        a &= 0x1FFF
        if a & 0x1000:
            self.hot(a); return
        self.hot(a)
        if not (a & 0x80):
            r = a & 0x3F
            self.tia_w[r] = v
            if r == 0x02:   # WSYNC
                c = self.cyc()
                self.mpu.processorCycles = ((c + 75) // 76) * 76 if c % 76 else c
                self.wsync_count += 1
            elif r == 0x00:
                on = bool(v & 2)
                if on and not self.vsync_on:
                    self.frame += 1
                    fl = (self.cyc() - getattr(self, 'fstart', 0)) // 76
                    self.frame_lines.append(fl)
                    self.fstart = self.cyc()
                self.vsync_on = on
            elif 0x15 <= r <= 0x1A and self.audlog is not None:
                self.audlog.append((self.frame, r, v))
            return
        if not (a & 0x200):
            self.ram[a & 0x7F] = v; return
        if a & 0x14 == 0x14:
            self.tim_shift = (0, 3, 6, 10)[a & 3]
            self.tim_val = v
            self.tim_base = self.cyc() + 1

    def step(self):
        pc = self.mpu.pc
        self.cov.add((self.bank, pc))
        self.mpu.step()

    def run_frames(self, n, hook=None, maxsteps=10**9):
        target = self.frame + n
        s = 0
        while self.frame < target and s < maxsteps:
            self.step(); s += 1
            if hook: hook(self)
        return s
