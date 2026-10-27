class LCG:
    # Numerical Recipes constants
    A = 1664525
    C = 1013904223
    M = 2**32

    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFF

    def generate(self, n: int) -> list:
        results = []
        for _ in range(n):
            self.state = (self.A * self.state + self.C) % self.M
            results.append(self.state / self.M)
        return results
