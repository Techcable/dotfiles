DELETE FROM db_versions;
INSERT INTO db_versions(id) VALUES (2);

DROP INDEX file_hash_dependencies_by_cached_value;
ALTER TABLE file_hash_dependencies RENAME TO old_file_hash_dependencies;

CREATE TABLE file_hash_dependencies(
    cached_value INTEGER REFERENCES cached_values(id),
    file_path VARCHAR(2048) NOT NULL,
    hash VARCHAR(128) NOT NULL,
    hash_func VARCHAR(255) NOT NULL
);

CREATE UNIQUE INDEX file_hash_dependencies_by_key ON file_hash_dependencies(cached_value, file_path);

INSERT INTO file_hash_dependencies(cached_value, file_path, hash, hash_func)
    SELECT cached_value, file_path, hash, hash_func FROM old_file_hash_dependencies;

DROP TABLE old_file_hash_dependencies;
