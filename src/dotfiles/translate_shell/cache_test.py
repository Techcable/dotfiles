import random
import tempfile
import time
from datetime import timedelta
from pathlib import Path
from typing import NoReturn

import pytest

from .cache import Cache, CachedValue, HashFunc, RehashFilesChanged, RehashSimple


def unreachable() -> NoReturn:
    raise AssertionError("Assumed unreachable")


def test_cache():
    return Cache.open("test", location=":memory:")


def defer(value, *, counter=None):
    assert counter is None or (isinstance(counter, list) and len(counter) == 1)

    def load():
        if counter is not None:
            counter[0] += 1
        return value

    return load


def test_cache_hit():
    cache = test_cache()
    val = cache.get_or_load(
        "bar",
        defer(
            CachedValue(
                value=49, check_frequency=timedelta(), rehash=RehashSimple.NEVER
            )
        ),
    )
    assert val == 49
    val2 = cache.get_or_load("bar", lambda: unreachable())
    assert val2 == val


@pytest.mark.parametrize("should_expire", [True, False])
def test_time_expiration(should_expire):
    cache = test_cache()
    count = [0]
    check_frequency = timedelta(microseconds=1) if should_expire else timedelta.max
    val = cache.get_or_load(
        "bar",
        defer(
            CachedValue(
                value=7 * 6, check_frequency=check_frequency, rehash=RehashSimple.ALWAYS
            ),
            counter=count,
        ),
    )
    assert timedelta.resolution <= timedelta(microseconds=1)
    assert val == 42
    assert count[0] == 1
    time.sleep(timedelta(microseconds=5).total_seconds())
    val2 = cache.get_or_load(
        "bar", defer(CachedValue(value=val, rehash=RehashSimple.ALWAYS), counter=count)
    )
    assert count[0] == (2 if should_expire else 1)
    assert val2 == val


@pytest.mark.parametrize("hash_func", [func for func in HashFunc if func.supported])
def test_hashfile_expiration(hash_func):
    assert isinstance(hash_func, HashFunc)
    cache = test_cache()
    with tempfile.TemporaryDirectory() as tmp:

        def randfile(name: str | Path, *, size=None) -> Path:
            if isinstance(name, str):
                p = Path(tmp) / name
            else:
                assert isinstance(name, Path)
                p = name
            if size is None:
                size = random.randint(1, 4096)
            with open(p, "wb") as f:
                f.write(random.randbytes(size))
            return p

        files = [
            randfile("zerosize.dat", size=0),
            randfile("bar.dat", size=32),
            *(randfile(f"foo{i}.dat") for i in range(1, 11)),
        ]
        hashes = {str(f): hash_func.hash_file(f) for f in files}
        counter = [0]
        val = cache.get_or_load(
            "bar",
            defer(
                CachedValue(
                    value="hello!",
                    check_frequency=timedelta(),
                    rehash=RehashFilesChanged(
                        hashes=hashes,
                        hash_func=hash_func,
                    ),
                ),
                counter=counter,
            ),
        )
        assert val == "hello!"
        assert counter[0] == 1
        files[2].touch(exist_ok=True)
        # Should hit
        val2 = cache.get_or_load("bar", lambda: unreachable())
        assert val2 == val
        # Edit a file
        randfile(files[1], size=12)
        val3 = cache.get_or_load(
            "bar",
            defer(
                CachedValue(
                    value=val,
                    check_frequency=timedelta.max,
                    rehash=RehashFilesChanged(hashes=hashes, hash_func=hash_func),
                ),
                counter=counter,
            ),
        )
        assert counter[0] == 2
        assert val3 == val2
