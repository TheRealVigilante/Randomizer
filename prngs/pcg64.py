import numpy as np


class PCG64Gen:
    def __init__(self, seed: int):
        self._rng = np.random.Generator(np.random.PCG64(seed))

    def generate(self, n: int) -> list:
        return self._rng.random(n).tolist()
