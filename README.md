# 🎲 PRNG Explorer

A Streamlit app for exploring, comparing, and generating random numbers using 8 different pseudo-random number generation algorithms. Pick a single algorithm or mix several together via XOR-combination, inspect the distribution, or generate values mapped to any numeric range.

---

## Getting Started

```bash
conda activate dawn
cd path/to/Randomizer
streamlit run app.py
```

---

## The 8 Algorithms

### 1. LCG — Linear Congruential Generator
The oldest and most widely deployed PRNG family, dating back to 1948. Produces the next value with a single formula:

```
x = (a × x + c) mod m
```

This implementation uses the **Numerical Recipes** constants (`a = 1664525`, `c = 1013904223`, `m = 2³²`), the same ones used in many C standard library `rand()` implementations. It is extremely fast and uses only 32 bits of state, but low-order bits cycle with short periods and it fails modern statistical test suites in higher dimensions. Best for situations where raw speed matters more than quality.

- **Period:** 2³²
- **State:** 32 bits
- **CSPRNG:** No

---

### 2. Xorshift64
A minimal generator from George Marsaglia (2003) that uses only XOR and bit-shift operations on a 64-bit integer. The state advances via three shifts:

```
x ^= x << 13
x ^= x >> 7
x ^= x << 17
```

It is one of the fastest generators possible and fits in a single CPU register. The tradeoff is a detectable linear structure — statistical test suites catch the correlation in high dimensions. A zero state would lock the generator permanently, so a seed of 0 is automatically remapped to 1.

- **Period:** 2⁶⁴ − 1
- **State:** 64 bits
- **CSPRNG:** No

---

### 3. MT19937 — Mersenne Twister
The dominant PRNG of the 1990s–2010s, still the default in Python's `random` module and R. Named after its period of 2¹⁹⁹³⁷ − 1 (a Mersenne prime). It achieves 623-dimensional equidistribution, meaning that every possible 623-tuple of 32-bit values appears equally often across the full period.

The implementation here is a thin wrapper around Python's built-in `random.Random`, so its output is identical to `random.random()` for the same seed. Despite its reputation, MT19937 fails the BigCrush birthday spacings test and has a known weakness with sparse seeds (many zeros) that produces poor output for thousands of initial values.

- **Period:** 2¹⁹⁹³⁷ − 1
- **State:** 2,496 bytes (624 × 32-bit words)
- **CSPRNG:** No

---

### 4. PCG64 — Permuted Congruential Generator
Designed by Melissa O'Neill in 2014, PCG applies a non-linear output permutation (a bit rotation keyed on the high bits) on top of a 128-bit LCG. This eliminates the LCG's low-bit weaknesses while keeping the speed and mathematical tractability of the underlying recurrence.

PCG64 passes all known statistical test suites including BigCrush, supports 2⁶³ independent streams, and allows O(1) advance to any position in the sequence. It has been the default generator in NumPy since v1.17. The implementation here wraps `numpy.random.PCG64` directly.

- **Period:** 2¹²⁸
- **State:** 128 bits
- **CSPRNG:** No

---

### 5. Xoshiro256\*\*
The current state-of-the-art for general-purpose non-cryptographic generation, designed by David Blackman and Sebastiano Vigna (2018). Operates on 256 bits of state split into four 64-bit words, using XOR, shifts, and rotations. The `**` (double-star) scrambler multiplies the output twice to eliminate any remaining low-bit weaknesses.

The four state words are seeded using a SplitMix64 splitter to guarantee a well-distributed starting state from any single integer seed. It supports efficient jump-ahead by 2¹²⁸ steps in O(1), making it trivially parallelizable. Passes all known statistical tests.

- **Period:** 2²⁵⁶ − 1
- **State:** 256 bits (4 × 64-bit words)
- **CSPRNG:** No

---

### 6. SplitMix64
A hash-counter design from Steele et al. (2014), used as Java's `SplittableRandom`. Increments a 64-bit counter by the golden-ratio-derived constant `0x9e3779b97f4a7c15` (the Weyl sequence step), then applies a Murmur-style finalizer mix to produce the output.

