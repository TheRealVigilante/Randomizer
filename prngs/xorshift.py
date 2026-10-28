class Xorshift64:
    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFFFFFFFFFF
        if self.state == 0:
            self.state = 1  # xorshift must not have zero state

    def _next(self) -> int:
        x = self.state
        x ^= (x << 13) & 0xFFFFFFFFFFFFFFFF
        x ^= (x >> 7)
        x ^= (x << 17) & 0xFFFFFFFFFFFFFFFF
        self.state = x & 0xFFFFFFFFFFFFFFFF
        return self.state

    def generate(self, n: int) -> list:
        return [self._next() / (2**64) for _ in range(n)]
