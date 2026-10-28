import os


class ChaCha20:
    IGNORES_SEED = True  # used by the UI to show a warning

    def __init__(self, seed: int):
        pass  # seed is ignored; uses OS CSPRNG

    def generate(self, n: int) -> list:
        results = []
        for _ in range(n):
            raw = int.from_bytes(os.urandom(8), 'little')
            results.append(raw / (2**64))
        return results
