class MiddleSquareWeyl:
    def __init__(self, seed: int):
        # x is the middle-square state, w is the Weyl sequence counter
        self.x = seed & 0xFFFFFFFFFFFFFFFF
        self.w = seed & 0xFFFFFFFFFFFFFFFF
        # Weyl constant (odd, large): commonly recommended value
        self.s = 0xb5ad4eceda1ce2a9

    def _next(self) -> int:
        self.w = (self.w + self.s) & 0xFFFFFFFFFFFFFFFF
        self.x = (self.x * self.x + self.w) & 0xFFFFFFFFFFFFFFFF
        # middle-square: rotate right by 32 bits
        self.x = ((self.x >> 32) | (self.x << 32)) & 0xFFFFFFFFFFFFFFFF
        return self.x

    def generate(self, n: int) -> list:
        return [self._next() / (2**64) for _ in range(n)]
