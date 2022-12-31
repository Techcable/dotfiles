from __future__ import annotations

import functools
import hashlib
import logging
import pickle
import re
import sqlite3
from abc import ABCMeta, abstractmethod
from dataclasses import KW_ONLY, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Generic,
    Iterable,
    Optional,
    TypeVar,
)

if TYPE_CHECKING:
    from os import PathLike

    from typing_extensions import Self


try:
    import blake3
except ImportError:
    blake3 = None


class HashFunc(Enum):
    SHA256 = "sha256"
    BLAKE3 = "blake3"

    @property
    def digest_length(self) -> int:
        return 64

    @functools.cached_property
    def supported(self) -> bool:
        try:
            return self.create_impl()
        except NotImplementedError:
            return False

    def create_impl(self) -> Any:
        match self:
            case HashFunc.SHA256:
                return hashlib.sha256()
            case HashFunc.BLAKE3:
                if blake3 is not None:
                    return blake3.blake3()
                else:
                    raise NotImplementedError("Missing blake3 impl")
            case _:
                raise AssertionError

    def hash_file(self, p: PathLike) -> str:
        with open(p, "rb") as f:
            # read bytes
            hasher = self.create_impl()
            while b := f.read(4096):
                hasher.update(b)
            return hasher.hexdigest()

    def __str__(self):
        return self.value

    PREFERRED: ClassVar[HashFunc]


HashFunc.PREFERRED = HashFunc.BLAKE3 if HashFunc.BLAKE3.supported else HashFunc.SHA256


class CacheException(Exception):
    cache_key: Optional[str]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.cache_key = None


class CacheLoadError(CacheException):
    pass


class CacheInvalidateException(CacheException):
    pass


class RehashKind(Enum):
    ALWAYS = "always"
    NEVER = "never"
    FILES_CHANGED = "files_changed"

    def condition_class(self) -> type[RehashCondition]:
        match self:
            case RehashKind.ALWAYS | RehashKind.NEVER:
                return RehashSimple
            case RehashKind.FILES_CHANGED:
                return RehashFilesChanged
            case _:
                raise AssertionError


@dataclass
class RehashCondition(metaclass=ABCMeta):
    kind: RehashKind

    @classmethod
    @abstractmethod
    def load_db(
        cls, db: sqlite3.Connection, kind: RehashKind, cached_value_id: int
    ) -> Self:
        pass

    @abstractmethod
    def write_db_details(self, db: sqlite3.Connection, cached_value_id: int):
        pass

    @abstractmethod
    def check(self, log: logging.Logger):
        pass


HEX_PATTERN = re.compile(r"[a-fA-F\d]*")


@dataclass
class RehashFilesChanged(RehashCondition):
    hashes: dict[Path, str]
    hash_func: HashFunc

    def __init__(
        self, hashes: dict[Path, str], *, hash_func: HashFunc = HashFunc.PREFERRED
    ):
        super().__init__(kind=RehashKind.FILES_CHANGED)
        self.hashes = {Path(p): val for p, val in hashes.items()}
        self.hash_func = hash_func
        assert isinstance(hashes, dict)
        assert hashes, "Empty hash dictionary"
        assert isinstance(hash_func, HashFunc)

    @staticmethod
    def for_files(
        files: Iterable[PathLike], *, hash_func: HashFunc = HashFunc.PREFERRED
    ) -> RehashFilesChanged:
        hashes = {Path(p): hash_func.hash_file(p) for p in files}
        return RehashFilesChanged(hashes=hashes, hash_func=hash_func)

    @classmethod
    def load_db(
        cls, db: sqlite3.Connection, kind: RehashKind, cached_value_id: int
    ) -> RehashFilesChanged:
        assert kind == RehashKind.FILES_CHANGED
        res = db.execute(
            """
            SELECT file_path, hash, hash_func FROM file_hash_dependencies 
            WHERE cached_value == ?""",
            (cached_value_id,),
        )
        primary_hash_func = None
        hashes = {}
        for file_path, hash_value, hash_func_name in res:
            if file_path in hashes:
                raise CacheLoadError(f"Duplicate hashes for file: {file_path!r}")
            hashes[file_path] = hash_value
            try:
                actual_hash_func = HashFunc(hash_func_name)
            except ValueError:
                raise CacheLoadError(f"Invalid hash function: {hash_func_name!r}")
            if primary_hash_func is None:
                primary_hash_func = actual_hash_func
            elif actual_hash_func != primary_hash_func:
                raise CacheLoadError(
                    f"Using conflicting hash functions: {actual_hash_func} and {primary_hash_func}"
                )
        if not hashes:
            raise CacheLoadError(f"No hashes for cached value (id={cached_value_id})")
        assert primary_hash_func is not None
        return RehashFilesChanged(
            hashes=hashes,
            hash_func=primary_hash_func,
        )

    def write_db_details(self, db: sqlite3.Connection, cached_value_id: int):
        db.execute("SAVEPOINT update_file_hashes;")
        db.execute(
            "DELETE FROM file_hash_dependencies WHERE cached_value = ?;",
            (cached_value_id,),
        )
        db.executemany(
            "INSERT INTO file_hash_dependencies(cached_value, file_path, hash, hash_func) VALUES(?, ?, ?, ?)",
            [
                (cached_value_id, str(pth), hash_val, str(self.hash_func))
                for pth, hash_val in self.hashes.items()
            ],
        )
        db.execute("RELEASE SAVEPOINT update_file_hashes;")

    def check(self, log: logging.Logger):
        if not self.hash_func.supported:
            raise CacheInvalidateException(
                f"Missing required hash function {self.hash_func}"
            )
        for p, expected_hash in self.hashes.items():
            try:
                actual_hash = self.hash_func.hash_file(p)
            except FileNotFoundError:
                raise CacheInvalidateException(
                    f"Missing file {p}. Expected hash {expected_hash}"
                ) from None
            else:
                if actual_hash != expected_hash:
                    raise CacheInvalidateException(
                        f"Hash changed for file {p}: {expected_hash} => {actual_hash}"
                    )
                else:
                    pass
                    # log.debug("File %s has same hash: %s", p, expected_hash)
        # success
        log.debug("Successfully checked %s files", len(self.hashes))


