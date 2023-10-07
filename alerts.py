import numpy as np

from sound import *

def do_warnings(plane, AoA, G):
    if not get_channel_busy(7):
        warning = None
        
        if plane.pos[1] < 1000 and plane.vel[1] < 0:
            if plane.pos[1] / -plane.vel[1] < 3:
                warning = "pull_up"

        elif plane.pos[1] < 100 and -2 < plane.vel[1] < 0:
            warning = "dont_sink"

        elif G > 9:
            warning = "overg"

        elif np.linalg.norm(plane.vel) < 50 and AoA > 10:
            warning = "stall"

        if warning:
            play_sfx(warning, 0, 7, 1)

