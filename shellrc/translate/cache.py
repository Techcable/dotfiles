from __future__ import annotations

import copy
import hashlib
import logging
import re
from abc import ABCMeta, abstractmethod
from dataclasses import KW_ONLY, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, ClassVar, Generic, Optional, Self, TypeVar

HASH_FUNCTION_LENGTHS: dict[str, int] = {"sha256": 64, "blake3": 64}
VALID_HASH_FUNCS = frozenset(HASH_FUNCTION_LENGTHS.keys())
PREFERRED_HASH_FUNC: str
HASH_FUNCTION_IMPLS: dict[str, Callable[[], object]] = {"sha256": hashlib.sha256}
try:
    import blake3
except ImportError:
    PREFERRED_HASH_FUNC = "sha256"
else:
    PREFERRED_HASH_FUNC = "blake3"
    HASH_FUNCTION_IMPLS["blake3"] = blake3.blake3


class CacheException(Exception):
    cache_key: Optional[str]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.cache_key = None


class DeserializeError(CacheException):
    pass


class CacheInvalidateException(CacheException):
    pass


class RehashCondition(metaclass=ABCMeta):
    WHEN_ID: ClassVar[str]
    BY_CONDITION: ClassVar[dict[str, type[RehashCondition]]]

    @abstractmethod
    def serialize(self) -> dict:
        pass

    @classmethod
    @abstractmethod
    def _deserialize(cls, data: dict) -> Self:
        pass

    @staticmethod
    def deserialize(data: dict) -> RehashCondition:
        try:
            when = data["when"]
            rehash_condition_type = RehashCondition.BY_CONDITION[when]
        except KeyError:
            raise DeserializeError(
                f"Unknown rehash condition (when={data.get('when', '?')})"
            )
        return rehash_condition_type._deserialize(data)

    @abstractmethod
    def check(self, log: logging.Logger):
        pass


HEX_PATTERN = re.compile(r"[a-fA-F\d]*")


@dataclass
class RehashFilesChanged(RehashCondition):
    hashes: dict[Path, str]
    hash_func: str
    WHEN_ID: ClassVar[str] = "files_changed"

    def serialize(self) -> dict:
        return {
            "when": self.WHEN_ID,
            "hash_func": self.hash_func,
            "hashes": {str(p): val for p, val in self.hashes.items()},
        }

    @classmethod
    def _deserialize(cls, data: dict) -> Self:
        try:
            if (actual_when := data["when"]) != RehashFilesChanged.WHEN_ID:
                raise DeserializeError(
                    f"Unexpected `when` for condition: {actual_when}"
                )
            hash_func_name = data["hash_func"]
            if hash_func_name not in VALID_HASH_FUNCS:
                raise DeserializeError(f"Unknown hash function: {hash_func_name}")
            expected_hash_len = HASH_FUNCTION_LENGTHS[hash_func_name]
            raw_hashes = data["hashes"]
            hashes = {}
            for path, value in raw_hashes.items():
                assert isinstance(path, str)  # Known to be string because json
                if not HEX_PATTERN.fullmatch(value) or len(value) != 64:
                    raise DeserializeError(f"Unexpected hash value: {value!r}")
                hashes[Path(path)] = value
            return RehashFilesChanged(hashes=hashes, hash_func=PREFERRED_HASH_FUNC)
        except KeyError:
            raise DeserializeError

    def check(self, log: logging.Logger):
        for p, expected_hash in self.hashes.items():
            with open(p, "rb") as f:
                try:
                    hasher_func = HASH_FUNCTION_IMPLS[self.hash_func]
                except KeyError:
                    raise CacheInvalidateException(
                        f"Missing required hash function {self.hash_func!r}"
                    )
                # read bytes
                hasher: Any = hasher_func()
                while b := f.read(4096):
                    hasher.update(b)
                actual_hash = hasher.hexdigest()
                if actual_hash != expected_hash:
                    raise CacheInvalidateException(
                        f"Hash changed for file {p}: {expected_hash} => {actual_hash}"
                    )
                else:
                    log.debug("File %s has same hash: %s", p, expected_hash)
        # success
        log.debug("Successfully checked %s files", len(self.hashes))


class RehashAlways(RehashCondition):
    WHEN_ID: ClassVar[str] = "always"

    def serialize(self) -> dict:
        return {"when": self.WHEN_ID}

    def _deserialize(cls, data: dict) -> RehashAlways:
        try:
            if (actual_when := data["when"]) != cls.WHEN_ID:
                raise DeserializeError(
                    f"Unexpected `when` for condition: {actual_when}"
                )
        except KeyError:
            raise DeserializeError
        else:
            return RehashAlways()

    def check(self, log: logging.Logger):
        raise CacheInvalidateException(
            "Using `RehashAlways` unconditionally invalidates."
        )


