import difflib
import json
import multiprocessing
import os
import shutil
from pathlib import Path
from typing import Literal, TypedDict


class NotAuthorizedError(Exception):
    pass


def _get_allowed_dir() -> list[Path]:
    allowed_dir_str = os.environ["ALLOWED_DIR"]
    if not allowed_dir_str:
        return []
    if "[" in allowed_dir_str:
        return [Path(p).resolve() for p in json.loads(allowed_dir_str)]
    else:
        return [Path(allowed_dir_str).resolve()]


ALLOWED_DIR = _get_allowed_dir()


def _path_is_allowed(path: str):
    if any(Path(path).resolve() == dir for dir in ALLOWED_DIR):
        return
    if not any(dir in Path(path).resolve().parents for dir in ALLOWED_DIR):
        raise NotAuthorizedError()


def _read_files_helper(path: str) -> str:
    with open(path, "r") as file:
        contents = file.read()
    return contents


def read_files(paths: list[str]) -> dict:
    """
    Read files

    Args:
    - paths (list[str]): List of paths to files

    Returns:
        A dictionary where keys are paths and values are contents of the files
    """
    for path in paths:
        _path_is_allowed(path)
    pool = multiprocessing.Pool()
    tasks = pool.map_async(_read_files_helper, paths)
    tasks.wait()
    results = tasks.get()
    return {path: result for path, result in zip(paths, results)}


def write_file(path: str, content: str, overwrite_if_exists: bool = False) -> str:
    """
    Create a file with content
    If file exists, overwrite file with content if overwrite_if_exists=True

    Args:
    - path (str): Path to file
    - content (str): Content to write
    - overwrite_if_exists (bool): Whether to overwrite file if it exists, defaults to False

    Returns:
        If file does not exist, return "File created"
        If file exists and is overwritten, return "File overwritten"
        If file exists and overwrite_if_exists=False, return "File exists, no action taken"
    """
    _path_is_allowed(path)
    file_exists = Path(path).exists()
    if file_exists and not overwrite_if_exists:
        return "File exists, no action taken"
    with open(path, "w") as file:
        file.write(content)
    if file_exists:
        return "File overwritten"
    return "File created"


def edit_file(path: str, old_str: str, new_str: str, dry_run: bool = False) -> str:
    """
    Edit a file by searching and replacing strings
    Supports a dry run mode if dry_run=True, which will return the expected changes
    as a diff

    Args:
    - path (str): Path to file
    - old_str (str): Old string to replace
    - new_str (str): New replacement string
    - dry_run (bool): Whether to use dry run mode, defaults to False

    Returns:
        If dry_run=True, returns the before/after diff without applying any changes
        If dry_run=False, applies the changes and returns "File edited"
    """
    _path_is_allowed(path)
    with open(path, "r") as file:
        before = file.read()
    after = before.replace(old_str, new_str)
    if dry_run:
        return "".join(
            list(
                difflib.unified_diff(
                    before.splitlines(keepends=True),
                    after.splitlines(keepends=True),
                    fromfile="before",
                    tofile="after",
                )
            )
        )
    else:
        with open(path, "w") as file:
            file.write(after)
        return "File edited"


def create_dir(path: str, parents: bool = True, exist_ok: bool = True) -> str:
    """
    Create a directory

    Args:
    - path (str): Path to directory
    - parents (bool): Whether to create parent directories if needed, defaults to True
    - exist_ok (bool): Whether to raise an error if directory already exists, defaults to True

    Returns:
        "Path created"
    """
    _path_is_allowed(path)
    Path(path).mkdir(parents=parents, exist_ok=exist_ok)
    return "Path created"


class ListChild(TypedDict):
    name: str
    type: Literal["dir", "file"]


def list_dir(path: str) -> list[ListChild]:
    """
    List immediate children of a directory
    Indicates if each child is a directory or a file

    Args:
    - path (str): Path to directory

    Returns:
        List of children, where each child has the following attributes:
        - name (str): The name of the child directory or file
        - type (Literal["dir", "file"]): The type of the child, whether directory or file
    """
    _path_is_allowed(path)
    children = Path(path).glob("*")
    return [
        {
            "name": c.name,
            "type": "dir" if c.is_dir() else "file",
        }
        for c in children
    ]


def move(src: str, dst: str) -> str:
    """
    Move or rename a file or directory

    Args:
    - src (str): Path to source
    - dst (str): Path to destination

    Returns:
        "Moved path"
    """
    _path_is_allowed(src)
    _path_is_allowed(dst)
    if Path(dst).exists():
        raise FileExistsError(f"Destination {dst} already exists")
    shutil.move(src, dst)
    return "Moved path"


def search(path: str, pattern: str) -> list[str]:
    """
    Search for files or directories by their name

    Args:
    - path (str): Starting directory
    - pattern (str): Search pattern, supports glob formats

    Returns:
        List of strings indicating found paths
    """
    _path_is_allowed(path)
    results = Path(path).glob(pattern)
    return [str(r) for r in results]


def get_path_info(path: str):
    """
    Retrieves metadata of a file or directory

    Args:
    - path (str): Path to file or directory of interest

    Returns:
        A dictionary comprising the following:
        - size_in_bytes (int): Size in bytes
        - created_at (float): Creation timestamp
        - modified_at (float): Modified timestamp
        - accessed_at (float): Modified timestamp
        - type (Literal["dir", "file"]): The type of the child, whether directory or file
        - permissions (int): Decimal representation of file permissions
    """
    _path_is_allowed(path)
    _path = Path(path)
    return {
        "size_in_bytes": _path.stat().st_size,
        "created_at": _path.stat().st_ctime,
        "modified_at": _path.stat().st_mtime,
        "accessed_at": _path.stat().st_atime,
        "type": "dir" if _path.is_dir() else "file",
        "permissions": _path.stat().st_mode,
    }


def list_allowed_dir():
    """
    Returns the list of directories accessible by this tool index

    Returns:
        A list of paths accessible
    """
    return [str(d) for d in ALLOWED_DIR]