@dataclass
class RehashSimple(RehashCondition):
    def __post_init__(self):
        assert self.kind in {RehashKind.ALWAYS, RehashKind.NEVER}

    @classmethod
    def load_db(
        cls, db: sqlite3.Connection, kind: RehashKind, cached_value_id: int
    ) -> Self:
        return RehashSimple(kind=kind)

    def write_db_details(self, db: sqlite3.Connection, cached_value_id: int):
        pass

    def check(self, log: logging.Logger):
        match self.kind:
            case RehashKind.ALWAYS:
                raise CacheInvalidateException(
                    "Using `rehash=always` unconditionally invalidates."
                )
            case RehashKind.NEVER:
                log.debug("NOTE: Using `rehash=never` never invalidates.")
            case _:
                raise AssertionError(f"Unexpected kind: {self.kind!r}")

    ALWAYS: ClassVar[RehashSimple]
    NEVER: ClassVar[RehashSimple]


RehashSimple.ALWAYS = RehashSimple(RehashKind.ALWAYS)
RehashSimple.NEVER = RehashSimple(RehashKind.NEVER)


TIMEDELTA_PATTERN = re.compile(r"(?:(\d+) days?, )?(\d?\d):(\d\d):(\d\d)(?:\.(\d+))?")


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
    value: T = field(repr=False)
    _: KW_ONLY
    rehash: RehashCondition
    sql_id: Optional[int] = None
    last_checked: Optional[datetime] = field(default_factory=datetime.now)
    check_frequency: timedelta = field(default=DEFAULT_CHECK_FREQUENCY)

    def __post_init__(self):
        if self.check_frequency.total_seconds() < 0:
            raise ValueError("Check frequency cannot be negative")

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


LATEST_DATABASE_VERSION = 2
MIGRATION_DIR = Path(__file__).parent / "migrations"


def get_db_version(db: sqlite3.Connection) -> Optional[int]:
    versions = db.execute("SELECT id from db_versions").fetchall()
    match len(versions):
        case 0:
            return None
        case 1:
            return versions[0][0]
        case _:
            raise CacheLoadError(f"Multiple versions of database schema: {versions!r}")


def migrate_database(
    db: sqlite3.Connection, *, expected_version: int = LATEST_DATABASE_VERSION
):
    if expected_version > LATEST_DATABASE_VERSION:
        raise NotImplementedError(
            f"Cannot migrate to future version: {expected_version}"
        )
    # Initial setup
    db.execute("CREATE TABLE IF NOT EXISTS db_versions(id INTEGER);")
    old_ver = get_db_version(db)
    if old_ver is None:
        old_ver = 0
    elif old_ver > expected_version:
        raise CacheException(
            f"Can't migrate DB backwards: {old_ver} -> {expected_version}"
        )
    for migration_version in range(old_ver + 1, expected_version + 1):
        migration_script = MIGRATION_DIR / f"cache_v{migration_version}.sql"
        db.execute("BEGIN TRANSACTION;")
        with db, open(migration_script, "rt") as f:
            db.executescript(f.read())
            assert get_db_version(db) == migration_version