class RehashNever(RehashCondition):
    WHEN_ID: ClassVar[str] = "never"

    def serialize(self) -> dict:
        return {"when": self.WHEN_ID}

    def _deserialize(cls, data: dict) -> RehashNever:
        try:
            if (actual_when := data["when"]) != cls.WHEN_ID:
                raise DeserializeError(
                    f"Unexpected `when` for condition: {actual_when}"
                )
        except KeyError:
            raise DeserializeError
        else:
            return RehashNever()

    def check(self, log: logging.Logger):
        log.debug("NOTE: Using `RehashNever` never invalidates.")


TIMEDELTA_PATTERN = re.compile(r"(?:(\d+) days?, )?(\d?\d):(\d\d):(\d\d)(\.\d+)?")


def parse_timedelta(text: str) -> timedelta:
    match = TIMEDELTA_PATTERN.fullmatch(text)
    if match is None:
        raise ValueError(f"Invalid timedelta: {text!r}")
    days, hours, minutes, seconds, micros = map(int, match.groups("0"))
    return timedelta(
        days=days, hours=hours, minutes=minutes, seconds=seconds, microseconds=micros
    )


T = TypeVar("T")
DEFAULT_CHECK_FREQUENCY = timedelta(minutes=15)


@dataclass(frozen=True)
class CachedValue(Generic[T]):
    raw_value: T
    _: KW_ONLY
    last_checked: Optional[datetime] = field(default_factory=datetime.now)
    check_frequency: timedelta = field(default=DEFAULT_CHECK_FREQUENCY)
    rehash: RehashCondition = field(default_factory=RehashAlways)

    def serialize(self) -> dict:
        return {
            "value": self.raw_value,
            "rehash": self.rehash.serialize(),
            "last_checked": self.last_checked.isoformat(),
            "check_frequency": str(self.check_frequency),
        }

    @staticmethod
    def deserialize(data: dict) -> CachedValue:
        try:
            return CachedValue(
                raw_value=data["value"],
                last_checked=datetime.fromisoformat(data.get("last_checked")),
                check_frequency=parse_timedelta(
                    data.get("check_frequency", DEFAULT_CHECK_FREQUENCY)
                ),
                rehash=RehashCondition.deserialize(data["rehash"]),
            )
        except (KeyError, ValueError):
            raise DeserializeError

    def is_time_expired(self) -> bool:
        """Check if the time has expired"""
        if self.last_checked is None:
            # don't know about last time checked => time to check again
            return True
        time_elapsed = datetime.now() - self.last_checked
        return time_elapsed >= self.check_frequency or time_elapsed < timedelta()

    def check_validity(self, log: logging.Logger, *, only_if_time_expired=True):
        """
        Check if the cached value still valid.

        Implicitly ignores the request if the time is not expired.

        Throws CacheInvalidateException if the cache is invalid
        """
        if only_if_time_expired and not self.is_time_expired():
            return
        self.rehash.check(log)


class Cache:
    name: str
    _data: dict[str, CachedValue]
    dirty: bool

    LOGGER: ClassVar[logging.Logger] = logging.getLogger("cache")

    def __init__(self, name: str, data: dict[str, CachedValue]):
        self.name = name
        self._data = data
        self.dirty = False

    def get_or_load(self, key: str, fallback: Callable[[], CachedValue[T]]) -> T:
        try:
            existing_value = self._data[key]
        except KeyError:
            existing_value = None
        logger = Cache.LOGGER
        if existing_value is not None:
            try:
                existing_value.check_validity(logger)
            except CacheInvalidateException as e:
                logger.info("Invalidating %s: %s", key, e)
                self.dirty = True
                del self._data[key]
            else:
                return existing_value.raw_value
        logger.info("Loading value for %s", key)
        updated_value = fallback()
        self.dirty = True
        self._data[key] = updated_value
        return updated_value.raw_value

    @staticmethod
    def location_of(name: str) -> Path:
        if not name.isalnum() or not name.isascii():
            raise ValueError(f"Invalid name: {name!r}")
        return Path.home() / f".cache/techcable/dotfiles/{name}.json"

    @staticmethod
    def load(name: str, *, allow_missing=True):
        location = Cache.location_of(name)
        try:
            with open(location, "rt") as f:
                raise NotImplementedError
        except FileNotFoundError:
            if not allow_missing:
                raise
            return Cache(
                name=name,
                data={},
            )

    def save(self):
        raise NotImplementedError
