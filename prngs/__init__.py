from .lcg import LCG
from .xorshift import Xorshift64
from .mt19937 import MT19937
from .pcg64 import PCG64Gen
from .xoshiro256 import Xoshiro256
from .splitmix64 import SplitMix64
from .chacha20 import ChaCha20
from .middle_square_weyl import MiddleSquareWeyl

REGISTRY = {
    "LCG (Linear Congruential)": LCG,
    "Xorshift64": Xorshift64,
    "MT19937 (Mersenne Twister)": MT19937,
    "PCG64": PCG64Gen,
    "Xoshiro256**": Xoshiro256,
    "SplitMix64": SplitMix64,
    "ChaCha20 (CSPRNG)": ChaCha20,
    "Middle Square Weyl": MiddleSquareWeyl,
}

METADATA = {
    "LCG (Linear Congruential)": {
        "period": "2^32",
        "state_size": "32 bits",
        "speed": "Fast",
        "csprng": False,
    },
    "Xorshift64": {
        "period": "2^64 - 1",
        "state_size": "64 bits",
        "speed": "Fast",
        "csprng": False,
    },
    "MT19937 (Mersenne Twister)": {
        "period": "2^19937 - 1",
        "state_size": "2496 bytes",
        "speed": "Medium",
        "csprng": False,
    },
    "PCG64": {
        "period": "2^128",
        "state_size": "128 bits",
        "speed": "Fast",
        "csprng": False,
    },
    "Xoshiro256**": {
        "period": "2^256 - 1",
        "state_size": "256 bits",
        "speed": "Fast",
        "csprng": False,
    },
    "SplitMix64": {
        "period": "2^64",
        "state_size": "64 bits",
        "speed": "Fast",
        "csprng": False,
    },
    "ChaCha20 (CSPRNG)": {
        "period": "2^70 blocks",
        "state_size": "512 bits",
        "speed": "Medium",
        "csprng": True,
    },
    "Middle Square Weyl": {
        "period": "2^64",
        "state_size": "128 bits",
        "speed": "Fast",
        "csprng": False,
    },
}
