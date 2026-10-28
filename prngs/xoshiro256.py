class Xoshiro256:
    def __init__(self, seed: int):
        # Initialize 4x64-bit state from seed using SplitMix64 splitter
        def splitmix(s):
            s = (s + 0x9e3779b97f4a7c15) & 0xFFFFFFFFFFFFFFFF
            s = ((s ^ (s >> 30)) * 0xbf58476d1ce4e5b9) & 0xFFFFFFFFFFFFFFFF
            s = ((s ^ (s >> 27)) * 0x94d049bb133111eb) & 0xFFFFFFFFFFFFFFFF
            return s ^ (s >> 31)

        s = seed & 0xFFFFFFFFFFFFFFFF
        self.s = [0] * 4
        for i in range(4):
            s = splitmix(s)
            self.s[i] = s

    def _rotl(self, x, k):
        return ((x << k) | (x >> (64 - k))) & 0xFFFFFFFFFFFFFFFF

    def _next(self) -> int:
        s = self.s
        result = (self._rotl((s[1] * 5) & 0xFFFFFFFFFFFFFFFF, 7) * 9) & 0xFFFFFFFFFFFFFFFF
        t = (s[1] << 17) & 0xFFFFFFFFFFFFFFFF
        s[2] ^= s[0]
        s[3] ^= s[1]
        s[1] ^= s[2]
        s[0] ^= s[3]
        s[2] ^= t
        s[3] = self._rotl(s[3], 45)
        return result

    def generate(self, n: int) -> list:
        return [self._next() / (2**64) for _ in range(n)]
