"""File I/O utilities for reading and validating statement files.

This module provides shared utilities for reading various file formats
(text, binary) and validating file extensions.
"""

from typing import Callable


def validate_file_extension(filepath: str, expected_extension: str) -> None:
    """Validate that a file has the expected extension.

    Args:
        filepath: Path to the file.
        expected_extension: Expected extension (e.g., ".csv", ".pdf.txt").

    Raises:
        ValueError: If the file extension doesn't match.
    """
    if not filepath.lower().endswith(expected_extension.lower()):
        raise ValueError(f"Input must be a {expected_extension} file")


def read_text_file(filepath: str, encoding: str = "utf-8") -> str:
    """Read a text file.

    Args:
        filepath: Path to the file.
        encoding: Text encoding (default: utf-8).

    Returns:
        File contents as string.
    """
    with open(filepath, "r", encoding=encoding) as handle:
        return handle.read()


def read_binary_file(filepath: str) -> bytes:
    """Read a binary file.

    Args:
        filepath: Path to the file.

    Returns:
        File contents as bytes.
    """
    with open(filepath, "rb") as handle:
        return handle.read()


def render_file_generic(
    filepath: str,
    expected_extension: str,
    render_text_func: Callable[[str], str],
    encoding: str = "utf-8",
) -> str:
    """Generic file rendering function for text files.

    Args:
        filepath: Path to the file.
        expected_extension: Expected file extension.
        render_text_func: Function to render the text content.
        encoding: Text encoding (default: utf-8).

    Returns:
        Rendered output string.

    Raises:
        ValueError: If file extension doesn't match.
    """
    validate_file_extension(filepath, expected_extension)
    text = read_text_file(filepath, encoding)
    return render_text_func(text)


def render_binary_file_generic(
    filepath: str,
    expected_extension: str,
    render_func: Callable[[bytes], str],
) -> str:
    """Generic file rendering function for binary files.

    Args:
        filepath: Path to the file.
        expected_extension: Expected file extension.
        render_func: Function to render the binary content.

    Returns:
        Rendered output string.

    Raises:
        ValueError: If file extension doesn't match.
    """
    validate_file_extension(filepath, expected_extension)
    data = read_binary_file(filepath)
    return render_func(data)
