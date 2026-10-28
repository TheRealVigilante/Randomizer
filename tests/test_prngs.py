"""
Tests for all 8 PRNG implementations.

Run with:
    conda run -n dawn python -m pytest tests/ -v

Each generator is tested for:
  1. Output range      — all values in [0, 1)
  2. Determinism       — same seed → same sequence (except ChaCha20)
  3. Seed independence — different seeds → different sequences
  4. Count             — generate(n) returns exactly n values
  5. Zero-seed safety  — seed=0 doesn't crash or lock up
  6. Large N           — generate(10_000) completes without error
  7. Uniqueness        — large run has no long run of identical values
  8. Algorithm-specific properties (where applicable)
"""

import math
import pytest
import sys
import os

# Make sure the project root is on the path when running from any CWD
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from prngs.lcg import LCG
from prngs.xorshift import Xorshift64
from prngs.mt19937 import MT19937
from prngs.pcg64 import PCG64Gen
from prngs.xoshiro256 import Xoshiro256
from prngs.splitmix64 import SplitMix64
from prngs.chacha20 import ChaCha20
from prngs.middle_square_weyl import MiddleSquareWeyl

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SEED = 42
N_SMALL = 100
N_LARGE = 10_000


def all_in_range(values: list) -> bool:
    """All values must be in [0, 1)."""
    return all(0.0 <= v < 1.0 for v in values)


def no_long_run(values: list, max_run: int = 20) -> bool:
    """Return True if no single value repeats more than max_run times in a row."""
    run = 1
    for i in range(1, len(values)):
        if values[i] == values[i - 1]:
            run += 1
            if run > max_run:
                return False
        else:
            run = 1
    return True


def mean_in_band(values: list, lo: float = 0.4, hi: float = 0.6) -> bool:
    """Mean of a large uniform sample should be near 0.5."""
    return lo <= sum(values) / len(values) <= hi


def passes_chi_square_uniform(values: list, bins: int = 10, significance: float = 0.001) -> bool:
    """
    Very lightweight chi-square uniformity test.
    Fails only for extremely non-uniform distributions.
    Not a substitute for BigCrush — just a sanity check.
    """
    counts = [0] * bins
    for v in values:
        idx = min(int(v * bins), bins - 1)
        counts[idx] += 1
    expected = len(values) / bins
    chi2 = sum((c - expected) ** 2 / expected for c in counts)
    # For bins-1=9 degrees of freedom, chi2 > 27.9 → p < 0.001
    return chi2 < 27.9


# ---------------------------------------------------------------------------
# Parametrize over all deterministic generators (ChaCha20 excluded)
# ---------------------------------------------------------------------------

DETERMINISTIC_GENERATORS = [
    ("LCG", LCG),
    ("Xorshift64", Xorshift64),
    ("MT19937", MT19937),
    ("PCG64", PCG64Gen),
    ("Xoshiro256", Xoshiro256),
    ("SplitMix64", SplitMix64),
    ("MiddleSquareWeyl", MiddleSquareWeyl),
]


