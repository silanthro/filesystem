# filesystem

Tools for filesystem operations.

This requires the following environment variable:

- `ALLOWED_DIR`: The allowed directory. The tools will only be able to read/write within this directory. To allow multiple directories, supply a strictly valid JSON-encoded list e.g. use double quotes: '["dir_a", "dir_b"]'

Note that the `filesystem.read_files` tool opens files in "r" mode, which means it primarily handles text content, and not specialized file types like `.docx`.