It uses the smallest possible state (one 64-bit integer), is among the fastest generators available, and is primarily used in two roles: seeding larger generators from a single integer (e.g. initializing Xoshiro256's four state words), and as a splittable generator for parallel workloads.

- **Period:** 2⁶⁴
- **State:** 64 bits
- **CSPRNG:** No

---

### 7. ChaCha20 — CSPRNG
A cryptographically secure pseudo-random number generator based on Daniel Bernstein's ChaCha20 stream cipher (2008). Unlike the other generators, it is backed by the operating system's entropy source (`os.urandom`) rather than a deterministic recurrence, making it suitable for security-sensitive applications.

Because it draws from OS entropy, **the seed input is ignored** — the app shows a warning when ChaCha20 is selected. Each call to `os.urandom(8)` returns 8 bytes from the system CSPRNG (Linux uses ChaCha20 in `getrandom()`, Windows uses BCrypt). It passes all statistical tests and has no known cryptographic weaknesses.

- **Period:** Effectively unlimited (OS-managed entropy)
- **State:** 512 bits (OS-managed)
- **CSPRNG:** ✅ Yes

---

### 8. Middle Square Weyl
A modernized take on John von Neumann's original 1946 Middle Square method, fixed by a Weyl sequence addition. The classic middle-square algorithm squares the current value and extracts the middle digits — but it degenerates to zero eventually. The Weyl fix adds an odd constant `s` to an accumulator `w` on every step:

```
w = (w + s) mod 2⁶⁴
x = (x² + w) mod 2⁶⁴
x = rotate_right(x, 32)
```

The Weyl sequence guarantees the accumulator visits every 64-bit value exactly once per period, preventing the zero-lock of the original algorithm. It produces good statistical quality for its simplicity and has historical significance as the algorithm that started computational randomness.

- **Period:** 2⁶⁴
- **State:** 128 bits (x + w)
- **CSPRNG:** No

---

## Mixing Algorithms

When more than one algorithm is selected, the app combines their outputs using **XOR mixing**:

1. Each generator independently produces `n` floats in `[0, 1)` from the same seed
2. Each float is scaled to a 32-bit integer (`int(v × 2³²)`)
3. Corresponding integers across all generators are XOR-ed element-wise
4. The result is divided by 2³² to produce the final float in `[0, 1)`

XOR-mixing is a standard technique for combining independent entropy sources — it cannot make the output weaker than the strongest individual generator.

---

## App Tabs

### 📊 Distribution Explorer

The main analysis tab. Configure everything from the sidebar:

- **Algorithms** — multiselect any combination of the 8 generators
- **Seed** — integer seed for reproducible sequences (ignored by ChaCha20)
- **N values** — slider from 10 to 10,000

The tab shows:
- **Algorithm info cards** — period, state size, speed class, and CSPRNG status for each selected algorithm
- **Generated values table** — first 20 rows displayed, full dataset downloadable as CSV
- **Distribution histogram** — 50-bin Plotly histogram of the output
- **Mix details expander** — when multiple algorithms are selected, explains the XOR-mixing method and lists each algorithm's properties

---

### 🎯 Range Picker

A focused tab for generating random values in a specific numeric range — useful when you need a random integer between 1 and 100, or a random float between two bounds.

**Controls (independent from the sidebar):**

- **Range** — set Low and High bounds; toggle between integer and float mode
- **Algorithms** — multiselect; if more than one is chosen, outputs are XOR-mixed before range mapping
- **Seed** — independent seed for this tab
- **Count** — how many values to generate (1 to 10,000)

**Output:**

- **Count = 1** → large centered display card showing the single value, plus a metric widget
- **Count > 1** → table (first 20 rows), statistics panel (min, max, mean, std dev), histogram, and CSV download

Integer mode maps to `[low, high]` inclusive. Float mode maps to `[low, high)`.

---

## Project Structure

```
Randomizer/
├── app.py                   # Streamlit app
├── requirements.txt         # Python dependencies
├── prngs/
│   ├── __init__.py          # Registry and metadata for all 8 generators
│   ├── lcg.py               # Linear Congruential Generator
│   ├── xorshift.py          # Xorshift64
│   ├── mt19937.py           # Mersenne Twister (wraps Python stdlib)
│   ├── pcg64.py             # PCG64 (wraps NumPy)
│   ├── xoshiro256.py        # Xoshiro256**
│   ├── splitmix64.py        # SplitMix64
│   ├── chacha20.py          # ChaCha20 via os.urandom
│   └── middle_square_weyl.py# Middle Square Weyl
└── tests/
    └── test_prngs.py        # 95 pytest tests covering all 8 generators
```

## Running Tests

```bash
conda activate dawn
cd path/to/Randomizer
python -m pytest tests/ -v
```
