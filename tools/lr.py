# Minimal libretro frontend for the Stella core (headless): run frames,
# grab RGB frames, RAM, audio, set joystick/switches.
import ctypes as C, os
CORE = os.path.join(os.path.dirname(__file__), 'stella/src/os/libretro/stella_libretro.so')

class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]
class GameGeom(C.Structure):
    _fields_ = [('bw', C.c_uint), ('bh', C.c_uint), ('mw', C.c_uint), ('mh', C.c_uint), ('ar', C.c_float)]
class Timing(C.Structure):
    _fields_ = [('fps', C.c_double), ('rate', C.c_double)]
class AV(C.Structure):
    _fields_ = [('geom', GameGeom), ('timing', Timing)]
class Var(C.Structure):
    _fields_ = [('key', C.c_char_p), ('value', C.c_char_p)]

ENV = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VID = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUD = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUDB = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL = C.CFUNCTYPE(None)
STATE = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)

# joypad ids
B, Y, SELECT, START, UP, DOWN, LEFT, RIGHT, A, X, L, R, L2, R2, L3, R3 = range(16)

class Stella:
    def __init__(self, rom, opts=None):
        self.lib = C.CDLL(CORE)
        self.opts = {b'stella_console': b'auto', b'stella_palette': b'standard'}
        if opts: self.opts.update(opts)
        self.keep = []
        self.pressed = set()
        self.frame = None; self.w = self.h = 0; self.audio_n = 0; self.audio = []
        self.sysdir = C.c_char_p(b'/tmp')
        def env(cmd, data):
            cmd &= 0xFFFF
            if cmd == 10:   # SET_PIXEL_FORMAT
                return True
            if cmd in (9, 31):  # GET_SYSTEM_DIRECTORY / SAVE_DIRECTORY
                C.cast(data, C.POINTER(C.c_char_p))[0] = self.sysdir.value; return True
            if cmd == 15:   # GET_VARIABLE
                v = C.cast(data, C.POINTER(Var))[0]
                val = self.opts.get(v.key)
                if val is None: return False
                C.cast(data, C.POINTER(Var))[0].value = val; return True
            if cmd == 17: C.cast(data, C.POINTER(C.c_bool))[0] = False; return True
            return False
        def vid(data, w, h, pitch):
            if data:
                self.w, self.h = w, h
                buf = (C.c_uint8 * (pitch * h)).from_address(data)
                self.frame = (bytes(buf), w, h, pitch)
        def aud(l, r): pass
        def audb(data, frames):
            self.audio_n += frames
            if self.keep_audio:
                self.audio.append(bytes((C.c_int16 * (frames * 2)).from_address(data)))
            return frames
        def poll(): pass
        def state(port, dev, idx, id_):
            return 1 if (port == 0 and id_ in self.pressed) else 0
        self.keep_audio = False
        self.cbs = [ENV(env), VID(vid), AUD(aud), AUDB(audb), POLL(poll), STATE(state)]
        L = self.lib
        L.retro_set_environment(self.cbs[0]); L.retro_set_video_refresh(self.cbs[1])
        L.retro_set_audio_sample(self.cbs[2]); L.retro_set_audio_sample_batch(self.cbs[3])
        L.retro_set_input_poll(self.cbs[4]); L.retro_set_input_state(self.cbs[5])
        L.retro_init()
        self.data = open(rom, 'rb').read()
        self.buf = C.create_string_buffer(self.data, len(self.data))
        gi = GameInfo(rom.encode(), C.cast(self.buf, C.c_void_p), len(self.data), None)
        assert L.retro_load_game(C.byref(gi)), 'load failed'
        L.retro_get_memory_data.restype = C.c_void_p
        L.retro_get_memory_size.restype = C.c_size_t
    def av(self):
        a = AV(); self.lib.retro_get_system_av_info(C.byref(a)); return a
    def run(self, n=1, keys=()):
        self.pressed = set(keys)
        for _ in range(n): self.lib.retro_run()
    def ram(self):
        p = self.lib.retro_get_memory_data(2); n = self.lib.retro_get_memory_size(2)
        return bytes((C.c_uint8 * n).from_address(p)) if p else b''
    def poke(self, addr, v):
        p = self.lib.retro_get_memory_data(2)
        (C.c_uint8 * 128).from_address(p)[addr & 0x7F] = v
    def image(self):
        from PIL import Image
        data, w, h, pitch = self.frame
        im = Image.frombuffer('RGBA', (pitch // 4, h), data, 'raw', 'BGRA', 0, 1)
        return im.crop((0, 0, w, h)).convert('RGB')
