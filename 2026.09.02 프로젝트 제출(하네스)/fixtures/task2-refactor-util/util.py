import math


def slugify(text, sep="-"):
    out = []
    prev_sep = False
    for ch in text.strip().lower():
        if ch.isalnum():
            out.append(ch)
            prev_sep = False
        elif not prev_sep:
            out.append(sep)
            prev_sep = True
    return "".join(out).strip(sep)


def chunk(items, size):
    if size < 1:
        raise ValueError("size must be >= 1")
    return [items[i:i + size] for i in range(0, len(items), size)]


def retry_delays(base, attempts, cap=None):
    delays = []
    for n in range(attempts):
        d = base * math.pow(2, n)
        if cap is not None:
            d = min(d, cap)
        delays.append(d)
    return delays
