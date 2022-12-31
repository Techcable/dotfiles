/*
 * Cache database migration/initialization.
 *
 * VERSION: 1
 */

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- mark schema version
INSERT INTO db_versions(id) VALUES (1);

CREATE TABLE cache(
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE cached_values(
    id INTEGER PRIMARY KEY,
    cache_id INTEGER NOT NULL REFERENCES cache(id),
    key VARCHAR(255) NOT NULL,
    rehash_cond VARCHAR(255) NOT NULL,
    -- format: datetime.isoformat()
    last_checked DATETIME NOT NULL,
    -- format: timedelta.__str__
    check_frequency VARCHAR(255),
    raw_value BLOB
);

CREATE UNIQUE INDEX cached_values_by_key ON cached_values(cache_id, key);

CREATE TABLE file_hash_dependencies(
    cached_value INTEGER REFERENCES cached_values(id),
    file_path VARCHAR(2048) UNIQUE NOT NULL,
    hash VARCHAR(64) NOT NULL,
    hash_func VARCHAR(255) NOT NULL
);
CREATE INDEX file_hash_dependencies_by_cached_value ON file_hash_dependencies(cached_value);
