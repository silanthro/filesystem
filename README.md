# filesystem

Tools for filesystem operations.

This requires the following environment variable:

- `ALLOWED_DIR`: The allowed directory. The tools will only be able to read/write within this directory. To allow multiple directories, supply a strictly valid JSON-encoded list e.g. use double quotes: '["dir_a", "dir_b"]'
