class SplitMix64:
    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFFFFFFFFFF

    def _next(self) -> int:
        self.state = (self.state + 0x9e3779b97f4a7c15) & 0xFFFFFFFFFFFFFFFF
        z = self.state
        z = ((z ^ (z >> 30)) * 0xbf58476d1ce4e5b9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94d049bb133111eb) & 0xFFFFFFFFFFFFFFFF
        return z ^ (z >> 31)

    def generate(self, n: int) -> list:
        return [self._next() / (2**64) for _ in range(n)]
