"""Experimental physical-constant-based 256-bit hash.

Research prototype; cryptographic security is not established.
Usage as a module:  from experimental_hash import experimental_hash
Usage as a script:  python experimental_hash.py
"""
import math

MASK = 0xFFFFFFFF

# (name, numerator, decimal_places, exponent10)
CONSTANTS = [
    ("Gravitational constant G",      667430,        5, -11),
    ("Planck constant h",             662607015,     8, -34),
    ("Reduced Planck constant hbar",  1054571817,    9, -34),
    ("Boltzmann constant kB",         1380649,       6, -23),
    ("Elementary charge e",           1602176634,    9, -19),
    ("Fine-structure constant alpha", 729735256,     8,  -3),
    ("Vacuum permittivity epsilon0",  88541878188,  10, -12),
    ("Vacuum permeability mu0",       125663706127, 11,  -6),
]


def generate_initial_word(numerator, decimal_places):
    # floor(frac(sqrt(N)) * 2^32), N = numerator / 10^places, exact integer math
    scaled = (numerator << 64) // (10 ** decimal_places)
    return math.isqrt(scaled) & MASK


def generate_initial_state():
    return [generate_initial_word(c[1], c[2]) for c in CONSTANTS]


def rotr32(x, r):
    r &= 31
    if r == 0:
        return x & MASK
    return ((x >> r) | (x << (32 - r))) & MASK


def round_constant(initial, rnd):
    x = initial[rnd % 8]
    y = initial[(rnd + 3) % 8]
    rotation = (rnd % 31) + 1
    return (x + rotr32(y, rotation) + (0x9E3779B9 * (rnd + 1))) & MASK


def round_multiplier(initial, rnd):
    return initial[(rnd + 5) % 8] | 1


def experimental_round(state, initial, message_word, rnd):
    a, b, c, d, e, f, g, h = state

    u = (a + message_word + round_constant(initial, rnd)) & MASK
    v = u ^ rotr32(c, 11)
    x = (v + rotr32(e, 17)) & MASK

    choice = (b & d) ^ ((~b & MASK) & f)
    y = choice ^ (d & rotr32(f, 7))

    z = (x + y) & MASK
    rotation = (rnd % 31) + 1

    q = rotr32(z, rotation) ^ rotr32(g, 13) ^ rotr32(h, 19)
    t = (q * round_multiplier(initial, rnd)) & MASK

    return [
        (t + rotr32(y, 3)) & MASK,
        a,
        b ^ rotr32(t, 5),
        c,
        (d + rotr32(x, 9)) & MASK,
        e ^ rotr32(y, 13),
        f,
        (g + rotr32(t, 17)) & MASK,
    ]


def expand_message(block):
    w = [0] * 64
    for i in range(16):
        j = i * 4
        w[i] = (block[j] << 24) | (block[j + 1] << 16) | (block[j + 2] << 8) | block[j + 3]
    for i in range(16, 64):
        x = w[i - 7]
        y = w[i - 2]
        sigma1 = rotr32(x, 7) ^ rotr32(x, 18) ^ (x >> 3)
        sigma2 = rotr32(y, 17) ^ rotr32(y, 19) ^ (y >> 10)
        w[i] = (w[i - 16] + sigma1 + w[i - 1] + sigma2) & MASK
    return w


def compress_block(hash_state, initial, block):
    words = expand_message(block)
    working = list(hash_state)
    for rnd in range(64):
        working = experimental_round(working, initial, words[rnd], rnd)
    for i in range(8):
        hash_state[i] = (hash_state[i] + working[i]) & MASK


def experimental_hash(message):
    """Return the 32-byte digest of a str (UTF-8 encoded) or bytes."""
    initial = generate_initial_state()
    state = list(initial)

    data = bytearray(message.encode("utf-8") if isinstance(message, str) else message)
    bit_length = len(data) * 8

    data.append(0x80)
    while len(data) % 64 != 56:
        data.append(0x00)
    data += (bit_length & 0xFFFFFFFFFFFFFFFF).to_bytes(8, "big")

    for offset in range(0, len(data), 64):
        compress_block(state, initial, data[offset:offset + 64])

    return b"".join(s.to_bytes(4, "big") for s in state)


def hexdigest(message):
    return experimental_hash(message).hex().upper()


def main():
    print("Experimental Physical-Constant Hash")
    print("====================================\n")
    print("Initial state:")
    for i, v in enumerate(generate_initial_state()):
        print(f"H{i} = 0x{v:08X}")
    message = input("\nEnter a message: ")
    print(f"\nMessage: {message}")
    print("Digest (256 bits):")
    print(hexdigest(message))


if __name__ == "__main__":
    main()
