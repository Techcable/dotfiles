from math import log2, floor

# Note: Uses powers of two
#
# This appears to be official: https://physics.nist.gov/cuu/Units/binary.html
_SIZE_POWER_SUFFIXES= {
    0: 'B',
    1: 'KiB',
    2: 'MiB',
    3: 'Gib',
    4: 'Tib',
}
def format_size(size):
    """Nicely format the specified size in bytes (like 3.33 MiB)"""
    power = int(floor(log2(size))) // 10
    sufix = _SIZE_POWER_SUFFIXES[power]
    return f"{size/(1024**power):.2f} {sufix}"


__all__ = [
    "format_size"
]

