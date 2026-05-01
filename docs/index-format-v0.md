# Index format v0

The v0 index is a SQLite database at `db/haiku-atlas.sqlite3`.

## Tables

    settings
        key/value metadata such as source_path and last_indexed_at

    files
        indexed header files with path, mtime, size, last_indexed_at

    kits
        inferred Haiku kits with stable name and display_name

    symbols
        classes, structs, enums, constructors, destructors, and methods

    relations
        symbol edges such as inherits, contains, and defined_in

    docs
        source-derived context attached to symbols

## Stability

v0 consumers may rely on:

    settings.source_path
    files.path
    kits.name
    symbols.kind
    symbols.qualified_name
    symbols.raw_declaration
    relations.relation_type
    docs.source = source_context

Schema changes after v0 should be additive or use a migration entry in
`schema_migrations`.