@pytest.mark.parametrize("name,cls", DETERMINISTIC_GENERATORS)
class TestDeterministicGenerators:
    """Shared tests that every deterministic PRNG must pass."""

    def test_output_range(self, name, cls):
        """All outputs must be in [0, 1)."""
        rng = cls(SEED)
        values = rng.generate(N_SMALL)
        assert all_in_range(values), f"{name}: value(s) outside [0, 1)"

    def test_output_count(self, name, cls):
        """generate(n) must return exactly n values."""
        rng = cls(SEED)
        values = rng.generate(N_SMALL)
        assert len(values) == N_SMALL, f"{name}: expected {N_SMALL} values, got {len(values)}"

    def test_determinism(self, name, cls):
        """Same seed must produce the same sequence."""
        seq1 = cls(SEED).generate(N_SMALL)
        seq2 = cls(SEED).generate(N_SMALL)
        assert seq1 == seq2, f"{name}: same seed produced different sequences"

    def test_different_seeds_differ(self, name, cls):
        """Different seeds must produce different sequences."""
        seq1 = cls(SEED).generate(N_SMALL)
        seq2 = cls(SEED + 1).generate(N_SMALL)
        assert seq1 != seq2, f"{name}: different seeds produced identical sequences"

    def test_zero_seed(self, name, cls):
        """Seed=0 must not crash or degenerate to all-zeros."""
        rng = cls(0)
        values = rng.generate(N_SMALL)
        assert all_in_range(values), f"{name}: zero seed produced out-of-range values"
        # Should not be entirely zeros
        assert not all(v == 0.0 for v in values), f"{name}: zero seed locked to 0.0"

    def test_large_n(self, name, cls):
        """generate(10_000) must complete without error."""
        rng = cls(SEED)
        values = rng.generate(N_LARGE)
        assert len(values) == N_LARGE

    def test_no_long_constant_run(self, name, cls):
        """No value should repeat identically more than 20 times in a row."""
        rng = cls(SEED)
        values = rng.generate(N_LARGE)
        assert no_long_run(values), f"{name}: detected suspiciously long run of identical values"

    def test_mean_near_half(self, name, cls):
        """Mean of 10,000 samples should be within [0.4, 0.6]."""
        rng = cls(SEED)
        values = rng.generate(N_LARGE)
        assert mean_in_band(values), (
            f"{name}: mean {sum(values)/len(values):.4f} is far from 0.5"
        )

    def test_chi_square_uniformity(self, name, cls):
        """Chi-square uniformity sanity check across 10 bins."""
        rng = cls(SEED)
        values = rng.generate(N_LARGE)
        assert passes_chi_square_uniform(values), (
            f"{name}: chi-square test suggests non-uniform distribution"
        )

    def test_sequential_calls_advance_state(self, name, cls):
        """A second generate() call must continue from where the first left off."""
        rng = cls(SEED)
        first_10 = rng.generate(10)
        next_10 = rng.generate(10)
        assert first_10 != next_10, (
            f"{name}: second call returned same values as first — state not advancing"
        )

    def test_returns_list_of_floats(self, name, cls):
        """Output must be a list of Python floats (or float-compatible)."""
        rng = cls(SEED)
        values = rng.generate(10)
        assert isinstance(values, list), f"{name}: generate() did not return a list"
        for v in values:
            assert isinstance(v, (float, int)), (
                f"{name}: element {v!r} is not float/int"
            )


# ---------------------------------------------------------------------------
# Algorithm-specific tests
# ---------------------------------------------------------------------------

class TestLCG:
    """LCG-specific: known output values for the Numerical Recipes constants."""

    def test_known_first_value(self):
        """Verify the first step manually: state = (1664525*42 + 1013904223) % 2^32."""
        rng = LCG(42)
        expected_state = (1664525 * 42 + 1013904223) % (2 ** 32)
        expected = expected_state / (2 ** 32)
        result = rng.generate(1)[0]
        assert math.isclose(result, expected, rel_tol=1e-12), (
            f"LCG first value mismatch: got {result}, expected {expected}"
        )

    def test_state_wraps_at_32_bits(self):
        """State must never exceed 32-bit range."""
        rng = LCG(2 ** 32 - 1)  # max 32-bit seed
        values = rng.generate(N_SMALL)
        assert all_in_range(values)


class TestXorshift64:
    """Xorshift64: state must never be zero after init."""

    def test_zero_seed_remapped(self):
        """Seed=0 should be remapped to 1 so the generator doesn't lock."""
        rng = Xorshift64(0)
        assert rng.state != 0, "Xorshift64: zero state not corrected on init"

    def test_state_never_zero_during_run(self):
        """XOR-shift state must never reach zero (that would lock the sequence)."""
        rng = Xorshift64(SEED)
        # Access internal state via _next
        for _ in range(N_LARGE):
            rng._next()
            assert rng.state != 0, "Xorshift64: state reached zero during generation"


class TestMT19937:
    """MT19937: backed by Python's built-in random.Random — spot-check."""

    def test_matches_stdlib_random(self):
        """Our wrapper must produce the same values as random.Random(seed)."""
        import random
        ref = random.Random(SEED)
        our = MT19937(SEED)
        ref_vals = [ref.random() for _ in range(20)]
        our_vals = our.generate(20)
        assert ref_vals == our_vals, "MT19937 wrapper diverges from stdlib random.Random"


class TestPCG64:
    """PCG64: backed by numpy — spot-check against numpy directly."""

    def test_matches_numpy_pcg64(self):
        """Our wrapper must match numpy.random.Generator(PCG64(seed)).random()."""
        import numpy as np
        ref = np.random.Generator(np.random.PCG64(SEED))
        our = PCG64Gen(SEED)
        ref_vals = ref.random(20).tolist()
        our_vals = our.generate(20)
        assert ref_vals == our_vals, "PCG64Gen wrapper diverges from numpy PCG64"