class Cache:
    name: str
    connection: sqlite3.Connection
    _sql_id: int

    LOGGER: ClassVar[logging.Logger] = logging.getLogger("cache")

    def __init__(self, name: str, connection: sqlite3.Connection):
        self.name = name
        self.connection = connection
        migrate_database(connection)
        connection.execute("BEGIN TRANSACTION;")
        with connection:
            connection.execute(
                "INSERT INTO cache (name) VALUES (?) ON CONFLICT(name) DO NOTHING",
                (name,),
            )
            res = connection.execute("SELECT id FROM cache WHERE name = ?;", (name,))
            id_res = res.fetchone()
            if id_res is None:
                raise CacheLoadError(
                    f"ID for {name!r} should not be none (just did an insert)"
                )
            else:
                (self._sql_id,) = id_res
            if (second_id := res.fetchone()) is not None:
                raise CacheLoadError(
                    f"Conflicting ids for cache {name!r}: {self._sql_id}, {second_id}"
                )

    def get_or_load(self, key: str, fallback: Callable[[], CachedValue[T]]) -> T:
        self.connection.execute("BEGIN TRANSACTION;")
        with self.connection:
            existing_value = self._load_value(key)
            logger = Cache.LOGGER
            logger.debug("Loaded from db: %r", existing_value)
            if existing_value is not None:
                try:
                    existing_value.check_validity(logger)
                except CacheInvalidateException as e:
                    logger.info("Invalidating %s: %s", key, e)
                else:
                    return existing_value.value
            # fallthrough to failure
            logger.info("Reloading value for %s", key)
            updated_value = fallback()
            self._save_value(key, updated_value)
            assert self.connection.in_transaction
            return updated_value.value

    def _load_value(self, key: str) -> Optional[CachedValue]:
        assert self.connection.in_transaction
        res = self.connection.execute(
            """SELECT id, raw_value, last_checked, check_frequency, rehash_cond FROM cached_values
            WHERE cache_id = ? AND key = ?""",
            (self._sql_id, key),
        ).fetchone()
        if res is None:
            return None
        sql_value_id, raw_value, last_checked, check_frequency, rehash_cond_name = res
        # TODO: give descriptive errors on failure
        value = pickle.loads(raw_value)
        rehash_kind = RehashKind(rehash_cond_name)
        last_checked = datetime.fromisoformat(last_checked)
        check_frequency = (
            parse_timedelta(check_frequency)
            if check_frequency is not None
            else DEFAULT_CHECK_FREQUENCY
        )
        rehash_cond = rehash_kind.condition_class().load_db(
            self.connection, rehash_kind, sql_value_id
        )
        return CachedValue(
            value=value,
            sql_id=sql_value_id,
            rehash=rehash_cond,
            last_checked=last_checked,
            check_frequency=check_frequency,
        )

    def _save_value(self, key: str, val: CachedValue):
        assert key is not None
        assert self.connection.in_transaction
        if val.sql_id is not None:
            assert self._resolve_value_id(key) == val.sql_id
        data = {
            "cache_id": self._sql_id,
            "cache_key": key,
            "last_checked": val.last_checked.isoformat()
            if val.last_checked is not None
            else None,
            "check_frequency": str(val.check_frequency),
            "rehash_kind": val.rehash.kind.value,
            "raw_value": pickle.dumps(val.value, max(pickle.DEFAULT_PROTOCOL, 5)),
        }
        res = self.connection.execute(
            "DELETE FROM cached_values WHERE cache_id = :cache_id AND key = :cache_key",
            data,
        )
        assert res.rowcount in (0, 1)
        if val.sql_id is not None:
            assert res.rowcount == 1
        res = self.connection.execute(
            """
            INSERT INTO cached_values
                (cache_id, key, rehash_cond, last_checked, check_frequency, raw_value)
                VALUES(:cache_id, :cache_key, :rehash_kind, :last_checked,  :check_frequency, :raw_value)
            """,
            data,
        )
        if res.rowcount != 1:
            raise CacheException(
                f"Failed to save value for {key!r} in {self.name!r} (inserted {res.rowcount} rows)"
            )
        new_value_id = self._resolve_value_id(key)
        assert new_value_id is not None
        # Update rehash condition data
        val.rehash.write_db_details(self.connection, new_value_id)

    def _resolve_value_id(self, key: str) -> Optional[int]:
        res = self.connection.execute(
            "SELECT id FROM cached_values WHERE key = ? AND cache_id = ?",
            (key, self._sql_id),
        ).fetchone()
        return res[0] if res is not None else None

    PRIMARY_LOCATION: Path = Path.home() / ".cache/techcable/dotfiles/cache.sqlite"

    @staticmethod
    def open(name: str, *, location: str | Path = PRIMARY_LOCATION) -> Cache:
        if isinstance(location, Path):
            location.parent.mkdir(parents=True, exist_ok=True)
        return Cache(name, sqlite3.connect(str(location)))

    def close(self):
        self.connection.close()

    def __repr__(self):
        return f"Cache(name={self.name!r}, connection={self.connection!r}, _sql_id={self._sql_id!r})"
