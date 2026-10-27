import random


class MT19937:
    def __init__(self, seed: int):
        self._rng = random.Random(seed)

    def generate(self, n: int) -> list:
        return [self._rng.random() for _ in range(n)]