class TestXoshiro256:
    """Xoshiro256**: state must be a 4-element list of 64-bit integers."""

    def test_initial_state_nonzero(self):
        """All four state words must be nonzero after seeding."""
        rng = Xoshiro256(SEED)
        assert all(w != 0 for w in rng.s), "Xoshiro256: one or more state words are zero after seeding"

    def test_state_mutates_each_step(self):
        """State must change after each call to _next()."""
        rng = Xoshiro256(SEED)
        before = list(rng.s)
        rng._next()
        after = list(rng.s)
        assert before != after, "Xoshiro256: state did not change after _next()"


class TestSplitMix64:
    """SplitMix64: counter-based — verify the Murmur-style mix is applied."""

    def test_known_step(self):
        """
        Manually compute one step with seed=0 and compare.
        state after step: (0 + 0x9e3779b97f4a7c15) & MASK
        """
        MASK = 0xFFFFFFFFFFFFFFFF
        rng = SplitMix64(0)
        # After __init__, state == 0. After first _next(), state == GOLDEN.
        GOLDEN = 0x9e3779b97f4a7c15
        z = GOLDEN
        z = ((z ^ (z >> 30)) * 0xbf58476d1ce4e5b9) & MASK
        z = ((z ^ (z >> 27)) * 0x94d049bb133111eb) & MASK
        expected = (z ^ (z >> 31)) / (2 ** 64)
        result = rng.generate(1)[0]
        assert math.isclose(result, expected, rel_tol=1e-12), (
            f"SplitMix64 step mismatch: got {result}, expected {expected}"
        )


class TestChaCha20:
    """ChaCha20 (CSPRNG): seed is ignored; output must still be valid and non-degenerate."""

    def test_output_range(self):
        rng = ChaCha20(SEED)
        values = rng.generate(N_SMALL)
        assert all_in_range(values), "ChaCha20: value(s) outside [0, 1)"

    def test_output_count(self):
        rng = ChaCha20(SEED)
        assert len(rng.generate(N_SMALL)) == N_SMALL

    def test_large_n(self):
        rng = ChaCha20(SEED)
        values = rng.generate(N_LARGE)
        assert len(values) == N_LARGE

    def test_not_deterministic(self):
        """Two runs with the same seed should (almost certainly) differ."""
        seq1 = ChaCha20(SEED).generate(50)
        seq2 = ChaCha20(SEED).generate(50)
        # The probability of collision is astronomically small
        assert seq1 != seq2, "ChaCha20: two independent runs produced identical output (extremely unlikely unless broken)"

    def test_ignores_seed_flag(self):
        """The IGNORES_SEED class attribute must be True."""
        assert ChaCha20.IGNORES_SEED is True

    def test_mean_near_half(self):
        rng = ChaCha20(SEED)
        values = rng.generate(N_LARGE)
        assert mean_in_band(values), (
            f"ChaCha20: mean {sum(values)/len(values):.4f} is far from 0.5"
        )

    def test_chi_square_uniformity(self):
        rng = ChaCha20(SEED)
        values = rng.generate(N_LARGE)
        assert passes_chi_square_uniform(values), (
            "ChaCha20: chi-square test suggests non-uniform distribution"
        )


class TestMiddleSquareWeyl:
    """Middle Square Weyl: the Weyl counter must increment every step."""

    def test_weyl_counter_advances(self):
        """w must increase by the Weyl constant each step."""
        rng = MiddleSquareWeyl(SEED)
        w_before = rng.w
        rng._next()
        w_after = rng.w
        delta = (w_after - w_before) & 0xFFFFFFFFFFFFFFFF
        assert delta == rng.s, (
            f"MiddleSquareWeyl: Weyl counter did not advance by s={rng.s:#x}"
        )

    def test_no_zero_lock(self):
        """With Weyl sequence, the generator must not degenerate to 0."""
        rng = MiddleSquareWeyl(0)  # worst case: seed=0
        values = rng.generate(200)
        nonzero = sum(1 for v in values if v > 0.0)
        assert nonzero > 150, (
            f"MiddleSquareWeyl: too many zero outputs with seed=0 ({200 - nonzero} zeros)"
        )
