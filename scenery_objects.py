import random

from model import *

class SceneryObject:
    def __init__(self, model, pos):
        self.model = model
        self.pos = pos

class RandomBuilding(SceneryObject):
    def __init__(self, pos):
        self.pos = pos
        self.model = Model("cube")
        rand_height = random.uniform(5, 70)
        rand_width = random.uniform(0.3, 0.7) * rand_height
        rand_depth = random.uniform(0.3, 0.7) * rand_height
        for idx_v, v in enumerate(self.model.vertices):
            self.model.vertices[idx_v] = np.array([self.model.vertices[idx_v][0] * rand_width,
                                                   self.model.vertices[idx_v][1] * rand_height,
                                                   self.model.vertices[idx_v][2] * rand_depth])
